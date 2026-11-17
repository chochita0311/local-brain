"""Shared view preferences; these never own or restore terminal processes."""
import json
import os
import re
import stat

from localbrain.foundation.preferences import atomic_private_write
from localbrain.foundation.private_json import read_json


class PresentationError(ValueError):
    pass


def _path(root):
    info = root.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o077):
        raise PresentationError("탭 순서 저장 위치를 확인해 주세요.")
    return root / "view-order.json"


def _read(root):
    path = _path(root)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if info.st_size > 16 * 1024:
        raise PresentationError("저장한 탭 순서를 읽을 수 없습니다.")
    value = read_json(path)
    if (not isinstance(value, dict) or set(value) != {"schema", "generation", "tabs"}
            or type(value["schema"]) is not int or value["schema"] != 1
            or not isinstance(value["generation"], str)
            or not re.fullmatch(r"[a-f0-9]{32}", value["generation"])
            or not isinstance(value["tabs"], list) or len(value["tabs"]) > 32
            or any(not isinstance(item, str) or len(item) > 128 for item in value["tabs"])
            or len(set(value["tabs"])) != len(value["tabs"])):
        raise PresentationError("저장한 탭 순서를 읽을 수 없습니다.")
    return value


def load_order(root, generation, tabs):
    ids = [tab["id"] for tab in tabs]
    if not generation or not ids:
        return {"order": ids}
    try:
        value = _read(root)
        saved = value["tabs"] if value and value["generation"] == generation else []
        return {"order": [item for item in saved if item in ids]
                + [item for item in ids if item not in saved]}
    except (OSError, ValueError):
        return {"order": ids, "error": "저장한 탭 순서를 읽지 못했습니다."}


def save_order(root, generation, tabs, order):
    ids = [tab["id"] for tab in tabs]
    if (not isinstance(order, list) or len(order) != len(ids)
            or not isinstance(generation, str) or not re.fullmatch(r"[a-f0-9]{32}", generation)
            or any(not isinstance(item, str) for item in order)
            or len(set(order)) != len(order) or set(order) != set(ids)):
        raise PresentationError("탭 목록이 바뀌었습니다. 다시 이동해 주세요.")
    path = _path(root)
    previous = _read(root)
    saved = previous["tabs"] if previous and previous["generation"] == generation else []
    current = [item for item in saved if item in ids] + [item for item in ids if item not in saved]
    by_id = {tab["id"]: tab for tab in tabs}
    for before, after in zip(current, order):
        first, second = by_id[before], by_id[after]
        if first.get("workspaceId", first.get("cwd")) != second.get("workspaceId", second.get("cwd")) or (before != after and (first.get("hidden") or second.get("hidden"))):
            raise PresentationError("작업 공간이나 백그라운드 탭은 함께 이동할 수 없습니다.")
    atomic_private_write(path, json.dumps({"schema": 1, "generation": generation, "tabs": order},
                                       ensure_ascii=False, separators=(",", ":")).encode())
    return {"generation": generation, "order": order}
