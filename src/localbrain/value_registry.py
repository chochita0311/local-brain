import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Optional


REGISTRY_PATH = Path(__file__).with_name("value-registry.json")
REGISTRY_SCHEMA = "localbrain.data-model-value-registry.v1"
PRESENTATION_MODES = {"direct", "logical-label", "internal-only"}
FALLBACK_ACTIONS = {"reject", "internal", "label"}


class ValueRegistryError(RuntimeError):
    pass


def _value_key(value: Any) -> str:
    if value is None:
        return "__null__"
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def validate_value_registry(registry: Mapping[str, Any]) -> None:
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise ValueRegistryError("unsupported value registry schema")
    subjects = registry.get("subjects")
    families = registry.get("families")
    exclusions = registry.get("exclusions")
    if not isinstance(subjects, list) or len(subjects) != 9:
        raise ValueRegistryError("value registry must declare nine subjects")
    if not isinstance(families, list) or not families:
        raise ValueRegistryError("value registry has no families")
    if not isinstance(exclusions, list) or not exclusions:
        raise ValueRegistryError("value registry has no exclusion ledger")

    subject_ids = {item.get("id") for item in subjects if isinstance(item, dict)}
    if len(subject_ids) != len(subjects) or None in subject_ids:
        raise ValueRegistryError("subject identifiers must be unique and present")

    family_ids = set()
    physical_fields = set()
    for family in families:
        if not isinstance(family, dict):
            raise ValueRegistryError("family entries must be objects")
        family_id = family.get("id")
        if not isinstance(family_id, str) or not family_id:
            raise ValueRegistryError("family identifier is missing")
        if family_id in family_ids:
            raise ValueRegistryError("duplicate family identifier: {}".format(family_id))
        family_ids.add(family_id)
        if family.get("subject") not in subject_ids:
            raise ValueRegistryError("{} has an unknown subject".format(family_id))

        fields = family.get("physical_fields")
        values = family.get("values")
        if not isinstance(fields, list) or not fields:
            raise ValueRegistryError("{} has no physical or projection field".format(family_id))
        if not isinstance(values, list) or not values:
            raise ValueRegistryError("{} has no bounded values".format(family_id))
        value_keys = [_value_key(value) for value in values]
        if len(value_keys) != len(set(value_keys)):
            raise ValueRegistryError("{} has duplicate values".format(family_id))
        for field in fields:
            if field in physical_fields:
                raise ValueRegistryError("duplicate physical field owner: {}".format(field))
            physical_fields.add(field)

        for required in (
            "enforcement",
            "axis",
            "default",
            "fallbacks",
            "producers",
            "consumers",
            "consequence",
            "presentation",
            "sources",
        ):
            if required not in family:
                raise ValueRegistryError("{} is missing {}".format(family_id, required))

        fallbacks = family["fallbacks"]
        if set(fallbacks) != {"null", "unknown", "invalid", "future"}:
            raise ValueRegistryError("{} has incomplete fallback policy".format(family_id))
        for key, fallback in fallbacks.items():
            if not isinstance(fallback, dict) or fallback.get("action") not in FALLBACK_ACTIONS:
                raise ValueRegistryError(
                    "{} has an invalid {} fallback".format(family_id, key)
                )
            if fallback["action"] == "label" and not fallback.get("label"):
                raise ValueRegistryError(
                    "{} has an unlabeled {} fallback".format(family_id, key)
                )

        presentation = family["presentation"]
        mode = presentation.get("mode")
        if mode not in PRESENTATION_MODES:
            raise ValueRegistryError("{} has an invalid presentation mode".format(family_id))
        labels = presentation.get("labels", {})
        visible = family.get("visible_consumers", [])
        if mode == "logical-label":
            if set(labels) != set(value_keys):
                raise ValueRegistryError(
                    "{} logical labels do not cover the complete family".format(family_id)
                )
            if not all(isinstance(label, str) and label.strip() for label in labels.values()):
                raise ValueRegistryError("{} has an empty logical label".format(family_id))
        elif labels:
            raise ValueRegistryError(
                "{} may not declare labels in {} mode".format(family_id, mode)
            )
        if mode == "internal-only" and visible:
            raise ValueRegistryError(
                "{} is internal-only but declares visible consumers".format(family_id)
            )


@lru_cache(maxsize=1)
def load_value_registry() -> dict:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    validate_value_registry(registry)
    return registry


def value_family(family_id: str) -> dict:
    for family in load_value_registry()["families"]:
        if family["id"] == family_id:
            return family
    raise ValueRegistryError("unknown value family: {}".format(family_id))


def visible_value_label(
    family_id: str,
    value: Any,
    *,
    fallback: Optional[str] = None,
) -> str:
    family = value_family(family_id)
    presentation = family["presentation"]
    mode = presentation["mode"]
    if mode == "internal-only":
        raise ValueRegistryError("{} is not visible".format(family_id))
    key = _value_key(value)
    if key not in {_value_key(item) for item in family["values"]}:
        fallback_key = fallback or ("null" if value is None else "unknown")
        policy = family["fallbacks"].get(fallback_key)
        if not policy or policy["action"] != "label":
            raise ValueRegistryError(
                "{} rejects {} fallback".format(family_id, fallback_key)
            )
        return policy["label"]
    if mode == "direct":
        return key
    try:
        return presentation["labels"][key]
    except KeyError as exc:
        raise ValueRegistryError(
            "{} has no label for {}".format(family_id, key)
        ) from exc


def display_value_label(family_id: str, value: Any) -> str:
    """Return a bounded ordinary-screen label without exposing an unknown token."""
    try:
        return visible_value_label(family_id, value)
    except ValueRegistryError:
        return "표시할 수 없음"


def visible_value_help(family_id: str) -> str:
    family = value_family(family_id)
    if family["presentation"]["mode"] == "internal-only":
        raise ValueRegistryError("{} is not visible".format(family_id))
    return family["presentation"].get("help", "")
