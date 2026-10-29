"""Explicit, cancellable installation of public search assets in a child process."""

import json
import os
import signal
import subprocess
import sys
import threading

from .model_installation import generation_models, generation_runtime_missing, model_root, runtime_missing
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
    from .model_installation import install_embedding, install_model
    from .config import settings
    def progress(phase):
        print(json.dumps({"phase": phase}), flush=True)
    try:
        if sys.platform == "darwin" and sys.version_info >= (3, 10):
            # This is a dedicated application worker, not import-time library
            # behavior. Keep TLS verification and use the Mac's trusted CAs.
            import truststore
            truststore.inject_into_ssl()
        key = os.environ.get('LOCALBRAIN_MODEL_KEY', 'embedding')
        if key not in {'embedding', '4b', '8b'}:
            raise ValueError('Unknown model')
        if key == 'embedding':
            install_embedding(model_root(key, settings.data_dir), progress=progress)
        else:
            progress('verifying' if next(m for m in generation_models(settings) if m['key'] == key)['available'] else 'downloading')
            install_model(key)
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
        self._active_key = 'embedding'
        self._generation_phases = {'4b': 'idle', '8b': 'idle'}

    def _set_phase(self, phase):
        if self._active_key == 'embedding':
            self._phase = phase
        else:
            self._generation_phases[self._active_key] = phase

    def status(self):
        with self._guard:
            if self._phase == "preparing":
                state = self.search.status().get("state")
                if state in {"ready", "no-data", "partial"}:
                    self._phase = "ready"
                elif state == "failed":
                    self._phase = "index-failed"
            running = bool(self._process and self._process.poll() is None)
            models = [{**model, 'phase': self._generation_phases[model['key']],
                       'running': running and self._active_key == model['key']}
                      for model in generation_models(self.config)]
            return {"phase": self._phase, "running": running, 'active_key': self._active_key,
                    "installed": (model_root("embedding", self.config.data_dir) / "model.json").is_file(),
                    "runtime_missing": runtime_missing(), "download_bytes_approx": 1210000000,
                    'generation_runtime_missing': generation_runtime_missing(),
                    'generation_models': models}

    def start(self, key='embedding'):
        if key not in {'embedding', '4b', '8b'}:
            raise PreferencesError('지원하는 모델을 선택해 주세요.')
        with self._guard:
            if self._thread and self._thread.is_alive():
                if key != self._active_key:
                    raise PreferencesError('진행 중인 모델 설치를 마치거나 중단한 뒤 시도해 주세요.')
                return
            if (runtime_missing() if key == 'embedding' else generation_runtime_missing()):
                raise PreferencesError("검색 모델 실행 환경이 없습니다. local-models를 포함한 앱이나 개발 환경을 사용해 주세요.")
            command = [sys.executable, "--install-search-model"] if getattr(sys, "frozen", False) else [sys.executable, "-m", "localbrain.model_setup"]
            env = {**os.environ, "LOCALBRAIN_DATA_DIR": str(self.config.data_dir), "LOCALBRAIN_MODEL_PARENT_PIPE": "1", 'LOCALBRAIN_MODEL_KEY': key}
            self._process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            self._active_key, self._canceled = key, False
            self._set_phase('downloading')
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
                        self._set_phase(phase)
            code = process.wait()
            with self._guard:
                if self._canceled:
                    self._set_phase('canceled')
                    return
                self._set_phase(('preparing' if self._active_key == 'embedding' else 'installed') if code == 0 else 'failed')
            if code == 0 and self._active_key == 'embedding':
                self.search.request_prepare()
        except (OSError, ValueError):
            with self._guard:
                self._set_phase('failed')
        finally:
            process.stdout.close()
            process.stdin.close()

    def cancel(self):
        with self._guard:
            self._canceled = True
            process = self._process
            if process and process.poll() is None:
                process.terminate()
            self._set_phase('canceled')
        if self._active_key == 'embedding':
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
