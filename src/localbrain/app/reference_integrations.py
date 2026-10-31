"""Application-owned composition of optional reference consumers/producers."""

from functools import wraps

from localbrain.ingest.extensions import observe_ingestion


def default_ingestion_observers():
    from localbrain.atlassian.ingestion import AtlassianIngestion
    return (AtlassianIngestion(),)


def with_ingestion_observers(scan, observers):
    @wraps(scan)
    def composed(*args, **kwargs):
        with observe_ingestion(observers):
            return scan(*args, **kwargs)
    return composed


def install_reference_integrations(
    app, *, atlassian=True, workstreams=True, workflow=True, natural_search=True,
):
    app.state.ingestion_observers = default_ingestion_observers() if atlassian else ()
    app.state.document_memberships = None
    app.state.add_organization_link = None
    app.state.remove_organization_link = None
    app.state.session_workflow_available = None
    app.state.search_return = None
    if workstreams:
        from localbrain.workstreams.service import entity_memberships, add_link, remove_link
        app.state.document_memberships = entity_memberships
        app.state.add_organization_link = add_link
        app.state.remove_organization_link = remove_link
    if workflow:
        from localbrain.workflow.focus import workflow_session_is_eligible
        app.state.session_workflow_available = workflow_session_is_eligible
    if natural_search:
        from localbrain.natural_search.presentation import safe_return
        app.state.search_return = safe_return

    @app.middleware("http")
    async def reference_integrations(request, call_next):
        with observe_ingestion(request.app.state.ingestion_observers):
            return await call_next(request)
