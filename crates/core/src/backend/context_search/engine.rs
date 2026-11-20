//! Bounded tool loop. Evidence is per turn and cleared on every exit.
use super::{
    chars, dumps, error,
    tools::{public_sources, tool_schemas, truth, FileTools},
};
use crate::backend::{search, sources::registry::PythonText, Result};
use localbrain_models::Cancellation;
use serde_json::{json, Value};
use std::collections::BTreeSet;
pub const SYSTEM: &str = include_str!("system.txt");
pub fn validate_request(value: &Value) -> Result<(String, Vec<Value>)> {
    let bad = || error("INPUT", "모델과 질문을 확인해 주세요.");
    let obj = value.as_object().ok_or_else(bad)?;
    if obj.len() != 2
        || !obj.contains_key("model")
        || !obj.contains_key("messages")
        || !matches!(value["model"].as_str(), Some("4b" | "8b"))
    {
        return Err(bad());
    }
    let long = || error("INPUT", "대화가 길어졌습니다. 새 질문으로 시작해 주세요.");
    let messages = value["messages"]
        .as_array()
        .filter(|v| (1..=13).contains(&v.len()))
        .ok_or_else(long)?;
    let mut size = 0;
    for (index, message) in messages.iter().enumerate() {
        let role = if index % 2 == 0 { "user" } else { "assistant" };
        if !message
            .as_object()
            .is_some_and(|m| m.len() == 2 && m.contains_key("role") && m.contains_key("content"))
            || message["role"] != role
            || message["content"]
                .as_str()
                .is_none_or(|s| s.py_trim().is_empty())
        {
            return Err(error("INPUT", "질문과 답변 순서를 확인해 주세요."));
        }
        let length = message["content"].as_str().unwrap().chars().count();
        if length > if role == "user" { 4000 } else { 12000 } {
            return Err(error("INPUT", "질문이나 대화를 줄여 다시 시도해 주세요."));
        }
        size += length
    }
    if messages.last().unwrap()["role"] != "user" || size > 24000 {
        return Err(long());
    }
    Ok((value["model"].as_str().unwrap().into(), messages.clone()))
}
pub fn parse_calls(output: &str) -> Result<Vec<Value>> {
    let blocks = search::pattern(r"(?s)<tool_call>\s*(.*?)\s*</tool_call>")
        .captures_iter(output)
        .map(|c| c.map(|c| c[1].to_owned()))
        .collect::<std::result::Result<Vec<_>, _>>()
        .map_err(|_| {
            error(
                "PROTOCOL",
                "모델의 도구 요청을 읽지 못했습니다. 질문을 구체화해 다시 시도해 주세요.",
            )
        })?;
    if blocks.is_empty() {
        if output.contains("<tool_call") || output.contains("</tool_call>") {
            return Err(error(
                "PROTOCOL",
                "모델의 도구 요청을 읽지 못했습니다. 질문을 구체화해 다시 시도해 주세요.",
            ));
        }
        return Ok(Vec::new());
    }
    if blocks.len() > 4 {
        return Err(error(
            "PROTOCOL",
            "한 번에 너무 많은 도구를 요청했습니다. 질문 범위를 줄여 주세요.",
        ));
    }
    if output.matches("<tool_call>").count() != blocks.len()
        || output.matches("</tool_call>").count() != blocks.len()
    {
        return Err(error(
            "PROTOCOL",
            "완료되지 않은 도구 요청입니다. 다시 질문해 주세요.",
        ));
    }
    blocks
        .iter()
        .map(|block| {
            let invalid = || {
                error(
                    "PROTOCOL",
                    "모델의 도구 요청 형식이 올바르지 않습니다. 다시 질문해 주세요.",
                )
            };
            let value = crate::backend::json::decode(block).map_err(|_| invalid())?;
            if !value.as_object().is_some_and(|m| {
                m.len() == 2 && m.contains_key("name") && m.contains_key("arguments")
            }) || !value["name"].is_string()
                || !value["arguments"].is_object()
            {
                return Err(invalid());
            }
            Ok(value)
        })
        .collect()
}
pub fn compact_result(mut result: Value) -> Result<Value> {
    for key in ["matches", "files", "sources"] {
        if result.get(key).is_none() {
            continue;
        }
        while dumps(&result)?.chars().count() > 6000
            && result[key].as_array().is_some_and(|a| !a.is_empty())
        {
            result[key].as_array_mut().unwrap().pop();
            result["limited"] = json!(true)
        }
        if key == "files" && truth(result.get("limited")) {
            result["next_offset"] = if result["files"].as_array().is_some_and(|a| !a.is_empty()) {
                json!(
                    result["offset"].as_u64().unwrap_or(0)
                        + result["files"].as_array().unwrap().len() as u64
                )
            } else {
                Value::Null
            }
        }
    }
    if let Some(text) = result["text"].as_str().filter(|s| s.chars().count() > 5000) {
        let text = chars(text, 5000);
        result["text"] = json!(text);
        result["limited"] = json!(true)
    }
    Ok(result)
}
/// Injection boundary permits deterministic offline tool-loop verification.
pub trait ContextGenerator {
    fn generate(
        &mut self,
        messages: &[Value],
        tools: &[Value],
        cancel: &Cancellation,
    ) -> Result<String>;
    fn clear_turn(&mut self) {}
}
impl ContextGenerator for localbrain_models::generation::LocalGenerator {
    fn generate(
        &mut self,
        messages: &[Value],
        tools: &[Value],
        cancel: &Cancellation,
    ) -> Result<String> {
        self.generate_messages(messages, Some(tools), cancel)
            .map(|v| v.text)
            .map_err(crate::backend::models::failure)
    }
}
pub fn answer(
    generator: &mut dyn ContextGenerator,
    sources: &[Value],
    history: &[Value],
    mut emit: impl FnMut(Value) -> Result<()>,
    cancel: &Cancellation,
) -> Result<Value> {
    let result = (|| {
        let mut tools = FileTools::new(sources)?;
        let mut messages = vec![
            json!({"role":"system","content":format!("{SYSTEM}\nAvailable sources:\n{}",dumps(&json!(public_sources(sources)))?)}),
        ];
        messages.extend_from_slice(history);
        let (mut used, mut attempted, mut nudged, mut limited) = (0, false, false, false);
        for _ in 0..8 {
            if cancel.load(std::sync::atomic::Ordering::Acquire) {
                return Err(error("cancelled", "모델 실행을 중단했습니다."));
            }
            emit(json!({"type":"status","phase":"generating"}))?;
            let output = generator.generate(&messages, &tool_schemas(), cancel)?;
            let calls = parse_calls(&output)?;
            if calls.is_empty() {
                if tools.evidence.is_empty() {
                    if !attempted && !nudged {
                        nudged = true;
                        messages.push(json!({"role":"assistant","content":output}));
                        messages.push(json!({"role":"user","content":"아직 문서를 검색하거나 읽지 않았습니다. 답변 전에 사용자 질문의 핵심 용어로 search_text 도구를 호출하세요. 실제 도구 결과를 받은 뒤 답하세요."}));
                        continue;
                    }
                    return Ok(
                        json!({"type":"answer","text":"모델이 자료에서 확인할 수 있는 근거를 찾지 못했습니다. 대상 폴더나 문서에 쓰인 구체적인 용어를 넣어 다시 질문해 주세요.","evidence":[],"limited":limited||!attempted}),
                    );
                }
                let cited = search::pattern(r"\[(S\d+)\]")
                    .captures_iter(&output)
                    .filter_map(|m| m.ok().map(|m| m[1].to_owned()))
                    .collect::<BTreeSet<_>>();
                let refs = tools
                    .evidence
                    .iter()
                    .filter_map(|v| v["ref"].as_str())
                    .collect::<BTreeSet<_>>();
                if cited.is_empty() || !cited.iter().all(|r| refs.contains(r.as_str())) {
                    messages.push(json!({"role":"assistant","content":output}));
                    messages.push(json!({"role":"user","content":"검증한 이번 질문의 근거 ref만 [S번호]로 인용해 답변을 다시 작성하세요. 근거가 부족하면 부족하다고 말하세요."}));
                    continue;
                }
                return Ok(
                    json!({"type":"answer","text":output,"evidence":tools.evidence.iter().filter(|v|cited.contains(v["ref"].as_str().unwrap_or(""))).collect::<Vec<_>>(),"limited":limited}),
                );
            }
            used += calls.len();
            if used > 12 {
                break;
            }
            messages.push(json!({"role":"assistant","content":"","tool_calls":calls.iter().map(|call|json!({"type":"function","function":call})).collect::<Vec<_>>()}));
            for call in calls {
                let name = call["name"].as_str().unwrap();
                attempted |= matches!(name, "search_text" | "read_file");
                emit(
                    json!({"type":"status","phase":if name=="read_file"{"reading"}else{"searching"},"tool":name}),
                )?;
                let result = match tools
                    .call(name, &call["arguments"])
                    .and_then(compact_result)
                {
                    Ok(result) => {
                        limited |= truth(result.get("limited")) || truth(result.get("unreadable"));
                        result
                    }
                    Err(_) => {
                        limited = true;
                        json!({"error":"요청한 자료를 읽을 수 없습니다. 허용된 소스/파일/인자를 확인하고 다른 검색이나 파일을 사용하세요."})
                    }
                };
                messages.push(json!({"role":"tool","name":name,"content":dumps(&result)?}));
            }
        }
        Err(error(
            "BUDGET",
            "이번 질문의 탐색 한도에 도달했습니다. 폴더·파일·키워드를 좁혀 다시 질문해 주세요.",
        ))
    })();
    generator.clear_turn();
    result
}
