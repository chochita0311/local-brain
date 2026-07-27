import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple


READ_POLICY_VERSION = "localbrain.atlassian-read-policy.v1"
CAPABILITY_SCHEMA = "localbrain.external-capabilities.v1"

PROVIDER_MCP_GATEWAY = "mcp_gateway"
PROVIDER_ATLASSIAN_CLOUD = "atlassian_cloud"
SERVICE_JIRA = "jira"
SERVICE_CONFLUENCE = "confluence"

AVAILABILITY_VALUES = {
    "available",
    "unavailable",
    "unauthorized",
    "error",
}

JIRA_METADATA_FIELDS = (
    "key",
    "summary",
    "status",
    "issuetype",
    "priority",
    "labels",
    "components",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolution",
    "project",
    "parent",
)
JIRA_DESCRIPTION_FIELDS = ("key", "description", "updated")

INSTANCE_KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
CONFIG_ALIAS_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
JIRA_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*-[1-9][0-9]*$")
SCHEMA_FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ERROR_CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
REGULAR_PAGE_CQL_PATTERN = re.compile(
    r"\btype\s*=\s*(?:\"page\"|'page'|page)\b", re.IGNORECASE
)
EXCLUDED_CQL_TYPE_PATTERN = re.compile(
    r"\btype\s*=\s*(?:\"(?:comment|attachment|blogpost)\"|"
    r"'(?:comment|attachment|blogpost)'|comment|attachment|blogpost)\b",
    re.IGNORECASE,
)
EXCLUDED_JQL_FIELD_PATTERN = re.compile(
    r"\b(comment|worklog|attachment|development)\b", re.IGNORECASE
)
SAFE_ERROR_MESSAGES = {
    "unavailable": "External capability is unavailable.",
    "unauthorized": "External capability authorization is unavailable.",
    "error": "External capability inspection failed.",
}
DEFAULT_ERROR_CODES = {
    "unavailable": "service-unavailable",
    "unauthorized": "authorization-unavailable",
    "error": "inspection-failed",
}


class ExternalAccessError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ToolDispatch:
    source_instance_id: int
    logical_operation: str
    tool_name: str
    arguments: Dict[str, Any]
    policy_version: str = READ_POLICY_VERSION


@dataclass(frozen=True)
class OperationPolicy:
    tool_name: str
    argument_builder: Callable[[Mapping[str, Any], Mapping[str, Any]], Dict[str, Any]]
    gateway_target: Optional[str] = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _deny(code: str, message: str) -> None:
    raise ExternalAccessError(code, message)


def _bounded_text(
    value: Any,
    field: str,
    *,
    maximum: int,
    optional: bool = False,
) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        _deny("invalid-argument", f"{field} must be a non-empty string")
    normalized = value.strip()
    if len(normalized) > maximum:
        _deny("invalid-argument", f"{field} exceeds {maximum} characters")
    return normalized


def _exact_keys(
    arguments: Mapping[str, Any],
    *,
    required: Iterable[str] = (),
    optional: Iterable[str] = (),
) -> None:
    if not isinstance(arguments, Mapping):
        _deny("invalid-argument", "arguments must be an object")
    required_keys = set(required)
    allowed_keys = required_keys | set(optional)
    missing = required_keys - set(arguments)
    extra = set(arguments) - allowed_keys
    if missing:
        _deny("invalid-argument", "missing arguments: " + ", ".join(sorted(missing)))
    if extra:
        _deny("invalid-argument", "unsupported arguments: " + ", ".join(sorted(extra)))


def _bounded_int(
    value: Any,
    field: str,
    *,
    minimum: int,
    maximum: int,
    default: int,
) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        _deny("invalid-argument", f"{field} must be an integer")
    if value < minimum or value > maximum:
        _deny(
            "invalid-argument",
            f"{field} must be between {minimum} and {maximum}",
        )
    return value


def _field_list(value: Any, allowed: Tuple[str, ...]) -> list:
    if value is None:
        return list(allowed)
    if not isinstance(value, (list, tuple)) or not value:
        _deny("invalid-argument", "fields must be a non-empty list")
    selected = []
    for field in value:
        if not isinstance(field, str) or field not in allowed:
            _deny("field-not-allowed", f"field is not allowed: {field}")
        if field not in selected:
            selected.append(field)
    return selected


def _source_config_ref(instance: Mapping[str, Any]) -> str:
    config_ref = _normalized_config_ref(
        instance.get("provider_kind"), instance.get("config_ref")
    )
    if config_ref is None:
        _deny(
            "missing-config-ref",
            "the Source Instance has no external configuration reference",
        )
    return config_ref


def _normalized_config_ref(
    provider_kind: str, value: Optional[str]
) -> Optional[str]:
    config_ref = _bounded_text(
        value, "config_ref", maximum=300, optional=True
    )
    if config_ref is None:
        return None
    if provider_kind == PROVIDER_MCP_GATEWAY:
        if not CONFIG_ALIAS_PATTERN.fullmatch(config_ref):
            _deny(
                "invalid-config-ref",
                "Gateway config_ref must be a bounded configuration alias",
            )
        return config_ref
    if provider_kind == PROVIDER_ATLASSIAN_CLOUD:
        if not UUID_PATTERN.fullmatch(config_ref):
            _deny(
                "invalid-config-ref",
                "Atlassian config_ref must be a Cloud ID",
            )
        return config_ref.lower()
    _deny("invalid-config-ref", "unsupported provider config_ref")


def _bounded_jql(value: Any) -> str:
    jql = _bounded_text(value, "jql", maximum=4000)
    if EXCLUDED_JQL_FIELD_PATTERN.search(jql):
        _deny(
            "field-not-allowed",
            "JQL cannot inspect comments, worklogs, attachments, or development data",
        )
    return jql


def _gateway_list_builder(
    server: str,
) -> Callable[[Mapping[str, Any], Mapping[str, Any]], Dict[str, Any]]:
    def build(
        arguments: Mapping[str, Any], _instance: Mapping[str, Any]
    ) -> Dict[str, Any]:
        _exact_keys(arguments)
        return {"kind": "tool", "server": server}

    return build


def _gateway_describe_builder(
    prefix: str,
) -> Callable[[Mapping[str, Any], Mapping[str, Any]], Dict[str, Any]]:
    def build(
        arguments: Mapping[str, Any], _instance: Mapping[str, Any]
    ) -> Dict[str, Any]:
        _exact_keys(arguments, required=("names",))
        names = arguments["names"]
        if not isinstance(names, (list, tuple)) or not 1 <= len(names) <= 50:
            _deny("invalid-argument", "names must contain between 1 and 50 tools")
        items = []
        for name in names:
            if not isinstance(name, str) or not name.startswith(prefix):
                _deny("tool-not-allowed", "tool name is outside this Source Instance")
            items.append({"kind": "tool", "name": name})
        return {"items": items}

    return build


def _gateway_jira_search_builder(
    *,
    description: bool,
) -> Callable[[Mapping[str, Any], Mapping[str, Any]], Dict[str, Any]]:
    def build(
        arguments: Mapping[str, Any], _instance: Mapping[str, Any]
    ) -> Dict[str, Any]:
        if description:
            _exact_keys(arguments, required=("issue_key",))
            issue_key = _bounded_text(
                arguments["issue_key"], "issue_key", maximum=80
            ).upper()
            if not JIRA_KEY_PATTERN.fullmatch(issue_key):
                _deny("invalid-argument", "issue_key is not a valid Jira key")
            return {
                "jql": f'key = "{issue_key}"',
                "fields": ",".join(JIRA_DESCRIPTION_FIELDS),
                "maxResults": 1,
                "startAt": 0,
            }

        _exact_keys(
            arguments,
            required=("jql",),
            optional=("fields", "limit", "offset"),
        )
        return {
            "jql": _bounded_jql(arguments["jql"]),
            "fields": ",".join(
                _field_list(arguments.get("fields"), JIRA_METADATA_FIELDS)
            ),
            "maxResults": _bounded_int(
                arguments.get("limit"),
                "limit",
                minimum=1,
                maximum=100,
                default=20,
            ),
            "startAt": _bounded_int(
                arguments.get("offset"),
                "offset",
                minimum=0,
                maximum=1000000,
                default=0,
            ),
        }

    return build


def _cloud_jira_search_builder(
    *,
    description: bool,
) -> Callable[[Mapping[str, Any], Mapping[str, Any]], Dict[str, Any]]:
    def build(
        arguments: Mapping[str, Any], instance: Mapping[str, Any]
    ) -> Dict[str, Any]:
        if description:
            _exact_keys(
                arguments,
                required=("issue_key",),
                optional=("content_format",),
            )
            issue_key = _bounded_text(
                arguments["issue_key"], "issue_key", maximum=80
            ).upper()
            if not JIRA_KEY_PATTERN.fullmatch(issue_key):
                _deny("invalid-argument", "issue_key is not a valid Jira key")
            content_format = arguments.get("content_format", "adf")
            if content_format not in {"adf", "markdown"}:
                _deny("invalid-argument", "unsupported Jira content format")
            return {
                "cloudId": _source_config_ref(instance),
                "jql": f'key = "{issue_key}"',
                "fields": list(JIRA_DESCRIPTION_FIELDS),
                "maxResults": 1,
                "responseContentFormat": content_format,
                "searchResultMode": "issues",
            }

        _exact_keys(
            arguments,
            required=("jql",),
            optional=("fields", "limit", "cursor"),
        )
        output = {
            "cloudId": _source_config_ref(instance),
            "jql": _bounded_jql(arguments["jql"]),
            "fields": _field_list(arguments.get("fields"), JIRA_METADATA_FIELDS),
            "maxResults": _bounded_int(
                arguments.get("limit"),
                "limit",
                minimum=1,
                maximum=100,
                default=50,
            ),
            "searchResultMode": "issues",
        }
        cursor = arguments.get("cursor")
        if cursor is not None:
            output["nextPageToken"] = _bounded_text(
                cursor, "cursor", maximum=2000
            )
        return output

    return build


def _gateway_project_builder(
    arguments: Mapping[str, Any], _instance: Mapping[str, Any]
) -> Dict[str, Any]:
    _exact_keys(arguments, required=("project_id_or_key",))
    return {
        "projectIdOrKey": _bounded_text(
            arguments["project_id_or_key"],
            "project_id_or_key",
            maximum=100,
        )
    }


def _regular_page_cql(value: Any) -> str:
    cql = _bounded_text(value, "cql", maximum=4000)
    if not REGULAR_PAGE_CQL_PATTERN.search(cql):
        _deny("content-type-not-allowed", "CQL must explicitly select type = page")
    if EXCLUDED_CQL_TYPE_PATTERN.search(cql):
        _deny("content-type-not-allowed", "CQL includes an excluded content type")
    return f"({cql}) AND type = page"


def _gateway_confluence_search_builder(
    arguments: Mapping[str, Any], _instance: Mapping[str, Any]
) -> Dict[str, Any]:
    _exact_keys(
        arguments,
        required=("cql",),
        optional=("limit", "offset"),
    )
    return {
        "cql": _regular_page_cql(arguments["cql"]),
        "limit": _bounded_int(
            arguments.get("limit"),
            "limit",
            minimum=1,
            maximum=200,
            default=25,
        ),
        "start": _bounded_int(
            arguments.get("offset"),
            "offset",
            minimum=0,
            maximum=1000000,
            default=0,
        ),
        "expand": "title,excerpt,space.key,version",
    }


def _cloud_confluence_search_builder(
    arguments: Mapping[str, Any], instance: Mapping[str, Any]
) -> Dict[str, Any]:
    _exact_keys(
        arguments,
        required=("cql",),
        optional=("limit", "cursor"),
    )
    output = {
        "cloudId": _source_config_ref(instance),
        "cql": _regular_page_cql(arguments["cql"]),
        "limit": _bounded_int(
            arguments.get("limit"),
            "limit",
            minimum=1,
            maximum=250,
            default=25,
        ),
    }
    cursor = arguments.get("cursor")
    if cursor is not None:
        output["cursor"] = _bounded_text(cursor, "cursor", maximum=2000)
    return output


def _gateway_page_builder(
    arguments: Mapping[str, Any], _instance: Mapping[str, Any]
) -> Dict[str, Any]:
    _exact_keys(arguments, required=("page_id",))
    return {
        "pageId": _bounded_text(arguments["page_id"], "page_id", maximum=200),
        "expand": "body.view,version,space.key,ancestors,metadata.labels",
    }


def _cloud_page_builder(
    arguments: Mapping[str, Any], instance: Mapping[str, Any]
) -> Dict[str, Any]:
    _exact_keys(
        arguments,
        required=("page_id",),
        optional=("content_format",),
    )
    content_format = arguments.get("content_format", "html")
    if content_format not in {"html", "markdown", "adf"}:
        _deny("invalid-argument", "unsupported Confluence content format")
    return {
        "cloudId": _source_config_ref(instance),
        "pageId": _bounded_text(arguments["page_id"], "page_id", maximum=200),
        "contentType": "page",
        "contentFormat": content_format,
    }


def _gateway_children_builder(
    arguments: Mapping[str, Any], _instance: Mapping[str, Any]
) -> Dict[str, Any]:
    _exact_keys(arguments, required=("page_id",))
    return {
        "pageId": _bounded_text(arguments["page_id"], "page_id", maximum=200),
        "expand": "title,space.key,version",
    }


def _cloud_children_builder(
    arguments: Mapping[str, Any], instance: Mapping[str, Any]
) -> Dict[str, Any]:
    _exact_keys(
        arguments,
        required=("page_id",),
        optional=("limit", "cursor"),
    )
    page_id = _bounded_text(arguments["page_id"], "page_id", maximum=200)
    output = {
        "cloudId": _source_config_ref(instance),
        "cql": f'parent = "{page_id}" AND type = page',
        "limit": _bounded_int(
            arguments.get("limit"),
            "limit",
            minimum=1,
            maximum=250,
            default=25,
        ),
    }
    cursor = arguments.get("cursor")
    if cursor is not None:
        output["cursor"] = _bounded_text(cursor, "cursor", maximum=2000)
    return output


def _cloud_resources_builder(
    arguments: Mapping[str, Any], _instance: Mapping[str, Any]
) -> Dict[str, Any]:
    _exact_keys(arguments)
    return {}


def _gateway_policy(
    server: str,
    service_operations: Dict[str, OperationPolicy],
) -> Dict[str, OperationPolicy]:
    return {
        "capability.list_tools": OperationPolicy(
            "mcp_gateway.gateway_list",
            _gateway_list_builder(server),
        ),
        "capability.describe_tools": OperationPolicy(
            "mcp_gateway.gateway_describe",
            _gateway_describe_builder(server + "__"),
        ),
        **service_operations,
    }


POLICIES: Dict[Tuple[str, str], Dict[str, OperationPolicy]] = {
    (PROVIDER_MCP_GATEWAY, SERVICE_JIRA): _gateway_policy(
        "jira",
        {
            "jira.search_metadata": OperationPolicy(
                "mcp_gateway.gateway_dispatch",
                _gateway_jira_search_builder(description=False),
                gateway_target="jira__searchIssuesByJql",
            ),
            "jira.read_description": OperationPolicy(
                "mcp_gateway.gateway_dispatch",
                _gateway_jira_search_builder(description=True),
                gateway_target="jira__searchIssuesByJql",
            ),
            "jira.read_project": OperationPolicy(
                "mcp_gateway.gateway_dispatch",
                _gateway_project_builder,
                gateway_target="jira__getProjectDetails",
            ),
        },
    ),
    (PROVIDER_MCP_GATEWAY, SERVICE_CONFLUENCE): _gateway_policy(
        "wiki",
        {
            "confluence.search_pages": OperationPolicy(
                "mcp_gateway.gateway_dispatch",
                _gateway_confluence_search_builder,
                gateway_target="wiki__searchWiki",
            ),
            "confluence.read_page": OperationPolicy(
                "mcp_gateway.gateway_dispatch",
                _gateway_page_builder,
                gateway_target="wiki__getPageById",
            ),
            "confluence.list_children": OperationPolicy(
                "mcp_gateway.gateway_dispatch",
                _gateway_children_builder,
                gateway_target="wiki__getChildPages",
            ),
        },
    ),
    (PROVIDER_ATLASSIAN_CLOUD, SERVICE_JIRA): {
        "capability.inspect_resources": OperationPolicy(
            "atlassian.getAccessibleAtlassianResources",
            _cloud_resources_builder,
        ),
        "jira.search_metadata": OperationPolicy(
            "atlassian.searchJiraIssuesUsingJql",
            _cloud_jira_search_builder(description=False),
        ),
        "jira.read_description": OperationPolicy(
            "atlassian.searchJiraIssuesUsingJql",
            _cloud_jira_search_builder(description=True),
        ),
    },
    (PROVIDER_ATLASSIAN_CLOUD, SERVICE_CONFLUENCE): {
        "capability.inspect_resources": OperationPolicy(
            "atlassian.getAccessibleAtlassianResources",
            _cloud_resources_builder,
        ),
        "confluence.search_pages": OperationPolicy(
            "atlassian.searchConfluenceUsingCql",
            _cloud_confluence_search_builder,
        ),
        "confluence.read_page": OperationPolicy(
            "atlassian.getConfluencePage",
            _cloud_page_builder,
        ),
        "confluence.list_children": OperationPolicy(
            "atlassian.searchConfluenceUsingCql",
            _cloud_children_builder,
        ),
    },
}


def policy_manifest() -> dict:
    providers = []
    for (provider_kind, service), operations in sorted(POLICIES.items()):
        providers.append(
            {
                "provider_kind": provider_kind,
                "service": service,
                "operations": [
                    {
                        "logical_operation": logical_operation,
                        "tool_name": operation.tool_name,
                        "gateway_target": operation.gateway_target,
                    }
                    for logical_operation, operation in sorted(operations.items())
                ],
            }
        )
    return {
        "schema": "localbrain.external-read-policy.v1",
        "version": READ_POLICY_VERSION,
        "providers": providers,
    }


def known_policy_operations(provider_kind: str, service: str) -> Tuple[str, ...]:
    operations = POLICIES.get((provider_kind, service))
    if operations is None:
        _deny("unsupported-source-instance", "unsupported provider/service pair")
    return tuple(sorted(operations))


def register_source_instance(
    connection,
    *,
    instance_key: str,
    provider_kind: str,
    service: str,
    display_name: str,
    config_ref: Optional[str] = None,
    enabled: bool = True,
) -> dict:
    if not isinstance(instance_key, str) or not INSTANCE_KEY_PATTERN.fullmatch(
        instance_key
    ):
        _deny("invalid-instance-key", "instance_key has an invalid shape")
    known_policy_operations(provider_kind, service)
    display_name = _bounded_text(display_name, "display_name", maximum=160)
    config_ref = _normalized_config_ref(provider_kind, config_ref)
    enabled_value = int(bool(enabled))
    existing = connection.execute(
        "SELECT * FROM external_source_instances WHERE instance_key = ?",
        (instance_key,),
    ).fetchone()
    if existing:
        existing = dict(existing)
        identity = (
            existing["provider_kind"],
            existing["service"],
            existing["config_ref"],
        )
        requested = (provider_kind, service, config_ref)
        if identity != requested:
            _deny(
                "source-instance-identity-conflict",
                "an existing instance_key cannot change provider, service, or config_ref",
            )
        connection.execute(
            """
            UPDATE external_source_instances
            SET display_name = ?, enabled = ?, updated_at = ?
            WHERE id = ?
            """,
            (display_name, enabled_value, _utc_now(), existing["id"]),
        )
        row_id = existing["id"]
    else:
        row_id = connection.execute(
            """
            INSERT INTO external_source_instances(
                instance_key, provider_kind, service, display_name,
                config_ref, enabled
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                instance_key,
                provider_kind,
                service,
                display_name,
                config_ref,
                enabled_value,
            ),
        ).lastrowid
    return dict(
        connection.execute(
            "SELECT * FROM external_source_instances WHERE id = ?", (row_id,)
        ).fetchone()
    )


def set_source_instance_enabled(
    connection, source_instance_id: int, enabled: bool
) -> dict:
    updated = connection.execute(
        """
        UPDATE external_source_instances
        SET enabled = ?, updated_at = ?
        WHERE id = ?
        """,
        (int(bool(enabled)), _utc_now(), source_instance_id),
    )
    if updated.rowcount != 1:
        _deny("source-instance-not-found", "Source Instance does not exist")
    return dict(
        connection.execute(
            "SELECT * FROM external_source_instances WHERE id = ?",
            (source_instance_id,),
        ).fetchone()
    )


def bind_source_instance_config_ref(
    connection, source_instance_id: int, config_ref: str
) -> dict:
    row = connection.execute(
        "SELECT * FROM external_source_instances WHERE id = ?",
        (source_instance_id,),
    ).fetchone()
    if not row:
        _deny("source-instance-not-found", "Source Instance does not exist")
    instance = dict(row)
    normalized = _normalized_config_ref(instance["provider_kind"], config_ref)
    if normalized is None:
        _deny("invalid-config-ref", "config_ref must be present")
    existing = instance["config_ref"]
    if existing is not None and existing != normalized:
        _deny(
            "source-instance-identity-conflict",
            "a bound Source Instance config_ref cannot be changed",
        )
    if existing is None:
        now = _utc_now()
        connection.execute(
            """
            UPDATE external_source_instances
            SET config_ref = ?, updated_at = ?
            WHERE id = ?
            """,
            (normalized, now, source_instance_id),
        )
        connection.execute(
            """
            UPDATE external_source_capabilities
            SET invalidated_at = ?, updated_at = ?
            WHERE source_instance_id = ?
              AND invalidated_at IS NULL
            """,
            (now, now, source_instance_id),
        )
    return dict(
        connection.execute(
            "SELECT * FROM external_source_instances WHERE id = ?",
            (source_instance_id,),
        ).fetchone()
    )


def _canonical_capability_json(operations: Iterable[str]) -> str:
    return json.dumps(
        {
            "schema": CAPABILITY_SCHEMA,
            "operations": sorted(set(operations)),
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def record_capability_observation(
    connection,
    source_instance_id: int,
    *,
    availability: str,
    operations: Iterable[str] = (),
    schema_fingerprint: Optional[str] = None,
    checked_at: Optional[str] = None,
    error_code: Optional[str] = None,
) -> dict:
    instance_row = connection.execute(
        "SELECT * FROM external_source_instances WHERE id = ?",
        (source_instance_id,),
    ).fetchone()
    if not instance_row:
        _deny("source-instance-not-found", "Source Instance does not exist")
    instance = dict(instance_row)
    if availability not in AVAILABILITY_VALUES:
        _deny("invalid-availability", "unsupported capability availability")
    if isinstance(operations, str):
        _deny("invalid-capabilities", "operations must be a collection")
    try:
        observed_operations = tuple(sorted(set(operations)))
    except TypeError:
        _deny("invalid-capabilities", "operations must contain only strings")
    if not all(isinstance(operation, str) for operation in observed_operations):
        _deny("invalid-capabilities", "operations must contain only strings")
    known = set(
        known_policy_operations(instance["provider_kind"], instance["service"])
    )
    unknown = set(observed_operations) - known
    if unknown:
        _deny(
            "operation-not-allowed",
            "observation contains unknown operations: " + ", ".join(sorted(unknown)),
        )
    if availability != "available" and observed_operations:
        _deny(
            "invalid-capabilities",
            "non-available observations cannot advertise operations",
        )
    if availability == "available":
        if not isinstance(schema_fingerprint, str) or not (
            SCHEMA_FINGERPRINT_PATTERN.fullmatch(schema_fingerprint)
        ):
            _deny(
                "invalid-schema-fingerprint",
                "available observations require a SHA-256 schema fingerprint",
            )
        error_code = None
    elif schema_fingerprint is not None and not (
        isinstance(schema_fingerprint, str)
        and SCHEMA_FINGERPRINT_PATTERN.fullmatch(schema_fingerprint)
    ):
        _deny(
            "invalid-schema-fingerprint",
            "schema_fingerprint must be a SHA-256 value",
        )
    if availability != "available":
        error_code = error_code or DEFAULT_ERROR_CODES[availability]
        if not isinstance(error_code, str) or not ERROR_CODE_PATTERN.fullmatch(
            error_code
        ):
            _deny("invalid-error-code", "error_code must be a bounded identifier")
        error_message = SAFE_ERROR_MESSAGES[availability]
    else:
        error_message = None
    checked_at = _bounded_text(
        checked_at or _utc_now(), "checked_at", maximum=80
    )
    capability_json = _canonical_capability_json(observed_operations)
    now = _utc_now()
    connection.execute(
        """
        INSERT INTO external_source_capabilities(
            source_instance_id, policy_version, schema_fingerprint,
            availability, capability_json, error_code, error_message,
            checked_at, invalidated_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
        ON CONFLICT(source_instance_id) DO UPDATE SET
            policy_version = excluded.policy_version,
            schema_fingerprint = excluded.schema_fingerprint,
            availability = excluded.availability,
            capability_json = excluded.capability_json,
            error_code = excluded.error_code,
            error_message = excluded.error_message,
            checked_at = excluded.checked_at,
            invalidated_at = NULL,
            updated_at = excluded.updated_at
        """,
        (
            source_instance_id,
            READ_POLICY_VERSION,
            schema_fingerprint,
            availability,
            capability_json,
            error_code,
            error_message,
            checked_at,
            now,
        ),
    )
    return capability_state(connection, source_instance_id)


def invalidate_capability_observation(
    connection,
    source_instance_id: int,
    *,
    invalidated_at: Optional[str] = None,
) -> dict:
    timestamp = _bounded_text(
        invalidated_at or _utc_now(), "invalidated_at", maximum=80
    )
    updated = connection.execute(
        """
        UPDATE external_source_capabilities
        SET invalidated_at = ?, updated_at = ?
        WHERE source_instance_id = ?
        """,
        (timestamp, _utc_now(), source_instance_id),
    )
    if updated.rowcount != 1:
        instance = connection.execute(
            "SELECT 1 FROM external_source_instances WHERE id = ?",
            (source_instance_id,),
        ).fetchone()
        if not instance:
            _deny("source-instance-not-found", "Source Instance does not exist")
        _deny("capability-observation-not-found", "Capability observation does not exist")
    return capability_state(connection, source_instance_id)


def _operations_from_json(
    capability_json: str, known_operations: Iterable[str]
) -> Tuple[str, ...]:
    try:
        payload = json.loads(capability_json)
    except (TypeError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, dict) or payload.get("schema") != CAPABILITY_SCHEMA:
        return ()
    operations = payload.get("operations")
    if not isinstance(operations, list) or not all(
        isinstance(item, str) for item in operations
    ):
        return ()
    return tuple(sorted(set(operations) & set(known_operations)))


def capability_state(connection, source_instance_id: int) -> dict:
    row = connection.execute(
        """
        SELECT external_source_instances.*,
               external_source_capabilities.policy_version,
               external_source_capabilities.schema_fingerprint,
               external_source_capabilities.availability,
               external_source_capabilities.capability_json,
               external_source_capabilities.error_code,
               external_source_capabilities.error_message,
               external_source_capabilities.checked_at,
               external_source_capabilities.invalidated_at
        FROM external_source_instances
        LEFT JOIN external_source_capabilities
          ON external_source_capabilities.source_instance_id =
             external_source_instances.id
        WHERE external_source_instances.id = ?
        """,
        (source_instance_id,),
    ).fetchone()
    if not row:
        _deny("source-instance-not-found", "Source Instance does not exist")
    value = dict(row)
    known = known_policy_operations(value["provider_kind"], value["service"])
    if not value["enabled"]:
        state = "disabled"
    elif value["policy_version"] is None:
        state = "unknown"
    elif value["invalidated_at"] is not None:
        state = "stale"
    elif value["policy_version"] != READ_POLICY_VERSION:
        state = "stale"
    elif value["availability"] == "available" and not (
        isinstance(value["schema_fingerprint"], str)
        and SCHEMA_FINGERPRINT_PATTERN.fullmatch(value["schema_fingerprint"])
    ):
        state = "error"
    elif value["availability"] in AVAILABILITY_VALUES:
        state = (
            "current"
            if value["availability"] == "available"
            else value["availability"]
        )
    else:
        state = "error"
    effective_operations = ()
    if state == "current":
        effective_operations = _operations_from_json(
            value["capability_json"], known
        )
        if value["capability_json"] != _canonical_capability_json(
            effective_operations
        ):
            state = "error"
            effective_operations = ()
    return {
        "source_instance_id": value["id"],
        "instance_key": value["instance_key"],
        "provider_kind": value["provider_kind"],
        "service": value["service"],
        "display_name": value["display_name"],
        "enabled": bool(value["enabled"]),
        "availability": value["availability"],
        "state": state,
        "policy_version": value["policy_version"],
        "schema_fingerprint": value["schema_fingerprint"],
        "checked_at": value["checked_at"],
        "invalidated_at": value["invalidated_at"],
        "error_code": value["error_code"],
        "error_message": value["error_message"],
        "effective_operations": effective_operations,
    }


def authorize_external_read(
    connection,
    source_instance_id: int,
    logical_operation: str,
    arguments: Mapping[str, Any],
) -> ToolDispatch:
    instance_row = connection.execute(
        "SELECT * FROM external_source_instances WHERE id = ?",
        (source_instance_id,),
    ).fetchone()
    if not instance_row:
        _deny("source-instance-not-found", "Source Instance does not exist")
    instance = dict(instance_row)
    policy = POLICIES.get((instance["provider_kind"], instance["service"]), {})
    operation = policy.get(logical_operation)
    if operation is None:
        _deny("operation-not-allowed", "logical operation is not in static policy")
    if not instance["enabled"]:
        _deny("capability-not-current", "Source Instance capability state is disabled")
    if logical_operation.startswith("capability."):
        provider_arguments = operation.argument_builder(arguments, instance)
        return ToolDispatch(
            source_instance_id=source_instance_id,
            logical_operation=logical_operation,
            tool_name=operation.tool_name,
            arguments=provider_arguments,
        )
    state = capability_state(connection, source_instance_id)
    if state["state"] != "current":
        _deny(
            "capability-not-current",
            f"Source Instance capability state is {state['state']}",
        )
    if logical_operation not in state["effective_operations"]:
        _deny(
            "capability-not-observed",
            "logical operation is not present in the current observation",
        )
    provider_arguments = operation.argument_builder(arguments, instance)
    if operation.gateway_target:
        provider_arguments = {
            "method": "tools/call",
            "name": operation.gateway_target,
            "arguments": provider_arguments,
        }
    return ToolDispatch(
        source_instance_id=source_instance_id,
        logical_operation=logical_operation,
        tool_name=operation.tool_name,
        arguments=provider_arguments,
    )
