//! Version-controlled operation mapping. This module never dispatches a tool.
use super::common::*;
use crate::backend::{db, Result};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeSet;

pub const READ_POLICY_VERSION: &str = "localbrain.atlassian-read-policy.v1";
pub const CAPABILITY_SCHEMA: &str = "localbrain.external-capabilities.v1";
pub const PROVIDER_MCP_GATEWAY: &str = "mcp_gateway";
pub const PROVIDER_ATLASSIAN_CLOUD: &str = "atlassian_cloud";
pub const SERVICE_JIRA: &str = "jira";
pub const SERVICE_CONFLUENCE: &str = "confluence";
pub const JIRA_METADATA_FIELDS: &[&str] = &[
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
];
pub const JIRA_DESCRIPTION_FIELDS: &[&str] = &["key", "description", "updated"];
const AVAILABILITY: &[&str] = &["available", "unavailable", "unauthorized", "error"];
const KEY: &str = r"\A[a-z0-9][a-z0-9._-]{0,127}\z";
const UUID: &str =
    r"(?i)\A[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\z";
const JIRA_KEY: &str = r"\A[A-Z][A-Z0-9_]*-[1-9][0-9]*\z";
pub(super) const HASH: &str = r"\A[0-9a-f]{64}\z";
pub(super) const ERROR_CODE: &str = r"\A[a-z0-9][a-z0-9._-]{0,79}\z";

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ToolDispatch {
    pub source_instance_id: i64,
    pub logical_operation: String,
    pub tool_name: String,
    pub arguments: Value,
    pub policy_version: String,
}
#[derive(Clone, Copy)]
struct Policy {
    operation: &'static str,
    tool: &'static str,
    target: Option<&'static str>,
}
fn policies(provider: &str, service: &str) -> Option<Vec<Policy>> {
    let gateway = provider == PROVIDER_MCP_GATEWAY;
    if !gateway && provider != PROVIDER_ATLASSIAN_CLOUD
        || ![SERVICE_JIRA, SERVICE_CONFLUENCE].contains(&service)
    {
        return None;
    }
    let mut values = if gateway {
        vec![
            Policy {
                operation: "capability.list_tools",
                tool: "mcp_gateway.gateway_list",
                target: None,
            },
            Policy {
                operation: "capability.describe_tools",
                tool: "mcp_gateway.gateway_describe",
                target: None,
            },
        ]
    } else {
        vec![Policy {
            operation: "capability.inspect_resources",
            tool: "atlassian.getAccessibleAtlassianResources",
            target: None,
        }]
    };
    let operations: &[(&str, &str, &str)] = match (gateway, service) {
        (true, SERVICE_JIRA) => &[
            (
                "jira.search_metadata",
                "mcp_gateway.gateway_dispatch",
                "jira__searchIssuesByJql",
            ),
            (
                "jira.read_description",
                "mcp_gateway.gateway_dispatch",
                "jira__searchIssuesByJql",
            ),
            (
                "jira.read_project",
                "mcp_gateway.gateway_dispatch",
                "jira__getProjectDetails",
            ),
        ],
        (true, _) => &[
            (
                "confluence.search_pages",
                "mcp_gateway.gateway_dispatch",
                "wiki__searchWiki",
            ),
            (
                "confluence.read_page",
                "mcp_gateway.gateway_dispatch",
                "wiki__getPageById",
            ),
            (
                "confluence.list_children",
                "mcp_gateway.gateway_dispatch",
                "wiki__getChildPages",
            ),
        ],
        (false, SERVICE_JIRA) => &[
            (
                "jira.search_metadata",
                "atlassian.searchJiraIssuesUsingJql",
                "",
            ),
            (
                "jira.read_description",
                "atlassian.searchJiraIssuesUsingJql",
                "",
            ),
        ],
        (false, _) => &[
            (
                "confluence.search_pages",
                "atlassian.searchConfluenceUsingCql",
                "",
            ),
            ("confluence.read_page", "atlassian.getConfluencePage", ""),
            (
                "confluence.list_children",
                "atlassian.searchConfluenceUsingCql",
                "",
            ),
        ],
    };
    values.extend(operations.iter().map(|(operation, tool, target)| Policy {
        operation,
        tool,
        target: (!target.is_empty()).then_some(*target),
    }));
    Some(values)
}
pub fn policy_manifest() -> Value {
    let mut providers = vec![];
    for provider in [PROVIDER_ATLASSIAN_CLOUD, PROVIDER_MCP_GATEWAY] {
        for service in [SERVICE_CONFLUENCE, SERVICE_JIRA] {
            let mut policies = policies(provider, service).unwrap();
            policies.sort_by_key(|p| p.operation);
            providers.push(json!({"provider_kind":provider,"service":service,"operations":policies.iter().map(|p|json!({"logical_operation":p.operation,"tool_name":p.tool,"gateway_target":p.target})).collect::<Vec<_>>()}));
        }
    }
    json!({"schema":"localbrain.external-read-policy.v1","version":READ_POLICY_VERSION,"providers":providers})
}
pub fn known_policy_operations(provider: &str, service: &str) -> Result<Vec<String>> {
    let mut operations: Vec<_> = policies(provider, service)
        .ok_or_else(|| {
            fail(
                "unsupported-source-instance",
                "unsupported provider/service pair",
            )
        })?
        .into_iter()
        .map(|p| p.operation.to_owned())
        .collect();
    operations.sort();
    Ok(operations)
}
pub fn normalized_config_ref(provider: &str, value: &Value) -> Result<Option<String>> {
    let Some(value) = optional_text(value, "config_ref", 300, "invalid-argument")? else {
        return Ok(None);
    };
    match provider {
        PROVIDER_MCP_GATEWAY if matches(KEY, &value) => Ok(Some(value)),
        PROVIDER_MCP_GATEWAY => Err(fail(
            "invalid-config-ref",
            "Gateway config_ref must be a bounded configuration alias",
        )),
        PROVIDER_ATLASSIAN_CLOUD if matches(UUID, &value) => Ok(Some(value.to_ascii_lowercase())),
        PROVIDER_ATLASSIAN_CLOUD => Err(fail(
            "invalid-config-ref",
            "Atlassian config_ref must be a Cloud ID",
        )),
        _ => Err(fail(
            "invalid-config-ref",
            "unsupported provider config_ref",
        )),
    }
}
fn config_ref(instance: &Value) -> Result<String> {
    normalized_config_ref(
        instance["provider_kind"].as_str().unwrap_or(""),
        &instance["config_ref"],
    )?
    .ok_or_else(|| {
        fail(
            "missing-config-ref",
            "the Source Instance has no external configuration reference",
        )
    })
}
fn arguments(value: &Value, required: &[&str], optional: &[&str]) -> Result<()> {
    let object = value
        .as_object()
        .ok_or_else(|| fail("invalid-argument", "arguments must be an object"))?;
    let mut missing: Vec<_> = required
        .iter()
        .filter(|key| !object.contains_key(**key))
        .copied()
        .collect();
    missing.sort();
    if !missing.is_empty() {
        return Err(fail(
            "invalid-argument",
            format!("missing arguments: {}", missing.join(", ")),
        ));
    }
    let mut extra: Vec<_> = object
        .keys()
        .filter(|key| !required.contains(&key.as_str()) && !optional.contains(&key.as_str()))
        .cloned()
        .collect();
    extra.sort();
    if !extra.is_empty() {
        return Err(fail(
            "invalid-argument",
            format!("unsupported arguments: {}", extra.join(", ")),
        ));
    }
    Ok(())
}
fn fields(value: &Value, allowed: &[&str]) -> Result<Vec<String>> {
    if value.is_null() {
        return Ok(allowed.iter().map(|s| (*s).into()).collect());
    }
    let selected = value
        .as_array()
        .filter(|a| !a.is_empty())
        .ok_or_else(|| fail("invalid-argument", "fields must be a non-empty list"))?;
    let mut result = vec![];
    for field in selected {
        let Some(field) = field.as_str().filter(|s| allowed.contains(s)) else {
            return Err(fail(
                "field-not-allowed",
                format!("field is not allowed: {}", python_string(field)),
            ));
        };
        if !result.iter().any(|s| s == field) {
            result.push(field.to_owned());
        }
    }
    Ok(result)
}
fn argument_text(value: &Value, field: &str, limit: usize) -> Result<String> {
    text(&value[field], field, limit, "invalid-argument")
}
fn integer(value: &Value, field: &str, minimum: i64, maximum: i64, default: i64) -> Result<i64> {
    bounded_integer(
        &value[field],
        field,
        minimum,
        maximum,
        default,
        "invalid-argument",
    )
}
fn issue_key(value: &Value) -> Result<String> {
    let key = crate::backend::unicode::uppercase(&argument_text(value, "issue_key", 80)?);
    if !matches(JIRA_KEY, &key) {
        return Err(fail(
            "invalid-argument",
            "issue_key is not a valid Jira key",
        ));
    }
    Ok(key)
}
fn jql(value: &Value) -> Result<String> {
    let value = argument_text(value, "jql", 4000)?;
    if query_matches(r"(?i)\b(comment|worklog|attachment|development)\b", &value) {
        return Err(fail(
            "field-not-allowed",
            "JQL cannot inspect comments, worklogs, attachments, or development data",
        ));
    }
    Ok(value)
}
fn cql(value: &Value) -> Result<String> {
    let value = argument_text(value, "cql", 4000)?;
    if !query_matches(r#"(?i)\btype\s*=\s*(?:"page"|'page'|page)\b"#, &value) {
        return Err(fail(
            "content-type-not-allowed",
            "CQL must explicitly select type = page",
        ));
    }
    if query_matches(
        r#"(?i)\btype\s*=\s*(?:"(?:comment|attachment|blogpost)"|'(?:comment|attachment|blogpost)'|comment|attachment|blogpost)\b"#,
        &value,
    ) {
        return Err(fail(
            "content-type-not-allowed",
            "CQL includes an excluded content type",
        ));
    }
    Ok(format!("({value}) AND type = page"))
}
fn query_matches(pattern: &str, value: &str) -> bool {
    // Policy patterns contain ASCII words, whitespace and punctuation. Project
    // other characters through Python14's categories so newer regex Unicode
    // tables cannot hide an excluded field at a word boundary. IGNORECASE has
    // four additional ASCII-letter equivalences.
    let projected: String = value
        .chars()
        .map(|ch| {
            if crate::backend::unicode::python_space(ch) {
                ' '
            } else if ch.is_ascii() {
                ch.to_ascii_lowercase()
            } else {
                match ch {
                    '\u{17f}' => 's',
                    '\u{212a}' => 'k',
                    '\u{130}' | '\u{131}' => 'i',
                    _ if crate::backend::unicode::python_alnum(ch) => 'x',
                    _ => '!',
                }
            }
        })
        .collect();
    matches(pattern, &projected)
}
fn build_arguments(operation: &str, value: &Value, instance: &Value) -> Result<Value> {
    let gateway = instance["provider_kind"] == PROVIDER_MCP_GATEWAY;
    let jira = instance["service"] == SERVICE_JIRA;
    let server = if jira { "jira" } else { "wiki" };
    let mut result = match operation {
        "capability.list_tools" => {
            arguments(value, &[], &[])?;
            json!({"kind":"tool","server":server})
        }
        "capability.describe_tools" => {
            arguments(value, &["names"], &[])?;
            let names = value["names"]
                .as_array()
                .filter(|v| (1..=50).contains(&v.len()))
                .ok_or_else(|| {
                    fail(
                        "invalid-argument",
                        "names must contain between 1 and 50 tools",
                    )
                })?;
            let mut items = vec![];
            for name in names {
                let name = name
                    .as_str()
                    .filter(|s| s.starts_with(&format!("{server}__")))
                    .ok_or_else(|| {
                        fail(
                            "tool-not-allowed",
                            "tool name is outside this Source Instance",
                        )
                    })?;
                items.push(json!({"kind":"tool","name":name}));
            }
            json!({"items":items})
        }
        "capability.inspect_resources" => {
            arguments(value, &[], &[])?;
            json!({})
        }
        "jira.search_metadata" => {
            arguments(
                value,
                &["jql"],
                if gateway {
                    &["fields", "limit", "offset"]
                } else {
                    &["fields", "limit", "cursor"]
                },
            )?;
            let selected = fields(&value["fields"], JIRA_METADATA_FIELDS)?;
            if gateway {
                json!({"jql":jql(value)?,"fields":selected.join(","),"maxResults":integer(value,"limit",1,100,20)?,"startAt":integer(value,"offset",0,1000000,0)?})
            } else {
                json!({"cloudId":config_ref(instance)?,"jql":jql(value)?,"fields":selected,"maxResults":integer(value,"limit",1,100,50)?,"searchResultMode":"issues"})
            }
        }
        "jira.read_description" => {
            arguments(
                value,
                &["issue_key"],
                if gateway { &[] } else { &["content_format"] },
            )?;
            let key = issue_key(value)?;
            if gateway {
                json!({"jql":format!("key = \"{key}\""),"fields":JIRA_DESCRIPTION_FIELDS.join(","),"maxResults":1,"startAt":0})
            } else {
                let format = value.get("content_format").unwrap_or(&Value::Null);
                let format = if format.is_null()
                    && !value.as_object().unwrap().contains_key("content_format")
                {
                    json!("adf")
                } else {
                    format.clone()
                };
                if ![json!("adf"), json!("markdown")].contains(&format) {
                    return Err(fail("invalid-argument", "unsupported Jira content format"));
                }
                json!({"cloudId":config_ref(instance)?,"jql":format!("key = \"{key}\""),"fields":JIRA_DESCRIPTION_FIELDS,"maxResults":1,"responseContentFormat":format,"searchResultMode":"issues"})
            }
        }
        "jira.read_project" => {
            arguments(value, &["project_id_or_key"], &[])?;
            json!({"projectIdOrKey":argument_text(value,"project_id_or_key",100)?})
        }
        "confluence.search_pages" => {
            arguments(
                value,
                &["cql"],
                if gateway {
                    &["limit", "offset"]
                } else {
                    &["limit", "cursor"]
                },
            )?;
            if gateway {
                json!({"cql":cql(value)?,"limit":integer(value,"limit",1,200,25)?,"start":integer(value,"offset",0,1000000,0)?,"expand":"title,excerpt,space.key,version"})
            } else {
                json!({"cloudId":config_ref(instance)?,"cql":cql(value)?,"limit":integer(value,"limit",1,250,25)?})
            }
        }
        "confluence.read_page" => {
            arguments(
                value,
                &["page_id"],
                if gateway { &[] } else { &["content_format"] },
            )?;
            if gateway {
                json!({"pageId":argument_text(value,"page_id",200)?,"expand":"body.view,version,space.key,ancestors,metadata.labels"})
            } else {
                let format = value
                    .get("content_format")
                    .cloned()
                    .unwrap_or(json!("html"));
                if ![json!("html"), json!("markdown"), json!("adf")].contains(&format) {
                    return Err(fail(
                        "invalid-argument",
                        "unsupported Confluence content format",
                    ));
                }
                json!({"cloudId":config_ref(instance)?,"pageId":argument_text(value,"page_id",200)?,"contentType":"page","contentFormat":format})
            }
        }
        "confluence.list_children" => {
            arguments(
                value,
                &["page_id"],
                if gateway { &[] } else { &["limit", "cursor"] },
            )?;
            let page = argument_text(value, "page_id", 200)?;
            if gateway {
                json!({"pageId":page,"expand":"title,space.key,version"})
            } else {
                json!({"cloudId":config_ref(instance)?,"cql":format!("parent = \"{page}\" AND type = page"),"limit":integer(value,"limit",1,250,25)?})
            }
        }
        _ => {
            return Err(fail(
                "operation-not-allowed",
                "logical operation is not in static policy",
            ))
        }
    };
    if !gateway
        && [
            "jira.search_metadata",
            "confluence.search_pages",
            "confluence.list_children",
        ]
        .contains(&operation)
        && !value["cursor"].is_null()
    {
        result[if jira { "nextPageToken" } else { "cursor" }] =
            json!(argument_text(value, "cursor", 2000)?);
    }
    Ok(result)
}

fn instance(connection: &Connection, source: i64) -> Result<Value> {
    required_row(
        connection,
        "SELECT * FROM external_source_instances WHERE id = ?",
        [source],
        "source-instance-not-found",
        "Source Instance does not exist",
    )
}
pub fn register_source_instance(connection: &Connection, values: &Value) -> Result<Value> {
    let key = values["instance_key"]
        .as_str()
        .filter(|s| matches(KEY, s))
        .ok_or_else(|| fail("invalid-instance-key", "instance_key has an invalid shape"))?;
    let provider = values["provider_kind"].as_str().unwrap_or("");
    let service = values["service"].as_str().unwrap_or("");
    known_policy_operations(provider, service)?;
    let display = argument_text(values, "display_name", 160)?;
    let config = normalized_config_ref(provider, &values["config_ref"])?;
    let enabled = values.get("enabled").is_none_or(truth);
    let id = if let Some(existing) = db::row(
        connection,
        "SELECT * FROM external_source_instances WHERE instance_key = ?",
        [key],
    )? {
        if existing["provider_kind"] != provider
            || existing["service"] != service
            || existing["config_ref"] != json!(config)
        {
            return Err(fail(
                "source-instance-identity-conflict",
                "an existing instance_key cannot change provider, service, or config_ref",
            ));
        }
        let id = id(&existing["id"])?;
        connection.execute("UPDATE external_source_instances SET display_name = ?, enabled = ?, updated_at = ? WHERE id = ?",params![display,enabled,access_now(),id])?;
        id
    } else {
        connection.execute("INSERT INTO external_source_instances(instance_key,provider_kind,service,display_name,config_ref,enabled) VALUES (?,?,?,?,?,?)",params![key,provider,service,display,config,enabled])?;
        connection.last_insert_rowid()
    };
    instance(connection, id)
}
pub fn set_source_instance_enabled(
    connection: &Connection,
    source: i64,
    enabled: bool,
) -> Result<Value> {
    if connection.execute(
        "UPDATE external_source_instances SET enabled = ?, updated_at = ? WHERE id = ?",
        params![enabled, access_now(), source],
    )? != 1
    {
        return Err(fail(
            "source-instance-not-found",
            "Source Instance does not exist",
        ));
    }
    instance(connection, source)
}
pub fn bind_source_instance_config_ref(
    connection: &Connection,
    source: i64,
    value: &Value,
) -> Result<Value> {
    let row = instance(connection, source)?;
    let normalized = normalized_config_ref(row["provider_kind"].as_str().unwrap_or(""), value)?
        .ok_or_else(|| fail("invalid-config-ref", "config_ref must be present"))?;
    if !row["config_ref"].is_null() && row["config_ref"] != normalized {
        return Err(fail(
            "source-instance-identity-conflict",
            "a bound Source Instance config_ref cannot be changed",
        ));
    }
    if row["config_ref"].is_null() {
        let now = access_now();
        connection.execute(
            "UPDATE external_source_instances SET config_ref = ?,updated_at = ? WHERE id = ?",
            params![normalized, now, source],
        )?;
        connection.execute("UPDATE external_source_capabilities SET invalidated_at = ?,updated_at = ? WHERE source_instance_id = ? AND invalidated_at IS NULL",params![now,now,source])?;
    }
    instance(connection, source)
}
fn capability_json(operations: impl IntoIterator<Item = String>) -> String {
    let operations: BTreeSet<_> = operations.into_iter().collect();
    // Both keys and every permitted operation are ASCII.
    format!(
        "{{\"operations\":{},\"schema\":\"{CAPABILITY_SCHEMA}\"}}",
        serde_json::to_string(&operations).unwrap()
    )
}
pub fn record_capability_observation(
    connection: &Connection,
    source: i64,
    values: &Value,
) -> Result<Value> {
    let row = instance(connection, source)?;
    let availability = values["availability"]
        .as_str()
        .filter(|s| AVAILABILITY.contains(s))
        .ok_or_else(|| {
            fail(
                "invalid-availability",
                "unsupported capability availability",
            )
        })?;
    let operations: BTreeSet<String> = match values.get("operations") {
        None => BTreeSet::new(),
        Some(Value::Object(values)) => values.keys().cloned().collect(),
        Some(Value::Array(values)) => values
            .iter()
            .map(|value| {
                value.as_str().map(ToOwned::to_owned).ok_or_else(|| {
                    fail(
                        "invalid-capabilities",
                        "operations must contain only strings",
                    )
                })
            })
            .collect::<Result<_>>()?,
        Some(Value::String(_)) => {
            return Err(fail(
                "invalid-capabilities",
                "operations must be a collection",
            ))
        }
        Some(_) => {
            return Err(fail(
                "invalid-capabilities",
                "operations must contain only strings",
            ))
        }
    };
    let known = known_policy_operations(
        row["provider_kind"].as_str().unwrap_or(""),
        row["service"].as_str().unwrap_or(""),
    )?;
    let unknown: Vec<_> = operations
        .iter()
        .filter(|s| !known.contains(s))
        .cloned()
        .collect();
    if !unknown.is_empty() {
        return Err(fail(
            "operation-not-allowed",
            format!(
                "observation contains unknown operations: {}",
                unknown.join(", ")
            ),
        ));
    }
    if availability != "available" && !operations.is_empty() {
        return Err(fail(
            "invalid-capabilities",
            "non-available observations cannot advertise operations",
        ));
    }
    let fingerprint = values["schema_fingerprint"].as_str();
    if availability == "available" && !fingerprint.is_some_and(|s| matches(HASH, s)) {
        return Err(fail(
            "invalid-schema-fingerprint",
            "available observations require a SHA-256 schema fingerprint",
        ));
    }
    if availability != "available"
        && !values["schema_fingerprint"].is_null()
        && !fingerprint.is_some_and(|s| matches(HASH, s))
    {
        return Err(fail(
            "invalid-schema-fingerprint",
            "schema_fingerprint must be a SHA-256 value",
        ));
    }
    let (error, message) = if availability == "available" {
        (None, None)
    } else {
        let (default, message) = match availability {
            "unavailable" => ("service-unavailable", "External capability is unavailable."),
            "unauthorized" => (
                "authorization-unavailable",
                "External capability authorization is unavailable.",
            ),
            _ => (
                "inspection-failed",
                "External capability inspection failed.",
            ),
        };
        let error = if truth(&values["error_code"]) {
            values["error_code"]
                .as_str()
                .filter(|s| matches(ERROR_CODE, s))
                .ok_or_else(|| {
                    fail(
                        "invalid-error-code",
                        "error_code must be a bounded identifier",
                    )
                })?
        } else {
            default
        };
        (Some(error), Some(message))
    };
    let checked = if truth(&values["checked_at"]) {
        argument_text(values, "checked_at", 80)?
    } else {
        access_now()
    };
    let now = access_now();
    connection.execute("INSERT INTO external_source_capabilities(source_instance_id,policy_version,schema_fingerprint,availability,capability_json,error_code,error_message,checked_at,invalidated_at,updated_at) VALUES (?,?,?,?,?,?,?,?,NULL,?) ON CONFLICT(source_instance_id) DO UPDATE SET policy_version=excluded.policy_version,schema_fingerprint=excluded.schema_fingerprint,availability=excluded.availability,capability_json=excluded.capability_json,error_code=excluded.error_code,error_message=excluded.error_message,checked_at=excluded.checked_at,invalidated_at=NULL,updated_at=excluded.updated_at",params![source,READ_POLICY_VERSION,fingerprint,availability,capability_json(operations),error,message,checked,now])?;
    capability_state(connection, source)
}
pub fn invalidate_capability_observation(
    connection: &Connection,
    source: i64,
    invalidated_at: Option<&str>,
) -> Result<Value> {
    let timestamp = match invalidated_at.filter(|s| !s.is_empty()) {
        Some(value) => text(&json!(value), "invalidated_at", 80, "invalid-argument")?,
        None => access_now(),
    };
    if connection.execute("UPDATE external_source_capabilities SET invalidated_at = ?,updated_at = ? WHERE source_instance_id = ?",params![timestamp,access_now(),source])?!=1{instance(connection,source)?;return Err(fail("capability-observation-not-found","Capability observation does not exist"));}
    capability_state(connection, source)
}
pub fn capability_state(connection: &Connection, source: i64) -> Result<Value> {
    let value=required_row(connection,"SELECT external_source_instances.*,external_source_capabilities.policy_version,external_source_capabilities.schema_fingerprint,external_source_capabilities.availability,external_source_capabilities.capability_json,external_source_capabilities.error_code,external_source_capabilities.error_message,external_source_capabilities.checked_at,external_source_capabilities.invalidated_at FROM external_source_instances LEFT JOIN external_source_capabilities ON external_source_capabilities.source_instance_id = external_source_instances.id WHERE external_source_instances.id = ?",[source],"source-instance-not-found","Source Instance does not exist")?;
    let known = known_policy_operations(
        value["provider_kind"].as_str().unwrap_or(""),
        value["service"].as_str().unwrap_or(""),
    )?;
    let availability = value["availability"].as_str().unwrap_or("");
    let mut state = if !truth(&value["enabled"]) {
        "disabled"
    } else if value["policy_version"].is_null() {
        "unknown"
    } else if !value["invalidated_at"].is_null() || value["policy_version"] != READ_POLICY_VERSION {
        "stale"
    } else if availability == "available"
        && !value["schema_fingerprint"]
            .as_str()
            .is_some_and(|s| matches(HASH, s))
    {
        "error"
    } else if AVAILABILITY.contains(&availability) {
        if availability == "available" {
            "current"
        } else {
            availability
        }
    } else {
        "error"
    };
    let mut effective = BTreeSet::new();
    if state == "current" {
        if let Some(payload) = value["capability_json"]
            .as_str()
            .and_then(|s| serde_json::from_str::<Value>(s).ok())
            .filter(|v| v["schema"] == CAPABILITY_SCHEMA)
        {
            if let Some(operations) = payload["operations"]
                .as_array()
                .filter(|v| v.iter().all(Value::is_string))
            {
                for item in operations {
                    let name = item.as_str().unwrap().to_owned();
                    if known.contains(&name) {
                        effective.insert(name);
                    }
                }
            }
        }
        if value["capability_json"] != capability_json(effective.iter().cloned()) {
            state = "error";
            effective.clear();
        }
    }
    let mut result = json!({"source_instance_id":value["id"],"state":state,"enabled":truth(&value["enabled"]),"effective_operations":effective});
    for key in [
        "instance_key",
        "provider_kind",
        "service",
        "display_name",
        "availability",
        "policy_version",
        "schema_fingerprint",
        "checked_at",
        "invalidated_at",
        "error_code",
        "error_message",
    ] {
        result[key] = value[key].clone();
    }
    Ok(result)
}
pub fn authorize_external_read(
    connection: &Connection,
    source: i64,
    operation: &str,
    value: &Value,
) -> Result<ToolDispatch> {
    let instance = instance(connection, source)?;
    let policy = policies(
        instance["provider_kind"].as_str().unwrap_or(""),
        instance["service"].as_str().unwrap_or(""),
    )
    .and_then(|v| v.into_iter().find(|p| p.operation == operation))
    .ok_or_else(|| {
        fail(
            "operation-not-allowed",
            "logical operation is not in static policy",
        )
    })?;
    if !truth(&instance["enabled"]) {
        return Err(fail(
            "capability-not-current",
            "Source Instance capability state is disabled",
        ));
    }
    if !operation.starts_with("capability.") {
        let state = capability_state(connection, source)?;
        if state["state"] != "current" {
            return Err(fail(
                "capability-not-current",
                format!(
                    "Source Instance capability state is {}",
                    state["state"].as_str().unwrap_or("error")
                ),
            ));
        }
        if !state["effective_operations"]
            .as_array()
            .is_some_and(|v| v.contains(&json!(operation)))
        {
            return Err(fail(
                "capability-not-observed",
                "logical operation is not present in the current observation",
            ));
        }
    }
    let mut built = build_arguments(operation, value, &instance)?;
    if let Some(target) = policy.target {
        built = json!({"method":"tools/call","name":target,"arguments":built});
    }
    Ok(ToolDispatch {
        source_instance_id: source,
        logical_operation: operation.into(),
        tool_name: policy.tool.into(),
        arguments: built,
        policy_version: READ_POLICY_VERSION.into(),
    })
}
