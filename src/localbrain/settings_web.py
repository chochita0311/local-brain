"""Shared settings API and views for the browser and the standalone app."""

import json
from contextlib import closing
import sqlite3

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .config import settings
from .contexts import list_context_sources
from .db import connect
from .edition import DESKTOP
from .local_operations import OperationBusy
from .preferences import PreferencesError, read_preferences, save_preferences
from .path_display import home_relative_path
from .source_settings import candidates, source_inventory, update_source


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
    @app.exception_handler(PreferencesError)
    async def preferences_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=409)

    @app.exception_handler(OperationBusy)
    async def busy_error(request, error):
        return JSONResponse({"detail": "동기화 또는 저장 작업이 진행 중입니다. 완료 후 다시 시도해 주세요."}, status_code=409)

    @app.get("/settings")
    def settings_page(request: Request):
        return templates.TemplateResponse("settings.html", {"request": request, "active_page": "settings"})

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
                "model": request.app.state.model_setup.status()}

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
        from .local_picker import choose_local_path
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
            from .natural_search.index import save_settings, read_settings
            from .local_operations import operation_lock
            with operation_lock(settings, "search-settings"):
                _, profile = read_settings(settings)
                save_settings(settings, profile=profile, enabled=False)
                request.app.state.natural_search.cancel()
        else:
            raise HTTPException(404)
        return request.app.state.model_setup.status()

    @app.post('/api/settings/model/{key}/{action}')
    def generation_model_action(key: str, action: str, request: Request):
        if key not in {'4b', '8b'} or action not in {'install', 'cancel'}:
            raise HTTPException(404)
        service = request.app.state.model_setup
        if action == 'install':
            service.start(key)
        elif service.status()['active_key'] == key:
            service.cancel()
        return service.status()

    from .storage_recovery import install_storage_routes
    install_storage_routes(app)
