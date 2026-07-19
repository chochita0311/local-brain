import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


SCHEMA_PRESENTATION_PATH = Path(__file__).with_name("schema-presentation.json")


@dataclass(frozen=True)
class SchemaPresentationLoad:
    available: bool
    manifest: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


def load_schema_presentation(
    path: Path = SCHEMA_PRESENTATION_PATH,
) -> SchemaPresentationLoad:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return SchemaPresentationLoad(
            available=False,
            error_code="manifest-unavailable",
        )
    except (UnicodeError, json.JSONDecodeError):
        return SchemaPresentationLoad(
            available=False,
            error_code="manifest-invalid",
        )

    if not _valid_manifest(manifest):
        return SchemaPresentationLoad(
            available=False,
            error_code="manifest-invalid",
        )
    return SchemaPresentationLoad(available=True, manifest=manifest)


def _valid_manifest(manifest: Any) -> bool:
    if not isinstance(manifest, dict):
        return False
    if manifest.get("schema") != "localbrain.schema-presentation.v1":
        return False
    if manifest.get("derived") is not True:
        return False

    baseline = manifest.get("baseline")
    global_view = manifest.get("global")
    subjects = manifest.get("subjects")
    tables = manifest.get("tables")
    relationships = manifest.get("relationships")
    if not _valid_baseline(baseline):
        return False
    if not _nonempty_string(global_view, "mermaid"):
        return False
    if not isinstance(subjects, list):
        return False
    if len(subjects) != baseline["subject_count"]:
        return False
    if not isinstance(tables, list):
        return False
    expected_table_count = (
        baseline["ordinary_table_count"] + baseline["fts5_table_count"]
    )
    if len(tables) != expected_table_count:
        return False
    if not isinstance(relationships, dict):
        return False
    if not isinstance(relationships.get("physical"), list):
        return False
    if not isinstance(relationships.get("application"), list):
        return False
    if len(relationships["physical"]) != baseline["physical_foreign_key_count"]:
        return False
    if not all(_valid_relationship(item) for item in relationships["physical"]):
        return False
    if not all(_valid_relationship(item) for item in relationships["application"]):
        return False

    if not all(_valid_subject(subject) for subject in subjects):
        return False
    if not all(_valid_table(table) for table in tables):
        return False
    table_ids = [table["id"] for table in tables]
    if len(set(table_ids)) != len(table_ids):
        return False
    owned_ids = [
        table_id
        for subject in subjects
        for table_id in subject["table_ids"]
    ]
    subject_ids = {subject["id"] for subject in subjects}
    if len(subject_ids) != len(subjects):
        return False
    if sorted(owned_ids) != sorted(table_ids):
        return False
    if any(table["subject_id"] not in subject_ids for table in tables):
        return False
    return all(
        table["id"] in next(
            subject["table_ids"]
            for subject in subjects
            if subject["id"] == table["subject_id"]
        )
        for table in tables
    )


def _valid_baseline(value: Any) -> bool:
    if not isinstance(value, dict) or not _nonempty_string(value, "id"):
        return False
    count_fields = (
        "ordinary_table_count",
        "fts5_table_count",
        "physical_foreign_key_count",
        "explicit_index_count",
        "subject_count",
    )
    if any(
        not isinstance(value.get(field), int) or value[field] < 0
        for field in count_fields
    ):
        return False
    sources = value.get("sources")
    return isinstance(sources, list) and bool(sources) and all(
        isinstance(source, dict)
        and _nonempty_string(source, "path")
        and _nonempty_string(source, "role")
        and isinstance(source.get("sha256"), str)
        and len(source["sha256"]) == 64
        for source in sources
    )


def _valid_subject(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and _nonempty_string(value, "id")
        and _nonempty_string(value, "label")
        and _nonempty_string(value, "document")
        and _nonempty_string(value, "mermaid")
        and isinstance(value.get("table_ids"), list)
        and bool(value["table_ids"])
        and all(isinstance(table_id, str) and table_id for table_id in value["table_ids"])
    )


def _valid_table(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("kind") not in {"ordinary", "fts5"}:
        return False
    if not all(
        _nonempty_string(value, field)
        for field in ("id", "subject_id", "semantic_document")
    ):
        return False
    columns = value.get("columns")
    constraints = value.get("constraints")
    indexes = value.get("indexes")
    foreign_keys = value.get("foreign_keys")
    semantics = value.get("semantics")
    if not isinstance(columns, list) or not columns:
        return False
    if not all(
        isinstance(column, dict)
        and _nonempty_string(column, "name")
        and "type" in column
        and isinstance(column.get("not_null"), bool)
        and "default_sql" in column
        and isinstance(column.get("primary_key_position"), int)
        and _nonempty_string(column, "semantic_contract")
        for column in columns
    ):
        return False
    if not isinstance(constraints, dict) or not all(
        field in constraints for field in ("primary_key", "unique", "checks", "documented")
    ):
        return False
    if not isinstance(indexes, list) or not isinstance(foreign_keys, list):
        return False
    if not isinstance(semantics, dict):
        return False
    semantic_fields = (
        "purpose_and_authority",
        "lifecycle_contract",
        "class",
        "rebuildability",
        "class_contract",
        "producers",
        "consumers",
        "deletion_effect",
        "recovery_path",
        "schema_ownership",
        "documented_constraints",
    )
    return all(_nonempty_string(semantics, field) for field in semantic_fields)


def _valid_relationship(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and _nonempty_string(value, "source_table")
        and _nonempty_string(value, "target_table")
        and value.get("enforcement") in {"sqlite-foreign-key", "application"}
    )


def _nonempty_string(value: Any, field: str) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get(field), str)
        and bool(value[field].strip())
    )
