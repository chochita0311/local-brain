"""Application-owned model lifetime and coalesced refresh after normalized Sync."""

import threading

from ..model_installation import model_root, runtime_missing
from ..session_simulation import read_json
from .index import folder, prepare, read_settings, save_settings, writer_active
from .model import SearchEncoder
from .retrieval import Retriever, database_stamp


class SearchService:
    def __init__(self, config, encoder_factory=SearchEncoder):
        self.config, self.encoder_factory = config, encoder_factory
        self._model_lock = threading.Lock()
        self._encoder, self._retriever, self._profile_contract = None, None, None
        self._stop, self._wake, self._cancel = threading.Event(), threading.Event(), threading.Event()
        self._thread = None
        self._running = False
        self._last_stamp = None
        self._requested = False
        self._error = None
        self._had_index = False
        self._force = False

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._watch, name="natural-search-refresh", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._cancel.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout=30)
        if self._retriever and not self._running:
            self._retriever.close()

    def request_prepare(self):
        enabled, profile = read_settings(self.config)
        if not enabled:
            save_settings(self.config, profile)
        if not self._running:
            self._requested = True
            self._error = None
        self.start()
        self._wake.set()

    def cancel(self):
        self._requested = False
        self._cancel.set()

    def _assets_present(self):
        return (model_root("embedding", self.config.data_dir) / "model.json").is_file() and not runtime_missing()

    def engine(self):
        enabled, profile = read_settings(self.config)
        if not enabled:
            raise ValueError("SEARCH_DISABLED")
        with self._model_lock:
            contract = profile.index_contract()
            if self._encoder is None or self._profile_contract != contract:
                if not self._assets_present() and self.encoder_factory is SearchEncoder:
                    raise ValueError("SEARCH_MODEL_MISSING")
                encoder = self.encoder_factory(self.config, profile)
                if self._retriever:
                    self._retriever.close()
                self._encoder = encoder
                self._retriever = Retriever(self.config, profile, encoder)
                self._profile_contract = contract
            self._retriever.profile = profile
            return self._encoder, self._retriever, profile

    def _watch(self):
        while not self._stop.is_set():
            try:
                enabled, profile = read_settings(self.config)
                stamp = (database_stamp(self.config.database_path), tuple(sorted(profile.index_contract().items())))
                exists = (folder(self.config) / "index.sqlite3").is_file()
                lost_index = self._had_index and not exists
                if enabled and (self._requested or self._last_stamp != stamp or lost_index):
                    self._requested = False
                    self._last_stamp = stamp
                    self._running = True
                    self._cancel.clear()
                    encoder, _, profile = self.engine()
                    prepared = prepare(self.config, encoder, profile, stopped=self._cancel.is_set, force=self._force)
                    if prepared["parents"] and not self._cancel.is_set():
                        # Warm enabled search after the index check, outside the request path.
                        _ = encoder.tokenizer
                    self._force = False
                    self._error = None
                self._had_index = (folder(self.config) / "index.sqlite3").is_file()
            except InterruptedError:
                self._error = "SEARCH_INTERRUPTED"
            except Exception as error:
                code = str(error)
                self._error = code if code in {"SEARCH_MODEL_MISSING", "SEARCH_BUSY"} else "SEARCH_PREPARATION_FAILED"
                if code == "SEARCH_BUSY":
                    self._last_stamp = None
            finally:
                self._running = False
            self._wake.wait(5)
            self._wake.clear()

    def status(self):
        enabled, _ = read_settings(self.config)
        result = {"state": "disabled", "parents": 0, "eligible_parents": 0, "fragments": 0}
        status_path = folder(self.config) / "status.json"
        if enabled and status_path.is_file():
            try:
                stored = read_json(status_path)
                if not isinstance(stored, dict):
                    raise ValueError("INVALID_SEARCH_STATUS")
                result.update({key: stored[key] for key in (
                    "parents", "eligible_parents", "fragments", "encoded", "reused", "elapsed_seconds",
                    "disk_bytes", "peak_disk_bytes", "excluded_sessions", "unreadable_context_roots",
                    "empty_sessions", "empty_documents", "excluded_runtime_documents", "error") if key in stored})
                result["state"] = stored.get("state", "failed")
            except (ValueError, OSError):
                result["state"] = "failed"
        if not enabled:
            return result
        if self.encoder_factory is SearchEncoder and not self._assets_present():
            result["state"] = "model-missing"
        elif self._running or self._requested:
            result["state"] = "preparing"
        elif writer_active(self.config):
            result["state"] = "preparing"
        elif self._error and self._error != "SEARCH_BUSY":
            result.update(state="failed", error=self._error)
        elif not (folder(self.config) / "index.sqlite3").is_file():
            result["state"] = "preparing" if self._thread and self._thread.is_alive() else "partial"
        elif result["state"] == "preparing":
            result["state"] = "partial"
        elif result["state"] == "disabled":
            result["state"] = "ready"
        result["can_cancel"] = self._running and self._error != "SEARCH_BUSY"
        return result

    def search(self, query, *, page=1):
        _, retriever, _ = self.engine()
        try:
            result = retriever.search(query, page=page)
        except ValueError as error:
            if str(error) in {"SEARCH_INDEX_INCOMPATIBLE", "INVALID_SEARCH_VECTORS"}:
                self._force = True
                self._requested = True
                self._wake.set()
            raise
        if result["partial"]:
            self._requested = True
            self._wake.set()
        return result

    def evidence(self, rowid, generation):
        return self.engine()[1].evidence(rowid, generation)


def refresh_after_scan(config):
    """CLI has no surviving app worker, so finish its explicitly enabled refresh."""
    enabled, profile = read_settings(config)
    if not enabled:
        return None
    encoder = SearchEncoder(config, profile)
    return prepare(config, encoder, profile)
