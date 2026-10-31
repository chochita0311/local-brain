"""Shared infrastructure stays usable without optional product or model features."""

import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from localbrain.foundation import paths
from localbrain.foundation.files import StorageError, validate_runtime_directory
from localbrain.foundation.private_json import atomic_json, read_json
from localbrain.foundation.validation import ExperimentError
from localbrain.models.generation import safe_root
from localbrain.models.setup import ModelSetupService


ROOT = Path(__file__).resolve().parents[1]


class PackageBoundaryTests(unittest.TestCase):
    def test_package_root_contains_only_stable_entrypoints(self):
        self.assertEqual(
            {path.name for path in (ROOT / "src/localbrain").glob("*.py")},
            {"__init__.py", "main.py", "cli.py", "desktop.py"},
        )

    def test_feature_logic_does_not_import_application_or_web_handlers(self):
        root = ROOT / "src/localbrain"
        for file in root.rglob("*.py"):
            relative = file.relative_to(root)
            if len(relative.parts) == 1 or relative.parts[0] == "app" or file.stem == "web":
                continue
            package = "localbrain." + ".".join(relative.parts[:-1])
            for node in ast.walk(ast.parse(file.read_text())):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if node.level:
                        module = importlib.util.resolve_name("." * node.level + module, package)
                    names = [module + "." + alias.name for alias in node.names]
                else:
                    continue
                for name in names:
                    if name.startswith("localbrain."):
                        with self.subTest(file=str(relative), dependency=name):
                            self.assertNotIn(name.split(".")[1], {"main", "app"})
                            self.assertNotIn("web", name.split(".")[2:])

    def test_internal_imports_only_point_to_allowed_lower_layers(self):
        for package, allowed in (
            ("foundation", {"foundation"}),
            ("models", {"foundation", "models"}),
            ("references", {"references"}),
        ):
            for file in (ROOT / "src/localbrain" / package).glob("*.py"):
                tree = ast.parse(file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        if node.level:
                            module = importlib.util.resolve_name(
                                "." * node.level + module, "localbrain." + package)
                        names = [module + "." + alias.name for alias in node.names]
                    else:
                        continue
                    for name in names:
                        if name.startswith("localbrain."):
                            with self.subTest(file=file.name, line=node.lineno, dependency=name):
                                self.assertIn(name.split(".")[1], allowed)

    def isolated_import(self, modules, blocked):
        # A fresh interpreter catches imports hidden by the rest of the test suite.
        code = """
import importlib, importlib.abc, json, sys
modules, blocked = json.loads(sys.argv[1]), json.loads(sys.argv[2])
class Boundary(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == item or fullname.startswith(item + '.') for item in blocked):
            raise AssertionError('Unexpected dependency: ' + fullname)
sys.meta_path.insert(0, Boundary())
for module in modules:
    importlib.import_module(module)
assert not any(name == item or name.startswith(item + '.')
               for name in sys.modules for item in blocked)
"""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", code, json.dumps(modules), json.dumps(blocked)],
                env={**os.environ, "PYTHONPATH": str(ROOT / "src"),
                     "LOCALBRAIN_DATA_DIR": str(Path(directory) / "data")},
                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shared_modules_import_without_product_or_inference_runtime(self):
        modules = ["localbrain." + package + "." + path.stem
                   for package in ("foundation", "models", "references")
                   for path in sorted((ROOT / "src/localbrain" / package).glob("*.py"))
                   if path.stem != "__init__"]
        blocked = ["fastapi", "sqlite3", "torch", "transformers", "sentence_transformers",
                   "huggingface_hub", "numpy", "localbrain.persistence.db", "localbrain.workstreams",
                   "localbrain.experiments.reconstruction", "localbrain.auto_work",
                   "localbrain.experiments.context"]
        self.isolated_import(modules, blocked)

    def test_session_and_search_consumers_import_without_experiments(self):
        self.isolated_import(
            ["localbrain.sessions.pins", "localbrain.sessions.chart_preferences",
             "localbrain.natural_search.model", "localbrain.context_search.worker"],
            ["localbrain.workstreams", "localbrain.experiments.reconstruction",
             "localbrain.auto_work", "localbrain.experiments.context",
             "torch", "transformers", "sentence_transformers"])

    def test_search_http_and_run_lifecycle_do_not_import_pilot_implementations(self):
        self.isolated_import(
            ["localbrain.natural_search.web", "localbrain.maintenance.service"],
            ["localbrain.atlassian", "localbrain.workstreams", "localbrain.workflow",
             "localbrain.auto_work", "localbrain.context_search"])

    def test_core_session_and_resource_reads_import_without_optional_features(self):
        self.isolated_import(
            ["localbrain.sessions." + module for module in
             ("activity", "queries", "reading", "pins", "chart_preferences", "skills", "subagents", "references")]
            + ["localbrain.resources.store", "localbrain.local_context.queries",
               "localbrain.local_context.references", "localbrain.sources.profiles"],
            ["localbrain.app", "localbrain.main", "localbrain.atlassian",
             "localbrain.workstreams", "localbrain.workflow", "localbrain.auto_work",
             "localbrain.experiments", "localbrain.insights", "localbrain.context_search",
             "localbrain.google_drive", "torch", "transformers", "sentence_transformers"])

    def test_migrations_do_not_depend_on_entrypoints_or_optional_features(self):
        root = ROOT / "src/localbrain/persistence/migrations"
        for file in root.glob("*.py"):
            for node in ast.walk(ast.parse(file.read_text())):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if node.level:
                        module = importlib.util.resolve_name(
                            "." * node.level + module, "localbrain.persistence.migrations")
                    names = [module + "." + alias.name for alias in node.names]
                else:
                    continue
                for name in names:
                    with self.subTest(file=file.name, dependency=name):
                        self.assertFalse(any(
                            name == banned or name.startswith(banned + ".")
                            for banned in ("localbrain.persistence.db", "localbrain.persistence.bootstrap",
                                           "localbrain.app", "localbrain.atlassian", "localbrain.workstreams",
                                           "localbrain.workflow", "localbrain.auto_work")))

    def test_recovery_and_contract_checks_import_without_http_or_bootstrap(self):
        self.isolated_import(
            ["localbrain.app.storage.recovery", "localbrain.persistence.storage",
             "localbrain.persistence.migrations.contracts", "localbrain.app.storage.layout",
             "localbrain.app.features"],
            ["fastapi", "localbrain.persistence.db", "localbrain.persistence.bootstrap",
             "localbrain.atlassian", "localbrain.workstreams", "localbrain.auto_work"])

    def test_common_storage_does_not_import_optional_feature_implementations(self):
        banned = {"atlassian", "workstreams", "workflow", "auto_work", "context_search", "experiments"}
        for name in ("layout", "recovery"):
            file = ROOT / "src/localbrain/app/storage" / (name + ".py")
            for node in ast.walk(ast.parse(file.read_text())):
                if isinstance(node, ast.Import):
                    imports = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if node.level:
                        module = importlib.util.resolve_name("." * node.level + module, "localbrain.app.storage")
                    imports = [module, *(module + "." + item.name for item in node.names)]
                else:
                    continue
                for module in imports:
                    if module.startswith("localbrain."):
                        with self.subTest(file=name, line=node.lineno, dependency=module):
                            self.assertNotIn(module.split(".")[1], banned)

    def test_source_wheel_and_frozen_layouts_keep_storage_exclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for relative, boundary in (
                ("checkout/src/localbrain", root / "checkout"),
                ("installed/site-packages/localbrain", root / "installed"),
                ("bundle/_internal/localbrain", root / "bundle"),
            ):
                package = root / relative
                (package / "foundation").mkdir(parents=True)
                with self.subTest(layout=relative), patch.object(
                    paths, "__file__", str(package / "foundation/paths.py")
                ), patch.dict(os.environ, {"HF_HUB_CACHE": str(root / "public-hub")}):
                    self.assertEqual(paths.package_boundary(), boundary)
                    self.assertEqual(paths.package_root(), package)
                    for forbidden in (boundary, boundary / "private"):
                        with self.assertRaisesRegex(StorageError, "INVALID_RUNTIME_DIRECTORY"):
                            validate_runtime_directory(forbidden)
                        with self.assertRaisesRegex(ExperimentError, "INVALID_MODEL_ROOT"):
                            safe_root(forbidden)
                        self.assertFalse((boundary / "private").exists())
                    private = root / "private"
                    self.assertEqual(validate_runtime_directory(private), private)
                    self.assertEqual(safe_root(private), private)
                    self.assertFalse(private.exists())

    def test_source_and_frozen_model_worker_commands(self):
        search = Mock()
        config = SimpleNamespace(data_dir=Path("/synthetic/data"))
        for frozen, expected in (
            (False, [sys.executable, "-m", "localbrain.models.setup"]),
            (True, [sys.executable, "--install-search-model"]),
        ):
            with self.subTest(frozen=frozen), \
                 patch.object(sys, "frozen", frozen, create=True), \
                 patch("localbrain.models.setup.runtime_missing", return_value=[]), \
                 patch("localbrain.models.setup.subprocess.Popen") as spawn, \
                 patch("localbrain.models.setup.threading.Thread"):
                ModelSetupService(config, search).start()
                self.assertEqual(spawn.call_args.args[0], expected)
                self.assertEqual(spawn.call_args.kwargs["env"]["LOCALBRAIN_DATA_DIR"], "/synthetic/data")
                self.assertEqual(spawn.call_args.kwargs["env"]["LOCALBRAIN_MODEL_PARENT_PIPE"], "1")
                self.assertEqual(spawn.call_args.kwargs["env"]["LOCALBRAIN_MODEL_KEY"], "embedding")


class PrivateJsonTests(unittest.TestCase):
    def test_failed_publication_preserves_previous_value_and_removes_own_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            atomic_json(path, {"값": [1, None]})
            original = path.read_bytes()
            for value in ({"bad": float("nan")}, {"bad": object()}):
                with self.assertRaises((ValueError, TypeError)):
                    atomic_json(path, value)
                self.assertEqual(path.read_bytes(), original)
                self.assertFalse(path.with_suffix(".json.pending").exists())
            with patch("localbrain.foundation.private_json.os.replace", side_effect=OSError("synthetic")):
                with self.assertRaises(OSError):
                    atomic_json(path, {"replacement": True})
            self.assertEqual(read_json(path), {"값": [1, None]})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertFalse(path.with_suffix(".json.pending").exists())

    def test_existing_pending_or_unsafe_target_is_refused_without_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "state.json"
            atomic_json(path, {"original": True})
            pending = root / "state.json.pending"
            pending.write_bytes(b"another writer")
            with self.assertRaisesRegex(ExperimentError, "UNOWNED_OUTPUT"):
                atomic_json(path, {})
            self.assertEqual(pending.read_bytes(), b"another writer")
            pending.unlink()
            for kind in ("symlink", "hardlink", "permissions"):
                with self.subTest(kind=kind):
                    other = root / "other.json"
                    if kind == "symlink":
                        other.symlink_to(path)
                        target = other
                    elif kind == "hardlink":
                        os.link(path, other)
                        target = path
                    else:
                        path.chmod(0o644)
                        target = path
                    try:
                        with self.assertRaisesRegex(ExperimentError, "UNOWNED_OUTPUT"):
                            atomic_json(target, {})
                        with self.assertRaisesRegex(ExperimentError, "UNOWNED_OUTPUT"):
                            read_json(target)
                        self.assertFalse(pending.exists())
                        self.assertEqual(json.loads(path.read_text()), {"original": True})
                    finally:
                        other.unlink(missing_ok=True)
                        path.chmod(0o600)
