"""Application composition and lifecycle wiring."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from localbrain import __version__
from localbrain.foundation.config import settings
from localbrain.foundation.paths import package_root
from .edition import install_boundary
from .lifecycle import lifespan
from .templating import templates
from .reference_integrations import install_reference_integrations
from .features import DEFAULT_FEATURE_PACKAGES


def create_app(*, feature_packages=DEFAULT_FEATURE_PACKAGES):
    """Compose the installed features; the argument also supports isolated fixtures.

    This is an internal assembly boundary, not a user preference or an import
    fallback. Production entrypoints use the complete explicit default set.
    """
    feature_packages = frozenset(feature_packages)
    if not feature_packages <= DEFAULT_FEATURE_PACKAGES:
        raise ValueError("Unknown application feature package")
    from .settings import install_settings_routes
    from .docs import install_routes as install_app_docs_routes
    from localbrain.google_drive.web import install_routes as install_google_drive_routes
    from localbrain.learning.web import install_routes as install_learning_routes
    from .routes import install_routes

    app = FastAPI(title="LocalBrain", version=__version__, lifespan=lifespan)
    app.state.feature_packages = feature_packages
    install_boundary(app, settings)
    install_reference_integrations(
        app, atlassian="atlassian" in feature_packages,
        workstreams="workstreams" in feature_packages,
        workflow="workflow" in feature_packages,
    )
    app.state.task_runner = None
    if feature_packages & {"atlassian", "workstreams"}:
        from localbrain.maintenance import service as task_runner
        app.state.task_runner = task_runner
    app.state.maintain_feature_cache = None
    if "auto_work" in feature_packages:
        from localbrain.auto_work.storage import maintain_cache
        app.state.maintain_feature_cache = maintain_cache
    app.state.context_search_factory = None
    if "context_search" in feature_packages:
        from localbrain.context_search.service import ContextSearchService
        app.state.context_search_factory = ContextSearchService
    app.state.external_read_executor = None
    app.mount("/static", StaticFiles(directory=package_root() / "static"), name="static")
    install_settings_routes(app, templates)
    install_google_drive_routes(app)
    if "context_search" in feature_packages:
        from localbrain.context_search.web import install_routes as install_context_search_routes
        install_context_search_routes(app, templates)
    install_learning_routes(app, templates)
    install_app_docs_routes(app, templates)
    install_routes(app)
    return app
