"""Durable workspace identity; manager generations alone own live tab membership."""
import copy
import hashlib
import json
import re
import uuid

from localbrain.foundation.files import StorageError, private_directory, validate_runtime_directory
from localbrain.foundation.operations import OperationBusy, operation_lock
from localbrain.foundation.preferences import PreferencesError, atomic_private_write
from localbrain.foundation.private_json import read_json

MAX_WORKSPACES = 128


class WorkspaceError(PreferencesError):
    pass


def _empty():
    return {"schema": 1, "generation": None, "items": []}


def _path(config):
    try:
        return validate_runtime_directory(config.data_dir) / "terminal-workspaces.json"
    except StorageError as error:
        raise WorkspaceError("작업공간 저장 위치를 확인해 주세요.") from error


def validate_document(value):
    """Validate saved metadata and recovery input without touching runtime state."""
    if (not isinstance(value, dict) or set(value) != {"schema", "generation", "items"}
            or type(value["schema"]) is not int or value["schema"] != 1
            or (value["generation"] is not None and not _id(value["generation"]))
            or not isinstance(value["items"], list) or len(value["items"]) > MAX_WORKSPACES):
        raise WorkspaceError("저장한 작업공간을 확인해 주세요.")
    ids, tabs = set(), set()
    for item in value["items"]:
        if (not isinstance(item, dict) or set(item) != {"id", "name", "cwd", "tabs"}
                or not _id(item["id"]) or item["id"] in ids
                or not isinstance(item["name"], str) or not item["name"].strip() or len(item["name"]) > 120
                or not isinstance(item["cwd"], str) or len(item["cwd"]) > 4096 or "\0" in item["cwd"]
                or (item["cwd"] and not item["cwd"].startswith("/"))
                or not isinstance(item["tabs"], list) or len(item["tabs"]) > 32
                or any(not isinstance(tab, str) or not tab or len(tab) > 128 or tab in tabs for tab in item["tabs"])
                or len(set(item["tabs"])) != len(item["tabs"])):
            raise WorkspaceError("저장한 작업공간을 확인해 주세요.")
        ids.add(item["id"]); tabs.update(item["tabs"])
    if len(tabs) > 32:
        raise WorkspaceError("저장한 작업공간의 탭 목록을 확인해 주세요.")
    return value


def _id(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{32}", value) is not None


def _read(config):
    path = _path(config)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return _empty()
    if info.st_size > 2 * 1024 * 1024:
        raise WorkspaceError("저장한 작업공간이 너무 큽니다.")
    return validate_document(read_json(path))


def _legacy_id(cwd):
    return hashlib.sha256(("terminal-workspace\0" + cwd).encode()).hexdigest()[:32]


def _project(saved, state, exclude=()):
    value = copy.deepcopy(saved)
    value["generation"] = state.get("generation")
    current = {tab["id"] for tab in state["tabs"]}
    for item in value["items"]:
        item["tabs"] = ([tab for tab in item["tabs"] if tab in current and tab not in exclude]
                        if saved["generation"] == value["generation"] else [])
    assigned = {tab for item in value["items"] for tab in item["tabs"]}
    for tab in state["tabs"]:
        if tab["id"] in assigned or tab["id"] in exclude:
            continue
        cwd = tab.get("cwd") or next((term["cwd"] for term in state["terminals"] if term["id"] in tab["terminals"]), "")
        identity = _legacy_id(cwd)
        item = next((item for item in value["items"] if item["id"] == identity), None)
        if item is None:
            item = {"id": identity, "name": (cwd.rstrip("/").rsplit("/", 1)[-1] or "작업공간")[:120], "cwd": cwd, "tabs": []}
            value["items"].append(item)
        item["tabs"].append(tab["id"])
    return value


def read_workspaces(config, state):
    try:
        saved = _read(config)
        projected = _project(saved, state)
        return {"items": projected["items"], "needsSave": saved != projected and bool(saved["items"] or state["tabs"])}
    except (OSError, ValueError) as error:
        return {"items": _project(_empty(), state)["items"], "needsSave": False,
                "error": "작업공간을 읽지 못했습니다. 기존 저장 파일을 확인해 주세요."}


def change_workspaces(config, read_state, action, body):
    try:
        with operation_lock(config, "terminal-workspaces"):
            state = read_state()
            if "generation" in body and body["generation"] != state.get("generation"):
                raise WorkspaceError("터미널 서비스가 바뀌었습니다. 다시 시도해 주세요.")
            saved = _read(config)
            tab_id = body.get("tabId")
            value = _project(saved, state, (tab_id,) if action in {"attach", "move"} else ())
            item = next((item for item in value["items"] if item["id"] == body.get("id")), None)
            if action == "create":
                if len(value["items"]) >= MAX_WORKSPACES:
                    raise WorkspaceError("작업공간 한도에 도달했습니다. 빈 작업공간을 목록에서 제거해 주세요.")
                item = {"id": uuid.uuid4().hex, "name": body["name"].strip(), "cwd": body["cwd"], "tabs": []}
                value["items"].append(item)
            elif action in {"update", "remove", "attach", "move"}:
                if action in {"attach", "move"}:
                    if not any(tab["id"] == tab_id for tab in state["tabs"]):
                        raise WorkspaceError("탭 목록이 바뀌었습니다. 다시 확인해 주세요.")
                    owner = next((entry for entry in saved["items"] if tab_id in entry["tabs"]), None) if saved["generation"] == state.get("generation") else None
                    if action == "attach" and owner and body.get("id") and owner["id"] != body["id"]:
                        raise WorkspaceError("이 탭은 다른 작업공간에 있습니다. 탭 이동을 사용해 주세요.")
                    if not body.get("id"):
                        item = next((entry for entry in value["items"] if owner and entry["id"] == owner["id"]), None)
                        if item is None:
                            value = _project(saved, state)
                            item = next(entry for entry in value["items"] if tab_id in entry["tabs"])
                    if item is not None and tab_id not in item["tabs"]:
                        item["tabs"].append(tab_id)
                if item is None:
                    raise WorkspaceError("작업공간을 찾지 못했습니다. 목록을 다시 확인해 주세요.")
                if action == "update":
                    item["name"] = body["name"].strip()
                    item["cwd"] = body["cwd"]
                elif action == "remove":
                    if item["tabs"]:
                        raise WorkspaceError("터미널을 모두 종료한 빈 작업공간만 목록에서 제거할 수 있습니다.")
                    value["items"].remove(item)
            elif action != "reconcile":
                raise WorkspaceError("작업공간 요청을 확인해 주세요.")
            validate_document(value)
            if saved != value:
                private_directory(config.data_dir)
                atomic_private_write(_path(config), json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())
            return {"items": value["items"], "needsSave": False, "id": item["id"] if item else None}
    except OperationBusy as error:
        raise WorkspaceError("다른 로컬 작업이 저장 중입니다. 잠시 후 다시 시도해 주세요.") from error
    except StorageError as error:
        raise WorkspaceError("작업공간 저장 위치를 확인해 주세요.") from error
