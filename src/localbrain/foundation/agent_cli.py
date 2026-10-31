"""Resolve explicitly selected local agent executables without starting them."""

import os
import shutil
from pathlib import Path
from typing import Optional


def runner_executable(runner: str = "claude") -> Optional[str]:
    if runner not in {"claude", "codex"}:
        return None
    configured = os.environ.get(
        "LOCALBRAIN_CLAUDE_BIN" if runner == "claude" else "LOCALBRAIN_CODEX_BIN"
    )
    if configured:
        path = Path(configured).expanduser()
        return str(path) if path.is_file() else None
    return shutil.which(runner)
