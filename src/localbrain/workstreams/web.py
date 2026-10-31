import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, Request
from fastapi.responses import (
    HTMLResponse,
)
from pydantic import BaseModel, Field
from localbrain.foundation.config import settings
from localbrain.persistence.db import connect, transaction
from localbrain.workstreams.runner import (
    prepare_run,
    start_run,
    list_runs,
    runner_command_preview,
    task_choices,
)
from localbrain.foundation.agent_cli import runner_executable
from localbrain.workstreams.service import (
    add_link,
    create_checkpoint,
    create_thread,
    create_workstream,
    generate_suggestions,
    get_workstream,
    list_workstreams,
    picker_resources,
    remove_link,
    resolve_suggestion,
    update_thread,
    update_workstream,
)
from localbrain.app.templating import templates


class WorkstreamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    summary: Optional[str] = Field(default=None, max_length=2000)


class WorkstreamUpdate(WorkstreamCreate):
    status: str = Field(max_length=32)


class ThreadCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    summary: Optional[str] = Field(default=None, max_length=2000)
    current_goal: Optional[str] = Field(default=None, max_length=2000)
    next_action: Optional[str] = Field(default=None, max_length=2000)


class ThreadUpdate(ThreadCreate):
    status: str = Field(max_length=32)


class CheckpointCreate(BaseModel):
    current_goal: Optional[str] = Field(default=None, max_length=4000)
    confirmed_facts: Optional[str] = Field(default=None, max_length=12000)
    recent_decisions: Optional[str] = Field(default=None, max_length=12000)
    open_questions: Optional[str] = Field(default=None, max_length=12000)
    next_actions: Optional[str] = Field(default=None, max_length=12000)
    files_to_open: Optional[str] = Field(default=None, max_length=12000)


class LinkCreate(BaseModel):
    scope_type: str
    scope_id: int
    entity_type: str
    entity_id: str
    relation_type: str = Field(default="related-to", min_length=1, max_length=80)


def workstreams_page(request: Request):
    with connect() as connection:
        items = list_workstreams(connection)
    return templates.TemplateResponse(
        "workstreams.html",
        {
            "request": request,
            "active_page": "workstreams",
            "workstreams": items,
        },
    )


def show_workstream(request: Request, workstream_id: int):
    with connect() as connection:
        workstream = get_workstream(connection, workstream_id)
        if not workstream:
            raise HTTPException(status_code=404, detail="Workstream not found")
        resources = picker_resources(connection)
        runs = list_runs(connection, workstream_id)
    return templates.TemplateResponse(
        "workstream.html",
        {
            "request": request,
            "active_page": "workstreams",
            "workstream": workstream,
            "resources": resources,
            "runs": runs,
            "task_choices": task_choices(),
            "runner_available": bool(runner_executable()),
            "runner_command": runner_command_preview(),
            "runner_cwd": str(Path.home()),
            "runner_mcp_budget": settings.mcp_call_budget,
        },
    )


def api_create_workstream(payload: WorkstreamCreate):
    try:
        with transaction() as connection:
            workstream_id = create_workstream(connection, payload.name, payload.summary)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="같은 이름의 Workstream이 있습니다.") from exc
    return {"ok": True, "id": workstream_id, "redirect": "/workstreams/{}".format(workstream_id)}


def api_update_workstream(workstream_id: int, payload: WorkstreamUpdate):
    try:
        with transaction() as connection:
            update_workstream(
                connection, workstream_id, payload.name, payload.status, payload.summary
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="같은 이름의 Workstream이 있습니다.") from exc
    return {"ok": True}


def api_create_thread(workstream_id: int, payload: ThreadCreate):
    try:
        with transaction() as connection:
            thread_id = create_thread(
                connection,
                workstream_id,
                payload.title,
                payload.summary,
                payload.current_goal,
                payload.next_action,
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="같은 제목의 Thread가 있습니다.") from exc
    return {"ok": True, "id": thread_id}


def api_update_thread(thread_id: int, payload: ThreadUpdate):
    try:
        with transaction() as connection:
            update_thread(
                connection,
                thread_id,
                payload.title,
                payload.status,
                payload.summary,
                payload.current_goal,
                payload.next_action,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="같은 제목의 Thread가 있습니다.") from exc
    return {"ok": True}


def api_create_checkpoint(workstream_id: int, payload: CheckpointCreate):
    with transaction() as connection:
        checkpoint_id = create_checkpoint(
            connection,
            workstream_id,
            payload.current_goal,
            payload.confirmed_facts,
            payload.recent_decisions,
            payload.open_questions,
            payload.next_actions,
            payload.files_to_open,
        )
    return {"ok": True, "id": checkpoint_id}


def api_add_link(payload: LinkCreate):
    try:
        with transaction() as connection:
            link_id = add_link(
                connection,
                payload.scope_type,
                payload.scope_id,
                payload.entity_type,
                payload.entity_id,
                payload.relation_type,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "id": link_id}


def api_remove_link(scope_type: str, scope_id: int, link_id: int):
    try:
        with transaction() as connection:
            remove_link(connection, scope_type, scope_id, link_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


def api_generate_suggestions(workstream_id: int):
    try:
        with transaction() as connection:
            created = generate_suggestions(connection, workstream_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "created": created}


def api_resolve_suggestion(suggestion_id: int, action: str):
    try:
        with transaction() as connection:
            resolve_suggestion(connection, suggestion_id, action)
    except (ValueError, LookupError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


class TaskRunCreate(BaseModel):
    task_type: str = Field(default="organize_resources", max_length=80)
    instruction: Optional[str] = Field(default=None, max_length=4000)
    refresh_suggestions: bool = False


async def api_start_task_run(workstream_id: int, payload: TaskRunCreate):
    if not runner_executable():
        raise HTTPException(status_code=503, detail="Claude CLI를 찾을 수 없습니다.")
    try:
        with transaction() as connection:
            active = connection.execute(
                """
                SELECT id FROM maintenance_runs
                WHERE workstream_id = ? AND status IN ('queued', 'running', 'cancelling')
                LIMIT 1
                """,
                (workstream_id,),
            ).fetchone()
            if active:
                raise ValueError("이 Workstream에서 이미 실행 중인 작업이 있습니다.")
            run_id = prepare_run(
                connection,
                workstream_id,
                payload.task_type,
                payload.instruction,
                refresh_suggestions=payload.refresh_suggestions,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    start_run(run_id)
    return {"ok": True, "run_id": run_id, "redirect": "/runs/{}".format(run_id)}
