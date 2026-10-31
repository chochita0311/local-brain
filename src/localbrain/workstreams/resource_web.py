"""Workstream-owned resource registration and membership mutations."""
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel, Field
from localbrain.persistence.db import transaction
from localbrain.resources.store import create_external_resource, create_local_resource
from localbrain.workstreams.service import add_link


class ExternalResourceCreate(BaseModel):
    resource_type: str
    title: str = Field(min_length=1, max_length=240)
    url: str = Field(min_length=1, max_length=2000)
    summary: Optional[str] = Field(default=None, max_length=4000)
    source_role: Optional[str] = Field(default=None, max_length=160)
    scope_type: str
    scope_id: int
    relation_type: str = Field(default="reference", min_length=1, max_length=80)


class LocalResourceCreate(BaseModel):
    path: str = Field(min_length=1, max_length=4000)
    title: Optional[str] = Field(default=None, max_length=240)
    summary: Optional[str] = Field(default=None, max_length=4000)
    scope_type: str
    scope_id: int
    relation_type: str = Field(default="reference", min_length=1, max_length=80)


def api_create_external_resource(payload: ExternalResourceCreate):
    try:
        with transaction() as connection:
            resource_id = create_external_resource(
                connection,
                payload.resource_type,
                payload.title,
                payload.url,
                payload.summary,
                payload.source_role,
            )
            add_link(
                connection,
                payload.scope_type,
                payload.scope_id,
                "external",
                str(resource_id),
                payload.relation_type,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "id": resource_id}


def api_create_local_resource(payload: LocalResourceCreate):
    try:
        with transaction() as connection:
            resource_id = create_local_resource(
                connection,
                payload.path,
                payload.title,
                payload.summary,
            )
            add_link(
                connection,
                payload.scope_type,
                payload.scope_id,
                "local",
                str(resource_id),
                payload.relation_type,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "id": resource_id}
