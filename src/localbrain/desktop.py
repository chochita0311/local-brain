"""Packaged backend entry point: one random loopback port, owned by the app."""

import json
import os
import socket
import sys
import threading


def main():
    if "--install-search-model" in sys.argv:
        from .model_setup import download_worker
        return download_worker()
    os.environ["LOCALBRAIN_EDITION"] = "desktop"
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
    if not os.environ.get("LOCALBRAIN_DESKTOP_TOKEN"):
        raise SystemExit("The backend must be launched by LocalBrain.app")
    import uvicorn
    from .main import app

    class DesktopServer(uvicorn.Server):
        async def startup(self, sockets=None):
            await super().startup(sockets=sockets)
            if self.started:
                print(json.dumps({"ready": True, "port": listener.getsockname()[1]}), flush=True)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    server = DesktopServer(uvicorn.Config(app, host="127.0.0.1", log_level="warning", access_log=False,
                                         timeout_graceful_shutdown=30, proxy_headers=False))

    @app.post("/desktop/shutdown")
    def shutdown():
        server.should_exit = True
        return {"ok": True}

    def parent_lifetime():
        # A native crash closes the pipe too, so an orphan cannot keep syncing.
        try:
            while os.read(sys.stdin.fileno(), 4096):
                pass
        except OSError:
            pass
        server.should_exit = True
    threading.Thread(target=parent_lifetime, name="desktop-owner", daemon=True).start()
    try:
        server.run(sockets=[listener])
    finally:
        listener.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
