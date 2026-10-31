"""Reviewed, local learning evidence and explicitly self-reported review history."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from localbrain.persistence.value_registry import display_value_label


MAX_PACKET_BYTES = 2 * 1024 * 1024
KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,79}\Z")
CONFIDENCE_VALUES = ("low", "medium", "high")
OUTCOME_VALUES = ("pending", "read", "again", "partial", "recalled")
SOURCE_KINDS = ("work", "official")
QUESTION_KINDS = ("recall", "apply")
VERSION_STATUSES = ("matched", "unverified")
REVIEWER_ROLES = ("owner", "assistant", "unspecified")
SCENE_KINDS = ("command", "diff")
SCENE_ORIGINS = ("source", "synthetic")
EXECUTION_STATES = ("suggested", "reported", "executed", "observed")
GIT_STATES = ("committed", "staged", "unstaged", "mixed")
QUESTION_DEPTHS = ("understand", "predict", "transfer")
SELECTION_SIGNALS = ("requested", "recurring", "recent", "general")


class LearningError(ValueError):
    """Safe, user-facing validation message; never includes private input."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def local_day(timestamp: str, timezone_name: str) -> date:
    return datetime.fromisoformat(timestamp).astimezone(ZoneInfo(timezone_name)).date()


def today(timezone_name: str) -> date:
    return utc_now().astimezone(ZoneInfo(timezone_name)).date()


def _object(value, required, optional=(), *, field="packet"):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise LearningError(f"{field}: 필수 항목 또는 지원하는 항목을 확인해 주세요.")
    return value


def _text(value, field, limit=8000, *, empty=False):
    if not isinstance(value, str) or len(value) > limit or (not empty and not value.strip()) or "\x00" in value:
        raise LearningError(f"{field}: 텍스트 길이와 내용을 확인해 주세요.")
    return value.strip()


def _key(value, field):
    if not isinstance(value, str) or not KEY.fullmatch(value):
        raise LearningError(f"{field}: 영문·숫자·하이픈으로 된 1–80자 식별자가 필요합니다.")
    return value


def _choice(value, choices, field):
    if not isinstance(value, str) or value not in choices:
        raise LearningError(f"{field}: 지원하는 값을 선택해 주세요.")
    return value


def _list(value, field, minimum, maximum):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise LearningError(f"{field}: 항목 수를 확인해 주세요.")
    return value


def _source(raw, current_day, *, literal=False):
    _object(raw, ("id", "kind", "title", "locator", "checked_on", "version", "snapshot"), ("url",), field="source")
    result = {"id": _key(raw["id"], "source.id"),
              "kind": _choice(raw["kind"], SOURCE_KINDS, "source.kind")}
    for field, limit in (("title", 240), ("locator", 2000), ("version", 240), ("snapshot", 12000)):
        result[field] = _text(raw[field], "source." + field, limit)
    checked = _text(raw["checked_on"], "source.checked_on", 10)
    try:
        checked_date = date.fromisoformat(checked)
    except ValueError:
        raise LearningError("source.checked_on: YYYY-MM-DD 날짜가 필요합니다.") from None
    if checked_date.isoformat() != checked or checked_date > current_day:
        raise LearningError("source.checked_on: 미래가 아닌 YYYY-MM-DD 날짜가 필요합니다.")
    result["checked_on"] = checked
    url = _text(raw.get("url", ""), "source.url", 2000, empty=True)
    if result["kind"] == "official":
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username
                     and not parsed.password and parsed.port in (None, 443)
                     and not any(char.isspace() or ord(char) < 32 for char in url)
                     and "\\" not in url)
        except ValueError:
            valid = False
        if not valid:
            raise LearningError("source.url: 공식 자료의 HTTPS 주소가 필요합니다.")
    elif url and not re.fullmatch(r"/(sessions|documents)/[1-9][0-9]*", url):
        raise LearningError("source.url: 업무 자료는 로컬 세션·문서 주소만 연결할 수 있습니다.")
    result["url"] = url
    if literal:
        result["snapshot"] = _literal(raw["snapshot"], "source.snapshot", 12000)
    result["snapshot_sha256"] = hashlib.sha256(result["snapshot"].encode()).hexdigest()
    return result


def _literal(value, field, limit=48000, *, empty=False):
    _text(value, field, limit, empty=empty)
    return value


def _day(value, field, current_day):
    value = _text(value, field, 10)
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise LearningError(f"{field}: YYYY-MM-DD 날짜가 필요합니다.") from None
    if parsed.isoformat() != value or parsed > current_day:
        raise LearningError(f"{field}: 미래가 아닌 날짜가 필요합니다.")
    return value


def _scene(raw, sources, current_day):
    common = ("kind", "source_id", "origin", "title", "language", "context",
              "conditions", "captured_at", "occurred_on")
    if not isinstance(raw, dict):
        raise LearningError("scene: 코드·명령의 원본 정보가 필요합니다.")
    kind = _choice(raw.get("kind"), SCENE_KINDS, "scene.kind")
    extra = ("code", "execution", "output") if kind == "command" else (
        "repo", "path", "before_ref", "after_ref", "git_state", "before", "after")
    _object(raw, common + extra, field="scene")
    scene = {"kind": kind, "source_id": _key(raw["source_id"], "scene.source_id"),
             "origin": _choice(raw["origin"], SCENE_ORIGINS, "scene.origin")}
    if scene["source_id"] not in sources or sources[scene["source_id"]]["kind"] != "work":
        raise LearningError("scene.source_id: 수업 안의 업무 근거를 연결해 주세요.")
    for field, limit in (("title", 240), ("language", 80), ("context", 8000), ("conditions", 8000)):
        scene[field] = _text(raw[field], "scene." + field, limit)
    scene["occurred_on"] = None if raw["occurred_on"] is None else _day(
        raw["occurred_on"], "scene.occurred_on", current_day)
    stamp = _text(raw["captured_at"], "scene.captured_at", 64)
    try:
        captured = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        raise LearningError("scene.captured_at: 시간대가 포함된 ISO 시각이 필요합니다.") from None
    if captured.tzinfo is None or captured.date() > current_day:
        raise LearningError("scene.captured_at: 미래가 아닌 시간대 포함 시각이 필요합니다.")
    scene["captured_at"] = captured.isoformat()
    if kind == "command":
        scene["code"] = _literal(raw["code"], "scene.code")
        scene["execution"] = _choice(raw["execution"], EXECUTION_STATES, "scene.execution")
        scene["output"] = _literal(raw["output"], "scene.output", empty=True)
        if scene["execution"] == "observed" and not scene["output"].strip():
            raise LearningError("scene.output: 결과 확인 상태에는 관측 자료가 필요합니다.")
        if scene["origin"] == "synthetic" and (scene["execution"] != "suggested" or scene["output"]):
            raise LearningError("scene.execution: 가상 명령은 실행·관측 기록으로 가져올 수 없습니다.")
    else:
        for field in ("repo", "path", "before_ref", "after_ref"):
            scene[field] = _text(raw[field], "scene." + field, 2000)
            if any(ord(char) < 32 for char in scene[field]):
                raise LearningError(f"scene.{field}: 한 줄의 식별자가 필요합니다.")
        scene["git_state"] = _choice(raw["git_state"], GIT_STATES, "scene.git_state")
        if scene["origin"] == "synthetic" and not (scene["repo"] == "synthetic" or scene["repo"].startswith("synthetic:")):
            raise LearningError("scene.repo: 가상 예시는 synthetic 식별자를 사용해 주세요.")
        for field in ("before", "after"):
            scene[field] = _literal(raw[field], "scene." + field, 96000, empty=True)
            scene[field + "_sha256"] = hashlib.sha256(scene[field].encode()).hexdigest()
            ref = scene[field + "_ref"]
            if scene["origin"] == "synthetic":
                valid = ref.startswith("synthetic:")
            elif scene["git_state"] == "committed":
                valid = re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", ref)
            else:
                valid = (re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", ref)
                         or ref == "sha256:" + scene[field + "_sha256"])
            if not valid:
                raise LearningError(f"scene.{field}_ref: 고정 commit 또는 해당 내용의 SHA-256이 필요합니다.")
        if (scene["origin"] == "source" and scene["git_state"] != "committed"
                and not any(scene[field + "_ref"].startswith("sha256:") for field in ("before", "after"))):
            raise LearningError("scene: 미커밋 변경에는 작업 트리 또는 index 내용의 SHA-256이 필요합니다.")
        if scene["before"] == scene["after"]:
            raise LearningError("scene: 변경 전후 내용이 같아 diff를 만들 수 없습니다.")
        lines = difflib.unified_diff(scene["before"].splitlines(keepends=True),
                                    scene["after"].splitlines(keepends=True),
                                    fromfile="a/" + scene["path"], tofile="b/" + scene["path"])
        scene["code"] = "".join(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
                                for line in lines)
    scene["code_sha256"] = hashlib.sha256(scene["code"].encode()).hexdigest()
    return scene


def _scene_question(question, scene):
    result = {"concept_id": _key(question["concept_id"], "question.concept_id"),
              "depth": _choice(question["depth"], QUESTION_DEPTHS, "question.depth"),
              "rationale": _text(question["rationale"], "question.rationale", 2000)}
    refs = _list(question["focus_lines"], "question.focus_lines", 1, 24)
    if any(type(line) is not int or not 1 <= line <= len(scene["code"].splitlines()) for line in refs):
        raise LearningError("question.focus_lines: 보존된 코드의 발췌 줄 번호가 필요합니다.")
    if len(set(refs)) != len(refs):
        raise LearningError("question.focus_lines: 중복된 줄 번호가 있습니다.")
    result["focus_lines"] = refs
    result["rubric"] = [_text(point, "question.rubric", 2000)
                        for point in _list(question["rubric"], "question.rubric", 1, 8)]
    if scene["source_id"] not in question["source_ids"]:
        raise LearningError("question.source_ids: 질문에서 실제 코드·명령의 업무 근거를 연결해 주세요.")
    return result


def _article(raw, scene, sources):
    _object(raw, ("intro", "code_range", "sections", "takeaway", "source_ids"), field="article")

    def references(value, field):
        refs = [_key(ref, field) for ref in _list(value, field, 1, 12)]
        if len(set(refs)) != len(refs) or any(ref not in sources for ref in refs) or not any(
            sources[ref]["kind"] == "official" for ref in refs
        ):
            raise LearningError(f"{field}: 수업 안의 공식 근거를 연결해 주세요.")
        return refs

    refs = references(raw["source_ids"], "article.source_ids")
    if scene["source_id"] not in refs:
        raise LearningError("article.source_ids: 글의 실제 작업 근거를 연결해 주세요.")
    code_range = _list(raw["code_range"], "article.code_range", 2, 2)
    if (any(type(line) is not int for line in code_range)
            or not 1 <= code_range[0] <= code_range[1] <= len(scene["code"].splitlines())
            or code_range[1] - code_range[0] >= 24):
        raise LearningError("article.code_range: 원본 안에서 최대 24줄의 연속 구간을 선택해 주세요.")
    sections, identifiers = [], set()
    for section in _list(raw["sections"], "article.sections", 2, 5):
        _object(section, ("id", "title", "body", "source_ids"), field="article.section")
        identifier = _key(section["id"], "article.section.id")
        if identifier in identifiers:
            raise LearningError("article.section.id: 글 안에서 고유한 식별자가 필요합니다.")
        identifiers.add(identifier)
        section_refs = references(section["source_ids"], "article.section.source_ids")
        if not set(section_refs) <= set(refs):
            raise LearningError("article.section.source_ids: 글의 전체 출처 목록에도 근거를 포함해 주세요.")
        sections.append({"id": identifier, "title": _text(section["title"], "article.section.title", 160),
                         "body": _text(section["body"], "article.section.body", 6000),
                         "source_ids": section_refs})
    return {"intro": _text(raw["intro"], "article.intro", 1600), "code_range": code_range,
            "sections": sections, "takeaway": _text(raw["takeaway"], "article.takeaway", 800),
            "source_ids": refs}


def validate_packet(raw, current_day: date) -> list[dict]:
    _object(raw, ("version", "lessons"))
    if type(raw["version"]) is not int or raw["version"] not in (1, 2):
        raise LearningError("packet.version: 지원하는 판본은 1과 2입니다.")
    scene_packet = raw["version"] == 2
    lessons = []
    keys = set()
    for item in _list(raw["lessons"], "lessons", 1, 30):
        _object(item, ("key", "title", "topic", "why", "explanation", "version_status",
                       "applicability", "sources", "questions") +
                (("scene", "selection", "authorship") if scene_packet else ()),
                ("reviewed_by",) + (("article",) if scene_packet else ()), field="lesson")
        lesson = {"key": _key(item["key"], "lesson.key")}
        lesson["reviewed_by"] = _choice(item.get("reviewed_by", "unspecified"), REVIEWER_ROLES, "reviewed_by")
        if lesson["key"] in keys:
            raise LearningError("lesson.key: 한 패킷에 같은 식별자가 중복되었습니다.")
        keys.add(lesson["key"])
        for field, limit in (("title", 240), ("topic", 120), ("why", 2000),
                             ("explanation", 12000), ("applicability", 2000)):
            lesson[field] = _text(item[field], "lesson." + field, limit)
        lesson["version_status"] = _choice(item["version_status"], VERSION_STATUSES, "version_status")
        sources = [_source(source, current_day, literal=scene_packet) for source in _list(item["sources"], "sources", 2, 12)]
        by_id = {source["id"]: source for source in sources}
        if len(by_id) != len(sources) or {s["kind"] for s in sources} != {"work", "official"}:
            raise LearningError("sources: 고유한 식별자와 업무·공식 자료가 모두 필요합니다.")
        if lesson["version_status"] == "matched" and any(
            s["version"].lower() == "unknown" for s in sources if s["kind"] == "official"
        ):
            raise LearningError("version_status: 적용 버전을 모르면 unverified로 기록해 주세요.")
        lesson["sources"] = sources
        if scene_packet:
            lesson["packet_version"] = 2
            lesson["scene"] = _scene(item["scene"], by_id, current_day)
            if "article" in item:
                lesson["article"] = _article(item["article"], lesson["scene"], by_id)
            selection = _object(item["selection"], ("signal", "reason"), field="selection")
            lesson["selection"] = {
                "signal": _choice(selection["signal"], SELECTION_SIGNALS, "selection.signal"),
                "reason": _text(selection["reason"], "selection.reason", 2000)}
            authored = _object(item["authorship"], ("author", "method", "reviewer", "authored_on"), field="authorship")
            lesson["authorship"] = {
                "author": _choice(authored["author"], ("owner", "assistant"), "authorship.author"),
                "method": _choice(authored["method"], ("manual",), "authorship.method"),
                "reviewer": _choice(authored["reviewer"], ("owner", "assistant"), "authorship.reviewer"),
                "authored_on": _day(authored["authored_on"], "authorship.authored_on", current_day)}
            if lesson["authorship"]["reviewer"] != lesson["reviewed_by"]:
                raise LearningError("authorship.reviewer: 수업의 검토 주체와 일치해야 합니다.")
        questions = []
        question_ids = set()
        for question in _list(item["questions"], "questions", 1, 12):
            _object(question, ("id", "kind", "prompt", "hint", "answer", "source_ids") +
                    (("concept_id", "depth", "focus_lines", "rationale", "rubric") if scene_packet else ()),
                    field="question")
            q = {"id": _key(question["id"], "question.id"),
                 "kind": _choice(question["kind"], QUESTION_KINDS, "question.kind")}
            if q["id"] in question_ids:
                raise LearningError("question.id: 한 수업 안에 중복된 식별자가 있습니다.")
            question_ids.add(q["id"])
            for field in ("prompt", "hint", "answer"):
                q[field] = _text(question[field], "question." + field)
            refs = [_key(ref, "question.source_ids") for ref in _list(question["source_ids"], "question.source_ids", 1, 12)]
            if len(set(refs)) != len(refs) or any(ref not in by_id for ref in refs) or not any(
                by_id[ref]["kind"] == "official" for ref in refs
            ):
                raise LearningError("question.source_ids: 수업에 포함된 공식 근거를 연결해 주세요.")
            q["source_ids"] = refs
            if scene_packet:
                q.update(_scene_question(question, lesson["scene"]))
            questions.append(q)
        lesson["questions"] = questions
        if scene_packet and {q["concept_id"] for q in questions} != {
            q["concept_id"] for q in questions if q["depth"] == "understand"
        }:
            raise LearningError("questions: 각 개념에 역할·흐름을 이해하는 질문이 필요합니다.")
        lessons.append(lesson)
    return lessons


def import_packet(connection: sqlite3.Connection, raw, timezone_name: str) -> dict:
    lessons = validate_packet(raw, today(timezone_name))
    if len(json.dumps(raw, ensure_ascii=False).encode()) > MAX_PACKET_BYTES:
        raise LearningError("패킷은 2 MiB 이하여야 합니다.")
    for lesson in lessons:
        for source in lesson["sources"]:
            if source["kind"] == "work" and source["url"]:
                _, route, identifier = source["url"].split("/")
                table = "sessions" if route == "sessions" else "context_documents"
                if len(identifier) > 18 or connection.execute(
                    f"SELECT 1 FROM {table} WHERE id = ?", (int(identifier),)
                ).fetchone() is None:
                    raise LearningError("source.url: 업무 원문을 찾을 수 없습니다. 주소를 비우고 원래 위치를 locator에 남겨 주세요.")
    # All validation precedes writes. The caller owns commit/rollback of this batch.
    inserted = 0
    for lesson in lessons:
        content = json.dumps(lesson, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        revision = hashlib.sha256(content.encode()).hexdigest()
        cursor = connection.execute(
            "INSERT INTO learning_lessons (lesson_key, revision, title, packet_json, created_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(lesson_key, revision) DO NOTHING",
            (lesson["key"], revision, lesson["title"], content, utc_now().isoformat()),
        )
        inserted += cursor.rowcount
    return {"inserted": inserted, "unchanged": len(lessons) - inserted}


def lesson_by_id(connection, lesson_id: int) -> dict:
    if not 0 < lesson_id < 2**63:
        raise LearningError("수업을 찾을 수 없습니다. 학습 목록에서 다시 선택해 주세요.")
    row = connection.execute("SELECT * FROM learning_lessons WHERE id = ?", (lesson_id,)).fetchone()
    if row is None:
        raise LearningError("수업을 찾을 수 없습니다. 학습 목록에서 다시 선택해 주세요.")
    return {**dict(row), **json.loads(row["packet_json"])}


def attempts_for(connection, lesson_id: int) -> list[dict]:
    return [dict(row) for row in connection.execute(
        "SELECT * FROM learning_attempts WHERE lesson_id = ? ORDER BY submitted_at, id", (lesson_id,)
    )]


def completed_days(attempts: list[dict], timezone_name: str, before: date | None = None) -> dict:
    by_day = {}
    for attempt in sorted(attempts, key=lambda a: (a["assessed_at"] or "", a["id"])):
        if attempt["outcome"] == "pending":
            continue
        day = local_day(attempt["assessed_at"], timezone_name)
        if before is None or day < before:
            by_day[day] = attempt
    return by_day


def schedule(attempts: list[dict], timezone_name: str, before: date | None = None) -> dict:
    days = completed_days(attempts, timezone_name, before)
    streak = 0
    due = None
    for day, attempt in sorted(days.items()):
        if attempt["outcome"] == "recalled" and not attempt["hint_used"]:
            streak += 1
            interval = (3, 7, 21)[min(streak, 3) - 1]
        else:
            streak = 0
            interval = 1
        due = day + timedelta(days=interval)
    return {"due": due, "days": len(days)}


def _feedback_aware_attempts(lesson, attempts, timezone_name):
    """Conservative derived scheduling input; never rewrite the stored hint report."""
    if not lesson.get("scene"):
        return attempts
    questions = {q["id"]: q for q in lesson["questions"]}
    exposed = set()
    result = []
    for attempt in sorted(attempts, key=lambda a: (a["submitted_at"], a["id"])):
        key = (local_day(attempt["submitted_at"], timezone_name),
               questions[attempt["question_id"]]["concept_id"])
        assisted = key in exposed
        result.append({**attempt, "feedback_assisted": assisted,
                       "hint_used": int(bool(attempt["hint_used"] or assisted))})
        # Every stored answer or explicit read makes feedback available.
        exposed.add(key)
    return result


def _next_question(lesson, attempts, timezone_name):
    current_day = today(timezone_name)
    questions = lesson["questions"]
    if not lesson.get("scene"):
        return questions[len(completed_days(attempts, timezone_name, before=current_day)) % len(questions)]
    previous = [a for a in _feedback_aware_attempts(lesson, attempts, timezone_name)
                if a["outcome"] != "pending"
                and local_day(a["assessed_at"], timezone_name) < current_day
                and local_day(a["submitted_at"], timezone_name) < current_day]
    concepts = list(dict.fromkeys(q["concept_id"] for q in questions))
    by_id = {q["id"]: q for q in questions}
    def concept_days(concept):
        return {local_day(a["submitted_at"], timezone_name) for a in previous
                if by_id[a["question_id"]]["concept_id"] == concept}
    concept = min(concepts, key=lambda value: (len(concept_days(value)), concepts.index(value)))
    candidates = [q for q in questions if q["concept_id"] == concept]
    depth = "understand"
    for level in QUESTION_DEPTHS:
        at_level = {q["id"] for q in candidates if q["depth"] == level}
        if not at_level:
            continue
        depth = level
        by_day = {}
        for attempt in sorted(previous, key=lambda a: (a["assessed_at"], a["id"])):
            if attempt["question_id"] in at_level:
                by_day[local_day(attempt["submitted_at"], timezone_name)] = attempt
        streak = 0
        for _, attempt in sorted(by_day.items()):
            streak = streak + 1 if attempt["outcome"] == "recalled" and not attempt["hint_used"] else 0
        if streak < 2:
            break
    eligible = [q for q in candidates if q["depth"] == depth]
    def last_day(question):
        return max((local_day(a["submitted_at"], timezone_name) for a in previous
                    if a["question_id"] == question["id"]), default=date.min)
    return min(eligible, key=lambda q: (last_day(q), questions.index(q)))


def library(connection, timezone_name: str) -> list[dict]:
    current_day = today(timezone_name)
    rows = connection.execute(
        "SELECT l.*, COALESCE(v.hidden, 0) AS hidden, v.snoozed_until "
        "FROM learning_lessons l LEFT JOIN learning_visibility v ON v.lesson_key = l.lesson_key "
        "WHERE l.id IN (SELECT MAX(id) FROM learning_lessons GROUP BY lesson_key) ORDER BY l.id"
    ).fetchall()
    result = []
    for row in rows:
        lesson = {**dict(row), **json.loads(row["packet_json"])}
        attempts = attempts_for(connection, lesson["id"])
        effective = _feedback_aware_attempts(lesson, attempts, timezone_name)
        lesson["before_today"] = schedule(effective, timezone_name, before=current_day)
        lesson["schedule"] = schedule(effective, timezone_name)
        prior_done = completed_days(effective, timezone_name, before=current_day)
        lesson["last_prior_assessment"] = prior_done[max(prior_done)] if prior_done else None
        lesson["prior_pending"] = next((a for a in attempts
                                        if local_day(a["submitted_at"], timezone_name) < current_day
                                        and (a["outcome"] == "pending" or
                                             local_day(a["assessed_at"], timezone_name) >= current_day)), None)
        lesson["done_today"] = current_day in completed_days(attempts, timezone_name)
        lesson["snoozed"] = bool(lesson["snoozed_until"] and lesson["snoozed_until"] > current_day.isoformat())
        pending_attempt = next((a for a in attempts if a["outcome"] == "pending"), None)
        lesson["pending"] = pending_attempt["id"] if pending_attempt else None
        if lesson.get("scene") and pending_attempt is None:
            pending_attempt = next((a for a in reversed(attempts) if a["outcome"] != "pending"
                                    and local_day(a["assessed_at"], timezone_name) == current_day), None)
        lesson["question"] = next(q for q in lesson["questions"] if q["id"] == pending_attempt["question_id"]) if pending_attempt else _next_question(lesson, attempts, timezone_name)
        result.append(lesson)
    return result


def daily_selection(connection, timezone_name: str) -> dict:
    lessons = library(connection, timezone_name)
    current_day = today(timezone_name)
    eligible = [lesson for lesson in lessons if not lesson["hidden"] and not lesson["snoozed"]]
    pending = sorted((l for l in eligible if l["prior_pending"]),
                     key=lambda l: (l["prior_pending"]["submitted_at"], l["id"]))
    def review_order(lesson):
        last = lesson["last_prior_assessment"]
        needs_help = last and (last["outcome"] != "recalled" or last["hint_used"])
        return (not needs_help, lesson["before_today"]["due"], lesson["id"])
    due = sorted((l for l in eligible if l["before_today"]["due"] is not None
                  and l["before_today"]["due"] <= current_day), key=review_order)
    def new_order(lesson):
        signal = lesson.get("selection", {}).get("signal", "general")
        occurred = lesson.get("scene", {}).get("occurred_on")
        return (SELECTION_SIGNALS.index(signal),
                -(date.fromisoformat(occurred).toordinal() if occurred else 0), lesson["id"])
    new = sorted((l for l in eligible if l["before_today"]["due"] is None), key=new_order)
    chosen = (pending or due or new)[:1]
    is_review = bool(pending or due)
    return {"new_lessons": [] if is_review else chosen, "reviews": chosen if is_review else [],
            "selected_lessons": chosen, "has_lessons": bool(lessons),
            "all_done": bool(chosen) and chosen[0]["done_today"], "day": current_day.isoformat()}


def reader(connection, lesson_id: int, timezone_name: str, attempt_id: int | None = None,
           question_id: str | None = None) -> dict:
    lesson = lesson_by_id(connection, lesson_id)
    for source in lesson["sources"]:
        source["available"] = True
        if source["kind"] == "work" and source["url"]:
            _, route, identifier = source["url"].split("/")
            table = "sessions" if route == "sessions" else "context_documents"
            source["available"] = connection.execute(
                f"SELECT 1 FROM {table} WHERE id = ?", (int(identifier),)
            ).fetchone() is not None
    attempts = attempts_for(connection, lesson_id)
    current_day = today(timezone_name)
    attempt = next((a for a in attempts if a["id"] == attempt_id), None) if attempt_id is not None else next(
        (a for a in attempts if a["outcome"] == "pending"), None
    )
    if question_id is not None and attempt_id is None:
        attempt = None
    elif lesson.get("scene") and attempt_id is None and attempt is None:
        attempt = next((a for a in reversed(attempts) if a["outcome"] != "pending"
                        and local_day(a["assessed_at"], timezone_name) == current_day), None)
    if attempt_id is not None and attempt is None:
        raise LearningError("이 수업의 답변 기록을 찾을 수 없습니다.")
    questions = lesson["questions"]
    if attempt:
        question = next(q for q in questions if q["id"] == attempt["question_id"])
    elif question_id is not None:
        question = next((q for q in questions if q["id"] == question_id), None)
        if question is None:
            raise LearningError("이 수업의 질문을 찾을 수 없습니다. 학습 목록에서 다시 열어 주세요.")
    else:
        question = _next_question(lesson, attempts, timezone_name)
    effective = _feedback_aware_attempts(lesson, attempts, timezone_name)
    assisted = bool(attempt and next(a for a in effective if a["id"] == attempt["id"]).get("feedback_assisted"))
    latest = connection.execute("SELECT MAX(id) FROM learning_lessons WHERE lesson_key = ?", (lesson["key"],)).fetchone()[0]
    old = [dict(row) for row in connection.execute(
        "SELECT id, created_at FROM learning_lessons WHERE lesson_key = ? AND id != ? ORDER BY id DESC",
        (lesson["key"], lesson_id),
    )]
    return {"lesson": lesson, "question": question, "attempt": attempt,
            "history": list(reversed(attempts[-10:])), "other_revisions": old,
            "latest_id": latest, "schedule": schedule(effective, timezone_name),
            "feedback_assisted": assisted,
            "practice_questions": [q for q in questions if q["id"] != question["id"]],
            "scene_lines": lesson.get("scene", {}).get("code", "").splitlines(),
            "source_review_due": any((current_day - date.fromisoformat(s["checked_on"])).days > 90
                                     for s in lesson["sources"]),
            "confidence_labels": {value: display_value_label("learning.confidence", value) for value in CONFIDENCE_VALUES},
            "outcome_labels": {value: display_value_label("learning.outcome", value) for value in OUTCOME_VALUES}}


def submit_attempt(connection, lesson_id: int, fields: dict) -> int:
    lesson = lesson_by_id(connection, lesson_id)
    question_id = _key(fields.get("question_id"), "질문")
    if question_id not in {q["id"] for q in lesson["questions"]}:
        raise LearningError("이 수업의 질문을 다시 선택해 주세요.")
    submission_key = _key(fields.get("submission_key"), "제출 식별자")
    action = _choice(fields.get("action"), {"answer", "read"}, "학습 방식")
    if action == "read":
        answer, confidence, hint_used, outcome = "", None, 0, "read"
    else:
        answer = _text(fields.get("answer", ""), "답변")
        confidence = _choice(fields.get("confidence"), CONFIDENCE_VALUES, "확신 정도")
        hint_used = int(_choice(fields.get("hint_used", "0"), {"0", "1"}, "힌트"))
        outcome = "pending"
    existing = connection.execute("SELECT * FROM learning_attempts WHERE submission_key = ?", (submission_key,)).fetchone()
    if existing:
        expected = (lesson_id, question_id, answer, confidence, hint_used, action == "read")
        actual = (existing["lesson_id"], existing["question_id"], existing["answer"],
                  existing["confidence"], existing["hint_used"], existing["outcome"] == "read")
        if expected != actual:
            raise LearningError("이미 사용한 제출입니다. 수업을 다시 열어 새 답변을 작성해 주세요.")
        return existing["id"]
    stamp = utc_now().isoformat()
    cursor = connection.execute(
        "INSERT INTO learning_attempts (lesson_id, question_id, submission_key, answer, confidence, "
        "hint_used, outcome, submitted_at, assessed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (lesson_id, question_id, submission_key, answer, confidence, hint_used, outcome, stamp,
         stamp if action == "read" else None),
    )
    return cursor.lastrowid


def assess_attempt(connection, lesson_id: int, attempt_id: int, outcome: str) -> None:
    lesson_by_id(connection, lesson_id)
    _choice(outcome, {"again", "partial", "recalled"}, "자기 평가")
    row = connection.execute("SELECT * FROM learning_attempts WHERE id = ? AND lesson_id = ?", (attempt_id, lesson_id)).fetchone()
    if row is None:
        raise LearningError("답변을 먼저 저장해 주세요.")
    if row["outcome"] == outcome:
        return
    if row["outcome"] != "pending":
        raise LearningError("이미 마친 자기 평가입니다. 기록을 확인하거나 다음 복습에서 다시 답해 주세요.")
    changed = connection.execute(
        "UPDATE learning_attempts SET outcome = ?, assessed_at = ? WHERE id = ? AND outcome = 'pending'",
        (outcome, utc_now().isoformat(), attempt_id),
    ).rowcount
    if not changed:
        raise LearningError("다른 화면에서 자기 평가가 변경되었습니다. 기록을 다시 확인해 주세요.")


def set_visibility(connection, lesson_id: int, action: str, timezone_name: str) -> None:
    lesson = lesson_by_id(connection, lesson_id)
    _choice(action, {"snooze", "hide", "restore"}, "목록 표시")
    until = (today(timezone_name) + timedelta(days=1)).isoformat() if action == "snooze" else None
    connection.execute(
        "INSERT INTO learning_visibility (lesson_key, hidden, snoozed_until, updated_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(lesson_key) DO UPDATE SET hidden = excluded.hidden, "
        "snoozed_until = excluded.snoozed_until, updated_at = excluded.updated_at",
        (lesson["key"], int(action == "hide"), until, utc_now().isoformat()),
    )
