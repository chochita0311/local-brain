"""Single-writer, resumable private generations with atomic reader publication."""

import fcntl
import json
import os
import sqlite3
import time
from contextlib import closing, contextmanager
from dataclasses import asdict

from localbrain.foundation.config import cache_directory
from localbrain.foundation.files import private_database, private_directory
from localbrain.foundation.private_json import atomic_json, read_json
from .molecules import Profile, molecularize
from .source import digest, read_sources

OWNER = "localbrain.natural-search.v1"
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS parents (key TEXT PRIMARY KEY, revision TEXT NOT NULL, metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS vectors (input_hash TEXT PRIMARY KEY, value BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS fragments (
    id INTEGER PRIMARY KEY, parent_key TEXT NOT NULL, ordinal INTEGER NOT NULL,
    input_hash TEXT NOT NULL, body_hash TEXT NOT NULL, text TEXT NOT NULL,
    context TEXT NOT NULL, locator TEXT NOT NULL, UNIQUE(parent_key, ordinal));
CREATE INDEX IF NOT EXISTS fragments_parent ON fragments(parent_key);
CREATE VIRTUAL TABLE IF NOT EXISTS terms USING fts5(tokens, tokenize='unicode61');
"""


def folder(config):
    return cache_directory(config) / "natural-search"


def read_settings(config):
    path = config.data_dir / "natural-search.json"
    if not path.exists():
        return False, Profile()
    value = read_json(path)
    if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("enabled"), bool):
        raise ValueError("INVALID_SEARCH_SETTINGS")
    try:
        profile = Profile(**value["profile"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("INVALID_SEARCH_SETTINGS") from None
    return value["enabled"], profile


def save_settings(config, profile=None, enabled=True):
    private_directory(config.data_dir)
    atomic_json(config.data_dir / "natural-search.json",
                {"version": 1, "enabled": enabled, "profile": asdict(profile or Profile())})


def lexical_tokens(text):
    import re
    import unicodedata
    output = []
    for word in re.findall(r"[가-힣]+|[a-z0-9_./:+-]+", unicodedata.normalize("NFKC", text).lower()):
        if re.fullmatch(r"[가-힣]+", word):
            output.extend(word[i:i + 2] for i in range(max(1, len(word) - 1)))
            if len(word) > 2:
                output.append(word)
        else:
            output.append(word)
            output.extend(part for part in re.split(r"[_./:+-]+", word) if part and part != word)
    return output


def meta(connection):
    return {row[0]: json.loads(row[1]) for row in connection.execute("SELECT key,value FROM meta")}


def set_meta(connection, **values):
    connection.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)",
                           [(key, json.dumps(value, sort_keys=True)) for key, value in values.items()])


def open_index(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError("SEARCH_INDEX_UNAVAILABLE")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def writer(config):
    root = private_directory(folder(config))
    lock = root / "writer.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_nlink != 1 or os.fstat(fd).st_uid != os.getuid():
            raise ValueError("UNOWNED_SEARCH_LOCK")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("SEARCH_BUSY") from None
        yield root
    finally:
        os.close(fd)


def writer_active(config):
    """Observe an app or CLI writer without creating a cache or trusting a PID."""
    try:
        fd = os.open(folder(config) / "writer.lock", os.O_RDWR | os.O_NOFOLLOW)
    except FileNotFoundError:
        return False
    try:
        if os.fstat(fd).st_nlink != 1 or os.fstat(fd).st_uid != os.getuid():
            raise ValueError("UNOWNED_SEARCH_LOCK")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(fd)


def prepare(config, encoder, profile, *, stopped=lambda: False, progress=None, force=False):
    import numpy as np
    started = time.monotonic()
    stats = {"state": "preparing", "parents": 0, "fragments": 0, "encoded": 0, "reused": 0,
             "context_limited": 0, "pid": os.getpid(), "started_at": time.time()}
    contract = {**encoder.contract, **profile.index_contract()}
    identity = digest(contract)
    binding = digest(str(config.database_path.resolve()))
    with writer(config) as root:
        stage, active = root / "building.sqlite3", root / "index.sqlite3"
        connection, prior = None, None

        def report():
            stats["elapsed_seconds"] = round(time.monotonic() - started, 3)
            stats["disk_bytes"] = sum(p.stat().st_size for p in root.iterdir() if p.is_file())
            stats["peak_disk_bytes"] = max(stats.get("peak_disk_bytes", 0), stats["disk_bytes"])
            atomic_json(root / "status.json", stats)
            if progress:
                progress(dict(stats))

        try:
            report()
            if stage.exists():
                with closing(open_index(stage)) as check:
                    old = meta(check)
                if old.get("owner") != OWNER or old.get("binding") != binding:
                    raise ValueError("UNOWNED_SEARCH_INDEX")
                if force or old.get("identity") != identity:
                    stage.unlink()
            private_database(stage)
            connection = sqlite3.connect(str(stage), timeout=30)
            connection.executescript(SCHEMA)
            set_meta(connection, owner=OWNER, binding=binding, identity=identity, contract=contract, complete=False)
            connection.executescript("DELETE FROM parents; DELETE FROM fragments; DELETE FROM terms;")
            connection.commit()
            if active.exists():
                prior = open_index(active)
                old = meta(prior)
                if old.get("owner") != OWNER or old.get("binding") != binding:
                    raise ValueError("UNOWNED_SEARCH_INDEX")
                if force or old.get("identity") != identity:
                    prior.close()
                    prior = None
            sources, coverage = read_sources(config)
            stats.update(coverage)
            revisions = {source.key: source.revision for source in sources}
            prior_revisions = {row["key"]: row["revision"] for row in prior.execute("SELECT key,revision FROM parents")} if prior else {}
            if prior and old.get("complete") and revisions == prior_revisions:
                # Preserve evidence URLs and avoid tokenizing an unchanged corpus.
                stats.update(parents=len(sources), fragments=old["fragments"], reused=old["fragments"],
                             state="ready" if sources else "no-data", unchanged=True,
                             context_limited=prior.execute("SELECT coalesce(sum(json_extract(locator,'$.context_limited')),0) FROM fragments").fetchone()[0])
                connection.close()
                connection = None
                stage.unlink()
                report()
                return stats
            pending = {}
            last_flush = 0

            def flush():
                nonlocal last_flush
                if stopped():
                    raise InterruptedError("SEARCH_INTERRUPTED")
                if pending:
                    vectors = encoder.encode(list(pending.values()))
                    if len(vectors) != len(pending):
                        raise ValueError("INVALID_SEARCH_VECTORS")
                    for key, vector in zip(pending, vectors):
                        value = np.asarray(vector, dtype="<f4")
                        if value.shape != (profile.dimension,) or not np.isfinite(value).all():
                            raise ValueError("INVALID_SEARCH_VECTORS")
                        norm = np.linalg.norm(value)
                        if norm <= 0:
                            raise ValueError("INVALID_SEARCH_VECTORS")
                        connection.execute("INSERT OR IGNORE INTO vectors VALUES (?,?)",
                                           (key, (value / norm).astype("<f4").tobytes()))
                    stats["encoded"] += len(pending)
                    pending.clear()
                connection.commit()
                last_flush = stats["fragments"]
                report()

            tokenizer = encoder.tokenizer if sources else None
            for source in sources:
                if stopped():
                    raise InterruptedError("SEARCH_INTERRUPTED")
                connection.execute("INSERT INTO parents VALUES (?,?,?)",
                                   (source.key, source.revision, json.dumps(source.metadata(), ensure_ascii=False)))
                if prior_revisions.get(source.key) == revisions[source.key]:
                    molecules = ({**dict(row), "input": row["context"] + "\n\n" + row["text"],
                                  "locator": json.loads(row["locator"])} for row in prior.execute(
                                      "SELECT * FROM fragments WHERE parent_key=? ORDER BY ordinal", (source.key,)))
                else:
                    molecules = molecularize(source, tokenizer, profile)
                for molecule in molecules:
                    key = molecule["input_hash"]
                    cached = connection.execute("SELECT 1 FROM vectors WHERE input_hash=?", (key,)).fetchone()
                    if cached or key in pending:
                        stats["reused"] += 1
                    else:
                        value = prior.execute("SELECT value FROM vectors WHERE input_hash=?", (key,)).fetchone() if prior else None
                        if value:
                            connection.execute("INSERT INTO vectors VALUES (?,?)", (key, value[0]))
                            stats["reused"] += 1
                        else:
                            pending[key] = molecule["input"]
                    cursor = connection.execute("""INSERT INTO fragments
                        (parent_key,ordinal,input_hash,body_hash,text,context,locator) VALUES (?,?,?,?,?,?,?)""",
                        (source.key, molecule["ordinal"], key, molecule["body_hash"], molecule["text"],
                         molecule["context"], json.dumps(molecule["locator"])))
                    words = lexical_tokens(source.title + "\n" + molecule["text"])
                    connection.execute("INSERT INTO terms(rowid,tokens) VALUES (?,?)", (cursor.lastrowid, " ".join(words)))
                    stats["fragments"] += 1
                    stats["context_limited"] += int(molecule["locator"]["context_limited"])
                    if stats["fragments"] - last_flush >= encoder.batch_size:
                        flush()
                stats["parents"] += 1
                flush()
            flush()
            connection.execute("DELETE FROM vectors WHERE input_hash NOT IN (SELECT input_hash FROM fragments)")
            set_meta(connection, complete=True, coverage=coverage, completed_at=time.time(),
                     fragments=stats["fragments"], generation=digest([identity, time.time_ns()]))
            connection.commit()
            connection.execute("VACUUM")
            connection.close()
            connection = None
            if prior:
                prior.close()
                prior = None
            os.replace(stage, active)
            stats["state"] = "ready" if sources else "no-data"
            report()
            return stats
        except BaseException as error:
            if connection:
                connection.rollback()
            stats["state"] = "failed"
            stats["error"] = "SEARCH_INTERRUPTED" if isinstance(error, (KeyboardInterrupt, InterruptedError)) else "SEARCH_PREPARATION_FAILED"
            report()
            raise
        finally:
            if connection:
                connection.close()
            if prior:
                prior.close()
