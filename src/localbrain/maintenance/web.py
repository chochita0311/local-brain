import json
from fastapi import HTTPException, Request
from fastapi.responses import (
    HTMLResponse,
)
from localbrain.persistence.db import connect
from localbrain.maintenance.service import (
    cancel_run,
    get_run,
    read_run_output,
)
from localbrain.persistence.value_registry import display_value_label
from localbrain.app.templating import templates


def show_run(request: Request, run_id: str):
    with connect() as connection:
        run = get_run(connection, run_id)
        if not run or not run["task_type"]:
            raise HTTPException(status_code=404, detail="Run not found")
        output = read_run_output(run)
        try:
            manifest = json.loads(run["source_snapshot_json"] or "{}")
            candidate_counts = manifest.get("retrieval", {}).get("counts", {})
        except json.JSONDecodeError:
            candidate_counts = {}
    return templates.TemplateResponse(
        request, "run.html",
        {
            "request": request,
            "active_page": "workstreams",
            "run": run,
            "output": output,
            "candidate_counts": candidate_counts,
        },
    )


def api_run_status(run_id: str):
    with connect() as connection:
        run = get_run(connection, run_id)
        if not run or not run["task_type"]:
            raise HTTPException(status_code=404, detail="Run not found")
        data = dict(run)
        data["output"] = read_run_output(run)
        data["status_label"] = display_value_label(
            "maintenance.status", data["status"]
        )
    return {"ok": True, "run": data}


async def api_cancel_run(run_id: str):
    cancelled = await cancel_run(run_id)
    if not cancelled:
        raise HTTPException(status_code=409, detail="중지할 수 있는 실행 상태가 아닙니다.")
    return {"ok": True}
