from fastapi import HTTPException, Request


def _auto_work_local_request(request: Request):
    if request.url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise HTTPException(status_code=400, detail="Local access required")
    if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
        raise HTTPException(status_code=400, detail="Local access required")
