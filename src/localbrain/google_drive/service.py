"""Backend-lifetime scheduling and cached Settings state for Google Drive."""

import threading
import time
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from localbrain.foundation.preferences import effective_preferences
from .api import API
from .auth import GcloudAuth
from .engine import Engine
from .policy import DriveError, FOLDER, INTERVALS, MAX_FILE_BYTES, interval, next_slot
from .store import Store


def now_text():
    return datetime.now(timezone.utc).isoformat()


class DriveService:
    def __init__(self, config, api_factory=None, source_loader=None, auth=None):
        self.config = config
        self.store = Store(config.data_dir)
        self.engine = Engine(self.store, config.data_dir)
        self.sources = source_loader or self._sources
        self.api_factory = api_factory
        self.auth = auth or GcloudAuth(self._bound_account, self._connected, self._auth_error)
        self.lock = threading.RLock()
        self.stop_event, self.cancel_event, self.wake = threading.Event(), threading.Event(), threading.Event()
        self.active = None
        self.progress = None
        self.worker = None
        self.slots, self.queue = {}, []
        self.thread = threading.Thread(target=self._schedule, name="drive-scheduler", daemon=True)
        # An interrupted job is preserved as incomplete; startup never replays it.
        for connection in self.store.connections():
            jobs = self.store.jobs(connection["id"])
            for job in jobs.values():
                if job.get("status") == "running":
                    job.update(status="interrupted", message="이전 동기화가 중단되었습니다. 다음 정시 또는 수동 실행을 기다립니다.")
            self.store.save_jobs(connection["id"], jobs)

    def _sources(self):
        db = sqlite3.connect(self.config.database_path)
        db.row_factory = sqlite3.Row
        try:
            return [dict(s) for s in db.execute("SELECT id,label,path,source_type FROM context_roots WHERE enabled=1 AND source_type IN ('folder','file') ORDER BY id")]
        finally:
            db.close()

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.cancel_event.set()
        self.wake.set()
        self.thread.join(timeout=2)
        self.auth.stop()
        if self.worker:
            self.worker.join(timeout=40)

    def zone(self):
        return effective_preferences(self.config)["timezone"]

    def api(self, connection, cancel=lambda: False):
        if self.api_factory:
            return self.api_factory(connection, cancel)
        return API(lambda: self.auth.access_token(connection["id"]),
                   {connection["root_id"]: connection["resource_key"]}, cancel=cancel,
                   refresh=lambda: self.auth.invalidate(connection["id"]))

    def _auth_error(self, connection_id, error):
        self.health(connection_id, "auth", error)

    def _bound_account(self, connection_id):
        connection = self.store.connection(connection_id)
        return connection.get("gcloud_account") or (connection.get("account") or {}).get("emailAddress")

    def _connected(self, connection_id, account, access_token):
        if self.stop_event.is_set():
            raise DriveError("cancelled", "Google 연결을 중단했습니다.")
        with closing(API(lambda: access_token)) as api:
            user = api.about()
        if not user or not user.get("permissionId"):
            raise DriveError("account", "Google 계정 식별 정보를 확인하지 못했습니다.")
        if user.get("emailAddress") and user["emailAddress"].casefold() != account.casefold():
            raise DriveError("account_changed", "gcloud 계정과 Google 응답 계정이 다릅니다. 사용할 계정을 확인해 주세요.")
        with self.lock:
            if self.stop_event.is_set():
                raise DriveError("cancelled", "Google 연결을 중단했습니다.")
            connection = self.store.connection(connection_id)
            previous = connection.get("account")
            if previous and previous.get("permissionId") != user["permissionId"]:
                raise DriveError("account_changed", "이 연결에 사용했던 Google 계정으로 연결해 주세요. 기존 사본과 설정을 보존합니다.")
            connection["gcloud_account"] = account
            connection["account"] = {k: user.get(k) for k in ("permissionId", "displayName", "emailAddress")}
            self.store.update_connection(connection)
            self.health(connection_id, "auth")

    def health(self, connection_id, area, error=None):
        with self.lock:
            value = self.store.get("health:" + connection_id, {})
            previous = value.get(area, {})
            observation = dict(observed_at=now_text(), status="error" if error else "ok",
                               code=error.code if error else None, message=str(error) if error else "확인했습니다.")
            if error:
                observation["last_success"] = previous.get("last_success")
            else:
                observation["last_success"] = observation["observed_at"]
            value[area] = observation
            self.store.put("health:" + connection_id, value)

    def status(self):
        with self.lock:
            readiness = self.auth.status()
            connections = []
            zone = self.zone()
            now = datetime.now(timezone.utc)
            for connection in self.store.connections():
                jobs = self.store.jobs(connection["id"])
                for key, job in jobs.items():
                    slot = self.slots.get((connection["id"], key))
                    job["next_slot"] = (slot[0] if slot else next_slot(now, job["interval"], zone)).isoformat() if job.get("selected") and job.get("auto") else None
                connections.append({**connection, "jobs": jobs,
                                    "publishers": self.store.get("publishers:" + connection["id"], []),
                                    "health": self.store.get("health:" + connection["id"], {}),
                                    "auth_pending": connection["id"] in self.auth.flows})
            return dict(connections=connections, sources=[{k: source.get(k) for k in ("id", "label", "path", "source_type")} for source in self.sources()],
                        intervals=list(INTERVALS), max_file_bytes=MAX_FILE_BYTES, timezone=zone,
                        auth_mode="gcloud", auth_scope="https://www.googleapis.com/auth/drive",
                        gcloud_ready=readiness["ready"], gcloud_message=readiness["message"],
                        active={"connection_id": self.active[0], "job": self.active[1],
                                "progress": dict(self.progress) if self.progress else None} if self.active else None)

    def add(self, url, target):
        with self.lock:
            connection = self.store.add(url, target)
            self.wake.set()
            return connection

    def authenticate(self, connection_id, account=None, login=False):
        with self.lock:
            self.store.connection(connection_id)
            if self.active and self.active[0] == connection_id:
                raise DriveError("busy", "현재 동기화가 끝난 뒤 연결해 주세요.")
        try:
            if login:
                self.auth.begin(connection_id, account)
            else:
                self.auth.connect(connection_id, account)
        except DriveError as error:
            self.health(connection_id, "auth", error)
            raise

    def browse(self, connection_id):
        with self.lock:
            connection = self.store.connection(connection_id)
        try:
            with closing(self.api(connection)) as api:
                root = api.get(connection["root_id"])
                if root.get("trashed") or root.get("mimeType") != FOLDER:
                    raise DriveError("root", "사용 가능한 Google Drive 폴더 URL을 확인해 주세요.")
                children = api.children(root["id"])
                publishers = [dict(id=c["id"], name=c["name"], resource_key=c.get("resourceKey", ""))
                              for c in children if c["mimeType"] == FOLDER and c["id"] != connection.get("target_id") and c["name"] != connection["target"]]
            with self.lock:
                self.store.put("publishers:" + connection_id, publishers)
                self.store.put("root_name:" + connection_id, root["name"])
                self.health(connection_id, "api")
                self.health(connection_id, "root")
                self.health(connection_id, "auth")
            return publishers
        except DriveError as error:
            self.health(connection_id, "root", error)
            if error.code in ("reauth", "unauthenticated", "scope"):
                self.health(connection_id, "auth", error)
            else:
                self.health(connection_id, "api", error)
            raise

    def configure(self, connection_id, key, changes):
        allowed = {"auto", "interval", "sources"} if key == "upload" else {"selected", "auto", "interval"}
        if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
            raise DriveError("invalid_settings", "지원하지 않는 동기화 설정입니다.")
        for name in ("selected", "auto"):
            if name in changes and type(changes[name]) is not bool:
                raise DriveError("invalid_settings", "선택·자동 실행 상태를 확인해 주세요.")
        if "interval" in changes:
            interval(changes["interval"])
        with self.lock:
            self.store.connection(connection_id)
            jobs = self.store.jobs(connection_id)
            if key != "upload":
                choices = self.store.get("publishers:" + connection_id, [])
                if key not in jobs and key not in {"receive:" + p["id"] for p in choices}:
                    raise DriveError("publisher", "루트에서 조회한 폴더를 선택해 주세요.")
            else:
                if "sources" in changes:
                    ids = {s["id"] for s in self.sources()}
                    values = changes["sources"]
                    if not isinstance(values, list) or any(type(v) is not int or v not in ids for v in values) or len(set(values)) != len(values):
                        raise DriveError("source", "등록된 Local Context 파일·폴더를 선택해 주세요.")
            current = jobs.get(key, dict(selected=False, auto=False, interval=1440))
            current.update(changes)
            if key == "upload":
                current["selected"] = bool(current.get("sources"))
            jobs[key] = current
            self.store.save_jobs(connection_id, jobs)
            if self.active == (connection_id, key):
                self.cancel_event.set()
            self.slots.pop((connection_id, key), None)
            self.queue = [item for item in self.queue if item != (connection_id, key)]
            self.wake.set()

    def run(self, connection_id, key):
        with self.lock:
            if self.active:
                raise DriveError("busy", "진행 중인 동기화가 끝난 뒤 실행해 주세요.")
            connection = self.store.connection(connection_id)
            jobs = self.store.jobs(connection_id)
            job = jobs.get(key)
            if not job or not job.get("selected"):
                raise DriveError("selection", "동기화할 항목을 먼저 선택해 주세요.")
            if key != "upload" and not key.startswith("receive:"):
                raise DriveError("job", "지원하지 않는 동기화 대상입니다.")
            self.active = (connection_id, key)
            self.progress = dict(stage="preparing", processed=0, total=None, current="", transferred=0,
                                 changed=0, excluded=0, last_activity_at=now_text()) if key == "upload" else None
            self.cancel_event.clear()
            job.update(status="running", started_at=now_text(), message="동기화 중입니다.")
            self.store.save_jobs(connection_id, jobs)
            source_ids = set(job.get("sources", []))
            selected_sources = [s for s in self.sources() if s["id"] in source_ids]

            def progress(**values):
                with self.lock:
                    self.progress.update(values, last_activity_at=now_text())

            def work():
                try:
                    with closing(self.api(connection, lambda: self.stop_event.is_set() or self.cancel_event.is_set())) as api:
                        # A root check enforces the configured scope before any media operation.
                        root = api.get(connection["root_id"])
                        if root.get("trashed") or root.get("mimeType") != FOLDER:
                            raise DriveError("root", "설정한 공유 루트를 확인할 수 없습니다.")
                        self.health(connection_id, "api")
                        self.health(connection_id, "root")
                        self.health(connection_id, "auth")
                        if key == "upload":
                            if len(selected_sources) != len(source_ids):
                                raise DriveError("source", "선택한 Local Context 등록을 확인해 주세요. 기존 사본은 보존합니다.")
                            report = self.engine.publish(connection, selected_sources, api, progress=progress)
                        else:
                            for publisher in self.store.get("publishers:" + connection_id, []):
                                if publisher["id"] == key[8:] and publisher.get("resource_key"):
                                    api.keys[publisher["id"]] = publisher["resource_key"]
                            report = self.engine.receive(connection, key[8:], api)
                        api.check()
                    status = "partial" if report["errors"] else "complete"
                    message = "일부 항목을 갱신하지 못했습니다. 항목별 이유를 확인해 주세요." if report["errors"] else "동기화가 완료되었습니다."
                    error = None
                except DriveError as caught:
                    report, error = {}, caught
                    status = "stopped" if caught.code == "cancelled" else "error"
                    message = str(caught)
                except Exception:
                    report, error = {}, DriveError("sync", "동기화를 완료하지 못했습니다. 기존 사본과 설정을 보존합니다.")
                    status, message = "error", str(error)
                with self.lock:
                    jobs = self.store.jobs(connection_id)
                    current = jobs[key]
                    current.update(status=status, message=message, observed_at=now_text(), report=report)
                    if status == "complete":
                        current["last_success"] = current["observed_at"]
                    self.store.save_jobs(connection_id, jobs)
                    if error and error.code in ("reauth", "unauthenticated", "scope"):
                        self.health(connection_id, "auth", error)
                    self.active = None
                    self.progress = None
                    self.wake.set()

            self.worker = threading.Thread(target=work, name="drive-sync", daemon=True)
            self.worker.start()

    def schedule_once(self, now, zone, reset=False):
        """One deterministic scheduler decision; reset skips slots missed while inactive."""
        with self.lock:
            if reset:
                self.slots.clear()
                self.queue.clear()
            active_keys = set()
            for connection in self.store.connections():
                jobs = self.store.jobs(connection["id"])
                for key, job in jobs.items():
                    if not job.get("selected") or not job.get("auto"):
                        continue
                    pair = (connection["id"], key)
                    active_keys.add(pair)
                    previous = self.slots.get(pair)
                    if not previous or previous[1:] != (job["interval"], zone):
                        self.slots[pair] = (next_slot(now, job["interval"], zone), job["interval"], zone)
                        continue
                    due = previous[0]
                    if due <= now:
                        slot_key = "slot:" + ":".join(pair)
                        last = self.store.get(slot_key)
                        if (now - due).total_seconds() < 60 and (not last or due.isoformat() > last) and pair != self.active and pair not in self.queue:
                            self.queue.append(pair)
                            self.store.put(slot_key, due.isoformat())
                        self.slots[pair] = (next_slot(now, job["interval"], zone), job["interval"], zone)
            self.slots = {k: v for k, v in self.slots.items() if k in active_keys}
            if not self.active and self.queue:
                connection_id, key = self.queue.pop(0)
                self.run(connection_id, key)

    def _schedule(self):
        last_wall, last_mono, last_zone = time.time(), time.monotonic(), None
        while not self.stop_event.is_set():
            try:
                now, mono = datetime.now(timezone.utc), time.monotonic()
                zone = self.zone()
                slept = mono - last_mono > 90 or abs((now.timestamp() - last_wall) - (mono - last_mono)) > 5
                self.schedule_once(now, zone, reset=slept or last_zone != zone)
                last_wall, last_mono, last_zone = now.timestamp(), mono, zone
            except Exception:
                # Invalid preferences/state never activate sync or erase saved settings.
                pass
            self.wake.wait(0.5)
            self.wake.clear()
