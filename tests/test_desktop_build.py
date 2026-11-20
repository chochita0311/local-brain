"""Synthetic native build publication, artifact inspection and Mermaid checks.

The retired sysconfig relocation and PyInstaller code-object assertions applied
only to the removed Python runtime. Native flags, rejected Python artifacts,
raw/compressed byte inspection and explicit asset roots cover their successors.
"""

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import gzip
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def load_tool(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load_tool("desktop_native_build_support", "apps/desktop/build_support.py")
with patch.dict(sys.modules, {"localbrain": None, "fastapi": None}):
    mermaid = load_tool("native_mermaid_verifier", "scripts/verify-installed-mermaid-assets.py")

ARTIFACTS = (
    "LocalBrain-apple-silicon", "LocalBrain-apple-silicon.zip", "LocalBrain-apple-silicon.sha256",
)


def write_build(parent, value):
    app = parent / ARTIFACTS[0]
    app.mkdir()
    (app / build.BUILD_OUTPUT_MARKER).write_text("synthetic owned build")
    (app / "app").write_text(value)
    for name in ARTIFACTS[1:]:
        (parent / name).write_text(value)


@contextmanager
def publication_work():
    with tempfile.TemporaryDirectory(prefix="lb-native-publication-") as folder:
        root = Path(folder)
        output = root / "output"
        staging = root / "staging"
        output.mkdir()
        staging.mkdir()
        write_build(output, "old")
        write_build(staging, "new")
        yield root, staging, output


def assert_build(test, parent, value):
    test.assertEqual((parent / ARTIFACTS[0] / "app").read_text(), value)
    for name in ARTIFACTS[1:]:
        test.assertEqual((parent / name).read_text(), value)


class NativeBuildPublicationTests(unittest.TestCase):
    def test_successful_owned_publication_replaces_the_complete_set(self):
        with publication_work() as (_, staging, output):
            build.publish_build(staging, output)
            assert_build(self, output, "new")
            self.assertFalse(list(output.glob(".localbrain-previous-*")))
            self.assertFalse(list(staging.iterdir()))

    def test_build_publication_keeps_complete_old_output_on_failure(self):
        for failed_name in ARTIFACTS:
            with self.subTest(artifact=failed_name), publication_work() as (_, staging, output):
                replace = build.os.replace

                def fail(source, target):
                    if source == staging / failed_name:
                        raise OSError("synthetic publication failure")
                    return replace(source, target)

                with patch.object(build.os, "replace", side_effect=fail):
                    with self.assertRaisesRegex(OSError, "synthetic publication failure"):
                        build.publish_build(staging, output)
                assert_build(self, output, "old")
                assert_build(self, staging, "new")
                self.assertFalse(list(output.glob(".localbrain-previous-*")))
                build.publish_build(staging, output)
                assert_build(self, output, "new")

    def test_build_publication_retains_backup_if_rollback_cannot_finish(self):
        with publication_work() as (_, staging, output):
            replace = build.os.replace

            def fail(source, target):
                if source == staging / ARTIFACTS[1] or (
                    source == output / ARTIFACTS[0] and target == staging / ARTIFACTS[0]
                ):
                    raise OSError("synthetic recovery failure")
                return replace(source, target)

            with patch.object(build.os, "replace", side_effect=fail):
                with self.assertRaisesRegex(RuntimeError, "previous files retained"):
                    build.publish_build(staging, output)
            backups = list(output.glob(".localbrain-previous-*"))
            self.assertEqual(len(backups), 1)
            assert_build(self, backups[0], "old")

    def test_build_publication_recovers_after_rename_then_interrupt(self):
        for phase in ("old", "new"):
            for artifact in ARTIFACTS:
                with self.subTest(phase=phase, artifact=artifact), publication_work() as (_, staging, output):
                    replace = build.os.replace
                    interrupted = False
                    trigger = (output if phase == "old" else staging) / artifact

                    def interrupt(source, target):
                        nonlocal interrupted
                        result = replace(source, target)
                        if source == trigger and not interrupted:
                            interrupted = True
                            raise KeyboardInterrupt()
                        return result

                    with patch.object(build.os, "replace", side_effect=interrupt):
                        with self.assertRaises(KeyboardInterrupt):
                            build.publish_build(staging, output)
                    self.assertTrue(interrupted)
                    assert_build(self, output, "old")
                    assert_build(self, staging, "new")
                    self.assertFalse(list(output.glob(".localbrain-previous-*")))

    def test_unowned_output_and_incomplete_candidates_are_refused_before_rename(self):
        cases = (
            "missing output marker", "linked output marker", "linked output directory",
            "linked output archive", "output archive directory", "missing candidate archive",
            "linked candidate marker", "linked candidate directory", "linked candidate archive",
        )
        for case in cases:
            with self.subTest(case=case), publication_work() as (root, staging, output):
                external = root / "unowned-file"
                external.write_text("preserve unrelated content")
                if case in ("missing output marker", "linked output marker", "linked candidate marker"):
                    parent = staging if case == "linked candidate marker" else output
                    marker = parent / ARTIFACTS[0] / build.BUILD_OUTPUT_MARKER
                    marker.unlink()
                    if case != "missing output marker":
                        marker.symlink_to(external)
                elif case in ("linked output directory", "linked candidate directory"):
                    parent = output if case == "linked output directory" else staging
                    app = parent / ARTIFACTS[0]
                    held = root / "unowned-directory"
                    app.rename(held)
                    app.symlink_to(held, target_is_directory=True)
                else:
                    parent = output if case.startswith("output") or case.startswith("linked output") else staging
                    archive = parent / ARTIFACTS[1]
                    archive.unlink()
                    if "directory" in case:
                        archive.mkdir()
                    elif case != "missing candidate archive":
                        archive.symlink_to(external)
                with patch.object(build.os, "replace", wraps=build.os.replace) as replace:
                    with self.assertRaises(ValueError):
                        build.publish_build(staging, output)
                    replace.assert_not_called()
                self.assertEqual(external.read_text(), "preserve unrelated content")
                self.assertEqual((output / ARTIFACTS[0] / "app").read_text(), "old")
                self.assertFalse(list(output.glob(".localbrain-previous-*")))


SOURCE_FILES = (
    "Cargo.toml", "Cargo.lock",
    "crates/core/Cargo.toml", "crates/core/build.rs",
    "crates/core/src/lib.rs", "crates/core/resources/contract.json",
    "crates/runtime/Cargo.toml", "crates/runtime/src/main.rs",
    "crates/runtime/engine/worker.cjs",
    "crates/runtime/engine/package.json", "crates/runtime/engine/package-lock.json",
    "apps/api/Cargo.toml", "apps/api/src/main.rs",
    "apps/web/static/styles.css", "apps/web/templates/base.html",
    "apps/desktop/build_support.py", "apps/desktop/package.json", "apps/desktop/package-lock.json",
    "apps/desktop/src-tauri/Cargo.toml", "apps/desktop/src-tauri/Cargo.lock",
    "apps/desktop/src-tauri/src/main.rs", "apps/desktop/src-tauri/build.rs",
    "apps/desktop/src-tauri/tauri.conf.json", "apps/desktop/src-tauri/Info.plist",
    "apps/desktop/src-tauri/icons/icon.png", "apps/desktop/ui/index.html",
    "scripts/build-api.py", "scripts/build-desktop.py", "scripts/build-terminal-runtime.py",
    "docs/policies/project/standalone-test-app-guide.md",
)


def write_source_tree(root):
    for relative in SOURCE_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic public input: " + relative.encode())


class NativeBuildIdentityTests(unittest.TestCase):
    def test_build_identity_tracks_native_inputs_without_runtime_or_generated_files(self):
        with tempfile.TemporaryDirectory(prefix="lb-native-inputs-") as folder:
            root = Path(folder)
            write_source_tree(root)
            with patch.object(build.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="")):
                before = build.source_identity(root)
                ignored = (
                    "runtime.db", "private/session.jsonl", "target/release/backend",
                    "apps/desktop/ui/app-styles.css", "apps/desktop/backend/generated",
                    "apps/desktop/node_modules/generated", "src/localbrain/retired.py",
                    "crates/core/src/__pycache__/generated.pyc",
                    "crates/core/tests/synthetic.rs",
                )
                for relative in ignored:
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"excluded synthetic content")
                self.assertEqual(build.source_identity(root), before)
                for relative in (
                    "Cargo.lock", "crates/core/src/lib.rs", "crates/core/build.rs",
                    "crates/core/resources/contract.json", "apps/api/src/main.rs",
                    "crates/runtime/engine/worker.cjs",
                    "crates/runtime/engine/package-lock.json",
                    "apps/web/static/styles.css", "apps/web/templates/base.html",
                    "apps/desktop/ui/index.html", "apps/desktop/src-tauri/src/main.rs",
                    "scripts/build-api.py",
                ):
                    with self.subTest(input=relative):
                        path = root / relative
                        original = path.read_bytes()
                        path.write_bytes(original + b" changed")
                        self.assertNotEqual(build.source_identity(root)["input_sha256"], before["input_sha256"])
                        path.write_bytes(original)
                linked = root / "crates/core/src/linked.rs"
                linked.symlink_to(root / "runtime.db")
                self.assertEqual(build.source_identity(root), before)

    def test_rust_flags_preserve_user_values_and_specific_path_ownership(self):
        original = {"RUSTFLAGS": "-C opt-level=2 --cfg 'feature=\"demo feature\"'", "OTHER": "kept"}
        roots = ("/synthetic/build user", "/synthetic/build user/repo", "/private/tmp/synthetic-stage")
        with patch.object(build.tempfile, "gettempdir", return_value="/synthetic/temporary"):
            result = build.rust_build_environment(original, roots)
        flags = result["CARGO_ENCODED_RUSTFLAGS"].split("\x1f")
        self.assertEqual(flags[:4], ["-C", "opt-level=2", "--cfg", 'feature="demo feature"'])
        home = "--remap-path-prefix=/synthetic/build user=/localbrain-build/home"
        source = "--remap-path-prefix=/synthetic/build user/repo=/localbrain-build/source"
        self.assertIn(home, flags)
        self.assertIn(source, flags)
        self.assertGreater(flags.index(source), flags.index(home))
        self.assertIn("--remap-path-prefix=/private/tmp=/localbrain-build/temporary", flags)
        self.assertEqual(result["OTHER"], "kept")
        self.assertNotIn("RUSTFLAGS", result)
        self.assertIn("RUSTFLAGS", original)
        encoded = {"CARGO_ENCODED_RUSTFLAGS": '--cfg\x1fdemo="some value"', "RUSTFLAGS": "ignored"}
        with patch.object(build.tempfile, "gettempdir", return_value="/synthetic/temporary"):
            flags = build.rust_build_environment(encoded, roots)["CARGO_ENCODED_RUSTFLAGS"].split("\x1f")
        self.assertEqual(flags[:2], ["--cfg", 'demo="some value"'])
        self.assertNotIn("ignored", flags)
        self.assertEqual(encoded["RUSTFLAGS"], "ignored")

    def test_same_source_with_two_standard_temporary_stages_reuses_cargo_flags(self):
        home, source = "/synthetic/home", "/synthetic/home/checkout"
        with patch.object(build.tempfile, "gettempdir", return_value="/synthetic/temporary"):
            first = build.rust_build_environment({}, (home, source, "/private/tmp/owned-stage-one"))
            second = build.rust_build_environment({}, (home, source, "/tmp/owned-stage-two"))
        self.assertEqual(first, second)
        flags = first["CARGO_ENCODED_RUSTFLAGS"]
        self.assertNotIn("owned-stage-one", flags)
        self.assertNotIn("owned-stage-two", flags)

    def test_custom_external_stage_has_an_explicit_private_path_remap(self):
        stage = "/synthetic/external build/owned-stage"
        with patch.object(build.tempfile, "gettempdir", return_value="/synthetic/temporary"):
            flags = build.rust_build_environment({}, ("/synthetic/home", "/synthetic/checkout", stage))["CARGO_ENCODED_RUSTFLAGS"].split("\x1f")
        self.assertIn("--remap-path-prefix=" + stage + "=/localbrain-build/staging/0", flags)

    def test_invalid_rust_remap_roots_refuse_without_echoing_paths(self):
        for roots in ((), ("/synthetic/home",), ("/", "/synthetic/source"),
                      ("relative", "/synthetic/source"), ("/synthetic/home", ""),
                      ("/synthetic/home", "/synthetic/source", "relative")):
            with self.subTest(roots=roots), self.assertRaises(ValueError) as error:
                build.rust_build_environment({}, roots)
            self.assertNotIn("/synthetic", str(error.exception))


class NativeBundleInspectionTests(unittest.TestCase):
    private = "/synthetic/private builder/toolchain"

    def test_stream_scan_finds_private_bytes_across_chunk_boundaries(self):
        for private in (self.private, "/synthetic/빌더"):
            prefix = b"x" * (1024 * 1024 - 3)
            self.assertTrue(build.stream_contains_paths(io.BytesIO(prefix + private.encode()), ("/other", private)))
        self.assertFalse(build.stream_contains_paths(io.BytesIO(prefix + b"public dependency"), (self.private,)))

    def test_raw_gzip_and_zip_private_paths_fail_without_execution_or_path_echo(self):
        for kind in ("raw", "gzip", "zip"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="lb-native-inspection-") as folder:
                root = Path(folder)
                executable = root / "localbrain-backend"
                executable.write_bytes(b"synthetic native executable")
                payload = b"x" * (1024 * 1024 - 3) + self.private.encode()
                if kind == "raw":
                    executable.write_bytes(payload)
                elif kind == "gzip":
                    path = root / "resource.gz"
                    with gzip.open(path, "wb") as stream:
                        stream.write(payload)
                    self.assertNotIn(self.private.encode(), path.read_bytes())
                else:
                    path = root / "resource.zip"
                    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                        archive.writestr("nested/resource.dat", payload)
                    self.assertNotIn(self.private.encode(), path.read_bytes())
                with patch.object(build.subprocess, "check_output") as execute:
                    with self.assertRaisesRegex(ValueError, "Private build path") as error:
                        build.check_bundle_paths(root, executable, (self.private,))
                    execute.assert_not_called()
                self.assertNotIn(self.private, str(error.exception))

    def test_python_runtime_files_archives_and_links_are_rejected_without_execution(self):
        names = (
            "module.py", "module.pyc", "module.pyo", "module.pyd", "libpython3.11.dylib",
            "python3.11", "PyInstaller.pkg", "Python.framework/Versions/3.11/Python",
            "PYZ.pyz", "base_library.zip", "resources.zip", "linked-python",
        )
        for name in names:
            with self.subTest(artifact=name), tempfile.TemporaryDirectory(prefix="lb-native-no-python-") as folder:
                root = Path(folder)
                executable = root / "localbrain-backend"
                executable.write_bytes(b"synthetic native executable")
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if name in ("base_library.zip", "resources.zip"):
                    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                        archive.writestr("json/__init__.pyc", b"synthetic Python bytecode")
                elif name == "linked-python":
                    path = root / "python3.11"
                    path.symlink_to(executable.name)
                else:
                    path.write_bytes(b"raise AssertionError('must not execute')")
                with patch.object(build.subprocess, "check_output", side_effect=[
                    "Mach-O 64-bit executable arm64", "localbrain-backend:\n/usr/lib/libSystem.B.dylib",
                ]) as execute:
                    with self.assertRaisesRegex(ValueError, "Python runtime content"):
                        build.check_bundle_paths(root, executable, (self.private,))
                    execute.assert_not_called()

    def test_private_link_targets_and_archive_member_names_are_rejected(self):
        for kind in ("link", "zip name"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="lb-native-link-path-") as folder:
                root = Path(folder)
                executable = root / "localbrain-backend"
                executable.write_bytes(b"synthetic native executable")
                if kind == "link":
                    (root / "resource").symlink_to(self.private + "/library")
                else:
                    with zipfile.ZipFile(root / "resources.zip", "w", zipfile.ZIP_DEFLATED) as archive:
                        archive.writestr(self.private.lstrip("/") + "/resource", b"public content")
                with patch.object(build.subprocess, "check_output") as execute:
                    # Link payloads and archived names are distribution bytes,
                    # even when the regular member contents are public.
                    with self.assertRaisesRegex(ValueError, "Private build path") as error:
                        build.check_bundle_paths(root, executable, (self.private, self.private.lstrip("/")))
                    execute.assert_not_called()
                self.assertNotIn(self.private.lstrip("/"), str(error.exception))

    def test_clean_compressed_assets_pass_and_native_abi_and_link_checks_still_run(self):
        with tempfile.TemporaryDirectory(prefix="lb-native-clean-bundle-") as folder:
            root = Path(folder)
            executable = root / "localbrain-backend"
            executable.write_bytes(b"synthetic native executable")
            with gzip.open(root / "resource.gz", "wb") as stream:
                stream.write(b"public resource")
            with zipfile.ZipFile(root / "resource.zip", "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("nested/resource.txt", b"public resource")
            with patch.object(build.subprocess, "check_output", side_effect=[
                "Mach-O 64-bit executable arm64", "localbrain-backend:\n/usr/lib/libSystem.B.dylib",
            ]) as inspect:
                build.check_bundle_paths(root, executable, (self.private,))
            self.assertEqual(inspect.call_args_list[0].args[0], ["/usr/bin/file", "-b", str(executable)])
            self.assertEqual(inspect.call_args_list[1].args[0], ["/usr/bin/otool", "-L", str(executable)])
            for description in ("ELF 64-bit executable", "Mach-O 64-bit executable x86_64", "text script"):
                with self.subTest(description=description), patch.object(build.subprocess, "check_output", return_value=description) as inspect:
                    with self.assertRaisesRegex(ValueError, "native arm64"):
                        build.check_bundle_paths(root, executable, (self.private,))
                    self.assertEqual(inspect.call_count, 1)
            with patch.object(build.subprocess, "check_output", side_effect=[
                "Mach-O 64-bit executable arm64", "localbrain-backend:\n/synthetic/Python.framework/Versions/3.11/Python",
            ]):
                with self.assertRaisesRegex(ValueError, "links a Python runtime"):
                    build.check_bundle_paths(root, executable, (self.private,))


def mermaid_assets():
    files = {
        "mermaid.esm.min.js": b"x" * 3_000_001,
        "mermaid-LICENSE.txt": b"MIT License: synthetic fixture",
        "layout-elk-LICENSE.txt": b"MIT License: synthetic fixture",
        "elkjs-LICENSE.txt": b"Eclipse Public License: synthetic fixture",
        "esbuild-LICENSE.txt": b"MIT License: synthetic fixture",
    }
    manifest = {
        "schema": "localbrain.mermaid-assets.v1",
        "dependencies": {
            "layoutElk": {"license": "MIT", "version": "0.2.2"},
            "elkjs": {"license": "EPL-2.0", "version": "0.9.3"},
        },
        "outputs": {name: hashlib.sha256(body).hexdigest() for name, body in files.items()},
    }
    assets = {mermaid.VENDOR + name: body for name, body in files.items()}
    assets[mermaid.VENDOR + "asset-manifest.json"] = json.dumps(manifest).encode()
    assets["mermaid-adapter.js"] = b'securityLevel: "strict"\nregisterLayoutLoaders(elkLayouts)'
    return assets, manifest


def write_assets(root, assets):
    for name, body in assets.items():
        path = root / "static" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)


@contextmanager
def asset_server(root, token=None, redirect=False):
    requests = []

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, *args):
            pass

        def do_GET(self):
            requests.append((self.path, self.headers.get("Authorization")))
            if redirect:
                self.send_response(302)
                self.send_header("Location", "https://example.test/unselected")
                self.end_headers()
            elif token and self.headers.get("Authorization") != "Bearer " + token:
                self.send_response(401)
                self.end_headers()
            else:
                super().do_GET()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port), requests
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        if worker.is_alive():
            raise AssertionError("Synthetic asset server did not stop")


class NativeMermaidVerifierTests(unittest.TestCase):
    def test_explicit_web_root_works_without_site_packages_or_localbrain(self):
        assets, _ = mermaid_assets()
        with tempfile.TemporaryDirectory(prefix="lb-native-mermaid-") as folder:
            root = Path(folder)
            write_assets(root, assets)
            result = subprocess.run([
                sys.executable, "-B", "-I", "-S", str(ROOT / "scripts/verify-installed-mermaid-assets.py"),
                "--web-root", str(root),
            ], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Mermaid assets verified", result.stdout)

    def test_repository_native_web_assets_pass_the_standalone_verifier(self):
        result = subprocess.run([
            sys.executable, "-B", "-I", "-S", str(ROOT / "scripts/verify-installed-mermaid-assets.py"),
            "--web-root", str(ROOT / "apps/web"),
        ], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Mermaid assets verified", result.stdout)

    def test_target_is_required_and_no_installed_app_is_inferred(self):
        for arguments in ([], ["--web-root", "/synthetic", "--url", "http://127.0.0.1"],
                          ["--web-root", "/synthetic", "--token-env", "SYNTHETIC_TOKEN"]):
            with self.subTest(arguments=arguments), redirect_stderr(io.StringIO()):
                with patch.object(mermaid, "verify_assets") as verify:
                    with self.assertRaises(SystemExit) as error:
                        mermaid.main(arguments)
                    self.assertEqual(error.exception.code, 2)
                    verify.assert_not_called()

    def test_contract_refusals_keep_bundle_metadata_licenses_and_security_checks(self):
        cases = (
            "small bundle", "wrong schema", "wrong layout version", "wrong engine license",
            "missing MIT license", "missing EPL license", "loose security", "missing ELK registration",
            "changed output bytes", "missing output hashes", "invalid output name", "invalid output hash",
        )
        for case in cases:
            with self.subTest(case=case):
                assets, manifest = mermaid_assets()
                if case == "small bundle":
                    assets[mermaid.VENDOR + "mermaid.esm.min.js"] = b"x" * 3_000_000
                elif case == "wrong schema":
                    manifest["schema"] = "synthetic.wrong"
                elif case == "wrong layout version":
                    manifest["dependencies"]["layoutElk"]["version"] = "0.0.0"
                elif case == "wrong engine license":
                    manifest["dependencies"]["elkjs"]["license"] = "invalid"
                elif case == "missing MIT license":
                    assets[mermaid.VENDOR + "layout-elk-LICENSE.txt"] = b"missing"
                elif case == "missing EPL license":
                    assets[mermaid.VENDOR + "elkjs-LICENSE.txt"] = b"missing"
                elif case == "loose security":
                    assets["mermaid-adapter.js"] = b'securityLevel: "loose"\nregisterLayoutLoaders(elkLayouts)'
                elif case == "missing ELK registration":
                    assets["mermaid-adapter.js"] = b'securityLevel: "strict"'
                elif case == "changed output bytes":
                    assets[mermaid.VENDOR + "esbuild-LICENSE.txt"] += b" changed"
                elif case == "missing output hashes":
                    manifest.pop("outputs")
                elif case == "invalid output name":
                    manifest["outputs"]["../unselected"] = "0" * 64
                elif case == "invalid output hash":
                    manifest["outputs"]["mermaid.esm.min.js"] = "invalid"
                assets[mermaid.VENDOR + "asset-manifest.json"] = json.dumps(manifest).encode()
                with self.assertRaises(AssertionError):
                    mermaid.verify_assets(assets.__getitem__)

    def test_filesystem_assets_cannot_escape_the_explicit_root_through_links(self):
        with tempfile.TemporaryDirectory(prefix="lb-native-mermaid-links-") as folder:
            root = Path(folder)
            selected = root / "selected"
            (selected / "static").mkdir(parents=True)
            outside = root / "unselected"
            outside.write_bytes(b"preserve unrelated content")
            (selected / "static/resource").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "escapes"):
                mermaid.filesystem_fetch(selected)("resource")

    def test_explicit_loopback_fetch_ignores_proxies_and_keeps_all_asset_checks(self):
        assets, _ = mermaid_assets()
        with tempfile.TemporaryDirectory(prefix="lb-native-mermaid-http-") as folder:
            root = Path(folder)
            write_assets(root, assets)
            with asset_server(root) as (url, requests):
                with patch.dict(mermaid.os.environ, {"http_proxy": "http://127.0.0.1:1", "HTTP_PROXY": "http://127.0.0.1:1", "no_proxy": "", "NO_PROXY": ""}):
                    mermaid.verify_assets(mermaid.loopback_fetch(url))
            self.assertEqual({path for path, _ in requests}, {"/static/" + name for name in assets})
            self.assertTrue(all(value is None for _, value in requests))

    def test_desktop_bearer_token_is_explicit_and_never_printed(self):
        assets, _ = mermaid_assets()
        token = "synthetic-mermaid-launch"
        with tempfile.TemporaryDirectory(prefix="lb-native-mermaid-auth-") as folder:
            root = Path(folder)
            write_assets(root, assets)
            with asset_server(root, token=token) as (url, requests):
                output = io.StringIO()
                with patch.dict(mermaid.os.environ, {"SYNTHETIC_MERMAID_TOKEN": token}), redirect_stdout(output):
                    self.assertEqual(mermaid.main(["--url", url, "--token-env", "SYNTHETIC_MERMAID_TOKEN"]), 0)
            self.assertNotIn(token, output.getvalue())
            self.assertTrue(requests)
            self.assertTrue(all(value == "Bearer " + token for _, value in requests))

    def test_non_loopback_ambiguous_and_credential_urls_refuse_before_transport(self):
        urls = (
            "https://example.test", "http://0.0.0.0:9", "file:///synthetic/assets", "http:///missing",
            "http://127.0.0.1:65536", "http://127.0.0.1/?token=synthetic", "http://127.0.0.1/#fragment",
            "http://" + "synthetic-user" + "@" + "127.0.0.1/",
        )
        with patch.object(mermaid, "build_opener") as transport:
            for url in urls:
                with self.subTest(url=url), self.assertRaises(ValueError):
                    mermaid.loopback_fetch(url, "synthetic-token")
            transport.assert_not_called()
        self.assertEqual(mermaid.loopback_url("http://[::1]:4321").hostname, "::1")

    def test_redirects_are_refused_before_a_token_or_request_reaches_another_origin(self):
        with tempfile.TemporaryDirectory(prefix="lb-native-mermaid-redirect-") as folder:
            with asset_server(Path(folder), redirect=True) as (url, requests):
                with self.assertRaisesRegex(ValueError, "redirects"):
                    mermaid.loopback_fetch(url, "synthetic-token")("mermaid-adapter.js")
            self.assertEqual(requests, [("/static/mermaid-adapter.js", "Bearer synthetic-token")])

    def test_http_failure_is_not_mistaken_for_an_asset(self):
        with tempfile.TemporaryDirectory(prefix="lb-native-mermaid-missing-") as folder:
            with asset_server(Path(folder)) as (url, _):
                with self.assertRaisesRegex(AssertionError, "did not return 200"):
                    mermaid.loopback_fetch(url)("missing.js")


if __name__ == "__main__":
    unittest.main()
