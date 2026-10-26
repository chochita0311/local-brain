"""Periodic collection of registered Session sources."""

from .preferences import PreferencesError
from .session_sources import load_session_source_settings
from .source_sync import SourceSyncService


class SessionSyncService(SourceSyncService):
    kind = "session"
    label = "세션"
    source_label = "세션 소스"

    def _has_sources(self):
        sources = load_session_source_settings(self.config)
        if sources.file_error:
            raise PreferencesError("세션 소스 설정을 읽지 못했습니다. 설정에서 확인해 주세요.")
        return any(entry.enabled for entry in sources.entries)
