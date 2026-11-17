"""Opt-in real Rust/payload/PTY parity. Only public packages and owned synthetic scopes."""
import json
import os
from pathlib import Path
import queue
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock
import uuid

from localbrain.terminal.core import TerminalError, TerminalService, runtime_environment, runtime_executable

BUNDLE = os.environ.get("LOCALBRAIN_TERMINAL_TEST_BUNDLE")


class Stream:
    def __init__(self, control, terminal):
        env=runtime_environment();env["LOCALBRAIN_TERMINAL_LAUNCHER"]="process"
        self.process=subprocess.Popen([str(runtime_executable()),"stream"],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        _,request=control.request("terminal.stream",{"id":terminal,"unicodeVersion":"11","checkpointVersion":"xterm6-v3"})
        self.process.stdin.write(request);self.process.stdin.flush()
        self.frames=queue.Queue(maxsize=4)
        def read():
            while True:
                line=self.process.stdout.readline(2*1024*1024+2)
                if not line: return
                self.frames.put(json.loads(line))
        self.reader=threading.Thread(target=read,daemon=True);self.reader.start()

    def send(self,value):
        self.process.stdin.write(json.dumps(value).encode()+b"\n");self.process.stdin.flush()

    def next(self,timeout=15): return self.frames.get(timeout=timeout)

    def output(self, *, ack=True):
        while True:
            frame=self.next()
            if frame["type"]=="error": raise AssertionError(frame)
            if frame["type"]=="output":
                if ack:self.send({"type":"ack","seq":frame["seq"]})
                return frame

    def close(self):
        if not self.process.stdin.closed:self.process.stdin.close()
        try:self.process.wait(timeout=12)
        except subprocess.TimeoutExpired:
            self.process.kill();self.process.wait();raise
        self.reader.join(timeout=1);self.process.stdout.close()


class SocketManager:
    """Owned protocol fixture for precise old-manager and pipe-saturation boundaries."""
    def __init__(self,control,version=2,stop_after_status=False):
        self.control=control;self.version=version;self.calls=[];self.stops=[]
        self.stop_after_status=stop_after_status
        self.input_seen=threading.Event();self.released=threading.Event();self.done=threading.Event()
        self.children=[];self.connections=[];self.claims=0

    def __enter__(self):
        self.control.install()
        selection=json.loads((self.control.root/"selection.json").read_text())
        self.generation=uuid.uuid4().hex
        self.identity={"pid":os.getpid(),"born":"synthetic birth","birthFormat":"utc-lstart-v1",
            "generation":self.generation,"version":self.version,"build":selection["payloadId"]}
        if self.version==2:self.identity.update(scopeHash=selection["scopeHash"],helperProtocol=1,checkpointVersion="xterm6-v3",unicodeVersion="11")
        path=self.control.root/"identity.json";path.write_text(json.dumps(self.identity));path.chmod(0o600)
        self.server=socket.socket(socket.AF_UNIX);self.socket=self.control.root/"control.sock"
        self.server.bind(str(self.socket));self.socket.chmod(0o600);self.server.listen();self.server.settimeout(.1)
        self.socket_inode=self.socket.stat().st_ino
        def handle(connection):
            try:
                data=bytearray()
                while not data.endswith(b"\n"):
                    chunk=connection.recv(65536)
                    if not chunk:return
                    data.extend(chunk)
                request=json.loads(data);method=request["method"];self.calls.append(method)
                if method=="status":
                    result={**self.identity,"running":True,"leaseHeld":True}
                    if self.stop_after_status:
                        # The first caller already read identity. End the fake
                        # generation before returning its final running reply.
                        self.done.set();self.server.close()
                        (self.control.root/"identity.json").unlink();self.socket.unlink()
                elif method=="claim":self.claims+=1;result={"lease":"lease-"+str(self.claims),"writable":True}
                elif method=="read":result={"seq":1,"data":"x"*1900000,"terminal":{"state":"running"},"snapshot":False,"writable":True}
                elif method=="input":
                    self.input_seen.set();connection.sendall(b'{"ok":false,"error":{"code":"input_busy","message":"partial input"}}\n');return
                elif method=="release":self.released.set();result={}
                elif method=="stop":self.stops.append(request["params"]);result={}
                else:result={}
                connection.sendall(json.dumps({"ok":True,"result":result}).encode()+b"\n")
            except OSError:pass
            finally:connection.close()
        def accept():
            while not self.done.is_set():
                try:connection,_=self.server.accept()
                except socket.timeout:continue
                except OSError:return
                self.connections.append(connection);thread=threading.Thread(target=handle,args=(connection,),daemon=True)
                self.children.append(thread);thread.start()
        self.thread=threading.Thread(target=accept,daemon=True);self.thread.start();return self

    def __exit__(self,*args):
        self.done.set();self.server.close()
        for connection in self.connections:
            try:connection.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        self.thread.join(timeout=2)
        for thread in self.children:thread.join(timeout=2)
        identity=self.control.root/"identity.json"
        if identity.exists() and json.loads(identity.read_text())["generation"]==self.generation:identity.unlink()
        if self.socket.exists() and self.socket.stat().st_ino==self.socket_inode:self.socket.unlink()


@unittest.skipUnless(BUNDLE and sys.platform=="darwin","explicit public runtime payload and macOS required")
class RuntimeParityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="lb-rp-",dir="/private/tmp")
        self.root=Path(self.temp.name).resolve();(self.root/"home").mkdir()
        self.config=SimpleNamespace(data_dir=self.root/"data",cache_dir=self.root/"cache")
        self.env=mock.patch.dict(os.environ,{"LOCALBRAIN_TERMINAL_BUNDLE":str(Path(BUNDLE).resolve()),
            "LOCALBRAIN_TERMINAL_RUNTIME":str(Path(BUNDLE).resolve()/"bin/localbrain-runtime"),
            "LOCALBRAIN_TERMINAL_LAUNCHER":"process","HOME":str(self.root/"home"),"SHELL":"/bin/sh",
            "HF_HUB_CACHE":str(self.root/"public-hub")});self.env.start()
        self.control=TerminalService(self.config,launcher="process");self.streams=[];self.controls=[self.control]

    def tearDown(self):
        try:
            for stream in self.streams:stream.close()
            for control in self.controls:
                current=control.list()
                if current["running"]:
                    control.stop(force=True,expected={"generation":current["generation"],"terminals":[t["id"] for t in current["terminals"]]})
        finally:
            self.env.stop();self.temp.cleanup()

    def create(self, control=None, **options):
        return (control or self.control).create({"key":str(uuid.uuid4()),"cwd":str(self.root),"shell":"/bin/sh","cols":80,"rows":24,**options})

    def attach(self, terminal):
        stream=Stream(self.control,terminal);self.streams.append(stream);return stream

    def expected(self, control=None):
        state=(control or self.control).list()
        return {"generation":state["generation"],"terminals":[t["id"] for t in state["terminals"]]}

    def test_cold_offline_create_without_path_node_npm_or_python(self):
        with mock.patch.dict(os.environ,{"PATH":"/synthetic/no-tools"}):
            before=self.control.list();self.assertFalse(self.control.root.exists())
            self.assertTrue(self.control.dependencies()["bundleReady"])
            result=self.create();state=self.control.list()
        self.assertEqual(state["service"]["version"],2)
        self.assertTrue(state["service"]["leaseHeld"])
        self.assertEqual(state["terminals"][0]["id"],result["terminal"]["id"])
        self.assertFalse((self.control.root/"engine").exists())
        identity=json.loads((self.control.root/"identity.json").read_text())
        self.assertEqual(identity["scopeHash"],state["service"]["scopeHash"])

    def test_invalid_cold_launch_never_prepares_or_bootstraps_manager(self):
        for body in ({},{"key":str(uuid.uuid4()),"cwd":str(self.root/"missing"),"shell":"/bin/sh"},
                     {"key":str(uuid.uuid4()),"cwd":str(self.root),"shell":"/bin/sh","rows":1}):
            with self.subTest(body=body),self.assertRaises(TerminalError):self.control.create(body)
            self.assertFalse(self.control.root.exists())

    def test_live_to_stopped_transition_revalidates_before_bootstrap(self):
        with SocketManager(self.control,stop_after_status=True):
            with self.assertRaises(TerminalError) as error:self.create(cwd=str(self.root/"missing"))
            self.assertEqual(error.exception.code,"invalid")
            self.assertFalse((self.control.root/"identity.json").exists())
            self.assertFalse((self.control.root/"control.sock").exists())

    def test_cold_and_live_cwd_lexical_resolution_match_node(self):
        existing=self.root/"existing";existing.mkdir()
        home_existing=self.root/"home/existing";home_existing.mkdir()
        for path,expected in ((str(self.root/"missing/../existing"),existing),("~//existing",home_existing)):
            cold=self.create(cwd=path)
            self.assertEqual(cold["terminal"]["cwd"],str(expected))
            self.assertEqual(self.create(cwd=path)["terminal"]["cwd"],str(expected))
            self.control.stop(force=True,expected=self.expected())

    def test_low_level_stop_cannot_widen_targets_on_already_live_old_manager(self):
        for version in (1,2):
            with self.subTest(version=version),SocketManager(self.control,version) as manager:
                with self.assertRaises(TerminalError) as error:
                    self.control.rpc("stop",{"id":"t-one","all":True,"expected":{"generation":manager.generation,"terminals":["t-one","t-two"]}})
                self.assertEqual(error.exception.code,"invalid")
                self.assertEqual(manager.stops,[])
                self.assertEqual(manager.calls,[])

    def test_full_outbound_pipe_preserves_final_warning_and_releases_input(self):
        with SocketManager(self.control) as manager:
            process=subprocess.Popen([str(runtime_executable()),"stream"],env=runtime_environment(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            try:
                _,request=self.control.request("terminal.stream",{"id":"t-synthetic","unicodeVersion":"11","checkpointVersion":"xterm6-v3"})
                process.stdin.write(request);process.stdin.flush()
                self.assertEqual(json.loads(process.stdout.readline())["type"],"control")
                prefix=process.stdout.read(1);self.assertEqual(prefix,b"{")
                # The 1.9 MB frame has begun; stop reading while both regular slots fill.
                for frame in ({"type":"claim"},{"type":"claim"},{"type":"input","data":"middle fragment"}):
                    process.stdin.write(json.dumps(frame).encode()+b"\n");process.stdin.flush()
                self.assertTrue(manager.input_seen.wait(5))
                self.assertTrue(manager.released.wait(5))
                process.stdin.close()
                result=queue.Queue()
                reader=threading.Thread(target=lambda:result.put(process.stdout.read()),daemon=True);reader.start()
                data=prefix+result.get(timeout=10);reader.join(timeout=1)
                self.assertEqual(process.wait(timeout=3),75)
                frames=[json.loads(line) for line in data.splitlines()]
                self.assertEqual(frames[-1]["code"],"input_busy")
                self.assertFalse(manager.stops)
            finally:
                if process.poll() is None:process.kill();process.wait()
                if not process.stdin.closed:process.stdin.close()
                process.stdout.close()

    def test_exact_idempotency_hide_split_bounds_and_reopen_after_last_close(self):
        first=self.create();term=first["terminal"]
        body={"key":str(uuid.uuid4()),"cwd":str(self.root),"shell":"/bin/sh"}
        one=self.control.create(body);two=self.control.create(body)
        self.assertEqual(one["terminal"]["id"],two["terminal"]["id"])
        with self.assertRaises(TerminalError):self.control.create({**body,"cols":100})
        self.control.rpc("tab",{"id":first["tabId"],"action":"hide"})
        self.assertTrue(next(t for t in self.control.list()["tabs"] if t["id"]==first["tabId"])["hidden"])
        self.control.rpc("tab",{"id":first["tabId"],"action":"show"})
        for _ in range(3):self.create(tabId=first["tabId"],direction="down")
        with self.assertRaises(TerminalError):self.create(tabId=first["tabId"],direction="right")
        self.control.rpc("stop",{"all":True,"force":True,"expected":self.expected()})
        self.assertFalse(self.control.list()["terminals"])
        self.assertEqual(len(self.create()["terminals"]),1)

    def test_stream_exact_ack_takeover_detach_and_same_process_reconnect(self):
        terminal=self.create()["terminal"];first=self.attach(terminal["id"])
        self.assertTrue(first.next()["writable"])
        initial=first.output(ack=False)
        first.send({"type":"ack","seq":True});first.send({"type":"ack","seq":initial["seq"]+1})
        first.send({"type":"input","data":"printf 'synthetic-ack-%s\\n' marker\n"})
        with self.assertRaises(queue.Empty):first.next(timeout=.15)
        first.send({"type":"ack","seq":initial["seq"]})
        text=""
        while "synthetic-ack-marker" not in text:text+=first.output()["data"]
        second=self.attach(terminal["id"]);self.assertFalse(second.next()["writable"]);second.output()
        second.send({"type":"claim"})
        while True:
            frame=second.next()
            if frame["type"]=="output":second.send({"type":"ack","seq":frame["seq"]})
            if frame["type"]=="control":self.assertTrue(frame["writable"]);break
        first.close();self.streams.remove(first)
        second.send({"type":"input","data":"printf 'synthetic-detach-%s\\n' marker\n"})
        text=""
        while "synthetic-detach-marker" not in text:
            frame=second.output();self.assertIsNot(frame.get("writable"),False);text+=frame["data"]
        second.close();self.streams.remove(second)
        state=self.control.list();self.assertEqual(state["terminals"][0]["pid"],terminal["pid"])
        restored=self.attach(terminal["id"]);self.assertTrue(restored.next()["writable"])
        checkpoint=restored.output()["checkpoint"]
        script="""
const fs=require('node:fs');const path=require('node:path');const root=process.argv[1];
const {Terminal}=require(path.join(root,'engine/node_modules/@xterm/headless'));
const {Unicode11Addon}=require(path.join(root,'engine/node_modules/@xterm/addon-unicode11'));
const state=JSON.parse(fs.readFileSync(0,'utf8'));const term=new Terminal({allowProposedApi:true,cols:state.cols,rows:state.rows});
term.loadAddon(new Unicode11Addon());term.unicode.activeVersion='11';
require(path.join(root,'manager/checkpoint.cjs')).restore(term,state);
for(let i=0;i<term.buffer.active.length;i++)console.log(term.buffer.active.getLine(i).translateToString(true));
term.dispose();
"""
        screen=subprocess.check_output([str(Path(BUNDLE)/"bin/node"),"-e",script,str(Path(BUNDLE).resolve())],input=json.dumps(checkpoint).encode(),timeout=5).decode()
        self.assertIn("synthetic-detach-marker",screen)

    def test_conflicting_stop_targets_and_stale_confirmation_change_nothing(self):
        first=self.create();second=self.create();expected=self.expected()
        for operation,args in (("terminal.stop",{"id":first["terminal"]["id"],"all":True,"expected":expected}),
                               ("manager.rpc",{"method":"stop","params":{"id":first["terminal"]["id"],"all":True,"expected":expected},"generation":None})):
            with self.assertRaises(TerminalError) as error:self.control.call(operation,args)
            self.assertEqual(error.exception.code,"invalid")
            self.assertEqual(len(self.control.list()["terminals"]),2)
        with self.assertRaises(TerminalError):self.control.stop(expected={"generation":"stale","terminals":expected["terminals"]})
        self.assertEqual(len(self.control.list()["terminals"]),2)

    def test_private_parent_symlink_cannot_retire_other_active_scope(self):
        self.control.install()
        other=TerminalService(SimpleNamespace(data_dir=self.root/"data-b",cache_dir=self.root/"cache-b"),launcher="process")
        self.controls.append(other);active=self.create(other)
        owned=self.control.root/"payloads-owned";original=self.control.root/"payloads"
        original.rename(owned);original.symlink_to(other.root/"payloads",target_is_directory=True)
        try:
            with self.assertRaises(TerminalError):self.control.call("runtime.retire",{"preview":True})
            self.assertEqual(other.list()["terminals"][0]["id"],active["terminal"]["id"])
            self.assertTrue((other.root/"payloads").is_dir())
        finally:original.unlink();owned.rename(original)

    def test_retirement_requires_exact_tree_and_foreign_helper_lease(self):
        self.control.install();preview=self.control.call("runtime.retire",{"preview":True})
        receipt=preview["receipt"];id=receipt["selectedPayloadId"]
        self.assertEqual(set(receipt),{"scopeHash","cleanStopped","selectedPayloadId","candidates"})
        cached=self.control.root/"payloads"/id
        held=subprocess.Popen([str(cached/"bin/localbrain-runtime"),"payload-lease"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        try:
            self.assertEqual(held.stdout.readline(),b"ready\n")
            protected=self.control.call("runtime.retire",{"preview":True})
            self.assertEqual(protected["protected"],[{"payloadId":id,"reason":"in_use"}])
            with self.assertRaises(TerminalError):self.control.call("runtime.retire",{"preview":False,"expectedReceipt":receipt,"payloadIds":[id]})
        finally:held.stdin.close();held.wait(timeout=3);held.stdout.close()
        changed=cached/"manager/status.cjs";before=changed.read_bytes();changed.write_bytes(before+b"\n")
        with self.assertRaises(TerminalError):self.control.call("runtime.retire",{"preview":False,"expectedReceipt":receipt,"payloadIds":[id]})
        changed.write_bytes(before)
        result=self.control.call("runtime.retire",{"preview":False,"expectedReceipt":receipt,"payloadIds":[id]})
        self.assertEqual(result["retired"],[id]);self.assertFalse(cached.exists())
        self.assertTrue((self.control.root/"control.lock").is_file())
        self.assertFalse((self.control.root/"selection.json").exists())

    def test_bundle_missing_does_not_block_app_less_status_and_stop(self):
        terminal=self.create()["terminal"];launcher=self.control.root/"localbrain-terminal"
        env=runtime_environment();env["LOCALBRAIN_TERMINAL_BUNDLE"]="/synthetic/removed.app/runtime";env["LOCALBRAIN_TERMINAL_RUNTIME"]="/synthetic/removed.app/helper"
        env["PATH"]="/synthetic/no-tools";env["LOCALBRAIN_TERMINAL_LAUNCHER"]="process"
        state=json.loads(subprocess.check_output([str(launcher),"list","--json"],env=env,timeout=10))
        self.assertEqual(state["terminals"][0]["pid"],terminal["pid"])
        subprocess.run([str(launcher),"service","stop","--yes","--json"],env=env,check=True,capture_output=True,timeout=20)
        self.assertFalse(self.control.list()["running"])

    def test_old_view_width_is_rejected_before_acquiring_a_lease(self):
        terminal=self.create()["terminal"]
        _,request=self.control.request("terminal.stream",{"id":terminal["id"],"unicodeVersion":"6","checkpointVersion":None})
        result=subprocess.run([str(runtime_executable()),"stream"],input=request,capture_output=True,timeout=5)
        self.assertEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout)["code"],"client_update_required")
        self.assertFalse(self.control.list()["terminals"][0]["controlled"])

    def test_source_build_mismatch_keeps_individual_and_tab_stop_available(self):
        first=self.create();second=self.create()
        source=self.root/"different-source";shutil.copytree(BUNDLE,source)
        value=json.loads((source/"manifest.json").read_text());value.pop("payloadId")
        value["provenance"]["inputSha256"]="a"*64
        import hashlib
        value["payloadId"]=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
        (source/"manifest.json").write_text(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n")
        with mock.patch.dict(os.environ,{"LOCALBRAIN_TERMINAL_BUNDLE":str(source)}):
            self.assertEqual(self.control.status()["state"],"incompatible")
            with self.assertRaises(TerminalError):self.create()
            self.control.rpc("stop",{"id":first["terminal"]["id"],"force":True})
            self.control.rpc("tab",{"id":second["tabId"],"action":"stop","expected":{"generation":second["generation"],"terminals":[second["terminal"]["id"]]},"force":True})
            self.assertFalse(self.control.list()["terminals"])
