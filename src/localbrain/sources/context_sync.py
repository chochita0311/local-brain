"""Periodic collection of registered Local Context sources."""

import sqlite3
from contextlib import closing

from localbrain.sources.sync import SourceSyncService


class ContextSyncService(SourceSyncService):
    kind = "context"
    label = "문서"
    source_label = "Local Context"

    def _has_sources(self):
        with closing(sqlite3.connect(self.config.database_path)) as connection:
            return connection.execute("SELECT 1 FROM context_roots WHERE enabled = 1 LIMIT 1").fetchone() is not None
