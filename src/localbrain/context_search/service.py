"""Cancelable request lifecycle, isolated from web/Drive networking and storage."""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field

from ..config import cache_directory
from ..model_installation import generation_models, generation_runtime_missing as runtime_missing
from ..runtime_storage import private_directory
from .engine import ChatError, validate_request
from .tools import public_sources, source_catalog


ERRORS = {
    'CONTEXT_TOO_LARGE': '대화나 읽은 자료가 모델 입력 한도를 넘었습니다. 새 질문에서 폴더·파일·키워드를 좁혀 주세요.',
    'OUTPUT_TRUNCATED': '모델이 답변을 끝내지 못했습니다. 질문 범위를 줄여 다시 시도해 주세요.',
    'MODEL_ASSETS_CHANGED': '모델 파일 검증에 실패했습니다. 설정 → 검색 모델에서 설치를 확인해 주세요.',
    'INVALID_MODEL': '모델 설치를 확인해 주세요. 설정 → 검색 모델에서 다시 연결할 수 있습니다.',
    'MODEL_NOT_CACHED': '모델 원본이 없습니다. 설정 → 검색 모델에서 설치해 주세요.',
    'MODEL_BUSY': '모델 설치나 검증이 진행 중입니다. 완료한 뒤 다시 질문해 주세요.',
    'PROTOCOL': '모델의 도구 요청을 읽지 못했습니다. 질문을 구체화해 다시 시도해 주세요.',
    'BUDGET': '이번 질문의 탐색 한도에 도달했습니다. 폴더·파일·키워드를 좁혀 주세요.',
}


@dataclass
class Job:
    events: queue.Queue = field(default_factory=lambda: queue.Queue(maxsize=64))
    canceled: threading.Event = field(default_factory=threading.Event)
    completed: bool = False
    thread: threading.Thread | None = None


class ContextSearchService:
    def __init__(self, config, drive_store=None):
        self.config, self.drive_store = config, drive_store
        self._guard = threading.Lock()
        self._worker_guard = threading.Lock()
        self._process, self._model, self._responses = None, None, None
        self._job = None
        self._closed = False

    def status(self):
        sources = source_catalog(self.config, self.drive_store)
        return dict(models=generation_models(self.config), runtime_missing=runtime_missing(),
                    sources=public_sources(sources), busy=self._job is not None)

    def begin(self, value):
        key, messages = validate_request(value)
        if runtime_missing():
            raise ChatError('RUNTIME', '설정 → 검색 모델에서 로컬 모델 실행 환경을 확인해 주세요.', 409)
        if not next(m for m in generation_models(self.config) if m['key'] == key)['available']:
            raise ChatError('MODEL_MISSING', '설정 → 검색 모델에서 선택한 모델을 설치해 주세요.', 409)
        sources = source_catalog(self.config, self.drive_store)
        if not sources:
            raise ChatError('SOURCES_MISSING', 'Local Context를 연결하거나 Google Drive 폴더를 먼저 받아 주세요.', 409)
        if len(sources) > 100:
            raise ChatError('SOURCES_LIMIT', '검색 대상이100개를 넘습니다. Local Context 연결 범위를 줄여 주세요.', 409)
        payload = json.dumps(dict(model=key, messages=messages, sources=sources), ensure_ascii=False)
        if len(payload.encode('utf-8')) > 250000:
            raise ChatError('INPUT', '질문이나 연결된 자료 범위를 줄여 주세요.')
        with self._guard:
            if self._closed or self._job is not None:
                raise ChatError('BUSY', '다른 질문을 처리 중입니다. 완료하거나 중단한 뒤 시도해 주세요.', 409)
            job = self._job = Job()
            job.thread = threading.Thread(target=self._run, args=(job, key, payload), daemon=True, name='context-search-turn')
            job.thread.start()
        return job

    def _spawn(self, key):
        self._terminate_worker()
        cache = cache_directory(self.config) / 'context-search'
        for leaf in ('torch', 'kernels', 'torch-home', 'triton'):
            private_directory(cache / leaf)
        command = [sys.executable, '--context-search-worker'] if getattr(sys, 'frozen', False) else [sys.executable, '-m', 'localbrain.context_search.worker']
        env = {**os.environ, 'LOCALBRAIN_DATA_DIR': str(self.config.data_dir),
               'LOCALBRAIN_CACHE_DIR': str(cache_directory(self.config)), 'LOCALBRAIN_CHAT_MODEL': key,
               'TORCHINDUCTOR_CACHE_DIR': str(cache / 'torch'), 'PYTORCH_KERNEL_CACHE_PATH': str(cache / 'kernels'),
               'TORCH_HOME': str(cache / 'torch-home'), 'TRITON_CACHE_DIR': str(cache / 'triton'),
               'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false',
               'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1', 'HF_HUB_DISABLE_TELEMETRY': '1'}
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, encoding='utf-8', bufsize=1, env=env)
        responses = queue.Queue(maxsize=64)

        def reader():
            try:
                while True:
                    line = process.stdout.readline(131073)
                    if not line or len(line) > 131072:
                        break
                    try:
                        value = json.loads(line)
                        if isinstance(value, dict):
                            responses.put(value, timeout=1)
                    except (ValueError, queue.Full):
                        break
                    finally:
                        line, value = '', None
            finally:
                try:
                    responses.put({'type': 'error', 'code': 'MODEL_FAILED'}, timeout=1)
                except queue.Full:
                    pass
                process.stdout.close()

        with self._worker_guard:
            self._process, self._model, self._responses = process, key, responses
        threading.Thread(target=reader, daemon=True, name='context-search-output').start()
        return process, responses

    def _run(self, job, key, payload):
        try:
            with self._worker_guard:
                process, responses = self._process, self._responses
                reusable = process is not None and process.poll() is None and self._model == key
            if not reusable:
                process, responses = self._spawn(key)
            if job.canceled.is_set():
                self._terminate_worker()
                return
            process.stdin.write(payload + '\n'); process.stdin.flush()
            payload = ''
            deadline = time.monotonic() + 360
            while not job.canceled.is_set():
                if time.monotonic() > deadline:
                    raise ChatError('TIMEOUT', '모델 응답 시간이 길어 중단했습니다. 질문 범위를 줄여 다시 시도해 주세요.')
                try:
                    value = responses.get(timeout=0.25)
                except queue.Empty:
                    continue
                if value.get('type') == 'error':
                    raise ChatError(value.get('code'), ERRORS.get(value.get('code'), '로컬 모델 실행에 실패했습니다. 설치와 사용 가능한 메모리를 확인해 주세요.'))
                if value.get('type') in {'status', 'answer'}:
                    job.events.put(value)
                    if value['type'] == 'answer':
                        job.completed = True
                        return
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            if not job.canceled.is_set():
                job.events.put(dict(type='error', message=str(error) if isinstance(error, ChatError) else '모델 실행이 중단되었습니다. 다시 시도해 주세요.'))
            self._terminate_worker()
        finally:
            payload = ''

    def _terminate_worker(self):
        with self._worker_guard:
            process, self._process = self._process, None
            self._model, self._responses = None, None
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=2)
            process.stdin.close()

    def release(self, job):
        if not job.completed:
            job.canceled.set()
            self._terminate_worker()
        if job.thread:
            job.thread.join(timeout=4)
        with self._guard:
            if self._job is job:
                self._job = None
        while not job.events.empty():
            try:
                job.events.get_nowait()
            except queue.Empty:
                break

    def stop(self):
        with self._guard:
            self._closed = True
            job = self._job
        if job is not None:
            self.release(job)
        self._terminate_worker()

    def unload_idle(self):
        with self._guard:
            if self._job is None:
                self._terminate_worker()
