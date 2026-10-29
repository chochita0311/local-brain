"""Batched known-metadata and bounded independent publication, synthetic only."""
import hashlib
import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from email import policy
from email.parser import BytesParser
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from unittest.mock import Mock, patch

import test_google_drive as fixtures
from localbrain.google_drive.api import API, BATCH
from localbrain.google_drive.auth import GcloudAuth
from localbrain.google_drive.policy import DriveError


def metadata(file_id, version='1'):
    return dict(id=file_id, name='demo', parents=['parent'], mimeType='application/octet-stream',
                md5Checksum=hashlib.md5(b'demo').hexdigest(), size='4', version=version)


def batch_response(rows):
    body = b''
    for content_id, status, value in rows:
        body += (f'--reply\r\nContent-Type: application/http\r\nContent-ID: <{content_id}>\r\n\r\n'
                 f'HTTP/1.1 {status} Result\r\nContent-Type: application/json\r\n\r\n').encode()
        body += json.dumps(value).encode() + b'\r\n'
    return fixtures.Response(body + b'--reply--\r\n', headers={'Content-Type': 'multipart/mixed; boundary=reply'})


class BatchTests(unittest.TestCase):
    def api(self, open_, **kwargs):
        return API(lambda: 'synthetic-token', opener=SimpleNamespace(open=open_), sleeper=lambda seconds: None, **kwargs)

    def test_one_hundred_metadata_reads_use_one_post_and_are_one_use(self):
        calls = []
        def open_(request, timeout):
            calls.append(request)
            if request.method == 'POST':
                return batch_response([(f'response-localbrain-{i}', 200, metadata('file-' + str(i))) for i in range(100)])
            return fixtures.Response(json.dumps(metadata('file-0', '2')).encode())
        api = self.api(open_)
        api.prefetch(['file-' + str(i) for i in range(100)])
        self.assertEqual([api.get('file-' + str(i))['id'] for i in range(100)], ['file-' + str(i) for i in range(100)])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].full_url, BATCH)
        self.assertEqual(calls[0].data.count(b'GET /drive/v3/files/'), 100)
        self.assertIn(b'supportsAllDrives=true', calls[0].data)
        self.assertEqual(api.get('file-0')['version'], '2')
        self.assertEqual(calls[-1].method, 'GET')

    def test_batches_are_bounded_deduplicated_and_correlated_by_content_id(self):
        calls = []; ids = ['file-' + str(i) for i in range(101)]
        def open_(request, timeout):
            calls.append(request)
            message = BytesParser(policy=policy.default).parsebytes(
                ('Content-Type: ' + request.get_header('Content-type') + '\r\n\r\n').encode() + request.data)
            rows = []
            for part in message.iter_parts():
                file_id = part.get_payload(decode=True).split(b'/files/')[1].split(b'?')[0].decode()
                rows.append(('response-' + str(part['Content-ID']).strip('<>'), 200, metadata(file_id)))
            return batch_response(list(reversed(rows)))
        api = self.api(open_); progress = []
        api.prefetch(ids + ids, progress=lambda completed, total: progress.append((completed, total)))
        self.assertEqual(len(calls), 2)
        self.assertEqual(progress, [(100, 101), (101, 101)])
        self.assertEqual(api.get('file-100')['id'], 'file-100')

    def test_item_permission_and_missing_errors_are_preserved_without_deletion_inference(self):
        api = self.api(lambda *a, **k: batch_response([
            ('response-localbrain-0', 404, {'error': {}}),
            ('response-localbrain-1', 403, {'error': {'errors': [{'reason': 'insufficientFilePermissions'}]}})]))
        api.prefetch(['missing', 'denied'])
        for key, expected in [('missing', 'unavailable'), ('denied', 'permission')]:
            with self.subTest(key=key), self.assertRaises(DriveError) as error:
                api.get(key)
            self.assertEqual(error.exception.code, expected)

    def test_transient_or_auth_parts_are_individually_revalidated(self):
        calls = []; refresh = Mock()
        def open_(request, timeout):
            calls.append(request)
            if request.method == 'POST':
                return batch_response([('response-localbrain-0', 401, {'error': {}}),
                                       ('response-localbrain-1', 429, {'error': {}})])
            file_id = request.full_url.split('/files/')[1].split('?')[0]
            return fixtures.Response(json.dumps(metadata(file_id)).encode())
        api = self.api(open_, refresh=refresh); api.prefetch(['one', 'two'])
        self.assertEqual(api.get('one')['id'], 'one'); self.assertEqual(api.get('two')['id'], 'two')
        self.assertEqual([request.method for request in calls], ['POST', 'GET', 'GET'])
        refresh.assert_called_once()

    def test_malformed_or_incomplete_parts_fall_back_to_fresh_reads(self):
        variants = [[], [('response-localbrain-0', 200, metadata('wrong'))],
                    [('unknown', 200, metadata('one'))],
                    [('response-localbrain-0', 200, metadata('one'))] * 2]
        for rows in variants:
            with self.subTest(rows=rows):
                calls = []
                def open_(request, timeout):
                    calls.append(request)
                    return batch_response(rows) if request.method == 'POST' else fixtures.Response(json.dumps(metadata('one')).encode())
                api = self.api(open_); api.prefetch(['one'])
                self.assertEqual(api.get('one')['id'], 'one')
                self.assertEqual([request.method for request in calls], ['POST', 'GET'])

    def test_unsupported_batch_endpoint_falls_back(self):
        calls = []
        def open_(request, timeout):
            calls.append(request)
            if request.method == 'POST':
                raise HTTPError(BATCH, 404, 'Unavailable', {}, None)
            return fixtures.Response(json.dumps(metadata('one')).encode())
        api = self.api(open_); api.prefetch(['one'])
        self.assertEqual(api.get('one')['id'], 'one')
        self.assertEqual(len(calls), 2)

    def test_resource_keys_apply_to_each_member_and_response_keys_are_retained(self):
        calls = []
        value = {**metadata('one'), 'resourceKey': 'new-key'}
        def open_(request, timeout):
            calls.append(request); return batch_response([('response-localbrain-0', 200, value)])
        api = self.api(open_, resource_keys={'root': 'root-key'}); api.keys['one'] = 'file-key'
        api.prefetch(['one'])
        self.assertIn(b'root/root-key', calls[0].data); self.assertIn(b'one/file-key', calls[0].data)
        self.assertEqual(api.get('one')['resourceKey'], 'new-key')
        self.assertEqual(api.keys['one'], 'new-key')

    def test_write_recovery_cannot_use_prefetched_success(self):
        content = b'demo'; calls = []
        def open_(request, timeout):
            calls.append(request)
            if request.method == 'POST':
                raise URLError('uncertain write')
            return fixtures.Response(json.dumps(metadata('one', 'fresh')).encode())
        api = self.api(open_); api.metadata_cache['one'] = metadata('one', 'stale')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot'; path.write_bytes(content)
            result = api.upload('one', 'demo', 'parent', path, hashlib.md5(content).hexdigest(), False, {}, lambda: None)
        self.assertEqual(result['version'], 'fresh')
        self.assertEqual([r.method for r in calls], ['POST', 'GET'])

    def test_cancellation_and_endpoint_boundaries(self):
        opener = Mock()
        api = self.api(opener, cancel=lambda: True)
        with self.assertRaises(DriveError): api.prefetch(['one'])
        opener.assert_not_called()
        api = self.api(opener)
        for method, url in [('PUT', BATCH), ('POST', 'https://outside.example/batch/drive/v3')]:
            with self.subTest(url=url), self.assertRaises(DriveError): api.request(method, url)
        opener.assert_not_called()


class PublisherParallelTests(fixtures.TempCase):
    def test_known_ids_from_stopped_sources_are_not_prefetched(self):
        other = self.root / 'other'; other.mkdir(); (other / 'a').write_bytes(b'other')
        (self.folder / 'a').write_bytes(b'demo')
        second = dict(id=2, path=str(other), label='Other', source_type='folder')
        self.engine.publish(self.connection, self.sources + [second], self.api)
        manifest = self.store.manifest(self.connection['id'], 'upload')
        wanted = {v['remote_id'] for v in manifest.values() if v['source_id'] == '1'}
        with patch.object(self.api, 'prefetch', wraps=self.api.prefetch) as prefetch:
            self.engine.publish(self.connection, self.sources, self.api)
        self.assertEqual(set(prefetch.call_args.args[0]), wanted)

    def test_independent_uploads_overlap_with_eight_workers_and_verified_checkpoints(self):
        for i in range(16): (self.folder / str(i)).write_bytes(('file-' + str(i)).encode())
        barrier = threading.Barrier(8); lock = threading.Lock(); active = peak = 0
        original = self.api.upload
        def upload(*args, **kwargs):
            nonlocal active, peak
            with lock: active += 1; peak = max(peak, active)
            try:
                barrier.wait(4)
                state, checkpoint = args[6], args[7]
                state['session'] = 'synthetic-' + args[0]; checkpoint()
                result = original(*args, **kwargs)
                state.pop('session'); checkpoint()
                return result
            finally:
                with lock: active -= 1
        with patch.object(self.api, 'upload', side_effect=upload):
            result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertEqual(peak, 8); self.assertEqual(active, 0)
        self.assertEqual(result['transferred'], 16); self.assertFalse(result['errors'])
        manifest = self.store.manifest(self.connection['id'], 'upload')
        self.assertTrue(all(v['complete'] and 'session' not in v for v in manifest.values()))
        for record in manifest.values():
            if record['kind'] == 'file':
                self.assertEqual(record['hash'], hashlib.md5(self.api.bodies[record['remote_id']]).hexdigest())

    def test_inaccessible_previously_complete_parent_blocks_children_and_deletion(self):
        (self.folder / 'old').write_bytes(b'keep')
        self.engine.publish(self.connection, self.sources, self.api)
        manifest = self.store.manifest(self.connection['id'], 'upload')
        old_id = manifest['1:vault/old']['remote_id']
        self.api.denied.add(manifest['1:vault']['remote_id'])
        (self.folder / 'old').unlink(); (self.folder / 'new').write_bytes(b'new')
        self.api.calls.clear()
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertTrue(result['errors'])
        self.assertFalse(self.api.files[old_id].get('trashed'))
        self.assertFalse(any(call[0] in ('upload', 'trash') for call in self.api.calls))

    def test_failed_folder_to_file_replacement_preserves_prior_descendants(self):
        directory = self.folder / 'replace'; directory.mkdir(); (directory / 'child').write_bytes(b'keep')
        self.engine.publish(self.connection, self.sources, self.api)
        old_id = self.store.manifest(self.connection['id'], 'upload')['1:vault/replace/child']['remote_id']
        shutil.rmtree(directory); directory.write_bytes(b'new')
        self.api.fail_upload = True
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertTrue(result['errors']); self.assertFalse(self.api.files[old_id].get('trashed'))

    def test_failed_renamed_parent_preserves_previous_copy(self):
        file = self.folder / 'a'; file.write_bytes(b'keep')
        self.engine.publish(self.connection, self.sources, self.api)
        old_id = self.store.manifest(self.connection['id'], 'upload')['1:vault/a']['remote_id']
        directory = self.folder / 'blocked'; directory.mkdir(); file.rename(directory / 'a')
        original = self.api.create_folder
        def create(key, name, parent):
            if name == 'blocked': raise DriveError('permission', 'Unavailable')
            return original(key, name, parent)
        with patch.object(self.api, 'create_folder', side_effect=create):
            result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertTrue(result['errors']); self.assertFalse(self.api.files[old_id].get('trashed'))

    def test_cancelled_workers_settle_before_any_deletion(self):
        old = self.folder / 'old'; old.write_bytes(b'keep')
        self.engine.publish(self.connection, self.sources, self.api)
        old_id = self.store.manifest(self.connection['id'], 'upload')['1:vault/old']['remote_id']
        old.unlink()
        for i in range(16): (self.folder / str(i)).write_bytes(b'new')
        barrier = threading.Barrier(8); cancelled = threading.Event(); active = 0; lock = threading.Lock()
        def upload(*args, **kwargs):
            nonlocal active
            with lock: active += 1
            try:
                barrier.wait(4); cancelled.set(); self.api.check()
            finally:
                with lock: active -= 1
        self.api.cancel = cancelled.is_set
        with patch.object(self.api, 'upload', side_effect=upload), self.assertRaises(DriveError) as error:
            self.engine.publish(self.connection, self.sources, self.api)
        self.assertEqual(error.exception.code, 'cancelled'); self.assertEqual(active, 0)
        self.assertFalse(self.api.files[old_id].get('trashed'))
        self.assertFalse(list(self.engine.stage.glob('snapshot-*')))


class TokenSingleFlightTests(unittest.TestCase):
    def test_parallel_workers_share_one_sdk_token_refresh(self):
        entered, release = threading.Event(), threading.Event(); calls = []
        def run(argv, env, timeout):
            calls.append(argv); entered.set()
            if not release.wait(4): raise AssertionError('token test not released')
            return subprocess.CompletedProcess(argv, 0, 'synthetic-parallel-token', '')
        auth = GcloudAuth(lambda cid: 'account-one', lambda *a: None, lambda *a: None, runner=run)
        try:
            with patch('localbrain.google_drive.auth.gcloud_path', return_value='/sdk/gcloud'), ThreadPoolExecutor(max_workers=8) as pool:
                futures = [pool.submit(auth.access_token, 'connection') for _ in range(8)]
                self.assertTrue(entered.wait(3)); self.assertEqual(len(calls), 1)
                release.set()
                self.assertEqual([f.result(4) for f in futures], ['synthetic-parallel-token'] * 8)
        finally:
            release.set(); auth.stop()
        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
