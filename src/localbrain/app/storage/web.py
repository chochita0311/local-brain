"""HTTP delivery for storage status, backup, restore and owned cache cleanup."""
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from localbrain.foundation.config import settings
from localbrain.foundation.operations import operation_lock
from localbrain.foundation.preferences import PreferencesError
from localbrain.app.storage.recovery import (
    MAX_BACKUP_BYTES, storage_status, create_backup, validate_backup, clear_owned_cache,
)


def install_storage_routes(app):
    @app.get("/api/settings/storage")
    def storage():
        from localbrain.foundation.paths import home_relative_path
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
        from localbrain.app.settings import payload
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
        return clear_owned_cache(
            request.app.state.natural_search,
            maintain_feature_cache=request.app.state.maintain_feature_cache,
        )
