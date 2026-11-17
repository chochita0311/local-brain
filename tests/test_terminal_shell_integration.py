import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock
import uuid

from localbrain.terminal.shell_integration import integrated_shell, ShellIntegrationError


class ShellFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lb-zsh-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = SimpleNamespace(data_dir=self.root / "data", cache_dir=self.root / "cache")


class ShellIntegrationTests(ShellFixture, unittest.TestCase):

    def test_other_shells_do_not_create_integration_files(self):
        self.assertEqual(integrated_shell(self.config, "/bin/sh"), "/bin/sh")
        self.assertFalse(self.config.data_dir.exists())

    @unittest.skipUnless(Path("/bin/zsh").is_file(), "zsh required")
    def test_preparation_is_stable_and_recovers_only_matching_owned_partial_files(self):
        from localbrain.terminal import shell_integration as module
        original = module.atomic_private_write
        writes = 0
        def interrupted(path, data):
            nonlocal writes
            writes += 1
            if writes == 3: raise OSError("synthetic interruption")
            original(path, data)
        with mock.patch.object(module, "atomic_private_write", side_effect=interrupted):
            with self.assertRaises(OSError): integrated_shell(self.config, "/bin/zsh")
        first = integrated_shell(self.config, "/bin/zsh")
        snapshot = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(first).parent.iterdir()}
        self.assertEqual(integrated_shell(self.config, "/bin/zsh"), first)
        self.assertEqual(integrated_shell(self.config, first), first)
        self.assertEqual(snapshot, {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(first).parent.iterdir()})
        self.assertEqual(Path(first).stat().st_mode & 0o777, 0o700)

    @unittest.skipUnless(Path("/bin/zsh").is_file(), "zsh required")
    def test_corrupt_or_linked_published_resources_are_never_rewritten(self):
        first = Path(integrated_shell(self.config, "/bin/zsh"))
        hooks = first.parent / "hooks.zsh"
        hooks.write_text("synthetic corruption")
        with self.assertRaises(ShellIntegrationError): integrated_shell(self.config, str(first))
        self.assertEqual(hooks.read_text(), "synthetic corruption")
        hooks.unlink(); keep = self.root / "keep"; keep.write_text("keep"); keep.chmod(0o600); hooks.symlink_to(keep)
        with self.assertRaises(ShellIntegrationError): integrated_shell(self.config, "/bin/zsh")
        self.assertEqual(keep.read_text(), "keep")


@unittest.skipUnless(os.environ.get("LOCALBRAIN_TERMINAL_TEST_BUNDLE") and Path("/bin/zsh").is_file(), "explicit public payload and zsh required")
class ZshPtyTests(ShellFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.config.data_dir = self.root / "data ' # 한글"
        self.home = self.root / "home"; self.home.mkdir()
        self.folder = self.root / "first"; self.folder.mkdir()
        bundle = Path(os.environ["LOCALBRAIN_TERMINAL_TEST_BUNDLE"]).resolve()
        self.environment = mock.patch.dict(os.environ, {"HOME":str(self.home), "SHELL":"/bin/zsh",
            "LOCALBRAIN_TERMINAL_BUNDLE":str(bundle), "LOCALBRAIN_TERMINAL_RUNTIME":str(bundle / "bin/localbrain-runtime"),
            "LOCALBRAIN_TERMINAL_LAUNCHER":"process", "HF_HUB_CACHE":str(self.root / "public-cache")})
        self.environment.start(); self.addCleanup(self.environment.stop)
        from localbrain.terminal.core import TerminalService
        self.control = TerminalService(self.config, launcher="process")
        self.streams = []
        self.addCleanup(self.stop_owned)

    def stop_owned(self):
        for stream in self.streams: stream.close()
        current = self.control.list()
        if current["running"]:
            self.control.stop(force=True, expected={"generation":current["generation"], "terminals":[term["id"] for term in current["terminals"]]})

    def start(self):
        from test_terminal_runtime_parity import Stream
        shell = integrated_shell(self.config, "/bin/zsh")
        result = self.control.create({"key":uuid.uuid4().hex, "cwd":str(self.folder), "shell":shell})
        self.terminal = result["terminal"]["id"]
        stream = Stream(self.control, self.terminal); self.streams.append(stream)
        for _ in range(40):
            frame = stream.output()
            if frame["terminal"].get("activity", {}).get("state") == "prompt": return stream
        self.fail("zsh initial prompt signal unavailable")

    def command(self, stream, text, code):
        before = self.control.list()["terminals"][0]["activity"]["completion"]
        stream.send({"type":"input", "data":text + "\r"})
        running = False
        for _ in range(80):
            frame = stream.output(); activity = frame["terminal"]["activity"]
            running |= activity["state"] == "running"
            if activity["completion"] > before and activity["state"] == "prompt":
                self.assertEqual(activity["exitCode"], code)
                return running
        self.fail("zsh command completion unavailable")

    def test_status_and_cwd_with_user_hooks_preserves_startup_files_and_execution(self):
        rc = self.home / ".zshrc"
        rc.write_text("PROMPT='probe> '\nprecmd() { return 19; }\nprior_hook() { return 23; }\nprecmd_functions=(prior_hook)\nprint rc >> \"$HOME/started\"\n")
        before = rc.read_bytes(); stream = self.start()
        self.assertEqual((self.home / "started").read_text().splitlines(), ["rc"])
        self.assertTrue(self.command(stream, "sleep 0.2; false", 1))
        self.command(stream, "true", 0)
        self.command(stream, "sh -c 'exit 37'", 37)
        self.command(stream, "false | true", 0)
        self.command(stream, "setopt PIPE_FAIL", 0)
        self.command(stream, "false | true", 1)
        other = self.root / "한글 # 100%"; other.mkdir()
        import shlex
        self.command(stream, "cd " + shlex.quote(str(other)), 0)
        state = self.control.list()["terminals"][0]
        self.assertEqual(state["cwd"], str(other))
        self.assertEqual(rc.read_bytes(), before)
        self.assertEqual(state["id"], self.terminal)

    def test_startup_directory_changes_are_chained_and_user_zdotdir_is_restored(self):
        first = self.root / "rc first"; first.mkdir()
        second = self.root / "rc second"; second.mkdir()
        third = self.root / "rc third"; third.mkdir()
        import shlex
        (self.home / ".zshenv").write_text("print env >> \"$HOME/order\"\nZDOTDIR=" + shlex.quote(str(first)) + "\n")
        (first / ".zprofile").write_text("print profile >> \"$HOME/order\"\nZDOTDIR=" + shlex.quote(str(second)) + "\n")
        (second / ".zshrc").write_text("print rc >> \"$HOME/order\"\nZDOTDIR=" + shlex.quote(str(third)) + "\n")
        (third / ".zlogin").write_text("print login >> \"$HOME/order\"\nprint -r -- \"$ZDOTDIR\" > \"$HOME/final-dir\"\n")
        stream = self.start()
        self.assertEqual((self.home / "order").read_text().splitlines(), ["env", "profile", "rc", "login"])
        self.assertEqual((self.home / "final-dir").read_text().strip(), str(third))
        self.command(stream, "[[ $ZDOTDIR = " + shlex.quote(str(third)) + " ]]", 0)
