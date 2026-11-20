//! Durable workspace metadata; manager generations own live membership.
use super::{storage, BackendError, Config, Result};
use serde_json::{json, Value};
use std::collections::HashSet;

fn failure(message: &str) -> BackendError {
    BackendError::conflict(message)
}
fn valid_id(value: &Value) -> bool {
    value.as_str().is_some_and(|s| {
        s.len() == 32
            && s.bytes()
                .all(|ch| ch.is_ascii_digit() || (b'a'..=b'f').contains(&ch))
    })
}
fn exact(value: &Value, keys: &[&str]) -> bool {
    value.as_object().is_some_and(|map| {
        map.len() == keys.len() && map.keys().all(|key| keys.contains(&key.as_str()))
    })
}
fn trim(value: &str) -> &str {
    value.trim_matches(|ch: char| ch.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&ch))
}
pub fn validate_document(value: &Value) -> Result<()> {
    let invalid = || failure("저장한 작업공간을 확인해 주세요.");
    if !exact(value, &["schema", "generation", "items"])
        || value["schema"].as_i64() != Some(1)
        || (!value["generation"].is_null() && !valid_id(&value["generation"]))
    {
        return Err(invalid());
    }
    let items = value["items"]
        .as_array()
        .filter(|v| v.len() <= 128)
        .ok_or_else(invalid)?;
    let mut ids = HashSet::new();
    let mut tabs = HashSet::new();
    for item in items {
        if !exact(item, &["id", "name", "cwd", "tabs"])
            || !valid_id(&item["id"])
            || !ids.insert(item["id"].as_str().unwrap())
        {
            return Err(invalid());
        }
        let name = item["name"].as_str().ok_or_else(invalid)?;
        let cwd = item["cwd"].as_str().ok_or_else(invalid)?;
        if trim(name).is_empty()
            || name.chars().count() > 120
            || cwd.chars().count() > 4096
            || cwd.contains('\0')
            || (!cwd.is_empty() && !cwd.starts_with('/'))
        {
            return Err(invalid());
        }
        let own = item["tabs"]
            .as_array()
            .filter(|v| v.len() <= 32)
            .ok_or_else(invalid)?;
        for tab in own {
            let tab = tab
                .as_str()
                .filter(|s| !s.is_empty() && s.chars().count() <= 128)
                .ok_or_else(invalid)?;
            if !tabs.insert(tab) {
                return Err(invalid());
            }
        }
    }
    if tabs.len() > 32 {
        return Err(failure("저장한 작업공간의 탭 목록을 확인해 주세요."));
    }
    Ok(())
}
fn empty() -> Value {
    json!({"schema":1,"generation":null,"items":[]})
}
fn read(config: &Config) -> Result<Value> {
    let dir = storage::files::validate_runtime_directory(&config.data_dir, config)
        .map_err(|_| failure("작업공간 저장 위치를 확인해 주세요."))?;
    let path = dir.join("terminal-workspaces.json");
    let invalid = || failure("저장한 작업공간을 확인해 주세요.");
    match std::fs::symlink_metadata(&path) {
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(empty()),
        Err(e) => return Err(e.into()),
        Ok(info) if info.len() > 2 * 1024 * 1024 => {
            return Err(failure("저장한 작업공간이 너무 큽니다."))
        }
        Ok(info) if !crate::files::regular(&info, true) => return Err(invalid()),
        _ => {}
    }
    let value = crate::files::read_json(&path, 2 * 1024 * 1024)
        .map_err(|_| invalid())?
        .ok_or_else(invalid)?;
    validate_document(&value)?;
    Ok(value)
}
fn project(saved: &Value, state: &Value, exclude: Option<&str>) -> Result<Value> {
    let mut value = saved.clone();
    value["generation"] = state["generation"].clone();
    let state_tabs = state["tabs"]
        .as_array()
        .ok_or_else(|| BackendError::unavailable("터미널 상태를 확인하지 못했습니다."))?;
    let terminals = state["terminals"]
        .as_array()
        .ok_or_else(|| BackendError::unavailable("터미널 상태를 확인하지 못했습니다."))?;
    let live: HashSet<_> = state_tabs.iter().filter_map(|t| t["id"].as_str()).collect();
    let items = value["items"]
        .as_array_mut()
        .ok_or_else(|| failure("저장한 작업공간을 확인해 주세요."))?;
    for item in items.iter_mut() {
        let own = item["tabs"].as_array_mut().unwrap();
        if saved["generation"] == state["generation"] {
            own.retain(|tab| {
                tab.as_str()
                    .is_some_and(|id| live.contains(id) && Some(id) != exclude)
            });
        } else {
            own.clear();
        }
    }
    let mut assigned: HashSet<String> = items
        .iter()
        .flat_map(|item| {
            item["tabs"]
                .as_array()
                .unwrap()
                .iter()
                .filter_map(|v| v.as_str().map(str::to_owned))
        })
        .collect();
    for tab in state_tabs {
        let tab_id = tab["id"]
            .as_str()
            .ok_or_else(|| BackendError::unavailable("터미널 상태를 확인하지 못했습니다."))?;
        if assigned.contains(tab_id) || Some(tab_id) == exclude {
            continue;
        }
        let cwd = tab["cwd"]
            .as_str()
            .filter(|s| !s.is_empty())
            .or_else(|| {
                terminals
                    .iter()
                    .find(|term| {
                        tab["terminals"]
                            .as_array()
                            .is_some_and(|ids| ids.contains(&term["id"]))
                    })
                    .and_then(|term| term["cwd"].as_str())
            })
            .unwrap_or("");
        let id =
            crate::files::digest(format!("terminal-workspace\0{cwd}").as_bytes())[..32].to_owned();
        let index = if let Some(index) = items.iter().position(|item| item["id"] == id) {
            index
        } else {
            let name = cwd
                .trim_end_matches('/')
                .rsplit('/')
                .next()
                .filter(|s| !s.is_empty())
                .unwrap_or("작업공간")
                .chars()
                .take(120)
                .collect::<String>();
            items.push(json!({"id":id,"name":name,"cwd":cwd,"tabs":[]}));
            items.len() - 1
        };
        items[index]["tabs"]
            .as_array_mut()
            .unwrap()
            .push(json!(tab_id));
        assigned.insert(tab_id.into());
    }
    Ok(value)
}
pub fn read_workspaces(config: &Config, state: &Value) -> Value {
    match read(config).and_then(|saved|{let projected=project(&saved,state,None)?;Ok(json!({"items":projected["items"],"needsSave":saved!=projected&&(!saved["items"].as_array().unwrap().is_empty()||state["tabs"].as_array().is_some_and(|v|!v.is_empty()))}))}) {
        Ok(value)=>value,
        Err(_)=>json!({"items":project(&empty(),state,None).map(|v|v["items"].clone()).unwrap_or_else(|_|json!([])),"needsSave":false,"error":"작업공간을 읽지 못했습니다. 기존 저장 파일을 확인해 주세요."}),
    }
}
pub fn change_workspaces(
    config: &Config,
    mut read_state: impl FnMut() -> Result<Value>,
    action: &str,
    body: &Value,
) -> Result<Value> {
    let _guard = storage::operation_lock(config, "terminal-workspaces")
        .map_err(|_| failure("다른 로컬 작업이 저장 중입니다. 잠시 후 다시 시도해 주세요."))?;
    let state = read_state()?;
    if body.get("generation").is_some() && body["generation"] != state["generation"] {
        return Err(failure("터미널 서비스가 바뀌었습니다. 다시 시도해 주세요."));
    }
    let saved = read(config)?;
    let tab_id = body["tabId"].as_str();
    let mut value = project(
        &saved,
        &state,
        if ["attach", "move"].contains(&action) {
            tab_id
        } else {
            None
        },
    )?;
    let mut selected = value["items"]
        .as_array()
        .unwrap()
        .iter()
        .position(|item| item["id"] == body["id"]);
    let mut removed_id = None;
    match action {
        "create" => {
            let items = value["items"].as_array_mut().unwrap();
            if items.len() >= 128 {
                return Err(failure(
                    "작업공간 한도에 도달했습니다. 빈 작업공간을 목록에서 제거해 주세요.",
                ));
            }
            let name = body["name"]
                .as_str()
                .ok_or_else(|| failure("작업공간 요청을 확인해 주세요."))?;
            items.push(json!({"id":uuid::Uuid::new_v4().simple().to_string(),"name":trim(name),"cwd":body["cwd"],"tabs":[]}));
            selected = Some(items.len() - 1);
        }
        "update" | "remove" | "attach" | "move" => {
            if ["attach", "move"].contains(&action) {
                let tab =
                    tab_id.ok_or_else(|| failure("탭 목록이 바뀌었습니다. 다시 확인해 주세요."))?;
                if !state["tabs"]
                    .as_array()
                    .is_some_and(|items| items.iter().any(|entry| entry["id"] == tab))
                {
                    return Err(failure("탭 목록이 바뀌었습니다. 다시 확인해 주세요."));
                }
                let owner = if saved["generation"] == state["generation"] {
                    saved["items"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .find(|item| item["tabs"].as_array().unwrap().iter().any(|v| v == tab))
                } else {
                    None
                };
                if action == "attach"
                    && owner.is_some_and(|owner| {
                        !body["id"].is_null() && body["id"] != "" && owner["id"] != body["id"]
                    })
                {
                    return Err(failure(
                        "이 탭은 다른 작업공간에 있습니다. 탭 이동을 사용해 주세요.",
                    ));
                }
                if body["id"].is_null() || body["id"] == "" {
                    selected = owner.and_then(|owner| {
                        value["items"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .position(|item| item["id"] == owner["id"])
                    });
                    if selected.is_none() {
                        value = project(&saved, &state, None)?;
                        selected = value["items"].as_array().unwrap().iter().position(|item| {
                            item["tabs"].as_array().unwrap().iter().any(|v| v == tab)
                        });
                    }
                }
                if let Some(index) = selected {
                    let tabs = value["items"][index]["tabs"].as_array_mut().unwrap();
                    if !tabs.iter().any(|v| v == tab) {
                        tabs.push(json!(tab));
                    }
                }
            }
            let index = selected
                .ok_or_else(|| failure("작업공간을 찾지 못했습니다. 목록을 다시 확인해 주세요."))?;
            if action == "update" {
                value["items"][index]["name"] = json!(trim(
                    body["name"]
                        .as_str()
                        .ok_or_else(|| failure("작업공간 요청을 확인해 주세요."))?
                ));
                value["items"][index]["cwd"] = body["cwd"].clone();
            } else if action == "remove" {
                if !value["items"][index]["tabs"].as_array().unwrap().is_empty() {
                    return Err(failure(
                        "터미널을 모두 종료한 빈 작업공간만 목록에서 제거할 수 있습니다.",
                    ));
                }
                removed_id =
                    Some(value["items"].as_array_mut().unwrap().remove(index)["id"].clone());
                selected = None;
            }
        }
        "reconcile" => {}
        _ => return Err(failure("작업공간 요청을 확인해 주세요.")),
    }
    validate_document(&value)?;
    let id = selected
        .map(|index| value["items"][index]["id"].clone())
        .or(removed_id)
        .unwrap_or(Value::Null);
    if saved != value {
        storage::files::private_directory(&config.data_dir, config)
            .map_err(|_| failure("작업공간 저장 위치를 확인해 주세요."))?;
        storage::files::atomic_write(
            &config.data_dir.join("terminal-workspaces.json"),
            &serde_json::to_vec(&value)?,
        )?;
    }
    Ok(json!({"items":value["items"],"needsSave":false,"id":id}))
}
