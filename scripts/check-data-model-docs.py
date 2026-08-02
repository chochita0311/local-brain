from __future__ import annotations

import hashlib
import re
import sqlite3
import sys
from pathlib import Path

from data_model_value_registry import check_documents


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "docs/policies/project/data-model.md"
SUBJECT_ROOT = ROOT / "docs/policies/project/data-model"
SCHEMA_PATH = ROOT / "src/localbrain/schema.sql"
DB_PATH = ROOT / "src/localbrain/db.py"

SUBJECTS = {
    "source-registry-and-scans.md": (
        "sources",
        "source_files",
        "external_source_instances",
        "external_source_capabilities",
    ),
    "workspace-and-session-activity.md": (
        "workspaces",
        "sessions",
        "activity_events",
        "session_pins",
    ),
    "usage-and-cost-records.md": (
        "usage_price_snapshots",
        "usage_model_prices",
        "usage_records",
    ),
    "local-context-corpus.md": ("context_roots", "context_documents"),
    "work-organization-and-resources.md": (
        "workstreams",
        "threads",
        "workstream_links",
        "thread_links",
        "local_resources",
        "external_resources",
    ),
    "atlassian-source-memory.md": (
        "atlassian_sites",
        "atlassian_site_bindings",
        "atlassian_spaces",
        "atlassian_items",
        "atlassian_item_urls",
        "atlassian_item_remote_state",
        "atlassian_item_content",
        "atlassian_item_local_state",
        "atlassian_classifications",
        "atlassian_item_classifications",
        "atlassian_evidence_scans",
        "atlassian_item_evidence",
    ),
    "review-and-resume-continuity.md": (
        "suggestions",
        "checkpoints",
        "checkpoint_resource_refs",
    ),
    "maintenance-execution.md": ("maintenance_runs", "external_sync_runs"),
    "derived-retrieval-index.md": ("search_index",),
}

REQUIRED_TABLE_LABELS = (
    "Lifecycle:",
    "Producers:",
    "Consumers:",
    "Relations and deletion:",
    "Recovery:",
    "DDL ownership:",
)

REQUIRED_SEMANTIC_SNIPPETS = {
    "data-model.md": (
        'SESSIONS ||--o{ ATLASSIAN_EVIDENCE_SCANS : "physical CASCADE composite unique"',
        'SESSIONS ||--o| SESSION_PINS : "physical CASCADE"',
    ),
    "workspace-and-session-activity.md": (
        'SESSIONS ||--o| SESSION_PINS : "physical CASCADE"',
    ),
    "atlassian-source-memory.md": (
        'SESSIONS ||--o{ ATLASSIAN_EVIDENCE_SCANS : "physical CASCADE composite unique"',
        'ATLASSIAN_ITEMS o|..o{ SEARCH_INDEX : "app indexed projection"',
        "`not_found`",
    ),
    "derived-retrieval-index.md": (
        'ATLASSIAN_ITEMS o|..o{ SEARCH_INDEX : "app indexed projection"',
        'ATLASSIAN_CLASSIFICATIONS }o..o{ SEARCH_INDEX : "app local role input"',
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_section(document: str, table: str) -> str | None:
    match = re.search(
        rf"^### `{re.escape(table)}`\s*$\n(.*?)(?=^### `|^## |\Z)",
        document,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else None


def markdown_targets(path: Path, document: str):
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document):
        target = target.split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        yield (path.parent / target).resolve()


def main() -> int:
    errors: list[str] = []
    entry = ENTRY.read_text(encoding="utf-8")
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    db_source = DB_PATH.read_text(encoding="utf-8")

    connection = sqlite3.connect(":memory:")
    connection.executescript(schema_sql)
    ordinary_tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name FROM sqlite_schema
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
              AND name != 'search_index'
              AND name NOT LIKE 'search_index_%'
            """
        )
    }
    search_sql_row = connection.execute(
        "SELECT sql FROM sqlite_schema WHERE type = 'table' AND name = 'search_index'"
    ).fetchone()
    search_exists = bool(search_sql_row and "fts5" in (search_sql_row[0] or "").lower())

    expected_ordinary = {
        table
        for tables in SUBJECTS.values()
        for table in tables
        if table != "search_index"
    }
    if ordinary_tables != expected_ordinary:
        errors.append(
            "ordinary table ownership differs: "
            f"missing={sorted(ordinary_tables - expected_ordinary)} "
            f"extra={sorted(expected_ordinary - ordinary_tables)}"
        )
    if not search_exists:
        errors.append("search_index is missing or is not an FTS5 table")
    if len(ordinary_tables) != 36:
        errors.append(f"expected 36 ordinary tables, found {len(ordinary_tables)}")

    physical_fk_count = sum(
        len(
            {
                row[0]
                for row in connection.execute(
                    f'PRAGMA foreign_key_list("{table}")'
                ).fetchall()
            }
        )
        for table in ordinary_tables
    )
    if physical_fk_count != 44:
        errors.append(f"expected 44 physical foreign keys, found {physical_fk_count}")

    fresh_indexes = {
        row[0]: row[1]
        for row in connection.execute(
            "SELECT name, tbl_name FROM sqlite_schema WHERE type = 'index' AND sql IS NOT NULL"
        )
    }
    runtime_indexes = {
        name: table
        for name, table in re.findall(
            r"CREATE INDEX IF NOT EXISTS\s+(\w+)\s+ON\s+(\w+)",
            db_source,
            flags=re.IGNORECASE,
        )
    }
    effective_indexes = {**fresh_indexes, **runtime_indexes}
    if len(fresh_indexes) != 27:
        errors.append(f"expected 27 fresh explicit indexes, found {len(fresh_indexes)}")
    if len(effective_indexes) != 34:
        errors.append(f"expected 34 effective explicit indexes, found {len(effective_indexes)}")

    documented_objects: list[str] = []
    documents: list[tuple[Path, str]] = [(ENTRY, entry)]
    for filename, expected_tables in SUBJECTS.items():
        path = SUBJECT_ROOT / filename
        if not path.is_file():
            errors.append(f"missing subject document: {path.relative_to(ROOT)}")
            continue
        document = path.read_text(encoding="utf-8")
        documents.append((path, document))
        marker = re.search(r"<!-- schema-objects:\s*([^>]+?)\s*-->", document)
        if not marker:
            errors.append(f"missing schema-objects marker: {path.relative_to(ROOT)}")
            continue
        marker_tables = tuple(item.strip() for item in marker.group(1).split(","))
        if marker_tables != expected_tables:
            errors.append(
                f"owner marker mismatch in {path.relative_to(ROOT)}: "
                f"expected={expected_tables} actual={marker_tables}"
            )
        documented_objects.extend(marker_tables)

        for table in expected_tables:
            section = table_section(document, table)
            if section is None:
                errors.append(f"missing catalog section for {table} in {path.relative_to(ROOT)}")
                continue
            for label in REQUIRED_TABLE_LABELS:
                if label not in section:
                    errors.append(f"{table} is missing {label} in {path.relative_to(ROOT)}")
            columns = [
                row[1]
                for row in connection.execute(f'PRAGMA table_info("{table}")').fetchall()
            ]
            for column in columns:
                if f"`{column}`" not in section:
                    errors.append(
                        f"{path.relative_to(ROOT)} does not catalog {table}.{column}"
                    )
            for index_name, index_table in effective_indexes.items():
                if index_table == table and f"`{index_name}`" not in section:
                    errors.append(
                        f"{path.relative_to(ROOT)} does not catalog index {index_name}"
                    )

    expected_objects = sorted(expected_ordinary | {"search_index"})
    if sorted(documented_objects) != expected_objects:
        errors.append("subject markers do not own every effective object exactly once")
    for table in expected_objects:
        if f"`{table}`" not in entry:
            errors.append(f"global entry does not name {table}")

    schema_digest = sha256(SCHEMA_PATH)
    db_digest = sha256(DB_PATH)
    if f"`schema.sql` SHA-256: `{schema_digest}`" not in entry:
        errors.append("schema.sql baseline digest is stale")
    if f"`db.py` SHA-256: `{db_digest}`" not in entry:
        errors.append("db.py baseline digest is stale")

    if "Ordinary tables: `36`" not in entry or "Physical foreign keys: `44`" not in entry:
        errors.append("global baseline counts are stale")
    if "Effective explicitly named indexes: `34`" not in entry:
        errors.append("global effective-index count is stale")

    semantic_documents = {
        "data-model.md": entry,
        **{
            filename: (SUBJECT_ROOT / filename).read_text(encoding="utf-8")
            for filename in SUBJECTS
        },
    }
    for filename, snippets in REQUIRED_SEMANTIC_SNIPPETS.items():
        for snippet in snippets:
            if snippet not in semantic_documents[filename]:
                errors.append(
                    f"{filename} is missing required semantic contract: {snippet}"
                )

    architecture = (ROOT / "docs/policies/project/architecture.md").read_text(encoding="utf-8")
    docs_map = (ROOT / "docs/README.md").read_text(encoding="utf-8")
    if "[Data Model](data-model.md)" not in architecture:
        errors.append("Project Architecture does not link to Data Model")
    if "[Data Model](policies/project/data-model.md)" not in docs_map:
        errors.append("Documentation Map does not link to Data Model")
    if "[Value Dictionaries](policies/project/data-model/value-dictionaries.md)" not in docs_map:
        errors.append("Documentation Map does not link to Value Dictionaries")
    if "[Value Dictionaries](data-model/value-dictionaries.md)" not in entry:
        errors.append("Data Model does not link to Value Dictionaries")
    for filename in SUBJECTS:
        subject_id = filename.removesuffix(".md")
        expected_link = f"[Value Dictionary](value-dictionaries/{subject_id}.md)"
        if expected_link not in semantic_documents[filename]:
            errors.append(f"{filename} does not link to its Value Dictionary")

    documents.extend(
        [
            (ROOT / "docs/policies/project/architecture.md", architecture),
            (ROOT / "docs/README.md", docs_map),
            (
                ROOT / "docs/policies/project/data-model/value-dictionaries.md",
                (
                    ROOT / "docs/policies/project/data-model/value-dictionaries.md"
                ).read_text(encoding="utf-8"),
            ),
        ]
    )
    for filename in SUBJECTS:
        subject_id = filename.removesuffix(".md")
        path = (
            ROOT
            / "docs/policies/project/data-model/value-dictionaries"
            / f"{subject_id}.md"
        )
        if path.is_file():
            documents.append((path, path.read_text(encoding="utf-8")))

    errors.extend(check_documents(ROOT))
    for path, document in documents:
        for target in markdown_targets(path, document):
            if not target.exists():
                errors.append(
                    f"broken local link in {path.relative_to(ROOT)}: {target}"
                )

    connection.close()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "Data-model docs match 36 ordinary tables, 1 FTS5 object, "
        "44 physical foreign keys, 34 explicit indexes, and 9 subject owners."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
