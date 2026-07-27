import sqlite3
import unittest
from pathlib import Path

from localbrain.queries import (
    SESSION_PAGE_SIZE,
    compact_pagination_items,
    pagination_items,
    session_detail,
    session_inventory_page,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class SessionInventoryTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp/codex')"
        )
        self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('claude', 'Claude', '/tmp/claude')"
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
