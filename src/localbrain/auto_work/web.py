import subprocess
import sys
from fastapi import HTTPException, Request
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from starlette.concurrency import run_in_threadpool
from localbrain.foundation.config import cache_directory, settings
from localbrain.auto_work.preview import preview_page
from localbrain.auto_work.affinity import affinity_page
from localbrain.app.request_guards import _auto_work_local_request
from localbrain.app.templating import templates


def auto_work_page(request: Request):
    _auto_work_local_request(request)
    params = request.query_params
    if params.get("mode") != "sample":
        return templates.TemplateResponse("affinity-map.html", {
            "request": request, "active_page": "auto-work",
            "mapview": affinity_page(settings.database_path, cache_directory(settings), params=params),
        }, headers={"Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff"})
    preview = preview_page(settings.database_path, cache_directory(settings),
                           page=params.get("page", "1"), flow=params.get("flow"),
                           view=params.get("view", "flows"), evidence_page=params.get("evidence_page", "1"))
    notices = {"updated": "현재 데이터로 분석 결과를 갱신했습니다. 분류 품질은 아직 미평가입니다.",
               "failed": "분석을 완료하지 못했습니다. 유효한 이전 결과는 유지됩니다. 다시 시도할 수 있습니다.",
               "busy": "이미 분석 중입니다. 잠시 후 이 화면을 새로고침해 주세요."}
    notice = params.get("notice")
    return templates.TemplateResponse("auto-work.html", {
        "request": request, "active_page": "auto-work", "preview": preview,
        "notice": notices.get(notice), "notice_failed": notice == "failed",
    }, headers={"Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff"})


def _refresh_auto_work():
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-m", "localbrain.auto_work", "--database", str(settings.database_path),
             "--cache-dir", str(cache_directory(settings))],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=300, start_new_session=True,
        )
        return "updated" if result.returncode == 0 else "busy" if result.returncode == 3 else "failed"
    except (OSError, subprocess.TimeoutExpired):
        return "failed"


async def auto_work_refresh(request: Request):
    _auto_work_local_request(request)
    origin = request.headers.get("origin")
    if origin != "{}://{}".format(request.url.scheme, request.url.netloc):
        raise HTTPException(status_code=400, detail="Same-origin submission required")
    async for chunk in request.stream():
        if chunk:
            raise HTTPException(status_code=400, detail="This action takes no input")
    notice = await run_in_threadpool(_refresh_auto_work)
    return RedirectResponse("/auto-work?mode=sample&notice=" + notice, status_code=303,
                            headers={"Cache-Control": "no-store, private"})
