"""Synthetic source admission and read-only context tools."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from localbrain.context_search.tools import FileTools, ToolError, public_sources, source_catalog, tool_schemas


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='context-tools-')
        self.root = Path(self.tmp.name).resolve()
        self.vault = self.root / 'vault'; self.vault.mkdir()
        (self.vault / 'guide.md').write_text('Airflow controls daily sample jobs.\nOwner: Demo operator.\n', encoding='utf8')
        (self.vault / 'hidden.txt').write_text('Other material')
        self.sources = [dict(id='own', name='Demo vault', kind='local', mode='files', root=str(self.vault))]
        self.tools = FileTools(self.sources)

    def tearDown(self):
        self.tmp.cleanup()

    def test_list_search_read_and_real_evidence_without_index(self):
        self.assertEqual(len(self.tools.call('list_files', {'source': 'own'})['files']), 2)
        result = self.tools.call('search_text', {'query': 'airflow'})
        self.assertEqual(result['scanned'], 2)
        self.assertEqual(result['matches'][0]['path'], 'guide.md')
        read = self.tools.call('read_file', dict(source='own', path='guide.md', start_line=2, end_line=2))
        self.assertIn('Demo operator', read['text'])
        self.assertNotEqual(read['ref'], result['matches'][0]['ref'])
        self.assertEqual(len(self.tools.evidence), 2)

    def test_unknown_source_and_write_tools_are_refused(self):
        for name, args in [('delete_file', {}), ('search_text', {'source': 'outside', 'query': 'x'}),
                           ('read_file', {'source': [], 'path': 'guide.md'}), ('list_sources', {'extra': 1})]:
            with self.subTest(name=name), self.assertRaises(ToolError):
                self.tools.call(name, args)
        self.assertTrue((self.vault / 'guide.md').exists())

    def test_escape_absolute_and_symlink_paths_are_refused(self):
        external = self.root / 'outside'; external.write_text('private outside')
        (self.vault / 'link').symlink_to(external)
        for value in ('../outside', str(external), 'link'):
            with self.subTest(value=value), self.assertRaises(ToolError):
                self.tools.call('read_file', {'source': 'own', 'path': value})
        self.assertNotIn('link', [v['path'] for v in self.tools.call('list_files', {'source': 'own'})['files']])

    def test_binary_and_incomplete_receive_staging_do_not_become_text(self):
        (self.vault / 'sample.bin').write_bytes(b'\x00binary')
        (self.vault / '.localbrain-drive-incomplete').write_text('not committed')
        result = self.tools.call('search_text', {'query': 'not committed'})
        self.assertFalse(result['matches'])
        self.assertEqual(result['unreadable'], 1)
        with self.assertRaises(ToolError):
            self.tools.call('read_file', {'source': 'own', 'path': 'sample.bin'})

    def test_declared_app_and_hub_subtrees_remain_excluded(self):
        runtime = self.vault / 'runtime'; runtime.mkdir(); (runtime / 'secret.txt').write_text('not corpus')
        self.sources[0]['excluded'] = [str(runtime)]
        self.tools = FileTools(self.sources)
        self.assertEqual(len(self.tools.call('list_files', {'source': 'own'})['files']), 2)
        with self.assertRaises(ToolError):
            self.tools.call('read_file', {'source': 'own', 'path': 'runtime/secret.txt'})

    def test_public_source_description_does_not_expose_private_root(self):
        description = json.dumps(public_sources(self.sources))
        self.assertNotIn(str(self.vault), description)
        self.assertIn('Demo vault', description)

    def test_result_and_read_bounds_are_explicit(self):
        (self.vault / 'long.md').write_text('x' * 2_100_000)
        result = self.tools.call('read_file', dict(source='own', path='long.md'))
        self.assertTrue(result['limited'])
        self.assertLessEqual(len(result['text']), 10000)
        with self.assertRaises(ToolError):
            self.tools.call('read_file', dict(source='own', path='guide.md', start_line=1, end_line=1000))
        self.assertEqual(len(tool_schemas()), 4)

    def test_catalog_admits_only_enabled_own_roots_and_saved_received_copies(self):
        data = self.root / 'data'; data.mkdir()
        dbpath = data / 'catalog.db'
        with sqlite3.connect(dbpath) as db:
            db.execute('CREATE TABLE context_roots(id INTEGER,path TEXT,label TEXT,source_type TEXT,enabled INTEGER,readable INTEGER)')
            db.execute('CREATE TABLE context_documents(id INTEGER,context_root_id INTEGER,title TEXT,body TEXT,mtime_ns INTEGER)')
            db.execute('INSERT INTO context_documents VALUES(1,4,?,?,1)', ('Demo note', 'Airflow note body'))
            db.executemany('INSERT INTO context_roots VALUES(?,?,?,?,?,?)', [
                (1, str(self.vault), 'Demo vault', 'folder', 1, 1),
                (2, str(data), 'App state', 'folder', 1, 1),
                (3, str(self.vault / 'hidden.txt'), 'Disabled', 'file', 0, 1),
                (4, 'notes', 'Demo notes', 'apple_notes', 1, 1)])
        received = data / 'external-sources/google-drive/connection-a/publisher-a'
        received.mkdir(parents=True); (received / 'copy.md').write_text('received sample')
        class Store:
            def connections(self): return [{'id': 'connection-a'}]
            def get(self, key, default): return [{'id': 'publisher-a', 'name': 'Shared demo'}]
            def jobs(self, key): return {'receive:publisher-a': {'selected': False, 'last_success': '2026-01-01'},
                                       'receive:../outside': {'selected': True}}
        config = SimpleNamespace(data_dir=data, database_path=dbpath, cache_dir=self.root / 'cache')
        sources = source_catalog(config, Store())
        self.assertEqual([s['name'] for s in sources], ['Demo vault', 'Demo notes', 'Shared demo'])
        self.assertFalse(sources[-1]['syncing'])
        self.assertEqual(FileTools(sources).call('search_text', {'query': 'received', 'source': sources[-1]['id']})['matches'][0]['path'], 'copy.md')
        tools=FileTools(sources)
        self.assertEqual(tools.call('read_file',dict(source='context-4',path='document-1'))['text'],'Airflow note body')
        with sqlite3.connect(dbpath) as db:
            db.execute('UPDATE context_roots SET enabled=0 WHERE id=4')
        with self.assertRaises(ToolError): tools.call('read_file',dict(source='context-4',path='document-1'))

    def test_selected_file_cannot_expand_into_a_replacement_folder(self):
        selected=self.vault/'selected.txt';selected.write_text('original')
        tools=FileTools([dict(id='file',name='Demo file',mode='files',root=str(selected),single_file=True)])
        selected.unlink();selected.mkdir();(selected/'extra.md').write_text('new scope')
        with self.assertRaises(ToolError): tools.call('list_files',{'source':'file'})

    def test_changed_ancestor_link_and_staging_direct_reads_are_refused(self):
        parent=self.root/'publisher';nested=parent/'vault';nested.mkdir(parents=True)
        (nested/'sample.md').write_text('allowed')
        tools=FileTools([dict(id='received',name='Demo copy',mode='files',root=str(nested),single_file=False)])
        parent.rename(self.root/'old-publisher');parent.symlink_to(self.root/'old-publisher',target_is_directory=True)
        with self.assertRaises(ToolError): tools.call('read_file',dict(source='received',path='sample.md'))
        (self.vault/'.localbrain-drive-incomplete').write_text('incomplete')
        with self.assertRaises(ToolError):self.tools.call('read_file',dict(source='own',path='.localbrain-drive-incomplete'))
        with self.assertRaises(ToolError):self.tools.call('search_text',dict(source=[],query='x'))

    def test_unreadable_source_does_not_hide_other_sources_or_claim_complete_search(self):
        gone=self.root/'gone';gone.mkdir()
        tools=FileTools([dict(id='gone',name='Demo unavailable',mode='files',root=str(gone)),*self.sources])
        gone.rmdir()
        result=tools.call('search_text',dict(query='Airflow'))
        self.assertTrue(result['limited'])
        self.assertEqual(result['unreadable'],1)
        self.assertEqual(result['matches'][0]['source_id'],'own')
        def walk(root,*,followlinks,onerror):
            onerror(PermissionError('synthetic unreadable child'))
            return iter([])
        with patch('localbrain.context_search.tools.os.walk',side_effect=walk):
            self.assertTrue(self.tools.call('list_files',dict(source='own'))['limited'])


if __name__ == '__main__':
    unittest.main()
