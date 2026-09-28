import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path

from localbrain.personal_insight_evidence import (
    MAX_EXCERPTS,
    MAX_SESSIONS,
    MAX_TOTAL_CHARS,
    _excerpt,
    build_insight_evidence_manifest,
    resolve_insight_evidence_reference,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"
REQUESTED_AT = datetime(2026, 9, 30, tzinfo=timezone.utc)


class PersonalInsightEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.sources = {}
        for key, provider in (
            ("claude-code", "claude"),
            ("codex-company", "codex"),
            ("unrelated", "other"),
        ):
            self.sources[key] = self.connection.execute(
                "INSERT INTO sources(kind, provider_kind, name, root_path) "
                "VALUES (?, ?, ?, ?)",
                (key, provider, key, "/synthetic/" + key),
            ).lastrowid

    def tearDown(self):
        self.connection.close()

    def add_session(
        self, key, name, *, session_class="work", session_role="primary",
        index_policy="full",
    ):
        return self.connection.execute(
            """INSERT INTO sessions(
                source_id, external_id, source_path, title,
                session_class, session_role, index_policy
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                self.sources[key], name, "/synthetic/" + name + ".jsonl", name,
                session_class, session_role, index_policy,
            ),
        ).lastrowid

    def add_event(
        self, session_id, sequence, text, *, occurred_at="2026-09-28T12:00:00Z",
        event_type="message", role="user",
    ):
        event_id = f"event-{session_id}-{sequence}"
        self.connection.execute(
            """INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, role, text,
                source_line
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id, session_id, sequence, occurred_at, event_type, role,
                text, sequence,
            ),
        )
        return event_id

    def add_search_row(self, session_id, body):
        self.connection.execute(
            """INSERT INTO search_index(
                entity_type, entity_id, source_kind, title, body, path
            ) VALUES ('session', ?, 'synthetic', 'Synthetic', ?, '/synthetic')""",
            (str(session_id), body),
        )

    def manifest(self, mode="discover", **kwargs):
        return build_insight_evidence_manifest(
            self.connection, mode=mode, requested_at=REQUESTED_AT, **kwargs
        )

    def test_input_validation_and_empty_scope(self):
        for values in (
            {"mode": "other"},
            {"mode": "ask", "question": "  "},
            {"mode": "discover", "question": "question"},
            {"mode": "discover", "date_from": "2026-09-31"},
            {"mode": "discover", "date_from": "2026-09-29", "date_to": "2026-09-28"},
            {"mode": "discover", "source_keys": ["missing"]},
            {"mode": "discover", "timezone": "Not/A_Zone"},
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.manifest(**values)
        with self.assertRaises(ValueError):
            build_insight_evidence_manifest(
                self.connection, mode="discover", requested_at=datetime(2026, 9, 30)
            )

        result = self.manifest()
        self.assertEqual(result["coverage"]["eligible_messages"], 0)
        self.assertEqual(result["sessions"], [])
        self.assertIn("no_eligible_messages", result["coverage"]["omission_reasons"])

    def test_primary_work_messages_and_local_date_boundaries(self):
        claude = self.add_session("claude-code", "claude-work")
        codex = self.add_session("codex-company", "codex-work")
        self.add_event(claude, 1, "first day boundary", occurred_at="2026-09-27T15:00:00Z")
        self.add_event(codex, 1, "last day boundary", occurred_at="2026-09-28T14:59:59Z")
        self.add_event(codex, 2, "next day", occurred_at="2026-09-28T15:00:00Z")
        self.add_event(codex, 3, "unknown date", occurred_at=None)
        self.add_event(codex, 4, "tool payload", event_type="tool_call")
        self.add_event(codex, 5, "   ")
        for name, options in (
            ("maintenance", {"session_class": "maintenance"}),
            ("child", {"session_role": "subsession"}),
            ("metadata", {"index_policy": "metadata_only"}),
        ):
            session_id = self.add_session("codex-company", name, **options)
            self.add_event(session_id, 1, "excluded")
        unrelated = self.add_session("unrelated", "other-provider")
        self.add_event(unrelated, 1, "excluded")

        before_changes = self.connection.total_changes
        result = self.manifest(date_from="2026-09-28", date_to="2026-09-28")
        self.assertEqual(self.connection.total_changes, before_changes)
        self.assertEqual(result["coverage"]["eligible_sessions"], 2)
        self.assertEqual(result["coverage"]["eligible_messages"], 2)
        self.assertEqual(result["coverage"]["selected_excerpts"], 2)
        self.assertEqual(result["coverage"]["undated_messages_excluded"], 1)
        self.assertEqual(
            {event["excerpt"] for session in result["sessions"] for event in session["events"]},
            {"first day boundary", "last day boundary"},
        )
        self.assertEqual(
            set(result["coverage"]["sources"]), {"claude-code", "codex-company"}
        )
        self.assertEqual(result, self.manifest(date_from="2026-09-28", date_to="2026-09-28"))

    def test_ask_lexical_match_and_honest_fallback(self):
        matching = self.add_session("claude-code", "matching")
        other = self.add_session("codex-company", "other")
        self.add_event(matching, 1, "alpha question")
        self.add_event(other, 1, "unrelated question")
        self.add_search_row(matching, "alpha question")
        self.add_search_row(other, "unrelated question")

        result = self.manifest("ask", question="alpha")
        self.assertEqual(result["sessions"][0]["session_id"], matching)
        self.assertEqual(result["selection"]["lexical_match_state"], "matched")
        self.assertEqual(result["sessions"][0]["events"][0]["selection_basis"], "lexical")

        fallback = self.manifest("ask", question="absent")
        self.assertEqual(fallback["selection"]["lexical_match_state"], "none")
        self.assertIn("no_indexed_lexical_match", fallback["coverage"]["omission_reasons"])
        self.assertEqual(fallback["coverage"]["selected_sessions"], 2)

        self.connection.execute("UPDATE activity_events SET text = 'different' WHERE session_id = ?", (matching,))
        title_only = self.manifest("ask", question="alpha")
        self.assertEqual(title_only["selection"]["indexed_session_count"], 1)
        self.assertEqual(title_only["selection"]["lexical_match_state"], "none")
        self.assertIn(
            "no_selected_message_lexical_match", title_only["coverage"]["omission_reasons"]
        )

    def test_requested_at_and_source_scope(self):
        claude = self.add_session("claude-code", "in-scope")
        codex = self.add_session("codex-company", "future")
        self.add_event(claude, 1, "known time")
        self.add_event(claude, 2, "unknown time", occurred_at=None)
        self.add_event(codex, 1, "future time", occurred_at="2026-10-01T00:00:00Z")

        result = self.manifest(source_keys=["claude-code"])
        self.assertEqual(result["coverage"]["eligible_messages"], 2)
        self.assertEqual(result["coverage"]["eligible_undated_messages"], 1)
        self.assertEqual(result["coverage"]["selected_undated_messages"], 1)
        self.assertEqual(set(result["coverage"]["sources"]), {"claude-code"})
        future_only = self.manifest(source_keys=["codex-company"])
        self.assertEqual(future_only["coverage"]["eligible_messages"], 0)

    def test_source_month_spread_and_session_excerpt_caps(self):
        for index in range(MAX_SESSIONS + 1):
            key = "claude-code" if index % 2 else "codex-company"
            session_id = self.add_session(key, f"session-{index}")
            month = "08" if index % 3 else "09"
            for sequence in range(1, 4):
                self.add_event(
                    session_id, sequence, f"message {index}-{sequence}",
                    occurred_at=f"2026-{month}-28T12:00:00Z",
                )

        result = self.manifest()
        self.assertEqual(result["coverage"]["eligible_sessions"], MAX_SESSIONS + 1)
        self.assertEqual(result["coverage"]["selected_sessions"], MAX_SESSIONS)
        self.assertEqual(result["coverage"]["selected_excerpts"], MAX_EXCERPTS)
        self.assertIn("session_sample_limit", result["coverage"]["omission_reasons"])
        self.assertEqual(
            len({
                (session["source_key"], session["events"][0]["occurred_at"][5:7])
                for session in result["sessions"][:4]
            }),
            4,
        )

    def test_character_cap_is_reported(self):
        for index in range(MAX_SESSIONS):
            session_id = self.add_session("codex-company", f"long-{index}")
            for sequence in range(1, 4):
                self.add_event(session_id, sequence, "x" * 600)
        result = self.manifest()
        self.assertEqual(result["coverage"]["excerpt_characters"], MAX_TOTAL_CHARS)
        self.assertLess(result["coverage"]["selected_excerpts"], MAX_EXCERPTS)
        self.assertIn("character_limit", result["coverage"]["omission_reasons"])

    def test_reference_becomes_stale_then_unavailable(self):
        session_id = self.add_session("claude-code", "original")
        self.add_event(session_id, 1, "synthetic private value")
        result = self.manifest()
        reference = result["sessions"][0]["events"][0]
        original_excerpt = reference["excerpt"]
        self.assertEqual(
            resolve_insight_evidence_reference(self.connection, reference)["status"],
            "current",
        )
        self.connection.execute(
            "UPDATE activity_events SET text = 'changed' WHERE id = ?", (reference["event_id"],)
        )
        self.assertEqual(
            resolve_insight_evidence_reference(self.connection, reference)["status"],
            "stale",
        )
        self.connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.assertEqual(
            resolve_insight_evidence_reference(self.connection, reference)["status"],
            "unavailable",
        )
        self.assertEqual(reference["excerpt"], original_excerpt)

    def test_unicode_casefold_keeps_excerpt_offsets_in_original_text(self):
        text = "ß" * 150 + "strasse"
        excerpt, start, end = _excerpt(text, {"strasse"}, 600)
        self.assertEqual(excerpt, text[start:end])
        self.assertIn("strasse", excerpt)
        self.assertLessEqual(start, text.index("strasse"))
        self.assertGreater(end, text.index("strasse"))


if __name__ == "__main__":
    unittest.main()
