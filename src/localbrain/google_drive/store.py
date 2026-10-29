"""Private, versioned sync state; no OAuth credentials or collected document text."""

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager

from .policy import DriveError, private_dir, root_url, safe_name


class Manifest(dict):
    """Track structural changes without rewriting every unchanged file checkpoint."""
    def __init__(self, values=()):
        super().__init__(values)
        self.dirty = set()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.dirty.add(key)

    def pop(self, key, *default):
        self.dirty.add(key)
        return super().pop(key, *default)


class Store:
    def __init__(self, data_dir):
        self.root = private_dir(data_dir / "google-drive")
        self.path = self.root / "sync.sqlite3"
        if self.path.is_symlink():
            raise DriveError("unsafe_path", "동기화 상태 파일의 링크를 처리할 수 없습니다.")
        self.lock = threading.RLock()
        with self.db() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise DriveError("state_version", "지원하지 않는 Drive 상태 버전입니다. 기존 상태를 보존합니다.")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS items (
                    namespace TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
                    PRIMARY KEY(namespace,key)
                );
                PRAGMA user_version=1;
            """)
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        with self.lock:
            db = sqlite3.connect(self.path, timeout=10)
            try:
                with db:
                    yield db
            finally:
                db.close()

    def get(self, key, default=None):
        with self.db() as db:
            row = db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, key, value):
        with self.db() as db:
            db.execute("INSERT INTO state VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                       (key, json.dumps(value, ensure_ascii=False)))

    def connections(self):
        return self.get("connections", [])

    def connection(self, connection_id):
        for item in self.connections():
            if item["id"] == connection_id:
                return item
        raise DriveError("missing_connection", "저장된 연결을 선택해 주세요.")

    def add(self, url, target):
        root_id, key = root_url(url)
        safe_name(target)
        with self.lock:
            connections = self.connections()
            if any(c["root_id"] == root_id for c in connections):
                raise DriveError("duplicate_root", "이미 등록한 루트입니다. 기존 연결을 선택해 주세요.")
            connection = dict(id=uuid.uuid4().hex, url=url, root_id=root_id, resource_key=key,
                              target=target, target_id=None, account=None)
            connections.append(connection)
            self.put("connections", connections)
        return connection

    def update_connection(self, connection):
        with self.lock:
            self.put("connections", [connection if c["id"] == connection["id"] else c for c in self.connections()])

    def jobs(self, connection_id):
        return self.get("jobs:" + connection_id, {"upload": dict(selected=False, auto=False, interval=360, sources=[])})

    def save_jobs(self, connection_id, jobs):
        self.put("jobs:" + connection_id, jobs)

    def manifest(self, connection_id, job):
        with self.db() as db:
            rows = db.execute("SELECT key,value FROM items WHERE namespace=?", (connection_id + ":" + job,)).fetchall()
        return Manifest((key, json.loads(value)) for key, value in rows)

    def checkpoint(self, connection_id, job, entries, touched=None):
        namespace = connection_id + ":" + job
        keys = set(entries.dirty) if isinstance(entries, Manifest) else set(entries)
        if touched in entries:
            keys.add(touched)
        with self.db() as db:
            for key in keys:
                if key in entries:
                    db.execute("INSERT INTO items VALUES (?,?,?) ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value",
                               (namespace, key, json.dumps(entries[key], ensure_ascii=False)))
                else:
                    db.execute("DELETE FROM items WHERE namespace=? AND key=?", (namespace, key))
        if isinstance(entries, Manifest):
            entries.dirty.clear()
