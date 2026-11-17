#!/usr/bin/env python3
"""Opt-in packaged-app checks in an owned relocated app and synthetic HOME/data/cache."""
import argparse
import hashlib
import json
import os
import plistlib
from pathlib import Path
import re
import shutil
import signal
import statistics
import socket
import subprocess
import tempfile
import time
import uuid
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def wait(test,seconds=30):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        try:
            result=test()
            if result:return result
        except (OSError,ValueError,KeyError,subprocess.SubprocessError):pass
        time.sleep(.1)
    raise RuntimeError("native QA condition timed out")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app",type=Path)
    parser.add_argument("--evidence",type=Path,required=True)
    parser.add_argument("--backend-only",action="store_true",help="Exercise packaged host/lifecycle without claiming WebView or physical input coverage")
    parser.add_argument("--skip-ime",action="store_true",help="Exercise native window/lifecycle independently; explicitly exclude the OS input-method probe")
    args=parser.parse_args()
    applications=subprocess.check_output(["/bin/ps","-axo","comm="],text=True)
    if any(line.strip().endswith("/Contents/MacOS/localbrain-desktop") for line in applications.splitlines()):
        raise SystemExit("A LocalBrain app is already running; preserve it rather than redirecting the isolated test through single-instance activation")
    if not args.backend_only:
        session=plistlib.loads(subprocess.check_output(["/usr/sbin/ioreg","-a","-n","Root","-d","1"]))
        def locked(value):
            if isinstance(value,dict):
                if any(user.get("CGSSessionScreenIsLocked") for user in value.get("IOConsoleUsers",[])):return True
                return any(locked(item) for item in value.values())
            return isinstance(value,list) and any(locked(item) for item in value)
        if locked(session):raise SystemExit("Mac screen is locked; unlock for UI/IME checks or select --backend-only without claiming that coverage")
    source=args.app.resolve();destination=args.evidence.resolve()
    if destination==ROOT or ROOT in destination.parents:
        raise SystemExit("Evidence must stay outside the repository")
    if not (source/"Contents/Resources/terminal/runtime/manifest.json").is_file():
        raise SystemExit("A built app with the public runtime is required")
    destination.mkdir(parents=True,exist_ok=True)
    evidence=Path(tempfile.mkdtemp(prefix="native-terminal-",dir=destination))
    owner=Path(tempfile.mkdtemp(prefix="lbn-",dir="/private/tmp"))
    (owner/".localbrain-native-qa").write_text("synthetic owned native validation\n")
    app=owner/"relocated app"/"LocalBrain.app"
    try:
        app.parent.mkdir();subprocess.run(["ditto",str(source),str(app)],check=True)
        rt=owner/"rt"
        for name in ("home","data","cache","development","context","claude","codex/sessions","tmp","project-a","project-b"):
            (rt/name).mkdir(parents=True,mode=0o700)
        (rt/"home/.profile").write_text("PS1='native> '\nexport PS1\n")
        shell=rt/"native-shell"
        shell.write_text("#!/bin/sh\nexport HOME='"+str(rt/"home")+"'\nexport TMPDIR='"+str(rt/"tmp")+"/'\nexec /bin/sh -l -i\n")
        shell.chmod(0o700)
        (rt/"home/.zshrc").write_text("PROMPT='native-zsh> '\nRPROMPT=''\n")
        zsh=rt/"zsh"
        zsh.write_text("#!/bin/sh\nexport HOME='"+str(rt/"home")+"'\nexec /bin/zsh \"$@\"\n")
        zsh.chmod(0o700)
        (rt/"data/settings.toml").write_text('schema_version = 1\nonboarding_completed = true\nstartup_screen = "context"\ntimezone = "UTC"\nsession_sync_enabled = false\ncontext_sync_enabled = false\n[terminal]\ncwd = '+json.dumps(str(rt/"project-a"))+'\nshell = '+json.dumps(str(shell))+'\n')
        (rt/"data/settings.toml").chmod(0o600)
        env={"PATH":"/usr/bin:/bin:/usr/sbin:/sbin","HOME":str(Path.home()),"SHELL":"/bin/sh","LANG":"en_US.UTF-8","TMPDIR":os.environ.get("TMPDIR",tempfile.gettempdir()+"/"),
             "LOCALBRAIN_DATA_DIR":str(rt/"data"),"LOCALBRAIN_CACHE_DIR":str(rt/"cache"),"LOCALBRAIN_DEVELOPMENT_DIR":str(rt/"development"),
             "LOCALBRAIN_CONTEXT_ROOT":str(rt/"context"),"LOCALBRAIN_CLAUDE_ROOT":str(rt/"claude"),"LOCALBRAIN_CODEX_ROOT":str(rt/"codex/sessions"),
             "HF_HOME":str(rt/"hub"),"HF_HUB_CACHE":str(rt/"hub/cache"),"HUGGINGFACE_HUB_CACHE":str(rt/"hub/cache"),"HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1"}
        tool=evidence/"native-control"
        subprocess.run(["swiftc","-O",str(ROOT/"scripts/qa-terminal-native-control.swift"),"-o",str(tool)],check=True,
                       env={**os.environ,"SWIFT_MODULECACHE_PATH":str(evidence/"swift-modules")})
        original=int(subprocess.check_output([str(tool),"frontmost"],text=True).strip())
    except BaseException:
        shutil.rmtree(owner)
        raise
    (evidence/"owned-runtime.txt").write_text(str(owner)+"\n")
    process=None;control_env={**os.environ,"LOCALBRAIN_QA_APP_PATH":str(app)};checks=[];base=None;token=None;clean=False
    timings={"launchSeconds":[]};presentation_order=None

    def ui(mode,*values,required=True):
        result=subprocess.run([str(tool),str(process.pid),mode,*map(str,values)],env=control_env,capture_output=True,text=True,timeout=15)
        if result.returncode:
            with (evidence/"ui-diagnostics.log").open("a") as log:log.write(mode+": "+result.stdout.strip()+" "+result.stderr.strip()+"\n")
            if required:raise RuntimeError(result.stdout.strip() or "native UI action failed")
        return result.returncode==0

    def api(path="/api/terminal",body=None):
        headers={"Authorization":"Bearer "+token,"Origin":base}
        if body is not None:headers["Content-Type"]="application/json"
        request=urllib.request.Request(base+path,None if body is None else json.dumps(body).encode(),headers=headers)
        with urllib.request.urlopen(request,timeout=20) as response:return json.load(response)

    def launch():
        nonlocal process,base,token
        started=time.monotonic()
        class OwnedApplication:
            def __init__(self,pid):
                self.pid=pid
                self.identity=self.snapshot()
                if not self.identity:raise RuntimeError("owned app identity missing")
            def snapshot(self):
                value=subprocess.run(["/bin/ps","-p",str(self.pid),"-o","lstart=,comm="],capture_output=True,text=True).stdout.strip()
                return value if value.endswith(str(app/"Contents/MacOS/localbrain-desktop")) else None
            def poll(self):return None if self.snapshot()==self.identity else 0
            def wait(self,timeout=45):
                deadline=time.monotonic()+timeout
                while self.poll() is None and time.monotonic()<deadline:time.sleep(.1)
                if self.poll() is None:raise subprocess.TimeoutExpired("owned app",timeout)
            def kill(self):
                if self.poll() is None:os.kill(self.pid,signal.SIGKILL)
        pid=int(subprocess.check_output([str(tool),"launch"],input=json.dumps(env),env=control_env,text=True,timeout=40).strip())
        process=OwnedApplication(pid)
        def child():
            if process.poll() is not None:raise RuntimeError("owned app exited before startup")
            for line in subprocess.check_output(["/bin/ps","-axo","pid=,ppid=,comm="],text=True).splitlines():
                fields=line.split(None,2)
                if len(fields)==3 and fields[1]==str(process.pid) and fields[2]==str(app/"Contents/Resources/backend/localbrain-backend"):
                    return int(fields[0])
        backend=wait(child,90)
        # This child's environment was constructed above and has no user secrets.
        raw=subprocess.check_output(["/bin/ps","eww","-p",str(backend),"-o","command="],text=True)
        token_match=re.search(r"(?:^|\s)LOCALBRAIN_DESKTOP_TOKEN=([0-9a-f-]{36})(?:\s|$)",raw)
        if not token_match:raise RuntimeError("owned backend token unavailable")
        token=token_match.group(1);del raw
        def port():
            names=subprocess.check_output(["/usr/sbin/lsof","-nP","-a","-p",str(backend),"-iTCP","-sTCP:LISTEN","-Fn"],text=True)
            match=re.search(r"^n127\.0\.0\.1:(\d+)$",names,re.M)
            return int(match.group(1)) if match else None
        base="http://127.0.0.1:"+str(wait(port,60))
        wait(lambda:api("/api/health"),90)
        if api("/api/terminal/settings?launch=true")!={"cwd":str(rt/"project-a"),"shell":str(shell)}:raise RuntimeError("unexpected native data scope")
        timings["launchSeconds"].append(round(time.monotonic()-started,3))

    scope=hashlib.sha256(str(rt/"data").encode()).hexdigest()[:10]
    service=rt/"cache"/("terminal-"+scope)

    def rpc(method,params):
        selection=json.loads((service/"selection.json").read_text());id=selection["payloadId"]
        if not re.fullmatch("[0-9a-f]{64}",id):raise RuntimeError("payload identity")
        helper=service/"payloads"/id/"bin/localbrain-runtime"
        request={"wire":1,"id":"native-qa","context":{"dataDir":str(rt/"data"),"cacheDir":str(rt/"cache"),"homeDir":str(rt/"home")},"operation":"manager.rpc","arguments":{"method":method,"params":params,"generation":None}}
        result=subprocess.run([str(helper),"control"],input=json.dumps(request).encode()+b"\n",capture_output=True,check=True,timeout=20,env=env)
        value=json.loads(result.stdout)
        if not value["ok"]:raise RuntimeError("native manager control failed")
        return value["result"]

    def count_ready(count, controlled=False):
        state=api()
        return state if len(state["terminals"])==count and (not controlled or all(t["controlled"] for t in state["terminals"])) else None

    def same(state,expected):
        return state["generation"]==expected["generation"] and sorted((t["id"],t["pid"]) for t in state["terminals"])==sorted((t["id"],t["pid"]) for t in expected["terminals"])

    try:
        subprocess.run(["codesign","--verify","--deep","--strict",str(app)],check=True,capture_output=True)
        launch();checks.append("relocated signed packaged backend starts in synthetic scope")
        try:urllib.request.urlopen(base+"/api/terminal",timeout=5);raise RuntimeError("native HTTP admitted missing credential")
        except urllib.error.HTTPError as error:
            if error.code!=401:raise
        checks.append("native HTTP rejects missing per-launch credential")
        if service.exists():raise RuntimeError("page startup prepared terminal runtime")
        if args.backend_only:
            def create(cwd,tab=None):
                body={"key":"native-"+uuid.uuid4().hex,"cwd":str(cwd),"shell":str(shell),"cols":80,"rows":24}
                if tab:body.update(tabId=tab,direction="right")
                api("/api/terminal/terminals",body)
                return api()
            for _ in range(2):
                started=time.monotonic()
                state=create(rt/"project-a");terminal=state["terminals"][0]
                timings.setdefault("createSeconds",[]).append(round(time.monotonic()-started,3))
                api("/api/terminal/terminals/"+terminal["id"]+"/stop",{"force":True,"expected":{"generation":state["generation"],"terminals":[terminal["id"]]}})
                wait(lambda:not api()["terminals"])
            state=create(rt/"project-a");tab=state["tabs"][0]["id"]
            for _ in range(3):create(rt/"project-a",tab)
            create(rt/"project-a");state=create(rt/"project-b")
            if sorted(len(t["terminals"]) for t in state["tabs"])!=[1,1,4]:raise RuntimeError("native API group/tab/pane structure")
            samples=[]
            for _ in range(20):
                started=time.monotonic();api();samples.append((time.monotonic()-started)*1000)
            timings["sixTerminalListMs"]={"samples":len(samples),"median":round(statistics.median(samples),2),"p95":round(sorted(samples)[18],2)}
            checks.append("packaged native API cold offline create, repeated last-stop/recreate and grouped tabs/four panes; no UI claim")
            from websockets.sync.client import connect
            from websockets.exceptions import InvalidStatus
            url=base.replace("http:","ws:")+"/api/terminal/terminals/"+state["terminals"][0]["id"]+"/stream?unicode=11&checkpoint=xterm6-v3"
            try:
                with connect(url,origin=base,open_timeout=10):pass
                raise RuntimeError("native WS admitted missing credential")
            except InvalidStatus:pass
            with connect(url,origin=base,additional_headers={"Cookie":"localbrain-desktop="+token},open_timeout=10) as connection:
                frame=json.loads(connection.recv(timeout=15))
                if frame["type"]=="error":raise RuntimeError("authenticated native WS failed")
            checks.append("actual packaged native WS rejects missing credential and accepts per-launch cookie with exact Origin")
        else:
            ui("screenshot",evidence/"startup-native.png",required=False)
            dump=subprocess.run([str(tool),str(process.pid),"dump"],env=control_env,capture_output=True,text=True)
            (evidence/"startup-ax.json").write_text(dump.stdout)
            wait(lambda:ui("press","Terminal",required=False),30)
            wait(lambda:ui("enabled","새 터미널 탭",required=False),30)
            if service.exists():raise RuntimeError("Terminal navigation prepared runtime")
            ui("press","새 터미널 탭");state=wait(lambda:count_ready(1))
            wait(lambda:ui("has","입력 가능",required=False))
            checks.append("actual Tauri WebView cold New prepares offline and connects authenticated WS")
            if not args.skip_ime:
                ui("ime");terminal=state["terminals"][0]
                wait(lambda:"LB_IME_한글" in rpc("read",{"id":terminal["id"],"after":-1})["data"],15)
                checks.append("real enabled macOS Korean IME key sequence reaches PTY as 한글")
            title_before=api()
            program_command="printf '\\033]133;C\\007\\033]0;\\342\\240\\213 Native Program\\007'; sleep 3; printf '\\033]0;\\342\\240\\231 Native Program\\007'; sleep 3; printf '\\033]0;Native Program\\007'; sleep 2; printf '\\033]133;D;0\\007\\033]133;A\\007'"
            (rt/"project-a/program-title-qa.sh").write_text(program_command+"\n",encoding="utf-8")
            (evidence/"program-title-command.sh").write_text(program_command+"\n",encoding="utf-8")
            ui("type", "sh program-title-qa.sh")
            ui("enter")
            wait(lambda:api()["terminals"][0]["name"]=="⠋ Native Program")
            wait(lambda:ui("has","Native Program",required=False))
            ui("screenshot",evidence/"program-title-native-first.png")
            wait(lambda:api()["terminals"][0]["name"]=="⠙ Native Program")
            ui("screenshot",evidence/"program-title-native-next.png")
            wait(lambda:(term:=api()["terminals"][0])["name"]=="Native Program" and term["activity"]["state"]=="running")
            ui("screenshot",evidence/"program-title-native-cleared.png")
            wait(lambda:api()["terminals"][0]["activity"]["state"]=="prompt")
            title_after=api()
            if not same(title_after,title_before) or title_after["tabs"][0]["name"]!=title_before["tabs"][0]["name"]:
                raise RuntimeError("program title changed tab identity, alias or execution")
            checks.append("actual WebView renders changing/removing program braille separately from the current check and shell-running description, preserving the tab alias and PTY")
            ui("pane-menu");ui("backtab");ui("backtab");ui("backtab")
            ui("space");ui("down");ui("down");ui("enter")
            wait(lambda:api()["tabs"][0]["hidden"])
            wait(lambda:ui("enabled","project-a 백그라운드 탭 다시 열기",required=False))
            ui("screenshot",evidence/"background-inline-native.png")
            if not same(api(),title_after):raise RuntimeError("native Hide changed execution")
            ui("press","project-a 백그라운드 탭 다시 열기")
            wait(lambda:not api()["tabs"][0]["hidden"])
            wait(lambda:ui("has","입력 가능",required=False))
            if not same(api(),title_after):raise RuntimeError("native inline restore changed execution")
            checks.append("actual keyboard Hide exposes an inline Background row; native restore returns the exact tab and PTY without a modal")
            ui("press","이 터미널 닫기 및 종료")
            wait(lambda:not api()["terminals"])
            wait(lambda:ui("enabled","새 터미널 탭",required=False));ui("press","새 터미널 탭")
            wait(lambda:len(api()["terminals"])==1)
            wait(lambda:ui("has","입력 가능",required=False))
            checks.append("actual direct last-pane close leaves New enabled for recreation without a confirmation")
            for count in (2,3,4):
                split_label="오른쪽 분할" if count==2 else "분할 추가"
                wait(lambda:ui("enabled",split_label,required=False))
                ui("press",split_label);wait(lambda:len(api()["terminals"])==count)
            if ui("enabled","분할 추가",required=False):raise RuntimeError("native split limit not applied")
            wait(lambda:ui("enabled","새 터미널 탭",required=False))
            ui("press","새 터미널 탭");wait(lambda:len(api()["terminals"])==5)
            wait(lambda:ui("enabled","작업공간 추가",required=False))
            ui("press","작업공간 추가")
            ui("screenshot",evidence/"workspace-dialog-native.png",required=False)
            # WKWebView's modal can disappear from this external AX child walk.
            # Exercise its actual focused form with ASCII keyboard input instead.
            ui("type","Project B");ui("tab");ui("type",rt/"project-b");ui("enter")
            wait(lambda:any(item["name"]=="Project B" and item["cwd"]==str(rt/"project-b") for item in api()["workspaces"]["items"]))
            if len(api()["terminals"])!=5:raise RuntimeError("creating an empty workspace started a terminal")
            wait(lambda:ui("enabled","새 터미널 탭",required=False));ui("press","새 터미널 탭")
            state=wait(lambda:count_ready(6))
            if len({tab["cwd"] for tab in state["tabs"]})!=2 or sorted(len(tab["terminals"]) for tab in state["tabs"])!=[1,1,4]:raise RuntimeError("native group/tab/pane structure")
            checks.append("native named empty workspace creation, optional folder, multiple tabs and maximum four panes")
            move_before=api()
            moving_tab=next(tab for tab in move_before["tabs"] if tab["cwd"]==str(rt/"project-b"))
            original_space=moving_tab["workspaceId"]
            first_space=next(item["id"] for item in move_before["workspaces"]["items"] if item["name"]=="project-a")
            # From terminal input: Shift+Escape reaches the pane menu; three
            # reverse Tabs pass down/right split controls to the tab menu.
            ui("pane-menu");ui("backtab");ui("backtab");ui("backtab")
            ui("space");ui("up");ui("enter")
            ui("screenshot",evidence/"workspace-move-native.png",required=False)
            ui("up");ui("enter")
            wait(lambda:any(tab["id"]==moving_tab["id"] and tab["workspaceId"]==first_space for tab in api()["tabs"]))
            if not same(api(),move_before):raise RuntimeError("native menu move changed execution")
            # From terminal input: Shift+Escape reaches the pane menu; three
            # reverse Tabs pass down/right split controls to the tab menu.
            ui("pane-menu");ui("backtab");ui("backtab");ui("backtab")
            ui("space");ui("up");ui("enter")
            ui("down");ui("enter")
            wait(lambda:any(tab["id"]==moving_tab["id"] and tab["workspaceId"]==original_space for tab in api()["tabs"]))
            if not same(api(),move_before):raise RuntimeError("native menu return changed execution")
            checks.append("actual WebView same-panel workspace move uses checked-current keyboard navigation and retains exact generation/PTY PIDs in both directions")
            ui("press","project-a 작업공간");ui("press","project-a","","AXRadioButton")
            if not ui("screenshot",evidence/"terminal-native.png",required=False):checks.append("owned screenshot unavailable; AX/PTY checks remain separate")
        starting=api();target=starting["tabs"][1]
        created=api("/api/terminal/terminals",{"key":"native-zsh-"+uuid.uuid4().hex,"workspaceId":target["workspaceId"],"tabId":target["id"],"direction":"right","cwd":str(rt/"project-b"),"shell":str(zsh)})
        zsh_id=created["terminal"]["id"]
        def integrated():return next((term for term in api()["terminals"] if term["id"]==zsh_id),None)
        wait(lambda:(term:=integrated()) and term.get("activity",{}).get("state")=="prompt")
        if not args.backend_only:
            wait(lambda:ui("has","프롬프트 대기",required=False))
            ui("screenshot",evidence/"zsh-prompt-ring-native.png")
        claim=rpc("claim",{"id":zsh_id,"unicodeVersion":"11","checkpointVersion":"xterm6-v3"})
        if not claim["writable"]:raise RuntimeError("owned zsh input unexpectedly controlled")
        rpc("input",{"id":zsh_id,"lease":claim["lease"],"data":"sleep 1; false\r"})
        wait(lambda:(term:=integrated()) and term["activity"]["state"]=="running")
        wait(lambda:(term:=integrated()) and term["activity"]["state"]=="prompt" and term["activity"]["exitCode"]==1)
        after=api()
        if after["generation"]!=starting["generation"] or any((term["id"],term["pid"]) not in {(current["id"],current["pid"]) for current in after["terminals"]} for term in starting["terminals"]):
            raise RuntimeError("zsh split changed another execution")
        checks.append("packaged new zsh startup shim reports prompt/running/nonzero result in a different-folder split while preserving existing processes; zsh remains for Quit/relaunch checks")
        before=api()
        workspace_identity=[(item["id"],item["name"],item["cwd"]) for item in before["workspaces"]["items"]]
        if before["tabs"][0]["cwd"]!=before["tabs"][1]["cwd"]:raise RuntimeError("native reorder fixture folder mismatch")
        presentation_order=[before["tabs"][1]["id"],before["tabs"][0]["id"],before["tabs"][2]["id"]]
        api("/api/terminal/view-order",{"generation":before["generation"],"order":presentation_order})
        ordered=api()
        if ordered["presentation"]["order"]!=presentation_order or not same(ordered,before):raise RuntimeError("native presentation order was not confirmed without execution changes")
        checks.append("packaged host saves same-workspace presentation order without changing execution")
        if not args.backend_only:
            ui("escape")
            ui("screenshot",evidence/"terminal-focus-active.png")
            subprocess.run([str(tool),str(original),"restore"],check=True,capture_output=True)
            time.sleep(.4)
            ui("screenshot-inactive",evidence/"terminal-focus-inactive.png")
            subprocess.run(["open","-a",str(app)],check=True)
            ui("screenshot",evidence/"terminal-focus-restored.png")
            if not same(api(),before):raise RuntimeError("window focus changed work")
            checks.append("actual active/inactive/restored window screenshots preserve selection and exact work; visual emphasis is evaluated separately")
            ui("minimize");time.sleep(.3)
            if not same(api(),before):raise RuntimeError("minimize changed work")
            subprocess.run(["open","-a",str(app)],check=True);wait(lambda:ui("visible",required=False))
            ui("close");time.sleep(.3)
            if process.poll() is not None or not same(api(),before):raise RuntimeError("window close changed work")
            subprocess.run(["open","-a",str(app)],check=True);wait(lambda:ui("visible",required=False))
            checks.append("native minimize, red close/hide and Dock reopen preserve generation and PTY PIDs")
        ui("quit");process.wait(timeout=45)
        launcher=service/"localbrain-terminal"
        standalone=json.loads(subprocess.check_output([str(launcher),"list","--json"],env=env,timeout=15))
        if not same(standalone,before):raise RuntimeError("normal app Quit ended work")
        removed=app.with_name("Removed-source.app");app.rename(removed)
        standalone=json.loads(subprocess.check_output([str(launcher),"list","--json"],env=env,timeout=15))
        if not same(standalone,before):raise RuntimeError("app removal ended work")
        removed.rename(app)
        checks.append("normal Quit and source-app removal preserve app-less cached management and exact work")
        manager=standalone["service"]["pid"]
        expected_birth=json.loads((service/"identity.json").read_text())["born"]
        def manager_birth():
            stamp=subprocess.run(["/bin/ps","-p",str(manager),"-o","lstart="],capture_output=True,text=True,env={**env,"LC_ALL":"C","TZ":"UTC"})
            return " ".join(stamp.stdout.split()) if stamp.returncode==0 else None
        if manager_birth()!=expected_birth:raise RuntimeError("owned manager identity changed before suspension")
        os.kill(manager,signal.SIGSTOP)
        try:time.sleep(.5)
        finally:
            if manager_birth()==expected_birth:os.kill(manager,signal.SIGCONT)
            else:raise RuntimeError("owned manager identity changed while suspended")
        launch();wait(lambda:same(api(),before))
        if [(item["id"],item["name"],item["cwd"]) for item in api()["workspaces"]["items"]]!=workspace_identity:
            raise RuntimeError("workspace identity changed on app relaunch")
        if presentation_order is not None and api()["presentation"]["order"]!=presentation_order:
            raise RuntimeError("presentation order did not survive host relaunch on its new port")
        if not args.backend_only:
            wait(lambda:ui("press","Terminal",required=False))
            wait(lambda:ui("has","입력 가능",required=False))
        checks.append("process suspension/resume and app relaunch reconnect same generation/PIDs without replay; not physical Mac sleep")
        state=api();api("/api/terminal/service/stop",{"force":True,"expected":{"generation":state["generation"],"terminals":[t["id"] for t in state["terminals"]]}})
        stopped=api()
        if stopped["running"]:raise RuntimeError("explicit native stop failed")
        checks.append("explicit exact-scope native stop ends test work and manager")
        if [(item["id"],item["name"],item["cwd"]) for item in stopped["workspaces"]["items"]]!=workspace_identity or any(item["tabs"] for item in stopped["workspaces"]["items"]):
            raise RuntimeError("empty workspace metadata lost after explicit service stop")
        checks.append("workspace names/defaults/IDs survive app relaunch and remain empty after service stop without process replay")
        clean=True
        (evidence/"result.json").write_text(json.dumps({"result":"PASS","backendOnly":args.backend_only,"imeProbe":not args.backend_only and not args.skip_ime,"checks":checks,"timings":timings,"timingScope":"synthetic packaged host under current OS state; not active WebView typing, comparative performance or a resource budget","appPayload":json.loads((app/"Contents/Resources/terminal/runtime/manifest.json").read_text())["payloadId"],"physicalSleep":False,"voiceOver":False},ensure_ascii=False,indent=2))
        print(json.dumps({"result":"PASS","checks":len(checks),"evidence":str(evidence)}))
    except BaseException as error:
        (evidence/"result.json").write_text(json.dumps({"result":"FAIL","checks":checks,"error":str(error)},ensure_ascii=False,indent=2))
        if process and process.poll() is None:
            try:
                state=api()
                output=[{"id":terminal["id"],"data":rpc("read",{"id":terminal["id"],"after":-1})["data"][-8000:]} for terminal in state["terminals"]]
                (evidence/"synthetic-terminal-output.json").write_text(json.dumps(output,ensure_ascii=False,indent=2))
            except (OSError,ValueError,KeyError,subprocess.SubprocessError):pass
            ui("screenshot",evidence/"failure-native.png",required=False)
            dump=subprocess.run([str(tool),str(process.pid),"dump"],env=control_env,capture_output=True,text=True)
            (evidence/"failure-ax.json").write_text(dump.stdout)
            diagnose=subprocess.run([str(tool),str(process.pid),"diagnose"],env=control_env,capture_output=True,text=True)
            (evidence/"native-diagnosis.json").write_text(diagnose.stdout)
            subprocess.run(["/usr/bin/sample",str(process.pid),"1","1","-file",str(evidence/"app.sample")],capture_output=True,timeout=15)
        raise
    finally:
        if process and process.poll() is None:
            try:ui("quit",required=False)
            except (OSError,subprocess.SubprocessError):pass
            try:process.wait(timeout=45)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        launcher=service/"localbrain-terminal"
        if launcher.exists():
            try:
                stopped=subprocess.run([str(launcher),"service","stop","--yes","--force","--json"],env=env,capture_output=True,timeout=25)
                clean=stopped.returncode==0
            except (OSError,subprocess.SubprocessError):clean=False
        if original:subprocess.run([str(tool),str(original),"restore"],capture_output=True)
        if (not process or process.poll() is not None) and (clean or not service.exists()):
            shutil.rmtree(owner)
            (evidence/"owned-runtime.txt").unlink()
        else:print(json.dumps({"retainedRuntime":str(owner),"reason":"owned terminal shutdown needs recovery"}))


if __name__=="__main__":main()
