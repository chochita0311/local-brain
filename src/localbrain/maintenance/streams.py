"""Shared runner stream and structured-output decoding."""

import json
from pathlib import Path
from typing import Optional

def _structured_result(event: Optional[dict]) -> Optional[dict]:
    if not event:
        return None
    value = event.get("structured_output")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    result = event.get("result")
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


async def _consume_stderr(stream, stderr_path: Path) -> str:
    chunks = []
    with stderr_path.open("a", encoding="utf-8") as output:
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace")
            output.write(decoded)
            output.flush()
            chunks.append(decoded)
    return "".join(chunks)
