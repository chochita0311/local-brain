"""Explicit read-only local input for the work-reconstruction experiment."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .work_reconstruction import (
    ExperimentError, bounded_list, eligible, identifier, key, require, timestamp, validate_snapshot,
)


def ids(value, limit):
    rows = bounded_list(value, limit)
    require(all(type(i) is int and i > 0 for i in rows))
    require(len(set(rows)) == len(rows))
    return rows


def selection(value, limit):
    require(isinstance(value, dict) and set(value) <= {"id", "start", "end", "sha256", "table"})
    require(type(value.get("id")) in (int, str) and not isinstance(value["id"], bool))
    require(bool(str(value["id"])) and len(str(value["id"])) <= 500)
    require(type(value.get("start")) is int and type(value.get("end")) is int)
    require(0 <= value["start"] < value["end"] and value["end"] - value["start"] <= limit, "INPUT_LIMIT")
    sha = value.get("sha256")
    require(isinstance(sha, str) and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha))


def validate_manifest(value):
    require(isinstance(value, dict) and value.get("version") == 1)
    require(set(value) == {"version", "source_ids", "start", "end", "snapshots", "owner", "expires_at"})
    ids(value["source_ids"], 8); require(bool(value["source_ids"]))
    start, end = timestamp(value["start"]), timestamp(value["end"])
    require(start <= end)
    identifier(value["owner"]); timestamp(value["expires_at"])
    snapshots = bounded_list(value["snapshots"], 12)
    require(bool(snapshots))
    names, previous = set(), start
    for snap in snapshots:
        require(isinstance(snap, dict) and set(snap) - {"coverage"} == {
            "name", "as_of", "session_ids", "events", "documents", "items", "organization", "organization_links"})
        if "coverage" in snap:
            coverage = snap["coverage"]
            require(isinstance(coverage, dict) and set(coverage) == {"complete", "unexamined"})
            require(type(coverage["complete"]) is bool and type(coverage["unexamined"]) is int and coverage["unexamined"] >= 0)
            require(not coverage["complete"] or coverage["unexamined"] == 0)
        name = identifier(snap["name"]); require(name not in names); names.add(name)
        cutoff = timestamp(snap["as_of"]); require(previous <= cutoff <= end); previous = cutoff
        ids(snap["session_ids"], 60)
        for field, count, text_limit in (("events", 12000, 4000), ("documents", 20, 8000),
                                          ("items", 20, 8000), ("organization", 20, 2000)):
            seen = set()
            for item in bounded_list(snap[field], count):
                selection(item, text_limit)
                identity = (item.get("table", field), item["id"])
                # One bounded selection per record prevents duplicated or
                # overlapping spans from bypassing body/record limits.
                require(identity not in seen); seen.add(identity)
                if field == "organization":
                    require(item.get("table") in {"workstreams", "threads", "checkpoints"})
                else:
                    require("table" not in item)
        ids(snap["organization_links"], 200)
    return value


@contextmanager
def read_only_database(path, timeout=120):
    path = Path(path)
    require(path.is_absolute() and not path.is_symlink() and path.is_file(), "INVALID_DATABASE")
    connection = None
    try:
        connection = sqlite3.connect(path.resolve(strict=True).as_uri() + "?mode=ro", uri=True, timeout=1)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA temp_store = MEMORY")
        allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                   sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_RECURSIVE}
        connection.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
        deadline = time.monotonic() + timeout
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        connection.execute("BEGIN")
        yield connection
    except sqlite3.Error:
        raise ExperimentError("DATABASE_UNAVAILABLE") from None
    finally:
        if connection is not None:
            connection.close()


def _text(connection, table, column, column_id, choice):
    length = connection.execute("SELECT length({}) FROM {} WHERE {} = ?".format(
        column, table, column_id), (choice["id"],)).fetchone()
    require(length is not None and length[0] is not None and choice["end"] <= length[0], "SOURCE_CHANGED")
    # Table/column identifiers are exclusively constants in this module.
    row = connection.execute(
        "SELECT substr({},{},?) FROM {} WHERE {} = ?".format(column, "?", table, column_id),
        (choice["start"] + 1, choice["end"] - choice["start"], choice["id"])).fetchone()
    require(row is not None and isinstance(row[0], str), "SOURCE_UNAVAILABLE")
    require(hashlib.sha256(row[0].encode("utf-8")).hexdigest() == choice["sha256"], "SOURCE_CHANGED")
    return row[0]


def _record(choice, kind, text, at, role="document", session_id=None):
    return {"key": key("record", choice.get("table", kind), str(choice["id"])),
            "kind": kind, "role": role, "session_id": session_id, "offset": choice["start"], "at": at, "text": text}


def _in_time(value, start, cutoff):
    require(value is not None and start <= timestamp(value) <= cutoff, "OUTSIDE_TIME_SCOPE")


def load_snapshots(database, manifest):
    validate_manifest(manifest)
    results = []
    with read_only_database(database) as connection:
        for scope in manifest["snapshots"]:
            start, cutoff = timestamp(manifest["start"]), timestamp(scope["as_of"])
            data = {"version": 1, "name": scope["name"], "sessions": [], "records": [],
                    "artifacts": [], "references": [], "organization_links": [],
                    "coverage": dict(scope.get("coverage", {"complete": True, "unexamined": 0}))}
            for sid in scope["session_ids"]:
                row = connection.execute("""SELECT s.id, s.source_id, s.external_id, s.session_class,
                    s.session_role, s.index_policy, s.event_count, sources.kind AS source_key
                    FROM sessions s JOIN sources ON sources.id = s.source_id WHERE s.id = ?""", (sid,)).fetchone()
                require(row is not None and row["source_id"] in manifest["source_ids"] and eligible(dict(row)), "INELIGIBLE_SOURCE")
                data["sessions"].append({k: row[k] for k in row.keys() if k != "source_id"})
            per_session_chars, per_session_events = {}, {}
            for choice in scope["events"]:
                row = connection.execute("""SELECT id, session_id, occurred_at, event_type, role
                    FROM activity_events WHERE id = ?""", (choice["id"],)).fetchone()
                require(row is not None and row["session_id"] in scope["session_ids"] and
                        row["event_type"] == "message" and row["role"] in {"user", "assistant"}, "INELIGIBLE_SOURCE")
                _in_time(row["occurred_at"], start, cutoff)
                sid = row["session_id"]
                per_session_chars[sid] = per_session_chars.get(sid, 0) + choice["end"] - choice["start"]
                per_session_events[sid] = per_session_events.get(sid, 0) + 1
                require(per_session_chars[sid] <= 32000 and per_session_events[sid] <= 200, "INPUT_LIMIT")
                text = _text(connection, "activity_events", "text", "id", choice)
                data["records"].append(_record(choice, "session", text, row["occurred_at"], row["role"], sid))
            for choice in scope["documents"]:
                row = connection.execute("""SELECT d.id, d.imported_at,
                    r.enabled, r.readable, r.status FROM context_documents d
                    JOIN context_roots r ON r.id = d.context_root_id WHERE d.id = ?""", (choice["id"],)).fetchone()
                require(row is not None and row["enabled"] == 1 and row["readable"] == 1 and row["status"] == "ready", "INELIGIBLE_SOURCE")
                _in_time(row["imported_at"], start, cutoff)
                text = _text(connection, "context_documents", "body", "id", choice)
                data["records"].append(_record(choice, "document", text, row["imported_at"]))
            for choice in scope["items"]:
                row = connection.execute("""SELECT i.coverage,
                    coalesce(i.source_instance_id, s.source_instance_id) AS source_instance_id, e.enabled,
                    c.applied_at FROM atlassian_items i
                    JOIN atlassian_item_content c ON c.external_resource_id = i.external_resource_id
                    JOIN atlassian_sites s ON s.id = i.site_id
                    LEFT JOIN external_source_instances e ON e.id = coalesce(i.source_instance_id, s.source_instance_id)
                    WHERE i.external_resource_id = ?""", (choice["id"],)).fetchone()
                require(row is not None and row["coverage"] == "indexed" and
                        (row["source_instance_id"] is None or row["enabled"] == 1), "INELIGIBLE_SOURCE")
                _in_time(row["applied_at"], start, cutoff)
                text = _text(connection, "atlassian_item_content", "normalized_text", "external_resource_id", choice)
                data["records"].append(_record(choice, "item", text, row["applied_at"]))
            selected_workstreams = set()
            for choice in scope["organization"]:
                table = choice["table"]
                column = "summary" if table == "workstreams" else "current_goal"
                owner_column = "id" if table == "workstreams" else "workstream_id"
                row = connection.execute("SELECT updated_at, {} AS owner FROM {} WHERE id = ?".format(
                    owner_column, table), (choice["id"],)).fetchone()
                require(row is not None, "SOURCE_UNAVAILABLE"); _in_time(row["updated_at"], start, cutoff)
                selected_workstreams.add(row["owner"])
                text = _text(connection, table, column, "id", choice)
                data["records"].append(_record(choice, "organization", text, row["updated_at"], "owner"))
            for link_id in scope["organization_links"]:
                row = connection.execute("""SELECT workstream_id, entity_type, entity_id, linked_by, created_at
                    FROM workstream_links WHERE id = ?""", (link_id,)).fetchone()
                require(row is not None and row["workstream_id"] in selected_workstreams and
                        row["linked_by"] == "user" and row["entity_type"] == "session" and
                        str(row["entity_id"]) in {str(i) for i in scope["session_ids"]}, "INELIGIBLE_SOURCE")
                _in_time(row["created_at"], start, cutoff)
                data["organization_links"].append({"key": key("owner-link", link_id),
                                                    "session_id": int(row["entity_id"]), "authority": "owner"})
            _references(connection, data, scope, start, cutoff)
            validate_snapshot(data)
            results.append(data)
    return results


def _references(connection, data, scope, start, cutoff):
    from .workstream_candidates import candidate_artifact_key
    from .workflow_projection import workflow_episode_key
    artifacts = {}
    document_ids = {str(c["id"]) for c in scope["documents"]}
    item_ids = {str(c["id"]) for c in scope["items"]}
    scanned = 0
    for session in data["sessions"]:
        scan = connection.execute("SELECT status FROM session_reference_scans WHERE session_id = ?", (session["id"],)).fetchone()
        if scan is None or scan["status"] != "ok":
            data["coverage"]["complete"] = False
            data["coverage"]["unexamined"] += 1
        rows = connection.execute("""SELECT id, target_kind, target_key, normalized_url, context_document_id,
            external_resource_id, evidence_kind, read_outcome, observed_at
            FROM session_reference_evidence WHERE session_id = ? ORDER BY id LIMIT ?""",
            (session["id"], 12001 - scanned)).fetchall()
        scanned += len(rows); require(scanned <= 12000, "INPUT_LIMIT")
        for row in rows:
            if row["observed_at"] is None:
                data["coverage"]["complete"] = False; data["coverage"]["unexamined"] += 1
                continue
            if not start <= timestamp(row["observed_at"]) <= cutoff:
                continue
            if row["target_kind"] == "context_document" and str(row["context_document_id"]) not in document_ids:
                continue
            if row["target_kind"] == "atlassian_item" and str(row["external_resource_id"]) not in item_ids:
                continue
            canonical = _canonical_reference(connection, row)
            if canonical is None:
                data["coverage"]["complete"] = False; data["coverage"]["unexamined"] += 1
                continue
            kind, source_scope, identity = canonical
            artifact_key = candidate_artifact_key(kind, source_scope, identity)
            artifacts[artifact_key] = {"kind": kind, "source_scope": source_scope, "source_identity": identity,
                                       "identity_state": "resolved", "enabled": True, "is_container": False,
                                       "availability": "available", "freshness": "unknown"}
            data["references"].append({"episode_key": workflow_episode_key(session["source_key"], session["external_id"]),
                                       "artifact_key": artifact_key, "reference_identity": str(row["id"]),
                                       "evidence_kind": row["evidence_kind"], "read_outcome": row["read_outcome"],
                                       "observed_at": row["observed_at"]})
    data["artifacts"] = [artifacts[k] for k in sorted(artifacts)]


def _canonical_reference(connection, row):
    if row["target_kind"] == "context_document":
        document = connection.execute("""SELECT d.relative_path, r.path, s.kind FROM context_documents d
            JOIN context_roots r ON r.id = d.context_root_id
            JOIN sources s ON s.id = d.source_id WHERE d.id = ?""", (row["context_document_id"],)).fetchone()
        if document and document["relative_path"]:
            return "context-document", key("source-scope", document["kind"], document["path"]), document["relative_path"]
    elif row["target_kind"] == "atlassian_item":
        item = connection.execute("""SELECT i.service, i.remote_id, i.remote_key, s.normalized_domain
            FROM atlassian_items i JOIN atlassian_sites s ON s.id = i.site_id
            WHERE i.external_resource_id = ?""", (row["external_resource_id"],)).fetchone()
        if item:
            identity = item["remote_key"] if item["service"] == "jira" else item["remote_id"]
            if identity:
                return ("jira-item" if item["service"] == "jira" else "wiki-item",
                        key("source-scope", item["service"], item["normalized_domain"]), identity)
    elif row["target_kind"] == "url" and row["normalized_url"]:
        from urllib.parse import urlsplit
        try:
            parsed = urlsplit(row["normalized_url"])
            if parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password:
                return "external-resource", "persisted-normalized-url", row["normalized_url"]
        except ValueError:
            pass
    return None
