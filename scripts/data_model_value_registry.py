from __future__ import annotations

import ast
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from localbrain.value_registry import (  # noqa: E402
    REGISTRY_PATH,
    ValueRegistryError,
    validate_value_registry,
)


DICTIONARY_ROOT = ROOT / "docs/policies/project/data-model/value-dictionaries"
DICTIONARY_ENTRY = ROOT / "docs/policies/project/data-model/value-dictionaries.md"

REQUIRED_BOOLEAN_FIELDS = {
    "external_source_instances.enabled",
    "workspaces.exists_now",
    "context_roots.readable",
    "context_roots.enabled",
    "atlassian_item_remote_state.known_changed",
    "atlassian_item_remote_state.projection_stale",
    "local_resources.exists_now",
    "maintenance_runs.refresh_suggestions",
    "maintenance_runs.mcp_budget_exceeded",
}

REQUIRED_APPLICATION_FAMILIES = {
    "source.kind",
    "source.provider-kind",
    "source.scan-status",
    "source-file.status",
    "context-root.source-type",
    "context-root.status",
    "workstream.status",
    "thread.status",
    "organization-link.entity-type",
    "external-resource.type",
    "local-resource.type",
    "suggestion.type",
    "suggestion.target",
    "suggestion.status",
    "checkpoint-reference.entity-type",
    "maintenance.runner",
    "maintenance.task-type",
    "maintenance.status",
    "external-sync.service",
    "search-index.entity-type",
}

REQUIRED_DERIVED_FAMILIES = {
    "external-capability.state",
    "usage.freshness",
    "atlassian-item.freshness",
    "external-sync.outcome",
}

CONSUMER_STATES = {"pending-normalization", "registry-backed"}


class RegistryCheckError(RuntimeError):
    pass


def _value_key(value: Any) -> str:
    if value is None:
        return "__null__"
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    registry = json.loads(path.read_text(encoding="utf-8"))
    validate_value_registry(registry)
    return registry


def _sql_literal_values(source: str) -> set[Any]:
    values: set[Any] = set()
    for token in source.split(","):
        token = token.strip()
        if re.fullmatch(r"'(?:''|[^'])*'", token):
            values.add(token[1:-1].replace("''", "'"))
        elif re.fullmatch(r"-?\d+", token):
            values.add(int(token))
    return values


def schema_check_families(root: Path = ROOT) -> dict[str, set[Any]]:
    schema = (root / "src/localbrain/schema.sql").read_text(encoding="utf-8")
    result: dict[str, set[Any]] = {}
    for table_match in re.finditer(
        r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)(?=\n\);)",
        schema,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        table, body = table_match.groups()
        for value_match in re.finditer(
            r"\b([a-z_][a-z0-9_]*)\s+IN\s*\(([^()]*)\)",
            body,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            column, raw_values = value_match.groups()
            values = _sql_literal_values(raw_values)
            if values:
                result.setdefault(f"{table}.{column}", set()).update(values)
    return result


def _assignment_nodes(path: Path) -> dict[str, ast.AST]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assignments: dict[str, ast.AST] = {}
    for node in module.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                assignments[target.id] = node.value
    return assignments


def _literal_family(node: ast.AST, assignments: Mapping[str, ast.AST]) -> set[Any]:
    if isinstance(node, ast.Constant):
        return {node.value}
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        result: set[Any] = set()
        for element in node.elts:
            result.update(_literal_family(element, assignments))
        return result
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in {"frozenset", "set", "tuple", "list"} and len(node.args) == 1:
            return _literal_family(node.args[0], assignments)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _literal_family(node.left, assignments) | _literal_family(
            node.right, assignments
        )
    if isinstance(node, ast.Name) and node.id in assignments:
        return _literal_family(assignments[node.id], assignments)
    raise RegistryCheckError("constant is not a bounded literal family")


def python_constant_values(root: Path, path: str, names: Iterable[str]) -> set[Any]:
    absolute = root / path
    assignments = _assignment_nodes(absolute)
    values: set[Any] = set()
    for name in names:
        if name not in assignments:
            raise RegistryCheckError(f"{path} does not declare {name}")
        values.update(_literal_family(assignments[name], assignments))
    return values


def validate_registry(
    root: Path = ROOT,
    registry: Mapping[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if registry is None:
        try:
            registry = load_registry(root / "src/localbrain/value-registry.json")
        except (OSError, json.JSONDecodeError, ValueRegistryError) as error:
            return [f"value registry is invalid: {error}"]
    else:
        registry = copy.deepcopy(registry)
        try:
            validate_value_registry(registry)
        except ValueRegistryError as error:
            return [f"value registry is invalid: {error}"]

    families = {family["id"]: family for family in registry["families"]}
    schema_families = schema_check_families(root)
    registry_schema_sources: dict[str, tuple[str, set[Any]]] = {}
    declared_visible_pairs: set[tuple[str, str]] = set()

    for family in registry["families"]:
        family_values = set(family["values"])
        for source in family["sources"]:
            kind = source.get("kind")
            if kind == "schema-check":
                field = source.get("field")
                if field in registry_schema_sources:
                    errors.append(f"{field} has duplicate schema-check owners")
                registry_schema_sources[field] = (family["id"], family_values)
            elif kind == "python-constant":
                try:
                    actual = python_constant_values(
                        root, source["path"], [source["name"]]
                    )
                except (OSError, SyntaxError, RegistryCheckError) as error:
                    errors.append(f"{family['id']} constant check failed: {error}")
                    continue
                if actual != family_values:
                    errors.append(
                        f"{family['id']} differs from {source['path']}:{source['name']}: "
                        f"registry={sorted(map(str, family_values))} "
                        f"code={sorted(map(str, actual))}"
                    )
            elif kind == "python-constants":
                try:
                    actual = python_constant_values(
                        root, source["path"], source["names"]
                    )
                except (OSError, SyntaxError, RegistryCheckError) as error:
                    errors.append(f"{family['id']} constant check failed: {error}")
                    continue
                if actual != family_values:
                    errors.append(
                        f"{family['id']} differs from {source['path']}:{source['names']}: "
                        f"registry={sorted(map(str, family_values))} "
                        f"code={sorted(map(str, actual))}"
                    )

        for consumer in family.get("visible_consumers", []):
            path = root / consumer.get("path", "")
            state = consumer.get("state")
            declared_visible_pairs.add(
                (consumer.get("path", ""), family["id"])
            )
            if state not in CONSUMER_STATES:
                errors.append(
                    f"{family['id']} has invalid consumer state {state!r}"
                )
            if not path.is_file():
                errors.append(
                    f"{family['id']} visible consumer is missing: "
                    f"{consumer.get('path')}"
                )
                continue
            if state == "registry-backed":
                marker = f'value_label("{family["id"]}"'
                alternate = f"value_label('{family['id']}'"
                document = path.read_text(encoding="utf-8")
                if marker not in document and alternate not in document:
                    errors.append(
                        f"{family['id']} registry-backed consumer lacks a "
                        f"value_label marker: {consumer['path']}"
                    )

    used_visible_pairs: set[tuple[str, str]] = set()
    templates_root = root / "src/localbrain/templates"
    if templates_root.is_dir():
        for path in templates_root.glob("*.html"):
            document = path.read_text(encoding="utf-8")
            relative = str(path.relative_to(root))
            for match in re.finditer(
                r"""value_label\(\s*["']([^"']+)["']""",
                document,
            ):
                used_visible_pairs.add((relative, match.group(1)))
    undeclared_pairs = used_visible_pairs - declared_visible_pairs
    if undeclared_pairs:
        errors.append(
            "value_label calls are missing from the visible consumer inventory: "
            + ", ".join(
                "{}:{}".format(path, family_id)
                for path, family_id in sorted(undeclared_pairs)
            )
        )

    schema_source_fields = set(registry_schema_sources)
    schema_fields = set(schema_families)
    if schema_source_fields != schema_fields:
        errors.append(
            "schema CHECK vocabulary ownership differs: "
            f"missing={sorted(schema_fields - schema_source_fields)} "
            f"extra={sorted(schema_source_fields - schema_fields)}"
        )
    for field in sorted(schema_fields & schema_source_fields):
        family_id, registered = registry_schema_sources[field]
        actual = schema_families[field]
        if registered != actual:
            errors.append(
                f"{family_id} differs from {field}: "
                f"registry={sorted(map(str, registered))} "
                f"schema={sorted(map(str, actual))}"
            )

    physical_owners = {
        field: family["id"]
        for family in registry["families"]
        for field in family["physical_fields"]
    }
    missing_boolean_fields = REQUIRED_BOOLEAN_FIELDS - set(physical_owners)
    if missing_boolean_fields:
        errors.append(
            f"boolean-like inventory is missing {sorted(missing_boolean_fields)}"
        )
    for field in sorted(REQUIRED_BOOLEAN_FIELDS & set(physical_owners)):
        family = families[physical_owners[field]]
        if set(family["values"]) != {0, 1}:
            errors.append(f"{family['id']} does not cover boolean values 0 and 1")

    missing_application = REQUIRED_APPLICATION_FAMILIES - set(families)
    if missing_application:
        errors.append(
            f"application-stored inventory is missing {sorted(missing_application)}"
        )
    missing_derived = REQUIRED_DERIVED_FAMILIES - set(families)
    if missing_derived:
        errors.append(f"derived inventory is missing {sorted(missing_derived)}")

    subject_ids = {subject["id"] for subject in registry["subjects"]}
    subjects_with_exclusions = {
        exclusion.get("subject") for exclusion in registry["exclusions"]
    }
    if not subject_ids.issubset(
        {family["subject"] for family in registry["families"]}
        | subjects_with_exclusions
    ):
        errors.append("one or more subjects have neither a family nor an exclusion")

    return errors


def _display_value(value: Any) -> str:
    if value is None:
        return "`NULL`"
    return f"`{value}`"


def _display_fallbacks(fallbacks: Mapping[str, Mapping[str, str]]) -> str:
    parts = []
    for name in ("null", "unknown", "invalid", "future"):
        policy = fallbacks[name]
        detail = policy["action"]
        if policy.get("label"):
            detail += f" → {policy['label']}"
        parts.append(f"`{name}`: {detail}")
    return "; ".join(parts)


def _generated_notice() -> str:
    return (
        "<!-- Generated from src/localbrain/value-registry.json by "
        "scripts/build-data-model-value-dictionaries.py. Do not edit. -->"
    )


def render_entry(registry: Mapping[str, Any]) -> str:
    family_counts = {
        subject["id"]: sum(
            family["subject"] == subject["id"] for family in registry["families"]
        )
        for subject in registry["subjects"]
    }
    exclusion_counts = {
        subject["id"]: sum(
            exclusion["subject"] == subject["id"]
            for exclusion in registry["exclusions"]
        )
        for subject in registry["subjects"]
    }
    lines = [
        _generated_notice(),
        "# Data Model Value Dictionaries",
        "",
        "This index projects the executable bounded-value authority into nine "
        "subject-owned dictionaries. The existing subject catalogs continue to "
        "own tables, columns, relationships, lifecycle, deletion, and recovery.",
        "",
        "## Presentation Modes",
        "",
        "- `direct`: every value in the complete family renders as its physical token.",
        "- `logical-label`: every allowed value and permitted fallback uses the complete mapping.",
        "- `internal-only`: the complete family stays off ordinary product screens.",
        "",
        "A family never mixes modes. Runtime code loads "
        "`src/localbrain/value-registry.json`; it does not parse these Markdown files.",
        "",
        "## Subject Dictionaries",
        "",
        "| Subject | Families | Explicit exclusions | Dictionary |",
        "| --- | ---: | ---: | --- |",
    ]
    for subject in registry["subjects"]:
        subject_id = subject["id"]
        lines.append(
            f"| {subject['label']} | {family_counts[subject_id]} | "
            f"{exclusion_counts[subject_id]} | "
            f"[Open](value-dictionaries/{subject_id}.md) |"
        )
    lines.extend(
        [
            "",
            "## Verification",
            "",
            "```bash",
            "uv run python scripts/build-data-model-value-dictionaries.py check",
            "uv run python scripts/check-data-model-docs.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def render_subject(registry: Mapping[str, Any], subject: Mapping[str, Any]) -> str:
    subject_id = subject["id"]
    families = [
        family
        for family in registry["families"]
        if family["subject"] == subject_id
    ]
    exclusions = [
        exclusion
        for exclusion in registry["exclusions"]
        if exclusion["subject"] == subject_id
    ]
    lines = [
        _generated_notice(),
        f"# {subject['label']} Value Dictionary",
        "",
        f"Durable table owner: [{subject['owner']}](../{Path(subject['owner']).name})",
        "",
        "This companion owns bounded physical/logical/presentation mappings only. "
        "It does not duplicate the table catalog.",
        "",
    ]
    for family in families:
        presentation = family["presentation"]
        labels = presentation.get("labels", {})
        lines.extend(
            [
                f"## `{family['id']}`",
                "",
                f"- Physical field or projection: {', '.join(f'`{field}`' for field in family['physical_fields'])}",
                f"- Allowed values: {', '.join(_display_value(value) for value in family['values'])}",
                f"- Enforcement: `{family['enforcement']}`",
                f"- Logical axis: {family['axis']}",
                f"- Default: {_display_value(family['default'])}",
                f"- Fallbacks: {_display_fallbacks(family['fallbacks'])}",
                f"- Producers: {', '.join(f'`{item}`' for item in family['producers'])}",
                f"- Consumers: {', '.join(f'`{item}`' for item in family['consumers'])}",
                f"- Consequence: {family['consequence']}",
                f"- Presentation mode: `{presentation['mode']}`",
            ]
        )
        if labels:
            lines.append(
                "- Labels: "
                + "; ".join(
                    f"`{key}` → {label}" for key, label in labels.items()
                )
            )
        else:
            lines.append("- Labels: none; the family is not visible on ordinary screens.")
        lines.append(f"- Help: {presentation.get('help') or 'none'}")
        if family["visible_consumers"]:
            lines.append(
                "- Visible consumer inventory: "
                + "; ".join(
                    f"`{consumer['path']}` ({consumer['state']})"
                    for consumer in family["visible_consumers"]
                )
            )
        else:
            lines.append("- Visible consumer inventory: none.")
        lines.append("")

    lines.extend(["## Explicit Exclusions", ""])
    if exclusions:
        lines.extend(
            [
                "| Pattern | Owner | Reason |",
                "| --- | --- | --- |",
            ]
        )
        for exclusion in exclusions:
            lines.append(
                f"| `{exclusion['pattern']}` | {exclusion['owner']} | "
                f"{exclusion['reason']} |"
            )
    else:
        lines.append("No subject-specific exclusions.")
    lines.append("")
    return "\n".join(lines)


def rendered_documents(
    registry: Mapping[str, Any],
    root: Path = ROOT,
) -> dict[Path, str]:
    documents = {root / DICTIONARY_ENTRY.relative_to(ROOT): render_entry(registry)}
    for subject in registry["subjects"]:
        path = (
            root
            / DICTIONARY_ROOT.relative_to(ROOT)
            / f"{subject['id']}.md"
        )
        documents[path] = render_subject(registry, subject)
    return documents


def write_documents(root: Path = ROOT) -> None:
    registry = load_registry(root / "src/localbrain/value-registry.json")
    errors = validate_registry(root, registry)
    if errors:
        raise RegistryCheckError("\n".join(errors))
    for path, document in rendered_documents(registry, root).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document, encoding="utf-8")


def check_documents(root: Path = ROOT) -> list[str]:
    try:
        registry = load_registry(root / "src/localbrain/value-registry.json")
    except (OSError, json.JSONDecodeError, ValueRegistryError) as error:
        return [f"value registry is invalid: {error}"]
    errors = validate_registry(root, registry)
    for path, expected in rendered_documents(registry, root).items():
        if not path.is_file():
            errors.append(f"generated value dictionary is missing: {path.relative_to(root)}")
        elif path.read_text(encoding="utf-8") != expected:
            errors.append(f"generated value dictionary is stale: {path.relative_to(root)}")
    return errors
