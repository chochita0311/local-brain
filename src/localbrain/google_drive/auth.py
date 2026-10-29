"""Google CLI credential helper; app storage never owns Google credentials."""

import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

from .policy import DriveError

LOGIN_COMMAND = 'gcloud auth login --enable-gdrive-access --force'


def gcloud_path():
    """Also find standard installations when a macOS app lacks the shell PATH."""
    override = os.environ.get('LOCALBRAIN_GCLOUD_PATH')
    if override:
        candidates = [Path(override).expanduser()]
    else:
        found = shutil.which('gcloud')
        candidates = ([Path(found)] if found else []) + [
            Path.home() / 'google-cloud-sdk/bin/gcloud',
            Path('/opt/homebrew/bin/gcloud'), Path('/usr/local/bin/gcloud'),
            Path('/opt/homebrew/share/google-cloud-sdk/bin/gcloud'),
            Path('/usr/local/share/google-cloud-sdk/bin/gcloud'),
            Path.home() / '.local/share/google-cloud-sdk/bin/gcloud',
        ]
    for path in candidates:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.absolute())
    raise DriveError('gcloud_missing', 'Google Cloud CLI(gcloud)를 찾을 수 없습니다. 설치 후 다시 연결해 주세요.')


def sdk_environment():
    env = dict(os.environ)
    # The SDK must use its own Python/runtime rather than a frozen app's loader.
    for key in ('PYTHONHOME', 'PYTHONPATH', '_MEIPASS2', '_PYI_APPLICATION_HOME_DIR',
                'DYLD_LIBRARY_PATH', 'DYLD_FALLBACK_LIBRARY_PATH', 'LD_LIBRARY_PATH'):
        env.pop(key, None)
    env['PATH'] = os.pathsep.join([env.get('PATH', ''), '/opt/homebrew/bin', '/usr/local/bin', '/usr/bin', '/bin'])
    env.update(CLOUDSDK_CORE_DISABLE_USAGE_REPORTING='true',
               CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK='true',
               CLOUDSDK_CORE_DISABLE_FILE_LOGGING='true', CLOUDSDK_CORE_LOG_HTTP='false')
    # Credential overrides/impersonation must not replace the pinned user account.
    for key in ('CLOUDSDK_AUTH_ACCESS_TOKEN', 'CLOUDSDK_AUTH_ACCESS_TOKEN_FILE',
                'CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE', 'CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT'):
        env[key] = ''
    return env


def account_name(value):
    if (not isinstance(value, str) or not value or len(value) > 320
            or value.startswith('-') or any(c.isspace() or ord(c) < 32 for c in value)):
        raise DriveError('account', '연결할 Google 계정을 확인해 주세요.')
    return value


def sdk_error(stderr):
    """Inspect known reasons without returning raw output, addresses or tokens."""
    text = (stderr or '').lower()
    if any(word in text for word in ('connection', 'network', 'timed out', 'timeout', 'sslerror', 'transporterror', 'name resolution')):
        return DriveError('network', 'Google 인증 서버에 연결하지 못했습니다. 연결 상태를 확인하고 다시 시도해 주세요.', True)
    if any(word in text for word in ('invalid_grant', 'reauthentication', 'no valid credentials',
                                     'does not have valid credentials', 'not have valid credentials',
                                     'no active account', 'not have an active account', 'login required')):
        return DriveError('reauth', 'Google 로그인이 필요합니다. Drive 접근을 포함해 다시 로그인해 주세요.')
    if 'python' in text and any(word in text for word in ('not found', 'could not', 'unsupported', 'requires')):
        return DriveError('gcloud_runtime', 'gcloud 실행 환경을 확인하지 못했습니다. Google Cloud CLI 설치와 Python 설정을 확인해 주세요.')
    return DriveError('gcloud_request', 'gcloud 인증 요청을 완료하지 못했습니다. Google 로그인 상태와 CLI 설치를 확인해 주세요.')


class GcloudAuth:
    def __init__(self, bound_account, on_connected, on_error, runner=None):
        self.bound_account, self.on_connected, self.on_error = bound_account, on_connected, on_error
        self.runner = runner
        self.lock = threading.RLock()
        self.tokens, self.flows, self.processes = {}, {}, {}
        self.token_locks = {}
        self.stopped = threading.Event()

    @staticmethod
    def status():
        try:
            gcloud_path()
            return dict(ready=True, message=None)
        except DriveError as error:
            return dict(ready=False, message=str(error))

    def command(self, arguments, timeout=45):
        if self.stopped.is_set():
            raise DriveError('cancelled', 'Google 연결을 중단했습니다.')
        argv = [gcloud_path(), *arguments, '--quiet', '--user-output-enabled']
        if self.runner:
            result = self.runner(argv, sdk_environment(), timeout)
        else:
            try:
                process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
                                           env=sdk_environment(), start_new_session=os.name == 'posix')
            except OSError:
                raise DriveError('gcloud_runtime', 'gcloud를 실행하지 못했습니다. 설치 경로와 실행 권한을 확인해 주세요.') from None
            with self.lock:
                if self.stopped.is_set():
                    self._terminate(process)
                    process.communicate()
                    raise DriveError('cancelled', 'Google 연결을 중단했습니다.')
                self.processes[process.pid] = process
            try:
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    self._terminate(process)
                    process.communicate()
                    raise DriveError('auth_timeout' if arguments[:2] == ['auth', 'login'] else 'network',
                                     'Google 인증 요청 시간이 끝났습니다. 연결 상태를 확인하고 다시 시도해 주세요.', True) from None
                result = subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
            finally:
                with self.lock:
                    self.processes.pop(process.pid, None)
        if self.stopped.is_set():
            raise DriveError('cancelled', 'Google 연결을 중단했습니다.')
        if result.returncode:
            raise sdk_error(result.stderr)
        if len(result.stdout or '') > 65536:
            raise DriveError('gcloud_response', 'gcloud 인증 응답을 확인하지 못했습니다.')
        return result.stdout or ''

    @staticmethod
    def _terminate(process):
        if process.poll() is not None:
            return
        try:
            if os.name == 'posix':
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if os.name == 'posix':
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
        except ProcessLookupError:
            pass

    def accounts(self):
        try:
            values = json.loads(self.command(['auth', 'list', '--format=json']))
            if not isinstance(values, list):
                raise ValueError()
            return [dict(account=account_name(v['account']), active=v.get('status') == 'ACTIVE') for v in values]
        except (ValueError, TypeError, KeyError):
            raise DriveError('gcloud_response', 'gcloud 로그인 계정 목록을 확인하지 못했습니다.') from None

    def resolve_account(self, connection_id, requested=None, allow_empty=False):
        bound = self.bound_account(connection_id)
        if requested:
            return account_name(requested)
        if bound:
            return account_name(bound)
        accounts = self.accounts()
        active = [a['account'] for a in accounts if a['active']]
        if len(active) == 1:
            return active[0]
        if len(accounts) == 1:
            return accounts[0]['account']
        if not accounts and allow_empty:
            return None
        if not accounts:
            raise DriveError('unauthenticated', 'gcloud에 로그인한 Google 계정이 없습니다. Google 로그인을 진행해 주세요.')
        raise DriveError('account', '사용할 Google 계정을 입력해 주세요. 연결 뒤에는 이 계정을 고정해 사용합니다.')

    def token_for(self, account):
        account_name(account)
        with self.lock:
            gate = self.token_locks.setdefault(account, threading.Lock())
        # Concurrent media workers share a refresh, without blocking stop()/process tracking.
        with gate:
            return self._token_for(account)

    def _token_for(self, account):
        with self.lock:
            if self.stopped.is_set():
                raise DriveError('cancelled', 'Google 연결을 중단했습니다.')
            cached = self.tokens.get(account)
            if cached and cached[1] > time.monotonic():
                return cached[0]
        token = self.command(['auth', 'print-access-token', '--account=' + account, '--format=value(token)']).strip()
        if not re.fullmatch(r'[A-Za-z0-9._~+/-]{12,16384}', token):
            raise DriveError('gcloud_response', 'gcloud 액세스 토큰을 확인하지 못했습니다.')
        with self.lock:
            if self.stopped.is_set():
                raise DriveError('cancelled', 'Google 연결을 중단했습니다.')
            # SDK tokens may already be near expiry; keep only a brief memory cache.
            # A real401 invalidates this cache and retries through gcloud once.
            self.tokens[account] = (token, time.monotonic() + 30)
            return token

    def access_token(self, connection_id):
        account = self.bound_account(connection_id)
        if not account:
            raise DriveError('unauthenticated', 'Google 연결이 필요합니다. 사용할 gcloud 계정을 연결해 주세요.')
        return self.token_for(account)

    def invalidate(self, connection_id):
        account = self.bound_account(connection_id)
        with self.lock:
            self.tokens.pop(account, None)

    def connect(self, connection_id, requested=None):
        account = self.resolve_account(connection_id, requested)
        token = self.token_for(account)
        self.on_connected(connection_id, account, token)

    def begin(self, connection_id, requested=None):
        with self.lock:
            if self.flows:
                raise DriveError('auth_pending', '진행 중인 Google 로그인을 먼저 마쳐 주세요.')
        account = self.resolve_account(connection_id, requested, allow_empty=True)
        arguments = ['auth', 'login'] + ([account] if account else [])
        arguments += ['--enable-gdrive-access', '--force', '--no-activate']

        def login():
            try:
                self.command(arguments, timeout=300)
                selected = account or self.resolve_account(connection_id)
                with self.lock:
                    self.tokens.pop(selected, None)
                self.on_connected(connection_id, selected, self.token_for(selected))
            except DriveError as error:
                if error.code != 'cancelled':
                    self.on_error(connection_id, error)
            except Exception:
                self.on_error(connection_id, DriveError('gcloud_request', 'Google 연결을 완료하지 못했습니다. 기존 설정과 사본을 보존합니다.'))
            finally:
                with self.lock:
                    self.flows.pop(connection_id, None)

        with self.lock:
            if self.stopped.is_set() or self.flows:
                raise DriveError('auth_pending', 'Google 연결 상태를 다시 확인해 주세요.')
            thread = threading.Thread(target=login, name='drive-gcloud-login', daemon=True)
            self.flows[connection_id] = thread
            thread.start()

    def stop(self):
        self.stopped.set()
        with self.lock:
            processes, threads = list(self.processes.values()), list(self.flows.values())
        for process in processes:
            self._terminate(process)
        for thread in threads:
            thread.join(timeout=5)
        with self.lock:
            self.tokens.clear()
