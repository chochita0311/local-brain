"""Public connection, initialization and transaction entrypoints."""

import sqlite3
from contextlib import contextmanager
from typing import Generator
from localbrain.foundation.config import settings
from localbrain.foundation.files import private_database
from localbrain.persistence.bootstrap import initialize_database


def connect() -> sqlite3.Connection:
    private_database(settings.database_path)
    connection = sqlite3.connect(str(settings.database_path), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


@contextmanager
def transaction(*, immediate: bool = False) -> Generator[sqlite3.Connection, None, None]:
    connection = connect()
    try:
        connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    initialize_database(connect(), settings)
