"""Settings-only Google Drive routes; page/status reads never contact Google."""

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool

from .google_drive.policy import DriveError
from .settings_web import payload


def install_routes(app):
    def service(request):
        if request.app.state.google_drive is None:
            raise HTTPException(503, "Google Drive의 로컬 상태를 읽지 못했습니다. 기존 상태를 보존합니다. 앱 데이터 폴더를 확인해 주세요.")
        return request.app.state.google_drive

    async def action(request, operation):
        try:
            return await run_in_threadpool(operation)
        except DriveError as error:
            raise HTTPException(409 if error.code == "busy" else 422, detail=str(error)) from None

    @app.get("/api/settings/google-drive")
    async def status(request: Request):
        return await action(request, service(request).status)

    @app.post("/api/settings/google-drive/connections")
    async def add(request: Request):
        values = await payload(request)
        if set(values) != {"url", "target"} or not all(isinstance(v, str) for v in values.values()):
            raise HTTPException(422, "루트 폴더 URL과 내 대상 폴더명을 입력해 주세요.")
        return await action(request, lambda: service(request).add(values["url"], values["target"]))

    @app.post("/api/settings/google-drive/{connection_id}/connect")
    async def authenticate(connection_id: str, request: Request):
        values = await payload(request)
        if (not set(values) <= {"account", "login"}
                or ("account" in values and not isinstance(values["account"], str))
                or ("login" in values and type(values["login"]) is not bool)):
            raise HTTPException(422, "Google 계정과 로그인 요청을 확인해 주세요.")
        login = values.get("login", False)
        await action(request, lambda: service(request).authenticate(connection_id, values.get("account") or None, login))
        return {"status": "auth_pending" if login else "connected"}

    @app.post("/api/settings/google-drive/{connection_id}/browse")
    async def browse(connection_id: str, request: Request):
        return {"publishers": await action(request, lambda: service(request).browse(connection_id))}

    @app.patch("/api/settings/google-drive/{connection_id}/jobs/{job}")
    async def configure(connection_id: str, job: str, request: Request):
        values = await payload(request)
        await action(request, lambda: service(request).configure(connection_id, job, values))
        return {"saved": True}

    @app.post("/api/settings/google-drive/{connection_id}/jobs/{job}/run")
    async def run(connection_id: str, job: str, request: Request):
        await action(request, lambda: service(request).run(connection_id, job))
        return {"started": True}
