"""Rust validates terminal defaults; the shared Python transaction alone commits TOML."""
import hashlib

from localbrain.foundation.operations import OperationBusy, operation_lock
from localbrain.foundation.preferences import PreferencesError, atomic_private_write, read_preferences, toml_text
from .core import TerminalService


def _snapshot(current):
    raw = current["raw"]
    values = raw.get("terminal", {})
    section = {"kind": "missing" if "terminal" not in raw else "table" if isinstance(values, dict) else "invalid"}
    for key in ("cwd", "shell"):
        if not isinstance(values, dict) or key not in values:
            section[key] = {"kind": "missing"}
        elif isinstance(values[key], str):
            section[key] = {"kind": "string", "value": values[key]}
        else:
            section[key] = {"kind": "invalid"}
    return {"revision": current["revision"], "section": section}


def read_launch_settings(config):
    current = read_preferences(config)
    result = TerminalService(config).call("settings.read", _snapshot(current))
    result["preferences"] = {key: current[key] for key in ("saved", "effective", "source", "revision")}
    return result


def launch_parameters(config, *, cwd=None):
    arguments = _snapshot(read_preferences(config))
    if cwd is not None:
        arguments["cwdOverride"] = cwd
    return TerminalService(config).call("settings.launch", arguments)


def save_launch_settings(config, cwd, shell, revision):
    try:
        with operation_lock(config, "settings"):
            current = read_preferences(config)
            if revision != current["revision"]:
                raise PreferencesError("다른 창에서 설정이 변경되었습니다. 다시 불러온 뒤 저장해 주세요.")
            control = TerminalService(config)
            prepared = control.call("settings.prepare", {**_snapshot(current), "cwd": cwd, "shell": shell})
            expected_scope = hashlib.sha256((control.context["dataDir"] + "\0" + control.context["cacheDir"]).encode()).hexdigest()
            if (set(prepared) != {"revision", "scopeHash", "patch"} or prepared["revision"] != revision
                    or prepared["scopeHash"] != expected_scope or set(prepared["patch"]) != {"cwd", "shell"}
                    or any(not isinstance(value, str) for value in prepared["patch"].values())):
                raise PreferencesError("터미널 설정 응답을 확인하지 못했습니다. 기존 파일을 보존했습니다.")
            values = current["raw"].get("terminal", {})
            raw = {**current["raw"], "terminal": {**values, **prepared["patch"]}}
            ordered = {"schema_version": 1, "onboarding_completed": current["saved"]["onboarding_completed"], **raw}
            atomic_private_write(config.data_dir / "settings.toml", toml_text(ordered).encode("utf-8"))
            return read_launch_settings(config)
    except OperationBusy:
        raise PreferencesError("설정을 저장하는 중입니다. 잠시 후 다시 시도해 주세요.") from None
