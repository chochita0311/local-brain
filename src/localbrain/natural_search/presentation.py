"""Bounded user-facing state and same-app result return locations."""

from urllib.parse import parse_qs, urlencode, urlsplit

MESSAGES = {
    "disabled": ("자연어 검색을 준비해 주세요", "세션과 등록된 Local Context를 이 기기에서 준비합니다. 처음 한 번은 시간이 걸릴 수 있습니다."),
    "model-missing": ("검색 모델 설치가 필요합니다", "로컬 모델 실행 환경과 Qwen 검색 모델을 설치한 뒤 다시 준비해 주세요. 기존 키워드 검색은 사용할 수 있습니다."),
    "preparing": ("검색 자료를 준비하고 있습니다", "완료된 자료가 있으면 검색할 수 있습니다. 준비 중에도 검색어를 바꿀 수 있습니다."),
    "partial": ("일부 자료를 갱신하고 있습니다", "현재 원문을 확인한 결과만 표시합니다. 갱신이 끝나면 같은 검색을 다시 실행해 주세요."),
    "failed": ("검색 준비를 마치지 못했습니다", "다시 준비하면 완료된 작업을 재사용합니다. 기존 키워드 검색은 계속 사용할 수 있습니다."),
    "ready": ("자연어 검색 준비 완료", "전체 작업 세션과 등록된 Local Context에서 관련 원문을 찾습니다."),
    "no-data": ("검색할 자료가 없습니다", "Sessions 또는 Local Context에서 자료를 동기화한 뒤 다시 검색해 주세요."),
}


def state_copy(status):
    value = dict(status)
    if value.get("state") not in MESSAGES:
        value["state"] = "failed"
    value["title"], value["description"] = MESSAGES[value["state"]]
    if value.get("error") == "SEARCH_INTERRUPTED":
        value["title"] = "검색 준비를 중단했습니다"
    return value


def safe_return(value):
    if not isinstance(value, str) or len(value) > 4000:
        return "/natural-search"
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "/natural-search"
    if (parsed.scheme or parsed.netloc or parsed.path != "/natural-search"
            or any(ord(c) < 32 for c in value) or "\\" in value):
        return "/natural-search"
    try:
        fields = parse_qs(parsed.query, max_num_fields=8)
        query = fields.get("q", [""])[-1]
        page = int(fields.get("page", ["1"])[-1])
    except ValueError:
        return "/natural-search"
    if len(query) > 300 or not 1 <= page <= 1000000:
        return "/natural-search"
    mode = fields.get("mode", ["ai"])[-1]
    if mode not in {"keyword", "ai"}:
        return "/natural-search"
    result = "/natural-search?" + urlencode({"q": query, "page": page, "mode": mode})
    if parsed.fragment.startswith("natural-result-") and all(c.isalnum() or c == "-" for c in parsed.fragment):
        result += "#" + parsed.fragment
    return result
