"""User-managed source registration without moving or editing originals."""

import base64
import hashlib
import json
from contextlib import closing
import os
from pathlib import Path

from .config import settings
from .db import connect, transaction
from .local_operations import operation_lock
from .preferences import PreferencesError, atomic_private_write, tomllib
from .session_sources import load_session_source_settings, load_and_reconcile_session_sources, session_sources_path, session_sources_text
from .source_profiles import PALETTE, default_color, valid_source_id
from .ingest.contracts import (
    CLAUDE_SESSION_REVISION,
    CODEX_SESSION_REVISION,
    SessionRevisionError,
)
from .ingest.sync.storage import _check_session_revision


def source_configuration(config=settings):
    result = load_session_source_settings(config)
    if result.file_error:
        raise PreferencesError("세션 소스 설정을 읽지 못했습니다. 기존 파일을 확인해 주세요.")
    content = result.settings_path.read_bytes()
    return tomllib.loads(content.decode("utf-8")), hashlib.sha256(content).hexdigest(), result


def _restore_failed_write(path, before, attempted):
    actual = path.read_bytes()
    if actual == before:
        return
    if attempted is None or actual != attempted:
        raise PreferencesError("저장 중 설정 파일이 변경되었습니다. 현재 파일을 보존했습니다.")
    atomic_private_write(path, before)


def migrate_source_settings(config=settings):
    """One-time file upgrade; current settings contain only numeric identities."""
    from .source_identity_migration import upgrade_config, restore_config
    path = session_sources_path(config)
    if not path.exists():
        return
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return
    if raw.get("schema_version") != 1:
        return
    recovery = None
    with operation_lock(config, "source-migration"):
        try:
            with transaction() as connection:
                recovery = upgrade_config(connection, config)
                registry = load_and_reconcile_session_sources(connection, config)
                if any(d.code != "config_missing" for d in registry.diagnostics):
                    raise PreferencesError("기존 프로필 설정을 확인해 주세요. 파일은 보존했습니다.")
        except Exception:
            restore_config(recovery)
            raise


def source_inventory(config=settings):
    migrate_source_settings(config)
    raw, revision, parsed = source_configuration(config)
    if parsed.schema_version != 2 and not parsed.diagnostics:
        raise PreferencesError("기존 프로필 ID·도구·세션 경로가 일치하는지 확인해 주세요. 설정 파일은 보존했습니다.")
    with closing(connect()) as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM sources WHERE provider_kind IN ('claude','codex') ORDER BY profile_position,id")]
    by_id = {row["id"]: row for row in rows}
    # Manual file edits use the same validated projection as UI writes. Avoid a
    # writer lock for the ordinary unchanged settings read during ingestion.
    changed = parsed.schema_version == 2 and not parsed.diagnostics and any(
        entry.source_id not in by_id or any((
            by_id[entry.source_id]["name"] != entry.display_label,
            by_id[entry.source_id]["provider_kind"] != entry.provider_kind,
            by_id[entry.source_id]["root_path"] != str(entry.root),
            by_id[entry.source_id]["profile_color"] != (entry.color or default_color(entry.provider_kind)),
            by_id[entry.source_id]["profile_position"] != position,
        )) for position, entry in enumerate(parsed.entries)
    )
    configured_ids = {entry.source_id for entry in parsed.entries}
    changed = changed or (parsed.schema_version == 2 and not parsed.diagnostics and any(
        row["id"] not in configured_ids and row["profile_position"] != 2147483647 for row in rows))
    if changed:
        with operation_lock(config, "source-settings"), transaction() as connection:
            raw, revision, parsed = source_configuration(config)
            registry = load_and_reconcile_session_sources(connection, config)
            if any(d.code != "config_missing" for d in registry.diagnostics):
                raise PreferencesError("프로필 설정을 적용하지 못했습니다. ID·도구·세션 경로를 확인해 주세요.")
            rows = [dict(row) for row in connection.execute("SELECT * FROM sources WHERE provider_kind IN ('claude','codex') ORDER BY profile_position,id")]
    entries = {entry["source_id"]: entry for entry in raw["session_sources"]
               if isinstance(entry, dict) and valid_source_id(entry.get("source_id"))}
    statuses = {item.source_id: item.availability for item in parsed.entries}
    for row in rows:
        entry = entries.get(row["id"], {})
        row.update(configured=bool(entry), registered=bool(entry) and entry.get("enabled", True), agent_home=entry.get("agent_home", ""),
                   availability=statuses.get(row["id"], "config_missing"),
                   color=row["profile_color"] or default_color(row["provider_kind"]))
        row.pop("profile_color")
        row.pop("profile_position")
    return dict(revision=revision, sources=rows, palette=[dict(value=k, label=v) for k, v in PALETTE.items()],
                diagnostics=[dict(code=d.code, message=d.message, source_id=d.source_id) for d in parsed.diagnostics])


def candidates():
    choices = [("codex", "Codex", Path.home() / ".codex"),
               ("claude", "Claude Code", Path.home() / ".claude")]
    return [dict(provider_kind=provider, display_label=label, agent_home=str(home),
                 root=str(home / ("sessions" if provider == "codex" else "projects")))
            for provider, label, home in choices if home.is_dir()]


def update_source(payload, config=settings):
    with operation_lock(config, "source-settings"):
        migrate_source_settings(config)
        raw, revision, parsed = source_configuration(config)
        if payload.get("revision") != revision:
            raise PreferencesError("소스 설정이 변경되었습니다. 목록을 다시 불러온 뒤 저장해 주세요.")
        if parsed.diagnostics or parsed.schema_version != 2:
            raise PreferencesError("기존 소스 설정의 오류를 먼저 해결해 주세요. 파일은 보존했습니다.")
        entries = raw["session_sources"]
        source_id = payload.get("source_id")
        if "source_key" in payload:
            raise PreferencesError("프로필 ID 형식이 변경되었습니다. 설정을 다시 열어 주세요.")
        if source_id is not None and not valid_source_id(source_id):
            raise PreferencesError("프로필 ID를 확인해 주세요.")
        current = next((entry for entry in entries if entry["source_id"] == source_id), None)
        def configured_root(entry):
            root = Path(entry["root"]).expanduser()
            return root if root.is_absolute() else session_sources_path(config).parent / root
        if current:
            current["root"] = str(configured_root(current))
        action = payload.get("action", "save")
        if not isinstance(action, str) or action not in {"save", "remove", "reconnect", "color", "reorder"}:
            raise PreferencesError("지원하지 않는 소스 작업입니다.")
        if source_id is not None and current is None:
            with closing(connect()) as connection:
                retained = connection.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
            if not retained or retained["provider_kind"] not in {"codex", "claude"}:
                raise PreferencesError("등록된 소스를 찾지 못했습니다.")
            if action not in {"save", "reconnect"}:
                raise PreferencesError("프로필을 다시 등록한 뒤 변경해 주세요.")
            current = dict(source_id=source_id, display_label=retained["name"], provider_kind=retained["provider_kind"],
                           root=retained["root_path"], color=retained["profile_color"] or default_color(retained["provider_kind"]), enabled=False)
            entries.append(current)
        replacement = None
        if action == "reorder":
            order = payload.get("source_ids")
            expected = [entry["source_id"] for entry in entries]
            if (not isinstance(order, list) or not all(valid_source_id(i) for i in order)
                    or len(order) != len(expected) or len(set(order)) != len(order) or set(order) != set(expected)):
                raise PreferencesError("프로필 순서가 현재 목록과 다릅니다. 목록을 다시 불러와 주세요.")
            by_id = {entry["source_id"]: entry for entry in entries}
            entries = [by_id[i] for i in order]
        elif action == "remove":
            if not current:
                raise PreferencesError("해제할 소스를 선택해 주세요.")
            replacement = {**current, "enabled": False}
        elif action == "color":
            if not current or not isinstance(payload.get("color"), str) or payload["color"] not in PALETTE:
                raise PreferencesError("프로필과 색상을 확인해 주세요.")
            replacement = {**current, "color": payload["color"]}
        else:
            provider, label = payload.get("provider_kind"), payload.get("display_label", "")
            if not isinstance(provider, str) or provider not in {"codex", "claude"} or (current and current["provider_kind"] != provider):
                raise PreferencesError("소스 도구 종류를 확인해 주세요. 기존 소스의 종류는 바꿀 수 없습니다.")
            if not isinstance(label, str) or not 1 <= len(label.strip()) <= 160:
                raise PreferencesError("표시 이름은 1~160자로 입력해 주세요.")
            home, raw_root = payload.get("agent_home", ""), payload.get("root", "")
            if not isinstance(home, str) or len(home) > 4096:
                raise PreferencesError("Home 경로를 확인해 주세요.")
            if not isinstance(raw_root, str) or not raw_root.strip() or len(raw_root) > 4096:
                raise PreferencesError("실제로 읽을 세션 경로를 입력해 주세요.")
            root = Path(raw_root.strip()).expanduser()
            if not root.is_absolute():
                raise PreferencesError("세션 위치는 절대 경로로 입력해 주세요.")
            root = root.resolve()
            if not current and (not root.is_dir() or not os.access(root, os.R_OK | os.X_OK)):
                raise PreferencesError("읽을 수 있는 세션 폴더를 선택해 주세요.")
            for entry in entries:
                other = configured_root(entry).resolve()
                if entry is not current and not entry.get("enabled", True):
                    if root == other:
                        raise PreferencesError("등록을 해제한 같은 경로가 있습니다. 해당 소스의 ‘다시 등록’을 사용해 주세요.")
                    continue
                if entry is not current and (root == other or root in other.parents or other in root.parents):
                    raise PreferencesError("다른 세션 소스와 경로가 겹칩니다. 하나의 소스로 등록해 주세요.")
            color = payload.get("color", current.get("color", default_color(provider)) if current else default_color(provider))
            if not isinstance(color, str) or color not in PALETTE:
                raise PreferencesError("지원하는 프로필 색상을 선택해 주세요.")
            # Preserve the imported lexical path when it resolves to the same
            # folder (for example /var vs /private/var on macOS).
            stored_root = current["root"] if current and root == configured_root(current).resolve() else str(root)
            replacement = dict(source_id=source_id, display_label=label.strip(), provider_kind=provider,
                               root=stored_root, enabled=True, color=color)
            if home.strip():
                agent_home = Path(home.strip()).expanduser()
                if not agent_home.is_absolute():
                    raise PreferencesError("Home은 절대 경로로 입력해 주세요.")
                replacement["agent_home"] = str(agent_home.resolve())
        path = session_sources_path(config)
        original = path.read_bytes()
        attempted = None
        journal = config.data_dir / "source-reconnect.json"
        changed_root = bool(current and replacement and Path(current["root"]).expanduser().resolve() != Path(replacement["root"]).expanduser().resolve())
        try:
            with transaction() as connection:
                # Reserve restored/configured IDs before allocating a new PK.
                registry = load_and_reconcile_session_sources(connection, config)
                if any(d.code != "config_missing" for d in registry.diagnostics):
                    raise PreferencesError("기존 프로필 설정을 확인해 주세요. 파일은 보존했습니다.")
                if replacement is not None:
                    if current is None:
                        source_id = connection.execute("SELECT COALESCE(MAX(id),0)+1 FROM sources").fetchone()[0]
                        if not valid_source_id(source_id):
                            raise PreferencesError("새 프로필 ID를 만들지 못했습니다. 기존 등록은 보존했습니다.")
                        connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (?,?,?,?)",
                                           (source_id, replacement["provider_kind"], replacement["display_label"], replacement["root"]))
                        replacement["source_id"] = source_id
                        entries.append(replacement)
                    else:
                        entries = [replacement if entry is current else entry for entry in entries]
                updated = session_sources_text(entries).encode()
                if changed_root:
                    if action != "reconnect" or payload.get("confirm_same_source") is not True:
                        raise PreferencesError("경로 변경은 ‘같은 소스 재연결’로 확인해 주세요.")
                    atomic_private_write(journal, json.dumps({"source_id": source_id, "old_root": current["root"],
                        "new_root": replacement["root"], "before": base64.b64encode(original).decode(),
                        "after_sha256": hashlib.sha256(updated).hexdigest()}).encode())
                    _reconnect(connection, current, replacement)
                if path.read_bytes() != original:
                    raise PreferencesError("저장 중 설정이 변경되었습니다. 현재 파일을 보존했습니다.")
                attempted = updated
                atomic_private_write(path, updated)
                registry = load_and_reconcile_session_sources(connection, config)
                if any(d.code != "config_missing" for d in registry.diagnostics):
                    raise PreferencesError("소스 설정을 적용하지 못했습니다. 기존 등록을 보존했습니다.")
        except Exception:
            _restore_failed_write(path, original, attempted)
            journal.unlink(missing_ok=True)
            raise
        journal.unlink(missing_ok=True)
    return source_inventory(config)


def _reconnect(connection, before, after):
    old, new = Path(before["root"]).expanduser().resolve(), Path(after["root"])
    if not new.is_dir() or not os.access(new, os.R_OK | os.X_OK):
        raise PreferencesError("재연결할 폴더를 읽을 수 없습니다.")
    source = connection.execute("SELECT id FROM sources WHERE id=?", (before["source_id"],)).fetchone()
    if not source:
        return
    source_id = source["id"]
    revision = {"codex": CODEX_SESSION_REVISION, "claude": CLAUDE_SESSION_REVISION}[
        before["provider_kind"]
    ]
    try:
        _check_session_revision(connection, source_id, revision)
    except SessionRevisionError as error:
        raise PreferencesError(str(error)) from error
    rows = connection.execute("SELECT id,source_path,external_id FROM sessions WHERE source_id=?", (source_id,)).fetchall()
    rewrites = []
    for row in rows:
        try:
            target = new / Path(row["source_path"]).relative_to(old)
        except ValueError:
            raise PreferencesError("기존 세션 경로가 등록된 폴더와 일치하지 않습니다.") from None
        if not target.is_file():
            raise PreferencesError("기존 세션 파일이 새 위치에 모두 있는지 확인해 주세요. 기존 기록은 유지됩니다.")
        from localbrain.ingest.providers.codex import parse_codex_session
        from localbrain.ingest.providers.claude import parse_claude_session
        parser = parse_codex_session if before["provider_kind"] == "codex" else parse_claude_session
        try:
            if parser(target).external_id != row["external_id"]:
                raise PreferencesError("새 위치의 세션 ID가 기존 소스와 다릅니다.")
        except (OSError, ValueError) as error:
            raise PreferencesError("새 위치의 세션 동일성을 확인하지 못했습니다. 기존 등록을 보존했습니다.") from error
        rewrites.append((str(target), row["id"]))
    connection.executemany("UPDATE sessions SET source_path=? WHERE id=?", rewrites)
    for row in connection.execute("SELECT id,path FROM source_files WHERE source_id=?", (source_id,)).fetchall():
        try:
            target = new / Path(row["path"]).relative_to(old)
        except ValueError:
            continue
        connection.execute("UPDATE source_files SET path=?,session_contract_version=NULL WHERE id=?", (str(target), row["id"]))
    connection.execute("UPDATE sources SET root_path=? WHERE id=?", (str(new), source_id))


def registered_session_roots(config=settings):
    parsed = load_session_source_settings(config)
    if parsed.file_error:
        return {}
    return {entry.source_id: str(entry.root) for entry in parsed.entries if entry.enabled and entry.availability == "ready"}


def recover_source_reconnect(config=settings):
    journal = config.data_dir / "source-reconnect.json"
    if not journal.exists():
        return
    with operation_lock(config, "source-recovery"):
        value = json.loads(journal.read_text())
        path = session_sources_path(config)
        current = path.read_bytes()
        original = base64.b64decode(value["before"])
        if current != original and hashlib.sha256(current).hexdigest() != value["after_sha256"]:
            raise PreferencesError("중단된 소스 재연결 후 설정이 변경되었습니다. 기존 파일과 source-reconnect.json을 보존했습니다.")
        with closing(connect()) as connection:
            row = connection.execute("SELECT root_path FROM sources WHERE id=?", (value["source_id"],)).fetchone()
        if not row or row["root_path"] != value["new_root"]:
            atomic_private_write(path, original)
        journal.unlink()
