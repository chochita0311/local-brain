import copy
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


STOP_WORDS = {
    "about",
    "and",
    "context",
    "for",
    "from",
    "local",
    "project",
    "the",
    "this",
    "with",
    "개발",
    "관련",
    "관리",
    "대한",
    "문서",
    "범위",
    "사용",
    "상태",
    "작업",
    "정보",
    "프로젝트",
    "필요",
    "확인",
}


def _tokens(value: str) -> Set[str]:
    return {
        token.lower().strip("._-")
        for token in re.findall(r"[A-Za-z0-9가-힣_.-]{2,}", value or "")
        if token.lower().strip("._-") not in STOP_WORDS
    }


def _fts_expression(tokens: Iterable[str], operator: str = "OR") -> str:
    return (" {} ".format(operator)).join(
        '"{}"'.format(token.replace('"', '""')) for token in sorted(set(tokens))
    )


def _excerpt(text: str, matched_tokens: Set[str], radius: int = 280) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= radius * 2:
        return compact
    lowered = compact.lower()
    positions = [lowered.find(token) for token in matched_tokens]
    positions = [position for position in positions if position >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - radius)
    end = min(len(compact), center + radius)
    prefix = "..." if start else ""
    suffix = "..." if end < len(compact) else ""
    return prefix + compact[start:end] + suffix


def _thread_query(
    workstream: dict, thread: dict
) -> Tuple[Set[str], Set[str], Set[str]]:
    thread_text = " ".join(
        filter(
            None,
            [
                thread.get("title"),
                thread.get("summary"),
                thread.get("current_goal"),
                thread.get("next_action"),
            ],
        )
    )
    workstream_text = " ".join(
        filter(None, [workstream.get("name"), workstream.get("summary")])
    )
    thread_tokens = _tokens(thread_text)
    title_tokens = _tokens(thread.get("title") or "")
    workstream_tokens = _tokens(workstream_text)
    query_tokens = thread_tokens or workstream_tokens
    return query_tokens, workstream_tokens, title_tokens or query_tokens


def _matching_search_rows(
    connection: sqlite3.Connection, candidate_tokens: Set[str]
) -> List[dict]:
    expression = _fts_expression(candidate_tokens, operator="AND")
    if not expression:
        return []
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT entity_type, entity_id, title, path, bm25(search_index) AS fts_score
            FROM search_index
            WHERE search_index MATCH ?
              AND entity_type IN ('session', 'document')
            ORDER BY fts_score, entity_type, entity_id
            """,
            (expression,),
        ).fetchall()
    ]


def _thread_link_maps(
    connection: sqlite3.Connection, workstream_id: int
) -> Tuple[Dict[Tuple[int, str, str], str], Set[Tuple[str, str]]]:
    confirmed = {
        (row["thread_id"], row["entity_type"], row["entity_id"]): row[
            "relation_type"
        ]
        for row in connection.execute(
            """
            SELECT thread_links.thread_id, thread_links.entity_type,
                   thread_links.entity_id, thread_links.relation_type
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            WHERE threads.workstream_id = ?
            """,
            (workstream_id,),
        ).fetchall()
    }
    shared = {
        (row["entity_type"], row["entity_id"])
        for row in connection.execute(
            "SELECT entity_type, entity_id FROM workstream_links WHERE workstream_id = ?",
            (workstream_id,),
        ).fetchall()
    }
    return confirmed, shared


def _suggestion_states(
    connection: sqlite3.Connection, workstream_id: int
) -> Dict[Tuple[int, str, str], str]:
    states: Dict[Tuple[int, str, str], str] = {}
    rows = connection.execute(
        """
        SELECT suggestions.target_id, suggestions.status, suggestions.payload_json
        FROM suggestions
        JOIN threads ON suggestions.target_type = 'thread'
            AND threads.id = suggestions.target_id
        WHERE threads.workstream_id = ?
          AND suggestions.status IN ('pending', 'rejected')
        """,
        (workstream_id,),
    ).fetchall()
    for row in rows:
        try:
            payload = json.loads(row["payload_json"] or "{}")
        except json.JSONDecodeError:
            continue
        entity_type = payload.get("entity_type")
        entity_id = payload.get("entity_id")
        if entity_type and entity_id is not None:
            states[(row["target_id"], entity_type, str(entity_id))] = row["status"]
            continue
        resource_type = payload.get("resource_type")
        locator = payload.get("locator")
        mapped_type = {
            "session": "session",
            "document": "document",
            "project": "project",
        }.get(resource_type)
        if mapped_type and locator is not None:
            states[(row["target_id"], mapped_type, str(locator))] = row["status"]
    return states


def _relation_state(
    thread_id: int,
    entity_type: str,
    entity_id: str,
    confirmed: Dict[Tuple[int, str, str], str],
    suggestion_states: Dict[Tuple[int, str, str], str],
) -> Tuple[str, Optional[str]]:
    key = (thread_id, entity_type, str(entity_id))
    if key in confirmed:
        return "confirmed", confirmed[key]
    if key in suggestion_states:
        return suggestion_states[key], None
    return "candidate", None


def _session_resource(connection: sqlite3.Connection, session_id: int) -> Optional[dict]:
    row = connection.execute(
        """
        SELECT sessions.id, sessions.workspace_id, sessions.title, sessions.source_path,
               sessions.cwd_raw, sessions.started_at, sessions.ended_at,
               sessions.last_event_at, sessions.event_count,
               sessions.user_message_count, sessions.assistant_message_count,
               sessions.git_branch,
               sources.kind AS source_kind,
               workspaces.display_name AS workspace_name,
               workspaces.canonical_path AS workspace_path,
               workspaces.git_root
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE sessions.id = ? AND sessions.session_class = 'work'
          AND sessions.session_role = 'primary'
        """,
        (session_id,),
    ).fetchone()
    return dict(row) if row else None


def _document_resource(
    connection: sqlite3.Connection, document_id: int
) -> Optional[dict]:
    row = connection.execute(
        """
        SELECT id, workspace_id, title, path, relative_path, size_bytes, mtime_ns,
               content_hash
        FROM context_documents WHERE id = ?
        """,
        (document_id,),
    ).fetchone()
    return dict(row) if row else None


def _add_relation_summary(resource: dict, relation: dict) -> None:
    summary = resource.setdefault(
        "thread_relation_summary",
        {"confirmed": [], "candidate": [], "pending": [], "rejected": []},
    )
    state = relation["state"]
    if state in summary and relation["thread_id"] not in summary[state]:
        summary[state].append(relation["thread_id"])


def _score_match(
    metadata_tokens: Set[str], evidence_tokens: Set[str], evidence_count: int
) -> float:
    weight = len(metadata_tokens) * 3 + len(evidence_tokens) + min(evidence_count, 10)
    return round(min(0.99, 0.35 + weight * 0.035), 3)


def build_candidate_bundle(connection: sqlite3.Connection, workstream: dict) -> dict:
    confirmed, shared = _thread_link_maps(connection, workstream["id"])
    suggestion_states = _suggestion_states(connection, workstream["id"])
    resources = {
        "sessions": {},
        "documents": {},
        "projects": {},
        "local_paths": {},
        "external_references": {},
    }
    evidence: Dict[str, Dict[str, dict]] = {}
    relations: Dict[Tuple[int, str, str], dict] = {}
    session_events: Dict[int, List[dict]] = {}
    document_bodies: Dict[int, str] = {}

    threads = [thread for thread in workstream["threads"] if thread["status"] != "done"]
    for thread in threads:
        query_tokens, workstream_tokens, candidate_tokens = _thread_query(
            workstream, thread
        )
        for search_row in _matching_search_rows(connection, candidate_tokens):
            entity_type = search_row["entity_type"]
            entity_id = int(search_row["entity_id"])
            evidence_ids: List[str] = []
            evidence_tokens: Set[str] = set()
            metadata_tokens = query_tokens & _tokens(
                "{} {}".format(search_row.get("title") or "", search_row.get("path") or "")
            )

            if entity_type == "session":
                resource = resources["sessions"].get(entity_id)
                if resource is None:
                    resource = _session_resource(connection, entity_id)
                    if not resource:
                        continue
                    resource["thread_relation_summary"] = {
                        "confirmed": [], "candidate": [], "pending": [], "rejected": []
                    }
                    resources["sessions"][entity_id] = resource
                events = session_events.get(entity_id)
                if events is None:
                    events = [
                        dict(row)
                        for row in connection.execute(
                            """
                            SELECT id, sequence, occurred_at, event_type, role, text, tool_name
                            FROM activity_events WHERE session_id = ? ORDER BY sequence
                            """,
                            (entity_id,),
                        ).fetchall()
                    ]
                    session_events[entity_id] = events
                    resource["tools"] = sorted(
                        {event["tool_name"] for event in events if event.get("tool_name")}
                    )
                resource_evidence = evidence.setdefault("session:{}".format(entity_id), {})
                for event in events:
                    if not event.get("text"):
                        continue
                    event_tokens = _tokens(event["text"])
                    if not candidate_tokens & event_tokens:
                        continue
                    matched = query_tokens & event_tokens
                    evidence_ids.append(event["id"])
                    evidence_tokens.update(matched)
                    resource_evidence.setdefault(
                        event["id"],
                        {
                            "id": event["id"],
                            "sequence": event["sequence"],
                            "occurred_at": event["occurred_at"],
                            "event_type": event["event_type"],
                            "role": event["role"],
                            "text": _excerpt(event["text"], matched),
                        },
                    )
            else:
                resource = resources["documents"].get(entity_id)
                if resource is None:
                    resource = _document_resource(connection, entity_id)
                    if not resource:
                        continue
                    resource["thread_relation_summary"] = {
                        "confirmed": [], "candidate": [], "pending": [], "rejected": []
                    }
                    resources["documents"][entity_id] = resource
                body = document_bodies.get(entity_id)
                if body is None:
                    body_row = connection.execute(
                        "SELECT body FROM context_documents WHERE id = ?", (entity_id,)
                    ).fetchone()
                    body = body_row["body"] if body_row else ""
                    document_bodies[entity_id] = body
                resource_evidence = evidence.setdefault("document:{}".format(entity_id), {})
                for line_number, line in enumerate(body.splitlines(), start=1):
                    line_tokens = _tokens(line)
                    if not candidate_tokens & line_tokens:
                        continue
                    matched = query_tokens & line_tokens
                    evidence_id = "document:{}:line:{}".format(entity_id, line_number)
                    evidence_ids.append(evidence_id)
                    evidence_tokens.update(matched)
                    resource_evidence.setdefault(
                        evidence_id,
                        {
                            "id": evidence_id,
                            "line": line_number,
                            "text": _excerpt(line, matched),
                        },
                    )

            state, relation_type = _relation_state(
                thread["id"], entity_type, str(entity_id), confirmed, suggestion_states
            )
            relation = {
                "thread_id": thread["id"],
                "resource_type": entity_type,
                "resource_id": entity_id,
                "state": state,
                "relation_type": relation_type,
                "shared_confirmed": (entity_type, str(entity_id)) in shared,
                "score": _score_match(metadata_tokens, evidence_tokens, len(evidence_ids)),
                "matched_tokens": sorted(metadata_tokens | evidence_tokens),
                "evidence_ids": evidence_ids,
                "workstream_tokens": sorted(workstream_tokens & (metadata_tokens | evidence_tokens)),
            }
            relations[(thread["id"], entity_type, str(entity_id))] = relation
            _add_relation_summary(resource, relation)

    _add_derived_resources(
        connection,
        workstream["id"],
        resources,
        relations,
        confirmed,
        shared,
        suggestion_states,
    )
    _add_confirmed_relations_for_candidates(resources, relations, confirmed, shared)

    candidate_resources = {
        key: sorted(values.values(), key=_resource_sort_key, reverse=True)
        for key, values in resources.items()
    }
    relation_list = sorted(
        relations.values(),
        key=lambda item: (item["thread_id"], -item["score"], item["resource_type"], str(item["resource_id"])),
    )
    fingerprint_input = {
        "resources": {
            key: [_resource_version(item) for item in values]
            for key, values in candidate_resources.items()
        },
        "relations": [
            {
                "thread_id": relation["thread_id"],
                "resource_type": relation["resource_type"],
                "resource_id": relation["resource_id"],
                "score": relation["score"],
                "matched_tokens": relation["matched_tokens"],
                "evidence_ids": relation["evidence_ids"],
            }
            for relation in relation_list
        ],
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_input, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "policy": {
            "retriever": "sqlite-fts5-and-structured-signals",
            "ai_used": False,
            "candidate_count_limit": None,
            "evidence_count_limit_per_resource": None,
            "deduplication": "resource and evidence IDs",
            "session_candidates": {
                "session_class": "work",
                "session_role": "primary",
                "excluded": ["maintenance", "subsession"],
            },
        },
        "fingerprint": fingerprint,
        "counts": {
            "sessions": len(candidate_resources["sessions"]),
            "documents": len(candidate_resources["documents"]),
            "projects": len(candidate_resources["projects"]),
            "local_paths": len(candidate_resources["local_paths"]),
            "external_references": len(candidate_resources["external_references"]),
            "thread_resource_matches": len(relation_list),
            "evidence_items": sum(len(items) for items in evidence.values()),
        },
        "candidate_resources": candidate_resources,
        "thread_resource_matches": relation_list,
        "_evidence": {
            key: list(items.values()) for key, items in evidence.items()
        },
    }


def _add_confirmed_relations_for_candidates(
    resources: dict,
    relations: Dict[Tuple[int, str, str], dict],
    confirmed: Dict[Tuple[int, str, str], str],
    shared: Set[Tuple[str, str]],
) -> None:
    groups = {
        "session": "sessions",
        "document": "documents",
        "project": "projects",
        "local": "local_paths",
        "external": "external_references",
    }
    for (thread_id, entity_type, entity_id), relation_type in confirmed.items():
        group = groups.get(entity_type)
        if not group:
            continue
        resource = resources[group].get(int(entity_id))
        if resource is None:
            continue
        key = (thread_id, entity_type, entity_id)
        relation = relations.get(key)
        if relation is None:
            relation = {
                "thread_id": thread_id,
                "resource_type": entity_type,
                "resource_id": int(entity_id),
                "state": "confirmed",
                "relation_type": relation_type,
                "shared_confirmed": (entity_type, entity_id) in shared,
                "score": 1.0,
                "matched_tokens": [],
                "evidence_ids": [],
            }
            relations[key] = relation
        else:
            relation["state"] = "confirmed"
            relation["relation_type"] = relation_type
        _add_relation_summary(resource, relation)


def _add_derived_resources(
    connection: sqlite3.Connection,
    workstream_id: int,
    resources: dict,
    relations: Dict[Tuple[int, str, str], dict],
    confirmed: Dict[Tuple[int, str, str], str],
    shared: Set[Tuple[str, str]],
    suggestion_states: Dict[Tuple[int, str, str], str],
) -> None:
    source_resources = list(resources["sessions"].values()) + list(
        resources["documents"].values()
    )
    for source in source_resources:
        workspace_id = source.get("workspace_id")
        if not workspace_id:
            continue
        row = connection.execute(
            """
            SELECT id, display_name AS title, canonical_path, git_root,
                   exists_now, last_activity_at, updated_at
            FROM workspaces WHERE id = ?
            """,
            (workspace_id,),
        ).fetchone()
        if not row:
            continue
        project = resources["projects"].setdefault(workspace_id, dict(row))
        project.setdefault(
            "thread_relation_summary",
            {"confirmed": [], "candidate": [], "pending": [], "rejected": []},
        )
        source_type = "session" if source.get("source_path") else "document"
        for key, source_relation in list(relations.items()):
            if key[1] != source_type or str(key[2]) != str(source["id"]):
                continue
            relation_key = (source_relation["thread_id"], "project", str(workspace_id))
            state, relation_type = _relation_state(
                source_relation["thread_id"],
                "project",
                str(workspace_id),
                confirmed,
                suggestion_states,
            )
            relation = relations.get(relation_key)
            if relation is None:
                relation = {
                    "thread_id": source_relation["thread_id"],
                    "resource_type": "project",
                    "resource_id": workspace_id,
                    "state": state,
                    "relation_type": relation_type,
                    "shared_confirmed": ("project", str(workspace_id)) in shared,
                    "score": max(0.35, round(source_relation["score"] - 0.05, 3)),
                    "matched_tokens": source_relation["matched_tokens"],
                    "evidence_ids": source_relation["evidence_ids"],
                    "derived_from": [
                        {"resource_type": source_type, "resource_id": source["id"]}
                    ],
                }
                relations[relation_key] = relation
            else:
                relation["evidence_ids"] = sorted(
                    set(relation["evidence_ids"]) | set(source_relation["evidence_ids"])
                )
                relation.setdefault("derived_from", []).append(
                    {"resource_type": source_type, "resource_id": source["id"]}
                )
                relation["score"] = max(
                    relation["score"], max(0.35, round(source_relation["score"] - 0.05, 3))
                )
            _add_relation_summary(project, relation)

    thread_queries = {
        row["id"]: _tokens(row["title"])
        or _tokens(" ".join(filter(None, [row["summary"], row["current_goal"]])))
        for row in connection.execute(
            """
            SELECT id, title, summary, current_goal, next_action
            FROM threads WHERE workstream_id = ? AND status != 'done'
            """,
            (workstream_id,),
        ).fetchall()
    }
    direct_sources = (
        (
            "projects",
            "project",
            connection.execute(
                """
                SELECT id, display_name AS title, canonical_path, git_root,
                       exists_now, last_activity_at, updated_at
                FROM workspaces
                """
            ).fetchall(),
            ("title", "canonical_path", "git_root"),
        ),
        (
            "local_paths",
            "local",
            connection.execute(
                "SELECT id, title, path, resource_type, summary, exists_now, discovered_by, updated_at FROM local_resources"
            ).fetchall(),
            ("title", "path", "summary"),
        ),
        (
            "external_references",
            "external",
            connection.execute(
                "SELECT id, title, url, resource_type, summary, source_role, updated_at FROM external_resources"
            ).fetchall(),
            ("title", "url", "summary"),
        ),
    )
    for resource_group, entity_type, rows, text_fields in direct_sources:
        for row in rows:
            item = dict(row)
            item_tokens = _tokens(" ".join(str(item.get(field) or "") for field in text_fields))
            for thread_id, query_tokens in thread_queries.items():
                matched = query_tokens & item_tokens
                if not matched:
                    continue
                resource = resources[resource_group].setdefault(item["id"], item)
                resource.setdefault(
                    "thread_relation_summary",
                    {"confirmed": [], "candidate": [], "pending": [], "rejected": []},
                )
                state, relation_type = _relation_state(
                    thread_id, entity_type, str(item["id"]), confirmed, suggestion_states
                )
                relation = {
                    "thread_id": thread_id,
                    "resource_type": entity_type,
                    "resource_id": item["id"],
                    "state": state,
                    "relation_type": relation_type,
                    "shared_confirmed": (entity_type, str(item["id"])) in shared,
                    "score": _score_match(matched, set(), 0),
                    "matched_tokens": sorted(matched),
                    "evidence_ids": [],
                }
                relation_key = (thread_id, entity_type, str(item["id"]))
                existing_relation = relations.get(relation_key)
                if existing_relation:
                    existing_relation["score"] = max(
                        existing_relation["score"], relation["score"]
                    )
                    existing_relation["matched_tokens"] = sorted(
                        set(existing_relation["matched_tokens"]) | matched
                    )
                    relation = existing_relation
                else:
                    relations[relation_key] = relation
                _add_relation_summary(resource, relation)


def _resource_sort_key(item: dict) -> tuple:
    activity = item.get("last_event_at") or item.get("mtime_ns") or item.get("updated_at") or ""
    return (str(activity), str(item.get("id")))


def _resource_version(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "last_event_at": item.get("last_event_at"),
        "event_count": item.get("event_count"),
        "content_hash": item.get("content_hash"),
        "updated_at": item.get("updated_at"),
    }


def write_candidate_evidence(bundle: dict, run_root: Path) -> dict:
    output = copy.deepcopy(bundle)
    evidence = output.pop("_evidence", {})
    evidence_root = run_root / "evidence"
    for resource_key, items in evidence.items():
        resource_type, resource_id = resource_key.split(":", 1)
        directory = evidence_root / (resource_type + "s")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (resource_id + ".json")
        path.write_text(
            json.dumps(
                {
                    "schema": "localbrain.resource-evidence.v1",
                    "resource_type": resource_type,
                    "resource_id": int(resource_id),
                    "evidence": items,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        group = "sessions" if resource_type == "session" else "documents"
        for resource in output["candidate_resources"][group]:
            if str(resource["id"]) == resource_id:
                resource["evidence_path"] = str(path)
                resource["evidence_count"] = len(items)
                break
    output["evidence_root"] = str(evidence_root)
    return output
