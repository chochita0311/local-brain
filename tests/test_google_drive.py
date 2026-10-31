"""Synthetic-only Drive sync contracts; no user data or Google account needed."""
import copy
import hashlib
import io
import json
import os
import ssl
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from localbrain.google_drive import policy
from localbrain.google_drive.api import API, api_error, google_opener
from localbrain.google_drive.engine import Engine
from localbrain.google_drive.policy import DriveError, FOLDER, MAX_FILE_BYTES, local_inventory, next_slot, root_url
from localbrain.google_drive.store import Store
from localbrain.google_drive.service import DriveService
from localbrain.foundation.config import Settings


class FakeAPI:
    def __init__(self):
        self.files = {'root': dict(id='root', name='shared', mimeType=FOLDER, parents=[], version='1')}
        self.bodies = {}
        self.calls = []
        self.keys = {}
        self.sequence = 0
        self.cancel = lambda: False
        self.denied = set()
        self.fail_listing = False
        self.fail_upload = False

    def check(self):
        if self.cancel():
            raise DriveError('cancelled', 'Stopped')

    def close(self):
        pass

    def get(self, key):
        self.check()
        if key in self.denied or key not in self.files:
            raise DriveError('unavailable', 'Unavailable')
        return copy.deepcopy(self.files[key])

    def prefetch(self, keys, progress=lambda checked, total: None):
        self.check()  # In-memory fixture needs no remote prefetch.

    def invalidate(self, keys):
        pass  # In-memory fixture has no metadata snapshot.

    def children(self, parent):
        if self.fail_listing:
            raise DriveError('partial_listing', 'Incomplete')
        return [copy.deepcopy(f) for f in self.files.values() if parent in f.get('parents', []) and not f.get('trashed') and f['id'] not in self.denied]

    def new_id(self):
        self.sequence += 1
        return 'generated-' + str(self.sequence)

    def create_folder(self, key, name, parent):
        self.calls.append(('mkdir', key))
        self.files[key] = dict(id=key, name=name, parents=[parent], mimeType=FOLDER, version='1')
        return self.get(key)

    def metadata(self, key, name, parent, current):
        self.calls.append(('metadata', key))
        self.files[key].update(name=name, parents=[parent], trashed=False)
        return self.get(key)

    def trash(self, key):
        self.calls.append(('trash', key))
        self.files[key]['trashed'] = True
        return self.get(key)

    def upload(self, key, name, parent, path, digest, existing, state, checkpoint, progress=lambda sent, size: None):
        self.calls.append(('upload', key))
        if self.fail_upload:
            raise DriveError('network', 'Disconnected', True)
        self.body(key, name, parent, path.read_bytes())
        progress(path.stat().st_size, path.stat().st_size)
        return self.get(key)

    def body(self, key, name, parent, body):
        self.bodies[key] = body
        self.files[key] = dict(id=key, name=name, parents=[parent], mimeType='application/octet-stream',
                               size=str(len(body)), md5Checksum=hashlib.md5(body).hexdigest(),
                               version=str(int(self.files.get(key, {}).get('version', '0')) + 1))

    def download(self, metadata, path):
        self.calls.append(('download', metadata['id']))
        path.write_bytes(self.bodies[metadata['id']])
        return hashlib.md5(self.bodies[metadata['id']]).hexdigest()


class TempCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='drive-test-')
        # macOS /var is a symlink; runtime uses its resolved private location.
        self.root = Path(self.temp.name).resolve()
        self.data = self.root / 'data'
        self.store = Store(self.data)
        self.connection = self.store.add('https://drive.google.com/drive/folders/root?resourcekey=link-key', 'publisher-self')
        self.engine = Engine(self.store, self.data)
        self.api = FakeAPI()
        self.folder = self.root / 'vault'
        self.folder.mkdir()
        self.sources = [dict(id=1, path=str(self.folder), source_type='folder', label='Vault')]

    def tearDown(self):
        self.temp.cleanup()

    def received(self):
        return self.data / 'external-sources/google-drive' / self.connection['id'] / 'peer'

    def peer(self):
        self.api.create_folder('peer', 'publisher-peer', 'root')


class PolicyTests(TempCase):
    def test_full_url_and_resource_key_only(self):
        self.assertEqual(root_url('https://drive.google.com/drive/u/0/folders/abc_12?resourcekey=key-1'), ('abc_12', 'key-1'))
        for value in ['abc_12', 'http://drive.google.com/drive/folders/a', 'https://evil.test/drive/folders/a', 'https://drive.google.com.evil.test/drive/folders/a', 'https://drive.google.com/drive/folders/a?resourcekey=x%2Fy']:
            with self.subTest(value=value), self.assertRaises(DriveError): root_url(value)

    def test_size_is_inclusive_before_reading(self):
        file = self.folder / 'limit.iso'
        with file.open('wb') as out: out.truncate(MAX_FILE_BYTES)
        entries, errors = local_inventory(self.sources)
        self.assertFalse(errors)
        self.assertIsNone(entries['1:vault/limit.iso']['error'])
        with file.open('ab') as out: out.write(b'x')
        with patch('pathlib.Path.open', side_effect=AssertionError('must not read bodies')):
            entries, errors = local_inventory(self.sources)
        self.assertEqual(len(errors), 1)

    def test_hidden_files_and_special_links(self):
        (self.folder / '.config').write_text('hidden')
        (self.folder / 'link').symlink_to(self.root)
        entries, errors = local_inventory(self.sources)
        self.assertIn('1:vault/.config', entries)
        self.assertEqual(len(errors), 1)
        self.assertNotIn('1:vault/link/data', entries)

    def test_missing_root_is_failure_not_empty(self):
        self.folder.rmdir()
        with self.assertRaises(DriveError): local_inventory(self.sources)

    def test_all_seven_slots_and_no_catchup(self):
        now = datetime(2026, 10, 28, 1, 20, tzinfo=timezone.utc)  # 10:20 Seoul
        expected = {15: (1,30), 30: (1,30), 60: (2,0), 180: (3,0), 360: (3,0), 720: (3,0), 1440: (15,0)}
        for value, hm in expected.items():
            result = next_slot(now, value, 'Asia/Seoul')
            self.assertEqual((result.hour, result.minute), hm)
            self.assertGreater(result, now)
        exact = datetime(2026,10,28,0,0,tzinfo=timezone.utc)
        self.assertEqual(next_slot(exact,15,'UTC').minute,15)

    def test_dst_gap_and_fold_are_real_future_instants(self):
        spring = datetime(2026,3,8,6,59,tzinfo=timezone.utc)
        self.assertEqual(next_slot(spring,60,'America/New_York'), datetime(2026,3,8,7,0,tzinfo=timezone.utc))
        autumn = datetime(2026,11,1,5,50,tzinfo=timezone.utc)
        self.assertEqual(next_slot(autumn,60,'America/New_York'), datetime(2026,11,1,6,0,tzinfo=timezone.utc))

    def test_private_persistent_state_defaults_and_version(self):
        self.assertEqual(self.store.path.stat().st_mode & 0o777, 0o600)
        job = self.store.jobs(self.connection['id'])['upload']
        self.assertEqual((job['auto'], job['interval']), (False,360))
        self.store.put('checkpoint', {'id':'synthetic'})
        self.assertEqual(Store(self.data).get('checkpoint'), {'id':'synthetic'})


class EngineTests(TempCase):
    def test_publish_initial_diff_update_rename_and_trash(self):
        (self.folder / '.settings').mkdir()
        file = self.folder / '.settings/a.bin'
        file.write_bytes(b'first')
        first = self.engine.publish(self.connection, self.sources, self.api)
        self.assertEqual(first['transferred'],1)
        manifest = self.store.manifest(self.connection['id'],'upload')
        file_id = manifest['1:vault/.settings/a.bin']['remote_id']
        self.api.calls.clear()
        second = self.engine.publish(self.connection, self.sources, self.api)
        self.assertEqual((second['transferred'],second['changed'],second['errors']), (0,0,[]))
        file.rename(file.with_name('renamed.bin'))
        third = self.engine.publish(self.connection, self.sources, self.api)
        self.assertEqual(third['transferred'],0)
        self.assertEqual(self.api.files[file_id]['name'],'renamed.bin')
        file = file.with_name('renamed.bin')
        file.write_bytes(b'updated')
        self.assertEqual(self.engine.publish(self.connection,self.sources,self.api)['transferred'],1)
        file.unlink()
        self.engine.publish(self.connection,self.sources,self.api)
        self.assertTrue(self.api.files[file_id]['trashed'])

    def test_move_folder_preserves_file_identity_without_transfer(self):
        (self.folder/'one').mkdir(); (self.folder/'one/file').write_bytes(b'content')
        self.engine.publish(self.connection,self.sources,self.api)
        (self.folder/'one').rename(self.folder/'two')
        result=self.engine.publish(self.connection,self.sources,self.api)
        self.assertEqual(result['transferred'],0)
        self.assertFalse(result['errors'])

    def test_unselected_source_preserves_upload(self):
        (self.folder/'a').write_bytes(b'original')
        self.engine.publish(self.connection,self.sources,self.api)
        before=copy.deepcopy(self.api.files)
        self.engine.publish(self.connection,[],self.api)
        self.assertEqual(before,self.api.files)

    def test_oversize_keeps_prior_copy_and_other_files_continue(self):
        file=self.folder/'a'; file.write_bytes(b'old')
        self.engine.publish(self.connection,self.sources,self.api)
        file_id=self.store.manifest(self.connection['id'],'upload')['1:vault/a']['remote_id']
        file.write_bytes(b'longer-than-cap')
        (self.folder/'b').write_bytes(b'new')
        with patch('localbrain.google_drive.policy.MAX_FILE_BYTES',8):
            result=self.engine.publish(self.connection,self.sources,self.api)
        self.assertEqual((result['excluded'],result['transferred']), (1,1))
        self.assertEqual(self.api.bodies[file_id],b'old')
        self.assertFalse(self.api.files[file_id].get('trashed'))
        file.unlink(); self.engine.publish(self.connection,self.sources,self.api)
        self.assertTrue(self.api.files[file_id]['trashed'])

    def test_failed_scan_or_remote_access_never_erases(self):
        (self.folder/'a').write_bytes(b'old');self.engine.publish(self.connection,self.sources,self.api)
        before=copy.deepcopy(self.api.files)
        self.folder.rename(self.root/'moved')
        with self.assertRaises(DriveError):self.engine.publish(self.connection,self.sources,self.api)
        self.assertEqual(before,self.api.files)

    def test_failed_upload_uses_same_preallocated_id_after_restart(self):
        (self.folder/'a').write_bytes(b'old');self.api.fail_upload=True
        self.engine.publish(self.connection,self.sources,self.api)
        checkpoint=self.store.manifest(self.connection['id'],'upload')['1:vault/a']['remote_id']
        self.api.fail_upload=False
        self.engine=Engine(Store(self.data),self.data)
        self.engine.publish(self.connection,self.sources,self.api)
        self.assertEqual(self.store.manifest(self.connection['id'],'upload')['1:vault/a']['remote_id'],checkpoint)
        self.assertEqual(sum(f['name']=='a' for f in self.api.files.values()),1)

    def test_receive_initial_diff_rename_move_and_remote_trash(self):
        self.peer();self.api.create_folder('dir','old','peer');self.api.body('doc','a.bin','dir',b'hello')
        first=self.engine.receive(self.connection,'peer',self.api)
        self.assertEqual(first['transferred'],1)
        self.assertEqual((self.received()/'old/a.bin').read_bytes(),b'hello')
        self.assertEqual(self.engine.receive(self.connection,'peer',self.api)['transferred'],0)
        self.api.files['dir']['name']='new';self.api.files['doc']['name']='renamed.bin'
        result=self.engine.receive(self.connection,'peer',self.api)
        self.assertEqual(result['transferred'],0)
        self.assertTrue((self.received()/'new/renamed.bin').exists())
        self.assertFalse((self.received()/'old').exists())
        self.api.trash('doc')
        self.engine.receive(self.connection,'peer',self.api)
        self.assertFalse((self.received()/'new/renamed.bin').exists())

    def test_receive_access_loss_partial_listing_and_failed_media_preserve(self):
        self.peer();self.api.body('doc','a','peer',b'old');self.engine.receive(self.connection,'peer',self.api)
        self.api.denied.add('doc')
        result=self.engine.receive(self.connection,'peer',self.api)
        self.assertTrue(result['errors']);self.assertEqual((self.received()/'a').read_bytes(),b'old')
        self.api.denied.clear();self.api.fail_listing=True
        with self.assertRaises(DriveError):self.engine.receive(self.connection,'peer',self.api)
        self.assertEqual((self.received()/'a').read_bytes(),b'old')
        self.api.fail_listing=False;self.api.body('doc','a','peer',b'new')
        with patch.object(self.api,'download',side_effect=DriveError('network','Interrupted')):
            result=self.engine.receive(self.connection,'peer',self.api)
        self.assertTrue(result['errors']);self.assertEqual((self.received()/'a').read_bytes(),b'old')
        self.assertFalse(list(self.received().glob('.localbrain-drive-*')))

    def test_receive_oversize_unmanaged_files_and_links_preserve(self):
        self.peer();self.api.body('doc','a','peer',b'old');self.engine.receive(self.connection,'peer',self.api)
        self.api.body('doc','a','peer',b'updated');self.api.files['doc']['size']=str(MAX_FILE_BYTES+1)
        self.api.calls.clear();result=self.engine.receive(self.connection,'peer',self.api)
        self.assertTrue(result['errors']);self.assertNotIn(('download','doc'),self.api.calls)
        self.assertEqual((self.received()/'a').read_bytes(),b'old')
        (self.received()/'personal').write_bytes(b'unmanaged');self.api.body('new','personal','peer',b'remote')
        self.engine.receive(self.connection,'peer',self.api)
        self.assertEqual((self.received()/'personal').read_bytes(),b'unmanaged')
        (self.received()/'a').unlink();outside=self.root/'outside';outside.write_bytes(b'private')
        (self.received()/'a').symlink_to(outside);self.api.files['doc']['size']='7'
        result=self.engine.receive(self.connection,'peer',self.api)
        self.assertEqual(outside.read_bytes(),b'private');self.assertTrue(result['errors'])

    def test_remote_duplicate_or_traversal_names_abort_before_changes(self):
        self.peer();self.api.body('doc','../escape','peer',b'bad')
        with self.assertRaises(DriveError):self.engine.receive(self.connection,'peer',self.api)
        self.api.files['doc']['name']='same';self.api.body('other','SAME','peer',b'bad')
        with self.assertRaises(DriveError):self.engine.receive(self.connection,'peer',self.api)

    def test_local_edit_is_replaced_from_remote_and_google_docs_skip(self):
        self.peer();self.api.body('doc','a','peer',b'original');self.engine.receive(self.connection,'peer',self.api)
        (self.received()/'a').write_bytes(b'edited')
        self.assertEqual(self.engine.receive(self.connection,'peer',self.api)['transferred'],1)
        self.assertEqual((self.received()/'a').read_bytes(),b'original')
        self.api.files['native']=dict(id='native',name='native',parents=['peer'],mimeType='application/vnd.google-apps.document',version='1')
        self.assertTrue(self.engine.receive(self.connection,'peer',self.api)['errors'])

    def test_cancel_stops_before_mutation(self):
        (self.folder/'a').write_bytes(b'old');self.api.cancel=lambda:True
        with self.assertRaises(DriveError):self.engine.publish(self.connection,self.sources,self.api)
        self.assertEqual(len(self.api.files),1)


class Response(io.BytesIO):
    def __init__(self,body=b'',code=200,headers=None):
        super().__init__(body);self.code=code;self.headers=headers or {}


class AdapterTests(unittest.TestCase):
    def test_mac_https_uses_system_trust_without_global_ssl_injection(self):
        from unittest.mock import Mock
        context = object()
        native = SimpleNamespace(SSLContext=Mock(return_value=context))
        with patch.dict(sys.modules, {'truststore': native}), \
                patch('localbrain.google_drive.api.sys.platform', 'darwin'), \
                patch('localbrain.google_drive.api.sys.version_info', (3, 11)), \
                patch('localbrain.google_drive.api.PooledOpener') as build:
            google_opener()
        native.SSLContext.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
        self.assertIs(build.call_args.args[0], context)

    def test_default_https_retains_certificate_and_hostname_verification(self):
        with patch('localbrain.google_drive.api.sys.platform', 'linux'), \
                patch('localbrain.google_drive.api.PooledOpener') as build:
            google_opener()
        context = build.call_args.args[0]
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_certificate_failure_is_not_login_or_retryable_network_error(self):
        from urllib.error import URLError
        from unittest.mock import Mock
        transport = Mock()
        transport.open.side_effect = URLError(ssl.SSLCertVerificationError('synthetic private issuer'))
        api = API(lambda: 'synthetic-token', opener=transport)
        with self.assertRaises(DriveError) as result:
            api.about()
        self.assertEqual(result.exception.code, 'tls')
        self.assertFalse(result.exception.retryable)
        self.assertNotIn('synthetic private issuer', str(result.exception))
        self.assertEqual(transport.open.call_count, 1)

    def test_error_classes_do_not_guess_every_403_or_404(self):
        self.assertEqual(api_error(404,{},'read').code,'unavailable')
        self.assertEqual(api_error(403,{'error':{'errors':[{'reason':'rateLimitExceeded'}]}},'read').code,'rate_limit')
        self.assertEqual(api_error(403,{'error':{'errors':[{'reason':'insufficientFilePermissions'}]}},'create').code,'permission')
        self.assertEqual(api_error(403,{},'read').code,'google_request')

    def test_pagination_complete_and_resource_key_shared_drive_flags(self):
        requests=[]
        def open_(request,timeout):
            requests.append(request)
            page={'files':[dict(id='child',resourceKey='key')],'nextPageToken':'next'} if len(requests)==1 else {'files':[]}
            return Response(json.dumps(page).encode())
        api=API(lambda:'synthetic-token',{'root':'resource-key'},SimpleNamespace(open=open_))
        self.assertEqual(len(api.children('root')),1)
        self.assertIn('pageToken=next',requests[1].full_url)
        self.assertIn('supportsAllDrives=true',requests[0].full_url)
        self.assertIn('root/resource-key',requests[0].get_header('X-goog-drive-resource-keys'))
        self.assertEqual(api.keys['child'],'key')

    def test_partial_listing_and_untrusted_upload_endpoint_rejected(self):
        api=API(lambda:'token',opener=SimpleNamespace(open=lambda *a,**k:Response(b'{"files":[],"incompleteSearch":true}')))
        with self.assertRaises(DriveError):api.children('root')
        with self.assertRaises(DriveError):api.request('PUT','https://evil.test/upload',data=b'private')

    def test_download_unknown_size_is_bounded_and_detects_change(self):
        with tempfile.TemporaryDirectory() as work:
            path=Path(work)/'staging'
            api=API(lambda:'token',opener=SimpleNamespace(open=lambda *a,**k:Response(b'x'*20)))
            with patch('localbrain.google_drive.api.MAX_FILE_BYTES',8),self.assertRaises(DriveError) as caught:
                api.download(dict(id='doc',version='1',md5Checksum='unused'),path)
            self.assertEqual(caught.exception.code,'too_large')
            self.assertLessEqual(path.stat().st_size,8)
            metadata=dict(id='doc',version='1',size='3',md5Checksum=hashlib.md5(b'abc').hexdigest())
            api=API(lambda:'token',opener=SimpleNamespace(open=lambda *a,**k:Response(b'abc')))
            with patch.object(api,'get',return_value={**metadata,'version':'2'}),self.assertRaises(DriveError):api.download(metadata,path)



class ServiceTests(TempCase):
    def service(self):
        config=Settings(self.data,self.data/'localbrain.db',self.root/'context',self.root/'claude',self.root/'codex',20,'UTC')
        auth=SimpleNamespace(flows={},stop=lambda:None,status=lambda:dict(ready=True,message=None))
        def factory(connection,cancel):self.api.cancel=cancel;return self.api
        return DriveService(config,api_factory=factory,source_loader=lambda:self.sources,auth=auth)

    def test_cached_status_never_calls_google_and_selections_persist(self):
        service=self.service()
        user={'permissionId':'synthetic-user','displayName':'Synthetic user','emailAddress':None}
        with patch('localbrain.google_drive.service.API') as google:
            google.return_value.about.return_value=user
            service._connected(self.connection['id'],'account-one','synthetic-token')
            self.assertEqual(google.return_value.about.call_count,1)
        with patch.object(self.api,'get',side_effect=AssertionError('No remote GET on status')):
            state=service.status()
        self.assertEqual(len(state['connections']),1)
        service.configure(self.connection['id'],'upload',{'sources':[1],'auto':True,'interval':180})
        job=service.status()['connections'][0]['jobs']['upload']
        self.assertEqual((job['auto'],job['interval'],job['selected']),(True,180,True))
        service.configure(self.connection['id'],'upload',{'sources':[]})
        self.assertFalse(service.store.jobs(self.connection['id'])['upload']['selected'])

    def test_root_browse_excludes_own_and_independent_receive_defaults(self):
        self.peer();self.api.create_folder('self','publisher-self','root')
        service=self.service();choices=service.browse(self.connection['id'])
        self.assertEqual([p['id'] for p in choices],['peer'])
        service.configure(self.connection['id'],'receive:peer',{'selected':True})
        job=service.store.jobs(self.connection['id'])['receive:peer']
        self.assertEqual((job['auto'],job['interval']),(False,1440))

    def test_manual_run_success_then_network_failure_preserves_last_success(self):
        (self.folder/'a').write_bytes(b'original');service=self.service()
        service.configure(self.connection['id'],'upload',{'sources':[1]})
        service.run(self.connection['id'],'upload');service.worker.join(5)
        job=service.store.jobs(self.connection['id'])['upload'];self.assertEqual(job['status'],'complete')
        success=job['last_success'];self.api.denied.add('root')
        service.run(self.connection['id'],'upload');service.worker.join(5)
        job=service.store.jobs(self.connection['id'])['upload']
        self.assertEqual(job['status'],'error');self.assertEqual(job['last_success'],success)



class ResumableTests(unittest.TestCase):
    def test_lost_chunk_response_probes_offset_before_resend(self):
        from urllib.error import URLError,HTTPError
        session='https://www.googleapis.com/upload/drive/v3/files?upload_id=synthetic'
        digest=hashlib.md5(b'abc').hexdigest();meta=dict(id='new',size='3',md5Checksum=digest,version='1')
        replies=[Response(code=200,headers={'Location':session}),URLError('network'),HTTPError(session,308,'Resume',{'Range':'bytes=0-1'},None),Response(json.dumps(meta).encode())]
        requests=[]
        def open_(request,timeout):
            requests.append(request);reply=replies.pop(0)
            if isinstance(reply,Exception):raise reply
            return reply
        api=API(lambda:'synthetic-token',opener=SimpleNamespace(open=open_),sleeper=lambda delay:None)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'snapshot';path.write_bytes(b'abc');state={};checkpoints=[]
            with patch('localbrain.google_drive.api.MULTIPART_BYTES',0):
                result=api.upload('new','a','parent',path,digest,False,state,lambda:checkpoints.append(copy.deepcopy(state)))
        self.assertEqual(result['id'],'new')
        self.assertEqual(requests[-1].data,b'c')
        self.assertEqual(requests[-1].get_header('Content-range'),'bytes 2-2/3')
        self.assertTrue(checkpoints[0]['session']);self.assertNotIn('session',state)


class SchedulerTests(TempCase):
    def service(self):
        return ServiceTests.service(self)

    def test_fixed_slots_manual_does_not_shift_and_resume_waits(self):
        service=self.service();cid=self.connection['id']
        service.configure(cid,'upload',{'sources':[1],'auto':True,'interval':15})
        at=lambda h,m:datetime(2026,10,28,h,m,tzinfo=timezone.utc)
        with patch.object(service,'run') as run:
            service.schedule_once(at(10,20),'UTC');self.assertFalse(run.called)
            self.assertEqual(service.slots[(cid,'upload')][0],at(10,30))
            service.schedule_once(at(10,30),'UTC');run.assert_called_once_with(cid,'upload')
            service.schedule_once(at(10,30),'UTC');self.assertEqual(run.call_count,1)
            service.schedule_once(at(10,50),'UTC',reset=True);self.assertEqual(run.call_count,1)
            self.assertEqual(service.slots[(cid,'upload')][0],at(11,0))
            service.schedule_once(at(11,0),'UTC');self.assertEqual(run.call_count,2)

    def test_due_peers_queue_without_duplicate_active_or_timezone_catchup(self):
        service=self.service();cid=self.connection['id'];self.peer();service.browse(cid)
        service.configure(cid,'upload',{'sources':[1],'auto':True,'interval':60})
        service.configure(cid,'receive:peer',{'selected':True,'auto':True,'interval':180})
        with patch.object(service,'run') as run:
            service.schedule_once(datetime(2026,10,28,8,59,tzinfo=timezone.utc),'UTC')
            service.schedule_once(datetime(2026,10,28,9,0,tzinfo=timezone.utc),'UTC')
            self.assertEqual(run.call_count,1)
            service.schedule_once(datetime(2026,10,28,9,0,1,tzinfo=timezone.utc),'UTC')
            self.assertEqual(run.call_count,2)
            service.schedule_once(datetime(2026,10,28,9,0,2,tzinfo=timezone.utc),'Asia/Seoul',reset=True)
            self.assertEqual(run.call_count,2)

class StructureReplacementTests(TempCase):
    def test_outgoing_file_folder_replacement_and_link_never_erases_descendants(self):
        path=self.folder/'replace';path.write_bytes(b'old')
        self.engine.publish(self.connection,self.sources,self.api)
        old=self.store.manifest(self.connection['id'],'upload')['1:vault/replace']['remote_id']
        path.unlink();path.mkdir();(path/'child').write_bytes(b'child')
        result=self.engine.publish(self.connection,self.sources,self.api)
        self.assertFalse(result['errors']);self.assertTrue(self.api.files[old]['trashed'])
        current=self.store.manifest(self.connection['id'],'upload')['1:vault/replace/child']['remote_id']
        import shutil
        shutil.rmtree(path);path.symlink_to(self.root)
        result=self.engine.publish(self.connection,self.sources,self.api)
        self.assertTrue(result['errors']);self.assertFalse(self.api.files[current].get('trashed'))

    def test_incoming_replaces_confirmed_deleted_file_with_folder_then_file(self):
        self.peer();self.api.body('old','replace','peer',b'old');self.engine.receive(self.connection,'peer',self.api)
        self.api.trash('old');self.api.create_folder('dir','replace','peer');self.api.body('child','child','dir',b'child')
        result=self.engine.receive(self.connection,'peer',self.api)
        self.assertFalse(result['errors']);self.assertEqual((self.received()/'replace/child').read_bytes(),b'child')
        self.api.trash('dir');self.api.body('new','replace','peer',b'new')
        result=self.engine.receive(self.connection,'peer',self.api)
        self.assertFalse(result['errors']);self.assertEqual((self.received()/'replace').read_bytes(),b'new')

    def test_inaccessible_parent_does_not_count_as_move_outside(self):
        self.peer();self.api.create_folder('dir','folder','peer');self.api.body('child','child','dir',b'child')
        self.engine.receive(self.connection,'peer',self.api)
        self.api.denied.add('dir')
        result=self.engine.receive(self.connection,'peer',self.api)
        self.assertTrue(result['errors']);self.assertEqual((self.received()/'folder/child').read_bytes(),b'child')

class RecoveryTests(TempCase):
    def test_crash_after_file_replace_recovers_verified_checkpoint(self):
        self.peer();self.api.body('doc','a','peer',b'original')
        checkpoint=self.store.checkpoint
        def crash(connection,job,entries,touched=None):
            if entries.get('doc',{}).get('complete'):
                raise RuntimeError('simulated crash after atomic replacement')
            return checkpoint(connection,job,entries,touched)
        with patch.object(self.store,'checkpoint',side_effect=crash),self.assertRaises(RuntimeError):
            self.engine.receive(self.connection,'peer',self.api)
        self.assertTrue(self.store.get('receive-commit'))
        self.assertEqual((self.received()/'a').read_bytes(),b'original')
        self.store=Store(self.data);self.engine=Engine(self.store,self.data)
        self.assertIsNone(self.store.get('receive-commit'))
        self.assertTrue(self.store.manifest(self.connection['id'],'receive:peer')['doc']['complete'])
        result=self.engine.receive(self.connection,'peer',self.api)
        self.assertEqual(result['transferred'],0);self.assertFalse(result['errors'])
        for path in [self.received(),self.received().parent,self.received().parent.parent]:
            self.assertEqual(path.stat().st_mode&0o777,0o700)

class WebTests(TempCase):
    def setUp(self):
        super().setUp()
        import asyncio
        from fastapi import FastAPI
        from starlette.requests import Request
        from localbrain.google_drive.web import install_routes
        self.asyncio,self.Request=asyncio,Request
        self.service=ServiceTests.service(self)
        self.app=FastAPI();self.app.state.google_drive=self.service
        install_routes(self.app)
        self.endpoints={r.path:r.endpoint for r in self.app.routes if r.path.startswith('/api/settings/google-drive')}

    def request(self,body=None):
        delivered=False
        async def receive():
            nonlocal delivered
            if delivered:return {'type':'http.disconnect'}
            delivered=True
            return {'type':'http.request','body':json.dumps(body or {}).encode(),'more_body':False}
        return self.Request({'type':'http','method':'POST','scheme':'http','server':('127.0.0.1',8000),
            'path':'/api/settings/google-drive','query_string':b'','headers':[], 'app':self.app},receive)

    def test_status_and_new_selection_routes_are_settings_only_and_cached(self):
        self.assertTrue(all(path.startswith('/api/settings/google-drive') for path in self.endpoints))
        with patch.object(self.api,'get',side_effect=AssertionError('status may not call Google')):
            value=self.asyncio.run(self.endpoints['/api/settings/google-drive'](self.request()))
        self.assertEqual(value['max_file_bytes'],MAX_FILE_BYTES)
        endpoint=self.endpoints['/api/settings/google-drive/{connection_id}/jobs/{job}']
        result=self.asyncio.run(endpoint(self.connection['id'],'upload',self.request({'sources':[1],'auto':False})))
        self.assertTrue(result['saved'])
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as error:
            self.asyncio.run(endpoint(self.connection['id'],'upload',self.request({'sources':[True]})))
        self.assertEqual(error.exception.status_code,422)
        with self.assertRaises(HTTPException) as error:
            self.asyncio.run(endpoint(self.connection['id'],'upload',self.request({'selected':False})))
        self.assertEqual(error.exception.status_code,422)

    def test_invalid_root_and_unavailable_drive_state_preserve_existing_connections(self):
        from fastapi import HTTPException
        endpoint=self.endpoints['/api/settings/google-drive/connections']
        with self.assertRaises(HTTPException):self.asyncio.run(endpoint(self.request({'url':'bare-id','target':'test'})))
        self.assertEqual(len(self.store.connections()),1)
        self.app.state.google_drive=None
        with self.assertRaises(HTTPException) as error:self.asyncio.run(self.endpoints['/api/settings/google-drive'](self.request()))
        self.assertEqual(error.exception.status_code,503)


class SourceMutationTests(TempCase):
    def test_upload_snapshot_is_consistent_and_changed_scan_defers_deletes(self):
        file = self.folder / 'a'
        removed = self.folder / 'b'
        file.write_bytes(b'old'); removed.write_bytes(b'keep until stable')
        self.engine.publish(self.connection, self.sources, self.api)
        manifest = self.store.manifest(self.connection['id'], 'upload')
        file_id = manifest['1:vault/a']['remote_id']
        removed_id = manifest['1:vault/b']['remote_id']
        file.write_bytes(b'first change'); removed.unlink()
        upload = self.api.upload
        def mutate(*args, **kwargs):
            result = upload(*args, **kwargs)
            file.write_bytes(b'second change')
            return result
        with patch.object(self.api, 'upload', side_effect=mutate):
            result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertTrue(result['errors'])
        self.assertEqual(self.api.bodies[file_id], b'first change')
        self.assertFalse(self.api.files[removed_id].get('trashed'))
        result = self.engine.publish(self.connection, self.sources, self.api)
        self.assertFalse(result['errors'])
        self.assertEqual(self.api.bodies[file_id], b'second change')
        self.assertTrue(self.api.files[removed_id]['trashed'])


class GcloudServiceContractTests(TempCase):
    def test_account_mismatch_preserves_binding_selections_and_copies(self):
        service=ServiceTests.service(self)
        service.configure(self.connection['id'],'upload',{'sources':[1],'auto':True})
        with patch('localbrain.google_drive.service.API') as google:
            google.return_value.about.return_value={'permissionId':'first-user','displayName':'First user'}
            service._connected(self.connection['id'],'account-one','synthetic-token')
            before=service.store.connection(self.connection['id'])
            google.return_value.about.return_value={'permissionId':'other-user','displayName':'Other user'}
            with self.assertRaises(DriveError):service._connected(self.connection['id'],'account-two','synthetic-token')
        self.assertEqual(service.store.connection(self.connection['id']),before)
        self.assertEqual(service._bound_account(self.connection['id']),'account-one')
        self.assertTrue(service.store.jobs(self.connection['id'])['upload']['auto'])

    def test_auth_requests_are_explicit_and_status_never_starts_commands(self):
        service=ServiceTests.service(self)
        from unittest.mock import Mock
        service.auth.connect=Mock();service.auth.begin=Mock()
        service.authenticate(self.connection['id'],'account-one',False)
        service.auth.connect.assert_called_once_with(self.connection['id'],'account-one')
        service.auth.begin.assert_not_called()
        service.authenticate(self.connection['id'],'account-one',True)
        service.auth.begin.assert_called_once_with(self.connection['id'],'account-one')
        state=service.status()
        self.assertEqual(state['auth_mode'],'gcloud')
        self.assertEqual(state['auth_scope'],'https://www.googleapis.com/auth/drive')
        self.assertTrue(state['gcloud_ready']);self.assertNotIn('provider_ready',state)


if __name__ == '__main__':
    unittest.main()
