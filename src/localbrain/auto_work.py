"""Local, source-bound inspection of unassessed reconstruction output.

Only explicit preparation writes the single private preview. Browsing never
extracts, synchronizes sources, or changes user organization.
"""

from __future__ import annotations

import fcntl
import os
import stat
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from .work_reconstruction import VERSION, ExperimentError, digest, key, require, timestamp
from .work_reconstruction_experiment import MAX_BYTES, QuietParser, decode_bounded, encode_bounded, supervise
from .work_reconstruction_input import load_snapshots, read_only_database, validate_manifest


OWNER = "localbrain.auto-work-preview.v1"
DIRECTORY = "auto-work-preview"
FILENAME = "current.json"
PAGE_SIZE = 12
EVIDENCE_SIZE = 20
RETENTION = timedelta(days=7)
CHANGES = {"reduce": "줄이기", "increase": "늘리기", "improve": "개선", "fix": "수정",
           "add": "추가", "remove": "제거", "replace": "교체", "enable": "활성화", "disable": "비활성화"}
REASONS = {"unsupported-goal": "작업 목표를 식별하지 못함",
           "unsupported-negation": "부정 표현의 의미를 판단하지 못함",
           "unsupported-subject": "작업 대상을 식별하지 못함",
           "ambiguous-completion": "완료 조건이 서로 달라 소속을 판단하지 못함",
           "ineligible-session": "분석 대상이 아닌 세션"}
STATES = {
    "missing": ("아직 분석 결과가 없습니다", "현재 저장된 데이터로 표본 분석을 시작할 수 있습니다."),
    "expired": ("분석 결과의 보관 기간이 끝났습니다", "현재 데이터로 다시 분석하면 새 결과를 볼 수 있습니다."),
    "stale": ("분석 근거가 달라졌습니다", "원문이나 접근 범위가 바뀌어 이전 결과를 표시하지 않습니다. 다시 분석해 주세요."),
    "error": ("분석 결과를 불러오지 못했습니다", "결과 파일이나 로컬 저장 경로를 확인한 뒤 갱신해 주세요. 알 수 없거나 손상된 파일은 덮어쓰지 않습니다. 원본과 기존 작업 구성은 변경되지 않았습니다."),
}


def _directory(data_dir, create=False):
    base = Path(data_dir)
    repo = Path(__file__).resolve().parents[2]
    require(base.is_absolute() and base.is_dir() and base == base.resolve(), "INVALID_OUTPUT")
    require(base != repo and repo not in base.parents, "INVALID_OUTPUT")
    folder = base / DIRECTORY
    require(not folder.is_symlink(), "INVALID_OUTPUT")
    if create:
        folder.mkdir(mode=0o700, exist_ok=True)
    if folder.exists():
        info = folder.stat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077,
                "INVALID_OUTPUT")
    return folder


@contextmanager
def _lock(folder):
    descriptor = os.open(folder / "preview.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077,
                "INVALID_OUTPUT")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ExperimentError("PREVIEW_BUSY") from None
        yield
    finally:
        os.close(descriptor)


def _read(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077,
                "INVALID_OUTPUT")
        payload = decode_bounded(handle.read(MAX_BYTES + 1))
    require(isinstance(payload, dict) and set(payload) == {
        "version", "owner", "created_at", "expires_at", "manifest", "snapshot_digest", "preparation", "output"})
    require(payload["version"] == 1 and payload["owner"] == OWNER)
    require(timedelta(0) < timestamp(payload["expires_at"]) - timestamp(payload["created_at"]) <= RETENTION)
    manifest = validate_manifest(payload["manifest"])
    require(manifest["owner"] == OWNER and manifest["end"] == payload["created_at"] and
            manifest["expires_at"] == payload["expires_at"] and len(manifest["snapshots"]) == 1)
    require(isinstance(payload["snapshot_digest"], str) and len(payload["snapshot_digest"]) == 64)
    preparation = payload["preparation"]
    require(isinstance(preparation, dict))
    for name in ("eligible_sessions", "selected_sessions", "outside_sample_sessions", "omitted_or_truncated_records"):
        require(type(preparation.get(name)) is int and preparation[name] >= 0)
    require(preparation["selected_sessions"] <= 60 and preparation["eligible_sessions"] ==
            preparation["selected_sessions"] + preparation["outside_sample_sessions"])
    require(preparation["selected_sessions"] == len(manifest["snapshots"][0]["session_ids"]))
    require(isinstance(payload["output"], dict) and payload["output"].get("version") == VERSION)
    return payload


def prepare_preview(database, data_dir, now=None):
    """Explicit local preparation; preserves a previous valid preview on failure."""
    now = now or datetime.now(timezone.utc)
    through, expiry = now.isoformat(), (now + RETENTION).isoformat()
    folder = _directory(data_dir, create=True)
    target = folder / FILENAME
    with _lock(folder):
        if target.exists() or target.is_symlink():
            _read(target)  # An unknown or malformed existing file is not overwrite authority.
        prepared, _ = supervise("prepare", (str(database), through, OWNER, expiry))
        snapshot = prepared["snapshots"][-1]
        output, _ = supervise("text", (snapshot, (), False))
        manifest = {**prepared["manifest"], "snapshots": [prepared["manifest"]["snapshots"][-1]]}
        value = {"version": 1, "owner": OWNER, "created_at": through, "expires_at": expiry,
                 "manifest": manifest, "snapshot_digest": digest(snapshot),
                 "preparation": prepared["preparation"], "output": output}
        raw = encode_bounded(value)
        staged = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".staged-", dir=folder, delete=False) as handle:
                staged = Path(handle.name)
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            _read(staged)
            os.replace(staged, target)
        finally:
            if staged is not None and staged.exists():
                staged.unlink()


def _expire(folder, now):
    # Re-read under the writer's lock: never delete a concurrently refreshed result.
    with _lock(folder):
        if timestamp(_read(folder / FILENAME)["expires_at"]) <= now:
            (folder / FILENAME).unlink()


def _bound_output(output, data):
    """Refuse fabricated locators and stale wording, including unassigned scope."""
    records = {r["key"]: r for r in data["records"] if r["kind"] != "organization"}
    require(output.get("corrections") == [] and output.get("routine_confirmations") == 0)
    require(output.get("coverage") == data["coverage"])
    require(isinstance(output.get("flows"), list) and isinstance(output.get("unassigned"), list))
    seen = set()
    for flow in output["flows"]:
        require(isinstance(flow, dict) and isinstance(flow.get("flow_id"), str))
        require(flow["flow_id"] not in seen); seen.add(flow["flow_id"])
        require(flow.get("authority") == "inferred" and flow.get("lifecycle") == "unknown")
        require(flow.get("change") in CHANGES and isinstance(flow.get("subject"), str) and
                0 < len(flow["subject"]) <= 300 and isinstance(flow.get("members"), list) and flow["members"])
        require(flow.get("completion") is None or isinstance(flow["completion"], str))
        for member in flow["members"]:
            record, wording = _span(member, records)
            require(member.get("wording") == wording and member.get("session_id") == record.get("session_id"))
            require(member.get("role") == record["role"] and member.get("source_kind") == record["kind"] and
                    member.get("observed_at") == record["at"] and member.get("authority") == "inferred")
            require(member.get("subject") == flow["subject"] and member.get("change") == flow["change"])
    for item in output["unassigned"]:
        require(isinstance(item, dict))
        require(item.get("reason") in REASONS)
        _span(item, records)
    return records


def _span(item, records):
    require(isinstance(item, dict) and item.get("record_key") in records)
    record = records[item["record_key"]]
    start, end = item.get("start"), item.get("end")
    require(type(start) is int and type(end) is int and
            record["offset"] <= start < end <= record["offset"] + len(record["text"]))
    return record, record["text"][start - record["offset"]:end - record["offset"]]


def _destinations(database, manifest, records):
    result = {}
    scope = manifest["snapshots"][0]
    with read_only_database(database, timeout=5) as connection:
        sessions = {}
        for sid in scope["session_ids"]:
            row = connection.execute("SELECT substr(title,1,500) AS title FROM sessions WHERE id=?", (sid,)).fetchone()
            sessions[sid] = {"title": row["title"] or "제목 없는 세션", "href": "/sessions/{}".format(sid), "kind": "세션"}
        for record in records.values():
            if record["kind"] == "session":
                result[record["key"]] = sessions[record["session_id"]]
        for field, kind, table, title, identity, route, label in (
            ("documents", "document", "context_documents", "title", "id", "/documents/", "문서"),
            ("items", "item", "external_resources", "title", "id", "/atlassian/items/", "링크/문서"),
        ):
            for choice in scope[field]:
                row = connection.execute("SELECT substr({},1,500) AS title FROM {} WHERE {}=?".format(
                    title, table, identity), (choice["id"],)).fetchone()
                require(row is not None)
                result[key("record", kind, str(choice["id"]))] = {
                    "title": row["title"] or "제목 없음", "href": route + str(choice["id"]), "kind": label}
    return result


def _page(value, total, size):
    try:
        number = int(value) if isinstance(value, (int, str)) and len(str(value)) <= 9 else 1
    except (ValueError, TypeError):
        number = 1
    pages = max(1, (total + size - 1) // size)
    return min(pages, max(1, number)), pages


def _url(**values):
    return "/auto-work?" + urlencode({"mode": "sample", **{k: v for k, v in values.items() if v is not None}})


def _evidence(item, records, destinations):
    record, wording = _span(item, records)
    return {**destinations[record["key"]], "wording": wording, "at": record["at"],
            "role": {"user": "사용자", "assistant": "어시스턴트의 발언", "document": "문서"}.get(record["role"], "원문"),
            "start": item["start"], "end": item["end"],
            "reason": REASONS.get(item.get("reason")), "session_id": record.get("session_id")}


def preview_page(database, data_dir, *, page=1, flow=None, view="flows", evidence_page=1, now=None):
    now = now or datetime.now(timezone.utc)
    state = "error"
    try:
        folder = _directory(data_dir)
        try:
            payload = _read(folder / FILENAME)
        except FileNotFoundError:
            state = "missing"
            raise ExperimentError("PREVIEW_MISSING") from None
        if timestamp(payload["expires_at"]) <= now:
            state = "expired"
            try:
                _expire(folder, now)
            except (OSError, ExperimentError):
                pass  # Busy refresh retains expiry state, never stale private content.
            raise ExperimentError("PREVIEW_EXPIRED")
        state = "stale"
        data = load_snapshots(database, payload["manifest"])[0]
        require(digest(data) == payload["snapshot_digest"], "SOURCE_CHANGED")
        state = "error"
        records = _bound_output(payload["output"], data)
        destinations = _destinations(database, payload["manifest"], records)
        return _view(payload, records, destinations, page, flow, view, evidence_page)
    except (ExperimentError, OSError, ValueError, TypeError, KeyError, RecursionError):
        title, explanation = STATES[state]
        return {"state": state, "title": title, "explanation": explanation}


def _view(payload, records, destinations, page, flow_id, view, evidence_page):
    output = payload["output"]
    flows = sorted(output["flows"], key=lambda f: (f["subject"], f["change"], f["flow_id"]))
    page, pages = _page(page, len(flows), PAGE_SIZE)
    visible = flows[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
    mode = "unassigned" if view == "unassigned" else "flows"
    selected = next((f for f in flows if f["flow_id"] == flow_id), None) if flow_id else next(iter(visible), None)
    def summary(item):
        return {"id": item["flow_id"], "title": item["subject"] + " · " + CHANGES[item["change"]],
                "completion": item["completion"], "members": len(item["members"]),
                "sessions": len({m["session_id"] for m in item["members"] if m["session_id"] is not None}),
                "href": _url(page=page, flow=item["flow_id"])}
    rows = output["unassigned"] if mode == "unassigned" else selected["members"] if selected else []
    rows = sorted(rows, key=lambda r: (records[r["record_key"]]["at"], r["record_key"], r["start"]))
    evidence_page, evidence_pages = _page(evidence_page, len(rows), EVIDENCE_SIZE)
    current_id = selected["flow_id"] if selected and mode == "flows" else None
    assigned_records = {m["record_key"] for f in flows for m in f["members"]}
    return {"state": "ready", "created_at": payload["created_at"], "expires_at": payload["expires_at"],
            "start": payload["manifest"]["start"], "preparation": payload["preparation"],
            "coverage": output["coverage"], "group_count": len(flows),
            "unassigned_count": len(output["unassigned"]), "record_count": len(records),
            "assigned_record_count": len(assigned_records), "mode": mode,
            "groups": [summary(f) for f in visible], "selected": summary(selected) if selected and mode == "flows" else None,
            "selection_missing": bool(flow_id and not selected), "page": page, "pages": pages,
            "previous": _url(page=page - 1) if page > 1 else None,
            "next": _url(page=page + 1) if page < pages else None,
            "flows_url": _url(page=page, flow=flow_id), "unassigned_url": _url(page=page, view="unassigned"),
            "evidence": [_evidence(r, records, destinations) for r in rows[(evidence_page - 1) * EVIDENCE_SIZE:evidence_page * EVIDENCE_SIZE]],
            "evidence_total": len(rows), "evidence_page": evidence_page, "evidence_pages": evidence_pages,
            "evidence_previous": _url(page=page, flow=current_id, view=mode, evidence_page=evidence_page - 1) if evidence_page > 1 else None,
            "evidence_next": _url(page=page, flow=current_id, view=mode, evidence_page=evidence_page + 1) if evidence_page < evidence_pages else None}


def main(argv=None):
    parser = QuietParser(description="Prepare the local Auto Work preview explicitly.")
    parser.add_argument("--database", required=True)
    parser.add_argument("--data-dir", required=True)
    try:
        args = parser.parse_args(argv)
        prepare_preview(args.database, args.data_dir)
        print("AUTO_WORK_PREVIEW_READY")
        return 0
    except KeyboardInterrupt:
        print("AUTO_WORK_PREVIEW_CANCELLED")
        return 130
    except Exception as error:
        if isinstance(error, ExperimentError) and str(error) == "PREVIEW_BUSY":
            print("AUTO_WORK_PREVIEW_BUSY")
            return 3
        print("AUTO_WORK_PREVIEW_FAILED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
