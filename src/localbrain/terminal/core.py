"""Thin host protocol adapter. Rust owns terminal policy, IPC and process inspection."""
import asyncio
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import uuid

from localbrain.foundation.config import cache_directory
from localbrain.foundation.files import StorageError, validate_runtime_directory
from localbrain.foundation.preferences import PreferencesError
from .errors import TerminalError

MAX_REQUEST = 128 * 1024
MAX_REPLY = 2 * 1024 * 1024 + 4096
RUNTIME_ENVIRONMENT_KEYS = (
    "HOME", "PATH", "SHELL", "LANG", "LC_ALL", "LC_CTYPE", "ZDOTDIR", "TMPDIR",
    "LOCALBRAIN_TERMINAL_BUNDLE", "LOCALBRAIN_TERMINAL_RUNTIME", "LOCALBRAIN_TERMINAL_LAUNCHER",
    "HF_HOME", "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "XDG_CACHE_HOME",
)


def runtime_environment():
    # Child helpers need launch/configuration paths, never the host's desktop credential.
    environment = {key: os.environ[key] for key in RUNTIME_ENVIRONMENT_KEYS if key in os.environ}
    development_bundle = Path(__file__).resolve().parents[3] / "desktop/terminal/runtime"
    if "LOCALBRAIN_TERMINAL_BUNDLE" not in environment and development_bundle.is_dir():
        environment["LOCALBRAIN_TERMINAL_BUNDLE"] = str(development_bundle)
    return environment


def runtime_executable():
    """Only executable/host configuration chooses a binary; never browser data."""
    explicit = os.environ.get("LOCALBRAIN_TERMINAL_RUNTIME")
    bundle = runtime_environment().get("LOCALBRAIN_TERMINAL_BUNDLE")
    if explicit or bundle:
        path = Path(explicit) if explicit else Path(bundle) / "bin/localbrain-runtime"
        candidates = [path] if path.is_absolute() else []
    else:
        # Source checkout development; installed apps always supply the resource path.
        root = Path(__file__).resolve().parents[3]
        candidates = [root / "rust/target/release/localbrain-runtime", root / "rust/target/debug/localbrain-runtime"]
    for path in candidates:
        if path.is_file() and os.access(path, os.X_OK):
            return path
    raise TerminalError("setup_required", "터미널 Rust 실행 파일이 필요합니다. 터미널 runtime을 빌드해 주세요.")


def _bounded_control(command, data, timeout):
    """Bound both child pipes while retaining one deadline for the whole request."""
    process = subprocess.Popen(command, env=runtime_environment(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, diagnostic = bytearray(), bytearray()
    overflow = threading.Event()
    input_failed = threading.Event()

    def read(pipe, target, limit):
        try:
            while True:
                chunk = pipe.read1(min(65536, limit + 1 - len(target)))
                if not chunk:
                    return
                target.extend(chunk)
                if len(target) > limit:
                    overflow.set()
                    with contextlib.suppress(ProcessLookupError):
                        process.kill()
                    return
        finally:
            pipe.close()

    def write():
        try:
            process.stdin.write(data)
        except OSError:
            input_failed.set()
        finally:
            with contextlib.suppress(OSError):
                process.stdin.close()

    readers = [threading.Thread(target=read, args=(process.stdout, output, MAX_REPLY + 1), daemon=True),
               threading.Thread(target=read, args=(process.stderr, diagnostic, 4096), daemon=True)]
    writer = threading.Thread(target=write, daemon=True)
    for reader in readers:
        reader.start()
    writer.start()
    try:
        process.wait(timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        with contextlib.suppress(ProcessLookupError):
            process.kill()
        process.wait()
        raise TerminalError("unavailable", "터미널 실행부의 응답을 확인하지 못했습니다.") from error
    finally:
        for reader in [*readers, writer]:
            reader.join(timeout=1)
    if overflow.is_set() or input_failed.is_set() or any(reader.is_alive() for reader in [*readers, writer]) or process.returncode:
        raise TerminalError("protocol", "터미널 실행부의 응답 형식을 확인할 수 없습니다.")
    return bytes(output)


class TerminalService:
    def __init__(self, config, *, launcher=None):
        self.config = config
        self.context = {"dataDir": str(Path(config.data_dir).expanduser().resolve()),
                        "cacheDir": str(Path(cache_directory(config)).expanduser().resolve()),
                        "homeDir": str(Path.home().resolve())}
        scope = hashlib.sha256(self.context["dataDir"].encode()).hexdigest()[:10]
        self.root = Path(self.context["cacheDir"]) / ("terminal-" + scope)
        self.launcher = launcher

    def request(self, operation, arguments):
        # Settings can be repaired without consulting an unusable terminal cache.
        try:
            validate_runtime_directory(Path(self.context["dataDir"]))
            if not operation.startswith("settings."):
                validate_runtime_directory(Path(self.context["cacheDir"]))
                validate_runtime_directory(self.root)
        except StorageError as error:
            raise TerminalError("identity", "터미널 저장 위치를 확인해 주세요.") from error
        value = {"wire": 1, "id": uuid.uuid4().hex, "context": self.context,
                 "operation": operation, "arguments": arguments}
        data = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
        if len(data) > MAX_REQUEST:
            raise TerminalError("invalid", "요청이 너무 큽니다.")
        return value, data + b"\n"

    def call(self, operation, arguments=None, *, timeout=40):
        request, data = self.request(operation, {} if arguments is None else arguments)
        # The test host may select process mode explicitly; app/default uses launchd.
        command = [str(runtime_executable()), "control"]
        if self.launcher is not None:
            command = ["/usr/bin/env", "LOCALBRAIN_TERMINAL_LAUNCHER=" + self.launcher, *command]
        try:
            raw = _bounded_control(command, data, timeout)
            if not raw.endswith(b"\n") or b"\n" in raw[:-1]:
                raise ValueError()
            reply = json.loads(raw)
            if not isinstance(reply, dict):
                raise ValueError()
            if (set(reply) != ({"wire", "id", "ok", "result"} if reply.get("ok") is True else {"wire", "id", "ok", "error"})
                    or type(reply["wire"]) is not int or reply["wire"] != 1 or reply["id"] != request["id"]
                    or type(reply["ok"]) is not bool):
                raise ValueError()
            if reply["ok"]:
                return reply["result"]
            error = reply["error"]
            if (not isinstance(error, dict) or set(error) != {"kind", "code", "message"}
                    or error["kind"] not in {"terminal", "preferences"}
                    or not isinstance(error["code"], str) or not isinstance(error["message"], str)):
                raise ValueError()
            if error["kind"] == "preferences":
                raise PreferencesError(error["message"])
            raise TerminalError(error["code"], error["message"])
        except PreferencesError:
            raise
        except (ValueError, KeyError, TypeError, UnicodeError) as error:
            raise TerminalError("protocol", "터미널 실행부의 응답을 확인할 수 없습니다.") from error

    def status(self):
        return self.call("service.status")

    def list(self):
        return self.call("terminal.list")

    def dependencies(self):
        return self.call("service.dependencies")

    def install(self):
        return self.call("service.install")

    def start(self):
        return self.call("service.start")

    def stop(self, *, force=False, expected=None):
        return self.call("service.stop", {"force": force, **({"expected": expected} if expected is not None else {})})

    def restart(self, *, force=False, expected=None):
        return self.call("service.restart", {"force": force, **({"expected": expected} if expected is not None else {})})

    def create(self, body):
        return self.call("terminal.create", body)

    def rpc(self, method, params=None, *, timeout=8, generation=None):
        return self.call("manager.rpc", {"method": method, "params": params or {}, "generation": generation}, timeout=timeout + 8)

    async def stream(self, terminal_id, unicode, checkpoint):
        _, data = self.request("terminal.stream", {"id": terminal_id, "unicodeVersion": unicode, "checkpointVersion": checkpoint})
        env = runtime_environment()
        if self.launcher:
            env["LOCALBRAIN_TERMINAL_LAUNCHER"] = self.launcher
        process = await asyncio.create_subprocess_exec(str(runtime_executable()), "stream", env=env,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            limit=MAX_REPLY)
        try:
            process.stdin.write(data)
            await asyncio.wait_for(process.stdin.drain(), timeout=15)
        except BaseException:
            process.stdin.transport.abort()
            if process.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    process.kill()
            await process.wait()
            raise
        return process
