import json
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs
from fastapi import HTTPException, Query, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from localbrain.foundation.config import settings
from localbrain.persistence.db import connect, transaction
from localbrain.insights.skills import skill_insights_data
from localbrain.insights.evidence import resolve_insight_evidence_reference
from localbrain.insights.usage import insight_usage_cost
from localbrain.insights.runs import (
    cancel_insight_run,
    get_insight_run,
    list_insight_runs,
    prepare_insight_run,
    runner_choices as insight_runner_choices,
    start_insight_run,
)
from localbrain.rendering.markdown import render_markdown
from localbrain.app.request_guards import _auto_work_local_request
from localbrain.app.templating import templates


def session_insights(
    request: Request,
    run: Optional[str] = Query(default=None),
    before: Optional[str] = Query(default=None),
):
    _auto_work_local_request(request)
    return _session_insights_response(request, selected_id=run, before=before)


def _session_insights_response(
    request: Request,
    *,
    selected_id: Optional[str] = None,
    before: Optional[str] = None,
    error: Optional[str] = None,
    question: str = "",
):
    with connect() as connection:
        insights = skill_insights_data(connection)
        run_rows = list_insight_runs(connection, limit=21, before=before)
        has_more = len(run_rows) > 20
        run_rows = run_rows[:20]
        selected = get_insight_run(connection, selected_id) if selected_id else None
        if selected_id and selected is None:
            raise HTTPException(status_code=404, detail="Analysis Run not found")
        report_html = None
        reference_states = None
        if selected and selected["status"] in {"completed", "no_finding"}:
            report_path = Path(selected["report_path"])
            if report_path.is_file():
                report_source = report_path.read_text(encoding="utf-8", errors="replace")
                trusted_session_routes = set()
                try:
                    manifest = json.loads(Path(selected["evidence_path"]).read_text(encoding="utf-8"))
                    trusted_session_routes = {
                        f"/sessions/{session['session_id']}"
                        for session in manifest["sessions"]
                        if isinstance(session, dict)
                        and type(session.get("session_id")) is int
                        and session["session_id"] > 0
                    }
                    result = json.loads(Path(selected["response_path"]).read_text(encoding="utf-8"))
                    admitted = {
                        event["event_id"]: event
                        for session in manifest["sessions"] for event in session["events"]
                    }
                    cited = {
                        ref for finding in result.get("findings", [])
                        for field in ("evidence_ids", "counterevidence_ids")
                        for ref in finding.get(field, [])
                    }
                    cited.update(result.get("selection_evidence_ids", []))
                    cited.update(result.get("additional_evidence", {}).get("evidence_ids", []))
                    reference_states = {"current": 0, "stale": 0, "unavailable": 0}
                    for ref in cited:
                        event = admitted.get(ref.rsplit(":", 1)[-1])
                        state = (
                            resolve_insight_evidence_reference(connection, event)["status"]
                            if event else "unavailable"
                        )
                        reference_states[state] += 1
                except (OSError, ValueError, KeyError, TypeError, AttributeError, json.JSONDecodeError):
                    reference_states = None
                report_html = render_markdown(
                    report_source, trusted_session_routes=trusted_session_routes
                ).html
        selected_coverage = (
            json.loads(selected["coverage_json"]) if selected else None
        )
        selected_usage = (
            json.loads(selected["usage_json"]) if selected and selected["usage_json"] else None
        )
        selected_settings = (
            json.loads(selected["settings_json"]) if selected else None
        )
        selected_cost = insight_usage_cost(connection, selected["id"]) if selected else None
    return templates.TemplateResponse(
        "session_insights.html",
        {
            "request": request,
            "active_page": "sessions-dashboard",
            "insights": insights,
            "runner_choices": insight_runner_choices(),
            "insight_runs": run_rows,
            "selected_run": selected,
            "report_html": report_html,
            "selected_coverage": selected_coverage,
            "selected_usage": selected_usage,
            "selected_cost": selected_cost,
            "selected_settings": selected_settings,
            "reference_states": reference_states,
            "has_more_runs": has_more,
            "next_before": run_rows[-1]["id"] if run_rows and has_more else None,
            "form_error": error,
            "question_draft": question,
        },
        headers={"Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff"},
    )


def _insight_submission_guard(request: Request) -> None:
    _auto_work_local_request(request)
    origin = request.headers.get("origin")
    if origin and origin != "{}://{}".format(request.url.scheme, request.url.netloc):
        raise HTTPException(status_code=400, detail="Same-origin submission required")


async def create_insight_run(request: Request):
    _insight_submission_guard(request)
    if request.headers.get("content-type", "").split(";", 1)[0] != "application/x-www-form-urlencoded":
        raise HTTPException(status_code=415, detail="Form submission required")
    body = await request.body()
    if len(body) > 8_192:
        raise HTTPException(status_code=413, detail="Form is too large")
    try:
        form = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="Invalid form encoding") from error
    mode = (form.get("mode") or [""])[0]
    question = (form.get("question") or [""])[0].strip()
    runner = (form.get("runner") or [""])[0]
    try:
        with transaction(immediate=True) as connection:
            active = connection.execute(
                """SELECT id FROM personal_insight_runs
                   WHERE status IN ('queued', 'running') LIMIT 1"""
            ).fetchone()
            if active:
                raise ValueError("이미 분석이 실행 중입니다. 완료하거나 중지한 뒤 새로 시작해 주세요.")
            run_id = prepare_insight_run(
                connection, mode=mode,
                question=question if mode == "ask" else None, runner=runner,
            )
    except ValueError as error:
        return _session_insights_response(
            request, error=str(error), question=question,
        )
    start_insight_run(run_id)
    return RedirectResponse(
        "/sessions-dashboard/insights?run={}#session-insights-run-detail".format(run_id),
        status_code=303,
        headers={"Cache-Control": "no-store, private"},
    )


async def stop_insight_run(request: Request, run_id: str):
    _insight_submission_guard(request)
    if not await cancel_insight_run(run_id):
        raise HTTPException(status_code=409, detail="중지할 수 있는 분석 실행이 아닙니다.")
    return RedirectResponse(
        "/sessions-dashboard/insights?run={}#session-insights-run-detail".format(run_id),
        status_code=303,
        headers={"Cache-Control": "no-store, private"},
    )


def download_insight_report(request: Request, run_id: str):
    _auto_work_local_request(request)
    with connect() as connection:
        run = get_insight_run(connection, run_id)
    if not run or run["status"] not in {"completed", "no_finding"}:
        raise HTTPException(status_code=404, detail="Report not found")
    path = Path(run["report_path"])
    expected = settings.data_dir / "personal-insight-runs" / run_id / "report.md"
    if path != expected or not path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        path, media_type="text/markdown; charset=utf-8",
        filename="localbrain-insight-{}.md".format(run_id),
        headers={"Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff"},
    )


def insight_run_status(request: Request, run_id: str):
    _auto_work_local_request(request)
    with connect() as connection:
        run = get_insight_run(connection, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis Run not found")
    return JSONResponse({
        "id": run_id, "status": run["status"], "title": run["title"],
        "error": run["error"], "updated_at": run["updated_at"],
    }, headers={"Cache-Control": "no-store, private"})
