"""Small-file throughput, resumable recovery and truthful progress; synthetic only."""
import copy
import hashlib
import json
import tempfile
import threading
import unittest
from email import policy
from email.parser import BytesParser
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

import test_google_drive as fixtures
from localbrain.google_drive.api import API
from localbrain.google_drive.policy import DriveError

SESSION = 'https://www.googleapis.com/upload/drive/v3/files?upload_id=synthetic'


class UploadTransportTests(unittest.TestCase):
    def upload(self, content, replies, state=None, force_resumable=False, existing=False):
        calls, progress, checkpoints = [], [], []
        digest = hashlib.md5(content).hexdigest()
        def open_(request, timeout):
            calls.append(request)
            result = replies.pop(0)
            if isinstance(result, Exception):
                raise result
            return result
        api = API(lambda: 'synthetic-token', opener=SimpleNamespace(open=open_), sleeper=lambda delay: None)
        state = {} if state is None else state
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot'
            path.write_bytes(content)
            with patch('localbrain.google_drive.api.MULTIPART_BYTES', 0 if force_resumable else 5_000_000):
                result = api.upload('assigned-id', 'demo.bin', 'parent', path, digest, existing, state,
                                    lambda: checkpoints.append(copy.deepcopy(state)),
                                    progress=lambda sent, size: progress.append((sent, size)))
        return result, calls, progress, checkpoints

    @staticmethod
    def metadata(content):
        return dict(id='assigned-id', name='demo.bin', parents=['parent'], size=str(len(content)),
                    md5Checksum=hashlib.md5(content).hexdigest(), version='1')

    def test_generated_ids_are_batched_and_unique(self):
        calls = []
        def open_(request, timeout):
            calls.append(request)
            return fixtures.Response(json.dumps({'ids': ['generated-' + str(i) for i in range(100)]}).encode())
        api = API(lambda: 'synthetic-token', opener=SimpleNamespace(open=open_))
        self.assertEqual(len({api.new_id() for _ in range(100)}), 100)
        self.assertEqual(len(calls), 1)
        self.assertEqual(parse_qs(urlsplit(calls[0].full_url).query)['count'], ['100'])

    def test_small_binary_metadata_and_content_use_one_request(self):
        content = b'\x00\xffliteral\r\nbytes'
        result, calls, progress, checkpoints = self.upload(content, [fixtures.Response(json.dumps(self.metadata(content)).encode())])
        self.assertEqual(result['id'], 'assigned-id')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].method, 'POST')
        self.assertEqual(parse_qs(urlsplit(calls[0].full_url).query)['uploadType'], ['multipart'])
        message = BytesParser(policy=policy.default).parsebytes(
            ('Content-Type: ' + calls[0].get_header('Content-type') + '\r\n\r\n').encode() + calls[0].data)
        parts = list(message.iter_parts())
        self.assertEqual(json.loads(parts[0].get_payload(decode=True)), {'id': 'assigned-id', 'name': 'demo.bin', 'parents': ['parent']})
        self.assertEqual(parts[1].get_payload(decode=True), content)
        self.assertEqual(progress, [(len(content), len(content))])
        self.assertEqual(checkpoints, [{}])

    def test_empty_file_finishes_without_resumable_loop(self):
        _, calls, progress, _ = self.upload(b'', [fixtures.Response(json.dumps(self.metadata(b'')).encode())])
        self.assertEqual(len(calls), 1)
        self.assertEqual(progress, [(0, 0)])

    def test_multipart_preserves_dynamically_discovered_parent_resource_key(self):
        content = b'demo'; calls = []
        def open_(request, timeout):
            calls.append(request)
            return fixtures.Response(json.dumps(self.metadata(content)).encode())
        api = API(lambda: 'synthetic-token', {'root': 'root-key'}, opener=SimpleNamespace(open=open_))
        api.keys.update(parent='parent-key')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot'; path.write_bytes(content)
            api.upload('assigned-id', 'demo.bin', 'parent', path, hashlib.md5(content).hexdigest(), False, {}, lambda: None)
        self.assertIn('parent/parent-key', calls[0].get_header('X-goog-drive-resource-keys'))
        self.assertIn('root/root-key', calls[0].get_header('X-goog-drive-resource-keys'))

    def test_small_update_uses_same_id_and_does_not_reassign_parent(self):
        content = b'updated'
        _, calls, _, _ = self.upload(content, [fixtures.Response(json.dumps(self.metadata(content)).encode())], existing=True)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].method, 'PATCH')
        self.assertTrue(urlsplit(calls[0].full_url).path.endswith('/assigned-id'))
        message = BytesParser(policy=policy.default).parsebytes(
            ('Content-Type: ' + calls[0].get_header('Content-type') + '\r\n\r\n').encode() + calls[0].data)
        self.assertEqual(json.loads(next(message.iter_parts()).get_payload(decode=True)), {'name': 'demo.bin'})

    def test_default_multipart_boundary_is_inclusive_and_larger_files_resume(self):
        for size in (5_000_000, 5_000_001):
            with self.subTest(size=size):
                content = b'x' * size
                if size == 5_000_000:
                    replies = [fixtures.Response(json.dumps(self.metadata(content)).encode())]
                else:
                    replies = [fixtures.Response(headers={'Location': SESSION})]
                    replies += [HTTPError(SESSION, 308, 'Resume', {'Range': f'bytes=0-{offset - 1}'}, None)
                                for offset in range(1024 * 1024, size, 1024 * 1024)]
                    replies.append(fixtures.Response(json.dumps(self.metadata(content)).encode()))
                _, calls, _, _ = self.upload(content, replies)
                self.assertEqual(parse_qs(urlsplit(calls[0].full_url).query)['uploadType'],
                                 ['multipart' if size == 5_000_000 else 'resumable'])

    def test_lost_small_create_response_verifies_same_id_without_second_create(self):
        content = b'committed'
        _, calls, _, _ = self.upload(content, [URLError('lost response'), fixtures.Response(json.dumps(self.metadata(content)).encode())])
        self.assertEqual([request.method for request in calls], ['POST', 'GET'])
        self.assertTrue(urlsplit(calls[-1].full_url).path.endswith('/assigned-id'))

    def test_wrong_hash_never_reports_success(self):
        wrong = self.metadata(b'wrong')
        with self.assertRaises(DriveError) as error:
            self.upload(b'expected', [fixtures.Response(json.dumps(wrong).encode()), fixtures.Response(json.dumps(wrong).encode())])
        self.assertEqual(error.exception.code, 'integrity')

    def test_existing_small_session_is_resumed_instead_of_recreated(self):
        content = b'abc'
        state = dict(session=SESSION, upload_hash=hashlib.md5(content).hexdigest())
        _, calls, progress, _ = self.upload(content, [
            HTTPError(SESSION, 308, 'Resume', {'Range': 'bytes=0-1'}, None),
            fixtures.Response(json.dumps(self.metadata(content)).encode())], state=state)
        self.assertEqual([r.method for r in calls], ['PUT', 'PUT'])
        self.assertEqual(calls[0].get_header('Content-range'), 'bytes */3')
        self.assertEqual(calls[1].data, b'c')
        self.assertEqual(progress, [(2, 3), (3, 3)])
        self.assertNotIn('session', state)

    def test_acknowledged_chunks_advance_without_extra_status_probes(self):
        content = b'x' * (1024 * 1024 + 3)
        _, calls, progress, _ = self.upload(content, [
            fixtures.Response(headers={'Location': SESSION}),
            HTTPError(SESSION, 308, 'Resume', {'Range': 'bytes=0-1048575'}, None),
            fixtures.Response(json.dumps(self.metadata(content)).encode())], force_resumable=True)
        self.assertEqual([r.method for r in calls], ['POST', 'PUT', 'PUT'])
        self.assertEqual(calls[-1].data, b'xxx')
        self.assertEqual(progress, [(1024 * 1024, len(content)), (len(content), len(content))])

    def test_resumable_no_progress_is_bounded_and_session_is_retained(self):
        state = {}
        replies = [fixtures.Response(headers={'Location': SESSION})] + [fixtures.Response(code=308) for _ in range(5)]
        with self.assertRaises(DriveError) as error:
            self.upload(b'abc', replies, state=state, force_resumable=True)
        self.assertEqual(error.exception.code, 'upload_stalled')
        self.assertEqual(state['session'], SESSION)
        self.assertFalse(replies)

    def test_expired_session_is_cleared_without_blind_create(self):
        content = b'abc'; state = dict(session=SESSION, upload_hash=hashlib.md5(content).hexdigest())
        with self.assertRaises(DriveError) as error:
            self.upload(content, [HTTPError(SESSION, 410, 'Expired', {}, None)], state=state)
        self.assertEqual(error.exception.code, 'upload_expired')
        self.assertNotIn('session', state)

    def test_resumable_missing_metadata_is_verified_by_assigned_id(self):
        content = b'abc'
        _, calls, _, _ = self.upload(content, [fixtures.Response(headers={'Location': SESSION}),
                                              fixtures.Response(),
                                              fixtures.Response(json.dumps(self.metadata(content)).encode())], force_resumable=True)
        self.assertEqual([r.method for r in calls], ['POST', 'PUT', 'GET'])
        self.assertTrue(urlsplit(calls[-1].full_url).path.endswith('/assigned-id'))


class UploadProgressTests(fixtures.TempCase):
    def test_fresh_ids_skip_existence_get_but_pending_recovery_checks(self):
        (self.folder / 'a').write_bytes(b'demo')
        missing = []; original = self.api.get
        def get(key):
            if key not in self.api.files:
                missing.append(key)
            return original(key)
        self.api.fail_upload = True
        with patch.object(self.api, 'get', side_effect=get):
            result = self.engine.publish(self.connection, self.sources, self.api)
            self.assertTrue(result['errors'])
            self.assertFalse(missing)
            self.api.fail_upload = False
            result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual(len(missing), 1)

    def test_processed_items_and_new_transfers_are_distinct(self):
        (self.folder / 'a').write_bytes(b'unchanged')
        self.engine.publish(self.connection, self.sources, self.api)
        (self.folder / 'b').write_bytes(b'new')
        values = {}; events = []
        def progress(**changes):
            values.update(changes); events.append(dict(values))
        result = self.engine.publish(self.connection, self.sources, self.api, progress=progress)
        self.assertEqual(events[0]['stage'], 'scanning')
        self.assertEqual(events[-1]['processed'], 3)
        self.assertEqual(events[-1]['total'], 3)
        self.assertEqual(events[-1]['transferred'], 1)
        self.assertEqual(result['transferred'], 1)

    def test_running_progress_is_cache_only_and_never_last_success(self):
        (self.folder / 'a').write_bytes(b'demo')
        service = fixtures.ServiceTests.service(self)
        cid = self.connection['id']; service.configure(cid, 'upload', {'sources': [1]})
        entered, release = threading.Event(), threading.Event(); original = self.api.upload
        def upload(*args, **kwargs):
            entered.set()
            if not release.wait(4):
                raise AssertionError('test upload not released')
            return original(*args, **kwargs)
        try:
            with patch.object(self.api, 'upload', side_effect=upload):
                service.run(cid, 'upload')
                self.assertTrue(entered.wait(3))
                one = service.status(); two = service.status()
                self.assertEqual(one['active']['progress'], two['active']['progress'])
                self.assertEqual(one['active']['progress']['processed'], 1)
                self.assertEqual(one['active']['progress']['total'], 2)
                self.assertFalse(one['connections'][0]['jobs']['upload'].get('last_success'))
                self.assertNotIn('progress', service.store.jobs(cid)['upload'])
                release.set(); service.worker.join(4)
        finally:
            release.set()
            if service.worker:
                service.worker.join(4)
        result = service.status()
        self.assertIsNone(result['active'])
        self.assertEqual(result['connections'][0]['jobs']['upload']['status'], 'complete')
        self.assertTrue(result['connections'][0]['jobs']['upload']['last_success'])


if __name__ == '__main__':
    unittest.main()
