"""Synthetic missing-copy recovery and unchanged-work contracts."""

import copy
import hashlib
import os
import unittest
from unittest.mock import patch

import test_google_drive as fixtures
from localbrain.google_drive.api import API
from localbrain.google_drive.engine import Engine
from localbrain.google_drive.policy import DriveError, FOLDER, stamp
from localbrain.google_drive.store import Store


class Remote(fixtures.FakeAPI):
    def __init__(self):
        super().__init__()
        self.cache = {}

    def fresh(self, key):
        value = super().get(key)
        if value['mimeType'] == FOLDER:
            value.setdefault('capabilities', dict(canListChildren=True, canAddChildren=True))
        ancestors = list(value.get('parents', []))
        while ancestors:
            parent = self.files.get(ancestors.pop(), {})
            if parent.get('trashed'):
                value['trashed'] = True
                break
            ancestors.extend(parent.get('parents', []))
        return value

    def get(self, key):
        self.check()
        if key in self.cache:
            value = self.cache.pop(key)
            if isinstance(value, DriveError):
                raise value
            return copy.deepcopy(value)
        return self.fresh(key)

    def prefetch(self, keys, progress=lambda checked, total: None):
        self.cache.clear()
        for key in keys:
            try:
                self.cache[key] = self.fresh(key)
            except DriveError as error:
                self.cache[key] = error
        progress(len(self.cache), len(self.cache))

    def invalidate(self, keys):
        for key in keys:
            self.cache.pop(key, None)

    def metadata(self, key, *args):
        self.invalidate([key])
        return super().metadata(key, *args)

    def remove_tree(self, key):
        for child in list(self.files.values()):
            if key in child.get('parents', []):
                self.remove_tree(child['id'])
        self.files.pop(key)
        self.bodies.pop(key, None)


class RecoveryTests(fixtures.TempCase):
    def setUp(self):
        super().setUp()
        self.api = Remote()
        (self.folder / 'nested').mkdir()
        (self.folder / 'nested' / 'a.bin').write_bytes(b'original')
        self.engine.publish(self.connection, self.sources, self.api)
        self.before = self.manifest()
        self.api.calls.clear()

    def manifest(self):
        return self.store.manifest(self.connection['id'], 'upload')

    def test_missing_source_folder_rebuilds_the_local_tree_with_new_ids(self):
        self.api.remove_tree(self.before['1:vault']['remote_id'])
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual((result['transferred'], result['changed']), (1, 2))
        after = self.manifest()
        for key, prior in self.before.items():
            self.assertNotEqual(after[key]['remote_id'], prior['remote_id'])
            self.assertTrue(after[key]['complete'])
        self.assertEqual(self.api.bodies[after['1:vault/nested/a.bin']['remote_id']], b'original')
        self.assertFalse(any(call[0] == 'trash' for call in self.api.calls))
        self.assertEqual((self.folder / 'nested' / 'a.bin').read_bytes(), b'original')

    def test_missing_nested_folder_preserves_its_existing_parent_identity(self):
        self.api.remove_tree(self.before['1:vault/nested']['remote_id'])
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual(self.manifest()['1:vault']['remote_id'], self.before['1:vault']['remote_id'])
        self.assertEqual(result['transferred'], 1)

    def test_missing_file_is_recreated_with_a_new_checkpointed_identity(self):
        old = self.before['1:vault/nested/a.bin']['remote_id']
        self.api.remove_tree(old)
        upload = self.api.upload
        def checked_upload(key, *args, **kwargs):
            pending = self.manifest()['1:vault/nested/a.bin']
            self.assertEqual(pending['remote_id'], key)
            self.assertFalse(pending['complete'])
            self.assertNotEqual(key, old)
            self.assertNotIn('session', pending)
            return upload(key, *args, **kwargs)
        with patch.object(self.api, 'upload', side_effect=checked_upload):
            result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual(result['transferred'], 1)

    def test_missing_copy_requires_explicit_parent_list_and_create_capabilities(self):
        for capabilities in ({}, {'canAddChildren': True}, {'canListChildren': True},
                             {'canAddChildren': False, 'canListChildren': True}):
            with self.subTest(capabilities=capabilities):
                self.api.files[self.connection['target_id']]['capabilities'] = capabilities
                self.api.denied.add(self.before['1:vault']['remote_id'])
                result = self.engine.publish(self.connection, self.sources, self.api)
                self.assertTrue(result['errors'])
                self.assertEqual(self.manifest(), self.before)
                self.assertFalse(self.api.calls)

    def test_incomplete_parent_listing_preserves_old_mapping_and_copies(self):
        self.api.denied.add(self.before['1:vault']['remote_id'])
        self.api.fail_listing = True
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertTrue(result['errors'])
        self.assertEqual(self.manifest(), self.before)
        self.assertFalse(self.api.calls)

    def test_same_name_or_same_id_listing_prevents_blind_replacement(self):
        old = self.before['1:vault']['remote_id']
        self.api.denied.add(old)
        children = self.api.children
        for conflict in ({'id': 'another-id', 'name': 'VAULT'}, {'id': old, 'name': 'other-name'}):
            with self.subTest(conflict=conflict), patch.object(self.api, 'children', side_effect=lambda parent: [conflict] if parent == self.connection['target_id'] else children(parent)):
                result = self.engine.publish(self.connection, self.sources, self.api)
                self.assertTrue(result['errors'])
                self.assertEqual(self.manifest(), self.before)
                self.assertFalse(self.api.calls)

    def test_permission_network_and_auth_errors_never_allocate_replacements(self):
        original = self.api.get
        for code in ('permission', 'network', 'reauth'):
            def get(key):
                if key == self.before['1:vault']['remote_id']:
                    raise DriveError(code, 'Synthetic failure')
                return original(key)
            with self.subTest(code=code), patch.object(self.api, 'get', side_effect=get):
                result = self.engine.publish(self.connection, self.sources, self.api)
                self.assertTrue(result['errors'])
                self.assertEqual(self.manifest(), self.before)
                self.assertFalse(self.api.calls)

    def test_failed_recreation_reuses_its_durable_new_id_after_restart(self):
        self.api.remove_tree(self.before['1:vault']['remote_id'])
        create = self.api.create_folder
        allocated = []
        def fail(key, name, parent):
            if name == 'vault':
                pending = self.manifest()['1:vault']
                self.assertEqual(pending['remote_id'], key)
                self.assertFalse(pending['complete'])
                allocated.append(key)
                raise DriveError('network', 'Synthetic interruption', True)
            return create(key, name, parent)
        with patch.object(self.api, 'create_folder', side_effect=fail):
            self.assertTrue(self.engine.publish(self.connection, self.sources, self.api)['errors'])
        pending_id = self.manifest()['1:vault']['remote_id']
        self.assertEqual(allocated, [pending_id])
        self.engine = Engine(Store(self.data), self.data)
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual(self.manifest()['1:vault']['remote_id'], pending_id)
        self.assertNotEqual(pending_id, self.before['1:vault']['remote_id'])

    def test_recovered_pending_parent_is_not_assumed_empty(self):
        parent = self.before['1:vault/nested']['remote_id']
        old_file = self.before['1:vault/nested/a.bin']['remote_id']
        pending = self.manifest()
        pending['1:vault/nested'] = {**pending['1:vault/nested'], 'complete': False}
        self.store.checkpoint(self.connection['id'], 'upload', pending)
        self.api.remove_tree(old_file)
        self.api.body('unmanaged', 'a.bin', parent, b'keep foreign copy')
        original_get, original_create = self.api.get, self.api.create_folder
        def get(key):
            if key == parent:
                self.api.invalidate([parent])
                raise DriveError('unavailable', 'Synthetic uncertain previous create')
            return original_get(key)
        def recovered_create(key, name, ancestor):
            return self.api.fresh(parent) if key == parent else original_create(key, name, ancestor)
        with patch.object(self.api, 'get', side_effect=get), \
             patch.object(self.api, 'create_folder', side_effect=recovered_create):
            result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertTrue(result['errors'])
        self.assertEqual(self.manifest()['1:vault/nested/a.bin']['remote_id'], old_file)
        self.assertEqual(self.api.bodies['unmanaged'], b'keep foreign copy')
        self.assertFalse(any(call[0] in ('upload', 'trash') for call in self.api.calls))

    def test_trashed_folder_restores_same_ids_and_discards_descendant_snapshots(self):
        folder_id = self.before['1:vault']['remote_id']
        self.api.files[folder_id]['trashed'] = True
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual((result['transferred'], result['changed']), (0, 1))
        self.assertEqual({k: v['remote_id'] for k, v in self.manifest().items()},
                         {k: v['remote_id'] for k, v in self.before.items()})
        self.assertEqual(self.api.calls, [('metadata', folder_id)])

    def test_noop_repeat_hashes_without_staging_or_checkpoint_writes(self):
        with patch('localbrain.google_drive.engine.tempfile.mkstemp', side_effect=AssertionError('unchanged copy staged')), \
             patch.object(self.store, 'checkpoint', wraps=self.store.checkpoint) as checkpoint, \
             patch.object(self.engine, 'snapshot', wraps=self.engine.snapshot) as source:
            result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual((result['transferred'], result['changed']), (0, 0))
        checkpoint.assert_not_called()
        self.assertEqual(source.call_count, 1)
        self.assertEqual(source.call_args.kwargs, {'stage': False})
        self.assertEqual(self.manifest(), self.before)

    def test_same_size_change_with_restored_mtime_still_uploads_by_content(self):
        path = self.folder / 'nested' / 'a.bin'
        info = path.stat()
        path.write_bytes(b'modified')
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual(result['transferred'], 1)
        remote = self.manifest()['1:vault/nested/a.bin']['remote_id']
        self.assertEqual(self.api.bodies[remote], b'modified')
        self.assertEqual(self.manifest()['1:vault/nested/a.bin']['hash'], hashlib.md5(b'modified').hexdigest())

    def test_hash_only_source_change_is_rejected_without_remote_write(self):
        path = self.folder / 'nested' / 'a.bin'
        calls = 0
        def changed(info):
            nonlocal calls
            calls += 1
            value = stamp(info)
            if calls == 1:
                path.write_bytes(b'changed during comparison')
            return value
        with patch('localbrain.google_drive.engine.stamp', side_effect=changed):
            result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertTrue(result['errors'])
        self.assertFalse(self.api.calls)
        self.assertEqual(self.manifest(), self.before)


class CacheInvalidationTests(unittest.TestCase):
    def test_descendant_invalidation_preserves_unrelated_cached_results(self):
        api = API(lambda: 'synthetic', opener=object())
        api.metadata_cache.update(child={'id': 'child'}, peer={'id': 'peer'})
        api.invalidate(['child'])
        self.assertNotIn('child', api.metadata_cache)
        self.assertEqual(api.get('peer'), {'id': 'peer'})


if __name__ == '__main__':
    unittest.main()
