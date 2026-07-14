from pathlib import Path
from typing import List, Optional

from .ingest.claude import parse_claude_session
from .ingest.common import ParsedSession


def subagent_root(source_path: str) -> Path:
    path = Path(source_path)
    return path.parent / path.stem / "subagents"


def list_subagents(source_path: str) -> List[dict]:
    root = subagent_root(source_path)
    if not root.is_dir():
        return []
    items = []
    for path in sorted(root.glob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            parsed = parse_claude_session(path)
        except Exception:
            continue
        items.append(
            {
                "file_name": path.name,
                "agent_id": path.stem.removeprefix("agent-"),
                "title": parsed.title,
                "last_event_at": parsed.last_event_at,
                "event_count": len(parsed.events),
            }
        )
    return items


def load_subagent(source_path: str, file_name: str) -> Optional[ParsedSession]:
    if Path(file_name).name != file_name or not file_name.endswith(".jsonl"):
        return None
    root = subagent_root(source_path)
    candidate = root / file_name
    if not candidate.is_file() or candidate.parent != root:
        return None
    return parse_claude_session(candidate)
