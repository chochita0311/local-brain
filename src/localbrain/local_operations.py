"""One local writer boundary for ingestion, configuration and recovery."""

import fcntl
import os
import threading
from contextlib import contextmanager

_locks = {}
_guard = threading.Lock()
_held = threading.local()


class OperationBusy(RuntimeError):
    pass


@contextmanager
def operation_lock(config, purpose="operation", *, blocking=False):
    key = str(config.data_dir.resolve())
    held = getattr(_held, "paths", set())
    if key in held:
        yield
        return
    with _guard:
        lock = _locks.setdefault(key, threading.Lock())
    if not lock.acquire(blocking=blocking):
        raise OperationBusy("다른 로컬 작업이 진행 중입니다. 완료 후 다시 시도해 주세요.")
    fd = None
    try:
        config.data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(config.data_dir / "operations.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            raise OperationBusy("다른 창이나 서버에서 로컬 작업을 진행 중입니다.") from None
        _held.paths = held | {key}
        yield
    finally:
        _held.paths = held
        if fd is not None:
            os.close(fd)
        lock.release()


def operation_active(config):
    try:
        with operation_lock(config):
            return False
    except OperationBusy:
        return True
