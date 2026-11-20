use axum::{
    body::{to_bytes, Body},
    http::{HeaderMap, Method, StatusCode, Uri},
    response::{IntoResponse, Response},
    Json,
};
use localbrain_core::backend::{BackendError, Result};
use serde_json::{json, Map, Value};
use std::collections::{BTreeMap, BTreeSet};

pub struct ApiError(pub BackendError);
impl From<BackendError> for ApiError {
    fn from(error: BackendError) -> Self {
        Self(error)
    }
}
impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let BackendError {
            mut status,
            message,
            details,
            ..
        } = self.0;
        let mut detail = details
            .map(|value| *value)
            .unwrap_or(Value::String(message));
        if let Err(error) = localbrain_core::backend::json::validate_http_json(&detail) {
            status = error.status;
            detail = Value::String(error.message);
        }
        let mut body = Map::new();
        body.insert("detail".into(), detail);
        (
            StatusCode::from_u16(status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
            Json(Value::Object(body)),
        )
            .into_response()
    }
}

#[cfg(test)]
mod error_tests {
    use super::*;
    #[tokio::test]
    async fn structured_errors_keep_literal_objects_and_refuse_nonfinite_without_panicking() {
        for raw in [r#"{"nested":[NaN]}"#, r#"{"nested":[Infinity,-Infinity]}"#] {
            let detail = localbrain_core::backend::json::decode(raw).unwrap();
            let response =
                ApiError(BackendError::new(422, "synthetic", "invalid").with_details(detail))
                    .into_response();
            assert_eq!(response.status(), 500);
            let body = to_bytes(response.into_body(), 4096).await.unwrap();
            let value: Value = serde_json::from_slice(&body).unwrap();
            assert!(value["detail"].as_str().unwrap().contains("JSON"));
        }
        let detail = localbrain_core::backend::json::decode(
            r#"{"$serde_json::private::Number":{"literal":true}}"#,
        )
        .unwrap();
        let response =
            ApiError(BackendError::new(422, "synthetic", "invalid").with_details(detail.clone()))
                .into_response();
        assert_eq!(response.status(), 422);
        let body = to_bytes(response.into_body(), 4096).await.unwrap();
        let value =
            localbrain_core::backend::json::decode(std::str::from_utf8(&body).unwrap()).unwrap();
        assert_eq!(value["detail"], detail);
    }
}
pub type ApiResult<T> = std::result::Result<T, ApiError>;
pub fn redirect(location: &str) -> Response {
    let mut response = StatusCode::SEE_OTHER.into_response();
    match location.parse() {
        Ok(location) => {
            response.headers_mut().insert("location", location);
            response
        }
        Err(_) => {
            ApiError(BackendError::invalid("redirect", "Invalid redirect target")).into_response()
        }
    }
}
pub fn error(status: u16, message: &str) -> ApiError {
    ApiError(BackendError::new(status, "request", message))
}
pub fn decode_path(value: &str) -> String {
    let bytes = value.as_bytes();
    let mut result = Vec::new();
    let mut index = 0;
    let digit = |byte: u8| match byte {
        b'0'..=b'9' => Some(byte - b'0'),
        b'a'..=b'f' => Some(byte - b'a' + 10),
        b'A'..=b'F' => Some(byte - b'A' + 10),
        _ => None,
    };
    while index < bytes.len() {
        if bytes[index] == b'%' && index + 2 < bytes.len() {
            if let (Some(a), Some(b)) = (digit(bytes[index + 1]), digit(bytes[index + 2])) {
                result.push(a * 16 + b);
                index += 3;
                continue;
            }
        }
        result.push(bytes[index]);
        index += 1;
    }
    String::from_utf8_lossy(&result).into_owned()
}
#[derive(Clone)]
pub struct RequestContext {
    pub method: Method,
    pub headers: HeaderMap,
    pub uri: Uri,
    pub path: String,
    pub authority: String,
    pub origin: String,
    pub hostname: String,
    pub query: BTreeMap<String, String>,
}
impl RequestContext {
    pub fn new(method: Method, headers: HeaderMap, uri: Uri) -> Result<Self> {
        let header_host = headers.get("host").and_then(|h| h.to_str().ok());
        if uri
            .authority()
            .zip(header_host)
            .is_some_and(|(uri, header)| uri.as_str() != header)
        {
            return Err(BackendError::new(403, "local", "Local access required"));
        }
        let authority = header_host
            .or_else(|| uri.authority().map(|s| s.as_str()))
            .unwrap_or("")
            .to_owned();
        if authority.is_empty()
            || authority.chars().any(|ch| {
                ch.is_control() || ch.is_whitespace() || ['/', '\\', '?', '#'].contains(&ch)
            })
        {
            return Err(BackendError::new(403, "local", "Local access required"));
        }
        let origin = format!("http://{authority}");
        url::Url::parse(&origin)
            .map_err(|_| BackendError::new(403, "local", "Local access required"))?;
        // urllib's hostname preserves IPv4 spelling and IPv6 compression.
        // WHATWG parsing would widen the exact loopback allowlist by turning
        // 127.1, integer IPv4 and full-width names into accepted hosts.
        let host_port = authority.rsplit('@').next().unwrap_or("");
        let hostname = if let Some(bracketed) = host_port.strip_prefix('[') {
            bracketed
                .split_once(']')
                .map(|(host, _)| host)
                .unwrap_or("")
        } else {
            host_port.split(':').next().unwrap_or("")
        }
        .to_ascii_lowercase();
        let path = decode_path(uri.path());
        let mut query = BTreeMap::new();
        for (key, value) in url::form_urlencoded::parse(uri.query().unwrap_or("").as_bytes()) {
            query.insert(key.into_owned(), value.into_owned());
        }
        Ok(Self {
            method,
            headers,
            uri,
            path,
            authority,
            origin,
            hostname,
            query,
        })
    }
    pub fn header(&self, name: &str) -> &str {
        self.headers
            .get(name)
            .and_then(|v| v.to_str().ok())
            .unwrap_or("")
    }
    pub fn parameter(&self, name: &str) -> &str {
        self.query.get(name).map(String::as_str).unwrap_or("")
    }
    pub fn integer(&self, name: &str, default: i64) -> Result<i64> {
        self.query
            .get(name)
            .map(|value| {
                let literal = localbrain_core::backend::unicode::integer_literal(value)
                    .ok_or_else(|| {
                        BackendError::new(422, "query", format!("Invalid query parameter: {name}"))
                    })?;
                literal.parse::<i64>().map_err(|_| {
                    BackendError::new(500, "database", "Integer exceeds the database range")
                })
            })
            .unwrap_or(Ok(default))
    }
    pub fn same_origin(&self) -> bool {
        ["localhost", "127.0.0.1", "::1"].contains(&self.hostname.as_str())
            && self.header("origin") == self.origin
    }
    pub fn content_type(&self) -> &str {
        self.header("content-type")
            .split(';')
            .next()
            .unwrap_or("")
            .trim()
    }
    pub fn target(&self) -> String {
        format!(
            "{}{}",
            self.path,
            self.uri
                .query()
                .filter(|s| !s.is_empty())
                .map(|s| format!("?{s}"))
                .unwrap_or_default()
        )
    }
}
pub async fn bounded_body(body: Body, limit: usize) -> ApiResult<Vec<u8>> {
    to_bytes(body, limit)
        .await
        .map(|value| value.to_vec())
        .map_err(|_| error(413, "요청이 너무 큽니다."))
}
pub fn json_object(bytes: &[u8], status: u16, message: &str) -> ApiResult<Value> {
    let text = json_text(bytes).ok_or_else(|| error(status, message))?;
    let value =
        localbrain_core::backend::json::decode(&text).map_err(|_| error(status, message))?;
    if !value.is_object() {
        return Err(error(status, message));
    }
    Ok(value)
}
fn json_text(bytes: &[u8]) -> Option<String> {
    // Match json.loads(bytes) encoding detection, including UTF BOMs. Browser
    // requests normally take the single UTF-8 branch.
    let bytes = bytes.strip_prefix(b"\xef\xbb\xbf").unwrap_or(bytes);
    let (encoding, bytes) = if let Some(bytes) = bytes.strip_prefix(b"\0\0\xfe\xff") {
        (4, bytes)
    } else if let Some(bytes) = bytes.strip_prefix(b"\xff\xfe\0\0") {
        (5, bytes)
    } else if let Some(bytes) = bytes.strip_prefix(b"\xfe\xff") {
        (2, bytes)
    } else if let Some(bytes) = bytes.strip_prefix(b"\xff\xfe") {
        (3, bytes)
    } else if bytes.len() >= 4 && bytes[0] == 0 {
        (if bytes[1] == 0 { 4 } else { 2 }, bytes)
    } else if bytes.len() >= 4 && bytes[1] == 0 {
        (if bytes[2] == 0 && bytes[3] == 0 { 5 } else { 3 }, bytes)
    } else if bytes.len() == 2 && bytes[0] == 0 {
        (2, bytes)
    } else if bytes.len() == 2 && bytes[1] == 0 {
        (3, bytes)
    } else {
        (1, bytes)
    };
    match encoding {
        1 => std::str::from_utf8(bytes).ok().map(str::to_owned),
        2 | 3 => {
            if bytes.len() % 2 != 0 {
                return None;
            }
            char::decode_utf16(bytes.chunks_exact(2).map(|part| {
                if encoding == 2 {
                    u16::from_be_bytes([part[0], part[1]])
                } else {
                    u16::from_le_bytes([part[0], part[1]])
                }
            }))
            .collect::<std::result::Result<String, _>>()
            .ok()
        }
        _ => {
            if bytes.len() % 4 != 0 {
                return None;
            }
            bytes
                .chunks_exact(4)
                .map(|part| {
                    char::from_u32(if encoding == 4 {
                        u32::from_be_bytes(part.try_into().unwrap())
                    } else {
                        u32::from_le_bytes(part.try_into().unwrap())
                    })
                })
                .collect()
        }
    }
}
pub fn form(
    bytes: &[u8],
    max_fields: usize,
    multiple: &BTreeSet<&str>,
    allowed: Option<&BTreeSet<&str>>,
    duplicates: bool,
    strict: bool,
) -> ApiResult<Value> {
    let text = std::str::from_utf8(bytes).map_err(|_| error(400, "Invalid form"))?;
    if !text.is_empty() && text.split('&').count() > max_fields {
        return Err(error(400, "Invalid form"));
    }
    if strict {
        for part in text.split('&').flat_map(|part| part.splitn(2, '=')) {
            let bytes = part.as_bytes();
            let mut output = Vec::new();
            let mut index = 0;
            while index < bytes.len() {
                if bytes[index] == b'%' && index + 2 < bytes.len() {
                    let digit = |byte: u8| (byte as char).to_digit(16).map(|value| value as u8);
                    if let (Some(a), Some(b)) = (digit(bytes[index + 1]), digit(bytes[index + 2])) {
                        output.push(a * 16 + b);
                        index += 3;
                        continue;
                    }
                }
                output.push(bytes[index]);
                index += 1;
            }
            if std::str::from_utf8(&output).is_err() {
                return Err(error(400, "Invalid form"));
            }
        }
    }
    let mut values: Map<String, Value> = Map::new();
    for (key, value) in url::form_urlencoded::parse(text.as_bytes()) {
        if allowed.is_some_and(|allowed| !allowed.contains(key.as_ref()))
            || (!duplicates && values.contains_key(key.as_ref()))
        {
            return Err(error(400, "Invalid form fields"));
        }
        if multiple.contains(key.as_ref()) {
            values
                .entry(key.into_owned())
                .or_insert_with(|| json!([]))
                .as_array_mut()
                .unwrap()
                .push(json!(value));
        } else {
            values.insert(key.into_owned(), json!(value));
        }
    }
    Ok(Value::Object(values))
}
