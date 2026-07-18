import sqlite3
import tempfile
import unittest
from pathlib import Path

from localbrain.retrieval import build_candidate_bundle, write_candidate_evidence
from localbrain.workstreams import get_workstream


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = Path(handle.name)
        self.run_root = Path(tempfile.mkdtemp())
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        )
        self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('context', 'Context', '/tmp/context')"
        )
        self.connection.execute(
            "INSERT INTO workstreams(name, summary) VALUES ('샘플 플랫폼 유지보수', '인증 작업')"
        )
        self.connection.execute(
            "INSERT INTO threads(workstream_id, title, current_goal) VALUES (1, '검색 필터 개선', '인증 흐름')"
        )
        self.connection.execute(
            "INSERT INTO threads(workstream_id, title, current_goal) VALUES (1, '검색 필터 인증', '로그인 연동')"
        )
        self._insert_sessions()
        self._insert_documents()
        self.connection.execute(
            """
            INSERT INTO thread_links(thread_id, entity_type, entity_id, relation_type)
            VALUES (1, 'session', '1', 'evidence')
            """
        )
        self.connection.commit()

    def tearDown(self):
        self.connection.close()
        for path in sorted(self.run_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        self.run_root.rmdir()
        self.db_path.unlink(missing_ok=True)

    def _insert_sessions(self):
        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'codex'"
        ).fetchone()["id"]
        for session_number in range(10):
            cursor = self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, cwd_raw, title,
                    last_event_at, event_count
                ) VALUES (?, ?, ?, '/tmp/sample-project', ?, '2026-07-14T01:00:00Z', 4)
                """,
                (
                    source_id,
                    "session-{}".format(session_number),
                    "/tmp/session-{}.jsonl".format(session_number),
                    "검색 필터 개선 인증 세션 {}".format(session_number),
                ),
            )
            session_id = cursor.lastrowid
            body = []
            for sequence in range(4):
                text = "검색 필터 개선 인증 근거 {}-{}".format(session_number, sequence)
                body.append(text)
                self.connection.execute(
                    """
                    INSERT INTO activity_events(
                        id, session_id, sequence, event_type, role, text, source_line
                    ) VALUES (?, ?, ?, 'message', 'user', ?, ?)
                    """,
                    (
                        "event-{}-{}".format(session_number, sequence),
                        session_id,
                        sequence,
                        text,
                        sequence + 1,
                    ),
                )
            self.connection.execute(
                """
                INSERT INTO search_index(
                    entity_type, entity_id, source_kind, title, body, path
                ) VALUES ('session', ?, 'codex', ?, ?, '/tmp/sample-project')
                """,
                (str(session_id), "검색 필터 개선 인증 세션", "\n".join(body)),
            )
        child_id = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, external_id, source_path, cwd_raw, title,
                last_event_at, event_count, session_role, parent_session_id
            ) VALUES (?, 'child-session', '/tmp/child-session.jsonl',
                      '/tmp/sample-project', '검색 필터 개선 인증 child',
                      '2026-07-14T02:00:00Z', 1, 'subsession', 1)
            """,
            (source_id,),
        ).lastrowid
        self.connection.execute(
            """
            INSERT INTO activity_events(
                id, session_id, sequence, event_type, role, text, source_line
            ) VALUES ('child-event', ?, 1, 'message', 'user',
                      '검색 필터 개선 인증 child evidence', 1)
            """,
            (child_id,),
        )
        self.connection.execute(
            """
            INSERT INTO search_index(
                entity_type, entity_id, source_kind, title, body, path
            ) VALUES ('session', ?, 'codex', '검색 필터 개선 인증 child',
                      '검색 필터 개선 인증 child evidence', '/tmp/sample-project')
            """,
            (str(child_id),),
        )
        self.connection.execute(
            """
            INSERT INTO thread_links(thread_id, entity_type, entity_id, relation_type)
            VALUES (1, 'session', ?, 'evidence')
            """,
            (str(child_id),),
        )

    def _insert_documents(self):
        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'context'"
        ).fetchone()["id"]
        for document_number in range(10):
            body = "# 검색 필터 개선 인증 문서\n검색 필터 개선 근거\n검색 필터 인증 근거"
            cursor = self.connection.execute(
                """
                INSERT INTO context_documents(
                    source_id, path, relative_path, title, body, size_bytes,
                    mtime_ns, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    "/tmp/context/search-{}.md".format(document_number),
                    "search-{}.md".format(document_number),
                    "검색 필터 개선 인증 문서 {}".format(document_number),
                    body,
                    len(body),
                    document_number + 1,
                    "hash-{}".format(document_number),
                ),
            )
            self.connection.execute(
                """
                INSERT INTO search_index(
                    entity_type, entity_id, source_kind, title, body, path
                ) VALUES ('document', ?, 'context', ?, ?, ?)
                """,
                (
                    str(cursor.lastrowid),
                    "검색 필터 개선 인증 문서",
                    body,
                    "/tmp/context/search-{}.md".format(document_number),
                ),
            )

    def test_candidates_and_evidence_have_no_hard_count_caps(self):
        workstream = get_workstream(self.connection, 1)
        bundle = build_candidate_bundle(self.connection, workstream)
        self.assertEqual(bundle["counts"]["sessions"], 10)
        self.assertEqual(bundle["counts"]["documents"], 10)
        first_session_relations = [
            relation
            for relation in bundle["thread_resource_matches"]
            if relation["resource_type"] == "session"
            and relation["resource_id"] == 1
        ]
        self.assertEqual({relation["thread_id"] for relation in first_session_relations}, {1, 2})
        self.assertEqual(
            next(relation for relation in first_session_relations if relation["thread_id"] == 1)["state"],
            "confirmed",
        )
        self.assertGreaterEqual(len(bundle["_evidence"]["session:1"]), 4)

        materialized = write_candidate_evidence(bundle, self.run_root)
        session = next(
            item for item in materialized["candidate_resources"]["sessions"]
            if item["id"] == 1
        )
        self.assertTrue(Path(session["evidence_path"]).is_file())
        self.assertGreaterEqual(session["evidence_count"], 4)


if __name__ == "__main__":
    unittest.main()
