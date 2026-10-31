"""Common local preferences; domain stores retain their own values."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from localbrain.foundation.config import settings, _system_timezone_name
from localbrain.foundation.operations import operation_lock


class PreferencesError(ValueError):
    pass


def defaults(config=settings):
    timezone = _system_timezone_name() if config is settings else getattr(config, "timezone_name", "UTC")
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        timezone = "UTC"
    return dict(startup_screen="sessions", timezone=timezone,
                session_sync_enabled=True, session_sync_minutes=10,
                context_sync_enabled=True, context_sync_minutes=30,
                onboarding_completed=False)


def atomic_private_write(path, data):
    """Publish one complete file without exposing an incomplete saved value."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise PreferencesError("설정 파일의 심볼릭 링크는 저장 대상으로 사용할 수 없습니다.")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix="." + path.name + "-", delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def toml_text(value):
    """Serialize our small TOML shape while retaining unknown scalar fields."""
    def scalar(item):
        if isinstance(item, bool):
            return "true" if item else "false"
        if isinstance(item, str):
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, (int, float)):
            return str(item)
        if isinstance(item, (date, datetime, time)):
            return item.isoformat()
        if isinstance(item, list) and not any(isinstance(x, dict) for x in item):
            return "[" + ", ".join(scalar(x) for x in item) + "]"
        raise PreferencesError("기존 설정에 저장할 수 없는 값이 있습니다. 파일은 보존했습니다.")

    lines = []
    def table(values, prefix=""):
        for key, item in values.items():
            quoted = json.dumps(key, ensure_ascii=False)
            if not isinstance(item, dict) and not (isinstance(item, list) and item and isinstance(item[0], dict)):
                lines.append(quoted + " = " + scalar(item))
        for key, item in values.items():
            name = (prefix + "." if prefix else "") + json.dumps(key, ensure_ascii=False)
            if isinstance(item, dict):
                lines.extend(["", "[" + name + "]"])
                table(item, name)
            elif isinstance(item, list) and item and isinstance(item[0], dict):
                for entry in item:
                    if not isinstance(entry, dict):
                        raise PreferencesError("기존 설정에 저장할 수 없는 값이 있습니다. 파일은 보존했습니다.")
                    lines.extend(["", "[[" + name + "]]"])
                    table(entry, name)
    table(value)
    return "\n".join(lines) + "\n"


def _validate(values):
    if not isinstance(values["startup_screen"], str) or values["startup_screen"] not in {"sessions", "sessions-dashboard", "context"}:
        raise PreferencesError("시작 화면을 선택해 주세요.")
    if not isinstance(values["timezone"], str):
        raise PreferencesError("시간대는 IANA 이름으로 입력해 주세요.")
    try:
        ZoneInfo(values["timezone"])
    except (ZoneInfoNotFoundError, ValueError):
        raise PreferencesError("올바른 시간대를 입력해 주세요. 예: Asia/Seoul") from None
    for key in ("session_sync_enabled", "context_sync_enabled", "onboarding_completed"):
        if not isinstance(values[key], bool):
            raise PreferencesError("켜기/끄기 값을 확인해 주세요.")
    for key in ("session_sync_minutes", "context_sync_minutes"):
        if type(values[key]) is not int or not 10 <= values[key] <= 1440:
            raise PreferencesError("동기화 간격은 10분부터 1,440분 사이의 정수로 입력해 주세요.")


def read_preferences(config=settings):
    path = config.data_dir / "settings.toml"
    try:
        content = path.read_bytes() if path.exists() else b""
        raw = tomllib.loads(content.decode("utf-8")) if content else {"schema_version": 1}
    except (OSError, ValueError, UnicodeError) as error:
        raise PreferencesError("로컬 설정을 읽지 못했습니다. 기존 파일을 확인해 주세요.") from error
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        raise PreferencesError("이 앱이 지원하지 않는 설정 버전입니다. 기존 파일을 보존합니다.")
    base = defaults(config)
    saved = {key: raw.get(key, value) for key, value in base.items()}
    _validate(saved)
    source = {key: "saved" if key in raw else "default" for key in base}
    # Keep the response shape compatible; the file plus missing-field defaults
    # is the single value set used by every consumer.
    return dict(saved=saved, effective=dict(saved), source=source,
                revision=hashlib.sha256(content).hexdigest(), raw=raw)


def save_preferences(changes, revision, config=settings):
    if not isinstance(changes, dict) or not set(changes) <= set(defaults(config)):
        raise PreferencesError("지원하지 않는 설정 항목입니다.")
    with operation_lock(config, "settings"):
        current = read_preferences(config)
        if revision != current["revision"]:
            raise PreferencesError("다른 창에서 설정이 변경되었습니다. 다시 불러온 뒤 저장해 주세요.")
        values = {**current["saved"], **changes}
        _validate(values)
        atomic_private_write(config.data_dir / "settings.toml",
                             toml_text({**current["raw"], **values, "schema_version": 1}).encode("utf-8"))
    return read_preferences(config)


def effective_preferences(config=settings):
    return read_preferences(config)["effective"]


def presentation_preferences(config=settings):
    """Keep the recovery/settings screen usable even when a file needs repair."""
    try:
        return effective_preferences(config)
    except PreferencesError:
        return defaults(config)
