from fastapi.templating import Jinja2Templates
from localbrain import __version__
from localbrain.foundation.config import settings
from localbrain.foundation.paths import home_relative_path, package_root
from localbrain.foundation.preferences import presentation_preferences
from localbrain.app.edition import DESKTOP
from localbrain.persistence.db import connect
from localbrain.persistence.value_registry import display_value_label, visible_value_help
from localbrain.sources.profiles import profile_map

PACKAGE_ROOT = package_root()

def _profile_context(request):
    snapshot = None
    def source_profile(reference):
        nonlocal snapshot
        if snapshot is None:
            with connect() as connection:
                snapshot = profile_map(connection)
        return snapshot.get(str(reference), {"id": None, "name": "Session", "provider_kind": "", "color": "gray"})
    def feature_available(name):
        app = request.scope.get("app")
        selected = getattr(app.state, "feature_packages", None) if app else None
        return selected is None or name in selected
    return {
        "source_profile": source_profile,
        "auto_work_package_available": feature_available("auto_work"),
        "workstreams_available": feature_available("workstreams"),
        "atlassian_available": feature_available("atlassian"),
        "context_search_available": feature_available("context_search"),
    }

templates = Jinja2Templates(directory=PACKAGE_ROOT / "templates", context_processors=[_profile_context])
templates.env.globals["asset_version"] = max(
    path.stat().st_mtime_ns
    for path in (PACKAGE_ROOT / "static").iterdir()
    if path.is_file()
)
templates.env.globals["value_label"] = display_value_label
templates.env.globals["value_help"] = visible_value_help
templates.env.globals["auto_work_available"] = not DESKTOP
templates.env.globals["desktop_edition"] = DESKTOP
templates.env.globals["app_version"] = __version__
templates.env.globals["local_preferences"] = lambda: presentation_preferences(settings)
templates.env.filters["project_path"] = lambda path: home_relative_path(path) or "미지정"
