"""Terminal contracts: no real user files, provider sessions or outside processes."""
import contextlib
import base64
import hashlib
import io
import json
import os
import plistlib
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from localbrain.terminal.cli import main as terminal_cli
from localbrain.terminal.runtime import ENGINE_ENTRIES, PACKAGE, TerminalError, TerminalService
from localbrain.terminal.processes import process_table
from localbrain.terminal.web import install_routes


class FakeControl:
    def __init__(self):
        self.calls = []

    def list(self):
        return {"running": False, "generation": None, "tabs": [], "terminals": [],
                "service": {"state": "stopped", "running": False}}

    def dependencies(self):
        return {"installed": False, "node": True, "npm": True, "supported": True}

    def status(self):
        self.calls.append(("status",))
        return {"state": "stopped", "running": False}

    def rpc(self, method, params):
        self.calls.append((method, params))
        return {"stopped": True}

    def start(self):
        self.calls.append(("start",))
        return {"running": True}

    def stop(self, *, force=False, expected=None):
        self.expected = expected
        self.calls.append(("service-stop", force))
        return {"stopped": True}

    def restart(self, *, force=False, expected=None):
        self.expected = expected
        self.calls.append(("restart", force))
        return {"running": True}

    def create(self, body):
        self.calls.append(("create", body))
        return {"created": True}


class TerminalCliTests(unittest.TestCase):
    def invoke(self, argv, control=None):
        control = control or FakeControl()
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            result = terminal_cli(argv, config=object(), factory=lambda _: control)
        return result, output.getvalue(), error.getvalue(), control.calls

    def test_observation_does_not_start_and_json_is_clean(self):
        code, text, error, calls = self.invoke(["service", "status", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(text)["state"], "stopped")
        self.assertEqual(calls, [("status",)])
        self.assertEqual(error, "")
        code, text, _, calls = self.invoke(["list", "--json"])
        self.assertFalse(json.loads(text)["running"])
        self.assertEqual(calls, [])

    def test_terminal_and_service_stop_have_different_targets(self):
        _, _, _, calls = self.invoke(["stop", "t-synthetic", "--json"])
        self.assertEqual(calls[0], ("stop", {"id": "t-synthetic", "all": False, "force": False}))
        _, _, _, calls = self.invoke(["service", "stop", "--yes"])
        self.assertEqual(calls, [("service-stop", False)])
        _, _, _, calls = self.invoke(["stop", "--all", "--yes"])
        self.assertEqual(calls, [])  # Already stopped: no launch or socket mutation.
        control = FakeControl()
        control.list = lambda: {"running": True, "generation": "generation-a", "terminals": []}
        _, _, _, calls = self.invoke(["stop", "--all", "--yes"], control)
        self.assertTrue(calls[0][1]["all"])
        self.assertEqual(calls[0][1]["expected"], {"generation": "generation-a", "terminals": []})

    def test_missing_and_conflicting_targets_fail_before_control(self):
        for argv in (["stop"], ["stop", "t-synthetic", "--all"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                control = FakeControl()
                with self.assertRaises(SystemExit):
                    terminal_cli(argv, config=object(), factory=lambda _: control)
                self.assertEqual(control.calls, [])

    def test_destructive_automation_requires_confirmation(self):
        control = FakeControl()
        control.list = lambda: {"terminals": [{"state": "running"}]}
        with mock.patch("sys.stdin.isatty", return_value=False):
            code, text, error, calls = self.invoke(["service", "stop", "--json"], control)
        self.assertEqual(code, 1)
        self.assertEqual(text, "")
        self.assertEqual(json.loads(error)["error"]["code"], "confirmation_required")
        self.assertFalse(calls)

    def test_help_has_no_config_or_control_side_effects(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
            terminal_cli(["service", "--help"], factory=lambda _: self.fail("control created"))
        self.assertEqual(result.exception.code, 0)

    def test_bulk_stop_refuses_unclean_loss_instead_of_reporting_completion(self):
        control = FakeControl()
        control.list = lambda: {"running": False, "generation": None, "terminals": [],
                                "service": {"state": "stopped", "running": False, "unclean": True}}
        for flags in ([], ["--json"], ["--json", "--yes", "--force"]):
            with self.subTest(flags=flags):
                code, output, error, calls = self.invoke(["stop", "--all"] + flags, control)
                self.assertEqual(code, 1)
                self.assertEqual(output, "")
                self.assertFalse(calls)
                if "--json" in flags:
                    self.assertEqual(json.loads(error)["error"]["code"], "identity")
                else:
                    self.assertIn("종료를 확인할 수 없습니다", error)

    def test_service_confirmation_scope_is_forwarded_even_when_empty(self):
        control = FakeControl()
        control.list = lambda: {"running": True, "generation": "generation-a", "terminals": []}
        code, _, _, _ = self.invoke(["service", "restart", "--json"], control)
        self.assertEqual(code, 0)
        self.assertEqual(control.expected, {"generation": "generation-a", "terminals": []})


class TerminalWebTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        install_routes(self.app, None, object())
        self.control = FakeControl()
        self.app.state.terminal_factory = lambda: self.control
        self.client = TestClient(self.app, base_url="http://127.0.0.1:8123")

    def test_read_only_page_state_does_not_launch(self):
        response = self.client.get("/api/terminal")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["running"])
        self.assertEqual(self.control.calls, [])

    def test_rejected_input_ends_stream_before_later_paste_fragments(self):
        import asyncio
        calls = []
        def rpc(method, params):
            calls.append(method)
            if method == "claim":
                return {"lease": "synthetic", "writable": True}
            if method == "input":
                raise TerminalError("input_busy", "입력 대기 한도")
            return {}
        async def read(*args):
            await asyncio.Future()
        self.control.rpc, self.control.read = rpc, read
        with self.client.websocket_connect(
                "ws://127.0.0.1:8123/api/terminal/terminals/t-synthetic/stream",
                headers={"origin": "http://127.0.0.1:8123"}) as connection:
            self.assertEqual(connection.receive_json()["type"], "control")
            connection.send_json({"type": "input", "data": "middle-fragment"})
            connection.send_json({"type": "input", "data": "unsafe-suffix\n"})
            error = connection.receive_json()
            self.assertEqual(error["code"], "input_busy")
            with self.assertRaises(WebSocketDisconnect) as closed:
                connection.receive_json()
            self.assertEqual(closed.exception.code, 1013)
        self.assertEqual(calls.count("input"), 1)
        self.assertEqual(calls[-1], "release")

    def test_mutations_require_exact_origin_and_json(self):
        for headers in ({}, {"origin": "http://outside.invalid"}, {"origin": "http://127.0.0.1:8124"},
                        {"origin": "https://127.0.0.1:8123"}, {"origin": "http://127.0.0.1:8123/path"},
                        {"origin": "http://["}):
            with self.subTest(headers=headers):
                response = self.client.post("/api/terminal/service/start", json={}, headers=headers)
                self.assertEqual(response.status_code, 403)
        self.assertEqual(self.control.calls, [])
        response = self.client.post("/api/terminal/service/start", json={},
                                    headers={"origin": "http://127.0.0.1:8123"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.control.calls, [("start",)])

    def test_array_large_and_nonboolean_input_are_rejected(self):
        headers = {"origin": "http://127.0.0.1:8123"}
        for body, status in (([], 400), ({"data": "x" * 140000}, 413), ({"force": "false"}, 400)):
            response = self.client.post("/api/terminal/service/stop", json=body, headers=headers)
            self.assertEqual(response.status_code, status)
        self.assertEqual(self.control.calls, [])

    def test_websocket_origin_rejected_before_any_runtime_command(self):
        for origin in ("http://outside.invalid", "null", "", "https://127.0.0.1:8123", "http://["):
            with self.subTest(origin=origin), self.assertRaises(WebSocketDisconnect) as result:
                with self.client.websocket_connect(
                    "ws://127.0.0.1:8123/api/terminal/terminals/t-synthetic/stream",
                    headers={"origin": origin}):
                    pass
            self.assertEqual(result.exception.code, 1008)
        self.assertFalse(self.control.calls)

    def test_error_is_bounded_and_never_success(self):
        def failed():
            raise TerminalError("busy", "서비스 작업 진행 중")
        self.control.start = failed
        response = self.client.post("/api/terminal/service/start", json={},
                                    headers={"origin": "http://127.0.0.1:8123"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "busy")

    def test_websocket_passes_declared_width_version_before_acquiring_input(self):
        for suffix, wanted, checkpoint in (("", "6", None), ("?unicode=11", "11", None),
                                          ("?unicode=11&checkpoint=xterm6-v3", "11", "xterm6-v3")):
            def reject(method, params):
                self.assertEqual(method, "claim")
                self.assertEqual(params["unicodeVersion"], wanted)
                self.assertEqual(params["checkpointVersion"], checkpoint)
                raise TerminalError("client_update_required", "터미널 화면을 새로고침해 주세요.")
            self.control.rpc = reject
            with self.client.websocket_connect(
                    "ws://127.0.0.1:8123/api/terminal/terminals/t-synthetic/stream" + suffix,
                    headers={"origin": "http://127.0.0.1:8123"}) as connection:
                self.assertEqual(connection.receive_json(), {"type": "error", "message": "터미널 화면을 새로고침해 주세요."})


@unittest.skipUnless(shutil.which("node"), "optional Node ownership fixture")
class TerminalOwnershipTests(unittest.TestCase):
    def test_reused_root_and_unanchored_recovery_never_establish_ownership(self):
        script = """
const {ownedProcesses,signalTargets}=require(process.argv[1]);
const owner={pid:10,parent:5,group:10,session:10,born:'original',dead:false};
const child={pid:11,parent:10,group:11,session:10,born:'child',dead:false};
const replacement={...owner,parent:1,born:'replacement'};
const reparented={...child,parent:1};
const other={...child,pid:12,parent:1,born:'unrelated'};
console.log(JSON.stringify([
 ownedProcesses(owner,[owner],true,[replacement,child]),
 ownedProcesses(owner,[owner,child],true,[reparented]),
 ownedProcesses(owner,[owner],true,[other]),
 ownedProcesses(owner,[owner],true,[]),
 ownedProcesses(owner,[owner],false,[owner,{...child,session:11}]),
 ownedProcesses(owner,[owner],false,[{...owner,dead:true},reparented]),
 signalTargets(ownedProcesses(owner,[],false,[owner]),[replacement]),
 signalTargets(ownedProcesses(owner,[],false,[owner]),[{...owner,parent:1}])
]));
"""
        value = json.loads(subprocess.check_output([shutil.which("node"), "-e", script, str(PACKAGE / "ownership.cjs")], text=True))
        self.assertIsNone(value[0])
        self.assertEqual([row["pid"] for row in value[1]], [11])
        self.assertIsNone(value[2])
        self.assertEqual(value[3], [])
        self.assertEqual([row["pid"] for row in value[4]], [10, 11])
        self.assertEqual([row["pid"] for row in value[5]], [11])
        self.assertEqual(value[6], [])
        self.assertEqual(value[7], [])


@unittest.skipUnless(sys.platform == "darwin", "macOS terminal setup contract")
class TerminalSetupTests(unittest.TestCase):
    def test_reused_manager_pid_needs_positive_birth_evidence(self):
        with tempfile.TemporaryDirectory(prefix="lb-identity-", dir="/private/tmp") as folder:
            base = Path(folder)
            service = TerminalService(SimpleNamespace(data_dir=base / "data", cache_dir=base / "cache"), launcher="process")
            identity = {"pid": 12345, "born": "original", "birthFormat": "utc-lstart-v1"}
            for record, state in (({"pid": 12345, "born": "replacement"}, "stopped"),
                                  ({"pid": 12345, "born": "original"}, "unknown"),
                                  ({"pid": 12345, "born": "original", "dead": True}, "stopped"),
                                  ({"pid": 54321, "born": "replacement"}, "unknown")):
                with self.subTest(record=record), \
                     mock.patch.object(service, "rpc", side_effect=TerminalError("unavailable", "synthetic")), \
                     mock.patch.object(service, "_identity", return_value=identity), \
                     mock.patch.object(service, "installed", return_value=True), \
                     mock.patch("localbrain.terminal.runtime.os.kill") as signal, \
                     mock.patch("localbrain.terminal.runtime.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout=json.dumps([record]))):
                    self.assertEqual(service.status()["state"], state)
                    signal.assert_called_once_with(12345, 0)
            with mock.patch("localbrain.terminal.runtime.subprocess.run", side_effect=subprocess.TimeoutExpired("synthetic", 3)):
                self.assertFalse(service._manager_replaced(identity))
            with mock.patch("localbrain.terminal.runtime.subprocess.run") as inspect:
                self.assertFalse(service._manager_replaced({"pid": 12345}))
                self.assertFalse(service._manager_replaced({"pid": 12345, "born": "legacy local time"}))
                inspect.assert_not_called()

    def test_same_process_birth_is_stable_across_caller_timezones(self):
        with tempfile.TemporaryDirectory(prefix="lb-birth-tz-", dir="/private/tmp") as folder:
            base = Path(folder)
            service = TerminalService(SimpleNamespace(data_dir=base / "data", cache_dir=base / "cache"), launcher="process")
            born = " ".join(subprocess.check_output(["/bin/ps", "-p", str(os.getpid()), "-o", "lstart="],
                                                   text=True, env={**os.environ, "LC_ALL": "C", "TZ": "UTC"}).split())
            identity = {"pid": os.getpid(), "born": born, "birthFormat": "utc-lstart-v1"}
            for zone in ("UTC", "Asia/Seoul", "Pacific/Honolulu"):
                with self.subTest(zone=zone), mock.patch.dict(os.environ, {"TZ": zone}):
                    self.assertFalse(service._manager_replaced(identity))

    def test_start_prepares_an_existing_cache_for_either_node_architecture(self):
        with tempfile.TemporaryDirectory(prefix="lb-migrate-", dir="/private/tmp") as folder:
            base = Path(folder)
            service = TerminalService(SimpleNamespace(data_dir=base / "data", cache_dir=base / "cache"))
            helpers = []
            for arch in ("arm64", "x64"):
                helper = service.root / "engine/node_modules/node-pty/prebuilds" / ("darwin-" + arch) / "spawn-helper"
                helper.parent.mkdir(parents=True)
                helper.write_text("synthetic helper")
                helper.chmod(0o600)
                helpers.append(helper)
            with mock.patch.object(service, "installed", return_value=True), \
                 mock.patch.object(service, "_node", return_value="/synthetic/node"), \
                 mock.patch.object(service, "_remove_job"), \
                 mock.patch.object(service, "status", side_effect=[{"state": "stopped", "running": False}, {"state": "running", "running": True}]), \
                 mock.patch("localbrain.terminal.runtime.subprocess.run"):
                self.assertTrue(service.start()["running"])
            self.assertEqual([helper.stat().st_mode & 0o777 for helper in helpers], [0o700, 0o700])

    def test_setup_prepares_both_supported_node_architectures(self):
        with tempfile.TemporaryDirectory(prefix="lb-arch-", dir="/private/tmp") as folder:
            base = Path(folder)
            service = TerminalService(SimpleNamespace(data_dir=base / "data", cache_dir=base / "cache"), launcher="process")
            helpers = {}
            for arch in ("arm64", "x64"):
                helper = service.root / "engine/node_modules/node-pty/prebuilds" / ("darwin-" + arch) / "spawn-helper"
                helper.parent.mkdir(parents=True)
                helper.write_text("synthetic helper")
                helper.chmod(0o600)
                helpers[arch] = helper
            results = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0, stdout="x64")]
            with mock.patch.object(service, "_node", return_value="/synthetic/node"), \
                 mock.patch.object(service, "status", return_value={"running": False}), \
                 mock.patch("localbrain.terminal.runtime.shutil.which", return_value="/synthetic/npm"), \
                 mock.patch("localbrain.terminal.runtime.subprocess.run", side_effect=results):
                self.assertTrue(service.install()["installed"])
            self.assertEqual(helpers["x64"].stat().st_mode & 0o777, 0o700)
            self.assertEqual(helpers["arm64"].stat().st_mode & 0o777, 0o700)

    def test_launchd_bootstrap_is_not_keepalive_and_removes_temporary_config(self):
        with tempfile.TemporaryDirectory(prefix="lb-launch-", dir="/private/tmp") as folder:
            base = Path(folder)
            service = TerminalService(SimpleNamespace(data_dir=base / "data", cache_dir=base / "cache"))
            paths = []
            def bootstrap(command, **kwargs):
                self.assertEqual(command[:3], ["/bin/launchctl", "bootstrap", "gui/" + str(os.getuid())])
                path = Path(command[3])
                paths.append(path)
                job = plistlib.loads(path.read_bytes())
                self.assertFalse(job["KeepAlive"])
                self.assertTrue(job["RunAtLoad"])
                self.assertEqual(path.stat().st_mode & 0o077, 0)
                self.assertNotIn("UNRELATED_CONTEXT", job["EnvironmentVariables"])
                return subprocess.CompletedProcess(command, 0)
            states = [{"state": "stopped", "running": False}, {"state": "running", "running": True}]
            with mock.patch.dict(os.environ, {"HOME": str(base), "PATH": "/usr/bin:/bin",
                 "SHELL": "/bin/sh", "UNRELATED_CONTEXT": "synthetic"}, clear=True), \
                 mock.patch.object(service, "installed", return_value=True), \
                 mock.patch.object(service, "_node", return_value="/synthetic/node"), \
                 mock.patch.object(service, "_remove_job"), \
                 mock.patch.object(service, "_prepare_helpers"), \
                 mock.patch.object(service, "status", side_effect=states), \
                 mock.patch("localbrain.terminal.runtime.subprocess.run", side_effect=bootstrap):
                self.assertTrue(service.start()["running"])
            self.assertEqual(len(paths), 1)
            self.assertFalse(paths[0].exists())

    def test_failed_reinstall_clears_readiness_and_offers_setup_again(self):
        with tempfile.TemporaryDirectory(prefix="lb-setup-", dir="/private/tmp") as folder:
            base = Path(folder)
            service = TerminalService(SimpleNamespace(data_dir=base / "data", cache_dir=base / "cache"), launcher="process")
            service.root.mkdir(mode=0o700, parents=True)
            marker = service.root / "engine-ready.json"
            marker.write_text(json.dumps({"lock": hashlib.sha256((PACKAGE / "runtime/package-lock.json").read_bytes()).hexdigest()}))
            marker.chmod(0o600)
            for name in ENGINE_ENTRIES:
                entry = service.root / "engine/node_modules" / name
                entry.parent.mkdir(parents=True, exist_ok=True)
                entry.write_text("synthetic module")
            self.assertTrue(service.installed())
            with mock.patch.object(service, "_node", return_value="/synthetic/node"), \
                 mock.patch.object(service, "status", return_value={"running": False}), \
                 mock.patch("localbrain.terminal.runtime.shutil.which", return_value="/synthetic/npm"), \
                 mock.patch("localbrain.terminal.runtime.subprocess.run", side_effect=subprocess.CalledProcessError(1, "npm")):
                with self.assertRaises(TerminalError) as error:
                    service.install()
            self.assertEqual(error.exception.code, "install_failed")
            self.assertFalse(service.dependencies()["installed"])

    def test_partial_engine_loss_offers_setup_even_with_matching_marker(self):
        with tempfile.TemporaryDirectory(prefix="lb-setup-", dir="/private/tmp") as folder:
            base = Path(folder)
            service = TerminalService(SimpleNamespace(data_dir=base / "data", cache_dir=base / "cache"), launcher="process")
            service.root.mkdir(mode=0o700, parents=True)
            marker = service.root / "engine-ready.json"
            marker.write_text(json.dumps({"lock": hashlib.sha256((PACKAGE / "runtime/package-lock.json").read_bytes()).hexdigest()}))
            marker.chmod(0o600)
            self.assertFalse(service.installed())
            for name in ENGINE_ENTRIES:
                entry = service.root / "engine/node_modules" / name
                entry.parent.mkdir(parents=True, exist_ok=True)
                entry.write_text("synthetic module")
            self.assertTrue(service.installed())
            for name in ENGINE_ENTRIES:
                entry = service.root / "engine/node_modules" / name
                entry.unlink()
                self.assertFalse(service.dependencies()["installed"])
                entry.write_text("synthetic module")


@unittest.skipUnless(os.environ.get("LOCALBRAIN_TERMINAL_TEST_ENGINE") and sys.platform == "darwin",
                     "real PTY check requires an explicitly prepared private engine")
class TerminalProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # macOS Unix sockets allow only a short pathname; the system TMPDIR is longer.
        cls.folder = tempfile.TemporaryDirectory(prefix="lb-terminal-test-", dir="/private/tmp")
        cls.base = Path(cls.folder.name)
        cls.home = cls.base / "home"
        cls.home.mkdir()
        cls.env = mock.patch.dict(os.environ, {"HOME": str(cls.home), "SHELL": "/bin/sh"})
        cls.env.start()
        cls.config = SimpleNamespace(data_dir=cls.base / "data", cache_dir=cls.base / "cache")
        cls.service = TerminalService(cls.config, launcher="process")
        cls.service.root.mkdir(mode=0o700, parents=True)
        shutil.copytree(os.environ["LOCALBRAIN_TERMINAL_TEST_ENGINE"], cls.service.root / "engine")
        lock = hashlib.sha256((PACKAGE / "runtime/package-lock.json").read_bytes()).hexdigest()
        marker = cls.service.root / "engine-ready.json"
        marker.write_text(json.dumps({"lock": lock}))
        marker.chmod(0o600)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.service.stop(force=True)
        finally:
            cls.env.stop()
            cls.folder.cleanup()

    def tearDown(self):
        self.service.stop(force=True)

    def create(self, **extra):
        return self.service.create({"key": str(uuid.uuid4()), "cwd": str(self.home),
                                    "shell": "/bin/sh", **extra})

    def write(self, terminal, data, lease=None):
        lease = lease or self.service.rpc("claim", {"id": terminal, "unicodeVersion": "11", "checkpointVersion": "xterm6-v3"})["lease"]
        self.service.rpc("input", {"id": terminal, "lease": lease, "data": data})
        return lease

    def expected(self, ids=None):
        current = self.service.list()
        return {"generation": current["generation"],
                "terminals": ids if ids is not None else [term["id"] for term in current["terminals"]]}

    def await_text(self, terminal, text, timeout=4):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            frame = self.service.rpc("read", {"id": terminal, "after": -1})
            if text in frame["data"]:
                return frame
            time.sleep(.02)
        self.fail("Synthetic terminal marker was not observed")

    def test_inspection_is_read_only_and_new_shell_executes(self):
        self.assertFalse(self.service.list()["running"])
        self.assertFalse(self.service.socket.exists())
        result = self.create()
        terminal = result["terminal"]["id"]
        self.write(terminal, "printf 'RUNTIME_%s\\n' READY\r")
        frame = self.await_text(terminal, "RUNTIME_READY")
        self.assertTrue(frame["snapshot"])
        self.assertEqual(len(self.service.list()["terminals"]), 1)
        self.service.rpc("stop", {"id": terminal})
        self.assertEqual(self.service.list()["terminals"], [])
        self.assertTrue(self.service.status()["running"])

    def test_saved_launch_defaults_only_change_future_instances(self):
        from localbrain.terminal.settings import launch_parameters, read_launch_settings, save_launch_settings
        first_folder = self.base / "launch-a"
        second_folder = self.base / "launch-b"
        first_folder.mkdir(); second_folder.mkdir()
        with mock.patch.dict(os.environ, {"ZDOTDIR": str(self.home)}):
            settings = read_launch_settings(self.config)
            settings = save_launch_settings(self.config, str(first_folder), "/bin/sh", settings["revision"])
            first = self.service.create({"key": str(uuid.uuid4()), **launch_parameters(self.config)})["terminal"]
            save_launch_settings(self.config, str(second_folder), "/bin/zsh", settings["revision"])
            second = self.service.create({"key": str(uuid.uuid4()), **launch_parameters(self.config)})["terminal"]
            self.assertEqual((first["cwd"], first["shell"]), (str(first_folder), "/bin/sh"))
            self.assertEqual((second["cwd"], second["shell"]), (str(second_folder), "/bin/zsh"))
            current = next(t for t in self.service.list()["terminals"] if t["id"] == first["id"])
            self.assertEqual(current["pid"], first["pid"])
            self.write(first["id"], "printf 'DEFAULT_%s\\n' ALIVE\r")
            self.await_text(first["id"], "DEFAULT_ALIVE")

    def test_saved_invalid_defaults_do_not_start_manager(self):
        from localbrain.foundation.preferences import PreferencesError
        from localbrain.terminal.settings import launch_parameters, read_launch_settings, save_launch_settings
        folder = self.base / "removed-launch-folder"
        folder.mkdir()
        settings = read_launch_settings(self.config)
        save_launch_settings(self.config, str(folder), "/bin/sh", settings["revision"])
        folder.rmdir()
        with self.assertRaises(PreferencesError):
            launch_parameters(self.config)
        self.assertFalse(self.service.status()["running"])

    def test_create_retry_keeps_original_snapshot_after_defaults_change_or_disappear(self):
        from localbrain.terminal.settings import launch_parameters, read_launch_settings, save_launch_settings
        folder = self.base / "retry-default"
        folder.mkdir()
        settings = save_launch_settings(self.config, str(folder), "/bin/sh", read_launch_settings(self.config)["revision"])
        request = {"key": str(uuid.uuid4()), **launch_parameters(self.config)}
        first = self.service.create(request)
        save_launch_settings(self.config, str(self.home), "/bin/zsh", settings["revision"])
        folder.rmdir()
        replay = self.service.create(request)
        self.assertEqual(replay["terminal"]["id"], first["terminal"]["id"])
        self.assertEqual(replay["terminal"]["pid"], first["terminal"]["pid"])
        self.assertEqual(len(self.service.list()["terminals"]), 1)

    def test_immediate_shell_exit_does_not_leave_an_unmanageable_record(self):
        script = self.home / "exit-shell"
        script.write_text("#!/bin/sh\nexit 0\n")
        script.chmod(0o700)
        terminal = self.create(shell=str(script))["terminal"]["id"]
        until = time.monotonic() + 4
        while time.monotonic() < until:
            frame = self.service.rpc("read", {"id": terminal, "after": -1})
            if frame["terminal"]["state"] == "exited":
                break
            time.sleep(.02)
        self.assertEqual(frame["terminal"]["state"], "exited")
        self.service.rpc("stop", {"id": terminal})
        self.assertFalse(self.service.list()["terminals"])

    def test_snapshot_unicode_alternate_modes_and_background_keep_pid(self):
        result = self.create()
        terminal, tab = result["terminal"]["id"], result["tabId"]
        self.write(terminal, "printf '\\033[?1049h\\033[2J\\033[3;4H한글_%s\\033[?2004h' READY\r")
        frame = self.await_text(terminal, "한글_READY")
        self.assertIn("\x1b[?1049h", frame["data"])
        pid = result["terminal"]["pid"]
        self.service.rpc("tab", {"id": tab, "action": "hide"})
        self.assertTrue(self.service.list()["tabs"][0]["hidden"])
        self.service.rpc("tab", {"id": tab, "action": "show"})
        self.assertEqual(self.service.list()["terminals"][0]["pid"], pid)
        self.assertIn("한글_READY", self.service.rpc("read", {"id": terminal, "after": -1})["data"])

    def test_incompatible_view_cannot_claim_a_new_width_terminal(self):
        terminal = self.create()["terminal"]["id"]
        for version in (None, "6", "future"):
            params = {"id": terminal}
            if version is not None:
                params["unicodeVersion"] = version
            with self.assertRaises(TerminalError) as result:
                self.service.rpc("claim", params)
            self.assertEqual(result.exception.code, "client_update_required")
            self.assertFalse(self.service.list()["terminals"][0]["controlled"])
        accepted = self.service.rpc("claim", {"id": terminal, "unicodeVersion": "11", "checkpointVersion": "xterm6-v3"})
        self.assertTrue(accepted["writable"])

    def test_checkpoint_version_is_required_before_input_lease(self):
        terminal = self.create()["terminal"]["id"]
        for version in (None, "xterm6-v1", "future"):
            with self.subTest(version=version), self.assertRaises(TerminalError) as result:
                self.service.rpc("claim", {"id": terminal, "unicodeVersion": "11", "checkpointVersion": version})
            self.assertEqual(result.exception.code, "client_update_required")
            self.assertFalse(self.service.list()["terminals"][0]["controlled"])

    def test_checkpoint_rpc_preserves_partial_control_and_hidden_alternate_cells(self):
        go = self.home / "checkpoint-continue"
        code = ("import sys,time\nfrom pathlib import Path\n"
                "sys.stdout.write('\\x1b[?1049h'+'R'*30+'\\x1b[31');sys.stdout.flush()\n"
                "while not Path(" + repr(str(go)) + ").exists():time.sleep(.01)\n"
                "sys.stdout.write('mX');sys.stdout.flush();time.sleep(60)\n")
        shell = self.home / "checkpoint-shell"
        shell.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " -c " + shlex.quote(code) + "\n")
        shell.chmod(0o700)
        terminal = self.create(shell=str(shell), cols=30, rows=8)["terminal"]["id"]
        self.await_text(terminal, "R" * 30)
        lease = self.service.rpc("claim", {"id": terminal, "unicodeVersion": "11", "checkpointVersion": "xterm6-v3"})["lease"]
        params = {"id": terminal, "after": -1, "checkpointVersion": "xterm6-v3"}
        before_resize = self.service.rpc("read", params)
        self.service.rpc("resize", {"id": terminal, "lease": lease, "cols": 17, "rows": 8})
        frame = self.service.rpc("read", {**params, "after": before_resize["seq"]})
        self.assertTrue(frame["snapshot"])
        self.assertEqual(frame["data"], "")
        self.assertEqual(frame["checkpoint"]["cols"], 17)
        self.assertEqual(frame["checkpoint"]["buffers"][1]["lines"][0]["width"], 30)
        self.assertEqual(frame["checkpoint"]["parser"]["state"], 4)
        go.write_text("continue")
        until = time.monotonic() + 4
        while time.monotonic() < until:
            continued = self.service.rpc("read", params)
            if continued["checkpoint"]["parser"]["state"] == 0:
                break
            time.sleep(.02)
        script = """
const fs=require('node:fs'),path=require('node:path');
const {Terminal}=require(path.join(process.argv[1],'node_modules/@xterm/headless'));
const cp=require(process.argv[2]),frame=JSON.parse(fs.readFileSync(0,'utf8'));
const t=new Terminal({cols:17,rows:8,allowProposedApi:true});
cp.restore(t,frame.checkpoint);t.write('mX',()=>{console.log(JSON.stringify(cp.capture(t).buffers));t.dispose()});
"""
        observed = json.loads(subprocess.check_output([shutil.which("node"), "-e", script,
                              str(self.service.root / "engine"), str(PACKAGE / "checkpoint.cjs")],
                              input=json.dumps(frame), text=True))
        self.assertEqual(observed, continued["checkpoint"]["buffers"])

    def test_oversized_active_checkpoint_fails_explicitly_and_recovers_without_replay(self):
        go = self.home / "checkpoint-limit-continue"
        code = ("import sys,time\nfrom pathlib import Path\n"
                "sys.stdout.write('A'+'\\u0301'*(2*1024*1024));sys.stdout.flush()\n"
                "while not Path(" + repr(str(go)) + ").exists():time.sleep(.01)\n"
                "sys.stdout.write('\\x1bcRECOVERED');sys.stdout.flush();time.sleep(60)\n")
        shell = self.home / "checkpoint-limit-shell"
        shell.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " -c " + shlex.quote(code) + "\n")
        shell.chmod(0o700)
        terminal = self.create(shell=str(shell), cols=30, rows=8)["terminal"]
        params = {"id": terminal["id"], "after": -1, "checkpointVersion": "xterm6-v3"}
        until, limited = time.monotonic() + 8, False
        while time.monotonic() < until:
            try:
                self.service.rpc("read", params)
            except TerminalError as error:
                self.assertEqual(error.code, "checkpoint_limit")
                limited = True
                break
            time.sleep(.02)
        self.assertTrue(limited)
        self.assertEqual(self.service.list()["terminals"][0]["pid"], terminal["pid"])
        go.write_text("continue")
        until, recovered_state = time.monotonic() + 8, None
        while time.monotonic() < until:
            try:
                recovered_state = self.service.rpc("read", params)
                break
            except TerminalError as error:
                self.assertEqual(error.code, "checkpoint_limit")
            time.sleep(.02)
        self.assertIsNotNone(recovered_state)
        recovered = self.await_text(terminal["id"], "RECOVERED", timeout=8)
        self.assertEqual(recovered["terminal"]["pid"], terminal["pid"])
        self.assertEqual(self.service.rpc("read", params)["checkpoint"]["version"], "xterm6-v3")

    def test_unicode_widths_match_for_mixed_hangul_and_modern_emoji(self):
        result = self.create()["terminal"]
        self.assertEqual(result["unicodeVersion"], "11")
        self.write(result["id"], "printf 'UNICODE|A%s한B|END\\n' '🧠'\r")
        frame = self.await_text(result["id"], "UNICODE|A🧠한B|END")
        script = """
const path=require('node:path'), engine=process.argv[1];
const {Terminal}=require(path.join(engine,'node_modules/@xterm/headless'));
const {Unicode11Addon}=require(path.join(engine,'node_modules/@xterm/addon-unicode11'));
const data=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
const t=new Terminal({cols:data.terminal.cols,rows:data.terminal.rows,allowProposedApi:true});
t.loadAddon(new Unicode11Addon());t.unicode.activeVersion='11';
t.write(data.data,()=>{
  const b=t.buffer.active;
  for(let y=0;y<b.length;y++){
    const line=b.getLine(y);
    if(line.translateToString(true).startsWith('UNICODE|')){
      console.log(JSON.stringify([line.getCell(9).getChars(),line.getCell(9).getWidth(),
        line.getCell(11).getChars(),line.getCell(11).getWidth(),line.getCell(13).getChars()]));
      t.dispose();return;
    }
  }
  process.exitCode=1;t.dispose();
});
"""
        observed = json.loads(subprocess.check_output([shutil.which("node"), "-e", script,
                                                      str(self.service.root / "engine")],
                                                     input=json.dumps(frame), text=True))
        self.assertEqual(observed, ["🧠", 2, "한", 2, "B"])

    def test_login_interactive_startup_and_zdotdir_are_preserved(self):
        folder = self.home / "synthetic-zsh-config"
        folder.mkdir()
        (folder / ".zprofile").write_text("export LB_SYNTHETIC_LOGIN=READY\n")
        (folder / ".zshrc").write_text("printf 'STARTUP_%s\\n' $LB_SYNTHETIC_LOGIN\n")
        with mock.patch.dict(os.environ, {"ZDOTDIR": str(folder)}):
            terminal = self.create(shell="/bin/zsh")["terminal"]["id"]
        self.await_text(terminal, "STARTUP_READY")

    def test_manager_crash_reports_uncertain_work_and_never_replays(self):
        terminal = self.create()["terminal"]["id"]
        self.write(terminal, "printf 'CRASH_%s\\n' READY\r")
        self.await_text(terminal, "CRASH_READY")
        old = self.service.list()
        pty_pid = old["terminals"][0]["pid"]
        owned = [item for item in process_table() if item["pid"] == pty_pid or item["session"] == pty_pid]
        try:
            manager = self.service.status()["pid"]
            self.assertEqual(manager, self.service._process.pid)
            os.kill(manager, 9)  # Controlled failure injection, never a product stop path.
            self.service._process.wait(timeout=4)
            self.assertTrue(self.service.status()["unclean"])
            self.assertFalse(self.service.list()["running"])
            with self.assertRaises(TerminalError):
                self.service.restart(force=True)
            fresh = self.create()["terminal"]["id"]
            self.assertNotEqual(self.service.list()["generation"], old["generation"])
            frame = self.service.rpc("read", {"id": fresh, "after": -1})
            self.assertNotIn("CRASH_READY", frame["data"])
            self.assertEqual(len(self.service.list()["terminals"]), 1)
        finally:
            current = {item["pid"]: item for item in process_table()}
            for before in owned:
                now = current.get(before["pid"])
                if now and all(now[key] == before[key] for key in ("born", "group", "session")):
                    with contextlib.suppress(ProcessLookupError):
                        os.kill(before["pid"], 9)
    def test_idempotent_create_pane_limit_and_explicit_path_validation(self):
        params = {"key": str(uuid.uuid4()), "cwd": str(self.home), "shell": "/bin/sh"}
        first = self.service.create(params)
        second = self.service.create(params)
        self.assertEqual(first["terminal"]["id"], second["terminal"]["id"])
        for _ in range(3):
            self.create(tabId=first["tabId"])
        with self.assertRaises(TerminalError):
            self.create(tabId=first["tabId"])
        for field, value in (("cwd", False), ("cwd", str(self.home / "absent")), ("shell", False), ("cols", 0)):
            with self.subTest(field=field), self.assertRaises(TerminalError):
                self.create(**{field: value})
        self.assertEqual(len(self.service.list()["terminals"]), 4)

    def test_lease_takeover_blocks_old_input_resize_and_release(self):
        terminal = self.create()["terminal"]["id"]
        old = self.service.rpc("claim", {"id": terminal, "unicodeVersion": "11", "checkpointVersion": "xterm6-v3"})["lease"]
        self.assertFalse(self.service.rpc("claim", {"id": terminal, "unicodeVersion": "11", "checkpointVersion": "xterm6-v3"})["writable"])
        new = self.service.rpc("claim", {"id": terminal, "takeover": True, "unicodeVersion": "11", "checkpointVersion": "xterm6-v3"})["lease"]
        with self.assertRaises(TerminalError) as binary_error:
            self.service.rpc("binary", {"id": terminal, "lease": old, "data": "gA=="})
        self.assertEqual(binary_error.exception.code, "not_owner")
        for method, params in (("input", {"data": "should-not-type"}), ("resize", {"cols": 90, "rows": 30})):
            with self.subTest(method=method), self.assertRaises(TerminalError) as error:
                self.service.rpc(method, {"id": terminal, "lease": old, **params})
            self.assertEqual(error.exception.code, "not_owner")
        self.service.rpc("release", {"id": terminal, "lease": old})
        self.write(terminal, "printf 'OWNER_%s\\n' READY\r", new)
        self.await_text(terminal, "OWNER_READY")

    def test_restart_ends_owned_children_and_never_replays(self):
        terminal = self.create()["terminal"]["id"]
        self.write(terminal, "sleep 30 & printf 'OWNED_CHILD=%s\\n' $!\r")
        frame = self.await_text(terminal, "OWNED_CHILD=")
        match = re.search(r"OWNED_CHILD=(\d+)", frame["data"])
        until = time.monotonic() + 2
        while match is None and time.monotonic() < until:
            time.sleep(.02)
            frame = self.service.rpc("read", {"id": terminal, "after": -1})
            match = re.search(r"OWNED_CHILD=(\d+)", frame["data"])
        self.assertIsNotNone(match, repr(frame["data"]))
        child = int(match.group(1))
        before = self.service.status()["generation"]
        self.service.restart()
        self.assertNotEqual(before, self.service.status()["generation"])
        self.assertEqual(self.service.list()["terminals"], [])
        with self.assertRaises(ProcessLookupError):
            os.kill(child, 0)

    def test_normal_shell_exit_cleans_ordinary_background_job(self):
        terminal = self.create(shell="/bin/bash")["terminal"]["id"]
        lease = self.write(terminal, "set +H; shopt -u huponexit; sleep 30 & printf 'ORDINARY_%s=%s\\n' CHILD $!\r")
        frame = self.await_text(terminal, "ORDINARY_CHILD=")
        child = int(re.search(r"ORDINARY_CHILD=(\d+)", frame["data"]).group(1))
        try:
            self.write(terminal, "exit\r", lease)
            until = time.monotonic() + 5
            while time.monotonic() < until:
                if self.service.rpc("read", {"id": terminal, "after": -1})["terminal"]["state"] == "exited":
                    break
                time.sleep(.02)
            state = subprocess.run(["/bin/ps", "-p", str(child), "-o", "stat="], capture_output=True, text=True).stdout
            self.assertTrue(not state.strip() or "Z" in state, state)
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.kill(child, 9)

    def test_stale_bulk_generation_or_scope_never_ends_new_work(self):
        first = self.create()["terminal"]["id"]
        before = self.expected()
        second = self.create()["terminal"]["id"]
        with self.assertRaises(TerminalError) as error:
            self.service.rpc("stop", {"all": True, "expected": before})
        self.assertEqual(error.exception.code, "conflict")
        self.assertEqual({term["id"] for term in self.service.list()["terminals"]}, {first, second})
        self.service.restart()
        fresh = self.create()["terminal"]["id"]
        with self.assertRaises(TerminalError):
            self.service.rpc("stop", {"all": True, "expected": before})
        with self.assertRaises(TerminalError):
            self.service.stop(expected=before)
        self.assertEqual(self.service.list()["terminals"][0]["id"], fresh)

    def test_delayed_restart_cannot_resurrect_stopped_generation(self):
        self.create()
        old = self.expected()
        self.service.stop()
        with self.assertRaises(TerminalError) as error:
            self.service.restart(expected=old)
        self.assertEqual(error.exception.code, "conflict")
        self.assertFalse(self.service.status()["running"])
        self.service.restart(expected={"generation": None, "terminals": []})
        self.assertTrue(self.service.status()["running"])
        self.assertFalse(self.service.list()["terminals"])

    def test_failed_create_can_retry_same_key_then_deduplicates_success(self):
        folder = self.home / "created-after-failure"
        body = {"key": str(uuid.uuid4()), "cwd": str(folder), "shell": "/bin/sh"}
        with self.assertRaises(TerminalError):
            self.service.create(body)
        folder.mkdir()
        first = self.service.create(body)
        self.assertEqual(first["terminal"]["id"], self.service.create(body)["terminal"]["id"])
        self.assertEqual(len(self.service.list()["terminals"]), 1)

    def test_live_creation_key_survives_closed_request_history_pressure(self):
        body = {"key": str(uuid.uuid4()), "cwd": str(self.home), "shell": "/bin/sh"}
        original = self.service.create(body)["terminal"]["id"]
        fast = self.home / "history-exit-shell"
        fast.write_text("#!/bin/sh\nexit 0\n")
        fast.chmod(0o700)
        for _ in range(258):
            term = self.create(shell=str(fast))["terminal"]["id"]
            self.service.rpc("stop", {"id": term})
        self.assertEqual(self.service.create(body)["terminal"]["id"], original)
        self.assertEqual(len(self.service.list()["terminals"]), 1)

    def test_concurrent_split_reserves_the_last_pane_before_inspection(self):
        first = self.create()
        tab = first["tabId"]
        for _ in range(2):
            self.create(tabId=tab)
        outcomes = []
        def split():
            try:
                outcomes.append(self.service.rpc("create", {"key": str(uuid.uuid4()), "tabId": tab,
                    "cwd": str(self.home), "shell": "/bin/sh"}))
            except TerminalError as error:
                outcomes.append(error.code)
        threads = [threading.Thread(target=split) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=8)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(outcomes.count("limit"), 2)
        self.assertEqual(len(self.service.list()["tabs"][0]["terminals"]), 4)

    def test_stop_during_creation_waits_for_identity_and_leaves_no_shell(self):
        self.service.start()
        outcomes = []
        def create():
            outcomes.append(self.service.rpc("create", {"key": str(uuid.uuid4()), "cwd": str(self.home), "shell": "/bin/sh"}))
        thread = threading.Thread(target=create)
        thread.start()
        until = time.monotonic() + 3
        current = self.service.list()
        while not current["terminals"] and time.monotonic() < until:
            time.sleep(.005)
            current = self.service.list()
        self.assertTrue(current["terminals"])
        pid = current["terminals"][0]["pid"]
        self.service.rpc("stop", {"all": True, "expected": self.expected()})
        thread.join(timeout=8)
        self.assertFalse(thread.is_alive())
        self.assertTrue(outcomes)
        self.assertFalse(self.service.list()["terminals"])
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_binary_mouse_transport_preserves_high_bytes(self):
        terminal = self.create()["terminal"]["id"]
        program = ("import os,tty,termios; old=termios.tcgetattr(0); tty.setraw(0); "
                   "print('RAW_'+'READY',flush=True); "
                   "exec(\"data=b''\\nwhile len(data)<4: data+=os.read(0,4-len(data))\"); "
                   "termios.tcsetattr(0,termios.TCSANOW,old); print('RAW_HEX='+data.hex(),flush=True)")
        lease = self.write(terminal, "python3 -c " + shlex.quote(program) + "\r")
        self.await_text(terminal, "RAW_READY")
        self.service.rpc("binary", {"id": terminal, "lease": lease, "data": base64.b64encode(b"\x1b\x80\xffM").decode()})
        self.await_text(terminal, "RAW_HEX=1b80ff4d")

    def test_stop_all_blocks_concurrent_create(self):
        terminal = self.create()["terminal"]["id"]
        self.write(terminal, "trap '' HUP TERM; printf 'STOP_%s\\n' READY\r")
        self.await_text(terminal, "STOP_READY")
        outcome = []
        expected = self.expected()
        thread = threading.Thread(target=lambda: outcome.append(self.service.rpc("stop", {"all": True, "expected": expected})))
        thread.start()
        try:
            until = time.monotonic() + 2
            while not self.service.status().get("stopping") and time.monotonic() < until:
                time.sleep(.01)
            with self.assertRaises(TerminalError):
                self.create()
        finally:
            thread.join(timeout=8)
        self.assertFalse(thread.is_alive())
        self.assertTrue(outcome)
        self.assertEqual(self.service.list()["terminals"], [])

    def test_flood_is_bounded_and_control_stays_available(self):
        terminal = self.create()["terminal"]["id"]
        self.write(terminal, "python3 -c \"import sys; sys.stdout.write('x'*3000000); print('FLOOD_'+'DONE')\"\r")
        latencies = []
        for _ in range(20):
            start = time.perf_counter()
            self.service.status()
            latencies.append(time.perf_counter() - start)
            time.sleep(.01)
        self.await_text(terminal, "FLOOD_DONE", timeout=10)
        self.assertLess(max(latencies), .5)
        frame = self.service.rpc("read", {"id": terminal, "after": 0})
        self.assertTrue(frame["snapshot"])
        self.assertLess(len(frame["data"].encode()), 1024 * 1024)

    def test_query_reply_flood_is_contained_and_other_work_remains_usable(self):
        script = self.home / "unread-queries.py"
        script.write_text("#!" + sys.executable + "\nimport os,tty,time\ntty.setraw(0)\n"
                          "chunk=b'\\x1b[6n'*4000\nfor _ in range(50): os.write(1,chunk)\ntime.sleep(30)\n")
        script.chmod(0o700)
        terminal = self.create(shell=str(script))["terminal"]["id"]
        deadline = time.monotonic() + 6
        fault = None
        latencies = []
        while time.monotonic() < deadline:
            start = time.monotonic()
            current = self.service.list()
            latencies.append(time.monotonic() - start)
            fault = next(row for row in current["terminals"] if row["id"] == terminal)["inputError"]
            if fault:
                break
            time.sleep(.03)
        self.assertTrue(fault, "unread replies must reach a bounded, explicit per-terminal fault")
        self.assertLess(max(latencies), 1)
        other = self.create()["terminal"]["id"]
        self.write(other, "printf 'OTHER_%s\\n' HEALTHY\r")
        self.await_text(other, "OTHER_HEALTHY")
        self.service.rpc("stop", {"id": terminal})
        self.assertEqual([row["id"] for row in self.service.list()["terminals"]], [other])

    def test_bounded_input_does_not_deadlock_a_cooperative_duplex_program(self):
        count = self.home / "duplex-count"
        count.unlink(missing_ok=True)
        ready = self.home / "duplex-ready"
        ready.unlink(missing_ok=True)
        script = self.home / "duplex.py"
        script.write_text("#!" + sys.executable + "\nimport os,tty,time\nfrom pathlib import Path\n"
                          "tty.setraw(0)\nPath(" + repr(str(ready)) + ").write_text('ready')\n"
                          "time.sleep(.4)\nn=0\nwhile True:\n"
                          " d=os.read(0,4096)\n if not d:break\n left=d\n"
                          " while left:left=left[os.write(1,left):]\n n+=len(d)\n"
                          " Path(" + repr(str(count)) + ").write_text(str(n))\n")
        script.chmod(0o700)
        terminal = self.create(shell=str(script))["terminal"]["id"]
        deadline = time.monotonic() + 3
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(ready.exists())
        lease = self.service.rpc("claim", {"id": terminal, "unicodeVersion": "11", "checkpointVersion": "xterm6-v3"})["lease"]
        accepted = 0
        for _ in range(6):
            try:
                self.write(terminal, "A" * 65536, lease)
                accepted += 65536
            except TerminalError as error:
                self.assertEqual(error.code, "input_busy")
        self.assertGreaterEqual(accepted, 128 * 1024)
        delivered = 0
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and delivered < accepted:
            with contextlib.suppress(FileNotFoundError, ValueError):
                delivered = int(count.read_text())
            time.sleep(.02)
        self.assertEqual(delivered, accepted)
        self.assertIsNone(self.service.list()["terminals"][0]["inputError"])

    def test_detached_color_query_has_exactly_one_headless_response(self):
        result = self.home / "color-response.json"
        result.unlink(missing_ok=True)
        script = self.home / "color-query.py"
        script.write_text("#!" + sys.executable + "\nimport os,tty,time,select,json\nfrom pathlib import Path\n"
                          "tty.setraw(0)\nos.write(1,b'\\x1b]11;?\\x1b\\\\')\nreply=b''\n"
                          "end=time.monotonic()+.6\nwhile time.monotonic()<end:\n"
                          " r,_,_=select.select([0],[],[],.05)\n if r: reply+=os.read(0,4096)\n"
                          "Path(" + repr(str(result)) + ").write_text(json.dumps(reply.hex()))\ntime.sleep(30)\n")
        script.chmod(0o700)
        self.create(shell=str(script))
        deadline = time.monotonic() + 4
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertEqual(bytes.fromhex(json.loads(result.read_text())), b"\x1b]11;rgb:1919/1919/1919\x1b\\")

    def test_stale_identity_with_reused_pid_allows_fresh_start_without_signaling_it(self):
        self.service.stop(force=True)
        sleeper = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
        try:
            self.service._write_private("identity.json", {"pid": sleeper.pid, "generation": "stale-synthetic",
                                                         "version": 1, "build": "old", "born": "Thu Jan  1 00:00:00 1970",
                                                         "birthFormat": "utc-lstart-v1"})
            status = self.service.status()
            self.assertEqual(status["state"], "stopped")
            self.assertTrue(status["unclean"])
            fresh = self.service.start()
            self.assertTrue(fresh["running"])
            self.assertNotEqual(fresh["pid"], sleeper.pid)
            self.assertEqual(self.service.list()["terminals"], [])
            self.assertEqual(self.service._identity()["birthFormat"], "utc-lstart-v1")
            with mock.patch.dict(os.environ, {"TZ": "Pacific/Honolulu"}), \
                 mock.patch.object(self.service, "rpc", side_effect=TerminalError("unavailable", "synthetic outage")):
                self.assertEqual(self.service.status()["state"], "unknown")
            self.assertIsNone(sleeper.poll())
            self.service.stop(force=True)
            self.assertIsNone(sleeper.poll())
        finally:
            sleeper.terminate()
            sleeper.wait(timeout=3)

    def test_inspection_failure_marks_target_and_retry_preserves_identity(self):
        copied = self.base / "isolated-package"
        shutil.copytree(PACKAGE, copied, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        helper = copied / "processes.py"
        original = helper.read_bytes()
        with mock.patch("localbrain.terminal.runtime.PACKAGE", copied):
            terminal = self.create()["terminal"]["id"]
            try:
                helper.write_text("raise RuntimeError('synthetic inspection failure')\n")
                with self.assertRaises(TerminalError) as error:
                    self.service.rpc("stop", {"id": terminal})
                self.assertEqual(error.exception.code, "runtime_error")
                self.assertTrue(self.service.list()["terminals"][0]["error"])
                self.assertEqual(self.service.list()["terminals"][0]["state"], "running")
            finally:
                helper.write_bytes(original)
            self.service.rpc("stop", {"id": terminal})
            self.assertFalse(self.service.list()["terminals"])
