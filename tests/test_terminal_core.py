"""Actual host boundary, settings parity and app access; synthetic paths only."""
import asyncio
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from localbrain.app import edition
from localbrain.foundation.preferences import PreferencesError
from localbrain.terminal.core import MAX_REPLY, TerminalError, TerminalService, _bounded_control, runtime_executable
from localbrain.terminal.web import install_routes


class CoreHostTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="lb-core-host-",dir="/private/tmp" if sys.platform=="darwin" else None)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.control=TerminalService(SimpleNamespace(data_dir=self.root/"data",cache_dir=self.root/"cache"),launcher="process")

    def test_strict_control_wire_rejects_invalid_without_start_or_files(self):
        request,_=self.control.request("service.status",{})
        for change in ({"wire":True},{"wire":2},{"unknown":1},{"operation":"shell.exec"},{"arguments":{"exec":"/bin/sh"}}):
            value={**request,**change}
            result=subprocess.run([str(runtime_executable()),"control"],input=json.dumps(value).encode()+b"\n",capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(result.stdout,b"")
        self.assertFalse(self.control.root.exists())

    def test_response_id_shape_and_preferences_kind_are_verified(self):
        def reply(command,data,timeout):
            request=json.loads(data)
            return json.dumps({"wire":1,"id":request["id"],"ok":False,"error":{"kind":"preferences","code":"invalid","message":"synthetic preference failure"}}).encode()+b"\n"
        with mock.patch("localbrain.terminal.core._bounded_control",side_effect=reply),self.assertRaisesRegex(PreferencesError,"synthetic"):
            self.control.call("settings.read",{})
        for value in ({"wire":1,"id":"wrong","ok":True,"result":{}}, {"wire":True,"id":"wrong","ok":True,"result":{}}, []):
            with self.subTest(value=value),mock.patch("localbrain.terminal.core._bounded_control",return_value=json.dumps(value).encode()+b"\n"),self.assertRaises(TerminalError):
                self.control.status()

    def test_child_stdout_stderr_and_blocked_stdin_have_bounded_failure(self):
        for code in (f"import sys;sys.stdout.buffer.write(b'x'*{MAX_REPLY+2});sys.stdout.flush()", "import sys;sys.stderr.buffer.write(b'x'*10000);sys.stderr.flush()"):
            with self.assertRaises(TerminalError):
                _bounded_control([sys.executable,"-c",code],b"\n",3)
        before=time.monotonic()
        with self.assertRaises(TerminalError):
            _bounded_control([sys.executable,"-c","import time;time.sleep(30)"],b"x"*128000,0.15)
        self.assertLess(time.monotonic()-before,3)

    def test_real_control_child_receives_launch_paths_without_host_credentials(self):
        environment={"LOCALBRAIN_DESKTOP_TOKEN":"synthetic-desktop-token","UNRELATED_HOST_SECRET":"synthetic-private","HF_HUB_CACHE":str(self.root/"public-hub"),"SHELL":"/bin/sh"}
        code="import os,json;print(json.dumps({'desktop':'LOCALBRAIN_DESKTOP_TOKEN' in os.environ,'other':'UNRELATED_HOST_SECRET' in os.environ,'hub':os.environ.get('HF_HUB_CACHE'),'shell':os.environ.get('SHELL')}))"
        with mock.patch.dict(os.environ,environment):
            output=_bounded_control([sys.executable,"-c",code],b"",3)
            self.assertEqual(os.environ["LOCALBRAIN_DESKTOP_TOKEN"],"synthetic-desktop-token")
        self.assertEqual(json.loads(output),{"desktop":False,"other":False,"hub":str(self.root/"public-hub"),"shell":"/bin/sh"})
        # The same filtered child environment must still protect all configured
        # public model caches, even when their private destination does not exist.
        for key,suffix in (("HF_HUB_CACHE",""),("HUGGINGFACE_HUB_CACHE",""),("HF_HOME","hub"),("XDG_CACHE_HOME","huggingface/hub")):
            with self.subTest(key=key),mock.patch.dict(os.environ,{name:"" for name in ("HF_HOME","HF_HUB_CACHE","HUGGINGFACE_HUB_CACHE","XDG_CACHE_HOME")}):
                os.environ[key]=str(self.root/"public-hub")
                request,_=self.control.request("service.status",{})
                private=self.root/"public-hub"/suffix/"private-data"
                request["context"]={**request["context"],"dataDir":str(private)}
                reply=json.loads(_bounded_control([str(runtime_executable()),"control"],json.dumps(request).encode()+b"\n",3))
                self.assertFalse(reply["ok"])
                self.assertFalse(private.exists())

    def test_stream_spawn_uses_the_same_credential_free_environment(self):
        process=SimpleNamespace(stdin=SimpleNamespace(write=mock.Mock(),drain=mock.AsyncMock()))
        spawn=mock.AsyncMock(return_value=process)
        with mock.patch.dict(os.environ,{"LOCALBRAIN_DESKTOP_TOKEN":"synthetic-desktop-token","XDG_CACHE_HOME":str(self.root/"public-cache")}),mock.patch("localbrain.terminal.core.asyncio.create_subprocess_exec",spawn):
            self.assertIs(asyncio.run(self.control.stream("t-synthetic","11","xterm6-v3")),process)
        child=spawn.call_args.kwargs["env"]
        self.assertNotIn("LOCALBRAIN_DESKTOP_TOKEN",child)
        self.assertEqual(child["XDG_CACHE_HOME"],str(self.root/"public-cache"))
        self.assertEqual(child["LOCALBRAIN_TERMINAL_LAUNCHER"],"process")


class NativeTerminalAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.app=FastAPI()
        install_routes(self.app,None,object())
        self.calls=[]
        class Control:
            async def stream(inner,terminal,unicode,checkpoint):
                self.calls.append((terminal,unicode,checkpoint))
                raise TerminalError("synthetic","authorized transport reached")
        self.app.state.terminal_factory=Control
        self.native=mock.patch.object(edition,"DESKTOP",True);self.native.start();self.addCleanup(self.native.stop)
        self.env=mock.patch.dict(os.environ,{"LOCALBRAIN_DESKTOP_TOKEN":"synthetic-token"});self.env.start();self.addCleanup(self.env.stop)
        self.client=TestClient(self.app,base_url="http://127.0.0.1:8190")

    def test_ws_rejects_missing_stale_query_only_and_cross_origin_before_spawn(self):
        path="ws://127.0.0.1:8190/api/terminal/terminals/t-synthetic/stream?unicode=11&checkpoint=xterm6-v3"
        for suffix,headers in (("",{}),("",{"cookie":"localbrain-desktop=stale"}),("&token=synthetic-token",{}),("",{"cookie":"localbrain-desktop=synthetic-token","origin":"http://outside.invalid"})):
            with self.subTest(headers=headers),self.assertRaises(WebSocketDisconnect) as result:
                with self.client.websocket_connect(path+suffix,headers={"origin":"http://127.0.0.1:8190",**headers}):pass
            self.assertEqual(result.exception.code,1008)
        self.assertEqual(self.calls,[])

    def test_ws_cookie_and_bearer_use_same_per_launch_token(self):
        path="ws://127.0.0.1:8190/api/terminal/terminals/t-synthetic/stream?unicode=11&checkpoint=xterm6-v3"
        for credential in ({"cookie":"localbrain-desktop=synthetic-token"},{"authorization":"Bearer synthetic-token"}):
            with self.client.websocket_connect(path,headers={"origin":"http://127.0.0.1:8190",**credential}) as connection:
                self.assertEqual(connection.receive_json()["message"],"authorized transport reached")
        self.assertEqual(self.calls,[("t-synthetic","11","xterm6-v3")]*2)
