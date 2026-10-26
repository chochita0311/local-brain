"""Local path labels, independent of preferences and filesystem availability."""

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
