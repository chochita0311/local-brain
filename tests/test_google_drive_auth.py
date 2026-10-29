"""Google CLI transport doubles only; never log in or fetch real user tokens."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.google_drive.auth import GcloudAuth, gcloud_path, sdk_environment
from localbrain.google_drive.policy import DriveError, SCOPES


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.bound = {'connection': 'account-one'}
        self.calls, self.connected, self.errors = [], [], []
        self.active, self.credentials = 'account-one', ['account-one']
        self.failure = None
        self.auth = GcloudAuth(lambda key: self.bound.get(key), self.connected_callback,
                               lambda *args:self.errors.append(args), runner=self.run_cli)
        self.location = patch('localbrain.google_drive.auth.gcloud_path', return_value='/sdk/gcloud')
        self.location.start()
        self.addCleanup(self.location.stop)
        self.addCleanup(self.auth.stop)

    def connected_callback(self, connection, account, token):
        self.connected.append((connection,account,token))
        self.bound[connection]=account

    def run_cli(self, argv, env, timeout):
        self.calls.append((argv,env,timeout))
        if self.failure:
            return subprocess.CompletedProcess(argv,1,'',self.failure)
        if argv[1:3] == ['auth','list']:
            output=json.dumps([dict(account=a,status='ACTIVE' if a==self.active else '') for a in self.credentials])
        elif argv[1:3] == ['auth','login']:
            if not self.credentials:
                self.credentials=['new-account'];self.active=None
            output=''
        else:
            output='synthetic-access-token-value'
        return subprocess.CompletedProcess(argv,0,output,'')

    def test_full_drive_scope_and_token_account_are_explicit(self):
        self.assertEqual(SCOPES,('https://www.googleapis.com/auth/drive',))
        self.assertEqual(self.auth.access_token('connection'),'synthetic-access-token-value')
        self.assertIn('--account=account-one',self.calls[-1][0])
        self.active='account-two'
        self.auth.invalidate('connection')
        self.auth.access_token('connection')
        self.assertIn('--account=account-one',self.calls[-1][0])
        self.assertFalse(any(c[0][1:3]==['auth','list'] for c in self.calls))

    def test_token_cache_is_memory_only_and_refresh_uses_sdk(self):
        self.auth.access_token('connection');self.auth.access_token('connection')
        self.assertEqual(len(self.calls),1)
        self.auth.invalidate('connection');self.auth.access_token('connection')
        self.assertEqual(len(self.calls),2)
        self.auth.tokens['account-one']=('expired-token',0)
        self.auth.access_token('connection');self.assertEqual(len(self.calls),3)
        self.assertFalse(any('revoke' in c[0] or '--update-adc' in c[0] for c in self.calls))

    def test_no_bound_account_cannot_silently_follow_active_account(self):
        with self.assertRaises(DriveError) as error:self.auth.access_token('unbound')
        self.assertEqual(error.exception.code,'unauthenticated');self.assertFalse(self.calls)

    def test_existing_login_uses_active_account_without_opening_login(self):
        self.auth.connect('new-connection')
        self.assertEqual(self.bound['new-connection'],'account-one')
        self.assertFalse(any(c[0][1:3]==['auth','login'] for c in self.calls))

    def test_multiple_accounts_without_active_require_selection(self):
        self.credentials=['account-one','account-two'];self.active=None
        with self.assertRaises(DriveError) as error:self.auth.connect('new-connection')
        self.assertEqual(error.exception.code,'account')
        self.auth.connect('new-connection','account-two')
        self.assertEqual(self.bound['new-connection'],'account-two')

    def test_explicit_login_keeps_global_account_and_adc_unchanged(self):
        self.auth.begin('connection')
        thread=list(self.auth.flows.values())[0] if self.auth.flows else None
        if thread:thread.join(3)
        login=next(c for c in self.calls if c[0][1:3]==['auth','login'])
        for flag in ('--enable-gdrive-access','--force','--no-activate','--quiet'):
            self.assertIn(flag,login[0])
        self.assertIn('account-one',login[0]);self.assertNotIn('--update-adc',login[0])
        self.assertEqual(login[2],300);self.assertTrue(self.connected);self.assertFalse(self.errors)

    def test_first_login_binds_unique_new_account(self):
        self.credentials=[];self.active=None
        self.auth.begin('new-connection')
        thread=list(self.auth.flows.values())[0] if self.auth.flows else None
        if thread:thread.join(3)
        self.assertEqual(self.bound['new-connection'],'new-account')

    def test_network_and_reauth_errors_are_sanitized_and_distinct(self):
        self.failure='Network connection failed; synthetic-private-token-should-not-leak'
        with self.assertRaises(DriveError) as error:self.auth.access_token('connection')
        self.assertEqual(error.exception.code,'network');self.assertTrue(error.exception.retryable)
        self.assertNotIn('synthetic-private-token',str(error.exception))
        self.failure='invalid_grant: please reauthenticate'
        with self.assertRaises(DriveError) as error:self.auth.access_token('connection')
        self.assertEqual(error.exception.code,'reauth');self.assertEqual(self.bound['connection'],'account-one')

    def test_sdk_environment_removes_frozen_runtime_and_credential_overrides(self):
        with patch.dict(os.environ,{'PYTHONHOME':'frozen','PYTHONPATH':'private-runtime','DYLD_LIBRARY_PATH':'bundled',
                                    'CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE':'other-principal','CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT':'other-principal'}):
            env=sdk_environment()
        for key in ('PYTHONHOME','PYTHONPATH','DYLD_LIBRARY_PATH'):self.assertNotIn(key,env)
        self.assertEqual(env['CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE'],'')
        self.assertEqual(env['CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT'],'')
        self.assertEqual(env['CLOUDSDK_CORE_DISABLE_FILE_LOGGING'],'true')
        self.assertEqual(env['CLOUDSDK_CORE_LOG_HTTP'],'false')

    def test_status_reads_no_cli_or_google(self):
        self.assertTrue(self.auth.status()['ready']);self.assertFalse(self.calls)


class DiscoveryAndProcessTests(unittest.TestCase):
    def test_missing_and_override_paths_are_explicit(self):
        with patch.dict(os.environ,{'LOCALBRAIN_GCLOUD_PATH':'/missing/gcloud'}),self.assertRaises(DriveError) as error:gcloud_path()
        self.assertEqual(error.exception.code,'gcloud_missing')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'gcloud';path.write_text('#!/bin/sh\nexit 0\n');path.chmod(0o700)
            with patch.dict(os.environ,{'LOCALBRAIN_GCLOUD_PATH':str(path)}):self.assertEqual(gcloud_path(),str(path))

    def test_default_sdk_location_is_found_without_shell_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'google-cloud-sdk/bin/gcloud';path.parent.mkdir(parents=True)
            path.write_text('#!/bin/sh\nexit 0\n');path.chmod(0o700)
            with patch.dict(os.environ,{'PATH':'','LOCALBRAIN_GCLOUD_PATH':''}),patch('pathlib.Path.home',return_value=root):
                self.assertEqual(gcloud_path(),str(path))

    def test_real_subprocess_has_bounded_timeout_and_no_shell(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'gcloud'
            path.write_text('#!'+sys.executable+'\nimport time\ntime.sleep(30)\n');path.chmod(0o700)
            auth=GcloudAuth(lambda key:'account-one',lambda *a:None,lambda *a:None)
            try:
                with patch.dict(os.environ,{'LOCALBRAIN_GCLOUD_PATH':str(path)}),self.assertRaises(DriveError) as error:
                    auth.command(['auth','print-access-token'],timeout=0.05)
                self.assertEqual(error.exception.code,'network');self.assertFalse(auth.processes)
            finally:auth.stop()

    def test_shutdown_terminates_owned_login_and_preserves_external_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'gcloud'
            path.write_text('#!'+sys.executable+'\nimport sys,time\nif "list" in sys.argv: print("[]")\nelse: time.sleep(30)\n');path.chmod(0o700)
            auth=GcloudAuth(lambda key:None,lambda *a:None,lambda *a:None)
            with patch.dict(os.environ,{'LOCALBRAIN_GCLOUD_PATH':str(path)}):
                auth.begin('connection')
                deadline=time.monotonic()+3
                while not auth.processes and time.monotonic()<deadline:time.sleep(0.01)
                self.assertTrue(auth.processes)
                auth.stop()
                self.assertFalse(auth.processes);self.assertFalse(auth.flows)
