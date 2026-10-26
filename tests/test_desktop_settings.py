"""Synthetic-only contracts for shared settings and standalone lifecycle."""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from unittest.mock import Mock

from localbrain import db
from localbrain.config import Settings, load_settings, _system_timezone_name
from localbrain.local_operations import OperationBusy, operation_lock
from localbrain.preferences import PreferencesError, read_preferences, save_preferences
from localbrain.path_display import home_relative_path
from localbrain.source_settings import source_inventory, update_source
from localbrain.session_sync import SessionSyncService
from localbrain.storage_recovery import create_backup, validate_backup, backend_storage_lease, clear_owned_cache


class DesktopSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        self.data.mkdir()
        self.config = Settings(self.data, self.data / 'localbrain.db', self.root / 'context',
                               self.root / 'claude', self.root / 'codex', 20, 'UTC',
                               session_sources_path=self.data / 'session-sources.toml', cache_dir=self.root / 'cache')
        self.patch = patch.object(db, 'settings', self.config)
        self.patch.start()
        db.init_db()
        self.env = patch.dict(os.environ, {key: value for key, value in os.environ.items() if not key.startswith('LOCALBRAIN_')}, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.patch.stop()
        self.temp.cleanup()

    def register(self):
        folder = self.root / 'sessions'
        folder.mkdir(exist_ok=True)
        state = source_inventory(self.config)
        return update_source({'revision': state['revision'], 'provider_kind': 'codex', 'display_label': 'Personal', 'root': str(folder)}, self.config)

    def test_fresh_sources_and_context_are_empty(self):
        self.assertEqual(source_inventory(self.config)['sources'], [])
        with db.connect() as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM context_roots').fetchone()[0], 0)

    def test_file_settings_unknown_fields_and_revision(self):
        current = read_preferences(self.config)
        self.assertEqual(current['effective']['session_sync_minutes'], 10)
        path = self.data / 'settings.toml'
        path.write_text('schema_version = 1\nfuture_note = "keep"\nsession_sync_minutes = 30\n')
        current = read_preferences(self.config)
        with patch.dict(os.environ, {'LOCALBRAIN_SESSION_SYNC_MINUTES': '60'}):
            saved = save_preferences({'session_sync_minutes': 10}, current['revision'], self.config)
            self.assertEqual(saved['saved']['session_sync_minutes'], 10)
            self.assertEqual(saved['effective']['session_sync_minutes'], 10)
            self.assertEqual(saved['source']['session_sync_minutes'], 'saved')
            self.assertEqual(saved['raw']['future_note'], 'keep')
        with self.assertRaises(PreferencesError):
            save_preferences({'timezone': 'UTC'}, current['revision'], self.config)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_general_preferences_ignore_old_environment_overrides(self):
        changes = {'startup_screen': 'context', 'timezone': 'Asia/Seoul',
                   'session_sync_enabled': False, 'session_sync_minutes': 30}
        current = read_preferences(self.config)
        saved = save_preferences(changes, current['revision'], self.config)
        content = (self.data / 'settings.toml').read_bytes()
        for overrides in (
            {'LOCALBRAIN_STARTUP_SCREEN': 'sessions', 'LOCALBRAIN_TIMEZONE': 'UTC',
             'LOCALBRAIN_SESSION_SYNC_ENABLED': 'true', 'LOCALBRAIN_SESSION_SYNC_MINUTES': '60'},
            {key: 'invalid-retired-value' for key in (
                'LOCALBRAIN_STARTUP_SCREEN', 'LOCALBRAIN_TIMEZONE',
                'LOCALBRAIN_SESSION_SYNC_ENABLED', 'LOCALBRAIN_SESSION_SYNC_MINUTES')},
        ):
            with self.subTest(overrides=overrides), patch.dict(os.environ, overrides):
                actual = read_preferences(self.config)
                self.assertEqual(actual, saved)
                self.assertEqual(actual['saved'], actual['effective'])
                for key, value in changes.items():
                    self.assertEqual(actual['effective'][key], value)
                    self.assertEqual(actual['source'][key], 'saved')
                self.assertEqual((self.data / 'settings.toml').read_bytes(), content)

    def test_missing_preferences_use_defaults_without_environment(self):
        with patch.dict(os.environ, {'LOCALBRAIN_STARTUP_SCREEN': 'context',
            'LOCALBRAIN_TIMEZONE': 'not/a-zone', 'LOCALBRAIN_SESSION_SYNC_ENABLED': 'false',
            'LOCALBRAIN_SESSION_SYNC_MINUTES': '60', 'TZ': 'not/a-zone'}):
            current = read_preferences(self.config)
            self.assertEqual(current['effective'], {'startup_screen': 'sessions', 'timezone': 'UTC',
                'session_sync_enabled': True, 'session_sync_minutes': 10,
                'context_sync_enabled': True, 'context_sync_minutes': 30, 'onboarding_completed': False})
            self.assertEqual(set(current['source'].values()), {'default'})
            self.assertFalse((self.data / 'settings.toml').exists())
            with patch('localbrain.config.Path.resolve', return_value=Path('/usr/share/zoneinfo/Asia/Seoul')):
                self.assertEqual(_system_timezone_name(), 'Asia/Seoul')
                self.assertEqual(load_settings().timezone_name, 'Asia/Seoul')

    def test_sync_runtime_follows_file_despite_old_environment(self):
        self.register()
        current = read_preferences(self.config)
        save_preferences({'session_sync_minutes': 10}, current['revision'], self.config)
        calls = []
        service = SessionSyncService(self.config, lambda **kwargs: calls.append(1) or {'outcome': 'complete'})
        service._write({'completed_at': 1000})
        with patch.dict(os.environ, {'LOCALBRAIN_SESSION_SYNC_MINUTES': '60', 'LOCALBRAIN_SESSION_SYNC_ENABLED': 'false'}), \
             patch('localbrain.source_sync.time.time', return_value=1600):
            service._collect(False)
            self.assertEqual(len(calls), 1)
            self.assertTrue(service.status()['enabled'])
            self.assertEqual(service.status()['minutes'], 10)
            self.assertEqual(service.status()['next_at'], 2200)
        current = read_preferences(self.config)
        save_preferences({'session_sync_enabled': False}, current['revision'], self.config)
        with patch.dict(os.environ, {'LOCALBRAIN_SESSION_SYNC_ENABLED': 'true'}), \
             patch('localbrain.source_sync.time.time', return_value=5000):
            service._collect(False)
            self.assertEqual(len(calls), 1)
            self.assertFalse(service.status()['enabled'])
            self.assertIsNone(service.status()['next_at'])

    def test_malformed_future_file_preserved(self):
        for content in ['bad [', 'schema_version = 2']:
            path = self.data / 'settings.toml'
            path.write_text(content)
            with self.assertRaises(PreferencesError):
                read_preferences(self.config)
            self.assertEqual(path.read_text(), content)

    def test_invalid_preference_rejected(self):
        for change in [{'timezone': 'not/a-zone'}, {'session_sync_minutes': 1}, {'startup_screen': []}, {'onboarding_completed': 1}]:
            current = read_preferences(self.config)
            with self.assertRaises(PreferencesError):
                save_preferences(change, current['revision'], self.config)

    def test_custom_sync_interval_round_trip_and_bounds(self):
        current = read_preferences(self.config)
        for minutes in (10, 17, 45, 1440):
            with self.subTest(minutes=minutes):
                current = save_preferences({'session_sync_minutes': minutes}, current['revision'], self.config)
                self.assertEqual(read_preferences(self.config)['effective']['session_sync_minutes'], minutes)
        content = (self.data / 'settings.toml').read_bytes()
        for minutes in (9, 1441, 45.5, 45.0, True, '45', None):
            with self.subTest(invalid=minutes), self.assertRaises(PreferencesError):
                save_preferences({'session_sync_minutes': minutes}, current['revision'], self.config)
            self.assertEqual((self.data / 'settings.toml').read_bytes(), content)

    def test_custom_sync_interval_controls_due_time_and_survives_off(self):
        self.register()
        current = read_preferences(self.config)
        current = save_preferences({'session_sync_minutes': 17}, current['revision'], self.config)
        calls = []
        service = SessionSyncService(self.config, lambda **kwargs: calls.append(1) or {'outcome': 'complete'})
        service._write({'completed_at': 1000})
        with patch('localbrain.source_sync.time.time', return_value=2019):
            service._collect(False)
            self.assertEqual(calls, [])
            self.assertEqual(service.status()['next_at'], 2020)
        with patch('localbrain.source_sync.time.time', return_value=2020):
            service._collect(False)
            self.assertEqual(calls, [1])
            self.assertEqual(service.status()['next_at'], 3040)
        current = save_preferences({'session_sync_enabled': False}, current['revision'], self.config)
        with patch('localbrain.source_sync.time.time', return_value=3040):
            service._collect(False)
            self.assertEqual(calls, [1])
            self.assertIsNone(service.status()['next_at'])
            save_preferences({'session_sync_enabled': True}, current['revision'], self.config)
            self.assertEqual(service.status()['minutes'], 17)
            service._collect(False)
            self.assertEqual(calls, [1, 1])

    def test_home_display_preserves_suffix_and_path_boundaries(self):
        for home in (Path('/Users/<demo>'), Path('/Users/<another>')):
            cases = [(home, '~'), (home / 'Projects', '~/Projects'),
                     (home / 'Project1', '~/Project1'), (home / 'Project2', '~/Project2'),
                     (home / '.codex-work/sessions', '~/.codex-work/sessions'),
                     (str(home) + '2/app', str(home) + '2/app'),
                     ('/Volumes/Work/app', '/Volumes/Work/app'),
                     ('/Users/<other>/app', '/Users/<other>/app'),
                     ('~/missing/app', '~/missing/app'), ('relative/app', 'relative/app'),
                     ('', ''), (None, '')]
            with patch('localbrain.path_display.Path.home', return_value=home):
                for value, expected in cases:
                    with self.subTest(home=home, path=value):
                        self.assertEqual(home_relative_path(value), expected)

    def test_home_display_does_not_resolve_symlinks_or_require_existing_paths(self):
        link = self.root / 'linked-folder'
        link.symlink_to('/Volumes/Unavailable')
        with patch('localbrain.path_display.Path.home', return_value=self.root), \
             patch.object(Path, 'resolve', side_effect=AssertionError('Display must not resolve paths')), \
             patch.object(Path, 'exists', side_effect=AssertionError('Display must not probe paths')):
            self.assertEqual(home_relative_path(link / 'missing'), '~/linked-folder/missing')

    def test_retired_path_settings_are_inactive_and_preserved(self):
        path = self.data / 'settings.toml'
        for legacy in ('project_display = "absolute"\n[[projects]]\npath = "/Users/<demo>"\nlabel = "Alias"\n',
                       'project_display = "invalid-old-value"\nprojects = ["invalid-old-entry"]\n'):
            path.write_text('schema_version = 1\nfuture_note = "keep"\n' + legacy)
            with patch.dict(os.environ, {'LOCALBRAIN_PROJECT_DISPLAY': 'invalid-old-override'}):
                current = read_preferences(self.config)
                for section in ('saved', 'effective', 'source'):
                    self.assertNotIn('project_display', current[section])
                    self.assertNotIn('projects', current[section])
                saved = save_preferences({'timezone': 'UTC'}, current['revision'], self.config)
                for key in ('project_display', 'projects', 'future_note'):
                    self.assertEqual(saved['raw'][key], current['raw'][key])
                with patch('localbrain.path_display.Path.home', return_value=Path('/Users/<demo>')):
                    self.assertEqual(home_relative_path('/Users/<demo>/Project1'), '~/Project1')

    def test_retired_settings_cannot_be_written_or_created(self):
        current = read_preferences(self.config)
        for change in ({'project_display': 'absolute'}, {'projects': []}):
            with self.assertRaises(PreferencesError):
                save_preferences(change, current['revision'], self.config)
        saved = save_preferences({'timezone': 'UTC'}, current['revision'], self.config)
        self.assertNotIn('project_display', saved['raw'])
        self.assertNotIn('projects', saved['raw'])

    def test_workspace_label_uses_home_without_changing_identity(self):
        from localbrain.ingest.scanner import _upsert_workspace
        home = self.root / 'home'
        project = home / 'Projects'
        project.mkdir(parents=True)
        canonical = str(project.resolve())
        with db.connect() as connection, patch('localbrain.path_display.Path.home', return_value=home.resolve()):
            old_id = connection.execute('INSERT INTO workspaces(canonical_path, display_name) VALUES (?, ?)',
                                        (canonical, '.')).lastrowid
            self.assertEqual(_upsert_workspace(connection, canonical, None), old_id)
            row = connection.execute('SELECT canonical_path, display_name FROM workspaces WHERE id = ?', (old_id,)).fetchone()
            self.assertEqual(row['canonical_path'], canonical)
            self.assertEqual(row['display_name'], '~/Projects')

    def test_context_home_display_uses_same_rule_without_changing_source_path(self):
        from localbrain.contexts import add_context_root, list_context_sources
        with db.connect() as connection:
            source_id = add_context_root(connection, str(self.root))
            with patch('localbrain.path_display.Path.home', return_value=self.root.resolve()):
                source = next(row for row in list_context_sources(connection) if row['id'] == source_id)
            self.assertEqual(source['display_path'], '~')
            self.assertEqual(source['path'], str(self.root.resolve()))

    def test_source_rename_identity_and_overlap(self):
        state = self.register()
        source = state['sources'][0]
        updated = update_source({'revision': state['revision'], 'source_id': source['id'], 'provider_kind': 'codex', 'display_label': 'Renamed', 'root': source['root_path']}, self.config)
        self.assertEqual(updated['sources'][0]['id'], source['id'])
        with self.assertRaises(PreferencesError):
            update_source({'revision': updated['revision'], 'provider_kind': 'claude', 'display_label': 'Overlap', 'root': source['root_path']}, self.config)
        removed = update_source({'revision': updated['revision'], 'source_id': source['id'], 'action': 'remove'}, self.config)
        self.assertFalse(removed['sources'][0]['registered'])
        self.assertEqual(removed['sources'][0]['id'], source['id'])

    def test_disabled_source_does_not_make_sync_fail_and_can_be_reenabled(self):
        from localbrain.ingest import scanner
        current = self.register()
        source = current['sources'][0]
        current = update_source({'revision': current['revision'], 'source_id': source['id'], 'action': 'remove'}, self.config)
        with patch.object(scanner, 'settings', self.config):
            report = scanner.scan_session_sources()
        self.assertEqual(report['outcome'], 'complete')
        self.assertEqual(report['sources'], [])
        current = update_source({'revision': current['revision'], 'source_id': source['id'], 'provider_kind': 'codex', 'display_label': 'Restored', 'root': source['root_path']}, self.config)
        self.assertTrue(current['sources'][0]['registered'])
        self.assertEqual(current['sources'][0]['id'], source['id'])

    def test_operations_coalesce_between_threads(self):
        outcome = []
        with operation_lock(self.config, 'one'):
            def contender():
                try:
                    with operation_lock(self.config, 'two'):
                        outcome.append('wrong')
                except OperationBusy:
                    outcome.append('busy')
            thread = threading.Thread(target=contender); thread.start(); thread.join()
        self.assertEqual(outcome, ['busy'])

    def test_operations_exclude_another_backend_process(self):
        code = '''from pathlib import Path
from types import SimpleNamespace
import sys
from localbrain.local_operations import operation_lock, OperationBusy
try:
    with operation_lock(SimpleNamespace(data_dir=Path(sys.argv[1])), 'other-backend'):
        print('unexpected-write')
except OperationBusy:
    print('busy')
'''
        with operation_lock(self.config, 'first-backend'):
            result = subprocess.run([sys.executable, '-c', code, str(self.data)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'busy')

    def test_sync_completion_interval_failure_retains_success(self):
        calls = []
        service = SessionSyncService(self.config, lambda **kwargs: calls.append(1) or {'outcome': 'complete'})
        with patch('localbrain.source_sync.time.time', return_value=1000):
            service._collect(False)
        self.assertEqual(service.status()['last_success_at'], 1000)
        with patch('localbrain.source_sync.time.time', return_value=1599):
            service._collect(False)
        self.assertEqual(len(calls), 1)
        with patch('localbrain.source_sync.time.time', return_value=1600):
            service._collect(False)
        self.assertEqual(len(calls), 2)
        service.scanner = lambda **kwargs: (_ for _ in ()).throw(RuntimeError('private detail'))
        service._collect(True)
        self.assertEqual(service.status()['last_success_at'], 1600)
        self.assertNotIn('private detail', service.status()['error'])
        self.assertFalse(service.status()['running'])

    def test_disabled_sync_keeps_manual_action(self):
        current = read_preferences(self.config)
        save_preferences({'session_sync_enabled': False}, current['revision'], self.config)
        calls = []
        service = SessionSyncService(self.config, lambda **kwargs: calls.append(1) or {'outcome': 'complete'})
        service._collect(False)
        self.assertFalse(calls)
        service._collect(True)
        self.assertEqual(len(calls), 1)
        self.assertIsNone(service.status()['next_at'])

    def test_health_writes_do_not_change_database_stamp(self):
        before = self.config.database_path.stat().st_mtime_ns
        service = SessionSyncService(self.config, lambda **kwargs: {'outcome': 'complete'})
        service._write({'last_success_at': 1000})
        self.assertEqual(self.config.database_path.stat().st_mtime_ns, before)
        self.assertEqual(service.status()['last_success_at'], 1000)

    def test_manual_request_coalesces_with_other_backend_completion(self):
        calls = []
        service = SessionSyncService(self.config, lambda **kwargs: calls.append(1) or {'outcome': 'complete'})
        service._requested_at = 1000
        service._request.set()
        service._write({'completed_at': 1001, 'generation': 3})
        service._collect(True)
        self.assertFalse(calls)
        self.assertFalse(service.status()['queued'])

    def test_empty_registration_has_no_next_schedule(self):
        service = SessionSyncService(self.config, lambda **kwargs: {'outcome': 'complete'})
        self.assertIsNone(service.status()['next_at'])

    def test_download_worker_exits_when_parent_pipe_closes(self):
        code = ('import time; from localbrain import model_installation; '
                'model_installation.install_embedding=lambda *a, **k: time.sleep(60); '
                'from localbrain.model_setup import download_worker; download_worker()')
        process = subprocess.Popen([sys.executable, '-c', code], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, 'LOCALBRAIN_DATA_DIR': str(self.data), 'LOCALBRAIN_MODEL_PARENT_PIPE': '1'})
        try:
            process.communicate(timeout=10)
            self.assertEqual(process.returncode, -15)
        finally:
            if process.poll() is None:
                process.kill(); process.wait()

    def test_successful_download_worker_exits_with_parent_pipe_open(self):
        code = ('import sys; from types import SimpleNamespace; '
                'sys.modules["truststore"]=SimpleNamespace(inject_into_ssl=lambda: None); '
                'from localbrain import model_installation; '
                'model_installation.install_embedding=lambda *a, **k: None; '
                'from localbrain.model_setup import download_worker; sys.exit(download_worker())')
        process = subprocess.Popen([sys.executable, '-c', code], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, 'LOCALBRAIN_DATA_DIR': str(self.data), 'LOCALBRAIN_MODEL_PARENT_PIPE': '1'})
        try:
            process.wait(timeout=10)
            self.assertEqual(process.returncode, 0, process.stderr.read().decode())
            self.assertIn('installed', process.stdout.read().decode())
        finally:
            if process.poll() is None:
                process.kill(); process.wait()
            process.stdin.close(); process.stdout.close(); process.stderr.close()

    def test_unknown_toml_dates_are_preserved(self):
        path = self.data / 'settings.toml'
        path.write_text('schema_version = 1\nfuture_date = 2026-01-01\n')
        current = read_preferences(self.config)
        saved = save_preferences({'timezone': 'UTC'}, current['revision'], self.config)
        self.assertEqual(str(saved['raw']['future_date']), '2026-01-01')

    def test_backup_restore_and_original_exclusion(self):
        self.register()
        (self.root / 'sessions' / 'private.jsonl').write_text('original stays outside backup')
        work, archive = create_backup(self.config)
        try:
            with zipfile.ZipFile(archive) as bundle:
                self.assertNotIn('private.jsonl', bundle.namelist())
            staged = self.root / 'staged'; staged.mkdir()
            validate_backup(archive, staged, self.config)
            shutil.copyfile(archive, self.data / 'restore-pending.zip')
            with db.transaction() as connection:
                connection.execute("UPDATE sources SET name='changed'")
            with backend_storage_lease(self.config):
                with db.connect() as connection:
                    self.assertEqual(connection.execute('SELECT name FROM sources').fetchone()[0], 'Personal')
            self.assertTrue((self.data / 'recovery' / 'before' / 'localbrain.db').exists())
            self.assertFalse((self.data / 'restore-pending.zip').exists())
        finally:
            shutil.rmtree(work)

    def test_malicious_archive_is_rejected_before_writes(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            bundle.writestr('../escaped', 'bad')
        staged = self.root / 'staged'; staged.mkdir()
        with self.assertRaises(PreferencesError):
            validate_backup(archive, staged, self.config)
        self.assertFalse((self.root / 'escaped').exists())

    def test_cache_cleanup_checks_owner_and_preserves_originals(self):
        from localbrain.natural_search import index
        from localbrain.natural_search.source import digest
        from localbrain.runtime_storage import private_database
        original = self.root / 'original.md'; original.write_text('keep original')
        with index.writer(self.config) as folder:
            database = folder / 'building.sqlite3'
            private_database(database)
            with sqlite3.connect(database) as connection:
                connection.executescript(index.SCHEMA)
                index.set_meta(connection, owner='some-other-owner', binding=digest(str(self.config.database_path.resolve())))
            connection.close()
        search = Mock()
        with self.assertRaises(PreferencesError):
            clear_owned_cache(search, self.config)
        self.assertTrue(database.exists())
        with sqlite3.connect(database) as connection:
            index.set_meta(connection, owner=index.OWNER)
        connection.close()
        result = clear_owned_cache(search, self.config)
        self.assertGreater(result['removed_bytes'], 0)
        self.assertFalse(database.exists())
        self.assertEqual(original.read_text(), 'keep original')
        self.assertEqual(search.start.call_count, 2)


if __name__ == '__main__':
    unittest.main()
