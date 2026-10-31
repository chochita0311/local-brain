from typing import Optional
from fastapi import HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
)
from pydantic import BaseModel, Field, StrictInt
from localbrain.foundation.config import settings
from localbrain.foundation.operations import operation_lock
from localbrain.local_context.service import (
    ContextOrderConflict,
    reorder_context_sources,
    add_apple_notes_source,
    add_context_file,
    add_context_root,
    context_document_preview,
    context_document_reader,
    context_source_tree,
    list_context_sources,
    remove_context_root,
)
from localbrain.persistence.db import connect, transaction
from localbrain.ingest.scanner import scan_context_root
from localbrain.local_context.queries import document_detail
from localbrain.app.templating import templates


class ContextRootCreate(BaseModel):
    path: str = Field(min_length=1, max_length=4000)


class ContextFileCreate(BaseModel):
    path: str = Field(min_length=1, max_length=4000)


class ContextSourceOrder(BaseModel):
    source_ids: list[StrictInt] = Field(max_length=10000)
    expected_source_ids: list[StrictInt] = Field(max_length=10000)


def context_page(
    request: Request,
    root: Optional[int] = Query(default=None),
    document: Optional[int] = Query(default=None),
):
    with connect() as connection:
        sources = list_context_sources(connection)
        folders = [
            item for item in sources
            if item["source_type"] in {"folder", "apple_notes"}
        ]
        files = [item for item in sources if item["source_type"] == "file"]
        selected_source = next(
            (item for item in sources if item["id"] == root), None
        )
        if selected_source is None and sources:
            selected_source = sources[0]
        selected_document = document_detail(connection, document) if document else None
        if (
            selected_document
            and selected_source
            and selected_document["context_root_id"] != selected_source["id"]
        ):
            selected_document = None
        if selected_source and selected_source["source_type"] == "file" and not selected_document:
            first_document = connection.execute(
                "SELECT id FROM context_documents WHERE context_root_id = ? LIMIT 1",
                (selected_source["id"],),
            ).fetchone()
            if first_document:
                selected_document = document_detail(connection, first_document["id"])
        if selected_document:
            selected_document = context_document_preview(connection, selected_document)
        tree = (
            context_source_tree(
                connection,
                selected_source["id"],
                selected_document["id"] if selected_document else None,
            )
            if selected_source else []
        )
    return templates.TemplateResponse(
        request, "context.html",
        {
            "request": request,
            "active_page": "context",
            "selected_source": selected_source,
            "selected_document": selected_document,
            "tree": tree,
            "folders": folders,
            "files": files,
            "has_apple_notes": any(
                item["source_type"] == "apple_notes" for item in folders
            ),
            "document_count": sum(item["document_count"] for item in sources),
            "source_count": len(sources),
            "total_bytes": sum(item["total_bytes"] or 0 for item in sources),
        },
    )


def show_document(request: Request, document_id: int):
    with connect() as connection:
        document = document_detail(connection, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        reader = context_document_reader(connection, document)
        membership_reader = getattr(request.app.state, "document_memberships", None)
        memberships = membership_reader(connection, "document", document_id) if membership_reader else []
    return templates.TemplateResponse(
        request, "document.html",
        {
            "request": request,
            "active_page": "context",
            **reader,
            "memberships": memberships,
            "search_return": request.app.state.search_return(request.query_params["search_return"]) if request.query_params.get("search_return") and getattr(request.app.state, "search_return", None) else None,
        },
    )


def api_add_context_root(payload: ContextRootCreate):
    try:
        with operation_lock(settings, "context-settings"), transaction() as connection:
            root_id = add_context_root(connection, payload.path)
            imported, skipped, failed = scan_context_root(
                connection, root_id, force=True
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "id": root_id,
        "report": {
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
        },
        "redirect": "/context?root={}".format(root_id),
    }


def api_add_context_file(payload: ContextFileCreate):
    try:
        with operation_lock(settings, "context-settings"), transaction() as connection:
            source_id = add_context_file(connection, payload.path)
            imported, skipped, failed = scan_context_root(
                connection, source_id, force=True
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "id": source_id,
        "report": {
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
        },
        "redirect": "/context?root={}".format(source_id),
    }


def api_add_apple_notes_source():
    with operation_lock(settings, "context-settings"), transaction() as connection:
        source_id = add_apple_notes_source(connection)
        imported, skipped, failed = scan_context_root(
            connection, source_id, force=True
        )
    return {
        "ok": True,
        "id": source_id,
        "report": {
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
        },
        "redirect": "/context?root={}".format(source_id),
    }


def api_reorder_context_sources(payload: ContextSourceOrder):
    try:
        with operation_lock(settings, "context-settings"), transaction(immediate=True) as connection:
            reorder_context_sources(connection, payload.source_ids, payload.expected_source_ids)
    except ContextOrderConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


def api_remove_context_root(root_id: int):
    try:
        with operation_lock(settings, "context-settings"), transaction() as connection:
            remove_context_root(connection, root_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


def api_remove_context_source(source_id: int):
    return api_remove_context_root(source_id)
