from types import SimpleNamespace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from localbrain.terminal.presentation import load_order, save_order, PresentationError
from localbrain.terminal.web import install_routes


class TerminalPresentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lb-terminal-view-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "scope"
        self.root.mkdir(mode=0o700)
        self.generation = "a" * 32
        self.tabs = [{"id": "tab-a"}, {"id": "tab-b"}]

    def test_observation_is_no_write_and_old_generation_cannot_restore_tabs(self):
        missing = self.root / "absent"
        self.assertEqual(load_order(missing, None, []), {"order": []})
        self.assertFalse(missing.exists())
        self.assertEqual(load_order(self.root, self.generation, self.tabs), {"order": ["tab-a", "tab-b"]})
        self.assertEqual(list(self.root.iterdir()), [])
        save_order(self.root, self.generation, self.tabs, ["tab-b", "tab-a"])
        self.assertEqual(load_order(self.root, self.generation, self.tabs + [{"id": "tab-c"}])["order"], ["tab-b", "tab-a", "tab-c"])
        self.assertEqual(load_order(self.root, "b" * 32, self.tabs)["order"], ["tab-a", "tab-b"])
        self.assertEqual((self.root / "view-order.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(set(json.loads((self.root / "view-order.json").read_text())), {"schema", "generation", "tabs"})

    def test_changed_membership_and_failed_write_preserve_confirmed_order(self):
        save_order(self.root, self.generation, self.tabs, ["tab-b", "tab-a"])
        path = self.root / "view-order.json"
        original = path.read_bytes()
        for order in (["tab-a"], ["tab-a", "tab-a"], ["tab-a", "foreign"], ["tab-a", True]):
            with self.subTest(order=order), self.assertRaises(PresentationError):
                save_order(self.root, self.generation, self.tabs, order)
        with mock.patch("localbrain.terminal.presentation.atomic_private_write", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError): save_order(self.root, self.generation, self.tabs, ["tab-a", "tab-b"])
        self.assertEqual(path.read_bytes(), original)

    def test_unsafe_or_corrupt_cache_cannot_replace_other_file_or_gate_controls(self):
        path = self.root / "view-order.json"
        canary = self.root / "keep.json"
        canary.write_text("synthetic keep"); canary.chmod(0o600)
        for kind in ("symlink", "hardlink", "large", "corrupt", "public-mode"):
            with self.subTest(kind=kind):
                if kind == "symlink": path.symlink_to(canary)
                elif kind == "hardlink": os.link(canary, path)
                else:
                    path.write_text("x" * 17000 if kind == "large" else "bad json")
                    path.chmod(0o644 if kind == "public-mode" else 0o600)
                self.assertIn("error", load_order(self.root, self.generation, self.tabs))
                with self.assertRaises((ValueError, OSError)): save_order(self.root, self.generation, self.tabs, ["tab-a", "tab-b"])
                self.assertEqual(canary.read_text(), "synthetic keep")
                path.unlink()

    def test_order_cannot_cross_folder_or_move_background_slots(self):
        tabs = [{"id":"a","cwd":"/demo/a"},{"id":"hidden","cwd":"/demo/a","hidden":True},
                {"id":"other","cwd":"/demo/b"},{"id":"b","cwd":"/demo/a"},
                {"id":"hidden2","cwd":"/demo/a","hidden":True}]
        good = ["b","hidden","other","a","hidden2"]
        save_order(self.root, self.generation, tabs, good)
        for order in (["other","hidden","b","a","hidden2"], ["hidden","b","other","a","hidden2"],
                      ["b","hidden2","other","a","hidden"]):
            with self.subTest(order=order), self.assertRaises(PresentationError):
                save_order(self.root, self.generation, tabs, order)
        self.assertEqual(load_order(self.root, self.generation, tabs)["order"], good)

    def test_manager_change_after_snapshot_cannot_restore_old_generation(self):
        from localbrain.foundation.preferences import atomic_private_write
        state = {"running":True,"generation":self.generation,"tabs":self.tabs,"terminals":[]}
        control=mock.Mock(root=self.root);control.list.side_effect=lambda:dict(state)
        control.dependencies.return_value={"installed":True}
        app=FastAPI();install_routes(app,None,SimpleNamespace(data_dir=self.root / "data"));app.state.terminal_factory=lambda:control
        client=TestClient(app,base_url="http://127.0.0.1:8123")
        def publish(path,data):
            state.update(generation="b"*32,tabs=[{"id":"new-b"},{"id":"new-a"}])
            atomic_private_write(path,data)
        with mock.patch("localbrain.terminal.presentation.atomic_private_write",side_effect=publish):
            response=client.post("/api/terminal/view-order",json={"generation":self.generation,"order":["tab-b","tab-a"]},headers={"Origin":"http://127.0.0.1:8123"})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["generation"],self.generation)
        fresh=client.get("/api/terminal").json()
        self.assertEqual(fresh["presentation"]["order"],["new-b","new-a"])
        control.rpc.assert_not_called()

    def test_route_is_same_origin_generation_bound_and_forwards_single_stop_generation(self):
        state = {"running": True, "generation": self.generation, "tabs": self.tabs, "terminals": [], "service": {"state": "running"}}
        control = mock.Mock(root=self.root)
        control.list.side_effect = lambda: dict(state)
        control.dependencies.return_value = {"installed": True}
        app = FastAPI(); install_routes(app, None, SimpleNamespace(data_dir=self.root / "data")); app.state.terminal_factory = lambda: control
        client = TestClient(app, base_url="http://127.0.0.1:8123")
        body = {"generation": self.generation, "order": ["tab-b", "tab-a"]}
        self.assertEqual(client.post("/api/terminal/view-order", json=body).status_code, 403)
        headers = {"Origin": "http://127.0.0.1:8123"}
        self.assertEqual(client.post("/api/terminal/view-order", json=body, headers=headers).status_code, 200)
        self.assertEqual(client.get("/api/terminal").json()["presentation"]["order"], ["tab-b", "tab-a"])
        self.assertEqual(client.post("/api/terminal/view-order", json={**body, "generation": "b" * 32}, headers=headers).status_code, 409)
        self.assertEqual(client.post("/api/terminal/view-order", json={**body, "order": ["tab-a"]}, headers=headers).status_code, 409)
        control.rpc.return_value = state
        response = client.post("/api/terminal/terminals/t-synthetic/stop", json={"generation": self.generation}, headers=headers)
        self.assertEqual(response.status_code, 200)
        control.rpc.assert_called_once_with("stop", {"id": "t-synthetic", "force": False}, generation=self.generation)
