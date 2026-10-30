"""Profile identity and presentation changes must not recreate imported history."""
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from localbrain import db
from localbrain.config import Settings
from localbrain.ingest import scanner
from localbrain.preferences import PreferencesError, toml_text, tomllib
from localbrain.queries import session_source_scopes, session_inventory_page
from localbrain.session_chart_preferences import get_project_visibility, set_project_visibility
from localbrain.session_sources import load_session_source_settings
from localbrain.source_settings import source_inventory, update_source, migrate_source_settings
from localbrain.usage_queries import normalize_usage_scope
import test_session_sync as sync_fixtures


class SourceProfileTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.data = self.root / 'data'
        self.data.mkdir()
        self.config = Settings(self.data, self.data / 'localbrain.db', self.root / 'context',
                               self.root / 'claude', self.root / 'codex', 20, 'UTC',
                               session_sources_path=self.data / 'session-sources.toml', cache_dir=self.root / 'cache')
        self.stack.enter_context(patch.object(db, 'settings', self.config))
        self.stack.enter_context(patch.object(scanner, 'settings', self.config))
        db.init_db()
        self.path = self.config.session_sources_path
        self.addCleanup(self.stack.close)

    def write(self, entries, version=2):
        self.path.write_text(toml_text(dict(schema_version=version, session_sources=entries)))

    def register(self, name):
        folder = self.root / name / 'sessions'
        folder.mkdir(parents=True)
        state = source_inventory(self.config)
        return update_source(dict(revision=state['revision'], provider_kind='codex', display_label=name,
                                  root=str(folder), agent_home=str(folder.parent)), self.config)

    def mutate(self, **change):
        state = source_inventory(self.config)
        return update_source(dict(revision=state['revision'], **change), self.config)

    def legacy_fixture(self):
        entries = []
        for key in ('codex', 'custom-work'):
            folder = self.root / key
            folder.mkdir()
            sync_fixtures.SessionSyncTests()._write_codex_session(folder / 'example.jsonl', 'shared-external-id', 'Synthetic work')
            entries.append(dict(source_key=key, display_label=key.title(), provider_kind='codex', root=str(folder)))
        self.write(entries, 1)
        scanner.scan_session_sources()
        with db.transaction() as connection:
            ids = [row[0] for row in connection.execute('SELECT id FROM sessions ORDER BY id')]
            connection.execute('INSERT INTO session_pins VALUES (?,?)', (ids[0], '2026-10-24T00:00:00Z'))
            set_project_visibility(connection, '2', None, ['/tmp/project'])
            from source_identity_fixtures import legacy_registry
            legacy_registry(connection, {1:'codex', 2:'custom-work'})
        self.write(entries, 1)
        return entries

    def evidence(self):
        with db.connect() as connection:
            return {name: [tuple(row) for row in connection.execute(sql)] for name, sql in {
                'sessions': 'SELECT id,source_id,external_id,source_path FROM sessions ORDER BY id',
                'events': 'SELECT id,session_id,sequence,event_type,source_line FROM activity_events ORDER BY id',
                'usage': 'SELECT id,source_id,session_id,total_tokens,estimated_cost_usd,project_key,project_name_snapshot FROM usage_records ORDER BY id',
                'pins': 'SELECT * FROM session_pins ORDER BY session_id',
            }.items()}

    def test_migrate_reorder_color_rename_and_reimport_preserve_history(self):
        self.legacy_fixture()
        before = self.evidence()
        self.assertEqual(len(before['sessions']), 2)
        self.assertGreater(len(before['events']), 0)
        self.assertGreater(len(before['usage']), 0)
        db.init_db()
        state = source_inventory(self.config)
        ids = [source['id'] for source in state['sources']]
        raw = tomllib.loads(self.path.read_text())
        self.assertEqual(raw['schema_version'], 2)
        self.assertEqual([entry['source_id'] for entry in raw['session_sources']], ids)
        self.assertNotIn('source_key', self.path.read_text())
        self.mutate(action='reorder', source_ids=ids[::-1])
        self.mutate(action='color', source_id=ids[1], color='blue')
        source = next(row for row in source_inventory(self.config)['sources'] if row['id'] == ids[1])
        self.mutate(source_id=source['id'], provider_kind='codex', display_label='Studio', root=source['root_path'])
        scanner.scan_session_sources(force=True)
        self.assertEqual(self.evidence(), before)
        with db.connect() as connection:
            scopes = session_source_scopes(connection)
            self.assertEqual([row['id'] for row in scopes], ids[::-1])
            self.assertEqual(scopes[0]['display_label'], 'Studio')
            self.assertEqual(scopes[0]['color'], 'blue')
            self.assertEqual(session_inventory_page(connection, str(ids[1]))['total'], 1)
            self.assertEqual(get_project_visibility(connection, str(ids[1]), None), ['/tmp/project'])
            self.assertEqual(normalize_usage_scope(connection, source='custom-work')['source'], 'all')
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_new_same_provider_profiles_use_pk_and_manual_order(self):
        self.register('Personal')
        state = self.register('Studio')
        ids = [row['id'] for row in state['sources']]
        self.assertEqual(len(set(ids)), 2)
        self.assertNotIn('kind', state['sources'][0])
        raw = tomllib.loads(self.path.read_text())
        raw['session_sources'].reverse()
        raw['session_sources'][0]['color'] = 'red'
        self.write(raw['session_sources'])
        state = source_inventory(self.config)
        self.assertEqual([row['id'] for row in state['sources']], ids[::-1])
        self.assertEqual(state['sources'][0]['color'], 'red')
        raw = tomllib.loads(self.path.read_text())
        del raw['session_sources'][0]['color']
        self.write(raw['session_sources'])
        self.assertEqual(source_inventory(self.config)['sources'][0]['color'], 'green')
        with db.connect() as connection:
            self.assertNotIn('kind', {row['name'] for row in connection.execute('PRAGMA table_info(sources)')})

    def test_bad_ids_colors_and_order_preserve_config(self):
        state = self.register('Personal')
        source_id = state['sources'][0]['id']
        before = self.path.read_bytes()
        for bad in (True, 0, -1, '1', 1.5, 2**53, []):
            with self.subTest(id=bad), self.assertRaises(PreferencesError):
                self.mutate(source_id=bad, action='color', color='blue')
        for bad in ('unknown', [], {}, None):
            with self.subTest(color=bad), self.assertRaises(PreferencesError):
                self.mutate(source_id=source_id, action='color', color=bad)
        for order in ([], [source_id,source_id], [999], [True], '1'):
            with self.subTest(order=order), self.assertRaises(PreferencesError):
                self.mutate(action='reorder', source_ids=order)
        with self.assertRaises(PreferencesError):
            self.mutate(action=[])
        self.assertEqual(self.path.read_bytes(), before)

    def test_file_write_failure_rolls_back_new_id_and_stale_revision(self):
        state = self.register('Personal')
        before = self.path.read_bytes()
        folder = self.root/'other';folder.mkdir()
        with patch('localbrain.source_settings.atomic_private_write', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                update_source(dict(revision=state['revision'], provider_kind='codex', display_label='Other', root=str(folder)), self.config)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(len(source_inventory(self.config)['sources']), 1)
        self.mutate(action='color', source_id=state['sources'][0]['id'], color='yellow')
        with self.assertRaises(PreferencesError):
            update_source(dict(revision=state['revision'], action='reorder', source_ids=[state['sources'][0]['id']]), self.config)

    def test_restored_id_reserved_and_disabled_identity_retained(self):
        folder = self.root/'restored';folder.mkdir()
        self.write([dict(source_id=42, provider_kind='codex', display_label='Restored', root=str(folder), color='orange')])
        state=self.register('New')
        self.assertEqual([row['id'] for row in state['sources']], [42,43])
        self.mutate(action='remove', source_id=42)
        state=self.mutate(action='reorder', source_ids=[43,42])
        self.assertFalse(state['sources'][1]['registered'])
        self.assertTrue(state['sources'][1]['configured'])
        self.assertEqual(state['sources'][1]['id'],42)

    def test_invalid_file_not_replaced_and_home_only_does_not_reconnect(self):
        state=self.register('Personal');source=state['sources'][0]
        state=self.mutate(source_id=source['id'], provider_kind='codex', display_label=source['name'],
                          root=source['root_path'], agent_home=str(self.root/'alternate-home'))
        self.assertEqual(state['sources'][0]['root_path'], source['root_path'])
        raw=tomllib.loads(self.path.read_text())
        raw['session_sources'].append(dict(raw['session_sources'][0]))
        self.write(raw['session_sources']);before=self.path.read_bytes()
        migrate_source_settings(self.config)
        self.assertTrue(load_session_source_settings(self.config).file_error)
        self.assertEqual(self.path.read_bytes(),before)

    def test_provider_scan_includes_each_numeric_profile(self):
        self.register('First')
        state = self.register('Second')
        for source in state['sources']:
            sync_fixtures.SessionSyncTests()._write_codex_session(Path(source['root_path'])/'session.jsonl', 'same-id', 'Synthetic')
        self.assertEqual(scanner.scan_codex_sessions()['imported'], 2)
        self.assertEqual(scanner.scan_claude_sessions()['imported'], 0)

    def test_reconnect_cannot_erase_a_newer_session_revision(self):
        from localbrain.ingest.contracts import CODEX_SESSION_REVISION
        state = self.register('Personal')
        source = state['sources'][0]
        native = Path(source['root_path']) / 'session.jsonl'
        sync_fixtures.SessionSyncTests()._write_codex_session(native, 'same-id', 'Keep history')
        scanner.scan_session_sources()
        with db.transaction() as connection:
            connection.execute('UPDATE source_files SET session_contract_version=?', (CODEX_SESSION_REVISION + 1,))
        before = self.evidence()
        config_before = self.path.read_bytes()
        new_root = self.root / 'relocated' / 'sessions'
        new_root.mkdir(parents=True)
        (new_root / native.name).write_bytes(native.read_bytes())
        with self.assertRaisesRegex(PreferencesError, 'newer Session parser'):
            self.mutate(action='reconnect', source_id=source['id'], provider_kind='codex',
                        display_label='Personal', root=str(new_root), confirm_same_source=True)
        self.assertEqual(self.evidence(), before)
        self.assertEqual(self.path.read_bytes(), config_before)
        self.assertFalse((self.data / 'source-reconnect.json').exists())
        with db.connect() as connection:
            self.assertEqual(connection.execute('SELECT session_contract_version FROM source_files').fetchone()[0], CODEX_SESSION_REVISION + 1)
            self.assertEqual(connection.execute('SELECT root_path FROM sources WHERE id=?', (source['id'],)).fetchone()[0], source['root_path'])

    def test_error_after_file_replacement_restores_both_stores(self):
        import localbrain.source_settings as module
        state=self.register('Personal');source_id=state['sources'][0]['id']
        before=self.path.read_bytes();real=module.atomic_private_write;calls=[]
        def interrupted(path,data):
            real(path,data);calls.append(1)
            if len(calls)==1: raise OSError('directory sync interrupted')
        with patch.object(module,'atomic_private_write',side_effect=interrupted), self.assertRaises(OSError):
            self.mutate(action='color',source_id=source_id,color='red')
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(source_inventory(self.config)['sources'][0]['color'],'green')

    def test_pk_is_the_only_identity_even_when_labels_look_like_ids(self):
        from localbrain.source_profiles import profile_map
        with db.transaction() as connection:
            connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','2','/synthetic/first'),(2,'codex','Second','/synthetic/second')")
            self.assertEqual(profile_map(connection)['2']['name'],'Second')
            self.assertEqual(profile_map(connection)['1']['name'],'2')
            self.assertEqual(set(profile_map(connection)), {'1','2'})

    def test_registry_upgrade_migrates_dependents_and_is_idempotent(self):
        from localbrain.source_identity_migration import _episode_key
        from localbrain.workflow_assertions import workflow_boundary_key
        from localbrain.workflow_projection import workflow_episode_key
        self.legacy_fixture()
        old_episode = _episode_key('codex', 'shared-external-id')
        with db.transaction() as connection:
            session_id = connection.execute('SELECT id FROM sessions WHERE source_id=1').fetchone()[0]
            connection.execute("""INSERT INTO skill_observations(id,source_key,provider_kind,
                external_session_id,native_event_id,skill_name,skill_group_key,signal_kind,source_line)
                VALUES ('retained-skill','codex','codex','shared-external-id','skill-event','Review','review','codex_skill_context',1)""")
            connection.execute("""INSERT INTO workflow_assertions(boundary_key,boundary_version,
                boundary_kind,assertion_kind,source_episode_key,source_session_id,
                before_meaning,after_meaning,after_closure_reason,created_at)
                VALUES (?,1,'lifecycle','close',?,?,'lifecycle:unknown','lifecycle:closed','completed','2026-10-24T00:00:00Z')""",
                (workflow_boundary_key('lifecycle',old_episode),old_episode,session_id))
            connection.execute("""INSERT INTO personal_insight_runs(id,mode,status,runner,model,settings_json,
                guide_version,evidence_version,evidence_path,prompt_path,response_path,report_path,
                stream_path,stderr_path,coverage_json,created_at,updated_at)
                VALUES ('analysis','discover','completed','codex','synthetic',?,'guide','evidence',
                '/synthetic/evidence','/synthetic/prompt','/synthetic/response','/synthetic/report',
                '/synthetic/stream','/synthetic/stderr','{}','2026-10-24','2026-10-24')""",
                (json.dumps({'usage_source_key':'custom-work','other_setting':True}),))
            connection.execute("UPDATE search_index SET source_kind='custom-work' WHERE entity_type='session' AND entity_id=?", (str(session_id),))
        db.init_db()
        with db.connect() as connection:
            self.assertEqual(connection.execute('SELECT id,source_id FROM skill_observations').fetchone()[:], ('retained-skill',1))
            assertion=dict(connection.execute('SELECT * FROM workflow_assertions').fetchone())
            new_episode=workflow_episode_key(1,'shared-external-id')
            self.assertEqual(assertion['source_episode_key'],new_episode)
            self.assertEqual(assertion['boundary_key'],workflow_boundary_key('lifecycle',new_episode))
            self.assertEqual(assertion['source_session_id'],session_id)
            self.assertEqual(assertion['boundary_version'],1)
            self.assertEqual(json.loads(connection.execute('SELECT settings_json FROM personal_insight_runs').fetchone()[0]),
                             {'usage_source_id':2,'other_setting':True})
            self.assertEqual(connection.execute('SELECT DISTINCT source_kind FROM search_index').fetchall()[0][0],'codex')
            self.assertFalse(connection.execute('PRAGMA foreign_key_check').fetchall())
            columns=[row['name'] for row in connection.execute('PRAGMA table_info(skill_observations)')]
            self.assertIn('source_id',columns); self.assertNotIn('source_key',columns)
            before={table:[tuple(row) for row in connection.execute('SELECT * FROM '+table+' ORDER BY rowid')]
                    for table in ('sources','skill_observations','workflow_assertions','personal_insight_runs','session_chart_preferences')}
        config_before=self.path.read_bytes()
        db.init_db()
        with db.connect() as connection:
            for table,rows in before.items():
                self.assertEqual([tuple(row) for row in connection.execute('SELECT * FROM '+table+' ORDER BY rowid')],rows)
        self.assertEqual(self.path.read_bytes(),config_before)

    def test_registry_upgrade_failure_restores_database_and_file(self):
        import localbrain.source_identity_migration as migration
        self.legacy_fixture()
        before=self.evidence(); file_before=self.path.read_bytes()
        health=self.data/'session-sync-state.json'
        health.write_text(json.dumps(dict(completed_at=100,report=dict(sources=[dict(source_key='codex')]))))
        health_before=health.read_bytes()
        original=migration._replace_table
        def fail_sources(connection,schema,table,rows):
            if table=='sources': raise RuntimeError('synthetic interrupted migration')
            original(connection,schema,table,rows)
        with patch.object(migration,'_replace_table',side_effect=fail_sources), self.assertRaises(RuntimeError):
            db.init_db()
        self.assertEqual(self.path.read_bytes(),file_before)
        self.assertEqual(health.read_bytes(),health_before)
        self.assertEqual(self.evidence(),before)
        with db.connect() as connection:
            self.assertIn('kind',{r['name'] for r in connection.execute('PRAGMA table_info(sources)')})
            self.assertIn('source_key',{r['name'] for r in connection.execute('PRAGMA table_info(skill_observations)')})
            self.assertFalse(connection.execute('PRAGMA foreign_key_check').fetchall())
        db.init_db()
        self.assertEqual(self.evidence(),before)

    def test_invalid_legacy_profile_preserves_both_stores(self):
        entries=self.legacy_fixture()
        entries[0]['provider_kind']=[]
        self.write(entries,1); before=self.path.read_bytes(); evidence=self.evidence()
        with self.assertRaises(PreferencesError): db.init_db()
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(self.evidence(),evidence)
        with db.connect() as connection:
            self.assertIn('kind',{r['name'] for r in connection.execute('PRAGMA table_info(sources)')})

    def test_unexpected_schema_column_is_preserved_on_failed_upgrade(self):
        self.legacy_fixture(); before=self.path.read_bytes()
        with db.transaction() as connection:
            connection.execute("ALTER TABLE sources ADD COLUMN future_state TEXT")
            connection.execute("UPDATE sources SET future_state='retained'")
        with self.assertRaisesRegex(RuntimeError,'unexpected columns'): db.init_db()
        self.assertEqual(self.path.read_bytes(),before)
        with db.connect() as connection:
            self.assertEqual(connection.execute('SELECT future_state FROM sources LIMIT 1').fetchone()[0],'retained')

    def test_legacy_reconnect_recovery_precedes_identity_upgrade(self):
        import base64,hashlib
        self.legacy_fixture()
        before=self.path.read_bytes(); changed=before.replace(b'Custom-Work',b'Renamed')
        self.path.write_bytes(changed)
        journal=self.data/'source-reconnect.json'
        journal.write_text(json.dumps(dict(source_key='codex',new_root='/synthetic/uncommitted',
            before=base64.b64encode(before).decode(),after_sha256=hashlib.sha256(changed).hexdigest())))
        db.init_db()
        self.assertFalse(journal.exists())
        self.assertEqual(tomllib.loads(self.path.read_text())['schema_version'],2)
        self.assertEqual(tomllib.loads(self.path.read_text())['session_sources'][1]['display_label'],'Custom-Work')

    def test_search_provider_comes_from_entity_not_old_alias_spelling(self):
        entries=self.legacy_fixture()
        with db.transaction() as connection:
            connection.execute("UPDATE sources SET provider_kind='claude' WHERE id=1")
            connection.execute("UPDATE sources SET kind='claude' WHERE id=2")
            connection.execute("UPDATE search_index SET source_kind='codex' WHERE entity_id=(SELECT CAST(id AS TEXT) FROM sessions WHERE source_id=1)")
            connection.execute("UPDATE search_index SET source_kind='claude' WHERE entity_id=(SELECT CAST(id AS TEXT) FROM sessions WHERE source_id=2)")
        entries[0]['provider_kind']='claude'; entries[1]['source_key']='claude';self.write(entries,1)
        db.init_db()
        with db.connect() as connection:
            rows=connection.execute("SELECT i.source_kind,p.provider_kind FROM search_index i JOIN sessions s ON CAST(s.id AS TEXT)=i.entity_id JOIN sources p ON p.id=s.source_id WHERE i.entity_type='session'").fetchall()
            self.assertEqual(len(rows),2)
            self.assertTrue(all(row[0]==row[1] for row in rows))

    def test_ambiguous_numeric_chart_alias_cannot_silently_reassign_scope(self):
        entries=self.legacy_fixture()
        with db.transaction() as connection:
            connection.execute("UPDATE sources SET kind='2' WHERE id=1")
            connection.execute("UPDATE session_chart_preferences SET source_scope='2'")
        entries[0]['source_key']='2'; self.write(entries,1); before=self.path.read_bytes()
        with self.assertRaisesRegex(RuntimeError,'conflicts with a numeric source ID'): db.init_db()
        self.assertEqual(self.path.read_bytes(),before)

    def test_cached_sync_health_uses_pk_and_preserves_schedule_and_counts(self):
        self.legacy_fixture()
        paths=[]
        for domain in ('session','context'):
            path=self.data/(domain+'-sync-state.json');paths.append(path)
            path.write_text(json.dumps(dict(completed_at=100,last_success_at=90,generation=8,
                report=dict(outcome='partial',sources=[dict(source_key='custom-work',display_label='Work',imported=7),dict(source_key='settings',status='configuration_error')]))))
        db.init_db()
        for path in paths:
            value=json.loads(path.read_text())
            self.assertEqual((value['completed_at'],value['last_success_at'],value['generation']),(100,90,8))
            self.assertEqual(value['report']['sources'],[dict(source_id=2,display_label='Work',imported=7),dict(source_id=None,status='configuration_error')])
            self.assertNotIn('source_key',path.read_text())
