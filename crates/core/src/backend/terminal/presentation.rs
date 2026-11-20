//! Shared tab order is metadata; live processes remain manager-owned.
use crate::{
    backend::{BackendError, Result},
    files,
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    os::unix::fs::{MetadataExt, PermissionsExt},
    path::{Path, PathBuf},
};
fn invalid(message: &str) -> BackendError {
    BackendError::conflict(message)
}
fn path(root: &Path) -> Result<PathBuf> {
    let info = std::fs::symlink_metadata(root)?;
    if !info.is_dir()
        || info.uid() != unsafe { libc::getuid() }
        || info.permissions().mode() & 0o077 != 0
    {
        return Err(invalid("탭 순서 저장 위치를 확인해 주세요."));
    }
    Ok(root.join("view-order.json"))
}
fn generation(value: &str) -> bool {
    value.len() == 32
        && value
            .bytes()
            .all(|ch| ch.is_ascii_digit() || (b'a'..=b'f').contains(&ch))
}
fn read(root: &Path) -> Result<Option<Value>> {
    let path = path(root)?;
    let value = files::read_json(&path, 16 * 1024)
        .map_err(|_| invalid("저장한 탭 순서를 읽을 수 없습니다."))?;
    if let Some(value) = &value {
        let valid = value.as_object().is_some_and(|object| {
            object.len() == 3
                && object
                    .keys()
                    .all(|key| ["schema", "generation", "tabs"].contains(&key.as_str()))
        }) && value["schema"].as_i64() == Some(1)
            && value["generation"].as_str().is_some_and(generation)
            && value["tabs"].as_array().is_some_and(|tabs| {
                tabs.len() <= 32
                    && tabs
                        .iter()
                        .all(|tab| tab.as_str().is_some_and(|tab| tab.chars().count() <= 128))
                    && tabs
                        .iter()
                        .filter_map(Value::as_str)
                        .collect::<BTreeSet<_>>()
                        .len()
                        == tabs.len()
            });
        if !valid {
            return Err(invalid("저장한 탭 순서를 읽을 수 없습니다."));
        }
    }
    Ok(value)
}
fn ordered(saved: Option<&Value>, generation: &str, ids: &[Value]) -> Vec<Value> {
    let tabs = saved
        .filter(|saved| saved["generation"] == generation)
        .and_then(|saved| saved["tabs"].as_array());
    let mut order = tabs
        .map(|tabs| {
            tabs.iter()
                .filter(|tab| ids.contains(tab))
                .cloned()
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();
    for id in ids {
        if !order.contains(id) {
            order.push(id.clone());
        }
    }
    order
}
pub fn load_order(root: &Path, generation: &str, tabs: &[Value]) -> Value {
    let ids = tabs.iter().map(|tab| tab["id"].clone()).collect::<Vec<_>>();
    if generation.is_empty() || ids.is_empty() {
        return json!({"order":ids});
    }
    match read(root) {
        Ok(saved) => json!({"order":ordered(saved.as_ref(),generation,&ids)}),
        Err(_) => json!({"order":ids,"error":"저장한 탭 순서를 읽지 못했습니다."}),
    }
}
pub fn save_order(
    root: &Path,
    generation_value: &str,
    tabs: &[Value],
    order: &Value,
) -> Result<Value> {
    let ids = tabs.iter().map(|tab| tab["id"].clone()).collect::<Vec<_>>();
    let order = order.as_array().filter(|order| {
        order.len() == ids.len()
            && order.iter().all(Value::is_string)
            && order
                .iter()
                .filter_map(Value::as_str)
                .collect::<BTreeSet<_>>()
                .len()
                == order.len()
            && order.iter().all(|id| ids.contains(id))
    });
    let order = order
        .filter(|_| generation(generation_value))
        .ok_or_else(|| invalid("탭 목록이 바뀌었습니다. 다시 이동해 주세요."))?;
    let target = path(root)?;
    let previous = read(root)?;
    let current = ordered(previous.as_ref(), generation_value, &ids);
    let by_id = tabs
        .iter()
        .filter_map(|tab| tab["id"].as_str().map(|id| (id, tab)))
        .collect::<BTreeMap<_, _>>();
    for (before, after) in current.iter().zip(order) {
        let first = by_id[before.as_str().unwrap()];
        let second = by_id[after.as_str().unwrap()];
        if first.get("workspaceId").unwrap_or(&first["cwd"])
            != second.get("workspaceId").unwrap_or(&second["cwd"])
            || (before != after && (first["hidden"] == true || second["hidden"] == true))
        {
            return Err(invalid(
                "작업 공간이나 백그라운드 탭은 함께 이동할 수 없습니다.",
            ));
        }
    }
    files::atomic_json(
        &target,
        &json!({"schema":1,"generation":generation_value,"tabs":order}),
    )
    .map_err(|error| BackendError::unavailable(error.message))?;
    Ok(json!({"generation":generation_value,"order":order}))
}
