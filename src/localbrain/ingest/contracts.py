"""Lightweight ingestion contracts shared by adapters and their consumers."""

CODEX_SESSION_REVISION = 12
CLAUDE_SESSION_REVISION = 7


class SessionRevisionError(RuntimeError):
    """The current runtime cannot safely replace this source's Session results."""

