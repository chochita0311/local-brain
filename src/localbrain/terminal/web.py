"""Same-origin web bridge; PTYs remain owned by the independent manager."""
import asyncio
import contextlib
import json
from pathlib import Path

from fastapi import HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from .runtime import TerminalError, TerminalService
from .settings import launch_parameters, read_launch_settings, save_launch_settings
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
            if error.code in {"unavailable", "setup_required", "start_failed"}:
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
        result["dependencies"] = service.dependencies()
        result["defaultCwd"] = str(Path.home())
        return result

    @app.post("/api/terminal/install")
    async def install(request: Request):
        await _body(request)
        return await perform(control().install)

    @app.get("/api/terminal/settings")
    async def launch_settings(launch: bool = False):
        return await perform(launch_parameters if launch else read_launch_settings, config)

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
        allowed = {"key", "cwd", "shell", "cols", "rows", "tabId", "direction"}
        if set(body) - allowed:
            raise HTTPException(400, "알 수 없는 생성 옵션입니다.")
        return await perform(control().create, body)

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
        return await perform(control().rpc, "stop", {"id": terminal_id, "force": body.get("force", False)})

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
        if not _origin_allowed(websocket):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        service = control()
        lease = {"token": None}
        ack = asyncio.Event()
        sent = {"seq": None}
        send_lock = asyncio.Lock()

        async def send(value):
            async with send_lock:
                await websocket.send_json(value)

        async def claim(takeover=False):
            result = await run_in_threadpool(service.rpc, "claim", {
                "id": terminal_id, "takeover": takeover,
                "unicodeVersion": websocket.query_params.get("unicode", "6"),
                "checkpointVersion": websocket.query_params.get("checkpoint"),
            })
            lease["token"] = result["lease"]
            await send({"type": "control", "writable": result["writable"]})

        async def output():
            after = -1
            while True:
                token = lease["token"]
                frame = await service.read(terminal_id, after, token, websocket.query_params.get("checkpoint"))
                if token != lease["token"]:
                    frame.pop("writable", None)
                ack.clear()
                sent["seq"] = frame["seq"]
                await send({"type": "output", **frame})
                await asyncio.wait_for(ack.wait(), timeout=15)
                after = frame["seq"]
                if frame["terminal"]["state"] != "running":
                    return

        async def receive():
            while True:
                raw = await websocket.receive_text()
                if len(raw.encode()) > 128 * 1024:
                    raise TerminalError("invalid", "입력이 너무 큽니다.")
                message = json.loads(raw)
                if not isinstance(message, dict):
                    raise TerminalError("invalid", "입력 형식이 올바르지 않습니다.")
                kind = message.get("type")
                if kind == "ack":
                    if type(message.get("seq")) is int and message["seq"] == sent["seq"]:
                        ack.set()
                    continue
                if kind == "claim":
                    await claim(True)
                    continue
                if kind not in {"input", "binary", "resize"}:
                    raise TerminalError("invalid", "입력 형식이 올바르지 않습니다.")
                params = {"id": terminal_id, "lease": lease["token"]}
                if kind in {"input", "binary"}:
                    params["data"] = message.get("data")
                else:
                    params.update(cols=message.get("cols"), rows=message.get("rows"))
                try:
                    await run_in_threadpool(service.rpc, kind, params)
                except TerminalError as error:
                    if error.code == "not_owner":
                        lease["token"] = None
                        await send({"type": "control", "writable": False})
                    else:
                        await send({"type": "error", "code": error.code, "message": str(error)})
                        if error.code in {"input_busy", "input_failed"}:
                            # Later paste fragments must not continue after a hole.
                            await websocket.close(code=1013)
                            return

        tasks = []
        try:
            try:
                await claim()
            except TerminalError as error:
                if error.code != "exited":
                    raise
                await send({"type": "control", "writable": False})
            tasks = [asyncio.create_task(output()), asyncio.create_task(receive())]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
        except (TerminalError, ValueError, asyncio.TimeoutError) as error:
            with contextlib.suppress(RuntimeError, WebSocketDisconnect):
                await send({"type": "error", "message": str(error) if isinstance(error, TerminalError) else "연결이 끊겼습니다."})
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            if lease["token"]:
                with contextlib.suppress(TerminalError):
                    await run_in_threadpool(service.rpc, "release", {"id": terminal_id, "lease": lease["token"]})
            with contextlib.suppress(RuntimeError):
                await websocket.close()
