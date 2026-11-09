"""Synthetic public assets exercise selection, integrity and download recovery."""

from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from localbrain.foundation.preferences import PreferencesError
from localbrain.foundation.private_json import atomic_json
from localbrain.models.catalog import EMBEDDING_ASSETS, EMBEDDING_ID, EMBEDDING_REVISION
from localbrain.models.embedding import verified_assets
from localbrain.models.installation import install_embedding, model_root
from localbrain.models.setup import ModelSetupService, download_worker
from localbrain.models.storage import folder_status, inspect_folder
from localbrain.app.storage.recovery import storage_status
from localbrain.natural_search.source import _private_derived


class ModelStorageTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        self.config = SimpleNamespace(data_dir=self.root / 'data', cache_dir=self.root / 'private-cache',
                                      development_dir=self.root / 'development')
        self.config.data_dir.mkdir(mode=0o700)
        self.first, self.second = self.root / 'shared-hub', self.root / 'chosen-hub'
        self.snapshot = self.assets(self.first)
        inventory = [{'path': n, 'size': (self.snapshot / n).stat().st_size,
                      'sha256': hashlib.sha256((self.snapshot / n).read_bytes()).hexdigest()}
                     for n in sorted(EMBEDDING_ASSETS)]
        fingerprint = hashlib.sha256((json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()).hexdigest()
        self.stack.enter_context(patch.dict(os.environ, {'HF_HUB_CACHE': str(self.first)}))
        for name in ('installation', 'embedding'):
            self.stack.enter_context(patch('localbrain.models.' + name + '.EMBEDDING_FINGERPRINT', fingerprint))
        self.metadata = model_root('embedding', self.config.data_dir)
        install_embedding(self.metadata, local_only=True)
        self.manifest = self.metadata / 'model.json'
        self.original = self.manifest.read_bytes()
        self.search = Mock(); self.search.status.return_value = {'state': 'disabled'}
        self.service = ModelSetupService(self.config, self.search)
        self.config.cache_dir.mkdir()
        self.private_index = self.config.cache_dir / 'index.sqlite3'
        self.private_index.write_bytes(b'synthetic private index must remain')

    def assets(self, root):
        snapshot = root / ('models--' + EMBEDDING_ID.replace('/', '--')) / 'snapshots' / EMBEDDING_REVISION
        snapshot.mkdir(parents=True)
        for name in EMBEDDING_ASSETS:
            path = snapshot / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('synthetic public ' + name).encode())
        return snapshot

    def test_check_is_read_only_and_use_persists_verified_location(self):
        target = self.assets(self.second)
        with patch.dict('sys.modules', {'huggingface_hub': None}):
            checked = self.service.check_folder(str(self.second))
            self.assertEqual(checked['state'], 'valid')
            self.assertEqual(self.manifest.read_bytes(), self.original)
            self.service.use_folder(checked['path'], checked['revision'])
        self.assertEqual(folder_status(self.config)['path'], str(self.second))
        with patch.dict(os.environ, {'HF_HUB_CACHE': str(self.root / 'another-tool-cache')}):
            self.assertEqual(verified_assets(self.manifest)[0], target)
        self.assertTrue((self.snapshot / 'model.safetensors').is_file())
        self.assertEqual(self.private_index.read_bytes(), b'synthetic private index must remain')
        self.search.model_changed.assert_called_once()
        self.search.request_prepare.assert_not_called()
        # Both the HF default and the separately selected cache remain measurable.
        measured = storage_status(self.config)
        self.assertEqual(measured['models'], str(self.first))
        self.assertEqual(measured['embedding_models'], str(self.second))
        self.assertTrue(_private_derived(target / 'README.md', self.config, self.second))

    def test_changed_files_between_check_and_use_preserve_old_registration(self):
        target = self.assets(self.second)
        checked = self.service.check_folder(str(self.second))
        (target / 'model.safetensors').write_bytes(b'changed after checking')
        with self.assertRaises(PreferencesError):
            self.service.use_folder(checked['path'], checked['revision'])
        self.assertEqual(self.manifest.read_bytes(), self.original)
        self.assertEqual(verified_assets(self.manifest)[0], self.snapshot)
        self.assertEqual(inspect_folder(str(self.second), self.config)['state'], 'invalid')
        self.search.model_changed.assert_not_called()

    def test_concurrent_registration_change_is_not_overwritten(self):
        self.assets(self.second)
        checked = self.service.check_folder(str(self.second))
        value = json.loads(self.original); value['future_setting'] = 'preserve'
        atomic_json(self.manifest, value)
        concurrent = self.manifest.read_bytes()
        with self.assertRaisesRegex(PreferencesError, '설정이 변경'):
            self.service.use_folder(checked['path'], checked['revision'])
        self.assertEqual(self.manifest.read_bytes(), concurrent)

    def test_missing_folder_and_private_overlap_do_not_change_files(self):
        empty = self.root / 'not-created'
        checked = self.service.check_folder(str(empty))
        self.assertEqual(checked['state'], 'missing')
        self.assertFalse(empty.exists())
        with self.assertRaises(PreferencesError):
            self.service.use_folder(str(empty), checked['revision'])
        self.assertEqual(self.manifest.read_bytes(), self.original)
        for path in (self.root, self.config.data_dir / 'models', self.config.cache_dir):
            with self.subTest(path=path), self.assertRaisesRegex(PreferencesError, '겹치지 않는'):
                self.service.check_folder(str(path))

    def test_symlinked_snapshot_is_not_offered_as_verified(self):
        target = self.assets(self.second)
        moved = target.with_name('other-snapshot'); target.rename(moved)
        target.symlink_to(moved, target_is_directory=True)
        self.assertEqual(self.service.check_folder(str(self.second))['state'], 'invalid')
        self.assertEqual(self.manifest.read_bytes(), self.original)

    def test_interrupted_selected_download_keeps_old_location_then_resumes(self):
        checked = self.service.check_folder(str(self.second))
        partial = self.second / 'download.incomplete'
        calls = []
        def download(**kwargs):
            calls.append(kwargs)
            self.assertEqual(Path(kwargs['cache_dir']), self.second)
            if len(calls) == 1:
                self.second.mkdir(); partial.write_bytes(b'synthetic partial download')
                raise OSError('synthetic interrupted download')
            self.assertTrue(partial.exists())
            return str(self.assets(self.second))
        env = {'LOCALBRAIN_MODEL_KEY': 'embedding', 'LOCALBRAIN_MODEL_CACHE_ROOT': str(self.second),
               'LOCALBRAIN_MODEL_REGISTRATION_REVISION': checked['revision']}
        with patch.dict(os.environ, env), patch('localbrain.foundation.config.settings', self.config), \
             patch.dict('sys.modules', {'huggingface_hub': SimpleNamespace(snapshot_download=download),
                                       'truststore': SimpleNamespace(inject_into_ssl=lambda: None)}), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(download_worker(), 1)
            self.assertEqual(self.manifest.read_bytes(), self.original)
            self.assertTrue(partial.exists())
            self.assertEqual(download_worker(), 0)
        self.assertEqual(folder_status(self.config)['path'], str(self.second))
        self.assertTrue((self.snapshot / 'model.safetensors').is_file())
        self.assertEqual(self.private_index.read_bytes(), b'synthetic private index must remain')

    def test_folder_operations_cannot_race_a_model_job(self):
        self.service._folder_busy = True
        with self.assertRaises(PreferencesError):
            self.service.check_folder(str(self.second))
        with self.assertRaises(PreferencesError):
            self.service.start(cache_root=str(self.second), revision=folder_status(self.config)['revision'])
        self.assertEqual(self.manifest.read_bytes(), self.original)

    def test_malformed_registration_returns_bounded_location_error(self):
        registrations = [[], *[{'schema': 'foundry.semantic-model/v1', 'snapshot': value}
                               for value in (True, 1, [], {}, None, '')]]
        for value in registrations:
            with self.subTest(registration=value):
                original = json.dumps(value)
                self.manifest.write_text(original)
                status = folder_status(self.config)
                self.assertIsNone(status['path'])
                self.assertIsNone(status['revision'])
                self.assertIn('확인하지 못했습니다', status['error'])
                self.assertEqual(self.service.status()['folder'], status)
                self.assertIn('models', storage_status(self.config))
                self.assertEqual(self.manifest.read_text(), original)

    def test_folder_selection_never_changes_model_identity(self):
        self.assets(self.second)
        value = json.loads(self.original); value['resolved_revision'] = '0' * 40
        atomic_json(self.manifest, value)
        changed = self.manifest.read_bytes()
        checked = self.service.check_folder(str(self.second))
        with self.assertRaisesRegex(PreferencesError, '모델의 버전'):
            self.service.use_folder(checked['path'], checked['revision'])
        self.assertEqual(self.manifest.read_bytes(), changed)

    def test_unrelated_registration_fields_survive_location_change(self):
        self.assets(self.second)
        value = json.loads(self.original); value['future_setting'] = 'preserve'
        atomic_json(self.manifest, value)
        checked = self.service.check_folder(str(self.second))
        self.service.use_folder(checked['path'], checked['revision'])
        self.assertEqual(json.loads(self.manifest.read_text())['future_setting'], 'preserve')

    def test_empty_or_non_object_registration_is_preserved_on_apply(self):
        self.assets(self.second)
        for content in ('[]', '{}'):
            with self.subTest(content=content):
                self.manifest.write_text(content)
                from localbrain.models.installation import registration_revision
                with self.assertRaises(PreferencesError):
                    self.service.use_folder(str(self.second), registration_revision(self.metadata))
                self.assertEqual(self.manifest.read_text(), content)

    def test_model_download_destination_stays_outside_git_worktrees(self):
        repository = self.root / 'synthetic-project'; repository.mkdir()
        (repository / '.git').write_text('gitdir: /synthetic')
        candidate = repository / 'model-cache'
        with self.assertRaisesRegex(PreferencesError, '소스 코드 저장소 밖'):
            self.service.check_folder(str(candidate))
        self.assertFalse(candidate.exists())
        self.assertEqual(self.manifest.read_bytes(), self.original)

    def test_unsupported_registration_schema_is_not_rewritten(self):
        self.assets(self.second)
        for schema in ('future-model-schema/v99', [], {}):
            with self.subTest(schema=schema):
                value = json.loads(self.original); value['schema'] = schema
                atomic_json(self.manifest, value)
                checked = self.service.check_folder(str(self.second))
                original = self.manifest.read_bytes()
                with self.assertRaisesRegex(PreferencesError, '모델의 버전'):
                    self.service.use_folder(checked['path'], checked['revision'])
                self.assertEqual(self.manifest.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
