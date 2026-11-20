use super::urlencode;
use serde_json::Value;
pub fn state_copy(status: &Value) -> Value {
    let mut value = status.clone();
    let (title,description)=match value["state"].as_str(){Some("disabled")=>("자연어 검색을 준비해 주세요","세션과 등록된 Local Context를 이 기기에서 준비합니다. 처음 한 번은 시간이 걸릴 수 있습니다."),Some("model-missing")=>("검색 모델 설치가 필요합니다","로컬 모델 실행 환경과 Qwen 검색 모델을 설치한 뒤 다시 준비해 주세요. 기존 키워드 검색은 사용할 수 있습니다."),Some("preparing")=>("검색 자료를 준비하고 있습니다","완료된 자료가 있으면 검색할 수 있습니다. 준비 중에도 검색어를 바꿀 수 있습니다."),Some("partial")=>("일부 자료를 갱신하고 있습니다","현재 원문을 확인한 결과만 표시합니다. 갱신이 끝나면 같은 검색을 다시 실행해 주세요."),Some("ready")=>("자연어 검색 준비 완료","전체 작업 세션과 등록된 Local Context에서 관련 원문을 찾습니다."),Some("no-data")=>("검색할 자료가 없습니다","Sessions 또는 Local Context에서 자료를 동기화한 뒤 다시 검색해 주세요."),_=>{value["state"]="failed".into();("검색 준비를 마치지 못했습니다","다시 준비하면 완료된 작업을 재사용합니다. 설정에서 검색 상태를 확인하고 다시 시도해 주세요.")}};
    value["title"] = if value["error"] == "SEARCH_INTERRUPTED" {
        "검색 준비를 중단했습니다"
    } else {
        title
    }
    .into();
    value["description"] = description.into();
    value
}
pub fn safe_return(value: &str) -> String {
    let fallback = "/natural-search".to_string();
    if value.chars().count() > 4000
        || value.chars().any(|ch| (ch as u32) < 32)
        || value.contains('\\')
    {
        return fallback;
    }
    let cleaned = value.trim_start_matches(|ch: char| ch <= ' ');
    let (path_query, fragment) = cleaned.split_once('#').unwrap_or((cleaned, ""));
    let (path, query) = path_query.split_once('?').unwrap_or((path_query, ""));
    if path != "/natural-search" || query.split('&').count() > 8 {
        return fallback;
    }
    let mut fields = std::collections::BTreeMap::new();
    for (key, value) in url::form_urlencoded::parse(query.as_bytes()) {
        if !value.is_empty() {
            fields.insert(key.into_owned(), value.into_owned());
        }
    }
    let query = fields.get("q").cloned().unwrap_or_default();
    let page = fields
        .get("page")
        .map(String::as_str)
        .unwrap_or("1")
        .trim_matches(crate::backend::unicode::python_space);
    let page = page.strip_prefix('+').unwrap_or(page);
    let chars = page.chars().collect::<Vec<_>>();
    if chars.iter().enumerate().any(|(index, ch)| {
        *ch == '_'
            && (index == 0
                || index + 1 == chars.len()
                || chars[index - 1] == '_'
                || chars[index + 1] == '_')
    }) {
        return fallback;
    }
    let page = crate::backend::sources::profiles::decimal_integer(&page.replace('_', ""));
    let Some(page) = page.filter(|page| (1..=1_000_000).contains(page)) else {
        return fallback;
    };
    if query.chars().count() > 300
        || fields
            .get("mode")
            .is_some_and(|value| !["auto", "keyword", "ai"].contains(&value.as_str()))
    {
        return fallback;
    }
    let mut result = format!(
        "/natural-search?{}",
        urlencode(&[("q", query), ("page", page.to_string())])
    );
    if fragment.starts_with("natural-result-")
        && fragment
            .chars()
            .all(|ch| crate::backend::unicode::python_alnum(ch) || ch == '-')
    {
        result.push('#');
        result.push_str(fragment);
    }
    result
}
