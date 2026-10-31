from typing import Optional
from fastapi import Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from localbrain.persistence.db import connect, transaction
from localbrain.workflow.focus import workflow_focus_projection
from localbrain.workflow.assertions import (
    WorkflowAssertionError,
    apply_workflow_assertion,
    undo_workflow_assertion,
)
from localbrain.workflow.correction import (
    MAX_WORKFLOW_CORRECTION_FORM_BYTES,
    WORKFLOW_CORRECTION_PARTIAL,
    WorkflowCorrectionRequestError,
    parse_workflow_correction_form,
    reject_cross_site_workflow_correction,
)
from localbrain.workflow.correction_view import workflow_relation_id
from localbrain.workflow.map import workflow_map_state_view, workflow_map_view
from localbrain.app.templating import templates


def show_session_workflow(
    request: Request,
    session_id: int,
    workflow_result: Optional[str] = None,
):
    feedback = {
        "corrected": {
            "kind": "success",
            "code": "workflow-corrected",
            "message": "작업 흐름 경계를 사용자 확인으로 반영했습니다.",
        },
        "undone": {
            "kind": "success",
            "code": "workflow-undone",
            "message": "이전 경계를 되돌려 작업 흐름을 다시 투영했습니다.",
        },
    }.get(workflow_result)
    return _workflow_page_response(
        request, session_id, correction_feedback=feedback
    )


def _workflow_page_response(
    request: Request,
    session_id: int,
    *,
    correction_feedback: Optional[dict] = None,
    preferred_status_code: Optional[int] = None,
):
    try:
        with connect() as connection:
            projection = workflow_focus_projection(connection, session_id)
        workflow = workflow_map_view(projection, session_id)
    except Exception:
        workflow = workflow_map_state_view("unexpected-error", session_id)
        status_code = 500
    else:
        status_code = {
            "ready": 200,
            "missing": 404,
            "ineligible": 422,
        }[workflow["status"]]
        if preferred_status_code is not None and workflow["status"] == "ready":
            status_code = preferred_status_code
    return templates.TemplateResponse(
        request, "session-workflow.html",
        {
            "request": request,
            "active_page": "sessions",
            "workflow": workflow,
            "workflow_correction_feedback": correction_feedback,
        },
        status_code=status_code,
    )


_WORKFLOW_CORRECTION_CONFLICTS = frozenset(
    {
        "conflict",
        "duplicate-active",
        "assertion-not-active",
        "assertion-not-found",
        "requires-active-closure",
        "not-tip",
        "missing-endpoint",
        "cycle",
        "contradictory-boundary",
    }
)


_WORKFLOW_CORRECTION_MESSAGES = {
    "cross-site-request": "다른 사이트에서 시작된 작업 흐름 교정은 받지 않습니다.",
    "invalid-form": "교정 요청 형식을 읽을 수 없습니다.",
    "invalid-request": "교정 요청의 필드가 현재 작업과 맞지 않습니다.",
    "invalid-action": "지원하지 않는 작업 흐름 교정입니다.",
    "invalid-note": "메모는 1,000자 안에서 입력해 주세요.",
    "invalid-close-reason": "지원되는 종료 사유를 선택해 주세요.",
    "conflict": "작업 흐름이 달라졌습니다. 새로 고친 뒤 다시 확인해 주세요.",
    "duplicate-active": "같은 교정이 이미 적용되어 있습니다. 현재 흐름을 다시 확인해 주세요.",
    "assertion-not-active": "이 교정은 더 이상 현재 상태가 아닙니다. 새로 고쳐 주세요.",
    "assertion-not-found": "되돌릴 교정을 찾을 수 없습니다. 새로 고쳐 주세요.",
    "requires-active-closure": "현재 사용자 종료 경계가 없어 다시 열 수 없습니다.",
    "not-tip": "다음 Episode가 있는 지점은 종료할 수 없습니다.",
    "missing-endpoint": "교정할 Episode가 현재 흐름 범위에 없습니다.",
    "cycle": "이 교정은 순환 경로를 만들 수 있어 적용하지 않았습니다.",
    "contradictory-boundary": "도착 Episode에 다른 진입 경계가 있어 적용하지 않았습니다.",
    "self-relation": "같은 Episode를 관계의 양쪽으로 지정할 수 없습니다.",
    "non-forward-time": "관계는 관측 시간상 앞으로 이어져야 합니다.",
    "merge-before-source": "병합 지점은 출발 Episode보다 뒤여야 합니다.",
    "requires-continues": "현재 이어짐 관계에서만 분기로 바꿀 수 있습니다.",
    "invalid-projection": "이 Session에서는 작업 흐름을 교정할 수 없습니다.",
    "correction-failed": "교정을 적용하지 못했습니다. 현재 흐름은 바뀌지 않았습니다.",
}


def _workflow_correction_error(code: str, status_code: int) -> dict:
    safe_code = code if code in _WORKFLOW_CORRECTION_MESSAGES else "correction-failed"
    return {
        "kind": "conflict" if status_code == 409 else "error",
        "code": safe_code,
        "message": _WORKFLOW_CORRECTION_MESSAGES[safe_code],
        "reload": status_code == 409,
    }


def _workflow_vary(response):
    current = response.headers.get("vary")
    values = [item.strip() for item in current.split(",")] if current else []
    if "X-LocalBrain-Partial" not in values:
        values.append("X-LocalBrain-Partial")
    response.headers["Vary"] = ", ".join(item for item in values if item)
    return response


async def _workflow_correction_body(request: Request) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise WorkflowCorrectionRequestError(
                "invalid-form", "Content length is invalid.", status_code=400
            ) from exc
        if declared_length < 0:
            raise WorkflowCorrectionRequestError(
                "invalid-form", "Content length is invalid.", status_code=400
            )
        if declared_length > MAX_WORKFLOW_CORRECTION_FORM_BYTES:
            raise WorkflowCorrectionRequestError(
                "invalid-form", "Form is too large.", status_code=400
            )
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_WORKFLOW_CORRECTION_FORM_BYTES:
            raise WorkflowCorrectionRequestError(
                "invalid-form", "Form is too large.", status_code=400
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _workflow_correction_failure_response(
    request: Request,
    session_id: int,
    *,
    code: str,
    status_code: int,
    enhanced: bool,
):
    feedback = _workflow_correction_error(code, status_code)
    if enhanced:
        payload = {
            "status": "error",
            "code": feedback["code"],
            "message": feedback["message"],
        }
        if feedback["reload"]:
            payload["reload_url"] = "/sessions/{}/workflow".format(session_id)
        return _workflow_vary(JSONResponse(payload, status_code=status_code))
    return _workflow_vary(
        _workflow_page_response(
            request,
            session_id,
            correction_feedback=feedback,
            preferred_status_code=status_code,
        )
    )


async def correct_session_workflow(request: Request, session_id: int):
    enhanced = (
        request.headers.get("x-localbrain-partial")
        == WORKFLOW_CORRECTION_PARTIAL
    )
    try:
        reject_cross_site_workflow_correction(
            request.headers.get("sec-fetch-site")
        )
        body = await _workflow_correction_body(request)
        correction = parse_workflow_correction_form(
            request.headers.get("content-type"), body
        )
    except WorkflowCorrectionRequestError as error:
        return _workflow_correction_failure_response(
            request,
            session_id,
            code=error.code,
            status_code=error.status_code,
            enhanced=enhanced,
        )

    try:
        with transaction() as connection:
            projection = workflow_focus_projection(connection, session_id)
            if correction.action == "undo":
                result = undo_workflow_assertion(
                    connection,
                    projection,
                    assertion_id=correction.assertion_id,
                    expected_revision=correction.expected_revision,
                )
            else:
                result = apply_workflow_assertion(
                    connection,
                    projection,
                    assertion_kind=correction.action,
                    source_episode_key=correction.source_episode_key,
                    target_episode_key=correction.target_episode_key,
                    close_reason=correction.close_reason,
                    note=correction.note,
                    expected_active_assertion_id=(
                        correction.expected_active_assertion_id
                    ),
                    expected_revision=correction.expected_revision,
                )
    except WorkflowAssertionError as error:
        status_code = 409 if error.code in _WORKFLOW_CORRECTION_CONFLICTS else 422
        return _workflow_correction_failure_response(
            request,
            session_id,
            code=error.code,
            status_code=status_code,
            enhanced=enhanced,
        )
    except Exception:
        return _workflow_correction_failure_response(
            request,
            session_id,
            code="correction-failed",
            status_code=500,
            enhanced=enhanced,
        )

    assertion = result["assertion"]
    result_code = (
        "workflow-undone" if correction.action == "undo" else "workflow-corrected"
    )
    result_message = (
        "이전 경계를 되돌려 작업 흐름을 다시 투영했습니다."
        if correction.action == "undo"
        else "작업 흐름 경계를 사용자 확인으로 반영했습니다."
    )
    if enhanced:
        boundary = {
            "kind": str(assertion["boundary_kind"]),
            "source_episode_key": str(assertion["source_episode_key"]),
            "target_episode_key": assertion["target_episode_key"],
        }
        if boundary["kind"] == "relation":
            boundary["relation_id"] = workflow_relation_id(
                boundary["source_episode_key"],
                str(boundary["target_episode_key"]),
            )
        return _workflow_vary(
            JSONResponse(
                {
                    "status": "ok",
                    "code": result_code,
                    "message": result_message,
                    "reload_url": "/sessions/{}/workflow".format(session_id),
                    "boundary": boundary,
                }
            )
        )
    redirect_result = "undone" if correction.action == "undo" else "corrected"
    return _workflow_vary(
        RedirectResponse(
            "/sessions/{}/workflow?workflow_result={}#workflow-correction-feedback".format(
                session_id, redirect_result
            ),
            status_code=303,
        )
    )
