"""Owned, bounded HTTP pools; streaming and Google error policy stay in the API."""

import base64
import ssl
import threading
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit, urlunsplit
from urllib.request import getproxies, proxy_bypass

import urllib3

from .policy import DriveError, PUBLISH_WORKERS


def network_error(error):
    pending, seen = [error], set()
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, ssl.SSLCertVerificationError):
            return DriveError("tls", "Google 연결의 인증서를 확인하지 못했습니다. 이 기기의 신뢰 인증서와 네트워크 설정을 확인해 주세요.")
        if isinstance(value, BaseException):
            pending.extend(value.args)
            pending.extend(getattr(value, key, None) for key in ("reason", "original_error", "__cause__"))
    return DriveError("network", "Google Drive에 연결하지 못했습니다. 연결 상태를 확인해 주세요.", True)


class Response:
    def __init__(self, raw):
        self.raw = raw
        self.headers, self.code = raw.headers, raw.status
        self.closed = False

    def read(self, size=-1):
        try:
            data = self.raw.read(None if size < 0 else size, decode_content=False)
            while size > 0 and len(data) < size and self.raw.length_remaining not in (None, 0):
                part = self.raw.read(size - len(data), decode_content=False)
                if not part:
                    raise urllib3.exceptions.ProtocolError("Incomplete response")
                data += part
            return data
        except (urllib3.exceptions.HTTPError, OSError) as error:
            self.raw.close()
            self.close()
            raise network_error(error) from None

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            # A declared empty body can finish without another network read.
            if self.raw.length_remaining == 0 and not self.raw.isclosed():
                self.raw.read(1, decode_content=False)
            if not self.raw.isclosed():
                self.raw.close()  # Never drain an unbounded discarded body.
        except (urllib3.exceptions.HTTPError, OSError):
            self.raw.close()
        finally:
            self.raw.release_conn()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class PooledOpener:
    def __init__(self, context):
        options = dict(num_pools=1, maxsize=PUBLISH_WORKERS, block=True, ssl_context=context)
        proxies = getproxies()
        proxy = proxies.get("https") if not proxy_bypass("www.googleapis.com") else None
        try:
            if proxy:
                parsed = urlsplit(proxy if "://" in proxy else "http://" + proxy)
                headers = None
                if parsed.username is not None:
                    credentials = unquote(parsed.username) + ":" + unquote(parsed.password or "")
                    headers = {"proxy-authorization": "Basic " + base64.b64encode(credentials.encode()).decode("ascii")}
                proxy = urlunsplit((parsed.scheme, parsed.netloc.rsplit("@", 1)[-1], parsed.path, parsed.query, parsed.fragment))
                self.pool = urllib3.ProxyManager(proxy, proxy_headers=headers, proxy_ssl_context=context, **options)
            else:
                self.pool = urllib3.PoolManager(**options)
        except (urllib3.exceptions.HTTPError, ValueError, OSError) as error:
            raise network_error(error) from None
        self.closed = False
        self.lock = threading.Lock()
        self.connections = set()

    def open(self, request, timeout=30):
        try:
            with self.lock:
                if self.closed:
                    raise DriveError("cancelled", "Google 연결을 중단했습니다.")
                # Close idle sockets even if a completed response retains its pool.
                self.connections.add(self.pool.connection_from_url(request.full_url))
            raw = self.pool.urlopen(request.get_method(), request.full_url, body=request.data,
                                    headers=dict(request.header_items()), timeout=timeout, pool_timeout=timeout,
                                    retries=False, redirect=False, preload_content=False, decode_content=False)
        except (urllib3.exceptions.HTTPError, OSError) as error:
            raise network_error(error) from None
        response = Response(raw)
        if not 200 <= raw.status < 300:
            raise HTTPError(request.full_url, raw.status, raw.reason, raw.headers, response)
        return response

    def close(self):
        with self.lock:
            if not self.closed:
                self.closed = True
                for connection in self.connections:
                    connection.close()
                self.connections.clear()
                self.pool.clear()
