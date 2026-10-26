"""Explicit, cancellable installation of public search assets in a child process."""

import json
import os
import signal
import subprocess
import sys
import threading

from .model_installation import model_root, runtime_missing
from .preferences import PreferencesError


def download_worker():
    if os.environ.get("LOCALBRAIN_MODEL_PARENT_PIPE") == "1":
        def parent_lifetime():
            # Buffered stdin holds a Python lock across read; a daemon doing
            # that can abort interpreter shutdown after a successful download.
            try:
                while os.read(sys.stdin.fileno(), 4096):
                    pass
            except OSError:
                return
            os.kill(os.getpid(), signal.SIGTERM)
        threading.Thread(target=parent_lifetime, name="model-owner", daemon=True).start()
    from .model_installation import install_embedding
    from .config import settings
    def progress(phase):
        print(json.dumps({"phase": phase}), flush=True)
    try:
        if sys.platform == "darwin" and sys.version_info >= (3, 10):
            # This is a dedicated application worker, not import-time library
            # behavior. Keep TLS verification and use the Mac's trusted CAs.
            import truststore
            truststore.inject_into_ssl()
        install_embedding(model_root("embedding", settings.data_dir), progress=progress)
        progress("installed")
        return 0
    except Exception:
        progress("failed")
        return 1


class ModelSetupService:
    def __init__(self, config, search):
        self.config, self.search = config, search
        self._guard = threading.Lock()
        self._process = None
        self._thread = None
        self._phase = "idle"
        self._canceled = False

    def status(self):
        with self._guard:
            if self._phase == "preparing":
                state = self.search.status().get("state")
                if state in {"ready", "no-data", "partial"}:
                    self._phase = "ready"
                elif state == "failed":
                    self._phase = "index-failed"
            return {"phase": self._phase, "running": bool(self._process and self._process.poll() is None),
                    "installed": (model_root("embedding", self.config.data_dir) / "model.json").is_file(),
                    "runtime_missing": runtime_missing(), "download_bytes_approx": 1210000000}

    def start(self):
        with self._guard:
            if self._thread and self._thread.is_alive():
                return
            if runtime_missing():
                raise PreferencesError("검색 모델 실행 환경이 없습니다. local-models를 포함한 앱이나 개발 환경을 사용해 주세요.")
            command = [sys.executable, "--install-search-model"] if getattr(sys, "frozen", False) else [sys.executable, "-m", "localbrain.model_setup"]
            env = {**os.environ, "LOCALBRAIN_DATA_DIR": str(self.config.data_dir), "LOCALBRAIN_MODEL_PARENT_PIPE": "1"}
            self._process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            self._phase, self._canceled = "downloading", False
            self._thread = threading.Thread(target=self._watch, args=(self._process,), daemon=True)
            self._thread.start()

    def _watch(self, process):
        try:
            for line in process.stdout:
                try:
                    phase = json.loads(line).get("phase")
                except (ValueError, AttributeError):
                    continue
                if phase in {"downloading", "verifying", "installed", "failed"}:
                    with self._guard:
                        self._phase = phase
            code = process.wait()
            with self._guard:
                if self._canceled:
                    self._phase = "canceled"
                    return
                self._phase = "preparing" if code == 0 else "failed"
            if code == 0:
                self.search.request_prepare()
        except (OSError, ValueError):
            with self._guard:
                self._phase = "failed"
        finally:
            process.stdout.close()
            process.stdin.close()

    def cancel(self):
        with self._guard:
            self._canceled = True
            process = self._process
            if process and process.poll() is None:
                process.terminate()
            self._phase = "canceled"
        self.search.cancel()
        if process:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if self._thread:
            self._thread.join(timeout=10)

    def stop(self):
        if self._process or (self._thread and self._thread.is_alive()):
            self.cancel()


if __name__ == "__main__":
    raise SystemExit(download_worker())
