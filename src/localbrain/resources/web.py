from fastapi import HTTPException, Request
from localbrain.persistence.db import connect
from localbrain.resources.store import local_resource_detail
from localbrain.app.templating import templates


def show_local_resource(request: Request, resource_id: int):
    with connect() as connection:
        resource = local_resource_detail(connection, resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Local resource not found")
        membership_reader = getattr(request.app.state, "document_memberships", None)
        memberships = membership_reader(connection, "local", resource_id) if membership_reader else []
    return templates.TemplateResponse(
        request, "local_resource.html",
        {
            "request": request,
            "active_page": "context",
            "resource": resource,
            "memberships": memberships,
        },
    )
