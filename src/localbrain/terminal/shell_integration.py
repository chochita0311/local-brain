"""Versioned zsh launch shims, independent of the app and running manager payload."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat

from localbrain.foundation.files import StorageError, private_directory, validate_runtime_directory
from localbrain.foundation.operations import OperationBusy, operation_lock
from localbrain.foundation.preferences import PreferencesError, atomic_private_write
from localbrain.foundation.private_json import read_json


class ShellIntegrationError(PreferencesError):
    pass


_RESTORE = r'''
if [[ $__LOCALBRAIN_ZDOTDIR_SET == 1 ]]; then
  typeset -g ZDOTDIR="$__LOCALBRAIN_USER_ZDOTDIR"
  if [[ $__LOCALBRAIN_ZDOTDIR_EXPORTED == 1 ]]; then
    export ZDOTDIR
  else
    typeset -g +x ZDOTDIR
  fi
else
  unset ZDOTDIR
fi
'''

_CAPTURE = r'''
typeset -g __LOCALBRAIN_ZDOTDIR_SET=${+ZDOTDIR}
typeset -g __LOCALBRAIN_USER_ZDOTDIR=${ZDOTDIR-}
typeset -g __LOCALBRAIN_ZDOTDIR_EXPORTED=0
[[ ${parameters[ZDOTDIR]-} == *export* ]] && __LOCALBRAIN_ZDOTDIR_EXPORTED=1
'''

_HOOKS = r'''
__localbrain_precmd() {
  builtin local localbrain_exit_code="$?"
  emulate -L zsh
  if [[ ${ZDOTDIR-} == @SHIM@ ]]; then
@RESTORE@
  fi
  if (( ${__LOCALBRAIN_COMMAND_ACTIVE:-0} )); then
    builtin printf '\033]133;D;%d\007' "$localbrain_exit_code"
    __LOCALBRAIN_COMMAND_ACTIVE=0
  fi
  builtin printf '\033]133;A\007'
  builtin local -x LC_ALL=C
  builtin local localbrain_uri='' localbrain_byte
  builtin local -i localbrain_index
  for ((localbrain_index=1; localbrain_index<=${#PWD}; localbrain_index++)); do
    localbrain_byte=${PWD[localbrain_index]}
    case $localbrain_byte in
      [a-zA-Z0-9/._~-]) localbrain_uri+=$localbrain_byte ;;
      *) builtin printf -v localbrain_uri '%s%%%02X' "$localbrain_uri" "'$localbrain_byte" ;;
    esac
  done
  builtin printf '\033]7;file://localhost%s\007' "$localbrain_uri"
  return 0
}
__localbrain_preexec() {
  __LOCALBRAIN_COMMAND_ACTIVE=1
  builtin printf '\033]133;C\007'
  return 0
}
__localbrain_install_hooks() {
  emulate -L zsh
  typeset -ga precmd_functions preexec_functions
  (( ${precmd_functions[(Ie)__localbrain_precmd]} )) || precmd_functions+=(__localbrain_precmd)
  (( ${preexec_functions[(Ie)__localbrain_preexec]} )) || preexec_functions+=(__localbrain_preexec)
}
__localbrain_install_hooks
'''


def _templates(shell):
    launcher = '''#!/bin/sh
if [ "${ZDOTDIR-}" != @SHIM@ ]; then
  if [ "${ZDOTDIR+x}" = x ]; then
    export __LOCALBRAIN_ZDOTDIR_SET=1 __LOCALBRAIN_ZDOTDIR_EXPORTED=1 __LOCALBRAIN_USER_ZDOTDIR="$ZDOTDIR"
  else
    export __LOCALBRAIN_ZDOTDIR_SET=0 __LOCALBRAIN_ZDOTDIR_EXPORTED=0 __LOCALBRAIN_USER_ZDOTDIR=''
  fi
fi
export ZDOTDIR=@SHIM@
export SHELL=''' + shlex.quote(shell) + '''
exec ''' + shlex.quote(shell) + ''' "$@"
'''
    files = {"launcher": launcher, "hooks.zsh": _HOOKS.replace("@RESTORE@", _RESTORE)}
    for name in (".zshenv", ".zprofile", ".zshrc", ".zlogin"):
        # Source user files at startup scope, rather than inside a function whose
        # local variables/options would change the user's rc semantics.
        final = name == ".zlogin"
        body = _RESTORE + r'''
typeset -g __LOCALBRAIN_RC_RESULT=0
if [[ ${ZDOTDIR-$HOME} != @SHIM@ && -f ${ZDOTDIR-$HOME}/@RC@ ]]; then
  builtin source "${ZDOTDIR-$HOME}/@RC@"
  __LOCALBRAIN_RC_RESULT=$?
fi
''' + _CAPTURE + r'''
if [[ -o interactive ]]; then
  builtin source @SHIM@/hooks.zsh
fi
'''
        if not final:
            condition = '[[ -o rcs ]]' if name != ".zshrc" else '[[ -o rcs && -o login ]]'
            body += 'if ' + condition + '; then\n  export ZDOTDIR=@SHIM@\nfi\n'
        body += 'return $__LOCALBRAIN_RC_RESULT\n'
        files[name] = body.replace("@RC@", name)
    return files


def _regular(path, mode):
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != mode):
        raise ShellIntegrationError("셸 연동 파일의 소유권과 권한을 확인해 주세요.")


def _verify(root):
    for directory in (root.parent, root):
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ShellIntegrationError("셸 연동 저장 위치를 확인해 주세요.")
    _regular(root / "manifest.json", 0o600)
    if (root / "manifest.json").stat().st_size > 16 * 1024:
        raise ShellIntegrationError("셸 연동 파일을 확인해 주세요.")
    manifest = read_json(root / "manifest.json")
    expected = {"launcher", "hooks.zsh", ".zshenv", ".zprofile", ".zshrc", ".zlogin"}
    if (not isinstance(manifest, dict) or set(manifest) != {"schema", "shell", "files"}
            or type(manifest["schema"]) is not int or manifest["schema"] != 1
            or not isinstance(manifest["shell"], str) or not Path(manifest["shell"]).is_absolute()
            or not isinstance(manifest["files"], dict) or set(manifest["files"]) != expected):
        raise ShellIntegrationError("셸 연동 파일을 확인해 주세요.")
    for name, digest in manifest["files"].items():
        path = root / name
        _regular(path, 0o700 if name == "launcher" else 0o600)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ShellIntegrationError("셸 연동 파일이 변경되었습니다. 새 터미널 생성을 멈췄습니다.")


def integrated_shell(config, shell):
    if not isinstance(shell, str):
        return shell
    executable = Path(shell)
    if executable.name not in {"zsh", "launcher"}:
        return shell
    try:
        family = validate_runtime_directory(config.data_dir) / "terminal-shell"
    except StorageError as error:
        raise ShellIntegrationError("셸 연동 저장 위치를 확인해 주세요.") from error
    if executable.name == "launcher" and family in executable.parents:
        _verify(executable.parent)
        return shell
    if executable.name != "zsh" or not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
        return shell
    templates = _templates(str(executable))
    identity = hashlib.sha256(json.dumps(templates, sort_keys=True).encode()).hexdigest()[:24]
    root = family / ("zsh-" + identity)
    try:
        with operation_lock(config, "terminal-shell"):
            current = private_directory(config.data_dir)
            for part in ("terminal-shell", root.name):
                current = current / part
                current.mkdir(mode=0o700, exist_ok=True)
                info = current.lstat()
                if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise ShellIntegrationError("셸 연동 저장 위치를 확인해 주세요.")
            if (root / "manifest.json").exists() or (root / "manifest.json").is_symlink():
                _verify(root)
                return str(root / "launcher")
            hashes = {}
            for name, template in templates.items():
                path = root / name
                content = template.replace("@SHIM@", shlex.quote(str(root))).encode()
                if path.exists() or path.is_symlink():
                    info = path.lstat()
                    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1
                            or info.st_mode & 0o077 or path.read_bytes() != content):
                        raise ShellIntegrationError("완료되지 않은 셸 연동 파일을 확인해 주세요.")
                else:
                    atomic_private_write(path, content)
                path.chmod(0o700 if name == "launcher" else 0o600)
                hashes[name] = hashlib.sha256(content).hexdigest()
            atomic_private_write(root / "manifest.json", json.dumps({"schema": 1, "shell": shell, "files": hashes}).encode())
            _verify(root)
            return str(root / "launcher")
    except OperationBusy as error:
        raise ShellIntegrationError("다른 로컬 작업이 저장 중입니다. 잠시 후 다시 시도해 주세요.") from error
    except StorageError as error:
        raise ShellIntegrationError("셸 연동 저장 위치를 확인해 주세요.") from error
