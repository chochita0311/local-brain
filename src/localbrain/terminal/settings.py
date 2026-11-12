"""Feature-owned launch defaults in the shared private preferences file."""

import os
from pathlib import Path
import pwd

from localbrain.foundation.operations import OperationBusy, operation_lock
from localbrain.foundation.preferences import (
    PreferencesError, atomic_private_write, read_preferences, toml_text,
)


def _section(preferences):
    values = preferences["raw"].get("terminal", {})
    if not isinstance(values, dict):
        raise PreferencesError("터미널 설정 형식을 확인해 주세요.")
    for key in ("cwd", "shell"):
        value = values.get(key, "")
        if not isinstance(value, str) or len(value) > 4096:
            raise PreferencesError("터미널 작업 폴더와 셸은 경로로 입력해 주세요.")
    return values


def _default_shell():
    return os.environ.get("SHELL") or pwd.getpwuid(os.getuid()).pw_shell or "/bin/zsh"


def read_launch_settings(config):
    preferences = read_preferences(config)
    values = _section(preferences)
    return {"cwd": values.get("cwd", str(Path.home())), "shell": values.get("shell", ""),
            "default_shell": _default_shell(), "revision": preferences["revision"],
            "preferences": {key: preferences[key] for key in ("saved", "effective", "source", "revision")}}


def _paths(cwd, shell):
    for value in (cwd, shell):
        if not isinstance(value, str) or len(value) > 4096 or "\0" in value:
            raise PreferencesError("작업 폴더와 셸은 경로로 입력해 주세요.")
    try:
        folder = Path(cwd or "~").expanduser()
        executable = Path(shell or _default_shell()).expanduser()
    except (RuntimeError, ValueError):
        raise PreferencesError("작업 폴더와 셸의 경로를 확인해 주세요.") from None
    if not folder.is_absolute() or not folder.is_dir() or not os.access(folder, os.X_OK):
        raise PreferencesError("기본 작업 폴더에 접근할 수 없습니다. 설정에서 경로를 확인해 주세요.")
    if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
        raise PreferencesError("실행 가능한 셸 파일을 선택해 주세요. 예: /bin/zsh")
    return str(folder), str(executable)


def launch_parameters(config):
    values = read_launch_settings(config)
    cwd, shell = _paths(values["cwd"], values["shell"])
    return {"cwd": cwd, "shell": shell}


def save_launch_settings(config, cwd, shell, revision):
    # Share the generic preferences transaction, so neither consumer loses the
    # other's section or accepts a revision captured before another write.
    try:
        with operation_lock(config, "settings"):
            current = read_preferences(config)
            if revision != current["revision"]:
                raise PreferencesError("다른 창에서 설정이 변경되었습니다. 다시 불러온 뒤 저장해 주세요.")
            values = _section(current)
            folder, executable = _paths(cwd, shell)
            raw = {**current["raw"], "terminal": {
                **values, "cwd": folder, "shell": executable if shell else "",
            }}
            ordered = {"schema_version": 1,
                       "onboarding_completed": current["saved"]["onboarding_completed"], **raw}
            atomic_private_write(config.data_dir / "settings.toml", toml_text(ordered).encode("utf-8"))
            return read_launch_settings(config)
    except OperationBusy:
        raise PreferencesError("설정을 저장하는 중입니다. 잠시 후 다시 시도해 주세요.") from None
