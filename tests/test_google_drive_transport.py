"""Synthetic loopback HTTP/1.1 and isolated transport/lifecycle contracts."""

import socket
import ssl
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request
from unittest.mock import Mock, patch

import urllib3

import test_google_drive as fixtures
from localbrain.google_drive.api import API
from localbrain.google_drive.policy import DriveError
from localbrain.google_drive.transport import PooledOpener, network_error


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 16

    def __init__(self):
        super().__init__(('127.0.0.1', 0), Handler)
        self.accepted = self.requests = 0
        self.lock = threading.Lock()
        self.barrier = threading.Barrier(8)

    def get_request(self):
        result = super().get_request()
        with self.lock:
            self.accepted += 1
        return result

    def handle_error(self, request, address):
        pass  # Early client close is an expected synthetic test branch.


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def setup(self):
        super().setup()
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def log_message(self, *args):
        pass

    def do_GET(self):
        with self.server.lock:
            self.server.requests += 1
        if self.path == '/drop':
            self.close_connection = True
            return
        if self.path == '/concurrent':
            self.server.barrier.wait(timeout=4)
        code = {'/redirect': 302, '/resume': 308, '/empty': 204, '/denied': 403}.get(self.path, 200)
        body = b'' if code in (204, 308) else b'x' * 1_000_000 if self.path == '/large' else b'{}'
        self.send_response(code)
        self.send_header('Content-Length', str(10 if self.path == '/truncated' else len(body)))
        if code == 302:
            self.send_header('Location', 'https://outside.example/never-follow')
        if code == 308:
            self.send_header('Range', 'bytes=0-1023')
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError:
            pass
        if self.path == '/truncated':
            self.close_connection = True

    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length', '0')))
        self.do_GET()

    do_PUT = do_POST


class PoolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = Server()
        cls.thread = threading.Thread(target=lambda: cls.server.serve_forever(poll_interval=0.02), daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(3)

    def setUp(self):
        with patch('localbrain.google_drive.transport.getproxies', return_value={}), \
             patch('localbrain.google_drive.transport.proxy_bypass', return_value=True):
            self.opener = PooledOpener(ssl.create_default_context())

    def tearDown(self):
        self.opener.close()

    def get(self, path='/ok'):
        return self.opener.open(Request(self.base + path), timeout=3)

    def test_twenty_fully_read_responses_reuse_one_actual_connection(self):
        before = self.server.accepted
        for _ in range(20):
            with self.get() as response:
                self.assertEqual(response.read(100), b'{}')
        self.assertEqual(self.server.accepted - before, 1)

    def test_sixteen_concurrent_requests_are_bounded_to_eight_actual_connections(self):
        before = self.server.accepted
        def get(_):
            with self.get('/concurrent') as response:
                return response.read(100)
        with ThreadPoolExecutor(max_workers=16) as pool:
            self.assertEqual(list(pool.map(get, range(16))), [b'{}'] * 16)
        self.assertEqual(self.server.accepted - before, 8)

    def test_early_close_does_not_drain_or_reuse_an_unread_response(self):
        before = self.server.accepted
        response = self.get('/large')
        self.assertEqual(response.read(16), b'x' * 16)
        with patch.object(response.raw, 'read', side_effect=AssertionError('unbounded drain')):
            response.close()
        with self.get() as next_response:
            self.assertEqual(next_response.read(100), b'{}')
        self.assertEqual(self.server.accepted - before, 2)

    def test_empty_body_finishes_and_reuses_connection(self):
        before = self.server.accepted
        with self.get('/empty'):
            pass
        with self.get() as response:
            self.assertEqual(response.read(100), b'{}')
        self.assertEqual(self.server.accepted - before, 1)

    def test_redirect_is_returned_as_error_without_following(self):
        before = self.server.requests
        with self.assertRaises(HTTPError) as result:
            self.get('/redirect')
        try:
            self.assertEqual(result.exception.code, 302)
        finally:
            result.exception.close()
        self.assertEqual(self.server.requests - before, 1)

    def test_uncertain_post_is_not_automatically_retried(self):
        before = self.server.requests
        with self.assertRaises(DriveError) as result:
            self.opener.open(Request(self.base + '/drop', data=b'synthetic', method='POST'), timeout=3)
        self.assertEqual(result.exception.code, 'network')
        self.assertEqual(self.server.requests - before, 1)

    def test_truncated_read_reports_network_and_releases_pool_capacity(self):
        with self.get('/truncated') as response, self.assertRaises(DriveError) as result:
            response.read(100)
        self.assertEqual(result.exception.code, 'network')
        with self.get() as response:
            self.assertEqual(response.read(100), b'{}')

    def test_close_is_idempotent_and_prevents_new_requests(self):
        with self.get() as response:
            response.read(100)
        connection = self.opener.pool.connection_from_url(self.base)
        self.opener.close()
        self.opener.close()
        self.assertIsNone(connection.pool)
        self.assertEqual(len(self.opener.pool.pools), 0)
        with self.assertRaises(DriveError) as result:
            self.get()
        self.assertEqual(result.exception.code, 'cancelled')

    def api(self, path):
        def open_(request, timeout):
            return self.opener.open(Request(self.base + path, data=request.data,
                                            headers=dict(request.header_items()), method=request.get_method()), timeout=timeout)
        return API(lambda: 'synthetic-token', opener=SimpleNamespace(open=open_), sleeper=lambda _: None)

    def test_accepted_resumable_status_keeps_headers_and_releases_connection(self):
        before = self.server.accepted
        with self.api('/resume').request('PUT', 'files/demo', raw=True, accepted=(308,)) as response:
            self.assertEqual(response.code, 308)
            self.assertEqual(response.headers.get('Range'), 'bytes=0-1023')
        self.assertEqual(self.api('/ok').request('GET', 'files/demo'), {})
        self.assertEqual(self.server.accepted - before, 1)

    def test_api_sanitizes_error_and_returns_error_body_connection(self):
        before = self.server.accepted
        with self.assertRaises(DriveError) as result:
            self.api('/denied').get('demo')
        self.assertEqual(result.exception.code, 'google_request')
        self.assertEqual(self.api('/ok').get('demo'), {})
        self.assertEqual(self.server.accepted - before, 1)

    def test_api_retains_bounded_safe_get_retries(self):
        before = self.server.requests
        with self.assertRaises(DriveError):
            self.api('/drop').get('demo')
        self.assertEqual(self.server.requests - before, 4)


class TransportConfigTests(unittest.TestCase):
    def test_pool_streaming_and_no_hidden_retry_or_redirect(self):
        context = ssl.create_default_context()
        pool = Mock()
        pool.urlopen.return_value = SimpleNamespace(status=200, headers={})
        with patch('localbrain.google_drive.transport.getproxies', return_value={}), \
             patch('localbrain.google_drive.transport.proxy_bypass', return_value=False), \
             patch('localbrain.google_drive.transport.urllib3.PoolManager', return_value=pool) as factory:
            transport = PooledOpener(context)
        factory.assert_called_once_with(num_pools=1, maxsize=8, block=True, ssl_context=context)
        transport.open(Request('https://www.googleapis.com/drive/v3/about'), timeout=7)
        options = pool.urlopen.call_args.kwargs
        self.assertEqual({k: options[k] for k in ('retries', 'redirect', 'preload_content', 'decode_content')},
                         dict(retries=False, redirect=False, preload_content=False, decode_content=False))
        self.assertEqual((options['timeout'], options['pool_timeout']), (7, 7))
        transport.close()
        pool.clear.assert_called_once()

    def test_proxy_credentials_stay_in_proxy_headers_and_trust_is_preserved(self):
        context = ssl.create_default_context()
        proxy_host = 'proxy.example:3128'
        with patch('localbrain.google_drive.transport.getproxies', return_value={'https': 'http://demo%40user:pw%3Aa@' + proxy_host}), \
             patch('localbrain.google_drive.transport.proxy_bypass', return_value=False), \
             patch('localbrain.google_drive.transport.urllib3.ProxyManager') as factory:
            transport = PooledOpener(context)
        self.assertEqual(factory.call_args.args, ('http://proxy.example:3128',))
        options = factory.call_args.kwargs
        self.assertEqual(options['proxy_headers'], urllib3.make_headers(proxy_basic_auth='demo@user:pw:a'))
        self.assertIs(options['proxy_ssl_context'], context)
        self.assertIs(options['ssl_context'], context)
        self.assertFalse(options.get('use_forwarding_for_https', False))
        transport.close()

    def test_proxy_bypass_preserves_direct_route(self):
        with patch('localbrain.google_drive.transport.getproxies', return_value={'https': 'http://proxy.example'}), \
             patch('localbrain.google_drive.transport.proxy_bypass', return_value=True), \
             patch('localbrain.google_drive.transport.urllib3.ProxyManager') as proxy, \
             patch('localbrain.google_drive.transport.urllib3.PoolManager') as direct:
            transport = PooledOpener(ssl.create_default_context())
        proxy.assert_not_called()
        direct.assert_called_once()
        transport.close()

    def test_invalid_proxy_configuration_does_not_expose_credentials(self):
        with patch('localbrain.google_drive.transport.getproxies', return_value={'https': 'http://demo:synthetic-private-password@[invalid'}), \
             patch('localbrain.google_drive.transport.proxy_bypass', return_value=False), self.assertRaises(DriveError) as result:
            PooledOpener(ssl.create_default_context())
        self.assertEqual(result.exception.code, 'network')
        self.assertNotIn('synthetic-private-password', str(result.exception))

    def test_nested_certificate_failure_is_tls_without_private_reason(self):
        original = ssl.SSLCertVerificationError('synthetic private issuer')
        result = network_error(urllib3.exceptions.SSLError(original))
        self.assertEqual(result.code, 'tls')
        self.assertFalse(result.retryable)
        self.assertNotIn('synthetic private issuer', str(result))

    def test_api_closes_owned_transport_but_not_injected_opener(self):
        owned, injected = Mock(), Mock()
        with patch('localbrain.google_drive.api.google_opener', return_value=owned):
            API(lambda: 'synthetic').close()
        owned.close.assert_called_once()
        API(lambda: 'synthetic', opener=injected).close()
        injected.close.assert_not_called()


class LifecycleTests(fixtures.TempCase):
    def test_identity_check_closes_transport_on_success_and_error(self):
        service = fixtures.ServiceTests.service(self)
        for failure in (False, True):
            with self.subTest(failure=failure), patch('localbrain.google_drive.service.API') as google:
                google.return_value.about.return_value = {'permissionId': 'demo'}
                if failure:
                    google.return_value.about.side_effect = DriveError('network', 'Synthetic failure')
                    with self.assertRaises(DriveError):
                        service._connected(self.connection['id'], 'account-one', 'synthetic-token')
                else:
                    service._connected(self.connection['id'], 'account-one', 'synthetic-token')
                google.return_value.close.assert_called_once()

    def test_browse_closes_transport_on_success_and_error(self):
        service = fixtures.ServiceTests.service(self)
        self.api.close = Mock()
        service.browse(self.connection['id'])
        self.api.close.assert_called_once()
        self.api.close.reset_mock()
        self.api.fail_listing = True
        with self.assertRaises(DriveError):
            service.browse(self.connection['id'])
        self.api.close.assert_called_once()

    def test_job_closes_after_success_partial_error_and_cancellation(self):
        service = fixtures.ServiceTests.service(self)
        cid = self.connection['id']
        service.configure(cid, 'upload', {'sources': [1], 'auto': False})
        cases = [(dict(transferred=0, changed=0, excluded=0, errors=[]), 'complete'),
                 (dict(transferred=0, changed=0, excluded=1, errors=[{'path': 'demo', 'message': 'Synthetic'}]), 'partial'),
                 (DriveError('network', 'Synthetic'), 'error'), (DriveError('cancelled', 'Synthetic'), 'stopped')]
        for outcome, expected in cases:
            self.api.close = Mock()
            with self.subTest(status=expected), patch.object(service.engine, 'publish', side_effect=outcome if isinstance(outcome, Exception) else None, return_value=outcome):
                service.run(cid, 'upload')
                service.worker.join(4)
                self.assertFalse(service.worker.is_alive())
                self.assertEqual(self.store.jobs(cid)['upload']['status'], expected)
                self.api.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
