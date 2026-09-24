"""Prediction-independent, explicit bounded sampling of an existing local index."""

from __future__ import annotations

import hashlib
from datetime import timezone

from .work_reconstruction import ExperimentError, digest, identifier, require, timestamp
from .work_reconstruction_input import load_snapshots, read_only_database, validate_manifest


SAMPLING_VERSION = "localbrain.chronological-spread.v1"


def spread(rows, count):
    """Include both chronological endpoints; never inspect words or predictions."""
    if len(rows) <= count:
        return list(rows)
    return [rows[i * (len(rows) - 1) // (count - 1)] for i in range(count)]


def _dated(rows, through, omissions):
    result = []
    for original in rows:
        row = dict(original)
        try:
            at = timestamp(row["at"])
        except ExperimentError:
            omissions.append(None)
            continue
        if at <= through:
            row["instant"] = at
            result.append(row)
    return sorted(result, key=lambda r: (r["instant"], r.get("table", ""), str(r["id"])))


def _prefix(connection, row, table, column, identity_column, maximum, omissions):
    size = row["size"] or 0
    if size <= 0:
        return None
    count = min(size, maximum)
    # Identifiers come only from this module's fixed call sites, never a manifest.
    text = connection.execute("SELECT substr({},1,?) FROM {} WHERE {}=?".format(
        column, table, identity_column), (count, row["id"])).fetchone()[0]
    require(isinstance(text, str) and len(text) == count, "SOURCE_CHANGED")
    if size > count:
        omissions.append(row["instant"])
    choice = {"id": row["id"], "start": 0, "end": count,
              "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    if "table" in row:
        choice["table"] = row["table"]
    return {"choice": choice, "instant": row["instant"], "session_id": row.get("session_id"),
            "workstream_id": row.get("workstream_id")}


def _take(rows, count, omissions):
    chosen = spread(rows, count)
    identities = {(r.get("table"), r["id"]) for r in chosen}
    omissions.extend(r["instant"] for r in rows if (r.get("table"), r["id"]) not in identities)
    return chosen


def prepare_current(database, through, owner, expires_at):
    """Freeze an explicit whole-existing-history sample; no independent labels."""
    cutoff = timestamp(through)
    identifier(owner); require(timestamp(expires_at) > cutoff, "INVALID_EXPIRY")
    omissions, events, documents, items, organization = [], [], [], [], []
    with read_only_database(database) as connection:
        # Only metadata is scanned across the population. Bodies are selected
        # after the fixed sample, permission checks, and all source-count gates.
        population = _dated(connection.execute("""SELECT id,source_id,at FROM (
            SELECT s.id,s.source_id,e.occurred_at AS at,
                row_number() OVER (PARTITION BY s.id ORDER BY julianday(e.occurred_at),e.sequence,e.id) AS ordinal
            FROM sessions s JOIN sources ON sources.id=s.source_id
            JOIN activity_events e ON e.session_id=s.id
            WHERE s.session_class='work' AND s.session_role='primary' AND s.index_policy='full'
                AND e.event_type='message' AND e.role IN ('user','assistant')
                AND (julianday(e.occurred_at)<=julianday(?) OR julianday(e.occurred_at) IS NULL)
            ) WHERE ordinal=1""", (through,)), cutoff, omissions)
        require(bool(population), "NO_ELIGIBLE_INPUT")
        sources = sorted({r["source_id"] for r in population})
        require(len(sources) <= 8, "INPUT_LIMIT")
        selected = spread(population, 60)
        session_ids = [r["id"] for r in selected]
        marks = ",".join("?" for _ in session_ids)
        for session in selected:
            rows = _dated(connection.execute("""SELECT id,session_id,occurred_at AS at,length(text) AS size
                FROM activity_events WHERE session_id=? AND event_type='message'
                AND role IN ('user','assistant')""", (session["id"],)), cutoff, omissions)
            for row in _take(rows, 32, omissions):
                value = _prefix(connection, row, "activity_events", "text", "id", 1000, omissions)
                if value:
                    events.append(value)

        doc_rows = _dated(connection.execute("""SELECT DISTINCT d.id,d.imported_at AS at,length(d.body) AS size
            FROM context_documents d JOIN context_roots r ON r.id=d.context_root_id
            JOIN session_reference_evidence e ON e.context_document_id=d.id
            WHERE r.enabled=1 AND r.readable=1 AND r.status='ready'
                AND e.session_id IN ({}) AND julianday(e.observed_at)<=julianday(?)""".format(marks),
            (*session_ids, through)), cutoff, omissions)
        for row in _take(doc_rows, 20, omissions):
            value = _prefix(connection, row, "context_documents", "body", "id", 8000, omissions)
            if value:
                documents.append(value)

        item_rows = _dated(connection.execute("""SELECT DISTINCT i.external_resource_id AS id,c.applied_at AS at,
            length(c.normalized_text) AS size FROM atlassian_items i
            JOIN atlassian_item_content c ON c.external_resource_id=i.external_resource_id
            JOIN atlassian_sites s ON s.id=i.site_id
            LEFT JOIN external_source_instances b ON b.id=coalesce(i.source_instance_id,s.source_instance_id)
            JOIN session_reference_evidence e ON e.external_resource_id=i.external_resource_id
            WHERE i.coverage='indexed' AND (coalesce(i.source_instance_id,s.source_instance_id) IS NULL OR b.enabled=1)
                AND e.session_id IN ({}) AND julianday(e.observed_at)<=julianday(?)""".format(marks),
            (*session_ids, through)), cutoff, omissions)
        for row in _take(item_rows, 20, omissions):
            value = _prefix(connection, row, "atlassian_item_content", "normalized_text", "external_resource_id", 8000, omissions)
            if value:
                items.append(value)

        links = _dated(connection.execute("""SELECT id,workstream_id,entity_id AS session_id,created_at AS at
            FROM workstream_links WHERE linked_by='user' AND entity_type='session'
                AND entity_id IN ({})""".format(marks), tuple(str(i) for i in session_ids)), cutoff, omissions)
        links = _take(links, 200, omissions)
        owners = sorted({r["workstream_id"] for r in links})
        owner_rows = []
        if owners:
            owner_marks = ",".join("?" for _ in owners)
            for table, column, owner_column in (("workstreams", "summary", "id"),
                                                 ("threads", "current_goal", "workstream_id"),
                                                 ("checkpoints", "current_goal", "workstream_id")):
                for row in connection.execute("SELECT id,updated_at AS at,length({}) AS size,{} AS workstream_id FROM {} WHERE {} IN ({})".format(
                        column, owner_column, table, owner_column, owner_marks), owners):
                    owner_rows.append({**dict(row), "table": table})
        for row in _take(_dated(owner_rows, cutoff, omissions), 20, omissions):
            column = "summary" if row["table"] == "workstreams" else "current_goal"
            value = _prefix(connection, row, row["table"], column, "id", 2000, omissions)
            if value:
                organization.append(value)

    instants = [r["instant"] for r in population]
    instants.extend(r["instant"] for r in documents + items + organization + links)
    start = min(instants).astimezone(timezone.utc).isoformat()
    cutoffs = sorted({selected[(len(selected) - 1) // 3]["instant"],
                      selected[2 * (len(selected) - 1) // 3]["instant"], cutoff})
    manifest = {"version": 1, "source_ids": sources, "start": start, "end": through,
                "owner": owner, "expires_at": expires_at, "snapshots": []}
    for index, at in enumerate(cutoffs):
        ids = [r["id"] for r in selected if r["instant"] <= at]
        current_owner_rows = [r for r in organization if r["instant"] <= at]
        owner_ids = {r["workstream_id"] for r in current_owner_rows}
        missing = sum(t is None or t <= at for t in omissions)
        manifest["snapshots"].append({
            "name": "observation-{}".format(index + 1), "as_of": at.astimezone(timezone.utc).isoformat(),
            "session_ids": ids,
            "events": [r["choice"] for r in events if r["instant"] <= at and r["session_id"] in ids],
            "documents": [r["choice"] for r in documents if r["instant"] <= at],
            "items": [r["choice"] for r in items if r["instant"] <= at],
            "organization": [r["choice"] for r in current_owner_rows],
            "organization_links": [r["id"] for r in links if r["instant"] <= at and
                                   int(r["session_id"]) in ids and r["workstream_id"] in owner_ids],
            "coverage": {"complete": missing == 0, "unexamined": missing},
        })
    validate_manifest(manifest)
    snapshots = load_snapshots(database, manifest)  # Revalidate permissions and frozen hashes.
    return {"manifest": manifest, "snapshots": snapshots,
            "preparation": {"version": SAMPLING_VERSION, "eligible_sessions": len(population),
                            "selected_sessions": len(selected), "outside_sample_sessions": len(population) - len(selected),
                            "omitted_or_truncated_records": len(omissions)}}


def unassessed_expectations(snapshots):
    """Unknown placeholders are not an answer key and cannot yield quality PASS."""
    return {"version": 1, "snapshots": {r["name"]: {
        "version": 1, "snapshot_digest": digest(r), "groups": [], "negative": [],
        "unresolved": max(1, len(r["records"]))} for r in snapshots}}
