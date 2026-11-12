"""Private engine setup and service control. Inspection never starts a manager."""

import asyncio
import contextlib
import fcntl
import hashlib
import json
import os
import plistlib
import pwd
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from localbrain.foundation.config import cache_directory
from localbrain.foundation.files import StorageError, private_directory, read_owned_json, validate_runtime_directory


PACKAGE = Path(__file__).parent
MAX_REPLY = 2 * 1024 * 1024
VERSION = 1
BUILD_FILES = ("manager.cjs", "ownership.cjs", "checkpoint.cjs", "pty-input.cjs", "colors.cjs", "processes.py", "runtime/package-lock.json")
ENGINE_ENTRIES = ("node-pty/lib/index.js", "@xterm/headless/lib-headless/xterm-headless.js",
                  "@xterm/addon-serialize/lib/addon-serialize.js",
                  "@xterm/addon-unicode11/lib/addon-unicode11.js",
                  "node-pty/prebuilds/darwin-arm64/spawn-helper",
                  "node-pty/prebuilds/darwin-x64/spawn-helper")


def _build_fingerprint():
    value = hashlib.sha256()
    for name in BUILD_FILES:
        value.update(name.encode() + b"\0" + (PACKAGE / name).read_bytes())
    return value.hexdigest()


class TerminalError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _decode(raw):
    try:
        value = json.loads(raw)
        if not isinstance(value, dict) or not isinstance(value.get("ok"), bool):
            raise ValueError()
        if not value["ok"]:
            error = value["error"]
            if not isinstance(error, dict):
                raise ValueError()
            raise TerminalError(error.get("code", "runtime_error"), error.get("message", "터미널 요청 실패"))
        return value["result"]
    except (ValueError, KeyError, TypeError) as error:
        raise TerminalError("protocol", "서비스 응답을 확인할 수 없습니다.") from error


class TerminalService:
    """One configuration scope, with a deliberately separate optional engine."""

    def __init__(self, config, *, launcher=None):
        scope = hashlib.sha256(str(config.data_dir.resolve()).encode()).hexdigest()[:10]
        self.root = validate_runtime_directory(Path(cache_directory(config)) / ("terminal-" + scope))
        self.socket = self.root / "control.sock"
        self.label = "dev.localbrain.terminal." + hashlib.sha256(str(self.root).encode()).hexdigest()[:16]
        self.domain = "gui/" + str(os.getuid())
        self.launcher = launcher or ("launchd" if sys.platform == "darwin" else "unsupported")

    def supported(self):
        return self.launcher in {"launchd", "process"} and not getattr(sys, "frozen", False)

    def _require_supported(self):
        if not self.supported():
            raise TerminalError("unsupported", "터미널은 macOS 웹에서 사용할 수 있습니다.")
        if len(os.fsencode(self.socket)) >= 104:
            raise TerminalError("path_too_long", "캐시 경로가 너무 깁니다. LOCALBRAIN_CACHE_DIR을 짧은 경로로 설정해 주세요.")

    def _identity(self):
        try:
            result = read_owned_json(self.root / "identity.json", limit=4096)
            if not isinstance(result.get("pid"), int) or result["pid"] < 2:
                raise ValueError()
            if "born" in result and (not isinstance(result["born"], str) or not result["born"] or len(result["born"]) > 128):
                raise ValueError()
            return result
        except FileNotFoundError:
            return None
        except (OSError, ValueError, StorageError) as error:
            raise TerminalError("identity", "서비스 식별 정보를 확인할 수 없습니다.") from error

    def rpc(self, method, params=None, *, timeout=8, generation=None):
        payload = json.dumps({"method": method, "params": params or {}, "generation": generation},
                             ensure_ascii=False).encode() + b"\n"
        if len(payload) > 256 * 1024:
            raise TerminalError("invalid", "요청이 너무 큽니다.")
        try:
            info = self.socket.lstat()
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise TerminalError("identity", "서비스 소켓의 소유자를 확인할 수 없습니다.")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(timeout)
                connection.connect(str(self.socket))
                connection.sendall(payload)
                data = bytearray()
                while not data.endswith(b"\n"):
                    chunk = connection.recv(65536)
                    if not chunk:
                        raise TerminalError("disconnected", "서비스 연결이 끊겼습니다.")
                    data.extend(chunk)
                    if len(data) > MAX_REPLY:
                        raise TerminalError("protocol", "서비스 응답이 너무 큽니다.")
            return _decode(data)
        except (OSError, TimeoutError) as error:
            raise TerminalError("unavailable", "백그라운드 서비스에 연결할 수 없습니다.") from error

    async def read(self, terminal_id, after, lease, checkpoint_version=None):
        writer = None
        try:
            reader, writer = await asyncio.open_unix_connection(str(self.socket), limit=MAX_REPLY)
            writer.write(json.dumps({"method": "read", "params": {
                "id": terminal_id, "after": after, "lease": lease,
                "checkpointVersion": checkpoint_version,
            }}).encode() + b"\n")
            await writer.drain()
            raw = await asyncio.wait_for(reader.readline(), timeout=15)
            if not raw or len(raw) > MAX_REPLY:
                raise TerminalError("protocol", "출력 응답을 확인할 수 없습니다.")
            return _decode(raw)
        except (OSError, ValueError, asyncio.TimeoutError) as error:
            raise TerminalError("unavailable", "터미널 연결이 끊겼습니다.") from error
        finally:
            if writer:
                writer.close()
                with contextlib.suppress(OSError):
                    await writer.wait_closed()

    def status(self):
        if not self.supported():
            return {"running": False, "state": "unsupported", "installed": False, "supported": False}
        try:
            result = self.rpc("status", timeout=1)
            result.update(state="running", installed=self.installed(), supported=True)
            build = _build_fingerprint()
            if result.get("version") != VERSION or result.get("build") != build:
                result.update(state="incompatible")
            return result
        except TerminalError:
            identity = self._identity()
            if identity:
                try:
                    os.kill(identity["pid"], 0)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    return {"running": None, "state": "unknown", "installed": self.installed(), "supported": True}
                else:
                    if self._manager_replaced(identity):
                        return {"running": False, "state": "stopped", "installed": self.installed(),
                                "supported": True, "unclean": True}
                    return {"running": None, "state": "unknown", "installed": self.installed(), "supported": True}
            return {"running": False, "state": "stopped", "installed": self.installed(),
                    "supported": True, "unclean": identity is not None}

    def _manager_replaced(self, identity):
        if not identity.get("born") or identity.get("birthFormat") != "utc-lstart-v1":
            return False  # An unknown/legacy time format cannot prove replacement.
        try:
            result = subprocess.run([sys.executable, "-S", str(PACKAGE / "processes.py")],
                                    capture_output=True, text=True, timeout=3, check=True,
                                    env={**os.environ, "LC_ALL": "C", "TZ": "UTC"})
            table = json.loads(result.stdout)
            record = next((entry for entry in table if entry.get("pid") == identity["pid"]), None)
            return bool(record and (record.get("dead") is True or
                        isinstance(record.get("born"), str) and record["born"] != identity["born"]))
        except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
            return False

    def list(self):
        status = self.status()
        if status["state"] == "stopped" or status["state"] == "unsupported":
            return {"running": False, "generation": None, "revision": 0, "tabs": [], "terminals": [], "service": status}
        if status["state"] not in {"running", "incompatible"}:
            raise TerminalError("unavailable", "서비스 상태를 확인할 수 없습니다.")
        result = self.rpc("list")
        result["service"] = status
        return result

    @contextlib.contextmanager
    def _lock(self):
        private_directory(self.root)
        fd = os.open(self.root / "control.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise TerminalError("identity", "서비스 잠금을 확인할 수 없습니다.")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise TerminalError("busy", "다른 서비스 작업이 진행 중입니다.") from error
            yield
        finally:
            os.close(fd)

    def installed(self):
        try:
            marker = read_owned_json(self.root / "engine-ready.json", limit=4096)
            wanted = hashlib.sha256((PACKAGE / "runtime/package-lock.json").read_bytes()).hexdigest()
            return (marker.get("lock") == wanted and
                    all((self.root / "engine/node_modules" / name).is_file() for name in ENGINE_ENTRIES))
        except (OSError, ValueError, StorageError):
            return False

    def _node(self):
        executable = shutil.which("node")
        try:
            result = subprocess.run([executable, "--version"], capture_output=True, text=True,
                                    timeout=5, check=True) if executable else None
            if not result or int(result.stdout.strip().lstrip("v").split(".")[0]) < 20:
                raise ValueError()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise TerminalError("node_required", "Node.js 20 이상이 필요합니다.") from error
        return executable

    def dependencies(self):
        return {"node": bool(shutil.which("node")), "npm": bool(shutil.which("npm")),
                "installed": self.installed(), "supported": self.supported()}

    def install(self):
        self._require_supported()
        node, npm = self._node(), shutil.which("npm")
        if not npm:
            raise TerminalError("node_required", "Node.js 20 이상과 npm을 설치해 주세요.")
        with self._lock():
            if self.status()["running"] is not False:
                raise TerminalError("busy", "서비스를 중지한 뒤 설치해 주세요.")
            # npm ci replaces the engine tree; interrupted setup must remain retryable.
            try:
                (self.root / "engine-ready.json").unlink(missing_ok=True)
            except OSError as error:
                raise TerminalError("identity", "설치 상태 파일을 확인할 수 없습니다.") from error
            target = private_directory(self.root / "engine")
            for name in ("package.json", "package-lock.json"):
                destination = target / name
                if destination.is_symlink():
                    raise TerminalError("identity", "구성요소 경로를 확인할 수 없습니다.")
                shutil.copyfile(PACKAGE / "runtime" / name, destination)
                destination.chmod(0o600)
            try:
                subprocess.run([npm, "ci", "--registry=https://registry.npmjs.org", "--ignore-scripts",
                                "--omit=dev", "--no-audit", "--no-fund"],
                               cwd=target, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=240, check=True)
                probe = subprocess.run([node, "-e", "require('node-pty'); require('@xterm/headless'); require('@xterm/addon-serialize'); require('@xterm/addon-unicode11'); process.stdout.write(process.arch);"],
                                       cwd=target, capture_output=True, text=True, timeout=10, check=True)
                arch = probe.stdout.strip()
                if arch not in {"arm64", "x64"}:
                    raise OSError("unsupported Node architecture")
                # The pinned package carries both supported prebuilds. Preparing
                # both also permits switching native/Rosetta Node after setup.
                self._prepare_helpers()
            except (OSError, subprocess.SubprocessError) as error:
                raise TerminalError("install_failed", "터미널 구성요소를 설치하지 못했습니다.") from error
            marker = {"lock": hashlib.sha256((PACKAGE / "runtime/package-lock.json").read_bytes()).hexdigest()}
            self._write_private("engine-ready.json", marker)
        return {"installed": True}

    def _prepare_helpers(self):
        for arch in ("arm64", "x64"):
            helper = self.root / "engine/node_modules/node-pty/prebuilds" / ("darwin-" + arch) / "spawn-helper"
            info = helper.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                raise OSError("helper")
            helper.chmod(0o700)

    def _write_private(self, name, value):
        destination = self.root / name
        fd = os.open(destination, os.O_CREAT | os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        try:
            os.write(fd, json.dumps(value).encode())
        finally:
            os.close(fd)

    def start(self):
        self._require_supported()
        with self._lock():
            return self._start_locked()

    def _remove_job(self):
        subprocess.run(["/bin/launchctl", "bootout", self.domain + "/" + self.label],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)

    def _start_locked(self):
        if not self.installed():
            raise TerminalError("setup_required", "터미널 구성요소를 먼저 설치해 주세요.")
        node = self._node()
        status = self.status()
        if status["state"] == "running":
            if status.get("stopping"):
                raise TerminalError("stopping", "서비스를 중지하고 있습니다.")
            return status
        if status["running"] is not False:
            raise TerminalError("unavailable", "기존 서비스의 중지를 확인해 주세요.")
        try:
            self._prepare_helpers()
        except OSError as error:
            raise TerminalError("setup_required", "터미널 실행 구성요소를 확인하지 못했습니다. 구성요소를 다시 설치해 주세요.") from error
        for name in ("control.sock", "identity.json"):
            candidate = self.root / name
            if candidate.is_symlink():
                raise TerminalError("identity", "서비스 경로를 확인할 수 없습니다.")
            if candidate.exists():
                candidate.unlink()
        manager = str(PACKAGE / "manager.cjs")
        # launchd owns the lifetime; no login agent or persisted environment dump.
        allowed = ("HOME", "PATH", "SHELL", "LANG", "LC_ALL", "LC_CTYPE", "ZDOTDIR", "TMPDIR")
        environment = {key: os.environ[key] for key in allowed if key in os.environ}
        environment.setdefault("HOME", str(Path.home()))
        environment.setdefault("SHELL", pwd.getpwuid(os.getuid()).pw_shell)
        environment.setdefault("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
        environment.setdefault("LANG", "en_US.UTF-8")
        if self.launcher == "launchd":
            self._remove_job()
            # submit creates an always-running job. An in-memory bootstrap job
            # with KeepAlive disabled lets clean idle exit remain stopped.
            job = {"Label": self.label, "ProgramArguments": [node, manager, str(self.root), sys.executable],
                   "EnvironmentVariables": environment, "RunAtLoad": True, "KeepAlive": False,
                   "StandardOutPath": "/dev/null", "StandardErrorPath": "/dev/null", "Umask": 0o077}
            launch_path = None
            try:
                with tempfile.NamedTemporaryFile(dir=self.root, prefix="launch-", suffix=".plist", delete=False) as file:
                    launch_path = Path(file.name)
                    file.write(plistlib.dumps(job))
                subprocess.run(["/bin/launchctl", "bootstrap", self.domain, str(launch_path)],
                               capture_output=True, check=True, timeout=10)
            except (OSError, subprocess.SubprocessError) as error:
                raise TerminalError("start_failed", "백그라운드 서비스를 시작하지 못했습니다.") from error
            finally:
                if launch_path is not None:
                    launch_path.unlink(missing_ok=True)
        else:
            # Controlled test host; never selectable through an HTTP request.
            self._process = subprocess.Popen([node, manager, str(self.root), sys.executable], env=environment,
                                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL, start_new_session=True)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            child = getattr(self, "_process", None)
            if child and child.poll() is not None:
                raise TerminalError("start_failed", "백그라운드 서비스를 시작하지 못했습니다.")
            status = self.status()
            if status["state"] == "running":
                return status
            time.sleep(0.05)
        raise TerminalError("start_failed", "서비스의 시작을 확인하지 못했습니다.")

    def create(self, params):
        self._require_supported()
        with self._lock():
            status = self._start_locked()
            return self.rpc("create", params, generation=status["generation"])

    def stop(self, *, force=False, expected=None):
        self._require_supported()
        with self._lock():
            return self._stop_locked(force=force, expected=expected)

    def _stop_locked(self, *, force, expected=None):
        status = self.status()
        if status["state"] == "stopped":
            if status.get("unclean"):
                raise TerminalError("identity", "관리 서비스가 예기치 않게 종료되었습니다. 이전 작업의 종료를 별도로 확인해 주세요.")
            if expected is not None and (expected.get("generation") is not None or expected.get("terminals")):
                raise TerminalError("conflict", "서비스가 변경되었습니다. 상태를 다시 확인해 주세요.")
            child = getattr(self, "_process", None)
            if child:
                child.poll()
            if self.launcher == "launchd":
                self._remove_job()
            return {"stopped": True}
        if status["state"] not in {"running", "incompatible"}:
            raise TerminalError("unavailable", "서비스 식별과 종료를 확인할 수 없습니다.")
        current = self.rpc("list", generation=status["generation"])
        snapshot = {"generation": current["generation"], "terminals": [item["id"] for item in current["terminals"]]}
        if expected is not None and (expected.get("generation") != snapshot["generation"] or
                sorted(expected.get("terminals", [])) != sorted(snapshot["terminals"])):
            raise TerminalError("conflict", "실행 목록이 변경되었습니다. 범위를 다시 확인해 주세요.")
        identity = self._identity()
        if not identity or any(identity.get(key) != status.get(key) for key in ("pid", "generation")):
            raise TerminalError("identity", "서비스 식별 정보가 일치하지 않습니다.")
        self.rpc("shutdown", {"force": force, "expected": snapshot}, timeout=12, generation=identity["generation"])
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            child = getattr(self, "_process", None)
            if child:
                child.poll()
            try:
                os.kill(identity["pid"], 0)
                alive = True
            except ProcessLookupError:
                alive = False
            if not self.socket.exists() and not alive:
                if self.launcher == "launchd":
                    self._remove_job()
                return {"stopped": True, "generation": identity.get("generation") if identity else None}
            time.sleep(0.05)
        raise TerminalError("stop_failed", "서비스의 종료를 확인하지 못했습니다.")

    def restart(self, *, force=False, expected=None):
        self._require_supported()
        # Keep the generation transition indivisible with create/start/stop/install.
        with self._lock():
            self._stop_locked(force=force, expected=expected)
            return self._start_locked()
