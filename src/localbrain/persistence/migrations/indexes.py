"""Effective indexes and redundant-index retirement with coverage checks."""

import sqlite3


def _index_key_columns(
    connection: sqlite3.Connection, index: str
) -> list[str]:
    return [
        row["name"]
        for row in connection.execute('PRAGMA index_xinfo("{}")'.format(index))
        if row["key"] and row["name"] is not None
    ]


def _migrate_schema_indexes(connection: sqlite3.Connection) -> None:
    redundant_indexes = (
        (
            "activity_events",
            "idx_events_session_sequence",
            ["session_id", "sequence"],
        ),
        ("local_resources", "idx_local_resources_path", ["path"]),
        (
            "checkpoint_resource_refs",
            "idx_checkpoint_resource_refs",
            ["checkpoint_id", "thread_id"],
        ),
    )
    indexes_to_drop = []
    for table, index, required_prefix in redundant_indexes:
        indexes = connection.execute(
            'PRAGMA index_list("{}")'.format(table)
        ).fetchall()
        if index not in {row["name"] for row in indexes}:
            continue
        covered = any(
            row["origin"] == "u"
            and _index_key_columns(connection, row["name"])[
                : len(required_prefix)
            ]
            == required_prefix
            for row in indexes
        )
        if not covered:
            raise RuntimeError(
                "Cannot remove {}: required UNIQUE index coverage is missing".format(
                    index
                )
            )
        indexes_to_drop.append(index)

    for index in indexes_to_drop:
        connection.execute('DROP INDEX "{}"'.format(index))

    for definition in (
        "CREATE INDEX IF NOT EXISTS idx_checkpoints_workstream_version "
        "ON checkpoints(workstream_id, version DESC)",
        "CREATE INDEX IF NOT EXISTS idx_documents_source "
        "ON context_documents(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_documents_workspace "
        "ON context_documents(workspace_id, mtime_ns DESC)",
        "CREATE INDEX IF NOT EXISTS idx_source_files_session ON source_files(session_id, path)",
    ):
        connection.execute(definition)
