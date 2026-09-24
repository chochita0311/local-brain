"""Read-only, snapshot-scoped inspection of the owned full-history simulation.

No model import, preparation, persistent read cache, or organization writes.
"""

from __future__ import annotations

import fcntl
import math
import os
import sqlite3
import stat
import threading
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode

from .session_simulation import (EXTRACTION, OWNER, _date, _safe_file, _status,
                                 input_text, inventory, now, read_json, sha)
from .work_reconstruction import ExperimentError, digest, require, timestamp
from .work_reconstruction_input import read_only_database
from .session_simulation_graph import validate_parameters

VERSION = "localbrain.session-affinity.v2"
MAX_REPORT_BYTES = 128 * 1024 * 1024
PAGE_SIZE = 24
EVIDENCE_SIZE = 8
_cache = {}
_cache_lock = threading.RLock()
STATES = {
    "missing": ("전체 이력 계산이 아직 없습니다", "기존 로컬 시뮬레이션 명령으로 결과를 준비한 뒤 다시 열어 주세요. 화면을 여는 것만으로 계산하지 않습니다."),
    "busy": ("결과를 준비하고 있습니다", "완료된 결과가 게시된 뒤 다시 열어 주세요. 이 화면에서 새 계산을 시작하지는 않습니다."),
    "expired": ("보관 기한이 지난 결과입니다", "30일 비활성 보관 기한이 지났습니다. 명시적으로 다시 계산해 주세요. 원본 기록은 그대로 있습니다."),
    "invalid": ("결과를 안전하게 읽을 수 없습니다", "결과의 형식·크기·소유권·설정이 맞지 않습니다. 기존 시뮬레이션 저장소를 확인해 주세요. 화면에서 덮어쓰지 않습니다."),
    "unavailable": ("원본 저장소를 읽을 수 없습니다", "로컬 원본의 이용 가능 여부를 확인한 뒤 다시 열어 주세요."),
    "stale": ("계산 이후 원본이 달라졌습니다", "변경된 근거를 현재 결과처럼 보여주지 않습니다. 기존 명령으로 누락·변경 입력만 재계산해 주세요."),
    "selection-stale": ("이 선택은 현재 결과에 없습니다", "이전 계산의 링크이거나 존재하지 않는 선택입니다. 다른 묶음으로 자동 연결하지 않았습니다."),
}


def _state(name, **values):
    title, explanation = STATES.get(name, ("", ""))
    return {"version": VERSION, "state": name, "title": title,
            "explanation": explanation, **values}


def _signature(path):
    try:
        s = path.stat()
        return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    except FileNotFoundError:
        return None


def _source_signature(database):
    return (_signature(database), _signature(database.with_name(database.name + "-wal")))


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _index(report):
    require(report["owner"] == OWNER and report["processing_complete"] is True)
    require(report["quality"] == "unassessed" and report["lineage_status"] == "not_inferred")
    manifest, grouping = report["manifest"], report["grouping"]
    require(manifest["sampled"] is False and manifest["extraction"] == EXTRACTION)
    require(type(manifest["chunk_chars"]) is int and 128 <= manifest["chunk_chars"] <= 16000)
    require(_hash(manifest["digest"]))
    timestamp(report["created_at"])
    validate_parameters(report["parameters"])
    require(report["namespace"] == digest([report["model"], EXTRACTION, manifest["chunk_chars"]]))
    require(report["configuration"] == digest([report["namespace"], report["parameters"], grouping["engine"]]))
    require(grouping["authority"] == "inferred-affinity-only")
    require(grouping["engine"]["method"] == "cosine-knn-louvain-v2-ordered")
    sessions, by_input, seen = {}, defaultdict(list), set()
    statuses = {"eligible", "excluded-maintenance", "excluded-subsession",
                "excluded-metadata-only", "excluded-missing-source"}
    for s in report["sessions"]:
        require(_hash(s["key"]) and s["key"] not in sessions and s["status"] in statuses)
        require(type(s["id"]) is int and s["id"] > 0 and isinstance(s["title"], str) and len(s["title"]) <= 300)
        sessions[s["key"]] = s
    for c in report["chunks"]:
        require(c["session_key"] in sessions and sessions[c["session_key"]]["status"] == "eligible")
        require(type(c["start"]) is int and type(c["end"]) is int and 0 <= c["start"] < c["end"])
        require(c["end"] - c["start"] <= manifest["chunk_chars"])
        require(isinstance(c["event_id"], str) and len(c["event_id"]) <= 1000)
        require(c["role"] in {"user", "assistant"} and _hash(c["input_hash"]) and _hash(c["content_hash"]))
        require(c["key"] == digest([c["session_key"], c["event_id"], c["start"], c["end"]]) and c["key"] not in seen)
        if c["at"] is not None:
            timestamp(c["at"])
        seen.add(c["key"])
        by_input[c["input_hash"]].append(c)
    coverage = manifest["coverage"]
    require(coverage["total_sessions"] == len(sessions) and coverage["chunks"] == len(seen))
    require(coverage["admitted_characters"] == sum(c["end"] - c["start"] for c in report["chunks"]))
    with_text = {c["session_key"] for c in report["chunks"]}
    require(coverage["sessions_with_text"] == len(with_text))
    require(coverage["sessions_without_text"] == coverage["eligible_sessions"] - len(with_text))
    for status in statuses:
        require(coverage[status + "_sessions"] == sum(s["status"] == status for s in sessions.values()))
    require(report["cache"]["total"] == len(by_input) == grouping["node_count"])
    groups, children, assigned = {}, {}, set()

    def describe(group, kind):
        members = group["members"]
        require(members and len(set(members)) == len(members) and set(members) <= by_input.keys())
        require(group["id"] == digest([kind, sorted(members)]))
        chunks = sorted((c for k in members for c in by_input[k]), key=lambda c: (c["at"] or "", c["key"]))
        keys = sorted({c["session_key"] for c in chunks})
        dates = sorted({c["at"] for c in chunks if c["at"]})
        return {"id": group["id"], "kind": "group" if kind == "area" else "subgroup",
                "title": sessions[chunks[0]["session_key"]]["title"],
                "members": set(members), "chunks": chunks, "session_keys": keys,
                "sessions": len(keys), "occurrences": len(chunks), "vectors": len(members),
                "first": dates[0] if dates else None, "last": dates[-1] if dates else None}

    for a in grouping["areas"]:
        d = describe(a, "area")
        require(d["id"] not in groups and not assigned.intersection(d["members"]))
        assigned.update(d["members"])
        groups[d["id"]] = d
        parts, used = {}, set()
        for w in a["work_groups"]:
            sub = describe(w, "work")
            require(sub["id"] not in parts and not used.intersection(sub["members"]))
            used.update(sub["members"])
            parts[sub["id"]] = sub
        require(used == d["members"])
        children[d["id"]] = parts
    require(assigned == by_input.keys())
    edge_keys = set()
    for edge in grouping["edges"]:
        a, b, weight = edge["left"], edge["right"], edge["similarity"]
        require(a in by_input and b in by_input and a < b and (a, b) not in edge_keys)
        require(type(weight) in {float, int} and math.isfinite(weight) and 0 <= weight <= 1)
        edge_keys.add((a, b))
    require(grouping["edge_count"] == len(edge_keys))
    membership = Counter(k for g in groups.values() for k in g["session_keys"])
    return {"report": report, "sessions": sessions, "by_input": by_input, "groups": groups,
            "children": children, "membership": membership,
            "snapshot": digest([manifest["digest"], report["configuration"]]),
            "counts": {"groups": len(groups), "cross_session": sum(g["sessions"] > 1 for g in groups.values()),
                       "single_session": sum(g["sessions"] == 1 for g in groups.values()),
                       "overlap_sessions": sum(v > 1 for v in membership.values()), "vectors": len(by_input)}}


def _load(database, folder, at):
    """Returns only fully validated data; readers never call the writer owner."""
    global _cache
    if not folder.exists():
        return _state("missing")
    require(not folder.is_symlink() and folder == folder.resolve())
    info = folder.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077)
    if not database.is_file() or database.is_symlink():
        return _state("unavailable")
    _safe_file(folder / "writer.lock")
    fd = os.open(folder / "writer.lock", os.O_RDONLY | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return _state("busy")
        _safe_file(folder / "owner.json")
        require((folder / "owner.json").stat().st_size <= 65536)
        marker = read_json(folder / "owner.json")
        require(marker["owner"] == OWNER and marker["database"] == digest([
            str(database.resolve()), database.stat().st_dev, database.stat().st_ino]))
        if timestamp(marker["expires_at"]) <= at:
            with _cache_lock:
                _cache = {}
            return _state("expired")
        target = folder / "report.json"
        if not target.exists():
            return _state("missing")
        _safe_file(target)
        require(target.stat().st_size <= MAX_REPORT_BYTES)
        signature = _source_signature(database)
        cache_key = (str(target), _signature(target), signature)
        with _cache_lock:
            if _cache.get("key") == cache_key:
                return _cache["value"]
            indexed = _index(read_json(target))
            current_chunks = {}
            manifest = inventory(database, indexed["report"]["manifest"]["chunk_chars"],
                                 lambda kind, v: current_chunks.update({v["key"]: v["input_hash"]}) if kind == "chunk" else None)
            if _source_signature(database) != signature:
                return _state("busy")
            if manifest != indexed["report"]["manifest"]:
                old = {c["key"]: c["input_hash"] for c in indexed["report"]["chunks"]}
                indexed = _state("stale", coverage=indexed["report"]["manifest"]["coverage"],
                                 current_coverage=manifest["coverage"], created_at=indexed["report"]["created_at"],
                                 delta={"added": len(current_chunks.keys() - old.keys()),
                                        "removed": len(old.keys() - current_chunks.keys()),
                                        "changed": sum(old[k] != current_chunks[k] for k in old.keys() & current_chunks.keys())})
            else:
                indexed["state"] = "current"
            _cache = {"key": cache_key, "value": indexed}
            return indexed
    finally:
        os.close(fd)


def _page(items, number, size):
    pages = max(1, math.ceil(len(items) / size))
    value = str(number)
    page = min(pages, max(1, int(value))) if value.isdigit() and len(value) <= 6 else 1
    return items[(page - 1) * size:page * size], page, pages


def _public(group):
    return {k: v for k, v in group.items() if k not in {"chunks", "members", "session_keys"}}


def _timeline(candidates):
    """One elapsed-time scale per scope, independent of search/page/selection."""
    dates = [timestamp(c["at"]) for g in candidates for c in g["chunks"] if c["at"]]
    unknown = sum(c["at"] is None for g in candidates for c in g["chunks"])
    if not dates:
        return {"start": None, "end": None, "period_days": 1, "periods": 0,
                "dated_occurrences": 0, "unknown_occurrences": unknown}
    first, last = min(dates), max(dates)
    start = first.replace(hour=0, minute=0, second=0, microsecond=0)
    days = (last - start).days + 1
    period_days = max(1, math.ceil(days / 64))
    periods = math.ceil(days / period_days)
    return {"start": start.isoformat(), "end": (start + timedelta(days=periods * period_days)).isoformat(),
            "period_days": period_days, "periods": periods,
            "dated_occurrences": len(dates), "unknown_occurrences": unknown}


def _period(chunk, timeline):
    if chunk["at"] is None:
        return "unknown"
    return str((timestamp(chunk["at"]) - timestamp(timeline["start"])).days // timeline["period_days"])


def _activity(group, timeline):
    periods = defaultdict(list)
    for c in group["chunks"]:
        periods[_period(c, timeline)].append(c)
    result = []
    for period, chunks in sorted(periods.items(), key=lambda pair: 65 if pair[0] == "unknown" else int(pair[0])):
        dates = sorted(c["at"] for c in chunks if c["at"])
        result.append({"period": period, "first": dates[0] if dates else None, "last": dates[-1] if dates else None,
                       "at": sum(timestamp(d).timestamp() * 1000 for d in dates) / len(dates) if dates else None,
                       "occurrences": len(chunks), "sessions": len({c["session_key"] for c in chunks})})
    return result


def _edges(indexed, visible):
    owners, weights = defaultdict(dict), {}
    for item in visible:
        # First dated occurrence is a deterministic witness, never a group-span
        # endpoint invented for layout. Unknown-time witnesses remain unplaced.
        for c in sorted(item["chunks"], key=lambda c: (c["at"] is None, c["at"] or "", c["key"])):
            owners[c["input_hash"]].setdefault(item["id"], c)

    def add(left, right, weight, a, b):
        if left != right:
            key = tuple(sorted((left, right)))
            if left > right:
                a, b = b, a
            rank = (-weight, a["at"] is None or b["at"] is None, a["key"], b["key"])
            if key not in weights or rank < weights[key][0]:
                weights[key] = (rank, a["at"], b["at"])

    for keys in owners.values():  # identical inputs in different Sessions
        for a in keys:
            for b in keys:
                add(a, b, 1.0, keys[a], keys[b])
    for edge in indexed["report"]["grouping"]["edges"]:
        for a in owners.get(edge["left"], ()):
            for b in owners.get(edge["right"], ()):
                add(a, b, edge["similarity"], owners[edge["left"]][a], owners[edge["right"]][b])
    return [{"left": a, "right": b, "similarity": -v[0][0], "left_at": v[1], "right_at": v[2]}
            for (a, b), v in sorted(weights.items())]


def _evidence(database, rows, sessions):
    result = []
    with read_only_database(database) as source:
        for c in rows:
            item = {**c, "title": sessions[c["session_key"]]["title"], "available": False}
            r = source.execute("""SELECT s.id,s.source_id,s.external_id,s.title,s.session_class,
                s.session_role,s.index_policy,p.kind,e.role,e.event_type,e.occurred_at,
                substr(e.text,?,?) AS wording FROM activity_events e JOIN sessions s ON s.id=e.session_id
                LEFT JOIN sources p ON p.id=s.source_id WHERE e.id=? AND s.id=?""",
                (c["start"] + 1, c["end"] - c["start"], c["event_id"], sessions[c["session_key"]]["id"])).fetchone()
            if r:
                r = dict(r)
                text = r["wording"] or ""
                valid = (_status(r) == "eligible" and digest([r["kind"], r["external_id"]]) == c["session_key"]
                         and r["event_type"] == "message" and r["role"] == c["role"] and _date(r["occurred_at"]) == c["at"]
                         and len(text) == c["end"] - c["start"] and sha(text) == c["content_hash"]
                         and sha(input_text(r["title"][:300], r["role"], text)) == c["input_hash"])
                if valid:
                    item.update(available=True, wording=text, href="/sessions/{}".format(r["id"]),
                                focus_href="/sessions/{}/workflow".format(r["id"]))
            result.append(item)
    return result


def affinity_page(database, data_dir, *, params=None, at=None):
    """Bounded public projection. All reads are local, passive and reversible."""
    params = params or {}
    database = Path(database)
    try:
        indexed = _load(database, Path(data_dir) / "session-simulation", at or now())
        if indexed["state"] != "current":
            return indexed
        report, snapshot = indexed["report"], indexed["snapshot"]
        base = {"snapshot": snapshot}
        group, subgroup, pick = (params.get(k, "") for k in ("group", "subgroup", "pick"))
        def url(**overrides):
            return "/auto-work?" + urlencode({k: v for k, v in {**base, **overrides}.items() if v not in (None, "")})
        if (params.get("snapshot") not in (None, "", snapshot)
                or (group or subgroup or pick) and params.get("snapshot") != snapshot):
            return _state("selection-stale", overview_url=url())
        groups = indexed["groups"]
        if group and group not in groups or subgroup and (not group or subgroup not in indexed["children"][group]):
            return _state("selection-stale", overview_url=url())
        level = "groups"
        candidates = list(groups.values())
        crumbs = [{"title": "전체 묶음", "href": url()}]
        if group:
            base["group"] = group
            candidates, level = list(indexed["children"][group].values()), "subgroups"
            crumbs.append({"title": "세부 묶음", "href": url()})
        if subgroup:
            base["subgroup"] = subgroup
            level = "sessions"
            parent = indexed["children"][group][subgroup]
            candidates = []
            for key in parent["session_keys"]:
                chunks = [c for c in parent["chunks"] if c["session_key"] == key]
                dates = sorted({c["at"] for c in chunks if c["at"]})
                candidates.append({"id": key, "kind": "session", "title": indexed["sessions"][key]["title"],
                                   "chunks": chunks, "members": {c["input_hash"] for c in chunks}, "sessions": 1,
                                   "occurrences": len(chunks), "first": dates[0] if dates else None,
                                   "last": dates[-1] if dates else None})
            crumbs.append({"title": "세션", "href": url()})
        if params.get("inventory") == "all":
            base = {"snapshot": snapshot, "inventory": "all"}
            candidates = [{"id": s["key"], "kind": "inventory", "title": s["title"], "status": s["status"],
                           "members": set(), "chunks": [], "sessions": 1, "occurrences": 0,
                           "has_text": indexed["membership"][s["key"]] > 0,
                           "membership_count": indexed["membership"][s["key"]]} for s in indexed["sessions"].values()]
            level, crumbs = "inventory", [crumbs[0], {"title": "전체 기록 범위", "href": url()}]
        q = str(params.get("q", ""))[:120].strip()
        base["q"] = q
        candidates.sort(key=lambda g: (-g["occurrences"], g["id"]))
        timeline = _timeline(candidates)
        selected = next((g for g in candidates if g["id"] == pick), None)
        if pick and selected is None:
            return _state("selection-stale", overview_url=url(pick=None))
        filtered = [g for g in candidates if not q or any(q.casefold() in title.casefold() for title in
                    [g["title"]] + [indexed["sessions"][k]["title"] for k in g.get("session_keys", [])])]
        visible, page, pages = _page(filtered, params.get("page", 1), PAGE_SIZE)
        base["page"] = page
        def activity(g):
            return [{**a, "href": url(pick=g["id"], period=a["period"])} for a in _activity(g, timeline)]
        def node(g):
            return {**_public(g), "href": url(pick=g["id"]), "selected": g["id"] == pick,
                    "activity": activity(g)}
        # Paging belongs only to native text navigation. The canvas consumes the
        # complete matching scope, including connections across text-list pages.
        map_nodes = [node(g) for g in filtered] if level != "inventory" else []
        map_by_id = {n["id"]: n for n in map_nodes}
        nodes = [map_by_id[g["id"]] if g["id"] in map_by_id else node(g) for g in visible]
        selection = _public(selected) if selected else None
        period = str(params.get("period", ""))
        selected_activity = activity(selected) if selected else []
        if period and (not selected or period not in {a["period"] for a in selected_activity}):
            return _state("selection-stale", overview_url=url(pick=None))
        if selection:
            selection.update(activity=selected_activity, whole_href=url(pick=pick))
        if selection and level in {"groups", "subgroups"}:
            selection["expand_href"] = url(group=selected["id"] if level == "groups" else group,
                                            subgroup=selected["id"] if level == "subgroups" else None,
                                            pick=None, page=None, q=None)
        evidence = [c for c in selected["chunks"] if not period or _period(c, timeline) == period] if selected else []
        rows, ep, eps = _page(evidence, params.get("evidence_page", 1), EVIDENCE_SIZE)
        result = {"version": VERSION, "state": "current" if groups else "empty", "snapshot": snapshot,
                  "created_at": report["created_at"], "coverage": report["manifest"]["coverage"], "counts": indexed["counts"],
                  "model": report["model"], "parameters": report["parameters"], "configuration": report["configuration"],
                  "level": level, "nodes": nodes, "map_nodes": map_nodes,
                  "map_scope": [VERSION, snapshot, level, group, subgroup, q],
                  "edges": _edges(indexed, filtered) if map_nodes else [], "selection": selection,
                  "timeline": timeline, "period": period,
                  "scope_title": (indexed["children"][group][subgroup]["title"] if subgroup else groups[group]["title"] if group else None)
                                 if level != "inventory" else None,
                  "crumbs": crumbs, "q": q, "base": {k: v for k, v in base.items() if k != "q"},
                  "total": len(candidates), "matched": len(filtered), "page": page, "pages": pages,
                  "previous": url(page=page - 1, pick=pick, period=period) if page > 1 else None,
                  "next": url(page=page + 1, pick=pick, period=period) if page < pages else None,
                  "evidence": _evidence(database, rows, indexed["sessions"]),
                  "evidence_page": ep, "evidence_pages": eps, "evidence_total": len(evidence),
                  "evidence_previous": url(pick=pick, period=period, evidence_page=ep - 1) if ep > 1 else None,
                  "evidence_next": url(pick=pick, period=period, evidence_page=ep + 1) if ep < eps else None,
                  "clear_url": url(), "overview_url": "/auto-work?" + urlencode({"snapshot": snapshot}),
                  "inventory_url": "/auto-work?" + urlencode({"snapshot": snapshot, "inventory": "all"})}
        return result
    except (OSError, sqlite3.Error):
        return _state("unavailable")
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError, OverflowError):
        return _state("invalid")
