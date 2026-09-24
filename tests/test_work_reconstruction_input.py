import copy
import hashlib
import json
import multiprocessing
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from localbrain.work_reconstruction import ExperimentError, digest
from localbrain.work_reconstruction_input import load_snapshots, read_only_database, validate_manifest
from localbrain.work_reconstruction_experiment import (
    decode_bounded, encode_bounded, evaluate_history, publish, supervise,
)
from localbrain.work_reconstruction_preparation import prepare_current, unassessed_expectations
from work_reconstruction_cases import bind_expectations, goal, record, snapshot


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "src/localbrain/schema.sql").read_text(encoding="utf-8")
AT = "2030-01-01T00:00:00Z"


def selection(identity, text, **extras):
    return {"id": identity, "start": 0, "end": len(text),
            "sha256": hashlib.sha256(text.encode()).hexdigest(), **extras}


class ReconstructionInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="localbrain-reconstruction-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.db = self.root / "synthetic.sqlite"
        with sqlite3.connect(self.db) as connection:
            connection.executescript(SCHEMA)
            connection.execute("INSERT INTO sources(id,kind,name,root_path) VALUES (1,'synthetic','Synthetic','/synthetic')")
            connection.execute("""INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count)
                VALUES (1,1,'synthetic-native','/synthetic/session','Synthetic',1)""")
            connection.execute("""INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,role,text,source_line)
                VALUES ('event-1',1,1,?,'message','user','Fix parsing.',1)""", (AT,))
            connection.execute("""INSERT INTO session_reference_scans(session_id,source_fingerprint,extractor_version,status,scanned_at,updated_at)
                VALUES (1,?,'synthetic','ok',?,?)""", ("0" * 64, AT, AT))
            connection.execute("""INSERT INTO context_roots(id,path,label) VALUES (1,'/synthetic/documents','Synthetic')""")
            connection.execute("""INSERT INTO context_documents(id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash,imported_at)
                VALUES (1,1,1,'/synthetic/goal.md','goal.md','Synthetic','Improve indexing.',17,1,?,?)""", ("1" * 64, AT))
            connection.execute("""INSERT INTO external_resources(id,resource_type,title,url) VALUES (1,'wiki','Synthetic','https://example.test/wiki/1')""")
            connection.execute("""INSERT INTO atlassian_sites(id,normalized_domain,canonical_base_url) VALUES (1,'example.test','https://example.test')""")
            connection.execute("""INSERT INTO atlassian_items(external_resource_id,site_id,service,item_type,coverage) VALUES (1,1,'confluence','confluence_page','indexed')""")
            connection.execute("""INSERT INTO atlassian_item_content(external_resource_id,source_format,source_body,source_hash,normalized_document_json,normalized_text,normalizer_version,applied_at)
                VALUES (1,'plain_text','synthetic unadmitted source payload',?,'{}','Reduce latency.','synthetic',?)""", ("2" * 64, AT))
        self.manifest = {"version": 1, "source_ids": [1], "start": "2029-12-31T00:00:00Z",
                         "end": "2030-01-02T00:00:00Z", "owner": "synthetic-test",
                         "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                         "snapshots": [{"name": "synthetic", "as_of": AT, "session_ids": [1],
                                        "events": [selection("event-1", "Fix parsing.")], "documents": [], "items": [],
                                        "organization": [], "organization_links": []}]}

    def change(self, sql, args=()):
        with sqlite3.connect(self.db) as connection:
            connection.execute(sql, args)

    def test_real_schema_adapter_preserves_database_and_exact_spans(self):
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        self.manifest["snapshots"][0]["documents"] = [selection(1, "Improve indexing.")]
        self.manifest["snapshots"][0]["items"] = [selection(1, "Reduce latency.")]
        data = load_snapshots(self.db, self.manifest)[0]
        self.assertEqual([r["text"] for r in data["records"]], ["Fix parsing.", "Improve indexing.", "Reduce latency."])
        self.assertTrue(data["coverage"]["complete"])
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())
        self.assertNotIn("source payload", json.dumps(data))

    def test_read_only_authorizer_rejects_writes_ddl_and_attach(self):
        for query in ("DELETE FROM sessions", "CREATE TABLE forbidden(id)", "ATTACH DATABASE ':memory:' AS other",
                      "PRAGMA user_version = 99", "SELECT load_extension('forbidden')"):
            with self.subTest(query=query), self.assertRaises(ExperimentError):
                with read_only_database(self.db) as connection:
                    connection.execute(query)

    def test_ineligible_session_or_tool_text_is_rejected_before_body_read(self):
        mutations = [("UPDATE sessions SET session_class='maintenance'", "UPDATE sessions SET session_class='work'"),
                     ("UPDATE sessions SET session_role='subsession'", "UPDATE sessions SET session_role='primary'"),
                     ("UPDATE sessions SET index_policy='metadata_only'", "UPDATE sessions SET index_policy='full'"),
                     ("UPDATE activity_events SET event_type='tool_result'", "UPDATE activity_events SET event_type='message'")]
        for mutation, restore in mutations:
            self.change(mutation)
            with patch("localbrain.work_reconstruction_input._text") as body:
                with self.assertRaises(ExperimentError):
                    load_snapshots(self.db, self.manifest)
                body.assert_not_called()
            self.change(restore)

    def test_disabled_document_and_reference_only_item_do_not_read_bodies(self):
        scope = self.manifest["snapshots"][0]
        scope["events"] = []
        scope["documents"] = [selection(1, "Improve indexing.")]
        self.change("UPDATE context_roots SET enabled=0")
        with patch("localbrain.work_reconstruction_input._text") as body:
            with self.assertRaises(ExperimentError): load_snapshots(self.db, self.manifest)
            body.assert_not_called()
        scope["documents"] = []
        scope["items"] = [selection(1, "Reduce latency.")]
        self.change("UPDATE atlassian_items SET coverage='reference'")
        with patch("localbrain.work_reconstruction_input._text") as body:
            with self.assertRaises(ExperimentError): load_snapshots(self.db, self.manifest)
            body.assert_not_called()

    def test_changed_hash_or_time_scope_rejects_input(self):
        self.change("UPDATE activity_events SET text='Fix caching.'")
        with self.assertRaises(ExperimentError): load_snapshots(self.db, self.manifest)
        self.change("UPDATE activity_events SET text='Fix parsing.',occurred_at='2031-01-01T00:00:00Z'")
        with self.assertRaises(ExperimentError): load_snapshots(self.db, self.manifest)

    def test_disabled_site_binding_excludes_item_before_body_access(self):
        self.change("""INSERT INTO external_source_instances(id,instance_key,provider_kind,service,display_name,enabled)
            VALUES (1,'synthetic','mcp_gateway','confluence','Synthetic',0)""")
        self.change("UPDATE atlassian_sites SET source_instance_id=1")
        scope = self.manifest["snapshots"][0]
        scope["events"] = []
        scope["items"] = [selection(1, "Reduce latency.")]
        with patch("localbrain.work_reconstruction_input._text") as body:
            with self.assertRaises(ExperimentError): load_snapshots(self.db, self.manifest)
            body.assert_not_called()

    def test_reference_identity_comes_from_canonical_metadata_not_row_or_label(self):
        from localbrain.work_reconstruction_input import _canonical_reference
        with read_only_database(self.db) as connection:
            document = _canonical_reference(connection, {"target_kind": "context_document", "context_document_id": 1})
        self.assertEqual((document[0], document[2]), ("context-document", "goal.md"))
        self.change("UPDATE context_documents SET title='Renamed source title'")
        with read_only_database(self.db) as connection:
            self.assertEqual(document, _canonical_reference(connection, {"target_kind": "context_document", "context_document_id": 1}))
            self.assertIsNone(_canonical_reference(connection, {"target_kind": "atlassian_item", "external_resource_id": 1}))
        self.change("UPDATE atlassian_items SET remote_id='42'")
        with read_only_database(self.db) as connection:
            item = _canonical_reference(connection, {"target_kind": "atlassian_item", "external_resource_id": 1})
            self.assertEqual((item[0], item[2]), ("wiki-item", "42"))
            self.assertIsNone(_canonical_reference(connection, {"target_kind": "url", "normalized_url": "https://synthetic-user:synthetic-password@localhost/"}))

    def test_selected_persisted_references_feed_the_unchanged_pair_comparator(self):
        from localbrain.work_reconstruction import metadata_baseline, metadata_view
        self.change("""INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count)
            VALUES (2,1,'synthetic-second','/synthetic/second','Synthetic',1)""")
        self.change("UPDATE atlassian_items SET remote_id='42'")
        scope = self.manifest["snapshots"][0]
        scope["session_ids"] = [1, 2]
        scope["documents"] = [selection(1, "Improve indexing.")]
        scope["items"] = [selection(1, "Reduce latency.")]
        self.change("""INSERT INTO session_reference_scans(session_id,source_fingerprint,extractor_version,status,scanned_at,updated_at)
            VALUES (2,?,'synthetic','ok',?,?)""", ("0" * 64, AT, AT))
        for sid in (1, 2):
            for number, kind, document, item, url in ((1, "context_document", 1, None, None),
                                                       (2, "atlassian_item", None, 1, "https://example.test/wiki/42")):
                identity = "synthetic-{}-{}".format(sid, number)
                self.change("""INSERT INTO session_reference_evidence(session_id,source_path,source_line,evidence_ordinal,
                    target_kind,target_key,context_document_id,external_resource_id,evidence_kind,observed_identity,
                    normalized_url,observed_at,extractor_version,evidence_key,first_observed_at,last_observed_at)
                    VALUES (?,'/synthetic/source',1,?,?,?, ?,?,'user_mention',?,?,?,'synthetic',?,?,?)""",
                            (sid, number, kind, identity, document, item, identity, url, AT,
                             hashlib.sha256(identity.encode()).hexdigest(), AT, AT))
        data = load_snapshots(self.db, self.manifest)[0]
        self.assertTrue(data["coverage"]["complete"])
        self.assertEqual((len(data["artifacts"]), len(data["references"])), (2, 4))
        self.assertEqual(len(metadata_baseline(metadata_view(data))["flows"]), 1)
        prepared = self.prepare()["manifest"]["snapshots"][-1]
        self.assertEqual([r["id"] for r in prepared["documents"]], [1])
        self.assertEqual([r["id"] for r in prepared["items"]], [1])

    def test_missing_reference_scan_is_partial_not_false_completeness(self):
        self.change("DELETE FROM session_reference_scans")
        data = load_snapshots(self.db, self.manifest)[0]
        self.assertFalse(data["coverage"]["complete"])

    def test_invalid_manifest_and_all_category_limits_fail_before_database_access(self):
        variants = []
        for field, limit in (("events", 12000), ("documents", 20), ("items", 20), ("organization", 20)):
            value = copy.deepcopy(self.manifest)
            value["snapshots"][0][field] = [selection(i, "Fix parsing.") for i in range(limit + 1)]
            variants.append(value)
        value = copy.deepcopy(self.manifest); value["source_ids"] = list(range(1,10)); variants.append(value)
        value = copy.deepcopy(self.manifest); value["snapshots"][0]["session_ids"] = list(range(1,62)); variants.append(value)
        value = copy.deepcopy(self.manifest); value["snapshots"][0]["events"][0]["end"] = 4001; variants.append(value)
        value = copy.deepcopy(self.manifest); value["snapshots"][0]["organization_links"] = list(range(1,202)); variants.append(value)
        value = copy.deepcopy(self.manifest); value["source_ids"] = [True]; variants.append(value)
        for value in variants:
            with patch("localbrain.work_reconstruction_input.sqlite3.connect") as connect:
                with self.assertRaises(ExperimentError): load_snapshots(self.db, value)
                connect.assert_not_called()

    def test_no_default_or_missing_database_creation(self):
        missing = self.root / "missing.sqlite"
        with self.assertRaises(ExperimentError): load_snapshots(missing, self.manifest)
        self.assertFalse(missing.exists())

    def test_supervised_load_uses_no_bootstrap(self):
        result, resources = supervise("load", (str(self.db), self.manifest))
        self.assertEqual(result[0]["records"][0]["text"], "Fix parsing.")
        self.assertGreater(resources["peak_bytes"], 0)

    def test_extended_selection_keeps_source_record_and_existing_statement_identity(self):
        from localbrain.work_reconstruction import reconstruct
        first = load_snapshots(self.db, self.manifest)[0]
        self.change("UPDATE activity_events SET text='Fix parsing. Improve indexing.'")
        self.manifest["snapshots"][0]["events"] = [selection("event-1", "Fix parsing. Improve indexing.")]
        second = load_snapshots(self.db, self.manifest)[0]
        self.assertEqual(first["records"][0]["key"], second["records"][0]["key"])
        earlier = reconstruct(first)["flows"][0]["members"][0]["statement_key"]
        self.assertIn(earlier, {m["statement_key"] for f in reconstruct(second)["flows"] for m in f["members"]})

    def test_owner_record_and_relationship_are_read_only(self):
        self.change("INSERT INTO workstreams(id,name,summary,updated_at) VALUES (1,'Synthetic','Fix parsing.',?)", (AT,))
        self.change("INSERT INTO workstream_links(id,workstream_id,entity_type,entity_id,created_at) VALUES (1,1,'session','1',?)", (AT,))
        scope = self.manifest["snapshots"][0]
        scope["organization"] = [selection(1, "Fix parsing.", table="workstreams")]
        scope["organization_links"] = [1]
        self.assertEqual(len(load_snapshots(self.db, self.manifest)[0]["organization_links"]), 1)
        self.change("UPDATE workstream_links SET linked_by='inferred'")
        with self.assertRaises(ExperimentError): load_snapshots(self.db, self.manifest)

    def test_command_success_is_private_and_does_not_claim_viability(self):
        data = snapshot([record("r", "Fix parsing.")])
        gold = bind_expectations(data, {"version": 1, "groups": [goal("g", "parsing", "fix", data["records"])],
                                       "negative": [], "unresolved": 0})
        fixture, expected = self.root / "fixture.json", self.root / "expected.json"
        fixture.write_text(json.dumps({"version": 1, "snapshots": [data]}))
        expected.write_text(json.dumps({"version": 1, "snapshots": {"synthetic": gold}}))
        output = self.root / "result"
        command = [sys.executable, "-B", str(ROOT / "scripts/experiment-work-reconstruction.py"),
                   "--fixture", str(fixture), "--expectations", str(expected), "--output-dir", str(output),
                   "--owner", "synthetic", "--expires-at", self.manifest["expires_at"]]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "EXPERIMENT_RECORDED\n", ""))
        report = json.loads((output / "comparison.json").read_text())
        self.assertEqual(report["report"]["viability"], "unverified")
        self.assertEqual(output.stat().st_mode & 0o777, 0o700)
        self.assertEqual((output / "comparison.json").stat().st_mode & 0o777, 0o600)
        again = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual((again.returncode, again.stdout, again.stderr), (2, "EXPERIMENT_FAILED\n", ""))

    def test_database_command_end_to_end_keeps_source_and_private_output_local(self):
        data = load_snapshots(self.db, self.manifest)[0]
        expected = {"version": 1, "groups": [goal("g", "parsing", "fix", data["records"])],
                    "negative": [], "unresolved": 0}
        manifest, answers = self.root / "manifest.json", self.root / "answers.json"
        manifest.write_text(json.dumps(self.manifest))
        answers.write_text(json.dumps({"version": 1, "snapshots": {"synthetic": bind_expectations(data, expected)}}))
        output = self.root / "private-result"
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/experiment-work-reconstruction.py"),
                                 "--database", str(self.db), "--manifest", str(manifest),
                                 "--expectations", str(answers), "--output-dir", str(output)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "EXPERIMENT_RECORDED\n", ""))
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())
        report = json.loads((output / "comparison.json").read_text())["report"]
        self.assertEqual((report["input_kind"], report["private_quality"], report["viability"]),
                         ("private", "insufficient", "unverified"))
        self.assertNotIn(str(self.db), result.stdout + result.stderr)

    def prepare(self):
        return prepare_current(self.db, "2030-03-01T00:00:00Z", "synthetic", "2031-01-01T00:00:00Z")

    def test_current_preparation_spans_history_without_predictions_or_organization(self):
        for sid in range(2, 71):
            at = (datetime(2030, 1, 1, tzinfo=timezone.utc) + timedelta(hours=sid)).isoformat()
            self.change("""INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count)
                VALUES (?,1,?,'/synthetic/extra','Synthetic',1)""", (sid, str(sid)))
            self.change("""INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,role,text,source_line)
                VALUES (?,?,1,?,'message','user','Fix parsing.',1)""", ("event-{}".format(sid), sid, at))
        with patch("localbrain.work_reconstruction_experiment.reconstruct", side_effect=AssertionError("prediction")), \
             patch("localbrain.work_reconstruction.reconstruct", side_effect=AssertionError("prediction")), \
             patch("localbrain.work_reconstruction.metadata_baseline", side_effect=AssertionError("prediction")):
            prepared = self.prepare()
        selected = prepared["manifest"]["snapshots"][-1]["session_ids"]
        self.assertEqual(len(selected), 60)
        self.assertIn(1, selected); self.assertIn(70, selected)
        self.assertEqual(prepared["preparation"]["outside_sample_sessions"], 10)
        self.assertEqual(len(prepared["snapshots"]), 3)
        self.assertEqual(prepared["manifest"], self.prepare()["manifest"])
        answers = unassessed_expectations(prepared["snapshots"])
        self.assertTrue(all(not g["groups"] and not g["negative"] and g["unresolved"] > 0
                            for g in answers["snapshots"].values()))

    def test_current_preparation_event_prefix_caps_remain_partial(self):
        self.change("UPDATE activity_events SET text=?", ("x" * 1500,))
        for number in range(2, 35):
            self.change("""INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,role,text,source_line)
                VALUES (?,1,?,?,'message','user',?,1)""", ("extra-{}".format(number), number, AT, "x" * 1500))
        prepared = self.prepare()
        scope = prepared["manifest"]["snapshots"][-1]
        self.assertEqual(len(scope["events"]), 32)
        self.assertEqual(sum(e["end"] - e["start"] for e in scope["events"]), 32000)
        self.assertFalse(scope["coverage"]["complete"])
        self.assertFalse(prepared["snapshots"][-1]["coverage"]["complete"])
        self.assertEqual(prepared["snapshots"], load_snapshots(self.db, prepared["manifest"]))

    def test_current_preparation_checks_scope_and_time_before_bodies(self):
        self.change("UPDATE sessions SET index_policy='metadata_only'")
        with patch("localbrain.work_reconstruction_preparation._prefix") as prefix:
            with self.assertRaises(ExperimentError): self.prepare()
            prefix.assert_not_called()
        self.change("UPDATE sessions SET index_policy='full'")
        self.change("UPDATE activity_events SET occurred_at='2035-01-01T00:00:00Z'")
        with patch("localbrain.work_reconstruction_preparation._prefix") as prefix:
            with self.assertRaises(ExperimentError): self.prepare()
            prefix.assert_not_called()

    def test_current_preparation_source_limit_fails_before_body_reads(self):
        for sid in range(2, 10):
            self.change("INSERT INTO sources(id,kind,name,root_path) VALUES (?,?,'Synthetic','/synthetic')", (sid, str(sid)))
            self.change("""INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count)
                VALUES (?,?,?,'/synthetic/extra','Synthetic',1)""", (sid, sid, str(sid)))
            self.change("""INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,role,text,source_line)
                VALUES (?,?,1,?,'message','user','Fix parsing.',1)""", ("extra-{}".format(sid), sid, AT))
        with patch("localbrain.work_reconstruction_preparation._prefix") as prefix:
            with self.assertRaises(ExperimentError): self.prepare()
            prefix.assert_not_called()

    def test_preparation_has_no_implicit_unrelated_document_or_item_body_access(self):
        prepared = self.prepare()
        scope = prepared["manifest"]["snapshots"][-1]
        self.assertEqual(scope["documents"], [])
        self.assertEqual(scope["items"], [])
        self.assertEqual(scope["organization"], [])

    def test_preparation_includes_optional_owner_goals_and_only_user_links(self):
        self.change("INSERT INTO workstreams(id,name,summary,updated_at) VALUES (1,'Synthetic','Fix parsing.',?)", (AT,))
        self.change("INSERT INTO threads(id,workstream_id,title,current_goal,updated_at) VALUES (1,1,'Synthetic','Improve indexing.',?)", (AT,))
        self.change("INSERT INTO checkpoints(id,workstream_id,current_goal,updated_at) VALUES (1,1,'Reduce latency.',?)", (AT,))
        self.change("INSERT INTO workstream_links(id,workstream_id,entity_type,entity_id,created_at) VALUES (1,1,'session','1',?)", (AT,))
        scope = self.prepare()["manifest"]["snapshots"][-1]
        self.assertEqual({v["table"] for v in scope["organization"]}, {"workstreams", "threads", "checkpoints"})
        self.assertEqual(scope["organization_links"], [1])
        self.change("UPDATE workstream_links SET linked_by='inferred'")
        self.assertEqual(self.prepare()["manifest"]["snapshots"][-1]["organization"], [])

    def test_preparation_unknown_timestamps_are_not_assumed_utc(self):
        self.change("""INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,role,text,source_line)
            VALUES ('unknown-time',1,2,'not-a-time','message','user','Fix caching.',1)""")
        # An unlocatable first observation cannot establish a sample boundary.
        with self.assertRaises(ExperimentError): self.prepare()

    def test_preparation_cli_reports_unassessed_not_accuracy_and_keeps_database_unchanged(self):
        output = self.root / "prepared-result"
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        command = [sys.executable, "-B", str(ROOT / "scripts/experiment-work-reconstruction.py"),
                   "--database", str(self.db), "--prepare-through", "2030-03-01T00:00:00Z", "--unassessed",
                   "--owner", "synthetic", "--expires-at", "2031-01-01T00:00:00Z", "--output-dir", str(output)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "EXPERIMENT_RECORDED\n", ""))
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())
        report = json.loads((output / "comparison.json").read_text())["report"]
        self.assertEqual((report["assessment"], report["private_quality"], report["viability"]),
                         ("unassessed", "insufficient", "unverified"))
        self.assertTrue(report["input_manifest"])
        refused = subprocess.run([arg for arg in command if arg != "--unassessed"], capture_output=True, text=True, timeout=30)
        self.assertEqual((refused.returncode, refused.stdout, refused.stderr), (2, "EXPERIMENT_FAILED\n", ""))


class ReconstructionRuntimeTests(unittest.TestCase):
    def test_output_scope_expiry_and_failed_publication_leave_no_task_artifact(self):
        with tempfile.TemporaryDirectory(prefix="localbrain-reconstruction-test-") as temporary:
            root = Path(temporary).resolve()
            output = root / "result"
            with self.assertRaises(ExperimentError): publish(output, {}, "synthetic", "2000-01-01T00:00:00Z")
            expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            with self.assertRaises(ExperimentError): publish(ROOT / "forbidden-experiment-output", {}, "synthetic", expiry)
            with patch("localbrain.work_reconstruction_experiment.os.open", side_effect=OSError("synthetic write failure")):
                with self.assertRaises(OSError): publish(output, {}, "synthetic", expiry)
            self.assertFalse(output.exists())
            self.assertEqual(list(root.iterdir()), [])

    def test_interrupted_supervision_reaps_only_its_task_worker(self):
        before = {p.pid for p in multiprocessing.active_children()}
        with patch("multiprocessing.connection.Connection.poll", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                supervise("text", (snapshot([record("r", "Fix parsing.")]),))
        self.assertEqual(before, {p.pid for p in multiprocessing.active_children()})

    def test_json_duplicate_nonfinite_and_byte_limits(self):
        for payload in (b'{"a":1,"a":2}', b'{"a":NaN}', b'[[['):
            with self.assertRaises(ExperimentError): decode_bounded(payload)
        with self.assertRaises(ExperimentError): encode_bounded({"large": "x" * 100}, limit=20)

    def test_resource_limits_kill_and_reap_task_child(self):
        data = snapshot([record("r", "Fix parsing.")])
        before = {p.pid for p in multiprocessing.active_children()}
        for overrides in ({"wall_seconds": 0.000001}, {"memory_bytes": 1}):
            with self.subTest(overrides=overrides), self.assertRaises(ExperimentError):
                supervise("text", (data,), **overrides)
        self.assertEqual(before, {p.pid for p in multiprocessing.active_children()})

    def test_missing_resource_monitor_fails_closed(self):
        data = snapshot([record("r", "Fix parsing.")])
        with patch("localbrain.work_reconstruction_experiment._memory_usage", side_effect=ExperimentError("MONITOR_UNAVAILABLE")):
            with self.assertRaises(ExperimentError): supervise("text", (data,))

    def test_three_snapshots_record_stability_without_private_claim(self):
        snapshots, expected = [], {"version": 1, "snapshots": {}}
        for n in range(3):
            rows = [record(str(i), "Fix parsing.", i+1) for i in range(n+1)]
            data = snapshot(rows, name="snapshot-{}".format(n))
            snapshots.append(data)
            expected["snapshots"][data["name"]] = bind_expectations(data, {
                "version": 1, "groups": [goal("g", "parsing", "fix", rows)], "negative": [], "unresolved": 0})
        report = evaluate_history(snapshots, expected)
        self.assertEqual(len(report["history"]), 2)
        self.assertEqual(report["viability"], "unverified")

    def test_import_and_help_do_not_load_application_or_config(self):
        code = "import localbrain.work_reconstruction_experiment,sys; assert 'localbrain.config' not in sys.modules; assert 'localbrain.db' not in sys.modules"
        result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        help_result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/experiment-work-reconstruction.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--database", help_result.stdout)


if __name__ == "__main__":
    unittest.main()
