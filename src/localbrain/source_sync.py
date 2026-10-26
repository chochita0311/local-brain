"""Shared completion-based scheduling for independent local source domains."""

import json
import sqlite3
import threading
import time

from .local_operations import OperationBusy, operation_lock, operation_active
from .preferences import PreferencesError, effective_preferences, atomic_private_write


class SourceSyncService:
    kind = ""
    label = ""
    source_label = ""

    def _has_sources(self):
        raise NotImplementedError

    def __init__(self, config, scanner):
        self.config, self.scanner = config, scanner
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._request = threading.Event()
        self._thread = None
        self._progress = None
        self._error = None
        self._requested_at = None
        self._guard = threading.Lock()

    def _read(self):
        path = self.config.data_dir / (self.kind + "-sync-state.json")
        try:
            value = json.loads(path.read_text())
            return value if isinstance(value, dict) else {}
        except (FileNotFoundError, ValueError):
            # Rebuildable health state never changes imported data or preferences.
            return {}

    def _write(self, value):
        atomic_private_write(self.config.data_dir / (self.kind + "-sync-state.json"),
                             json.dumps(value, ensure_ascii=False).encode())

    def start(self):
        with self._guard:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._loop, name=self.kind + "-sync", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        self._wake.set()
        # A completed source transaction is the checkpoint. Never leave a writer
        # alive while app shutdown claims the backend has stopped.
        if self._thread:
            self._thread.join()

    def changed(self):
        self._wake.set()

    def request(self):
        if not self.status()["running"]:
            self._requested_at = time.time()
            self._request.set()
            self.start()
            self._wake.set()
        return self.status()

    def status(self):
        state = self._read()
        error = self._error
        try:
            preferences = effective_preferences(self.config)
        except PreferencesError as exc:
            preferences = {self.kind + "_sync_enabled": False, self.kind + "_sync_minutes": 10}
            error = str(exc)
        running = bool(state.get("running") and operation_active(self.config))
        completed = state.get("completed_at", 0)
        due = completed + preferences[self.kind + "_sync_minutes"] * 60
        try:
            has_sources = self._has_sources()
        except (PreferencesError, OSError, sqlite3.Error):
            has_sources = False
            error = error or self.source_label + " 설정을 확인해 주세요."
        return {**state, "running": running, "queued": self._request.is_set(),
                "enabled": preferences[self.kind + "_sync_enabled"],
                "minutes": preferences[self.kind + "_sync_minutes"],
                "next_at": max(due, time.time()) if preferences[self.kind + "_sync_enabled"] and has_sources and not running else None,
                "progress": self._progress, "error": error or state.get("error")}

    def _loop(self):
        while not self._stop.is_set():
            try:
                preferences = effective_preferences(self.config)
                state = self._read()
                explicit = self._request.is_set()
                due = time.time() >= state.get("completed_at", 0) + preferences[self.kind + "_sync_minutes"] * 60
                if explicit or (preferences[self.kind + "_sync_enabled"] and due):
                    if self._has_sources():
                        self._collect(explicit)
                    else:
                        self._request.clear()
                self._error = None
            except OperationBusy:
                # Another domain may own the writer. Retain one request until
                # our own completion clock can confirm that it was satisfied.
                pass
            except (PreferencesError, OSError, sqlite3.Error) as error:
                self._error = str(error) if isinstance(error, PreferencesError) else "동기화 상태를 확인하지 못했습니다."
                self._request.clear()
            self._wake.wait(5)
            self._wake.clear()

    def _collect(self, explicit):
        with operation_lock(self.config, self.kind + "-sync"):
            previous = self._read()
            preferences = effective_preferences(self.config)
            # A different backend can finish after a click but before this
            # worker observes the lock. That completion satisfies the request.
            if explicit and self._requested_at is not None and previous.get("completed_at", 0) >= self._requested_at:
                self._request.clear()
                return
            # Another backend may have completed while this one acquired the lock.
            if not explicit and (not preferences[self.kind + "_sync_enabled"] or
                time.time() < previous.get("completed_at", 0) + preferences[self.kind + "_sync_minutes"] * 60):
                return
            state = {**previous, "running": True, "started_at": time.time(), "error": None}
            self._write(state)
            self._request.clear()
            try:
                def progress(event):
                    self._progress = event
                report = self.scanner(progress=progress, cancelled=self._stop.is_set)
                finished = time.time()
                state.update(report=report, outcome=report.get("outcome", "failed"))
                if state["outcome"] == "complete":
                    state["last_success_at"] = finished
                if state["outcome"] != "complete":
                    state["error"] = "일부 소스를 가져오지 못했습니다. " + self.source_label + "의 상태를 확인해 주세요."
                state["generation"] = previous.get("generation", 0) + 1
            except Exception:
                state.update(outcome="failed", error=self.label + "을 가져오지 못했습니다. 기존 기록은 보존했습니다.")
            finally:
                self._progress = None
                state.update(running=False, completed_at=time.time())
                self._write(state)
