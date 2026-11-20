use crate::backend::{db, Result};
use rusqlite::Connection;
use serde_json::{json, Value};

pub const MAX_SOURCE_ID: i64 = (1_i64 << 53) - 1;
pub const PALETTE: [&str; 6] = ["green", "blue", "orange", "yellow", "red", "gray"];
pub fn palette() -> Result<Vec<Value>> {
    PALETTE.iter().map(|color|Ok(json!({"value":color,"label":crate::backend::value_registry::visible_value_label("source.profile-color",&json!(color),None)?}))).collect()
}
pub fn valid_source_id(value: &Value) -> bool {
    value
        .as_i64()
        .is_some_and(|value| value > 0 && value <= MAX_SOURCE_ID)
}
pub fn default_color(provider: &str) -> &'static str {
    match provider {
        "codex" => "green",
        "claude" => "orange",
        _ => "gray",
    }
}
pub fn valid_color(value: &str) -> bool {
    PALETTE.contains(&value)
}
pub fn profiles(connection: &Connection) -> Result<Vec<Value>> {
    db::rows(connection, "SELECT id,provider_kind,name,root_path,profile_color,profile_position FROM sources WHERE provider_kind IN ('codex','claude') ORDER BY profile_position,id", [])
}
pub fn profile_map(connection: &Connection) -> Result<Value> {
    Ok(Value::Object(profiles(connection)?.into_iter().map(|row| (row["id"].to_string(), json!({"id":row["id"],"name":row["name"],"provider_kind":row["provider_kind"],"color":row["profile_color"].as_str().unwrap_or_else(||default_color(row["provider_kind"].as_str().unwrap_or("")))}))).collect()))
}
pub fn canonical_source_id(value: &str) -> String {
    if value == "all" {
        return value.into();
    }
    if let Some(id) = decimal_integer(value) {
        if id > 0 && id <= MAX_SOURCE_ID {
            return id.to_string();
        }
    }
    "invalid".into()
}

pub use crate::backend::unicode::decimal_integer;
