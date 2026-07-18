import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DATA_DIR = Path.home() / "Library" / "Application Support" / "LocalBrain"


def _system_timezone_name() -> str:
    configured = os.environ.get("TZ")
    if configured:
        return configured
    try:
        resolved = str(Path("/etc/localtime").resolve())
        marker = "/zoneinfo/"
        if marker in resolved:
            return resolved.split(marker, 1)[1]
    except OSError:
        pass
    return "UTC"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_path: Path
    context_root: Path
    claude_root: Path
    codex_root: Path
    mcp_call_budget: int
    timezone_name: str = "UTC"


def load_settings() -> Settings:
    data_dir = Path(
        os.environ.get("LOCALBRAIN_DATA_DIR", str(DEFAULT_DATA_DIR))
    ).expanduser()
    try:
        mcp_call_budget = max(0, int(os.environ.get("LOCALBRAIN_MCP_CALL_BUDGET", "20")))
    except ValueError:
        mcp_call_budget = 20
    return Settings(
        data_dir=data_dir,
        database_path=data_dir / "localbrain.db",
        context_root=Path(
            os.environ.get(
                "LOCALBRAIN_CONTEXT_ROOT", str(Path.home() / "Projects" / "context")
            )
        ).expanduser(),
        claude_root=Path(
            os.environ.get(
                "LOCALBRAIN_CLAUDE_ROOT", str(Path.home() / ".claude" / "projects")
            )
        ).expanduser(),
        codex_root=Path(
            os.environ.get(
                "LOCALBRAIN_CODEX_ROOT", str(Path.home() / ".codex" / "sessions")
            )
        ).expanduser(),
        mcp_call_budget=mcp_call_budget,
        timezone_name=os.environ.get(
            "LOCALBRAIN_TIMEZONE", _system_timezone_name()
        ),
    )


settings = load_settings()
