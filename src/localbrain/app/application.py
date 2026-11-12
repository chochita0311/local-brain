"""Application composition and lifecycle wiring."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from localbrain import __version__
from localbrain.foundation.config import settings
from localbrain.foundation.paths import package_root
from .edition import DESKTOP, install_boundary
from .lifecycle import lifespan
from .templating import templates
from .reference_integrations import install_reference_integrations
from .features import DEFAULT_FEATURE_PACKAGES, available_feature_packages


def create_app(*, feature_packages=DEFAULT_FEATURE_PACKAGES):
    """Compose the installed features; the argument also supports isolated fixtures.

    This is an internal assembly boundary, not a user preference or an import
    fallback. Production entrypoints use the explicit current delivery set.
    """
    feature_packages = available_feature_packages(feature_packages, desktop=DESKTOP)
    from .settings import install_settings_routes
    from .docs import install_routes as install_app_docs_routes
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
    app.state.google_drive_factory = None
    if "google_drive" in feature_packages:
        from localbrain.google_drive.service import start_service
        app.state.google_drive_factory = start_service
    app.state.external_read_executor = None
    app.mount("/static", StaticFiles(directory=package_root() / "static"), name="static")
    install_settings_routes(app, templates)
    if "terminal" in feature_packages:
        from localbrain.terminal.web import install_routes as install_terminal_routes
        install_terminal_routes(app, templates, settings)
    if "google_drive" in feature_packages:
        from localbrain.google_drive.web import install_routes as install_google_drive_routes
        install_google_drive_routes(app)
    if "context_search" in feature_packages:
        from localbrain.context_search.web import install_routes as install_context_search_routes
        install_context_search_routes(app, templates)
    if not DESKTOP:
        from localbrain.learning.web import install_routes as install_learning_routes
        install_learning_routes(app, templates)
    install_app_docs_routes(app, templates)
    install_routes(app)
    return app
