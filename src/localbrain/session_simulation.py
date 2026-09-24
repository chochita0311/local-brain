"""Replayable private simulation. Never initializes or writes the source DB."""

from __future__ import annotations

import array
import fcntl
import hashlib
import json
import math
import os
import sqlite3
import stat
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .work_reconstruction import ExperimentError, digest, eligible, require, timestamp
from .work_reconstruction_input import read_only_database

OWNER = "localbrain.session-simulation.v1"
EXTRACTION = "all-message-character-windows-with-session-context.v1"
FILES = {"owner.json", "writer.lock", "state.sqlite3", "state.sqlite3-journal",
         "report.json", "previous-report.json", "progress.json"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
 key TEXT PRIMARY KEY, id INTEGER NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chunks (
 key TEXT PRIMARY KEY, session_key TEXT NOT NULL, event_id TEXT NOT NULL,
 start INTEGER NOT NULL, end INTEGER NOT NULL, content_hash TEXT NOT NULL,
 input_hash TEXT NOT NULL, role TEXT NOT NULL, at TEXT);
CREATE INDEX IF NOT EXISTS chunks_input ON chunks(input_hash);
CREATE TABLE IF NOT EXISTS embeddings (
 namespace TEXT NOT NULL, input_hash TEXT NOT NULL, vector BLOB NOT NULL,
 PRIMARY KEY(namespace,input_hash));
"""


def now():
    return datetime.now(timezone.utc)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_file(path):
    require(not path.is_symlink() and path.is_file(), "UNOWNED_OUTPUT")
    info = path.stat()
    require(info.st_uid == os.getuid() and not info.st_mode & 0o077
            and info.st_nlink == 1, "UNOWNED_OUTPUT")


def read_json(path):
    _safe_file(path)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path, value):
    pending = path.with_name(path.name + ".pending")
    require(not pending.exists() and not pending.is_symlink(), "UNOWNED_OUTPUT")
    if path.exists() or path.is_symlink():
        _safe_file(path)
    try:
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(pending, path)
    finally:
        if pending.exists() and not pending.is_symlink():
            pending.unlink()


@contextmanager
def owned_store(folder, database, *, purge=False):
    """One source-bound private owner, with exclusive writer and finite lifetime."""
    folder, database = Path(folder), Path(database)
    repo = Path(__file__).resolve().parents[2]
    require(database.is_absolute() and database.is_file() and not database.is_symlink(), "INVALID_DATABASE")
    require(folder.is_absolute() and folder == folder.resolve() and folder != repo
            and repo not in folder.parents and folder != database.parent, "INVALID_OUTPUT")
    require(folder.parent.is_dir(), "INVALID_OUTPUT")
    binding = digest([str(database.resolve()), database.stat().st_dev, database.stat().st_ino])
    created = not folder.exists()
    if created:
        require(not purge, "NO_SIMULATION")
        folder.mkdir(mode=0o700)
    info = folder.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and not info.st_mode & 0o077, "UNOWNED_OUTPUT")
    if not created:
        marker = read_json(folder / "owner.json")
        require(marker.get("owner") == OWNER and marker.get("database") == binding, "UNOWNED_OUTPUT")
    lock = folder / "writer.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    connection = None
    try:
        _safe_file(lock)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ExperimentError("SIMULATION_BUSY") from None
        if created:
            atomic_json(folder / "owner.json", {"owner": OWNER, "database": binding,
                        "expires_at": (now() + timedelta(days=30)).isoformat()})
        # An interrupted atomic write belongs to this validated, locked owner.
        for path in folder.iterdir():
            if path.name.endswith(".pending") and path.name[:-8] in FILES:
                _safe_file(path)
                path.unlink()
            else:
                require(path.name in FILES, "UNOWNED_OUTPUT")
                _safe_file(path)
        expired = timestamp(read_json(folder / "owner.json")["expires_at"]) <= now()
        if purge or expired:
            for name in sorted(FILES - {"writer.lock", "owner.json"}):
                path = folder / name
                if path.exists():
                    _safe_file(path)
                    path.unlink()
            if purge:
                yield None
                return
        atomic_json(folder / "owner.json", {"owner": OWNER, "database": binding,
                    "expires_at": (now() + timedelta(days=30)).isoformat()})
        dbpath = folder / "state.sqlite3"
        if not dbpath.exists():
            os.close(os.open(dbpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
        _safe_file(dbpath)
        connection = sqlite3.connect(dbpath)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA secure_delete=ON")
        connection.executescript(SCHEMA)
        yield connection
    finally:
        if connection is not None:
            connection.close()
        os.close(fd)


def _date(value):
    try:
        return timestamp(value).isoformat()
    except ExperimentError:
        return None


def _status(row):
    if row["kind"] is None:
        return "excluded-missing-source"
    if row["session_class"] != "work":
        return "excluded-maintenance"
    if row["session_role"] != "primary":
        return "excluded-subsession"
    if row["index_policy"] != "full":
        return "excluded-metadata-only"
    return "eligible"


def input_text(title, role, text):
    return "Session context: {}\n{}: {}".format(title, role, text)


def inventory(database, chunk_chars, visit=None):
    """Full streamed manifest, including unknown dates and empty Sessions."""
    require(type(chunk_chars) is int and 128 <= chunk_chars <= 16000, "INVALID_CHUNK_SIZE")
    counters = Counter({name: 0 for name in (
        "total_sessions", "eligible_sessions", "excluded-maintenance_sessions",
        "excluded-subsession_sessions", "excluded-metadata-only_sessions",
        "excluded-missing-source_sessions", "excluded_nonmessage_events",
        "message_events", "empty_events", "unknown_date_events", "admitted_characters",
        "chunks", "sessions_with_text", "sessions_without_text")})
    fingerprint = hashlib.sha256()

    def emit(kind, value):
        fingerprint.update(digest([kind, value]).encode("ascii"))
        if visit:
            visit(kind, value)

    with read_only_database(database, timeout=600) as source:
        for row in source.execute("""SELECT s.id,s.source_id,s.external_id,s.title,s.session_class,
                s.session_role,s.index_policy,p.kind FROM sessions s
                LEFT JOIN sources p ON p.id=s.source_id ORDER BY p.kind,s.external_id,s.id"""):
            skey = digest([row["kind"] or "missing-source-{}".format(row["source_id"]), row["external_id"]])
            status = _status(row)
            session = {"key": skey, "id": row["id"], "title": row["title"][:300], "status": status}
            counters["total_sessions"] += 1
            counters[status + "_sessions"] += 1
            emit("session", session)
            if status != "eligible":
                continue
            nchunks = 0
            for event in source.execute("""SELECT id,role,event_type,occurred_at,
                    CASE WHEN event_type='message' AND role IN ('user','assistant')
                         THEN length(text) END AS size,
                    CASE WHEN event_type='message' AND role IN ('user','assistant')
                         THEN substr(text,1,65536) END AS prefix
                    FROM activity_events WHERE session_id=? ORDER BY sequence,id""", (row["id"],)):
                event = dict(event)
                cached_text = event.pop("prefix") or ""
                cached_start = 0
                if event["event_type"] != "message" or event["role"] not in {"user", "assistant"}:
                    counters["excluded_nonmessage_events"] += 1
                    continue
                counters["message_events"] += 1
                emit("event", event)
                if not event["size"]:
                    counters["empty_events"] += 1
                    continue
                at = _date(event["occurred_at"])
                if at is None:
                    counters["unknown_date_events"] += 1
                for start in range(0, event["size"], chunk_chars):
                    # Bounded read-ahead avoids one source lookup per small
                    # chunk while preserving the exact old character windows.
                    end = min(start + chunk_chars, event["size"])
                    if end > cached_start + len(cached_text):
                        cached_start = start
                        cached_text = source.execute("SELECT substr(text,?,65536) FROM activity_events WHERE id=?",
                                                     (start + 1, event["id"])).fetchone()[0]
                    text = cached_text[start - cached_start:end - cached_start]
                    end = start + len(text)
                    chunk = {"key": digest([skey, event["id"], start, end]), "session_key": skey,
                             "event_id": event["id"], "start": start, "end": end,
                             "content_hash": sha(text),
                             "input_hash": sha(input_text(session["title"], event["role"], text)),
                             "role": event["role"], "at": at}
                    emit("chunk", chunk)
                    counters["admitted_characters"] += len(text)
                    nchunks += 1
            counters["chunks"] += nchunks
            counters["sessions_with_text" if nchunks else "sessions_without_text"] += 1
    return {"digest": fingerprint.hexdigest(), "coverage": dict(sorted(counters.items())),
            "extraction": EXTRACTION, "chunk_chars": chunk_chars, "sampled": False}


def sync_inventory(store, database, chunk_chars):
    with store:
        store.execute("DELETE FROM chunks")
        store.execute("DELETE FROM sessions")

        def insert(kind, value):
            if kind not in {"session", "chunk"}:
                return
            table = "sessions" if kind == "session" else "chunks"
            store.execute("INSERT INTO {} ({}) VALUES ({})".format(
                table, ",".join(value), ",".join("?" for _ in value)), tuple(value.values()))

        manifest = inventory(database, chunk_chars, insert)
        store.execute("INSERT OR REPLACE INTO meta VALUES ('manifest',?)", (json.dumps(manifest),))
        store.execute("DELETE FROM embeddings WHERE input_hash NOT IN (SELECT input_hash FROM chunks)")
    return manifest


def source_texts(database, rows):
    texts = []
    with read_only_database(database) as source:
        for chunk in rows:
            row = source.execute("""SELECT substr(e.text,?,?) AS text,e.role,s.title,
                    s.session_class,s.session_role,s.index_policy,p.kind,s.external_id
                    FROM activity_events e JOIN sessions s ON s.id=e.session_id
                    JOIN sources p ON p.id=s.source_id WHERE e.id=?""",
                    (chunk["start"] + 1, chunk["end"] - chunk["start"], chunk["event_id"])).fetchone()
            require(row is not None and eligible(dict(row)) and
                    digest([row["kind"], row["external_id"]]) == chunk["session_key"] and
                    isinstance(row["text"], str) and sha(row["text"]) == chunk["content_hash"], "SOURCE_CHANGED")
            text = input_text(row["title"][:300], row["role"], row["text"])
            require(sha(text) == chunk["input_hash"], "SOURCE_CHANGED")
            texts.append(text)
    return texts


def vector_bytes(values, dimension):
    require(len(values) == dimension and all(math.isfinite(float(v)) for v in values), "INVALID_VECTOR")
    norm = math.sqrt(sum(float(v) ** 2 for v in values))
    require(norm > 0, "INVALID_VECTOR")
    return array.array("f", [float(v) / norm for v in values]).tobytes()


def load_vector(raw, dimension):
    require(len(raw) == dimension * 4, "INVALID_VECTOR")
    value = array.array("f")
    value.frombytes(raw)
    vector_bytes(value, dimension)
    return value


def describe_groups(grouping, chunks, sessions):
    """Source titles are representative labels, never generated category truth."""
    if "areas" not in grouping:  # injected synthetic grouping harness
        return {}
    by_input, by_session = {}, {s["key"]: s for s in sessions}
    for chunk in chunks:
        by_input.setdefault(chunk["input_hash"], []).append(chunk)
    membership, descriptions = Counter(), []
    for area in grouping["areas"]:
        evidence = [c for node in area["members"] for c in by_input[node]]
        related = sorted({c["session_key"] for c in evidence})
        membership.update(related)
        representative = min(evidence, key=lambda c: (c["at"] or "", c["key"]))
        descriptions.append({"area_id": area["id"], "session_keys": related,
                             "representative_title": by_session[representative["session_key"]]["title"],
                             "label_basis": "source-session-title-not-area-name",
                             "representative_chunk": representative["key"],
                             "observed_dates": sorted({c["at"] for c in evidence if c["at"]}),
                             "lifecycle": "unknown"})
    return {"areas": descriptions,
            "single_session_areas": sum(len(a["session_keys"]) == 1 for a in descriptions),
            "cross_session_areas": sum(len(a["session_keys"]) > 1 for a in descriptions),
            "sessions_in_multiple_areas": sum(n > 1 for n in membership.values())}


def simulate(database, output, encoder, *, chunk_chars=1800, batch_size=16,
             parameters=None, force=False, grouper=None):
    """The encoder is injected; tests never need model assets or private input."""
    from .session_simulation_graph import group_vectors

    require(1 <= batch_size <= 256, "INVALID_BATCH_SIZE")
    parameters = parameters or {"neighbors": 8, "similarity": 0.65,
                                 "area_resolution": 0.6, "work_resolution": 1.2, "seed": 0}
    group = grouper or group_vectors
    folder = Path(output)
    contract = encoder.contract
    namespace = digest([contract, EXTRACTION, chunk_chars])
    with owned_store(folder, database) as store:
        started = now().isoformat()
        progress = {"owner": OWNER, "state": "inventory", "started_at": started,
                    "namespace": namespace, "encoded": 0, "quality": "unassessed"}
        atomic_json(folder / "progress.json", progress)
        try:
            manifest = sync_inventory(store, database, chunk_chars)
            if force:
                with store:
                    store.execute("DELETE FROM embeddings WHERE namespace=?", (namespace,))
            # A corrupted vector is a cache miss, not a trusted done marker.
            with store:
                for row in store.execute("SELECT input_hash,vector FROM embeddings WHERE namespace=?", (namespace,)):
                    try:
                        load_vector(row["vector"], contract["dimension"])
                    except ExperimentError:
                        store.execute("DELETE FROM embeddings WHERE namespace=? AND input_hash=?",
                                      (namespace, row["input_hash"]))
            total = store.execute("SELECT count(DISTINCT input_hash) FROM chunks").fetchone()[0]
            cached = store.execute("SELECT count(*) FROM embeddings WHERE namespace=?", (namespace,)).fetchone()[0]
            progress.update(state="embedding", manifest=manifest, total_vectors=total, reused=cached)
            atomic_json(folder / "progress.json", progress)
            after = ""
            while True:
                rows = store.execute("""SELECT * FROM chunks c WHERE NOT EXISTS
                    (SELECT 1 FROM embeddings e WHERE e.namespace=? AND e.input_hash=c.input_hash)
                    AND c.input_hash>? GROUP BY input_hash ORDER BY input_hash LIMIT ?""",
                    (namespace, after, batch_size)).fetchall()
                if not rows:
                    break
                encoded = encoder.encode(source_texts(database, rows))
                require(len(encoded) == len(rows), "INVALID_VECTOR")
                with store:
                    for row, vector in zip(rows, encoded):
                        store.execute("INSERT INTO embeddings VALUES (?,?,?)", (namespace, row["input_hash"],
                                      vector_bytes(vector, contract["dimension"])))
                progress["encoded"] += len(rows)
                after = rows[-1]["input_hash"]
                progress["updated_at"] = now().isoformat()
                atomic_json(folder / "progress.json", progress)
            progress["state"] = "grouping"
            atomic_json(folder / "progress.json", progress)
            vectors = {r["input_hash"]: load_vector(r["vector"], contract["dimension"])
                       for r in store.execute("SELECT input_hash,vector FROM embeddings WHERE namespace=? ORDER BY input_hash", (namespace,))}
            grouping = group(vectors, parameters)
            require(inventory(database, chunk_chars) == manifest, "SOURCE_CHANGED")
            chunks = [dict(r) for r in store.execute("SELECT * FROM chunks ORDER BY key")]
            sessions = [dict(r) for r in store.execute("SELECT * FROM sessions ORDER BY key")]
            previous_path = folder / "report.json"
            previous = read_json(previous_path) if previous_path.exists() else None
            config = digest([namespace, parameters, grouping["engine"]])
            report = {"owner": OWNER, "created_at": now().isoformat(), "quality": "unassessed",
                      "manifest": manifest, "model": contract, "configuration": config,
                      "namespace": namespace, "parameters": parameters,
                      "processing_complete": True, "lineage_status": "not_inferred",
                      "sessions": sessions, "chunks": chunks, "grouping": grouping,
                      "inspection": describe_groups(grouping, chunks, sessions),
                      "cache": {"reused": cached, "encoded": progress["encoded"], "total": total},
                      "comparison": {"previous_available": previous is not None,
                                     "same_input": previous is not None and previous["manifest"] == manifest,
                                     "same_configuration": previous is not None and previous["configuration"] == config,
                                     "same_grouping": previous is not None and previous["grouping"] == grouping}}
            if previous:
                require(previous.get("owner") == OWNER, "UNOWNED_OUTPUT")
                atomic_json(folder / "previous-report.json", previous)
            atomic_json(previous_path, report)
            # Retain only the current model namespace after successful publication.
            with store:
                store.execute("DELETE FROM embeddings WHERE namespace<>?", (namespace,))
            store.execute("VACUUM")
            progress.update(state="complete", finished_at=now().isoformat())
            atomic_json(folder / "progress.json", progress)
            return report
        except BaseException as error:
            progress.update(state="interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed",
                            error_code=str(error) if isinstance(error, ExperimentError) else "SIMULATION_FAILED")
            atomic_json(folder / "progress.json", progress)
            raise
