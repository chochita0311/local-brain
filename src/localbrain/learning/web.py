"""Server-rendered learning routes with native forms and no model side effects."""

from __future__ import annotations

import re
import secrets
import sqlite3
from contextlib import closing
from typing import Optional
from urllib.parse import parse_qs

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool

from localbrain.learning import service as learning
from localbrain.foundation.config import settings
from localbrain.persistence.db import connect
from localbrain.rendering.markdown import highlight_code, render_markdown


HEADERS = {"Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff",
           "Referrer-Policy": "no-referrer"}


def _local(request: Request):
    if request.url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise HTTPException(400, "Local access required")
    if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
        raise HTTPException(400, "Local access required")


async def _form(request: Request, allowed: set[str]) -> dict:
    _local(request)
    if request.headers.get("origin") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Same-origin submission required")
    if request.headers.get("content-type", "").split(";", 1)[0].strip() != "application/x-www-form-urlencoded":
        raise HTTPException(415, "URL-encoded form required")
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 100_000:
            raise HTTPException(413, "Form is too large")
        chunks.append(chunk)
    try:
        values = parse_qs(b"".join(chunks).decode("utf-8"), keep_blank_values=True,
                          max_num_fields=12, errors="strict")
    except (UnicodeError, ValueError):
        raise HTTPException(400, "Invalid form") from None
    if set(values) - allowed or any(len(value) != 1 for value in values.values()):
        raise HTTPException(400, "Invalid form fields")
    return {key: value[0] for key, value in values.items()}


def _render(templates, name, request, data, status=200):
    return templates.TemplateResponse(name, {"request": request, "active_page": "dashboard", **data},
                                      status_code=status, headers=HEADERS)


def _present_note(lesson):
    """Derive article presentation without changing its immutable source packet."""
    lesson["read_key"] = secrets.token_hex(16)
    article = lesson.get("article")
    references = article["source_ids"] if article else [source["id"] for source in lesson["sources"]]
    lesson["article_references"] = [{**source, "number": index + 1} for index, source in enumerate(
        source for source in lesson["sources"] if source["kind"] == "official" and source["id"] in references
    )]
    if article:
        lesson["article_intro"] = render_markdown(article["intro"]).html
        lesson["article_takeaway"] = render_markdown(article["takeaway"]).html
        lesson["article_sections"] = [{**section, "html": render_markdown(section["body"]).html,
            "references": [source for source in lesson["article_references"] if source["id"] in section["source_ids"]]}
            for section in article["sections"]]
    if scene := lesson.get("scene"):
        lines = scene["code"].splitlines()
        start, end = article["code_range"] if article else (1, min(6, len(lines)))
        lesson["preview_start"], lesson["preview_end"] = start, end
        lesson["preview_partial"] = start > 1 or end < len(lines)
        lesson["code_numbers"] = "\n".join(str(number) for number in range(start, end + 1))
        # Human language labels are not lexer identifiers. Never guess from code.
        labels = re.split(r"[\s/]+", scene["language"].lower())
        language = "diff" if scene["kind"] == "diff" else next(
            (label for label in labels if label in {"bash", "sh", "shell", "zsh", "console"}), "text")
        lesson["code_preview_html"] = highlight_code("\n".join(lines[start - 1:end]), language)


def render_home(request: Request, templates):
    _local(request)
    with closing(connect()) as connection:
        data = learning.daily_selection(connection, settings.timezone_name)
    for lesson in data["selected_lessons"]:
        _present_note(lesson)
    data["note_return"] = "home"
    return _render(templates, "dashboard.html", request, data)


def install_routes(app, templates):
    def render_reader(request, lesson_id, attempt_id=None, *, question_id=None, error=None, values=None, status=200):
        try:
            with closing(connect()) as connection:
                data = learning.reader(connection, lesson_id, settings.timezone_name, attempt_id,
                                       values.get("question_id") if values else question_id)
        except learning.LearningError as failure:
            return _render(templates, "learning-reader.html", request, {"missing": str(failure)}, 404)
        note_practice = (values.get("from_note") if values else request.query_params.get("from_note")) == "1"
        data.update({"error": error, "values": values or {}, "submission_key": secrets.token_hex(16),
                     "read_key": secrets.token_hex(16), "note_practice": note_practice,
                     "hint_used": note_practice or request.query_params.get("hint") == "1"})
        if values:
            # Keep the originally submitted question and text on validation/save failure.
            data["question"] = next((q for q in data["lesson"]["questions"]
                                     if q["id"] == values.get("question_id")), data["question"])
            data["submission_key"] = values.get("submission_key") or data["submission_key"]
            data["hint_used"] = note_practice or values.get("hint_used") == "1"
        return _render(templates, "learning-reader.html", request, data, status)

    def render_library(request, error=None, status=200):
        with closing(connect()) as connection:
            items = learning.library(connection, settings.timezone_name)
        return _render(templates, "learning-library.html", request,
                       {"lessons": items, "error": error,
                        "notice": "목록 표시를 변경했습니다." if request.query_params.get("updated") == "1" else None}, status)

    @app.get("/learning")
    def learning_library(request: Request):
        _local(request)
        return render_library(request)

    @app.get("/learning/{lesson_id}")
    def learning_reader(request: Request, lesson_id: int, attempt: Optional[int] = None,
                        question: Optional[str] = None):
        _local(request)
        return render_reader(request, lesson_id, attempt, question_id=question)

    @app.get("/learning/{lesson_id}/note")
    def learning_note(request: Request, lesson_id: int):
        _local(request)
        try:
            with closing(connect()) as connection:
                data = learning.reader(connection, lesson_id, settings.timezone_name)
        except learning.LearningError as error:
            return _render(templates, "learning-reader.html", request, {"missing": str(error)}, 404)
        lesson = data["lesson"]
        lesson["question"] = data["question"]
        lesson["pending"] = data["attempt"]["id"] if data["attempt"] and data["attempt"]["outcome"] == "pending" else None
        lesson["done_today"] = any(item["assessed_at"] and learning.local_day(item["assessed_at"], settings.timezone_name)
                                   == learning.today(settings.timezone_name) for item in data["history"])
        _present_note(lesson)
        data["note_return"] = "note"
        return _render(templates, "learning-note.html", request, data)

    @app.post("/learning/{lesson_id}/attempts")
    async def learning_submit(request: Request, lesson_id: int):
        fields = await _form(request, {"question_id", "submission_key", "action", "answer", "confidence", "hint_used", "from_note", "return_to"})
        if fields.get("from_note") == "1":
            fields["hint_used"] = "1"

        def save():
            with closing(connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                return learning.submit_attempt(connection, lesson_id, fields)

        try:
            attempt_id = await run_in_threadpool(save)
        except learning.LearningError as error:
            return await run_in_threadpool(render_reader, request, lesson_id, error=str(error), values=fields, status=422)
        except sqlite3.Error:
            return await run_in_threadpool(render_reader, request, lesson_id, values=fields, status=503,
                                           error="저장하지 못했습니다. 입력한 답변을 확인하고 다시 제출해 주세요.")
        if fields.get("action") == "read" and fields.get("return_to") == "home":
            return RedirectResponse("/#today-title", 303, headers=HEADERS)
        if fields.get("action") == "read" and fields.get("return_to") == "note":
            return RedirectResponse(f"/learning/{lesson_id}/note#article-finish", 303, headers=HEADERS)
        return RedirectResponse(f"/learning/{lesson_id}?attempt={attempt_id}#feedback", 303, headers=HEADERS)

    @app.post("/learning/{lesson_id}/assess")
    async def learning_assess(request: Request, lesson_id: int):
        fields = await _form(request, {"attempt_id", "outcome"})
        try:
            attempt_id = int(fields.get("attempt_id", ""))
        except ValueError:
            raise HTTPException(400, "Invalid attempt") from None
        if not 0 < attempt_id < 2**63:
            raise HTTPException(400, "Invalid attempt")

        def save():
            with closing(connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                learning.assess_attempt(connection, lesson_id, attempt_id, fields.get("outcome"))

        try:
            await run_in_threadpool(save)
        except learning.LearningError as error:
            return await run_in_threadpool(render_reader, request, lesson_id, attempt_id, error=str(error), status=422)
        except sqlite3.Error:
            return await run_in_threadpool(render_reader, request, lesson_id, attempt_id, status=503,
                                           error="자기 평가를 저장하지 못했습니다. 선택한 평가를 다시 제출해 주세요.")
        return RedirectResponse(f"/learning/{lesson_id}?attempt={attempt_id}#feedback", 303, headers=HEADERS)

    @app.post("/learning/{lesson_id}/visibility")
    async def learning_visibility(request: Request, lesson_id: int):
        fields = await _form(request, {"action"})

        def save():
            with closing(connect()) as connection, connection:
                learning.set_visibility(connection, lesson_id, fields.get("action"), settings.timezone_name)

        try:
            await run_in_threadpool(save)
        except learning.LearningError as error:
            return await run_in_threadpool(render_library, request, str(error), 422)
        except sqlite3.Error:
            return await run_in_threadpool(render_library, request, "표시 설정을 저장하지 못했습니다. 다시 시도해 주세요.", 503)
        return RedirectResponse("/learning?updated=1", 303, headers=HEADERS)
