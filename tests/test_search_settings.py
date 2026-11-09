"""Query-only cutoff changes preserve activation, profile and indexed evidence."""
from dataclasses import asdict
import json
import tempfile
import unittest
from unittest.mock import patch

from localbrain.foundation.private_json import atomic_json
from localbrain.natural_search.index import folder, prepare, read_settings, save_settings, search_settings, update_cutoff
from localbrain.natural_search.molecules import Profile
from localbrain.natural_search.service import SearchService
from natural_search_fixtures import ContractEncoder, fixture


class SearchSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='localbrain-search-settings-')
        self.addCleanup(self.temp.cleanup)
        self.config = fixture(self.temp.name)
        self.path = self.config.data_dir / 'natural-search.json'

    def test_default_read_is_read_only_and_cutoff_does_not_enable_search(self):
        state = search_settings(self.config)
        self.assertEqual((state['cutoff'], state['default_cutoff']), (.45, .45))
        self.assertFalse(self.path.exists())
        update_cutoff(self.config, .2, state['revision'])
        enabled, profile = read_settings(self.config)
        self.assertFalse(enabled)
        self.assertEqual(profile.cutoff, .2)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_only_cutoff_changes_and_default_can_be_restored(self):
        profile = Profile(target=256, dimension=1024, overlap=64, cutoff=.6)
        original = {'version': 1, 'enabled': True, 'profile': asdict(profile), 'future_note': 'preserve'}
        atomic_json(self.path, original)
        for cutoff in (0, 1, .45):
            current = search_settings(self.config)
            update_cutoff(self.config, cutoff, current['revision'])
            actual = json.loads(self.path.read_text())
            self.assertEqual(actual, {**original, 'profile': {**original['profile'], 'cutoff': cutoff}})

    def test_invalid_or_stale_write_preserves_the_current_file(self):
        save_settings(self.config, enabled=False)
        original = self.path.read_bytes()
        state = search_settings(self.config)
        for value in (-.01, 1.01, 10 ** 400, float('nan'), float('inf'), True, '0.4', None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, '^INVALID_SEARCH_CUTOFF$'):
                update_cutoff(self.config, value, state['revision'])
            self.assertEqual(self.path.read_bytes(), original)
        save_settings(self.config, enabled=True)
        changed = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, '^SEARCH_SETTINGS_CHANGED$'):
            update_cutoff(self.config, .1, state['revision'])
        self.assertEqual(self.path.read_bytes(), changed)

    def test_failed_publication_preserves_configuration(self):
        save_settings(self.config)
        original = self.path.read_bytes()
        with patch('localbrain.natural_search.index.atomic_json', side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError):
                update_cutoff(self.config, .1, search_settings(self.config)['revision'])
        self.assertEqual(self.path.read_bytes(), original)

    def test_next_query_uses_new_cutoff_without_reencoding_or_rebuilding(self):
        profile = Profile()
        save_settings(self.config, profile)
        prepare(self.config, ContractEncoder(self.config, profile), profile)
        service = SearchService(self.config, ContractEncoder)
        self.addCleanup(service.stop)
        query = '찾을 수 없는 독특한 질문'
        self.assertEqual(service.search(query)['total'], 0)
        encoder, reader, _ = service.engine()
        index = folder(self.config) / 'index.sqlite3'
        before = (index.read_bytes(), index.stat().st_mtime_ns)
        with patch('localbrain.natural_search.service.prepare', side_effect=AssertionError('unexpected reindex')):
            update_cutoff(self.config, 0, search_settings(self.config)['revision'])
            self.assertGreater(service.search(query)['total'], 0)
        self.assertIs(service.engine()[0], encoder)
        self.assertIs(service.engine()[1], reader)
        self.assertEqual((index.read_bytes(), index.stat().st_mtime_ns), before)
        update_cutoff(self.config, .45, search_settings(self.config)['revision'])
        self.assertEqual(service.search(query)['total'], 0)
        self.assertEqual((index.read_bytes(), index.stat().st_mtime_ns), before)
