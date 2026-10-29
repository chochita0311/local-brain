"""Model discovery/setup preserves shared public assets and embedding behavior."""
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from localbrain.model_installation import generation_models, generation_runtime_missing, runtime_missing
from localbrain.model_setup import ModelSetupService
from localbrain.preferences import PreferencesError


class ModelSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = SimpleNamespace(data_dir=self.root / 'app')
        self.search = Mock()
        self.service = ModelSetupService(self.config, self.search)

    def tearDown(self):
        self.tmp.cleanup()

    def test_cached_original_is_available_without_app_registration_or_hashing(self):
        repo = self.root / 'shared'; snapshot = repo / 'snapshots/pinned'; snapshot.mkdir(parents=True)
        (snapshot / 'model.safetensors').write_bytes(b'public sample')
        with patch('localbrain.model_installation.hub_repository', return_value=repo), patch(
                'localbrain.work_context_model.model_spec', return_value={'id': 'Qwen/Demo', 'revision': 'pinned', 'assets': {'model.safetensors'}}):
            models = generation_models(self.config)
            self.assertTrue(all(m['cached'] and m['available'] and not m['registered'] for m in models))
        self.assertFalse(self.config.data_dir.exists())
        self.assertEqual((snapshot / 'model.safetensors').read_bytes(), b'public sample')

    def test_generation_does_not_require_embedding_packages(self):
        with patch('localbrain.model_installation.importlib.util.find_spec', side_effect=lambda name: object() if name in {'torch','transformers','huggingface_hub'} else None):
            self.assertEqual(generation_runtime_missing(), [])
            self.assertIn('sentence_transformers', runtime_missing())

    def test_generation_install_does_not_prepare_embedding_index(self):
        self.service._active_key = '4b'
        process = SimpleNamespace(stdout=io.StringIO('{"phase":"installed"}\n'), stdin=io.StringIO(), wait=lambda: 0)
        self.service._watch(process)
        self.assertEqual(self.service._generation_phases['4b'], 'installed')
        self.search.request_prepare.assert_not_called()

    def test_embedding_install_still_prepares_index(self):
        process = SimpleNamespace(stdout=io.StringIO('{"phase":"installed"}\n'), stdin=io.StringIO(), wait=lambda: 0)
        self.service._watch(process)
        self.assertEqual(self.service._phase, 'preparing')
        self.search.request_prepare.assert_called_once()

    def test_unknown_model_never_starts_process(self):
        with patch('localbrain.model_setup.subprocess.Popen') as start, self.assertRaises(PreferencesError):
            self.service.start('arbitrary/remote-model')
        start.assert_not_called()

    def test_generation_cancel_does_not_cancel_embedding_search(self):
        self.service._active_key = '8b'
        self.service.cancel()
        self.search.cancel.assert_not_called()
        self.assertEqual(self.service._generation_phases['8b'], 'canceled')

    def test_install_command_passes_only_pinned_model_key_and_app_root(self):
        with patch('localbrain.model_setup.runtime_missing', return_value=[]), patch(
                'localbrain.model_setup.generation_runtime_missing', return_value=[]), patch(
                'localbrain.model_setup.subprocess.Popen') as start, patch('localbrain.model_setup.threading.Thread'):
            self.service.start('8b')
        env = start.call_args.kwargs['env']
        self.assertEqual(env['LOCALBRAIN_MODEL_KEY'], '8b')
        self.assertEqual(env['LOCALBRAIN_DATA_DIR'], str(self.config.data_dir))
        self.assertNotIn('HF_HOME', {k:v for k,v in env.items() if v == str(self.config.data_dir)})


if __name__ == '__main__':
    unittest.main()
