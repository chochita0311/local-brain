"""Explicit, scoped observers for optional ingestion features.

Core ingestion has no observers by default. Application/CLI composition supplies
them around a scan or request. Observers share the caller's connection and must
not commit, open new transactions, or fetch remote content.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol


class IngestionObserver(Protocol):
    def document_is_current(self, connection, document_id, content_hash): ...
    def document_indexed(self, connection, document_id, content_hash, body): ...
    def session_is_current(self, connection, **source): ...
    def session_indexed(self, connection, *, candidates, **source): ...
    def before_owner_deleted(self, connection, *, session_id, document_id): ...
    def after_owner_deleted(self, connection, snapshot): ...
    def session_sources_pruned(self, connection, source_id, valid_paths): ...
    def empty_session_source(self, connection, source_id, source_path): ...
    def context_root_removed(self, connection, root_id): ...


_OBSERVERS = ContextVar("localbrain_ingestion_observers", default=())


@contextmanager
def observe_ingestion(observers):
    token = _OBSERVERS.set(tuple(observers))
    try:
        yield
    finally:
        _OBSERVERS.reset(token)


def document_is_current(connection, document_id, content_hash):
    return all(o.document_is_current(connection, document_id, content_hash) for o in _OBSERVERS.get())


def document_indexed(connection, document_id, content_hash, body):
    for observer in _OBSERVERS.get():
        observer.document_indexed(connection, document_id, content_hash, body)


def session_is_current(connection, **source):
    return all(o.session_is_current(connection, **source) for o in _OBSERVERS.get())


def session_indexed(connection, *, candidates, **source):
    for observer in _OBSERVERS.get():
        observer.session_indexed(connection, candidates=candidates, **source)


@contextmanager
def deleting_owner(connection, *, session_id=None, document_id=None):
    snapshots = [
        (observer, observer.before_owner_deleted(connection, session_id=session_id, document_id=document_id))
        for observer in _OBSERVERS.get()
    ]
    yield
    for observer, snapshot in snapshots:
        observer.after_owner_deleted(connection, snapshot)


def session_sources_pruned(connection, source_id, valid_paths):
    for observer in _OBSERVERS.get():
        observer.session_sources_pruned(connection, source_id, valid_paths)


def empty_session_source(connection, source_id, source_path):
    for observer in _OBSERVERS.get():
        observer.empty_session_source(connection, source_id, source_path)


def context_root_removed(connection, root_id):
    for observer in _OBSERVERS.get():
        observer.context_root_removed(connection, root_id)
