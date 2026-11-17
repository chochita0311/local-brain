"""Same-origin web bridge; PTYs remain owned by the independent manager."""
import asyncio
import contextlib
import json
import os
from pathlib import Path

from fastapi import HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from .core import TerminalError, TerminalService
from .presentation import PresentationError, load_order, save_order
from .settings import launch_parameters, read_launch_settings, save_launch_settings
from .workspaces import read_workspaces, change_workspaces, WorkspaceError
from .shell_integration import integrated_shell
from localbrain.foundation.preferences import PreferencesError


def _origin_allowed(connection):
    scheme = {"ws": "http", "wss": "https"}.get(connection.url.scheme, connection.url.scheme)
    return (connection.url.hostname in {"localhost", "127.0.0.1", "::1"} and
            connection.headers.get("origin") == scheme + "://" + connection.url.netloc)


async def _body(request):
    if not _origin_allowed(request):
        raise HTTPException(403, "같은 LocalBrain 화면에서 요청해 주세요.")
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
        raise HTTPException(415, "JSON 요청이 필요합니다.")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > 128 * 1024:
            raise HTTPException(413, "요청이 너무 큽니다.")
    try:
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (ValueError, UnicodeError) as error:
        raise HTTPException(400, "요청 형식이 올바르지 않습니다.") from error


def _expected(body):
    value = body.get("expected")
    if (not isinstance(value, dict) or set(value) != {"generation", "terminals"}
            or not isinstance(value["generation"], (str, type(None)))
            or not isinstance(value["terminals"], list) or len(value["terminals"]) > 32
            or any(not isinstance(item, str) for item in value["terminals"])):
        raise HTTPException(400, "종료할 범위를 다시 확인해 주세요.")
    return value


def install_routes(app, templates, config):
    app.state.terminal_factory = lambda: TerminalService(config)

    def control():
        return app.state.terminal_factory()

    async def perform(call, *args, **kwargs):
        try:
            return await run_in_threadpool(call, *args, **kwargs)
        except PreferencesError as error:
            return JSONResponse({"detail": str(error)}, status_code=409)
        except OSError:
            return JSONResponse({"detail": "터미널 작업을 완료하지 못했습니다. 다시 시도해 주세요."}, status_code=503)
        except TerminalError as error:
            status = 409 if error.code in {"busy", "stopping", "not_owner", "conflict"} else 400
            if error.code in {"unavailable", "setup_required", "start_failed", "protocol", "disconnected"}:
                status = 503
            return JSONResponse({"error": {"code": error.code, "message": str(error)}}, status_code=status)

    @app.get("/terminal", response_class=HTMLResponse)
    async def terminal_page(request: Request):
        return templates.TemplateResponse(request, "terminal.html", {"active_page": "terminal"})

    @app.get("/api/terminal")
    async def terminal_state():
        service = control()
        result = await perform(service.list)
        if isinstance(result, JSONResponse):
            return result
        result["dependencies"] = await run_in_threadpool(service.dependencies)
        result["defaultCwd"] = str(Path.home())
        result["workspaces"] = await run_in_threadpool(read_workspaces, config, result)
        membership = {tab: item["id"] for item in result["workspaces"]["items"] for tab in item["tabs"]}
        result["tabs"] = [{**tab, "workspaceId": membership.get(tab["id"])} for tab in result["tabs"]]
        result["presentation"] = (await run_in_threadpool(load_order, service.root,
                                                         result["generation"], result["tabs"])
                                  if result.get("generation") and result["tabs"] else {"order": []})
        return result

    @app.post("/api/terminal/workspaces/{action}")
    async def workspace_action(action: str, request: Request):
        body = await _body(request)
        allowed = {"create": {"name", "cwd"}, "update": {"id", "name", "cwd"},
                   "remove": {"id"}, "move": {"id", "tabId", "generation"}, "reconcile": {"generation"}}
        if action not in allowed or set(body) != allowed[action]:
            raise HTTPException(400, "작업공간 요청을 확인해 주세요.")
        if "name" in body and (not isinstance(body["name"], str) or not body["name"].strip() or len(body["name"]) > 120):
            raise HTTPException(400, "작업공간 이름은 1~120자로 입력해 주세요.")
        if "cwd" in body:
            if not isinstance(body["cwd"], str):
                raise HTTPException(400, "기본 폴더를 확인해 주세요.")
            if body["cwd"]:
                paths = await perform(launch_parameters, config, cwd=body["cwd"])
                if isinstance(paths, JSONResponse):
                    return paths
                body["cwd"] = paths["cwd"]
        service = control()
        return await perform(change_workspaces, config, service.list, action, body)

    @app.post("/api/terminal/view-order")
    async def view_order(request: Request):
        body = await _body(request)
        if set(body) != {"generation", "order"} or not isinstance(body["generation"], str):
            raise HTTPException(400, "탭 이동 요청을 확인해 주세요.")
        service = control()
        state = await perform(service.list)
        if isinstance(state, JSONResponse):
            return state
        if not state.get("running") or body["generation"] != state.get("generation"):
            raise HTTPException(409, "터미널 서비스가 바뀌었습니다. 다시 이동해 주세요.")
        spaces = await run_in_threadpool(read_workspaces, config, state)
        membership = {tab: item["id"] for item in spaces["items"] for tab in item["tabs"]}
        tabs = [{**tab, "workspaceId": membership.get(tab["id"])} for tab in state["tabs"]]
        try:
            return await run_in_threadpool(save_order, service.root, state["generation"], tabs, body["order"])
        except PresentationError as error:
            raise HTTPException(409, str(error)) from error
        except (OSError, ValueError) as error:
            raise HTTPException(503, "탭 순서를 저장하지 못했습니다. 다시 이동해 주세요.") from error

    @app.post("/api/terminal/install")
    async def install(request: Request):
        await _body(request)
        return await perform(control().install)

    @app.get("/api/terminal/settings")
    async def launch_settings(launch: bool = False, cwd: str | None = None):
        if launch:
            return await perform(launch_parameters, config, cwd=cwd)
        return await perform(read_launch_settings, config)

    @app.post("/api/terminal/settings")
    async def update_launch_settings(request: Request):
        value = await _body(request)
        if set(value) != {"cwd", "shell", "revision"} or not isinstance(value["revision"], str):
            raise HTTPException(400, "터미널 설정 요청을 확인해 주세요.")
        return await perform(save_launch_settings, config, value["cwd"], value["shell"], value["revision"])

    @app.post("/api/terminal/service/{action}")
    async def service_action(action: str, request: Request):
        body = await _body(request)
        if action not in {"start", "stop", "restart"}:
            raise HTTPException(404)
        if type(body.get("force", False)) is not bool:
            raise HTTPException(400, "강제 종료 옵션을 확인해 주세요.")
        service = control()
        method = getattr(service, action)
        options = {"force": body.get("force", False), "expected": _expected(body)} if action != "start" else {}
        return await perform(method, **options)

    @app.post("/api/terminal/terminals")
    async def create(request: Request):
        body = await _body(request)
        allowed = {"key", "cwd", "shell", "cols", "rows", "tabId", "direction", "workspaceId"}
        if set(body) - allowed:
            raise HTTPException(400, "알 수 없는 생성 옵션입니다.")
        service = control()
        workspace_id = body.pop("workspaceId", None)
        if workspace_id is not None:
            state = await perform(service.list)
            if isinstance(state, JSONResponse):
                return state
            spaces = await run_in_threadpool(read_workspaces, config, state)
            item = next((item for item in spaces["items"] if item["id"] == workspace_id), None)
            if not item or (body.get("tabId") and body["tabId"] not in item["tabs"]):
                raise HTTPException(409, "작업공간의 탭 목록이 바뀌었습니다. 다시 확인해 주세요.")
        requested_shell = body.get("shell", "")
        if requested_shell == "":
            requested_shell = os.environ.get("SHELL") or "/bin/zsh"
        shell = await perform(integrated_shell, config, requested_shell)
        if isinstance(shell, JSONResponse):
            return shell
        body["shell"] = shell
        result = await perform(service.create, body)
        if isinstance(result, JSONResponse):
            return result
        if result.get("tabId"):
            try:
                result["workspaces"] = await run_in_threadpool(change_workspaces, config, service.list, "attach",
                    {"id": workspace_id, "tabId": result["tabId"], "generation": result.get("generation")})
            except (OSError, ValueError, TerminalError) as error:
                result["workspaceError"] = "터미널은 열렸지만 작업공간을 저장하지 못했습니다. 목록을 다시 확인해 주세요."
        return result

    @app.post("/api/terminal/stop")
    async def stop_all(request: Request):
        body = await _body(request)
        if type(body.get("force", False)) is not bool:
            raise HTTPException(400)
        return await perform(control().rpc, "stop", {"all": True, "force": body.get("force", False), "expected": _expected(body)})

    @app.post("/api/terminal/terminals/{terminal_id}/stop")
    async def stop(terminal_id: str, request: Request):
        body = await _body(request)
        if type(body.get("force", False)) is not bool:
            raise HTTPException(400)
        generation = body.get("generation")
        if generation is not None and (not isinstance(generation, str) or len(generation) != 32
                                       or any(char not in "0123456789abcdef" for char in generation)):
            raise HTTPException(400, "터미널 서비스를 다시 확인해 주세요.")
        options = {"generation": generation} if generation is not None else {}
        return await perform(control().rpc, "stop", {"id": terminal_id, "force": body.get("force", False)}, **options)

    @app.post("/api/terminal/tabs/{tab_id}/{action}")
    async def tab_action(tab_id: str, action: str, request: Request):
        body = await _body(request)
        if action not in {"hide", "show", "rename", "stop"}:
            raise HTTPException(404)
        params = {"id": tab_id, "action": action, "name": body.get("name")}
        if action == "stop":
            params["expected"] = _expected(body)
        return await perform(control().rpc, "tab", params)

    @app.websocket("/api/terminal/terminals/{terminal_id}/stream")
    async def stream(websocket: WebSocket, terminal_id: str):
        from localbrain.app import edition
        if (not _origin_allowed(websocket) or (edition.DESKTOP and
                (websocket.url.hostname != "127.0.0.1" or not edition.desktop_authorized(websocket)))):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        process = None
        tasks = []
        failed_input = False

        async def output():
            nonlocal failed_input
            while True:
                raw = await process.stdout.readline()
                if not raw:
                    code = await process.wait()
                    if code == 75:
                        failed_input = True
                        await websocket.send_json({"type": "error", "code": "input_failed", "message": "입력이 일부만 전달되었을 수 있습니다. 다시 연결한 뒤 Ctrl+C로 입력을 취소하고 확인해 주세요."})
                    elif code:
                        raise TerminalError("unavailable", "터미널 연결이 끊겼습니다.")
                    return
                if len(raw) > 2 * 1024 * 1024 + 1 or not raw.endswith(b"\n"):
                    raise TerminalError("protocol", "출력 응답을 확인할 수 없습니다.")
                frame = json.loads(raw)
                if not isinstance(frame, dict) or frame.get("type") not in {"output", "control", "error"}:
                    raise TerminalError("protocol", "출력 응답을 확인할 수 없습니다.")
                await websocket.send_json(frame)
                if frame.get("code") in {"input_busy", "input_failed"}:
                    failed_input = True
                    return

        async def receive():
            while True:
                raw = (await websocket.receive_text()).encode()
                if len(raw) > 128 * 1024:
                    raise TerminalError("invalid", "입력 형식이나 크기를 확인해 주세요.")
                # This host only transports frames. Rust owns claim/read/ack/input state.
                message = json.loads(raw)
                if not isinstance(message, dict):
                    raise TerminalError("invalid", "입력 형식이 올바르지 않습니다.")
                process.stdin.write(json.dumps(message, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode() + b"\n")
                await asyncio.wait_for(process.stdin.drain(), timeout=15)

        try:
            process = await control().stream(terminal_id, websocket.query_params.get("unicode", "6"),
                                             websocket.query_params.get("checkpoint"))
            tasks = [asyncio.create_task(output()), asyncio.create_task(receive())]
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
        except (TerminalError, ValueError, OSError, asyncio.TimeoutError) as error:
            with contextlib.suppress(RuntimeError, WebSocketDisconnect):
                await websocket.send_json({"type": "error", "message": str(error) if isinstance(error, TerminalError) else "연결이 끊겼습니다."})
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            if process:
                # Abort pending pipe bytes: detach must not flush unsent paste.
                process.stdin.transport.abort()
                with contextlib.suppress(OSError, BrokenPipeError, asyncio.TimeoutError):
                    await asyncio.wait_for(process.stdin.wait_closed(), timeout=1)
                try:
                    code = await asyncio.wait_for(process.wait(), timeout=10)
                    if code == 75 and not failed_input:
                        failed_input = True
                        with contextlib.suppress(RuntimeError, WebSocketDisconnect):
                            await websocket.send_json({"type": "error", "code": "input_failed", "message": "입력이 일부만 전달되었을 수 있습니다. 다시 연결한 뒤 Ctrl+C로 입력을 취소하고 확인해 주세요."})
                except asyncio.TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        process.kill()
                    await process.wait()
            with contextlib.suppress(RuntimeError):
                await websocket.close(code=1013 if failed_input else 1000)
