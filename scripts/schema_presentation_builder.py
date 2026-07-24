from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_OUTPUT = ROOT / "src/localbrain/schema-presentation.json"
ENTRY_PATH = ROOT / "docs/policies/project/data-model.md"

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from localbrain.db import _run_compatible_migrations  # noqa: E402


class PresentationBuildError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(document: str, heading: str) -> str:
    match = re.search(
        rf"^{re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        document,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise PresentationBuildError(f"Missing section: {heading}")
    return match.group(1)


def table_section(document: str, table: str, document_path: str) -> str:
    match = re.search(
        rf"^### `{re.escape(table)}`\s*$\n(.*?)(?=^### `|^## |\Z)",
        document,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise PresentationBuildError(f"{document_path}: missing table section {table}")
    return match.group(1)


def mermaid(document: str, document_path: str) -> str:
    diagrams = re.findall(r"```mermaid\s*\n([\s\S]*?)```", document)
    if len(diagrams) != 1:
        raise PresentationBuildError(
            f"{document_path}: expected one Mermaid definition, found {len(diagrams)}"
        )
    return diagrams[0].strip() + "\n"


def markdown_cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_subjects(entry: str) -> List[dict]:
    ownership = section(entry, "## Subject Ownership")
    subjects = []
    for line in ownership.splitlines():
        if not line.startswith("|") or "data-model/" not in line:
            continue
        cells = markdown_cells(line)
        if len(cells) != 3:
            continue
        link = re.search(r"\[[^\]]+\]\((data-model/([^)]+\.md))\)", cells[2])
        if not link:
            raise PresentationBuildError(f"Invalid subject owner link: {cells[2]}")
        tables = re.findall(r"`([a-z0-9_]+)`", cells[1])
        if not tables:
            raise PresentationBuildError(f"Subject has no objects: {cells[0]}")
        subjects.append(
            {
                "id": Path(link.group(2)).stem,
                "label": cells[0],
                "document": f"docs/policies/project/{link.group(1)}",
                "table_ids": tables,
            }
        )
    if len(subjects) != 9:
        raise PresentationBuildError(f"Expected 9 subjects, found {len(subjects)}")
    return subjects


def parse_lifecycle(entry: str) -> Dict[str, dict]:
    lifecycle_section = section(entry, "## Lifecycle And Recovery Vocabulary")
    mapping: Dict[str, dict] = {}
    for line in lifecycle_section.splitlines():
        if not line.startswith("|") or "`" not in line:
            continue
        cells = markdown_cells(line)
        if len(cells) != 4 or cells[0] == "Class":
            continue
        rebuildability = re.fullmatch(r"`([^`]+)`", cells[1])
        if not rebuildability:
            raise PresentationBuildError(f"Invalid rebuildability code: {cells[1]}")
        for table in re.findall(r"`([a-z0-9_]+)`", cells[3]):
            if table in mapping:
                raise PresentationBuildError(f"Duplicate lifecycle owner: {table}")
            mapping[table] = {
                "class": cells[0],
                "rebuildability": rebuildability.group(1),
                "class_contract": cells[2],
            }
    return mapping


SEMANTIC_LABELS = {
    "purpose_and_authority": "Purpose and authority",
    "lifecycle_contract": "Lifecycle",
    "producers": "Producers",
    "consumers": "Consumers",
    "deletion_effect": "Relations and deletion",
    "recovery_path": "Recovery",
    "schema_ownership": "DDL ownership",
}


def parse_table_semantics(
    document: str, document_path: str, table: str, lifecycle: dict
) -> dict:
    body = table_section(document, table, document_path)
    semantics = {}
    for key, label in SEMANTIC_LABELS.items():
        match = re.search(rf"^- {re.escape(label)}:\s*(.+)$", body, re.MULTILINE)
        if not match:
            raise PresentationBuildError(f"{document_path}: {table} missing {label}")
        semantics[key] = match.group(1).strip()

    column_contracts = {}
    for name, contract in re.findall(r"^\| `([^`]+)` \| (.+) \|$", body, re.MULTILINE):
        column_contracts[name] = contract.strip()
    if not column_contracts:
        raise PresentationBuildError(f"{document_path}: {table} has no column contracts")

    constraint_match = re.search(
        r"^(Constraints(?: and tokenizer)?):\s*(.+)$", body, re.MULTILINE
    )
    if not constraint_match:
        raise PresentationBuildError(
            f"{document_path}: {table} missing documented constraints"
        )

    semantics.update(lifecycle)
    semantics["column_contracts"] = column_contracts
    semantics["documented_constraints"] = constraint_match.group(2).strip()
    return semantics


def extract_check_constraints(sql: str) -> List[str]:
    checks = []
    upper = sql.upper()
    cursor = 0
    while True:
        start = upper.find("CHECK", cursor)
        if start < 0:
            break
        opening = sql.find("(", start + 5)
        if opening < 0:
            break
        depth = 0
        quote = None
        closing = None
        for index in range(opening, len(sql)):
            character = sql[index]
            if quote:
                if character == quote and (index == 0 or sql[index - 1] != "\\"):
                    quote = None
                continue
            if character in {"'", '"'}:
                quote = character
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    closing = index
                    break
        if closing is None:
            raise PresentationBuildError("Unbalanced CHECK constraint in effective schema")
        checks.append(" ".join(sql[opening + 1 : closing].split()))
        cursor = closing + 1
    return checks


def effective_connection(root: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        (root / "src/localbrain/schema.sql").read_text(encoding="utf-8")
    )
    _run_compatible_migrations(connection, include_data_migrations=False)
    return connection


def physical_table(connection: sqlite3.Connection, table: str, semantics: dict) -> dict:
    schema_row = connection.execute(
        "SELECT sql FROM sqlite_schema WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    if not schema_row:
        raise PresentationBuildError(f"Effective schema is missing {table}")
    create_sql = schema_row["sql"] or ""

    columns = []
    primary_key = []
    for row in connection.execute(f'PRAGMA table_info("{table}")').fetchall():
        name = row["name"]
        if name not in semantics["column_contracts"]:
            raise PresentationBuildError(f"Semantic catalog is missing {table}.{name}")
        columns.append(
            {
                "name": name,
                "type": row["type"] or None,
                "not_null": bool(row["notnull"]),
                "default_sql": row["dflt_value"],
                "primary_key_position": row["pk"],
                "semantic_contract": semantics["column_contracts"][name],
            }
        )
        if row["pk"]:
            primary_key.append((row["pk"], name))

    unique_constraints = []
    explicit_indexes = []
    for index in connection.execute(f'PRAGMA index_list("{table}")').fetchall():
        index_columns = [
            {
                "name": item["name"],
                "descending": bool(item["desc"]),
            }
            for item in connection.execute(
                f'PRAGMA index_xinfo("{index["name"]}")'
            ).fetchall()
            if item["key"] and item["name"] is not None
        ]
        if index["origin"] == "u":
            unique_constraints.append([item["name"] for item in index_columns])
        elif index["origin"] == "c":
            explicit_indexes.append(
                {
                    "name": index["name"],
                    "unique": bool(index["unique"]),
                    "partial": bool(index["partial"]),
                    "columns": index_columns,
                }
            )

    foreign_keys: Dict[int, dict] = {}
    for foreign_key in connection.execute(
        f'PRAGMA foreign_key_list("{table}")'
    ).fetchall():
        item = foreign_keys.setdefault(
            foreign_key["id"],
            {
                "target_table": foreign_key["table"],
                "source_columns": [],
                "target_columns": [],
                "on_update": foreign_key["on_update"],
                "on_delete": foreign_key["on_delete"],
            },
        )
        item["source_columns"].append(foreign_key["from"])
        item["target_columns"].append(foreign_key["to"])

    semantic_output = {
        key: value
        for key, value in semantics.items()
        if key != "column_contracts"
    }
    return {
        "id": table,
        "kind": "fts5" if "USING fts5" in create_sql else "ordinary",
        "columns": columns,
        "constraints": {
            "primary_key": [name for _, name in sorted(primary_key)],
            "unique": sorted(unique_constraints),
            "checks": extract_check_constraints(create_sql),
            "documented": semantics["documented_constraints"],
        },
        "indexes": sorted(explicit_indexes, key=lambda item: item["name"]),
        "foreign_keys": [foreign_keys[key] for key in sorted(foreign_keys)],
        "semantics": semantic_output,
    }


def application_relations(global_mermaid: str, table_ids: Iterable[str]) -> List[dict]:
    known = set(table_ids)
    relations = []
    relation_pattern = re.compile(
        r'^\s*([A-Z0-9_]+)\s+([|o{}]+)\.\.([|o{}]+)\s+'
        r'([A-Z0-9_]+)\s*:\s*"([^"]+)"\s*$',
        re.MULTILINE,
    )
    for source, source_cardinality, target_cardinality, target, label in relation_pattern.findall(
        global_mermaid
    ):
        source_id = source.lower()
        target_id = target.lower()
        if source_id not in known or target_id not in known:
            raise PresentationBuildError(
                f"Application relation has unknown object: {source_id} -> {target_id}"
            )
        relations.append(
            {
                "source_table": source_id,
                "target_table": target_id,
                "source_cardinality": source_cardinality,
                "target_cardinality": target_cardinality,
                "label": label,
                "enforcement": "application",
            }
        )
    if not relations:
        raise PresentationBuildError("Global Mermaid has no application relations")
    return sorted(
        relations,
        key=lambda item: (item["source_table"], item["target_table"], item["label"]),
    )


def parse_baseline_number(entry: str, label: str) -> int:
    match = re.search(rf"^- {re.escape(label)}: `(\d+)`", entry, re.MULTILINE)
    if not match:
        raise PresentationBuildError(f"Missing baseline count: {label}")
    return int(match.group(1))


def build_manifest(root: Path = ROOT) -> dict:
    entry_path = root / "docs/policies/project/data-model.md"
    entry = entry_path.read_text(encoding="utf-8")
    subjects = parse_subjects(entry)
    lifecycle = parse_lifecycle(entry)
    global_mermaid = mermaid(entry, str(entry_path.relative_to(root)))

    entry_id = re.search(r"^- Baseline: `([^`]+)`$", entry, re.MULTILINE)
    if not entry_id:
        raise PresentationBuildError("Missing baseline identity")

    expected_schema_digest = re.search(
        r"^- `schema\.sql` SHA-256: `([0-9a-f]{64})`$", entry, re.MULTILINE
    )
    expected_db_digest = re.search(
        r"^- `db\.py` SHA-256: `([0-9a-f]{64})`$", entry, re.MULTILINE
    )
    schema_path = root / "src/localbrain/schema.sql"
    db_path = root / "src/localbrain/db.py"
    if not expected_schema_digest or expected_schema_digest.group(1) != sha256(schema_path):
        raise PresentationBuildError("Data Model schema.sql baseline digest is stale")
    if not expected_db_digest or expected_db_digest.group(1) != sha256(db_path):
        raise PresentationBuildError("Data Model db.py baseline digest is stale")

    connection = effective_connection(root)
    try:
        effective_objects = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name FROM sqlite_schema
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                  AND name NOT LIKE 'search_index_%'
                """
            )
        }
        ordered_table_ids = [
            table for subject in subjects for table in subject["table_ids"]
        ]
        if len(ordered_table_ids) != len(set(ordered_table_ids)):
            raise PresentationBuildError("A table has more than one subject owner")
        if set(ordered_table_ids) != effective_objects:
            raise PresentationBuildError(
                "Subject ownership does not match the effective schema"
            )
        if set(lifecycle) != effective_objects:
            raise PresentationBuildError("Lifecycle ownership does not match the schema")

        source_documents = [entry_path]
        subject_outputs = []
        semantic_by_table = {}
        table_document = {}
        for subject in subjects:
            document_path = root / subject["document"]
            document = document_path.read_text(encoding="utf-8")
            source_documents.append(document_path)
            subject["mermaid"] = mermaid(document, subject["document"])
            subject_outputs.append(subject)
            for table in subject["table_ids"]:
                semantic_by_table[table] = parse_table_semantics(
                    document, subject["document"], table, lifecycle[table]
                )
                table_document[table] = subject["document"]

        tables = []
        physical_relations = []
        for table_id in ordered_table_ids:
            table = physical_table(connection, table_id, semantic_by_table[table_id])
            table["subject_id"] = next(
                subject["id"]
                for subject in subjects
                if table_id in subject["table_ids"]
            )
            table["semantic_document"] = table_document[table_id]
            tables.append(table)
            for foreign_key in table["foreign_keys"]:
                physical_relations.append(
                    {
                        "source_table": table_id,
                        "target_table": foreign_key["target_table"],
                        "source_columns": foreign_key["source_columns"],
                        "target_columns": foreign_key["target_columns"],
                        "on_update": foreign_key["on_update"],
                        "on_delete": foreign_key["on_delete"],
                        "enforcement": "sqlite-foreign-key",
                    }
                )

        explicit_index_count = sum(len(table["indexes"]) for table in tables)
        ordinary_count = sum(table["kind"] == "ordinary" for table in tables)
        fts_count = sum(table["kind"] == "fts5" for table in tables)
        if ordinary_count != parse_baseline_number(entry, "Ordinary tables"):
            raise PresentationBuildError("Ordinary table count differs from baseline")
        if fts_count != parse_baseline_number(entry, "FTS5 virtual tables"):
            raise PresentationBuildError("FTS5 count differs from baseline")
        if len(physical_relations) != parse_baseline_number(entry, "Physical foreign keys"):
            raise PresentationBuildError("Physical FK count differs from baseline")
        if explicit_index_count != parse_baseline_number(
            entry, "Effective explicitly named indexes"
        ):
            raise PresentationBuildError("Explicit index count differs from baseline")

        semantic_sources = [
            {
                "path": str(path.relative_to(root)),
                "role": "semantic-truth",
                "sha256": sha256(path),
            }
            for path in source_documents
        ]
        return {
            "schema": "localbrain.schema-presentation.v1",
            "derived": True,
            "baseline": {
                "id": entry_id.group(1),
                "ordinary_table_count": ordinary_count,
                "fts5_table_count": fts_count,
                "physical_foreign_key_count": len(physical_relations),
                "explicit_index_count": explicit_index_count,
                "subject_count": len(subjects),
                "sources": [
                    {
                        "path": "src/localbrain/schema.sql",
                        "role": "fresh-schema-truth",
                        "sha256": sha256(schema_path),
                    },
                    {
                        "path": "src/localbrain/db.py",
                        "role": "compatible-structure-truth",
                        "sha256": sha256(db_path),
                    },
                    *semantic_sources,
                ],
            },
            "global": {"mermaid": global_mermaid},
            "subjects": subject_outputs,
            "tables": tables,
            "relationships": {
                "physical": sorted(
                    physical_relations,
                    key=lambda item: (
                        item["source_table"],
                        item["target_table"],
                        item["source_columns"],
                    ),
                ),
                "application": application_relations(
                    global_mermaid, ordered_table_ids
                ),
            },
        }
    finally:
        connection.close()


def manifest_bytes(root: Path = ROOT) -> bytes:
    return (
        json.dumps(build_manifest(root), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def validate_mermaid(root: Path = ROOT) -> None:
    result = subprocess.run(
        ["node", "scripts/check-data-model-mermaid.mjs"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise PresentationBuildError(
            "Mermaid validation failed; run `node scripts/check-data-model-mermaid.mjs`."
        )


def write_manifest(output: Path = PACKAGE_OUTPUT, root: Path = ROOT) -> None:
    validate_mermaid(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(manifest_bytes(root))


def check_manifest(output: Path = PACKAGE_OUTPUT, root: Path = ROOT) -> None:
    validate_mermaid(root)
    expected = manifest_bytes(root)
    try:
        actual = output.read_bytes()
    except FileNotFoundError as error:
        raise PresentationBuildError(
            "Schema presentation is missing; run the build command."
        ) from error
    if actual != expected:
        raise PresentationBuildError(
            "Schema presentation is stale; run the build command."
        )
