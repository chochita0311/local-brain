import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from localbrain.main import app, sessions_page, show_session
from localbrain.queries import (
    SESSION_PAGE_SIZE,
    compact_pagination_items,
    dashboard_stats,
    pagination_items,
    project_activity,
    session_detail,
    session_inventory_page,
    session_source_scopes,
    source_inventory,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class SessionInventoryTests(unittest.TestCase):
    @staticmethod
    def _request(query: bytes = b"", path: str = "/sessions") -> Request:
        return Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("utf-8"),
                "query_string": query,
                "headers": [],
                "client": ("test", 50000),
                "server": ("test", 80),
                "root_path": "",
                "app": app,
                "router": app.router,
            }
        )

    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO sources(kind, provider_kind, name, root_path) VALUES ('codex', 'codex', 'Codex', '/tmp/codex')"
        ).lastrowid
        self.connection.execute(
            "INSERT INTO sources(kind, provider_kind, name, root_path) VALUES ('claude', 'claude', 'Claude', '/tmp/claude')"
        )
        self.connection.execute(
            """
            INSERT INTO workspaces(canonical_path, display_name, git_root, exists_now)
            VALUES ('/tmp/one', 'one', '/tmp/one', 1),
                   ('/tmp/two', 'two', NULL, 0)
            """
        )
        self.parents = []
        for number in range(1, 48):
            source_id = 1 if number % 2 else 2
            workspace_id = 1 if number <= 30 else 2
            session_id = self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, workspace_id, external_id, source_path, cwd_raw,
                    git_branch, title, last_event_at, event_count,
                    user_message_count, assistant_message_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    source_id,
                    workspace_id,
                    "parent-{}".format(number),
                    "/tmp/parent-{}.jsonl".format(number),
                    "/tmp/{}".format("one" if workspace_id == 1 else "two"),
                    "feature/{}".format(number),
                    "Parent {}".format(number),
                    "2026-07-17T00:{:02d}:00Z".format(number),
                    number,
                    number % 4,
                ),
            ).lastrowid
            self.parents.append(session_id)

        newest_parent = self.parents[-1]
        direct_child = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, cwd_raw, title,
                last_event_at, event_count, user_message_count, session_role,
                parent_external_id, parent_session_id
            ) VALUES (1, 2, 'direct-child', '/tmp/direct-child.jsonl', '/tmp/two',
                      'Direct child', '2026-07-17T01:00:00Z', 3, 0,
                      'subsession', 'parent-47', ?)
            """,
            (newest_parent,),
        ).lastrowid
        self.direct_child = direct_child
        self.grandchild = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, title,
                session_role, parent_external_id, parent_session_id
            ) VALUES (1, 2, 'grandchild', '/tmp/grandchild.jsonl', 'Grandchild',
                      'subsession', 'direct-child', ?)
            """,
            (direct_child,),
        ).lastrowid
        self.orphan = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, external_id, source_path, title,
                session_role, parent_external_id
            ) VALUES (1, 'orphan', '/tmp/orphan.jsonl', 'Orphan',
                      'subsession', 'missing-parent')
            """
        ).lastrowid
        self.cross_source_child = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, external_id, source_path, title,
                session_role, parent_external_id, parent_session_id
            ) VALUES (2, 'cross-source', '/tmp/cross-source.jsonl', 'Cross source',
                      'subsession', 'parent-47', ?)
            """,
            (newest_parent,),
        ).lastrowid
        self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, external_id, source_path, title, session_class,
                session_role, parent_external_id, parent_session_id
            ) VALUES (1, 'maintenance-child', '/tmp/maintenance-child.jsonl',
                      'Maintenance child', 'maintenance', 'subsession', 'parent-47', ?)
            """,
            (newest_parent,),
        )

    def tearDown(self):
        self.connection.close()

    def test_pages_count_only_primary_sessions_and_attach_direct_children(self):
        first = session_inventory_page(self.connection, page=1)
        self.assertEqual(SESSION_PAGE_SIZE, 15)
        self.assertEqual(first["total"], 47)
        self.assertEqual(first["total_pages"], 4)
        self.assertEqual(first["page_items"], [1, 2, 3, 4])
        self.assertEqual(first["compact_page_items"], [1, 2, 3, 4])
        self.assertEqual(len(first["items"]), 15)
        self.assertEqual(first["items"][0]["external_id"], "parent-47")
        self.assertEqual(first["items"][-1]["external_id"], "parent-33")
        self.assertIsNone(first["previous_page"])
        self.assertEqual(first["next_page"], 2)
        self.assertEqual(
            [child["id"] for child in first["items"][0]["subsessions"]],
            [self.direct_child],
        )

        final = session_inventory_page(self.connection, page=4)
        self.assertEqual(len(final["items"]), 2)
        self.assertEqual(final["previous_page"], 3)
        self.assertIsNone(final["next_page"])
        self.assertEqual(session_inventory_page(self.connection, page=999)["page"], 4)
        self.assertEqual(session_inventory_page(self.connection, page=-4)["page"], 1)

    def test_page_items_keep_edges_and_collapse_distant_pages(self):
        self.assertEqual(pagination_items(1, 10), [1, 2, 3, 4, None, 10])
        self.assertEqual(pagination_items(5, 10), [1, None, 4, 5, 6, None, 10])
        self.assertEqual(pagination_items(10, 10), [1, None, 7, 8, 9, 10])
        self.assertEqual(compact_pagination_items(1, 10), [1, 2, 3, None, 10])
        self.assertEqual(compact_pagination_items(5, 10), [1, None, 5, None, 10])
        self.assertEqual(compact_pagination_items(10, 10), [1, None, 8, 9, 10])

    def test_filters_apply_before_count_and_page_bounds(self):
        codex = session_inventory_page(self.connection, source_kind="codex", page=2)
        self.assertEqual(codex["total"], 24)
        self.assertEqual(codex["total_pages"], 2)
        self.assertEqual(len(codex["items"]), 9)
        workspace = session_inventory_page(self.connection, workspace_id=1, page=2)
        self.assertEqual(workspace["total"], 30)
        self.assertEqual(len(workspace["items"]), 15)

    def test_source_inventory_has_no_false_enablement_projection(self):
        sources = source_inventory(self.connection)
        self.assertEqual([source["kind"] for source in sources], ["claude", "codex"])
        self.assertTrue(all("enabled" not in source.keys() for source in sources))

    def test_registry_scopes_counts_and_projects_use_one_primary_work_denominator(self):
        company_source_id = self.connection.execute(
            """
            INSERT INTO sources(kind, provider_kind, name, root_path)
            VALUES ('codex-company', 'codex', 'Codex Company', '/tmp/company')
            """
        ).lastrowid
        company_session_id = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, title,
                last_event_at, event_count
            ) VALUES (?, 2, 'company-old', '/tmp/company-old.jsonl',
                      'Company old', '2024-01-02T00:00:00Z', 7)
            """,
            (company_source_id,),
        ).lastrowid
        self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, title,
                session_class
            ) VALUES (?, 2, 'company-maintenance', '/tmp/company-maintenance.jsonl',
                      'Company maintenance', 'maintenance')
            """,
            (company_source_id,),
        ).lastrowid
        self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, title,
                session_role, parent_external_id, parent_session_id
            ) VALUES (?, 2, 'company-child', '/tmp/company-child.jsonl',
                      'Company child', 'subsession', 'company-old', ?)
            """,
            (company_source_id, company_session_id),
        )

        scopes = session_source_scopes(self.connection)
        scope_counts = {
            row["source_key"]: row["eligible_session_count"] for row in scopes
        }
        company = session_inventory_page(
            self.connection, source_kind="codex-company"
        )
        personal = session_inventory_page(self.connection, source_kind="codex")
        combined = session_inventory_page(self.connection)

        self.assertEqual(
            [row["source_key"] for row in scopes],
            ["codex", "claude", "codex-company"],
        )
        self.assertEqual(scopes[-1]["display_label"], "Codex Company")
        self.assertEqual(company["total"], 1)
        self.assertEqual(company["items"][0]["external_id"], "company-old")
        self.assertEqual(personal["total"], 24)
        self.assertEqual(combined["total"], sum(scope_counts.values()))
        self.assertEqual(
            dashboard_stats(self.connection, "codex-company")["sessions"], 1
        )
        company_projects = project_activity(self.connection, "codex-company")
        self.assertEqual(
            [(row["display_name"], row["session_count"]) for row in company_projects],
            [("two", 1)],
        )

    def test_route_normalizes_unknown_source_and_accepts_company_stable_key(self):
        company_source_id = self.connection.execute(
            """
            INSERT INTO sources(kind, provider_kind, name, root_path)
            VALUES ('codex-company', 'codex', 'Codex Company', '/tmp/company')
            """
        ).lastrowid
        company_session_id = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, title,
                last_event_at
            ) VALUES (?, 2, 'company-one', '/tmp/company-one.jsonl',
                      'Company one', '2024-01-02T00:00:00Z')
            """,
            (company_source_id,),
        ).lastrowid
        company_child_id = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, title,
                last_event_at, session_role, parent_external_id,
                parent_session_id, user_message_count, event_count
            ) VALUES (?, 2, 'company-child', '/tmp/company-child.jsonl',
                      'Company child', '2024-01-02T01:00:00Z', 'subsession',
                      'company-one', ?, 3, 8)
            """,
            (company_source_id, company_session_id),
        ).lastrowid

        with patch("localbrain.main.connect", return_value=self.connection):
            unknown = sessions_page(
                self._request(b"source=phantom&workspace=2&page=4"),
                source="phantom",
                workspace=2,
                page="4",
            )
            missing_workspace = sessions_page(
                self._request(b"source=codex-company&workspace=999&page=4"),
                source="codex-company",
                workspace=999,
                page="4",
            )
            company = sessions_page(
                self._request(b"source=codex-company&workspace=2"),
                source="codex-company",
                workspace=2,
                page="1",
            )
            detail = show_session(
                self._request(
                    b"source=codex-company&workspace=2",
                    path="/sessions/{}".format(company_session_id),
                ),
                company_session_id,
                source="codex-company",
                workspace=2,
            )
            child_detail = show_session(
                self._request(
                    b"source=codex-company&workspace=2",
                    path="/sessions/{}".format(company_child_id),
                ),
                company_child_id,
                source="codex-company",
                workspace=2,
            )

        self.assertEqual(unknown.status_code, 303)
        self.assertEqual(unknown.headers["location"], "/sessions?workspace=2")
        self.assertEqual(missing_workspace.status_code, 303)
        self.assertEqual(
            missing_workspace.headers["location"],
            "/sessions?source=codex-company",
        )
        html = company.body.decode("utf-8")
        self.assertIn("Codex Company 세션", html)
        self.assertIn("Company one", html)
        self.assertNotIn("Parent 47", html)
        self.assertIn(
            'href="/sessions?source=codex-company&workspace=2"', html
        )
        detail_html = detail.body.decode("utf-8")
        self.assertIn("Codex Company", detail_html)
        self.assertNotIn('<p class="eyebrow">Codex Company</p>', detail_html)
        self.assertIn(
            'class="session-source large codex-company"><span aria-hidden="true">CC</span>',
            detail_html,
        )
        self.assertIn(
            'class="session-source codex-company"><span aria-hidden="true">CC</span>',
            detail_html,
        )
        self.assertIn("<small>company-child</small>", detail_html)
        self.assertNotIn("Codex Company · company-child", detail_html)
        question_count = detail_html.index(
            '<span class="subsession-question-count">질문 3</span>'
        )
        event_count = detail_html.index(
            '<span class="subsession-event-count">이벤트 8</span>'
        )
        self.assertLess(question_count, event_count)
        self.assertIn(
            'href="/sessions?source=codex-company&amp;workspace=2"',
            detail_html,
        )
        child_detail_html = child_detail.body.decode("utf-8")
        self.assertNotIn(
            '<p class="eyebrow">Codex Company · SUBSESSION</p>',
            child_detail_html,
        )
        self.assertIn('<p class="eyebrow">SUBSESSION</p>', child_detail_html)
        self.assertIn(
            'class="session-source large codex-company"><span aria-hidden="true">CC</span>',
            child_detail_html,
        )

    def test_inventory_and_detail_project_current_pin_state(self):
        session_id = self.parents[-1]
        self.connection.execute(
            """
            INSERT INTO session_pins(session_id, pinned_at)
            VALUES (?, '2026-07-24T04:00:00+00:00')
            """,
            (session_id,),
        )

        inventory = session_inventory_page(self.connection, page=1)
        pinned = next(item for item in inventory["items"] if item["id"] == session_id)
        detail = session_detail(self.connection, session_id)

        self.assertEqual(pinned["pinned_at"], "2026-07-24T04:00:00+00:00")
        self.assertEqual(detail["pinned_at"], pinned["pinned_at"])
        self.assertIsNone(inventory["items"][1]["pinned_at"])

    def test_non_displayable_children_remain_outside_detail_lookup(self):
        self.assertIsNotNone(session_detail(self.connection, self.direct_child))
        self.assertIsNone(session_detail(self.connection, self.grandchild))
        self.assertIsNone(session_detail(self.connection, self.orphan))
        self.assertIsNone(session_detail(self.connection, self.cross_source_child))


if __name__ == "__main__":
    unittest.main()
