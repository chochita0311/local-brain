"""Shared value and filesystem boundaries for both sync directions."""

import os
import re
import stat
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

MAX_FILE_BYTES = 100_000_000
PUBLISH_WORKERS = 8
INTERVALS = (15, 30, 60, 180, 360, 720, 1440)
FOLDER = "application/vnd.google-apps.folder"
SCOPES = ("https://www.googleapis.com/auth/drive",)


class DriveError(Exception):
    """Safe, actionable text; never include raw Google responses or credentials."""

    def __init__(self, code, message, retryable=False):
        super().__init__(message)
        self.code, self.retryable = code, retryable


def root_url(value):
    try:
        parsed = urlsplit(value)
        match = re.fullmatch(r"/drive/(?:u/\d+/)?folders/([A-Za-z0-9_-]+)/*", parsed.path)
        if parsed.scheme != "https" or parsed.netloc != "drive.google.com" or not match:
            raise ValueError()
        key = parse_qs(parsed.query).get("resourcekey", [""])[0]
        if key and not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise ValueError()
        return match[1], key
    except (TypeError, ValueError):
        raise DriveError("invalid_url", "전체 Google Drive 폴더 URL을 입력해 주세요.") from None


def safe_name(value):
    if (not isinstance(value, str) or not value or value in (".", "..")
            or any(ord(c) < 32 or c in "/\\\x7f" for c in value)
            or value.rstrip(" .") != value):
        raise DriveError("unsafe_path", "안전한 파일·폴더 이름으로 처리할 수 없습니다.")
    return value


def name_key(value):
    return unicodedata.normalize("NFC", safe_name(value)).casefold()


def interval(value):
    if type(value) is not int or value not in INTERVALS:
        raise DriveError("invalid_interval", "지원하는 동기화 주기를 선택해 주세요.")
    return value


def next_slot(now, minutes, zone):
    """Strictly future real instant; UTC iteration also handles DST gaps/folds."""
    interval(minutes)
    tz = ZoneInfo(zone)
    utc = now.astimezone(timezone.utc).replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(3 * 1440):
        local = utc.astimezone(tz)
        if (local.hour * 60 + local.minute) % minutes == 0:
            return utc
        utc += timedelta(minutes=1)
    raise DriveError("clock", "시간대의 다음 실행 시각을 계산하지 못했습니다.")


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def private_dir(path):
    path = Path(path)
    missing = []
    # Do not follow substituted links in any existing ancestor.
    for part in (path, *path.parents):
        if part.is_symlink():
            raise DriveError("unsafe_path", "저장 경로의 심볼릭 링크를 처리할 수 없습니다.")
        if not part.exists():
            missing.append(part)
    for part in reversed(missing):
        part.mkdir(exist_ok=True, mode=0o700)
        part.chmod(0o700)
    if not path.is_dir():
        raise DriveError("unsafe_path", "저장 폴더를 확인해 주세요.")
    path.chmod(0o700)
    return path


def local_path(root, relative):
    """Resolve an incoming path without traversing symlinks, including the leaf."""
    current = Path(root)
    if current.is_symlink():
        raise DriveError("unsafe_path", "수신 폴더의 링크를 처리할 수 없습니다.")
    for component in relative.split("/"):
        current = current / safe_name(component)
        if current.is_symlink():
            raise DriveError("unsafe_path", "수신 경로의 링크를 처리할 수 없습니다.")
    return current


def local_inventory(sources, cancelled=lambda: False):
    """All entries, including exclusions; incomplete scans cannot authorize deletes."""
    entries, errors, roots = {}, [], set()
    for source in sources:
        path = Path(source["path"])
        prefix = safe_name(path.name)
        if name_key(prefix) in roots:
            raise DriveError("duplicate_path", "선택한 항목의 최상위 이름이 겹칩니다. 이름을 구분해 주세요.")
        roots.add(name_key(prefix))
        source_id = str(source["id"])
        pending = [(path, prefix)]
        while pending:
            if cancelled():
                raise DriveError("cancelled", "동기화를 중단했습니다.")
            item, relative = pending.pop()
            key = source_id + ":" + relative
            try:
                info = item.lstat()
                kind = "folder" if stat.S_ISDIR(info.st_mode) else "file"
                error = None
                if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                    error = "링크·특수 파일은 동기화하지 않습니다."
                elif kind == "file" and info.st_size > MAX_FILE_BYTES:
                    error = "앱의 파일당 100MB 제한을 초과합니다. 기존 사본은 보존합니다."
                entry = dict(key=key, source_id=source_id, path=relative, local=str(item),
                             kind=kind, size=info.st_size, stamp=stamp(info),
                             identity=f"{info.st_dev}:{info.st_ino}:{getattr(info, 'st_birthtime', '')}",
                             error=error)
                entries[key] = entry
                if error:
                    errors.append(dict(path=relative, message=error))
                elif kind == "folder":
                    with os.scandir(item) as children:
                        batch = list(children)
                    names = set()
                    for child in batch:
                        folded = name_key(child.name)
                        if folded in names:
                            raise DriveError("duplicate_path", "파일 이름이 대소문자·문자 정규화 기준으로 겹칩니다.")
                        names.add(folded)
                        pending.append((Path(child.path), relative + "/" + child.name))
            except OSError:
                raise DriveError("local_read", "선택한 로컬 항목을 모두 읽지 못했습니다. 기존 사본을 보존합니다.") from None
    return entries, errors
