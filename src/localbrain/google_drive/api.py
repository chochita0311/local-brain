"""Google Drive v3 adapter. All media is bounded and Google endpoints are pinned."""

import hashlib
import json
import random
import re
import socket
import ssl
import sys
import time
import uuid
from email import policy
from email.parser import BytesParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request

from .policy import DriveError, FOLDER, MAX_FILE_BYTES
from .transport import PooledOpener

BASE = "https://www.googleapis.com/drive/v3/"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
BATCH = "https://www.googleapis.com/batch/drive/v3"
FIELDS = "id,name,mimeType,parents,size,md5Checksum,sha256Checksum,version,trashed,resourceKey,driveId,capabilities,appProperties"
MULTIPART_BYTES = 5_000_000


def google_opener():
    if sys.platform == "darwin" and sys.version_info >= (3, 10):
        import truststore
        # Use the Mac's trusted CAs without changing SSL behavior app-wide.
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    else:
        context = ssl.create_default_context()
    return PooledOpener(context)


def api_error(status, body, operation):
    try:
        reason = body.get("error", {}).get("errors", [{}])[0].get("reason", "")
    except (AttributeError, IndexError, TypeError):
        reason = ""
    if status == 401:
        return DriveError("reauth", "Google 연결을 다시 확인해 주세요. 필요한 경우 다시 로그인해 주세요.")
    if status == 429 or reason in ("rateLimitExceeded", "userRateLimitExceeded", "dailyLimitExceeded"):
        return DriveError("rate_limit", "Google API 호출 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.", True)
    if status >= 500:
        return DriveError("google_service", "Google Drive 요청을 완료하지 못했습니다. 잠시 후 다시 시도해 주세요.", True)
    if status == 404:
        return DriveError("unavailable", "현재 Google 계정으로 이 폴더·파일을 확인할 수 없습니다. URL과 공유 권한을 확인해 주세요.")
    if reason == "insufficientFilePermissions":
        labels = {"create": "새 폴더·파일을 추가", "update": "파일을 수정", "rename": "항목의 이름을 변경", "move": "항목을 이동", "restore": "항목을 복원", "trash": "항목을 휴지통으로 이동"}
        return DriveError("permission", f"이 위치에서 {labels.get(operation, '요청한 작업을 실행')}할 수 없습니다. 대상의 편집 권한을 확인해 주세요.")
    if reason in ("storageQuotaExceeded", "teamDriveFileLimitExceeded"):
        return DriveError("google_quota", "Google Drive 저장 한도를 확인해 주세요.")
    if reason in ("insufficientPermissions", "appNotAuthorizedToFile"):
        return DriveError("scope", "gcloud 로그인에 Drive 접근 권한이 필요합니다. Google 로그인을 다시 진행해 주세요.")
    return DriveError("google_request", "Google Drive 요청을 완료하지 못했습니다. 대상과 앱 권한을 확인해 주세요.")


class API:
    def __init__(self, token, resource_keys=None, opener=None, cancel=lambda: False, sleeper=time.sleep, refresh=None):
        self.token = token
        self.keys = dict(resource_keys or {})
        self.root_keys = set(self.keys)
        self.opener = opener or google_opener()
        self.owns_opener = opener is None
        self.cancel, self.sleeper = cancel, sleeper
        self.refresh = refresh
        self.ids = []
        self.metadata_cache = {}

    def close(self):
        if self.owns_opener:
            self.opener.close()

    def check(self):
        if self.cancel():
            raise DriveError("cancelled", "동기화를 중단했습니다.")

    def request(self, method, path, query=None, data=None, headers=None, operation="read", raw=False, accepted=(), resource_ids=()):
        url = path if path.startswith("https://") else BASE + path
        parsed = urlsplit(url)
        allowed = parsed.path.startswith(("/drive/v3/", "/upload/drive/v3/")) or (method == "POST" and url == BATCH)
        if parsed.scheme != "https" or parsed.netloc != "www.googleapis.com" or not allowed:
            raise DriveError("endpoint", "Google API 주소를 확인하지 못했습니다.")
        if query:
            url += ("&" if "?" in url else "?") + urlencode(query)
        body = json.dumps(data).encode() if isinstance(data, dict) else data
        for attempt in range(4):
            self.check()
            request_headers = {"Authorization": "Bearer " + self.token(), **(headers or {})}
            if isinstance(data, dict):
                request_headers["Content-Type"] = "application/json; charset=utf-8"
            if self.keys:
                relevant = self.root_keys | {parsed.path.rsplit("/", 1)[-1]} | set(resource_ids)
                relevant.update(re.findall(r"'([A-Za-z0-9_-]+)'", (query or {}).get("q", "")))
                if isinstance(data, dict):
                    relevant.update(data.get("parents", []))
                for name in ("addParents", "removeParents"):
                    relevant.update((query or {}).get(name, "").split(","))
                request_headers["X-Goog-Drive-Resource-Keys"] = ",".join(f"{key}/{self.keys[key]}" for key in relevant if self.keys.get(key))
            try:
                response = self.opener.open(Request(url, data=body, headers=request_headers, method=method), timeout=30)
                if raw:
                    return response
                with response:
                    return json.loads(response.read(4_000_000))
            except HTTPError as error:
                if error.code in accepted:
                    if raw:
                        return error
                    error.close()
                    return {}
                try:
                    payload = json.loads(error.read(65536))
                except (ValueError, OSError, DriveError):
                    payload = {}
                finally:
                    error.close()
                result = api_error(error.code, payload, operation)
                if error.code == 401 and attempt == 0 and self.refresh:
                    self.refresh()
                    continue
            except (URLError, OSError, socket.timeout) as error:
                if isinstance(getattr(error, "reason", error), ssl.SSLCertVerificationError):
                    result = DriveError("tls", "Google 연결의 인증서를 확인하지 못했습니다. 이 기기의 신뢰 인증서와 네트워크 설정을 확인해 주세요.")
                else:
                    result = DriveError("network", "Google Drive에 연결하지 못했습니다. 연결 상태를 확인해 주세요.", True)
            except (ValueError, TypeError):
                result = DriveError("response", "Google Drive 응답을 확인하지 못했습니다. 기존 사본을 보존합니다.")
            except DriveError as error:
                result = error
            # PUT media may have partially committed; upload() queries its session
            # before resending. Arbitrary POST creation is never blindly retried.
            if not result.retryable or method not in ("GET", "PATCH") or attempt == 3:
                raise result
            self.sleeper(min(8, 2 ** attempt) + random.random())
        raise result

    def about(self):
        return self.request("GET", "about", {"fields": "user"})["user"]

    def get(self, file_id):
        self.check()
        if file_id in self.metadata_cache:
            value = self.metadata_cache.pop(file_id)
            if isinstance(value, DriveError):
                raise value
            return value
        value = self.request("GET", "files/" + self.identifier(file_id), {"fields": FIELDS, "supportsAllDrives": "true"})
        if value.get("resourceKey"):
            self.keys[value["id"]] = value["resourceKey"]
        return value

    def invalidate(self, file_ids):
        """Discard descendants observed before their parent was restored."""
        for file_id in file_ids:
            self.metadata_cache.pop(file_id, None)

    def prefetch(self, file_ids, progress=lambda completed, total: None):
        """One-use metadata snapshots; unknown batches retain individual GET semantics."""
        self.check()
        identifiers = list(dict.fromkeys(self.identifier(value) for value in file_ids))
        self.metadata_cache.clear()
        completed = 0
        for start in range(0, len(identifiers), 100):
            self.check()
            batch = identifiers[start:start + 100]
            boundary = "localbrain_" + uuid.uuid4().hex
            expected, parts = {}, []
            for index, file_id in enumerate(batch):
                content_id = "localbrain-" + str(index)
                expected["response-" + content_id] = file_id
                path = "/drive/v3/files/" + file_id + "?" + urlencode(dict(fields=FIELDS, supportsAllDrives="true"))
                keys = self.root_keys | {file_id}
                key_header = ",".join(key + "/" + self.keys[key] for key in keys if self.keys.get(key))
                headers = "X-Goog-Drive-Resource-Keys: " + key_header + "\r\n" if key_header else ""
                parts.append((f"--{boundary}\r\nContent-Type: application/http\r\nContent-ID: <{content_id}>\r\n\r\n"
                              f"GET {path} HTTP/1.1\r\n{headers}\r\n").encode())
            body = b"".join(parts) + f"--{boundary}--\r\n".encode()
            try:
                response = self.request("POST", BATCH, data=body,
                                        headers={"Content-Type": "multipart/mixed; boundary=" + boundary}, raw=True)
                with response:
                    raw = response.read(8_000_001)
                    content_type = response.headers.get("Content-Type", "")
                if len(raw) > 8_000_000:
                    raise ValueError("batch response limit")
                message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\n\r\n").encode() + raw)
                if message.get_content_type() != "multipart/mixed" or not message.is_multipart() or message.defects:
                    raise ValueError("invalid batch")
                values, seen, reauth = {}, set(), False
                for part in message.iter_parts():
                    content_id = str(part.get("Content-ID", "")).strip().strip("<>")
                    if content_id not in expected or content_id in seen or part.get_content_type() != "application/http":
                        raise ValueError("unknown batch part")
                    seen.add(content_id)
                    header, payload = re.split(br"\r?\n\r?\n", part.get_payload(decode=True), maxsplit=1)
                    status = re.match(br"HTTP/\d(?:\.\d)?\s+(\d{3})\b", header)
                    if not status:
                        raise ValueError("invalid part status")
                    status = int(status[1]); value = json.loads(payload)
                    file_id = expected[content_id]
                    if status == 200:
                        if not isinstance(value, dict) or value.get("id") != file_id:
                            raise ValueError("wrong batch identity")
                        values[file_id] = value
                    elif status in (403, 404):
                        error = api_error(status, value if isinstance(value, dict) else {}, "read")
                        if error.code in ("permission", "unavailable", "google_request"):
                            values[file_id] = error
                    elif status == 401:
                        reauth = True
                if seen != set(expected):
                    raise ValueError("incomplete batch")
                self.check()
                if reauth and self.refresh:
                    self.refresh()
                self.metadata_cache.update(values)
                for value in values.values():
                    if isinstance(value, dict) and value.get("resourceKey"):
                        self.keys[value["id"]] = value["resourceKey"]
                completed += len(values)
            except DriveError as error:
                if error.code in ("cancelled", "reauth", "scope", "tls"):
                    raise
            except (ValueError, TypeError, OSError):
                pass  # Each uncached ID is checked normally; absence is not deletion.
            progress(completed, len(identifiers))

    @staticmethod
    def identifier(value):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise DriveError("identifier", "Google 항목 식별자를 확인하지 못했습니다.")
        return value

    def children(self, parent):
        page, seen, result = None, set(), []
        while True:
            query = dict(q=f"'{self.identifier(parent)}' in parents and trashed = false",
                         fields=f"nextPageToken,incompleteSearch,files({FIELDS})", pageSize=1000,
                         supportsAllDrives="true", includeItemsFromAllDrives="true")
            if page:
                query["pageToken"] = page
            value = self.request("GET", "files", query)
            if value.get("incompleteSearch") or not isinstance(value.get("files"), list):
                raise DriveError("partial_listing", "폴더 목록을 모두 확인하지 못했습니다. 기존 사본을 보존합니다.")
            for item in value["files"]:
                if item.get("resourceKey"):
                    self.keys[item["id"]] = item["resourceKey"]
            result.extend(value["files"])
            page = value.get("nextPageToken")
            if not page:
                return result
            if page in seen:
                raise DriveError("partial_listing", "폴더 목록이 완전하지 않습니다. 기존 사본을 보존합니다.")
            seen.add(page)

    def new_id(self):
        if not self.ids:
            self.ids = self.request("GET", "files/generateIds", dict(count=100, space="drive", type="files")).get("ids", [])
            if not self.ids:
                raise DriveError("response", "Google 파일 식별자를 준비하지 못했습니다.")
        return self.identifier(self.ids.pop())

    def create_folder(self, file_id, name, parent):
        self.metadata_cache.pop(file_id, None)
        try:
            return self.request("POST", "files", dict(fields=FIELDS, supportsAllDrives="true"),
                                dict(id=file_id, name=name, mimeType=FOLDER, parents=[parent]), operation="create")
        except DriveError as original:
            # A lost response can leave the exact preallocated ID committed.
            try:
                existing = self.get(file_id)
            except DriveError:
                raise original from None
            if existing.get("name") == name and parent in existing.get("parents", []) and not existing.get("trashed") and existing.get("mimeType") == FOLDER:
                return existing
            raise original

    def metadata(self, file_id, name, parent, current):
        self.metadata_cache.pop(file_id, None)
        query = dict(fields=FIELDS, supportsAllDrives="true")
        operation = "restore" if current.get("trashed") else "rename"
        if current.get("parents") != [parent]:
            query.update(addParents=parent, removeParents=",".join(current.get("parents", [])))
            operation = "move"
        return self.request("PATCH", "files/" + self.identifier(file_id), query, dict(name=name, trashed=False), operation=operation)

    def trash(self, file_id):
        self.metadata_cache.pop(file_id, None)
        return self.request("PATCH", "files/" + self.identifier(file_id), dict(fields=FIELDS, supportsAllDrives="true"),
                            dict(trashed=True), operation="trash")

    def upload(self, file_id, name, parent, path, digest, existing, state, checkpoint, progress=lambda sent, size: None):
        """Use one small-media request, retaining recovery for prior sessions."""
        self.metadata_cache.pop(file_id, None)
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise DriveError("too_large", "앱의 파일당 100MB 제한을 초과합니다.")
        if size <= MULTIPART_BYTES and not (state.get("session") and state.get("upload_hash") == digest):
            with path.open("rb") as source:
                media = source.read(MULTIPART_BYTES + 1)
            if len(media) != size:
                raise DriveError("source_changed", "전송 전에 업로드 사본의 크기가 바뀌었습니다. 다시 비교해 주세요.")
            boundary = "localbrain_" + uuid.uuid4().hex
            metadata = dict(name=name)
            if not existing:
                metadata.update(id=file_id, parents=[parent])
            body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()
                    + json.dumps(metadata).encode() + f"\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
                    + media + f"\r\n--{boundary}--\r\n".encode())
            try:
                result = self.request("PATCH" if existing else "POST", UPLOAD + ("/" + self.identifier(file_id) if existing else ""),
                                      dict(uploadType="multipart", supportsAllDrives="true", fields=FIELDS), body,
                                      {"Content-Type": "multipart/related; boundary=" + boundary}, operation="update" if existing else "create",
                                      resource_ids=(parent, file_id))
            except DriveError as original:
                if not original.retryable and original.code != "response":
                    raise
                # An uncertain create must reconcile the assigned ID, never create a sibling.
                try:
                    result = self.get(file_id)
                except DriveError:
                    raise original from None
                if result.get("md5Checksum") != digest or int(result.get("size", -1)) != size:
                    raise original
        else:
            result = self.resumable_upload(file_id, name, parent, path, digest, existing, state, checkpoint, progress)
        if result.get("md5Checksum") != digest or int(result.get("size", -1)) != size:
            result = self.get(file_id)
        if result.get("md5Checksum") != digest or int(result.get("size", -1)) != size:
            raise DriveError("integrity", "전송한 내용의 일치를 확인하지 못했습니다. 완료로 기록하지 않습니다.")
        state.pop("session", None)
        state.pop("upload_hash", None)
        checkpoint()
        progress(size, size)
        return result

    def resumable_upload(self, file_id, name, parent, path, digest, existing, state, checkpoint, progress):
        """Persist a resumable session and probe its offset after lost responses."""
        size = path.stat().st_size
        session = state.get("session") if state.get("upload_hash") == digest else None
        needs_probe = bool(session)
        if not session:
            query = dict(uploadType="resumable", supportsAllDrives="true", fields=FIELDS)
            metadata = dict(name=name)
            url = UPLOAD + ("/" + self.identifier(file_id) if existing else "")
            if not existing:
                metadata.update(id=file_id, parents=[parent])
            response = self.request("PATCH" if existing else "POST", url, query, metadata,
                                    {"X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "application/octet-stream"},
                                    operation="update" if existing else "create", raw=True)
            with response:
                session = response.headers.get("Location", "")
            state.update(session=session, upload_hash=digest)
            checkpoint()
        def acknowledged(response):
            value = response.headers.get("Range", "")
            match = re.fullmatch(r"bytes=0-(\d+)", value) if value else None
            if value and not match:
                raise DriveError("upload_offset", "Google 업로드 진행 상태를 확인하지 못했습니다.")
            received = int(match[1]) + 1 if match else 0
            if received > size:
                raise DriveError("upload_offset", "Google 업로드 진행 상태를 확인하지 못했습니다.")
            return received

        def uploaded_file(response):
            try:
                value = json.loads(response.read(1_000_000))
                return value if isinstance(value, dict) else {}
            except ValueError:
                return {}  # Verify by the known ID when final metadata is omitted.

        failures, stalled, offset = 0, 0, 0
        while True:
            self.check()
            if needs_probe:
                response = self.request("PUT", session, data=b"", headers={"Content-Range": f"bytes */{size}"},
                                        raw=True, accepted=(308, 404, 410))
                with response:
                    status = response.code
                    if status in (200, 201):
                        return uploaded_file(response)
                    if status in (404, 410):
                        state.pop("session", None)
                        checkpoint()
                        raise DriveError("upload_expired", "업로드 세션이 만료되었습니다. 다음 실행에서 이어서 확인합니다.", True)
                    offset = acknowledged(response)
                progress(offset, size)
                needs_probe = False
            with path.open("rb") as source:
                source.seek(offset)
                chunk = source.read(min(1024 * 1024, size - offset))
            headers = {"Content-Type": "application/octet-stream"}
            if chunk:
                headers["Content-Range"] = f"bytes {offset}-{offset + len(chunk) - 1}/{size}"
            try:
                response = self.request("PUT", session, data=chunk, headers=headers, raw=True, accepted=(308,))
                with response:
                    if response.code in (200, 201):
                        return uploaded_file(response)
                    next_offset = acknowledged(response)
                if next_offset <= offset:
                    stalled += 1
                    if stalled >= 3:
                        raise DriveError("upload_stalled", "업로드 수신량이 늘지 않아 중단했습니다. 연결 상태를 확인하고 다시 실행하면 이어서 확인합니다.")
                    needs_probe = True
                    self.sleeper(2 ** (stalled - 1))
                else:
                    offset = next_offset
                    stalled = 0
                    progress(offset, size)
                failures = 0
            except DriveError as error:
                if not error.retryable or failures >= 3:
                    raise
                self.sleeper(2 ** failures + random.random())
                failures += 1
                needs_probe = True

    def download(self, metadata, destination):
        """Caller owns atomic replacement; this writes only into its private staging file."""
        if metadata.get("size") is not None and int(metadata["size"]) > MAX_FILE_BYTES:
            raise DriveError("too_large", "앱의 파일당 100MB 제한을 초과합니다. 기존 사본을 보존합니다.")
        digest, sha, total = hashlib.md5(), hashlib.sha256(), 0
        response = self.request("GET", "files/" + self.identifier(metadata["id"]), dict(alt="media", supportsAllDrives="true"), raw=True)
        with response, destination.open("wb") as output:
            while True:
                self.check()
                chunk = response.read(min(1024 * 1024, MAX_FILE_BYTES - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    raise DriveError("too_large", "수신 중 파일당 100MB 제한을 초과했습니다. 기존 사본을 보존합니다.")
                output.write(chunk)
                digest.update(chunk)
                sha.update(chunk)
        if metadata.get("size") is not None and total != int(metadata["size"]):
            raise DriveError("integrity", "다운로드 크기가 원격 정보와 다릅니다. 기존 사본을 보존합니다.")
        if metadata.get("md5Checksum"):
            verified = digest.hexdigest() == metadata["md5Checksum"]
        elif metadata.get("sha256Checksum"):
            verified = sha.hexdigest() == metadata["sha256Checksum"]
        else:
            verified = False
        if not verified:
            raise DriveError("integrity", "다운로드 내용의 일치를 확인하지 못했습니다. 기존 사본을 보존합니다.")
        after = self.get(metadata["id"])
        if (after.get("trashed") or after.get("version") != metadata.get("version")
                or after.get("md5Checksum") != metadata.get("md5Checksum")):
            raise DriveError("source_changed", "다운로드 중 원본이 바뀌었습니다. 다음 실행에서 다시 비교합니다.", True)
        return digest.hexdigest()
