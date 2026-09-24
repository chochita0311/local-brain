import fcntl
import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlparse
from unittest.mock import patch
from types import SimpleNamespace
from starlette.requests import Request

from affinity_fixtures import prepare, seed
from localbrain import session_affinity as reader
from localbrain.session_simulation import atomic_json, now, read_json
from localbrain import main as web
from localbrain.work_reconstruction import digest


def query(url):
    return dict(parse_qsl(urlparse(url).query))


class AffinityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="localbrain-affinity-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.database = self.root / "localbrain.db"
        seed(self.database)
        self.folder = self.root / "session-simulation"
        self.report = prepare(self.database)
        reader._cache.clear()

    def view(self, **params):
        return reader.affinity_page(self.database, self.root, params=params)

    def edit(self, sql):
        with sqlite3.connect(self.database) as db:
            db.execute(sql)

    def render(self, query_string=b""):
        request = Request({"type": "http", "method": "GET", "path": "/auto-work", "query_string": query_string,
                           "headers": [], "scheme": "http", "server": ("127.0.0.1", 8018), "app": web.app})
        with patch.object(web, "settings", SimpleNamespace(database_path=self.database, data_dir=self.root)):
            return web.auto_work_page(request)

    def test_default_route_is_whole_history_and_never_sample_preparation(self):
        with patch.object(web, "preview_page", side_effect=AssertionError("not the sample")):
            response = self.render()
        body = response.body.decode()
        self.assertEqual(response.headers["cache-control"], "no-store, private")
        self.assertIn('data-affinity-root data-state="current"', body)
        self.assertIn('data-affinity-list open', body)
        self.assertIn('mode=sample', body)
        self.assertNotIn('action="/auto-work/refresh"', body)
        self.assertIn('id="global-query"', body)

    def test_selected_route_escapes_literal_evidence_and_keeps_native_navigation(self):
        first = self.view()
        body = self.render(urlparse(first["nodes"][0]["href"]).query.encode()).body.decode()
        self.assertIn('data-affinity-expand', body)
        self.assertIn('&lt;script&gt;syntheticOnly()', body)
        self.assertNotIn('<script>syntheticOnly()', body)
        self.assertIn('class="affinity-source" href="/sessions/', body)

    def test_unprepared_state_never_silently_falls_back_to_sample(self):
        with patch.object(web, "affinity_page", return_value=reader._state("missing")), patch.object(web, "preview_page") as sample:
            body = self.render().body.decode()
            sample.assert_not_called()
        self.assertIn('data-state="missing"', body)
        self.assertNotIn('data-auto-work-group', body)

    def test_whole_population_paging_overlap_and_duplicate_occurrences(self):
        first = self.view()
        self.assertEqual(first["state"], "current")
        self.assertEqual(first["coverage"]["total_sessions"], 96)
        self.assertEqual(first["coverage"]["eligible_sessions"], 94)
        self.assertEqual(first["coverage"]["sessions_without_text"], 1)
        self.assertLess(first["counts"]["vectors"], first["coverage"]["chunks"])
        self.assertGreater(first["counts"]["overlap_sessions"], 60)
        all_nodes = [n for p in range(1, first["pages"] + 1) for n in self.view(page=p)["nodes"]]
        self.assertEqual(len({n["id"] for n in all_nodes}), first["counts"]["groups"])
        self.assertGreater(first["counts"]["groups"], reader.PAGE_SIZE)
        inventory = self.view(inventory="all")
        all_records = [n for p in range(1, inventory["pages"] + 1) for n in self.view(inventory="all", page=p)["nodes"]]
        self.assertEqual(len(all_records), 96)
        self.assertEqual(sum(n["status"] != "eligible" for n in all_records), 2)

    def test_three_scales_keep_exact_sources_and_selection_stable(self):
        first = self.view()
        selected = self.view(**query(first["nodes"][0]["href"]))
        self.assertEqual([n["id"] for n in first["nodes"]], [n["id"] for n in selected["nodes"]])
        self.assertTrue(selected["selection"])
        self.assertTrue(all(e["available"] and "<script>" in e["wording"] for e in selected["evidence"]))
        subgroups = self.view(**query(selected["selection"]["expand_href"]))
        self.assertEqual(subgroups["level"], "subgroups")
        self.assertEqual(subgroups["scope_title"], selected["selection"]["title"])
        selected_sub = self.view(**query(subgroups["nodes"][0]["href"]))
        sessions = self.view(**query(selected_sub["selection"]["expand_href"]))
        self.assertEqual(sessions["level"], "sessions")
        one = self.view(**query(sessions["nodes"][0]["href"]))
        self.assertTrue(all(e["href"].startswith("/sessions/") for e in one["evidence"]))

    def test_continuous_map_is_independent_of_three_text_pages(self):
        wide = self.root / "continuous"
        wide.mkdir()
        database = wide / "localbrain.db"
        seed(database, count=160, topics=65)
        prepare(database)
        def view(**params):
            return reader.affinity_page(database, wide, params=params)
        first = view()
        self.assertGreaterEqual(first["pages"], 3)
        self.assertEqual(len(first["map_nodes"]), first["total"])
        self.assertEqual(len(first["nodes"]), reader.PAGE_SIZE)
        third = view(page=3)
        self.assertEqual(first["map_scope"], third["map_scope"])
        self.assertEqual(first["edges"], third["edges"])
        self.assertEqual([n["id"] for n in first["map_nodes"]], [n["id"] for n in third["map_nodes"]])
        def geometry(view):
            return [[{k: v for k, v in a.items() if k != "href"} for a in n["activity"]] for n in view["map_nodes"]]
        self.assertEqual(geometry(first), geometry(third))
        third_ids = {n["id"] for n in third["nodes"]}
        self.assertTrue(any((e["left"] in third_ids) != (e["right"] in third_ids) for e in third["edges"]))
        # A graph point whose text row is on another page still has exact evidence.
        off_page = next(n for n in first["map_nodes"] if n["id"] in third_ids)
        selected = view(**query(off_page["activity"][0]["href"]))
        self.assertEqual(selected["page"], 1)
        self.assertEqual(selected["map_scope"], first["map_scope"])
        self.assertTrue(all(e["available"] for e in selected["evidence"]))
        self.assertTrue(any(n["selected"] for n in selected["map_nodes"]))

    def test_map_scope_filters_and_hierarchy_not_list_page(self):
        first = self.view()
        filtered = self.view(q="mixed-English")
        self.assertNotEqual(first["map_scope"], filtered["map_scope"])
        self.assertEqual(len(filtered["map_nodes"]), filtered["matched"])
        self.assertEqual(filtered["timeline"], first["timeline"])
        self.assertEqual(self.view(q="does-not-exist")["map_nodes"], [])
        self.assertEqual(self.view(inventory="all")["map_nodes"], [])
        for _ in range(3):
            self.assertEqual(len(first["map_nodes"]), first["matched"])
            ids = {n["id"] for n in first["map_nodes"]}
            self.assertTrue(all(e["left"] in ids and e["right"] in ids for e in first["edges"]))
            self.assertEqual(first["map_scope"], self.view(**{**first["base"], "page": 99})["map_scope"])
            selected = self.view(**query(first["map_nodes"][0]["href"]))
            if selected["selection"].get("expand_href"):
                first = self.view(**query(selected["selection"]["expand_href"]))

    def test_previous_reader_payload_keeps_native_fallback_until_restart(self):
        old = self.view()
        old.pop("map_nodes")
        old.pop("map_scope")
        old["version"] = "localbrain.session-affinity.v1"
        with patch.object(web, "affinity_page", return_value=old):
            body = self.render().body.decode()
        self.assertNotIn("data-affinity-graph", body)
        self.assertIn("data-affinity-list open", body)
        self.assertIn("data-affinity-next", body)


    def test_occurrence_pages_never_collapse_duplicates(self):
        first = self.view()
        seen = set()
        for p in range(1, first["pages"] + 1):
            for node in self.view(page=p)["nodes"]:
                selected = self.view(**query(node["href"]))
                while True:
                    seen.update(e["key"] for e in selected["evidence"])
                    if not selected["evidence_next"]:
                        break
                    selected = self.view(**query(selected["evidence_next"]))
        self.assertEqual(len(seen), first["coverage"]["chunks"])

    def test_time_domain_is_shared_and_activity_conserves_all_occurrences(self):
        first = self.view()
        self.assertLessEqual(first["timeline"]["periods"], 64)
        self.assertEqual(first["timeline"], self.view(page=2)["timeline"])
        self.assertEqual(first["timeline"], self.view(q="mixed-English")["timeline"])
        total = 0
        for p in range(1, first["pages"] + 1):
            for node in self.view(page=p)["nodes"]:
                self.assertEqual(sum(a["occurrences"] for a in node["activity"]), node["occurrences"])
                self.assertEqual(node["activity"], next(n for n in self.view(**query(node["href"]))["nodes"] if n["id"] == node["id"])["activity"])
                for a in node["activity"]:
                    self.assertLessEqual(reader.timestamp(a["first"]).timestamp() * 1000, a["at"])
                    self.assertGreaterEqual(reader.timestamp(a["last"]).timestamp() * 1000, a["at"])
                    total += a["occurrences"]
        self.assertEqual(total, first["coverage"]["chunks"])

    def test_period_selection_filters_exact_evidence_and_survives_paging(self):
        first = self.view()
        node = first["nodes"][0]
        self.assertGreater(len(node["activity"]), 1)
        self.assertGreater(max(int(a["period"]) for a in node["activity"]) - min(int(a["period"]) for a in node["activity"]), 5)
        for a in node["activity"]:
            selected = self.view(**query(a["href"]))
            self.assertEqual(selected["evidence_total"], a["occurrences"])
            self.assertTrue(all(reader._period(e, selected["timeline"]) == a["period"] for e in selected["evidence"]))
            self.assertTrue(all(e["available"] for e in selected["evidence"]))
            self.assertEqual(self.view(**query(selected["selection"]["whole_href"]))["evidence_total"], node["occurrences"])
        for period in ("-1", "64", "unknown", "not-a-period", "9" * 200):
            self.assertEqual(self.view(**{**query(node["href"]), "period": period})["state"], "selection-stale")
        self.assertEqual(self.view(period="0")["state"], "selection-stale")

    def test_unknown_time_is_unplaced_but_accessible(self):
        self.edit("UPDATE activity_events SET occurred_at=NULL")
        prepare(self.database)
        view = self.view()
        self.assertIsNone(view["timeline"]["start"])
        self.assertEqual(view["timeline"]["unknown_occurrences"], view["coverage"]["chunks"])
        self.assertEqual(view["timeline"]["dated_occurrences"], 0)
        activity = view["nodes"][0]["activity"][0]
        self.assertEqual(activity["period"], "unknown")
        self.assertIsNone(activity["at"])
        selected = self.view(**query(activity["href"]))
        self.assertTrue(selected["evidence"])
        self.assertTrue(all(e["at"] is None for e in selected["evidence"]))
        self.assertTrue(all(e["left_at"] is None and e["right_at"] is None for e in view["edges"]))

    def test_edge_witnesses_are_exact_occurrences_in_their_strands(self):
        view = self.view()
        indexed = reader._load(self.database, self.folder, now())
        for edge in view["edges"]:
            for side in ("left", "right"):
                self.assertIn(edge[side + "_at"], {c["at"] for c in indexed["groups"][edge[side]]["chunks"]})
        selected = self.view(**query(view["nodes"][0]["href"]))
        self.assertEqual(view["edges"], selected["edges"])

    def test_search_and_invalid_pages_and_selections(self):
        for value in ("no", "-1", "9" * 5000):
            self.assertEqual(self.view(page=value)["page"], 1)
        self.assertEqual(self.view(q="does-not-exist")["nodes"], [])
        self.assertEqual(self.view(snapshot="obsolete")["state"], "selection-stale")
        self.assertEqual(self.view(group="missing")["state"], "selection-stale")
        first = self.view()
        self.assertEqual(self.view(snapshot=first["snapshot"], pick="missing")["state"], "selection-stale")

    def test_source_changes_invalidate_cached_read_and_report_deltas(self):
        self.view()
        self.edit("UPDATE activity_events SET text='changed' WHERE id='event-1-0'")
        stale = self.view()
        self.assertEqual(stale["state"], "stale")
        self.assertGreater(stale["delta"]["added"] + stale["delta"]["removed"] + stale["delta"]["changed"], 0)
        self.assertNotIn("nodes", stale)

    def test_unknown_date_retains_exact_evidence(self):
        self.edit("UPDATE activity_events SET occurred_at=NULL")
        prepare(self.database)
        first = self.view()
        selected = self.view(**query(first["nodes"][0]["href"]))
        self.assertTrue(all(e["available"] and e["at"] is None for e in selected["evidence"]))

    def test_removed_reclassified_and_appended_sources_are_stale(self):
        for sql in ("DELETE FROM activity_events WHERE session_id=1", "UPDATE sessions SET index_policy='metadata_only' WHERE id=3",
                    "INSERT INTO sessions(source_id,external_id,source_path,title) VALUES(1,'new','/synthetic/new','새 합성 기록')"):
            self.edit(sql)
            self.assertEqual(self.view()["state"], "stale")

    def test_exact_anchor_revalidation_after_cached_load(self):
        first = self.view()
        indexed = reader._load(self.database, self.folder, now())
        self.edit("UPDATE activity_events SET text='changed'")
        with patch.object(reader, "_load", return_value=indexed):
            view = self.view(**query(first["nodes"][0]["href"]))
        self.assertTrue(view["evidence"])
        self.assertTrue(all(not e["available"] and "wording" not in e and "href" not in e for e in view["evidence"]))

    def test_view_does_not_write_source_or_store_or_encode(self):
        paths = [self.database] + [p for p in self.folder.iterdir() if p.is_file()]
        before = {p: p.read_bytes() for p in paths}
        with patch("localbrain.session_simulation.simulate", side_effect=AssertionError("no hidden work")):
            first = self.view()
            self.view(**query(first["nodes"][0]["href"]))
            with patch.object(reader, "inventory", side_effect=AssertionError("unchanged cache")):
                self.view()
        self.assertEqual(before, {p: p.read_bytes() for p in paths})

    def test_busy_and_shared_reader_and_expiry_never_delete(self):
        with (self.folder / "writer.lock").open("rb") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.view()["state"], "busy")
            fcntl.flock(lock, fcntl.LOCK_UN)
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
            self.assertEqual(self.view()["state"], "current")
        expired = reader.affinity_page(self.database, self.root, at=now() + timedelta(days=31))
        self.assertEqual(expired["state"], "expired")
        self.assertTrue((self.folder / "report.json").exists())

    def test_corruption_oversize_symlink_and_unknown_owner_fail_closed(self):
        target = self.folder / "report.json"
        original = target.read_bytes()
        target.write_bytes(b"not-json")
        self.assertEqual(self.view()["state"], "invalid")
        target.write_bytes(original)
        with patch.object(reader, "MAX_REPORT_BYTES", 1):
            self.assertEqual(self.view()["state"], "invalid")
        moved = self.folder / "synthetic-held.json"
        target.rename(moved)
        target.symlink_to(moved)
        self.assertEqual(self.view()["state"], "invalid")
        target.unlink(); moved.rename(target)
        value = read_json(target); value["grouping"]["authority"] = "confirmed"
        atomic_json(target, value)
        self.assertEqual(self.view()["state"], "invalid")

    def test_config_change_and_empty_and_missing(self):
        first = self.view()
        report = read_json(self.folder / "report.json")
        report["configuration"] = "changed"
        atomic_json(self.folder / "report.json", report)
        self.assertEqual(self.view()["state"], "invalid")
        self.edit("UPDATE sessions SET session_class='maintenance'")
        prepare(self.database)
        self.assertEqual(self.view()["state"], "empty")
        self.assertEqual(self.view(snapshot=first["snapshot"])["state"], "selection-stale")
        self.assertEqual(reader.affinity_page(self.database, self.root / "not-created")["state"], "missing")
        self.assertFalse((self.root / "not-created").exists())

    def test_valid_new_configuration_does_not_remap_old_selection(self):
        first = self.view()
        report = read_json(self.folder / "report.json")
        report["parameters"]["neighbors"] = 9
        report["configuration"] = digest([report["namespace"], report["parameters"], report["grouping"]["engine"]])
        atomic_json(self.folder / "report.json", report)
        self.assertEqual(self.view()["state"], "current")
        self.assertEqual(self.view(**query(first["nodes"][0]["href"]))["state"], "selection-stale")

    def test_owner_and_database_binding_mismatch_fail_closed(self):
        target = self.folder / "owner.json"
        marker = read_json(target)
        for field in ("owner", "database"):
            atomic_json(target, {**marker, field: "not-this-owner"})
            self.assertEqual(self.view()["state"], "invalid")
        atomic_json(target, marker)
        self.assertEqual(self.view()["state"], "current")

    def test_unavailable_database_and_changed_during_inventory(self):
        with patch.object(reader, "_source_signature", side_effect=[("before",), ("after",)]):
            self.assertEqual(self.view()["state"], "busy")
        self.database.rename(self.root / "held.db")
        self.assertEqual(self.view()["state"], "unavailable")


if __name__ == "__main__":
    unittest.main()
