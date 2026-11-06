"""Synthetic build metadata and compressed-code privacy regressions."""

import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "desktop_build_support", Path(__file__).parents[1] / "desktop" / "build_support.py"
)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class PortableSysconfigTests(unittest.TestCase):
    def test_build_publication_keeps_complete_old_output_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); output = root / 'output'; output.mkdir()
            staging = root / 'staging'; staging.mkdir()
            names = ('LocalBrain-apple-silicon', 'LocalBrain-apple-silicon.zip', 'LocalBrain-apple-silicon.sha256')
            for location, value in ((output, 'old'), (staging, 'new')):
                app = location / names[0]; app.mkdir()
                (app / build.BUILD_OUTPUT_MARKER).write_text('owned')
                (app / 'app').write_text(value)
                for name in names[1:]: (location / name).write_text(value)
            replace = build.os.replace
            def fail_archive(source, target):
                if source == staging / names[1]: raise OSError('synthetic publication failure')
                return replace(source, target)
            with patch.object(build.os, 'replace', side_effect=fail_archive):
                with self.assertRaisesRegex(OSError, 'synthetic publication failure'):
                    build.publish_build(staging, output)
            self.assertEqual((output / names[0] / 'app').read_text(), 'old')
            for name in names[1:]: self.assertEqual((output / name).read_text(), 'old')
            self.assertFalse(list(output.glob('.localbrain-previous-*')))
            build.publish_build(staging, output)
            self.assertEqual((output / names[0] / 'app').read_text(), 'new')
            for name in names[1:]: self.assertEqual((output / name).read_text(), 'new')

    def test_build_publication_retains_backup_if_rollback_cannot_finish(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); output = root / 'output'; output.mkdir()
            staging = root / 'staging'; staging.mkdir()
            names = ('LocalBrain-apple-silicon', 'LocalBrain-apple-silicon.zip', 'LocalBrain-apple-silicon.sha256')
            for location, value in ((output, 'old'), (staging, 'new')):
                app = location / names[0]; app.mkdir()
                (app / build.BUILD_OUTPUT_MARKER).write_text('owned')
                (app / 'app').write_text(value)
                for name in names[1:]: (location / name).write_text(value)
            replace = build.os.replace
            def fail(source, target):
                if source == staging / names[1] or (source == output / names[0] and target == staging / names[0]):
                    raise OSError('synthetic recovery failure')
                return replace(source, target)
            with patch.object(build.os, 'replace', side_effect=fail):
                with self.assertRaisesRegex(RuntimeError, 'previous files retained'):
                    build.publish_build(staging, output)
            backups = list(output.glob('.localbrain-previous-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / names[0] / 'app').read_text(), 'old')
            for name in names[1:]: self.assertEqual((backups[0] / name).read_text(), 'old')

    def test_build_publication_recovers_after_rename_then_interrupt(self):
        for phase in ('old', 'new'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as folder:
                root = Path(folder); output = root / 'output'; output.mkdir()
                staging = root / 'staging'; staging.mkdir()
                names = ('LocalBrain-apple-silicon', 'LocalBrain-apple-silicon.zip', 'LocalBrain-apple-silicon.sha256')
                for location, value in ((output, 'old'), (staging, 'new')):
                    app = location / names[0]; app.mkdir()
                    (app / build.BUILD_OUTPUT_MARKER).write_text('owned')
                    (app / 'app').write_text(value)
                    for name in names[1:]: (location / name).write_text(value)
                replace = build.os.replace
                interrupted = False
                def interrupt(source, target):
                    nonlocal interrupted
                    result = replace(source, target)
                    trigger = (output if phase == 'old' else staging) / names[0]
                    if source == trigger and not interrupted:
                        interrupted = True
                        raise KeyboardInterrupt()
                    return result
                with patch.object(build.os, 'replace', side_effect=interrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        build.publish_build(staging, output)
                self.assertEqual((output / names[0] / 'app').read_text(), 'old')
                for name in names[1:]: self.assertEqual((output / name).read_text(), 'old')
                self.assertFalse(list(output.glob('.localbrain-previous-*')))

    def test_build_identity_tracks_content_without_runtime_or_generated_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'src/localbrain'; source.mkdir(parents=True)
            app = source / '__init__.py'; app.write_text('version = "synthetic"')
            ui = root / 'desktop/ui'; ui.mkdir(parents=True)
            (ui / 'index.html').write_text('<p>App</p>')
            before = build.source_identity(root)
            (root / 'runtime.db').write_bytes(b'private synthetic runtime')
            (ui / 'app-styles.css').write_text('generated copy')
            self.assertEqual(build.source_identity(root), before)
            app.write_text('version = "changed"')
            self.assertNotEqual(build.source_identity(root)['input_sha256'], before['input_sha256'])

    def setUp(self):
        self.builder = "/synthetic/builder"
        self.prefix = self.builder + "/python"
        self.variables = {
            "prefix": self.prefix,
            "LIBDIR": self.prefix + "/lib",
            "DESTDIRS": self.prefix + "/bin " + self.prefix + "/lib",
            "EXT_SUFFIX": ".cpython-311-darwin.so",
            "CFLAGS": "-arch arm64 -O3",
            "SIZEOF_VOID_P": 8,
        }

    def test_paths_follow_each_runtime_location_and_preserve_flags(self):
        source = build.sysconfig_module_source(self.variables, (self.prefix,), (self.builder,))
        self.assertNotIn(self.builder, source)
        for runtime in ("/Applications/LocalBrain.app/runtime", "/synthetic/another user/Downloads/App/runtime"):
            namespace = {}
            with patch.object(sys, "prefix", runtime):
                exec(compile(source, "_sysconfigdata_synthetic.py", "exec"), namespace)
            values = namespace["build_time_vars"]
            self.assertEqual(values["prefix"], runtime)
            self.assertEqual(values["LIBDIR"], runtime + "/lib")
            self.assertEqual(values["DESTDIRS"], runtime + "/bin " + runtime + "/lib")
            for key in ("EXT_SUFFIX", "CFLAGS", "SIZEOF_VOID_P"):
                self.assertEqual(values[key], self.variables[key])
        self.assertEqual(self.variables["prefix"], self.prefix)

    def test_unknown_private_path_fails_without_printing_it(self):
        for suffix in ("/unrelated/headers", "/python-other/lib"):
            values = {**self.variables, "INCLUDEPY": self.builder + suffix}
            with self.assertRaisesRegex(ValueError, "field: INCLUDEPY") as error:
                build.sysconfig_module_source(values, (self.prefix,), (self.builder,))
            self.assertNotIn(self.builder, str(error.exception))

    def test_root_or_relative_prefix_is_rejected(self):
        for prefix in ("/", "", "relative"):
            with self.assertRaises(ValueError):
                build.sysconfig_module_source(self.variables, (prefix,), (self.builder,))

    def test_rust_flags_preserve_values_with_spaces_and_scope_private_paths(self):
        original={'RUSTFLAGS':'-C opt-level=2 --cfg \'feature="demo feature"\'', 'OTHER':'kept'}
        result=build.rust_build_environment(original,('/synthetic/build user','/synthetic/build user/repo','/synthetic/temp'))
        flags=result['CARGO_ENCODED_RUSTFLAGS'].split('\x1f')
        self.assertEqual(flags[:4],['-C','opt-level=2','--cfg','feature="demo feature"'])
        self.assertEqual(flags[4],'--remap-path-prefix=/synthetic/build user=/localbrain-build/0')
        self.assertEqual(result['OTHER'],'kept');self.assertNotIn('RUSTFLAGS',result)
        self.assertIn('RUSTFLAGS',original)
        encoded=build.rust_build_environment({'CARGO_ENCODED_RUSTFLAGS':'--cfg\x1fdemo="some value"','RUSTFLAGS':'ignored'},('/synthetic/user',))
        self.assertEqual(encoded['CARGO_ENCODED_RUSTFLAGS'].split('\x1f')[:2],['--cfg','demo="some value"'])
        for path in ('/','relative'):
            with self.assertRaises(ValueError):build.rust_build_environment({},(path,))

    def test_code_inspection_includes_nested_constants_and_filenames(self):
        private = (self.builder,)
        code = compile("def nested():\n    return " + repr(self.prefix), "module.py", "exec")
        self.assertTrue(build.code_contains_paths(code, private))
        self.assertTrue(build.code_contains_paths(compile("pass", self.prefix + "/a.py", "exec"), private))
        self.assertTrue(build.code_contains_paths((self.prefix.encode(),), private))
        self.assertFalse(build.code_contains_paths(compile("value = 42", "module.py", "exec"), private))

    def test_stream_scan_finds_path_across_chunk_boundary(self):
        prefix = b"x" * (1024 * 1024 - 3)
        self.assertTrue(build.stream_contains_paths(io.BytesIO(prefix + self.prefix.encode()), (self.builder,)))
        self.assertFalse(build.stream_contains_paths(io.BytesIO(prefix + b"public dependency"), (self.builder,)))

    def test_bundle_check_reads_compressed_python_without_execution(self):
        private_code = compile("value = " + repr(self.prefix) + "\nraise RuntimeError('must not execute')", "metadata.py", "exec")
        modules = types.SimpleNamespace(toc={"sysconfig_metadata": None}, extract=lambda name: private_code)
        archive = types.SimpleNamespace(toc={"PYZ.pyz": ("z",)}, open_embedded_archive=lambda name: modules)
        readers = types.ModuleType("PyInstaller.archive.readers")
        readers.CArchiveReader = lambda path: archive
        fake_modules = {
            "PyInstaller": types.ModuleType("PyInstaller"),
            "PyInstaller.archive": types.ModuleType("PyInstaller.archive"),
            "PyInstaller.archive.readers": readers,
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, fake_modules):
            root = Path(directory)
            executable = root / "backend"
            executable.write_bytes(b"no private path in uncompressed bytes")
            with self.assertRaisesRegex(ValueError, "bundled Python module: sysconfig_metadata"):
                build.check_bundle_paths(root, executable, (self.builder,))
            source = build.sysconfig_module_source(self.variables, (self.prefix,), (self.builder,))
            modules.extract = lambda name: compile(source, "metadata.py", "exec")
            build.check_bundle_paths(root, executable, (self.builder,))


if __name__ == "__main__":
    unittest.main()
