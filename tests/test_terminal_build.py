"""Synthetic build admission/provenance regressions; no downloads or app execution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("terminal_runtime_builder",ROOT/"scripts/build-terminal-runtime.py")
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


class TerminalBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="lb-payload-build-")
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()

    def test_parent_marker_never_authorizes_unrelated_sibling_or_alias(self):
        (self.root/builder.OWNER).write_bytes(builder.OWNER_BYTES)
        unrelated=self.root/"personal";unrelated.mkdir();canary=unrelated/"canary.txt";canary.write_text("synthetic keep")
        with mock.patch.object(builder.platform,"system",return_value="Darwin"),mock.patch.object(builder.platform,"machine",return_value="arm64"),mock.patch.object(builder,"run") as run:
            with self.assertRaisesRegex(ValueError,"unowned"):builder.build(unrelated)
            run.assert_not_called()
        self.assertEqual(canary.read_text(),"synthetic keep")
        owned=self.root/"runtime";owned.mkdir();(owned/builder.OWNER).write_bytes(builder.OWNER_BYTES)
        alias=self.root/"alias";alias.symlink_to(owned,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,"linked"):builder.output_path(alias)
        self.assertTrue((owned/builder.OWNER).is_file())

    def test_output_ownership_requires_its_own_regular_marker(self):
        output=self.root/"runtime";output.mkdir();marker=output/builder.OWNER
        marker.write_bytes(builder.OWNER_BYTES)
        self.assertEqual(builder.output_path(output),output)
        marker.unlink();marker.symlink_to(self.root/"unknown")
        with self.assertRaises(ValueError):builder.output_path(output)

    def test_redirected_cargo_artifact_wins_over_stale_default_path(self):
        stale=self.root/"default-runtime";stale.write_bytes(b"old")
        current=self.root/"redirected-target"/"aarch64-apple-darwin/release/localbrain-runtime"
        current.parent.mkdir(parents=True);current.write_bytes(b"current")
        artifact={"reason":"compiler-artifact","target":{"name":"localbrain-runtime","kind":["bin"]},"executable":str(current)}
        output=json.dumps({"reason":"build-finished","success":True})+"\n"+json.dumps(artifact)+"\n"
        self.assertEqual(builder.cargo_artifact(output),current)
        self.assertEqual(builder.cargo_artifact(output).read_bytes(),b"current")
        with self.assertRaises(ValueError):builder.cargo_artifact(output+json.dumps(artifact)+"\n")

    def test_final_manifest_normalizes_late_generated_file_modes(self):
        engine=self.root/"engine";engine.mkdir();(engine/"package-lock.json").write_text("{}\n")
        notice=self.root/"late-notice.txt";notice.write_text("synthetic public license\n");notice.chmod(0o644)
        executable=self.root/"helper";executable.write_bytes(b"synthetic");executable.chmod(0o755)
        provenance={"sourceCommit":"synthetic","inputSha256":"0"*64,"nodeArchiveSha256":"1"*64,"signing":"ad-hoc"}
        with mock.patch.object(builder.subprocess,"check_output",return_value="rustc synthetic\n"):
            manifest=builder.finalize(self.root,provenance=provenance)
        self.assertEqual(notice.stat().st_mode&0o777,0o600)
        self.assertEqual(executable.stat().st_mode&0o777,0o700)
        self.assertEqual((self.root/"manifest.json").stat().st_mode&0o777,0o600)
        self.assertEqual({row["path"]:row["mode"] for row in manifest["files"]},{"engine/package-lock.json":"0600","helper":"0700","late-notice.txt":"0600"})
