import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from localbrain.terminal.workspaces import read_workspaces, change_workspaces, WorkspaceError


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lb-workspaces-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = SimpleNamespace(data_dir=self.root / "data")
        self.state = {"generation": "a" * 32, "tabs": [], "terminals": []}

    def change(self, action, **body):
        return change_workspaces(self.config, lambda: self.state, action, body)

    def test_empty_workspace_survives_manager_generations_and_observation_never_writes(self):
        self.assertEqual(read_workspaces(self.config, self.state)["items"], [])
        self.assertFalse(self.config.data_dir.exists())
        identity = self.change("create", name="Review", cwd="")["id"]
        self.state["generation"] = None
        self.assertEqual(read_workspaces(self.config, self.state)["items"][0]["id"], identity)
        self.state["generation"] = "b" * 32
        self.assertEqual(read_workspaces(self.config, self.state)["items"][0]["name"], "Review")
        self.assertEqual((self.config.data_dir / "terminal-workspaces.json").stat().st_mode & 0o777, 0o600)

    def test_legacy_adoption_different_root_tab_membership_and_no_reassignment_on_retry(self):
        self.state["tabs"] = [{"id": "t-a", "cwd": "/demo/a", "terminals": []}, {"id": "t-b", "cwd": "/demo/b", "terminals": []}]
        projected = read_workspaces(self.config, self.state)
        self.assertTrue(projected["needsSave"])
        self.assertFalse(self.config.data_dir.exists())
        saved = self.change("reconcile", generation=self.state["generation"])
        first, second = saved["items"]
        self.change("move", id=first["id"], tabId="t-b", generation=self.state["generation"])
        current = read_workspaces(self.config, self.state)["items"]
        self.assertEqual(current[0]["tabs"], ["t-a", "t-b"])
        self.assertEqual(current[1]["tabs"], [])
        with self.assertRaises(WorkspaceError):
            self.change("attach", id=second["id"], tabId="t-b", generation=self.state["generation"])
        self.assertEqual(read_workspaces(self.config, self.state)["items"][0]["tabs"], ["t-a", "t-b"])
        with self.assertRaises(WorkspaceError): self.change("remove", id=first["id"])
        self.state["tabs"] = []
        self.assertEqual(len(self.change("reconcile", generation=self.state["generation"])["items"]), 2)
        self.assertEqual(len(self.change("remove", id=second["id"])["items"]), 1)

    def test_new_generation_drops_membership_but_keeps_workspace_names_defaults_and_ids(self):
        room = self.change("create", name="Mixed", cwd="/demo/default")["id"]
        self.state["tabs"] = [{"id":"tab-new", "cwd":"/demo/other", "terminals":[]}]
        self.change("attach", id=room, tabId="tab-new", generation=self.state["generation"])
        self.assertEqual(len(read_workspaces(self.config, self.state)["items"]), 1)
        self.state = {"generation":"c" * 32, "tabs":[], "terminals":[]}
        item = self.change("reconcile", generation=self.state["generation"])["items"][0]
        self.assertEqual(item, {"id":room, "name":"Mixed", "cwd":"/demo/default", "tabs":[]})
        with self.assertRaises(WorkspaceError): self.change("move", id=room, tabId="tab-new", generation="a" * 32)

    def test_failed_or_unsafe_publication_preserves_existing_metadata_and_unrelated_files(self):
        self.change("create", name="Keep", cwd="")
        path = self.config.data_dir / "terminal-workspaces.json"
        original = path.read_bytes()
        with mock.patch("localbrain.terminal.workspaces.atomic_private_write", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError): self.change("create", name="Later", cwd="")
        self.assertEqual(path.read_bytes(), original)
        path.unlink()
        keep = self.root / "keep"; keep.write_text("unchanged"); keep.chmod(0o600)
        path.symlink_to(keep)
        self.assertIn("error", read_workspaces(self.config, self.state))
        with self.assertRaises((ValueError, OSError)): self.change("create", name="Later", cwd="")
        self.assertEqual(keep.read_text(), "unchanged")

    def test_default_and_title_edits_preserve_existing_tab_identity(self):
        room = self.change("create", name="Before", cwd="")["id"]
        self.state["tabs"] = [{"id":"tab", "cwd":"/demo/a", "terminals":[]}]
        self.change("attach", id=room, tabId="tab", generation=self.state["generation"])
        item = self.change("update", id=room, name="After", cwd="/demo/b")["items"][0]
        self.assertEqual(item, {"id":room, "name":"After", "cwd":"/demo/b", "tabs":["tab"]})


class WorkspaceRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lb-workspace-api-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); cache = self.root / "cache"; cache.mkdir(mode=0o700)
        self.config = SimpleNamespace(data_dir=self.root / "data")
        class Control:
            def __init__(inner):
                inner.root = cache; inner.calls = []; inner.receipts = {}; inner.count = 0
                inner.state = {"running":True,"generation":"a"*32,"tabs":[],"terminals":[],"service":{"state":"running","running":True}}
            def list(inner): return json.loads(json.dumps(inner.state))
            def dependencies(inner): return {"node":True,"npm":True,"installed":True,"bundleReady":True}
            def create(inner, body):
                inner.calls.append(dict(body))
                if body["key"] in inner.receipts: return json.loads(json.dumps(inner.receipts[body["key"]]))
                inner.count += 1; identity = "term-" + str(inner.count)
                tab = next((tab for tab in inner.state["tabs"] if tab["id"] == body.get("tabId")), None)
                if tab is None:
                    tab = {"id":"tab-"+str(inner.count),"cwd":body["cwd"],"terminals":[],"hidden":False}
                    inner.state["tabs"].append(tab)
                term = {"id":identity,"tabId":tab["id"],"cwd":body["cwd"],"pid":2000+inner.count}
                tab["terminals"].append(identity); inner.state["terminals"].append(term)
                value = {**inner.list(),"terminal":dict(term),"tabId":tab["id"]}
                inner.receipts[body["key"]] = value
                return json.loads(json.dumps(value))
        from localbrain.terminal.web import install_routes
        self.control = Control(); app = FastAPI(); install_routes(app, None, self.config)
        app.state.terminal_factory = lambda:self.control
        self.client = TestClient(app, base_url="http://127.0.0.1:8123")
        self.headers = {"Origin":"http://127.0.0.1:8123"}

    def post(self, path, body):
        response = self.client.post("/api/terminal/"+path, json=body, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def room(self, name): return self.post("workspaces/create", {"name":name,"cwd":""})["id"]

    def test_different_root_tabs_panes_order_and_metadata_move_preserve_process_ids(self):
        a = self.room("A"); b = self.room("B")
        one = self.post("terminals", {"workspaceId":a,"key":"one","cwd":"/demo/a","shell":"/bin/sh"})
        self.post("terminals", {"workspaceId":a,"key":"split","tabId":one["tabId"],"direction":"right","cwd":"/demo/b","shell":"/bin/sh"})
        two = self.post("terminals", {"workspaceId":a,"key":"two","cwd":"/demo/b","shell":"/bin/sh"})
        self.assertEqual(len(self.control.state["tabs"]), 2)
        self.assertEqual(self.control.state["tabs"][0]["terminals"], ["term-1","term-2"])
        self.assertTrue(all("workspaceId" not in body for body in self.control.calls))
        self.post("view-order", {"generation":"a"*32,"order":[two["tabId"],one["tabId"]]})
        before = [(t["id"],t["pid"]) for t in self.control.state["terminals"]]
        self.post("workspaces/move", {"id":b,"tabId":one["tabId"],"generation":"a"*32})
        self.assertEqual([(t["id"],t["pid"]) for t in self.control.state["terminals"]], before)
        state = self.client.get("/api/terminal").json()
        self.assertEqual(next(item for item in state["workspaces"]["items"] if item["id"]==b)["tabs"], [one["tabId"]])

    def test_origin_and_post_creation_storage_failure_preserve_known_terminal_identity(self):
        response = self.client.post("/api/terminal/workspaces/create", json={"name":"No","cwd":""})
        self.assertEqual(response.status_code, 403)
        a = self.room("A"); path = self.config.data_dir / "terminal-workspaces.json"; before = path.read_bytes()
        with mock.patch("localbrain.terminal.workspaces.atomic_private_write", side_effect=OSError("synthetic failure")):
            result = self.post("terminals", {"workspaceId":a,"key":"one","cwd":"/demo/a","shell":"/bin/sh"})
        self.assertEqual(result["terminal"]["id"], "term-1")
        self.assertIn("workspaceError", result)
        self.assertEqual(len(self.control.state["terminals"]), 1)
        self.assertEqual(path.read_bytes(), before)

    def test_retry_cannot_silently_move_confirmed_membership(self):
        a = self.room("A"); b = self.room("B")
        body = {"key":"same","cwd":"/demo/a","shell":"/bin/sh"}
        one = self.post("terminals", {**body,"workspaceId":a})
        again = self.post("terminals", {**body,"workspaceId":b})
        self.assertEqual(one["terminal"]["id"], again["terminal"]["id"])
        self.assertIn("workspaceError", again)
        current = self.client.get("/api/terminal").json()["workspaces"]["items"]
        self.assertEqual(next(item for item in current if item["id"]==a)["tabs"], [one["tabId"]])
        self.assertEqual(next(item for item in current if item["id"]==b)["tabs"], [])

    def test_post_create_manager_read_failure_returns_the_known_process_with_warning(self):
        from localbrain.terminal.core import TerminalError
        room = self.room("Keep")
        create = self.control.create
        def create_then_disconnect(body):
            result = create(body)
            self.control.list = mock.Mock(side_effect=TerminalError("disconnected", "synthetic disconnection"))
            return result
        self.control.create = create_then_disconnect
        result = self.post("terminals", {"workspaceId":room,"key":"known","cwd":"/demo/a","shell":"/bin/sh"})
        self.assertEqual(result["terminal"]["id"], "term-1")
        self.assertIn("workspaceError", result)
        self.assertEqual(len(self.control.state["terminals"]), 1)

    def test_defaulted_http_shell_uses_the_same_zsh_integration_as_explicit_creation(self):
        with mock.patch.dict("os.environ", {"SHELL":"/bin/zsh"}):
            for index, extra in enumerate(({}, {"shell":""}, {"shell":"/bin/zsh"})):
                self.post("terminals", {"key":"shell-"+str(index),"cwd":"/demo/a",**extra})
        with mock.patch.dict("os.environ"):
            import os
            os.environ.pop("SHELL", None)
            self.post("terminals", {"key":"fallback","cwd":"/demo/a"})
        shells = [body["shell"] for body in self.control.calls]
        self.assertEqual(len(set(shells)), 1)
        self.assertEqual(Path(shells[0]).name, "launcher")
        self.assertTrue(Path(shells[0]).is_file())
