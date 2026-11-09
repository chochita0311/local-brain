"""Shared settings API and views for the browser and the standalone app."""

import json
from contextlib import closing
import sqlite3

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from localbrain.foundation.config import settings
from localbrain.local_context.service import list_context_sources
from localbrain.persistence.db import connect
from localbrain.app.edition import DESKTOP
from localbrain.foundation.operations import OperationBusy
from localbrain.foundation.preferences import PreferencesError, read_preferences, save_preferences
from localbrain.foundation.paths import home_relative_path
from localbrain.sources.settings import candidates, source_inventory, update_source


async def payload(request):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 65536:
            raise HTTPException(413, "설정 요청이 너무 큽니다.")
    try:
        value = json.loads(body)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except ValueError:
        raise HTTPException(422, "설정 요청 형식을 확인해 주세요.") from None


def install_settings_routes(app, templates):
    def cutoff_settings():
        from localbrain.natural_search.index import search_settings
        from localbrain.natural_search.molecules import Profile
        try:
            return search_settings(settings)
        except (ValueError, OSError):
            return {"cutoff": None, "default_cutoff": Profile().cutoff, "revision": None,
                    "error": "검색 관련도 설정을 읽지 못했습니다. 다시 확인해 주세요."}

    def model_status(request):
        model = request.app.state.model_setup.status()
        if "context_search" not in request.app.state.feature_packages:
            model = {**model, "generation_models": [], "generation_runtime_missing": []}
        return model

    @app.exception_handler(PreferencesError)
    async def preferences_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=409)

    @app.exception_handler(OperationBusy)
    async def busy_error(request, error):
        return JSONResponse({"detail": "동기화 또는 저장 작업이 진행 중입니다. 완료 후 다시 시도해 주세요."}, status_code=409)

    @app.get("/settings")
    def settings_page(request: Request):
        return templates.TemplateResponse(request, "settings.html", {"request": request, "active_page": "settings"})

    @app.get("/onboarding")
    def onboarding(request: Request):
        try:
            screen = read_preferences()["effective"]["startup_screen"]
        except PreferencesError:
            return RedirectResponse("/settings", status_code=303)
        return RedirectResponse("/" + screen + "?setup=1", status_code=303)

    @app.get("/api/settings")
    def get_settings(request: Request):
        errors = []
        try:
            preferences = read_preferences()
            preferences.pop("raw")
        except PreferencesError as error:
            preferences = None
            errors.append(str(error))
        try:
            sources = source_inventory()
            for source in sources["sources"]:
                source["display_path"] = home_relative_path(source["root_path"])
        except (PreferencesError, OperationBusy) as error:
            sources = None
            errors.append(str(error))
        with closing(connect()) as connection:
            contexts = list_context_sources(connection)
        detected = [{**candidate, "display_home": home_relative_path(candidate["agent_home"])}
                    for candidate in candidates()]
        return {"preferences": preferences, "session_sources": sources, "context_sources": contexts,
                "candidates": detected, "errors": errors, "desktop": DESKTOP,
                "sync": request.app.state.session_sync.status(),
                "context_sync": request.app.state.context_sync.status(),
                "model": model_status(request), "search_settings": cutoff_settings()}

    @app.get("/api/settings/search")
    def get_search_settings():
        return JSONResponse(cutoff_settings(), headers={"Cache-Control": "no-store"})

    @app.post("/api/settings/search")
    async def search_settings_update(request: Request):
        from starlette.concurrency import run_in_threadpool
        from localbrain.natural_search.index import update_cutoff
        value = await payload(request)
        if set(value) != {"cutoff", "revision"}:
            raise HTTPException(422, "검색 관련도 요청을 확인해 주세요.")
        try:
            return await run_in_threadpool(update_cutoff, settings, value["cutoff"], value["revision"])
        except ValueError as error:
            if str(error) == "INVALID_SEARCH_CUTOFF":
                raise HTTPException(422, "최소 관련도는 0부터 1 사이의 숫자로 입력해 주세요.") from None
            if str(error) == "SEARCH_SETTINGS_CHANGED":
                raise HTTPException(409, "검색 설정이 변경되었습니다. 다시 확인한 뒤 저장해 주세요.") from None
            raise HTTPException(409, "검색 관련도 설정을 읽지 못했습니다. 다시 확인해 주세요.") from None
        except OSError:
            raise HTTPException(503, "검색 관련도를 저장하지 못했습니다. 다시 시도해 주세요.") from None

    @app.patch("/api/settings/preferences")
    async def preferences_update(request: Request):
        value = await payload(request)
        result = save_preferences(value.get("changes"), value.get("revision"))
        result.pop("raw")
        request.app.state.session_sync.changed()
        request.app.state.context_sync.changed()
        return result

    @app.post("/api/settings/session-sources")
    async def sources_update(request: Request):
        from starlette.concurrency import run_in_threadpool
        result = await run_in_threadpool(update_source, await payload(request))
        request.app.state.session_sync.changed()
        return result

    @app.post("/api/settings/choose-path")
    async def choose_path(request: Request):
        # An OS dialog is an explicit action from this local page, not a GET or
        # cross-origin form action. Do not accept a caller-supplied script/path.
        if (request.url.hostname not in {"localhost", "127.0.0.1", "::1"}
                or request.headers.get("origin") != str(request.base_url).rstrip("/")
                or request.headers.get("sec-fetch-site") == "cross-site"):
            raise HTTPException(403, "같은 앱 화면에서 요청해 주세요.")
        if request.headers.get("content-type", "").split(";", 1)[0].strip() != "application/json":
            raise HTTPException(415, "설정 요청 형식을 확인해 주세요.")
        value = await payload(request)
        if set(value) != {"directory"} or type(value["directory"]) is not bool:
            raise HTTPException(422, "파일 또는 폴더 선택을 지정해 주세요.")
        from starlette.concurrency import run_in_threadpool
        from localbrain.app.picker import choose_local_path
        return {"path": await run_in_threadpool(choose_local_path, value["directory"])}

    @app.post("/api/settings/model/{action}")
    def model_action(action: str, request: Request):
        if action == "install":
            request.app.state.model_setup.start()
        elif action == "cancel":
            request.app.state.model_setup.cancel()
        elif action == "prepare":
            request.app.state.natural_search.request_prepare()
        elif action == "disable":
            from localbrain.natural_search.index import save_settings, read_settings
            from localbrain.foundation.operations import operation_lock
            with operation_lock(settings, "search-settings"):
                _, profile = read_settings(settings)
                save_settings(settings, profile=profile, enabled=False)
                request.app.state.natural_search.cancel()
        else:
            raise HTTPException(404)
        return model_status(request)

    @app.post('/api/settings/model-folder/{action}')
    async def model_folder_action(action: str, request: Request):
        from starlette.concurrency import run_in_threadpool
        if action not in {'check', 'apply', 'download'}:
            raise HTTPException(404)
        value = await payload(request)
        if set(value) != ({'path'} if action == 'check' else {'path', 'revision'}):
            raise HTTPException(422, '모델 폴더 요청을 확인해 주세요.')
        service = request.app.state.model_setup
        if action == 'check':
            return await run_in_threadpool(service.check_folder, value['path'])
        if action == 'apply':
            return await run_in_threadpool(service.use_folder, value['path'], value['revision'])
        await run_in_threadpool(service.start, cache_root=value['path'], revision=value['revision'])
        return model_status(request)

    @app.post('/api/settings/model/{key}/{action}')
    def generation_model_action(key: str, action: str, request: Request):
        if ("context_search" not in request.app.state.feature_packages
                or key not in {'4b', '8b'} or action not in {'install', 'cancel'}):
            raise HTTPException(404)
        service = request.app.state.model_setup
        if action == 'install':
            service.start(key)
        elif service.status()['active_key'] == key:
            service.cancel()
        return service.status()

    from localbrain.app.storage.web import install_storage_routes
    install_storage_routes(app)
