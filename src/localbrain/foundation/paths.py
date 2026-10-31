"""Local path labels and shared runtime/cache boundaries."""

import os
from pathlib import Path
from typing import Optional, Union


def home_relative_path(path: Optional[Union[str, Path]]) -> str:
    """Abbreviate only this user's home; retain the recorded suffix and identity."""
    if not path:
        return ""
    value = str(path)
    home = str(Path.home())
    if value == home:
        return "~"
    if value.startswith(home + "/"):
        return "~" + value[len(home):]
    return value


def hub_cache_root():
    home = os.environ.get("HF_HOME") or str(
        Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "huggingface")
    return Path(os.environ.get("HF_HUB_CACHE") or os.environ.get("HUGGINGFACE_HUB_CACHE")
                or str(Path(home) / "hub")).expanduser().resolve()


def package_boundary():
    """Keep the original package-parent exclusion in source, wheel and frozen layouts."""
    return Path(__file__).resolve().parents[3]


def package_root():
    """Location of shared schema, templates, static files and bundled content."""
    return Path(__file__).resolve().parents[1]
