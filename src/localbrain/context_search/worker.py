"""One offline model per child; requests/results exist only in pipe/RAM."""
import json
import os
import queue
import signal
import sys
import threading

from .engine import ChatError, answer, validate_request


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def main():
    requests = queue.Queue(maxsize=1)

    def read_parent():
        pending = b''
        try:
            while True:
                chunk = os.read(sys.stdin.fileno(), 65536)
                if not chunk:
                    break
                pending += chunk
                chunk = b''
                if len(pending) > 262144:
                    break
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    requests.put(json.loads(line))
                    line = b''
        except (OSError, ValueError):
            pass
        # Also interrupts model loading/generation if the owner disappeared.
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=read_parent, name='context-search-owner', daemon=True).start()
    generator = None
    while True:
        request = requests.get()
        try:
            key, history = validate_request({k: request[k] for k in ('model', 'messages')})
            if key != os.environ.get('LOCALBRAIN_CHAT_MODEL'):
                raise ChatError('INPUT', '모델 선택을 확인해 주세요.')
            if generator is None:
                emit({'type': 'status', 'phase': 'loading'})
                from ..model_installation import install_model, model_root
                root = model_root(key)
                if not (root / 'model.json').is_file():
                    install_model(key, local_only=True)
                from ..work_context_model import LocalGenerator
                generator = LocalGenerator(root, thinking=False, max_output=1024, max_seconds=90)
                generator._load()
            emit(answer(generator, request['sources'], history, emit))
        except Exception as error:
            code = error.code if isinstance(error, ChatError) else str(error)
            allowed = {'INPUT', 'PROTOCOL', 'BUDGET', 'CONTEXT_TOO_LARGE', 'OUTPUT_TRUNCATED',
                       'MODEL_NOT_CACHED', 'MODEL_ASSETS_CHANGED', 'INVALID_MODEL', 'MODEL_BUSY'}
            emit({'type': 'error', 'code': code if code in allowed else 'MODEL_FAILED'})
        finally:
            if 'history' in locals():
                history.clear()
            request.clear()
            if generator is not None:
                generator.last_output = ''


if __name__ == '__main__':
    main()
