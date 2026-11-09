"""Select verified public embedding assets without moving originals or private state."""

import json
import os
from pathlib import Path

from localbrain.foundation.config import cache_directory, settings
from localbrain.foundation.paths import home_relative_path, hub_cache_root, package_boundary
from localbrain.foundation.preferences import PreferencesError
from localbrain.foundation.validation import ExperimentError
from localbrain.models.cache import hub_repository, hub_snapshot, registration_cache_root
from localbrain.models.catalog import EMBEDDING_ASSETS, EMBEDDING_ID, EMBEDDING_REVISION
from localbrain.models.installation import embedding_inventory, model_root, registration_revision


def embedding_cache_root(config=settings):
    path = model_root("embedding", config.data_dir) / "model.json"
    if not path.exists():
        return hub_cache_root()
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError('Invalid model registration')
    if value.get("schema") == "foundry.semantic-model/v1":
        # Legacy private originals remain readable; explicit selection never moves them.
        snapshot = value.get("snapshot")
        if not isinstance(snapshot, str) or not snapshot:
            raise ValueError('Invalid model registration')
        return (path.parent.parent.parent / snapshot).resolve().parent
    return registration_cache_root(value)


def folder_status(config=settings):
    root = model_root("embedding", config.data_dir)
    try:
        path = embedding_cache_root(config)
        revision = registration_revision(root)
    except (OSError, ValueError, KeyError, ExperimentError):
        return dict(path=None, display_path="", recommended_path=home_relative_path(hub_cache_root()),
                    revision=None, error="모델 저장 위치를 확인하지 못했습니다. 앱을 다시 열어 확인해 주세요.")
    return dict(path=str(path), display_path=home_relative_path(path),
                recommended_path=home_relative_path(hub_cache_root()), revision=revision, error=None)


def selected_folder(value, config=settings):
    if not isinstance(value, str) or not value.strip() or len(value) > 4096 or any(ord(c) < 32 for c in value):
        raise PreferencesError("모델 파일을 보관할 폴더 경로를 입력해 주세요.")
    try:
        candidate = Path(value.strip()).expanduser()
        if not candidate.is_absolute():
            raise ValueError()
        candidate = candidate.resolve()
        package = package_boundary()
        if (candidate == package or package in candidate.parents
                or any((parent / '.git').exists() for parent in (candidate, *candidate.parents))):
            raise PreferencesError('앱 설치 폴더와 소스 코드 저장소 밖의 모델 전용 폴더를 선택해 주세요.')
        for private in (config.data_dir, cache_directory(config)):
            private = Path(private).resolve()
            if candidate == private or private in candidate.parents or candidate in private.parents:
                raise PreferencesError("앱 데이터·검색 캐시와 겹치지 않는 모델 전용 폴더를 선택해 주세요.")
        parent = candidate
        while not parent.exists():
            parent = parent.parent
        if not parent.is_dir() or not os.access(parent, os.R_OK | os.X_OK):
            raise OSError()
    except PreferencesError:
        raise
    except (OSError, RuntimeError, ValueError):
        raise PreferencesError("폴더 경로와 접근 권한을 확인해 주세요.") from None
    return candidate


def inspect_folder(value, config=settings):
    candidate = selected_folder(value, config)
    revision = registration_revision(model_root("embedding", config.data_dir))
    try:
        repository = hub_repository(EMBEDDING_ID, candidate)
        snapshot = repository / "snapshots" / EMBEDDING_REVISION
        complete = all((snapshot / name).is_file() for name in EMBEDDING_ASSETS)
        if complete:
            snapshot, repository = hub_snapshot(EMBEDDING_ID, EMBEDDING_REVISION,
                                                snapshot.relative_to(candidate).as_posix(), candidate)
            embedding_inventory(snapshot, repository)
        state = "valid" if complete else "missing"
    except OSError:
        state = "unreadable"
    except ExperimentError:
        state = "invalid"
    return dict(path=str(candidate), state=state, revision=revision)
