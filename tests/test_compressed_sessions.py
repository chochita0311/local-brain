import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

if sys.version_info >= (3, 14):
    from compression import zstd
else:
    from backports import zstd

from localbrain.ingest.common import read_json_lines
from localbrain.ingest.contracts import (
    CODEX_SESSION_REVISION,
    CODEX_USAGE_CONTRACT_VERSION,
    SessionRevisionError,
)
from localbrain.ingest.providers.codex import parse_codex_session
from localbrain.ingest.sync.sessions import _scan_session_source, _session_paths
from localbrain.sessions.pins import pin_session


SCHEMA = Path(__file__).parents[1] / "src/localbrain/schema.sql"


class CompressedSessionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="localbrain-compressed-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.connection = sqlite3.connect(":memory:")
        self.addCleanup(self.connection.close)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA.read_text())
        self.sources = {}
        for name in ("personal", "company"):
            root = self.root / name / "sessions"
            root.mkdir(parents=True)
            identity = self.connection.execute(
                "INSERT INTO sources(provider_kind,name,root_path) VALUES ('codex',?,?)",
                (name, str(root)),
            ).lastrowid
            self.sources[name] = identity, root

    def records(self, identity="native-session"):
        return [
            {"type": "session_meta", "payload": {"id": identity, "cwd": "/synthetic/project"}},
            {"type": "turn_context", "payload": {"turn_id": "turn", "model": "gpt-5.5"}},
            {"type": "event_msg", "timestamp": "2026-06-28T01:00:00Z",
             "payload": {"type": "user_message", "message": "질문 https://docs.example.test/guide"}},
            {"type": "event_msg", "timestamp": "2026-06-28T01:00:01Z",
             "payload": {"type": "token_count", "info": {"last_token_usage": {
                 "input_tokens": 1000, "cached_input_tokens": 800, "output_tokens": 100,
                 "reasoning_output_tokens": 40, "total_tokens": 1100,
             }}}},
        ]

    def write(self, path, records=None):
        content = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode()
                           for row in (self.records() if records is None else records))
        path.write_bytes(zstd.compress(content) if path.suffix == ".zst" else content)
        return path

    def scan(self, name="personal", revision=CODEX_SESSION_REVISION):
        source_id, root = self.sources[name]
        return _scan_session_source(
            self.connection, source_id, name, root, parse_codex_session,
            CODEX_USAGE_CONTRACT_VERSION, provider_kind="codex",
            session_contract_version=revision,
        )

    def rows(self, table):
        return [tuple(row) for row in self.connection.execute(f"SELECT * FROM {table} ORDER BY rowid")]

    def frozen_usage(self):
        # A real rescan may advance its import observation, not its frozen facts.
        return [{key: row[key] for key in row.keys() if key != "imported_at"}
                for row in self.connection.execute("SELECT * FROM usage_records ORDER BY id")]

    def test_compressed_multiframe_matches_plain_lines_and_missing_meta_identity(self):
        plain = self.sources["personal"][1] / "fallback.jsonl"
        archive = plain.with_suffix(".jsonl.zst")
        for records in (self.records(), self.records()[1:]):
            self.write(plain, records)
            raw = plain.read_bytes() + b"bad-json\n"
            plain.write_bytes(raw)
            split = raw.index("질문".encode()) + 1
            archive.write_bytes(zstd.compress(raw[:split]) + zstd.compress(raw[split:]))
            self.assertEqual(list(read_json_lines(plain)), list(read_json_lines(archive)))
            left, right = asdict(parse_codex_session(plain)), asdict(parse_codex_session(archive))
            left.pop("source_path")
            right.pop("source_path")
            self.assertEqual(left, right)
            self.assertEqual(right["skipped_lines"], 1)

    def test_compression_keeps_subagent_replay_exclusion(self):
        records = self.records()
        records[0]["payload"].update(forked_from_id="parent", source={"subagent": {"kind": "thread_spawn"}})
        first = records[-1]
        first["timestamp"] = "2026-06-28T01:00:01.100Z"
        first["payload"]["info"]["total_token_usage"] = copy.deepcopy(first["payload"]["info"]["last_token_usage"])
        second = copy.deepcopy(first)
        second["timestamp"] = "2026-06-28T01:00:01.500Z"
        for usage in second["payload"]["info"].values():
            for key in usage:
                usage[key] *= 2
        third = copy.deepcopy(second)
        third["timestamp"] = "2026-06-28T01:00:02Z"
        third["payload"]["info"].pop("last_token_usage")
        for key in third["payload"]["info"]["total_token_usage"]:
            third["payload"]["info"]["total_token_usage"][key] = first["payload"]["info"]["total_token_usage"][key] * 3
        path = self.write(self.sources["personal"][1] / "child.jsonl.zst", records + [second, third])
        usage = parse_codex_session(path).usage_records
        self.assertEqual(len(usage), 1)
        self.assertEqual(usage[0].capability["usage_source"], "cumulative_delta")
        self.assertEqual(usage[0].total_tokens, 1100)

    def test_sources_stay_distinct_and_claude_does_not_admit_codex_archives(self):
        for name in self.sources:
            self.write(self.sources[name][1] / "same.jsonl.zst")
            self.assertEqual(self.scan(name), (1, 0, 0))
        self.assertEqual(self.connection.execute("SELECT count(*) FROM sessions").fetchone()[0], 2)
        rows = self.connection.execute("SELECT id,source_record_id FROM usage_records").fetchall()
        self.assertEqual(len({row["id"] for row in rows}), 2)
        self.assertEqual(len({row["source_record_id"] for row in rows}), 1)
        root = self.sources["personal"][1]
        self.assertEqual(list(_session_paths(root, None, "claude")), [])

    def test_plain_precedence_then_compression_preserves_curated_and_frozen_history(self):
        plain = self.write(self.sources["personal"][1] / "session.jsonl")
        archive = plain.with_suffix(".jsonl.zst")
        self.assertEqual(self.scan(), (1, 0, 0))
        session_id = self.connection.execute("SELECT id FROM sessions").fetchone()[0]
        pin_session(self.connection, session_id)
        self.connection.execute("UPDATE usage_records SET project_key='path:/synthetic/frozen', project_name_snapshot='Frozen'")
        before = {table: self.rows(table) for table in ("session_pins", "activity_events")}
        before_usage = self.frozen_usage()
        resources = [r[0] for r in self.connection.execute("SELECT resource_id FROM session_reference_evidence")]
        self.assertTrue(resources)
        archive.write_bytes(b"invalid archive ignored while the live file exists")
        self.assertEqual(self.scan(), (0, 1, 0))
        archive.write_bytes(zstd.compress(plain.read_bytes()))
        plain.unlink()
        self.assertEqual(self.scan(), (1, 0, 0))
        self.assertEqual({table: self.rows(table) for table in before}, before)
        self.assertEqual(self.frozen_usage(), before_usage)
        session = self.connection.execute("SELECT id,source_path FROM sessions").fetchone()
        self.assertEqual(tuple(session), (session_id, str(archive)))
        self.assertEqual([r[0] for r in self.connection.execute("SELECT path FROM source_files")], [str(archive)])
        self.assertEqual([r[0] for r in self.connection.execute("SELECT resource_id FROM session_reference_evidence")], resources)
        self.assertEqual(self.scan(), (0, 1, 0))

    def assert_plain_reappearance_preserves_history(self, keep_archive):
        archive = self.write(self.sources["personal"][1] / "session.jsonl.zst")
        self.assertEqual(self.scan(), (1, 0, 0))
        session_id = self.connection.execute("SELECT id FROM sessions").fetchone()[0]
        pin_session(self.connection, session_id)
        self.connection.execute("UPDATE usage_records SET project_key='path:/synthetic/frozen', project_name_snapshot='Frozen'")
        before = {table: self.rows(table) for table in ("session_pins", "activity_events")}
        before_usage = self.frozen_usage()
        resources = [r[0] for r in self.connection.execute("SELECT resource_id FROM session_reference_evidence")]
        self.assertTrue(resources)
        plain = self.write(archive.with_suffix(""))
        if not keep_archive:
            archive.unlink()
        self.assertEqual(self.scan(), (1, 0, 0))
        self.assertEqual(self.rows("session_pins"), before["session_pins"])
        self.assertEqual(self.rows("activity_events"), before["activity_events"])
        self.assertEqual(self.frozen_usage(), before_usage)
        self.assertEqual([tuple(r) for r in self.connection.execute("SELECT id,source_path FROM sessions")],
                         [(session_id, str(plain))])
        self.assertEqual([r[0] for r in self.connection.execute("SELECT path FROM source_files")], [str(plain)])
        self.assertEqual([r[0] for r in self.connection.execute("SELECT resource_id FROM session_reference_evidence")], resources)
        self.assertEqual(self.scan(), (0, 1, 0))
        self.assertEqual(self.frozen_usage(), before_usage)

    def test_plain_reappears_beside_archive_without_duplicate_or_lost_history(self):
        self.assert_plain_reappearance_preserves_history(keep_archive=True)

    def test_plain_replaces_archive_without_losing_history(self):
        self.assert_plain_reappearance_preserves_history(keep_archive=False)

    def test_plain_replacement_failure_retains_archive_owner_then_recovers(self):
        archive = self.write(self.sources["personal"][1] / "session.jsonl.zst")
        self.scan()
        session_id = self.connection.execute("SELECT id FROM sessions").fetchone()[0]
        pin_session(self.connection, session_id)
        before = {table: self.rows(table) for table in ("sessions", "usage_records", "session_pins", "activity_events")}
        self.write(archive.with_suffix(""))
        with patch(__name__ + ".parse_codex_session", side_effect=OSError("synthetic read failure")):
            self.assertEqual(self.scan(), (0, 0, 1))
        self.assertEqual({table: self.rows(table) for table in before}, before)
        self.assertEqual(self.scan(), (1, 0, 0))
        self.assertEqual(self.rows("session_pins"), before["session_pins"])
        self.assertEqual(self.scan(), (0, 1, 0))

    def test_plain_replacement_with_different_identity_retains_archive_owner(self):
        archive = self.write(self.sources["personal"][1] / "session.jsonl.zst")
        self.scan()
        before = {table: self.rows(table) for table in ("sessions", "usage_records", "activity_events")}
        self.write(archive.with_suffix(""), self.records("different-native-id"))
        self.assertEqual(self.scan(), (0, 0, 1))
        self.assertEqual({table: self.rows(table) for table in before}, before)

    def test_truncated_replacement_rolls_back_then_recovers_without_losing_owner(self):
        plain = self.write(self.sources["personal"][1] / "session.jsonl")
        self.assertEqual(self.scan(revision=CODEX_SESSION_REVISION - 1), (1, 0, 0))
        session_id = self.connection.execute("SELECT id FROM sessions").fetchone()[0]
        pin_session(self.connection, session_id)
        before = {table: self.rows(table) for table in ("sessions", "usage_records", "session_pins", "activity_events")}
        before_usage = self.frozen_usage()
        compressed = zstd.compress(plain.read_bytes())
        archive = plain.with_suffix(".jsonl.zst")
        archive.write_bytes(compressed[:-1])
        plain.unlink()
        with self.assertRaises((EOFError, zstd.ZstdError)):
            parse_codex_session(archive)
        self.assertEqual(self.scan(), (0, 0, 1))
        self.assertEqual({table: self.rows(table) for table in before}, before)
        archive.write_bytes(compressed)
        self.assertEqual(self.scan(), (1, 0, 0))
        self.assertEqual(self.frozen_usage(), before_usage)
        self.assertEqual(self.rows("session_pins"), before["session_pins"])
        self.assertEqual(self.scan(), (0, 1, 0))

    def test_changed_identity_in_replacement_cannot_retire_the_previous_session(self):
        plain = self.write(self.sources["personal"][1] / "session.jsonl")
        self.scan()
        before = {table: self.rows(table) for table in ("sessions", "usage_records", "activity_events")}
        self.write(plain.with_suffix(".jsonl.zst"), self.records("different-native-id"))
        plain.unlink()
        self.assertEqual(self.scan(), (0, 0, 1))
        self.assertEqual({table: self.rows(table) for table in before}, before)

    def test_confirmed_empty_archive_clears_conversation_but_keeps_historical_usage(self):
        plain = self.write(self.sources["personal"][1] / "session.jsonl")
        self.scan()
        before_usage = self.frozen_usage()
        archive = self.write(plain.with_suffix(".jsonl.zst"), self.records()[:1])
        plain.unlink()
        self.assertEqual(self.scan(), (0, 0, 0))
        self.assertEqual(self.frozen_usage(), before_usage)
        self.assertEqual(self.rows("activity_events"), [])
        session = self.connection.execute("SELECT source_path,event_count FROM sessions").fetchone()
        self.assertEqual(tuple(session), (str(archive), 0))

    def test_confirmed_empty_plain_replacement_keeps_historical_usage(self):
        archive = self.write(self.sources["personal"][1] / "session.jsonl.zst")
        self.scan()
        before_usage = self.frozen_usage()
        plain = self.write(archive.with_suffix(""), self.records()[:1])
        self.assertEqual(self.scan(), (0, 0, 0))
        self.assertEqual(self.frozen_usage(), before_usage)
        self.assertEqual(self.rows("activity_events"), [])
        session = self.connection.execute("SELECT source_path,event_count FROM sessions").fetchone()
        self.assertEqual(tuple(session), (str(plain), 0))

    def test_older_collector_refuses_before_pruning_newly_imported_archives(self):
        self.write(self.sources["personal"][1] / "session.jsonl.zst")
        self.assertEqual(self.scan(), (1, 0, 0))
        before = {table: self.rows(table) for table in ("sessions", "usage_records", "source_files", "activity_events")}
        with self.assertRaises(SessionRevisionError):
            self.scan(revision=CODEX_SESSION_REVISION - 1)
        self.assertEqual({table: self.rows(table) for table in before}, before)
