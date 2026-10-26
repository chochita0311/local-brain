"""Consistent local backups and restart-only, same-installation recovery."""

import fcntl
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import tempfile
import uuid
import zipfile
from contextlib import contextmanager, closing
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from .config import settings, cache_directory
from .local_operations import operation_lock
from .preferences import PreferencesError, atomic_private_write, tomllib

FILES = {"localbrain.db", "settings.toml", "session-sources.toml", "natural-search.json"}
MAX_BACKUP_BYTES = 10 * 1024 ** 3


def _private_copy(source, destination):
    """Stream a recovery copy into an atomic, durable private replacement."""
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".recovery-", delete=False) as output:
        temporary = Path(output.name)
        try:
            os.fchmod(output.fileno(), 0o600)
            with source.open("rb") as original:
                shutil.copyfileobj(original, output)
            output.flush()
            os.fsync(output.fileno())
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
    fd = os.open(destination.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identity(config):
    path = config.data_dir / "installation-id"
    if not path.exists():
        atomic_private_write(path, str(uuid.uuid4()).encode())
    return path.read_text().strip()


def _allowed(name):
    # Metadata only: public weights and external originals are never archived.
    from .model_catalog import MODELS
    slugs = {value["slug"] for value in MODELS.values()}
    parts = Path(name).parts
    return name in FILES or (
        len(parts) == 3 and parts[0] == "models" and parts[1] in slugs and parts[2] in {"owner.json", "model.json"}
    ) or (len(parts) == 2 and parts[0] in slugs and parts[1] in {"owner.json", "model.json"})


def _files(config):
    from .model_catalog import MODELS
    result = [name for name in FILES if (config.data_dir / name).is_file()]
    for value in MODELS.values():
        for folder in (config.data_dir / "models" / value["slug"], config.data_dir / value["slug"]):
            for name in ("owner.json", "model.json"):
                path = folder / name
                if path.is_file():
                    result.append(path.relative_to(config.data_dir).as_posix())
    return sorted(result)


def _size(root):
    size = 0
    if root.is_symlink() or not root.exists():
        return size
    for parent, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(parent) / name).is_symlink()]
        for name in files:
            try:
                info = (Path(parent) / name).lstat()
                if stat.S_ISREG(info.st_mode):
                    size += info.st_size
            except OSError:
                continue
    return size


def storage_status(config=settings):
    from .model_cache import hub_cache_root
    root = config.data_dir
    return {"data": str(root), "data_bytes": _size(root),
            "cache": str(cache_directory(config)), "cache_bytes": _size(cache_directory(config)),
            "models": str(hub_cache_root()), "models_bytes": _size(hub_cache_root()),
            "free_bytes": shutil.disk_usage(root).free,
            "restore_pending": (root / "restore-pending.zip").is_file(),
            "recovery": str(root / "recovery")}


def create_backup(config=settings):
    with operation_lock(config, "backup"):
        identity = _identity(config)
        work = Path(tempfile.mkdtemp(prefix="backup-", dir=config.data_dir))
        try:
            hashes = {}
            for name in _files(config):
                source, target = config.data_dir / name, work / name
                parents = source.relative_to(config.data_dir).parts[:-1]
                linked_parent = any(config.data_dir.joinpath(*parents[:i]).is_symlink() for i in range(1, len(parents) + 1))
                if source.is_symlink() or linked_parent or source.stat().st_uid != os.getuid():
                    raise PreferencesError("앱이 소유하지 않은 파일이 있어 백업을 중단했습니다.")
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                if name == "localbrain.db":
                    with closing(sqlite3.connect(source)) as original, closing(sqlite3.connect(target)) as snapshot:
                        original.backup(snapshot)
                else:
                    shutil.copyfile(source, target)
                target.chmod(0o600)
                hashes[name] = _digest(target)
            manifest = {"owner": "localbrain.backup.v1", "installation": identity,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "app_schema": _digest(Path(__file__).parent / "schema.sql"), "files": hashes}
            archive = work / "LocalBrain-backup.zip"
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                bundle.writestr("manifest.json", json.dumps(manifest))
                for name in hashes:
                    bundle.write(work / name, name)
            archive.chmod(0o600)
            return work, archive
        except Exception:
            shutil.rmtree(work)
            raise


def validate_backup(archive, target, config=settings):
    try:
        with zipfile.ZipFile(archive) as bundle:
            items = bundle.infolist()
            names = [item.filename for item in items]
            if len(names) != len(set(names)) or len(names) > 100 or sum(item.file_size for item in items) > MAX_BACKUP_BYTES:
                raise ValueError()
            if any(name != "manifest.json" and not _allowed(name) for name in names):
                raise ValueError()
            if any(stat.S_ISLNK(item.external_attr >> 16) or item.is_dir() for item in items):
                raise ValueError()
            if bundle.getinfo("manifest.json").file_size > 65536:
                raise ValueError()
            manifest = json.loads(bundle.read("manifest.json"))
            if manifest.get("owner") != "localbrain.backup.v1" or manifest.get("installation") != _identity(config):
                raise PreferencesError("이 Mac의 현재 LocalBrain에서 만든 백업만 복원할 수 있습니다.")
            if manifest.get("app_schema") != _digest(Path(__file__).parent / "schema.sql"):
                raise PreferencesError("현재 앱과 데이터베이스 스키마가 다른 백업입니다. 원래 버전에서 복원해 주세요. 현재 데이터는 보존했습니다.")
            hashes = manifest.get("files", {})
            if set(hashes) != set(names) - {"manifest.json"} or "localbrain.db" not in hashes:
                raise ValueError()
            for name, expected in hashes.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with bundle.open(name) as source, path.open("wb") as output:
                    shutil.copyfileobj(source, output)
                path.chmod(0o600)
                if _digest(path) != expected:
                    raise ValueError()
            with closing(sqlite3.connect(target / "localbrain.db")) as db:
                if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError()
                tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not {"sessions", "sources", "context_roots"} <= tables or db.execute("PRAGMA foreign_key_check").fetchone():
                    raise ValueError()
            for name, versions in (("settings.toml", (1,)), ("session-sources.toml", (1, 2))):
                if (target / name).exists() and tomllib.loads((target / name).read_text()).get("schema_version") not in versions:
                    raise ValueError()
            return hashes
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, sqlite3.Error) as error:
        if isinstance(error, PreferencesError):
            raise
        raise PreferencesError("유효한 LocalBrain 백업이 아닙니다. 현재 데이터는 바꾸지 않았습니다.") from error


@contextmanager
def backend_storage_lease(config=settings):
    """Recover before opening databases; other running backends prevent restore."""
    config.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(config.data_dir / "backend.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        pending = config.data_dir / "restore-pending.zip"
        if pending.exists():
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise PreferencesError("복원을 위해 다른 LocalBrain 앱과 웹 서버를 종료한 후 다시 실행해 주세요.") from None
            _apply_restore(pending, config)
        fcntl.flock(fd, fcntl.LOCK_SH)
        yield
    finally:
        os.close(fd)


def _apply_restore(archive, config):
    with operation_lock(config, "restore"):
        recovery = config.data_dir / "recovery"
        recovery.mkdir(exist_ok=True, mode=0o700)
        journal = recovery / "active.json"
        # A crash during publication always returns to the known pre-restore copy.
        if journal.exists():
            previous = json.loads(journal.read_text())
            for name in previous["targets"]:
                saved = recovery / "before" / name
                destination = config.data_dir / name
                if saved.exists():
                    _private_copy(saved, destination)
                else:
                    destination.unlink(missing_ok=True)
            journal.unlink()
            raise PreferencesError("중단된 복원 전의 상태로 되돌렸습니다. 앱을 다시 실행해 주세요.")
        with tempfile.TemporaryDirectory(prefix="restore-", dir=config.data_dir) as temporary:
            staged = Path(temporary)
            incoming = validate_backup(archive, staged, config)
            before = recovery / "before"
            if before.exists():
                # Preserve the previous recovery as a dated app-owned backup.
                before.rename(recovery / ("before-" + uuid.uuid4().hex[:12]))
            before.mkdir(mode=0o700)
            targets = sorted(set(_files(config)) | set(incoming))
            # Flush the old WAL before copying its database file.
            with closing(sqlite3.connect(config.database_path)) as db:
                if db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] != 0:
                    raise PreferencesError("데이터베이스가 사용 중입니다. 다른 실행을 종료해 주세요.")
            for name in targets:
                source = config.data_dir / name
                if source.exists():
                    saved = before / name
                    saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    _private_copy(source, saved)
            atomic_private_write(journal, json.dumps({"targets": targets}).encode())
            try:
                for name in targets:
                    destination = config.data_dir / name
                    if name in incoming:
                        # Atomic replacement streams large databases instead of loading them in RAM.
                        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                        _private_copy(staged / name, destination)
                    else:
                        destination.unlink(missing_ok=True)
                journal.unlink()
                archive.unlink()
            except Exception:
                # Keep the journal and recovery copies; next startup rolls back.
                raise PreferencesError("복원을 마치지 못했습니다. 다음 실행에서 복원 전 상태로 되돌립니다.") from None


def clear_owned_cache(search, config=settings):
    from .natural_search.index import folder, writer, meta, OWNER
    from .natural_search.source import digest
    from .storage_layout import _tree, _inactive, maintain_derived_cache
    search.stop()
    try:
        with operation_lock(config, "cache-cleanup"):
            path = folder(config)
            removed = 0
            if path.exists():
                with writer(config):
                    stamps = _tree(path)
                    known = {"writer.lock", "index.sqlite3", "index.sqlite3-wal", "index.sqlite3-shm", "status.json",
                             "building.sqlite3", "building.sqlite3-wal", "building.sqlite3-shm"}
                    if any(p != path and (p.name not in known or p.parent != path) for p, _ in stamps):
                        raise PreferencesError("알 수 없는 파일이 있어 검색 캐시를 보존했습니다.")
                    for name in ("index.sqlite3", "building.sqlite3"):
                        index = path / name
                        if index.exists():
                            try:
                                with closing(sqlite3.connect(index.as_uri() + "?mode=ro", uri=True)) as db:
                                    metadata = meta(db)
                                if metadata.get("owner") != OWNER or metadata.get("binding") != digest(str(config.database_path.resolve())):
                                    raise ValueError()
                            except (sqlite3.Error, ValueError):
                                raise PreferencesError("검색 캐시 소유 정보를 확인하지 못해 파일을 보존했습니다.") from None
                    files = [(p, info) for p, info in stamps if p.name not in {"owner.json", "writer.lock"} and p != path]
                    if not _inactive([item for item in files]):
                        raise PreferencesError("검색 캐시가 사용 중입니다. 다른 실행을 종료해 주세요.")
                    for p, info in files:
                        if stat.S_ISREG(info.st_mode):
                            removed += info.st_size
                            p.unlink()
            result = maintain_derived_cache(cache_directory(config))
            return {"removed_bytes": removed + result["removed_bytes"]}
    finally:
        search.start()


def install_storage_routes(app):
    @app.get("/api/settings/storage")
    def storage():
        from .path_display import home_relative_path
        status = storage_status()
        status["display_paths"] = {key: home_relative_path(status[key])
                                   for key in ("data", "cache", "models")}
        return status

    @app.post("/api/settings/backup")
    def backup():
        work, archive = create_backup()
        return FileResponse(archive, filename="LocalBrain-backup.zip", media_type="application/zip",
                            background=BackgroundTask(shutil.rmtree, work))

    @app.post("/api/settings/backup/export")
    async def export_backup(request: Request):
        from .settings_web import payload
        value = await payload(request)
        raw = value.get("path")
        if not isinstance(raw, str) or not raw or len(raw) > 4096:
            raise PreferencesError("백업을 저장할 파일을 선택해 주세요.")
        target = Path(raw).expanduser()
        if not target.is_absolute() or target.suffix.lower() != ".zip" or target.is_symlink() or not target.parent.is_dir():
            raise PreferencesError("저장할 ZIP 파일의 전체 경로를 확인해 주세요.")
        def export():
            work, archive = create_backup()
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".localbrain-backup-", delete=False) as output:
                    temporary = Path(output.name)
                    os.fchmod(output.fileno(), 0o600)
                    with archive.open("rb") as source:
                        shutil.copyfileobj(source, output)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, target)
                return {"saved": True}
            finally:
                if "temporary" in locals():
                    temporary.unlink(missing_ok=True)
                shutil.rmtree(work)
        return await run_in_threadpool(export)

    @app.post("/api/settings/restore")
    async def restore(request: Request):
        if request.headers.get("x-localbrain-confirm") != "replace-after-restart":
            raise HTTPException(422, "복원 후 재시작을 확인해 주세요.")
        with tempfile.TemporaryDirectory(prefix="restore-upload-", dir=settings.data_dir) as temporary:
            archive = Path(temporary) / "backup.zip"
            size = 0
            with archive.open("wb") as output:
                os.chmod(archive, 0o600)
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > MAX_BACKUP_BYTES:
                        raise HTTPException(413, "백업 크기 한도 10GB를 넘었습니다.")
                    output.write(chunk)
            validated = Path(temporary) / "validated"
            validated.mkdir(mode=0o700)
            await run_in_threadpool(validate_backup, archive, validated)
            with operation_lock(settings, "restore-stage"):
                os.replace(archive, settings.data_dir / "restore-pending.zip")
        return {"restart_required": True}

    @app.post("/api/settings/cache/clear")
    def cache_clear(request: Request):
        return clear_owned_cache(request.app.state.natural_search)
