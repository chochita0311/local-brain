"""Conservative, visible interpretation of explicit Korean search conditions."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass
class Conditions:
    kind: str = ""
    start: str = ""
    end: str = ""
    exclude: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    notices: list = field(default_factory=list)

    def matches(self, metadata):
        if self.kind and metadata["kind"] != self.kind:
            return False
        if self.start:
            try:
                stamp = datetime.fromisoformat(metadata["timestamp"].replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=ZoneInfo("UTC"))
            except (ValueError, TypeError):
                return False
            if not datetime.fromisoformat(self.start) <= stamp < datetime.fromisoformat(self.end):
                return False
        return True


def interpret(query, timezone_name="UTC", now=None):
    result = Conditions()
    literal_exclusion = re.compile(r'[“"「]([^”"」]+)[”"」](?:\s*문구)?(?:는|은|를|을)?\s*(?:제외|빼고)')
    remaining = literal_exclusion.sub("", query)
    # Quoted content is a search phrase, not an instruction to narrow source scope.
    remaining = re.sub(r'[“"「\'].*?[”"」\']', ' ', remaining)
    kinds = []
    for name, kind in (("세션", "session"), ("문서", "document")):
        if re.search(name + r"(?:만\b|(?:을|를)?(?:\s*(?:보여|찾아|검색|알려)|\s*$))", remaining):
            kinds.append(kind)
    ambiguous = bool(re.search(r"말고|아니[고라]|제외|빼고", remaining))
    kind_negation = bool(re.search(r"(?:세션|문서)(?:만|은|는|을|를)?\s*(?:말고|아니|제외|빼고)", remaining))
    if len(kinds) == 1 and not kind_negation:
        result.kind = kinds[0]
        result.labels.append("세션" if result.kind == "session" else "Local Context 문서")
    period_pattern = r"오늘|어제|이번\s*주|지난\s*주|이번\s*달|지난\s*달"
    matches = list(re.finditer(r"(?<![가-힣A-Za-z0-9_])(?:" + period_pattern + ")", remaining))
    periods = [match.group() for match in matches]
    uncertain_period = False
    for match in matches:
        tail = remaining[match.end():]
        if (not re.match(r"^(?:$|[\s,.!?]|(?:에|의|만|동안)(?:\s|$))", tail)
                or re.match(r"\s*(?:이후|이전|부터|까지|쯤|정도|전후|말)", tail)
                or re.match(r"(?:은|는|을|를)?\s*(?:(?:자료|작업|세션|문서)(?:은|는|을|를)?\s*)?(?:말고|아니|제외|빼고)", tail)):
            uncertain_period = True
    if len(set(re.sub(r"\s", "", p) for p in periods)) == 1 and not uncertain_period:
        zone = ZoneInfo(timezone_name)
        current = (now or datetime.now(zone)).astimezone(zone)
        today = current.replace(hour=0, minute=0, second=0, microsecond=0)
        period = re.sub(r"\s", "", periods[0])
        if period == "오늘":
            start, end = today, today + timedelta(days=1)
        elif period == "어제":
            start, end = today - timedelta(days=1), today
        elif period in ("이번주", "지난주"):
            monday = today - timedelta(days=today.weekday())
            start = monday - (timedelta(days=7) if period == "지난주" else timedelta())
            end = start + timedelta(days=7)
        else:
            first = today.replace(day=1)
            if period == "지난달":
                start, end = (first - timedelta(days=1)).replace(day=1), first
            else:
                start = first
                end = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        result.start, result.end = start.isoformat(), end.isoformat()
        result.labels.append("{} ≤ 날짜 < {} ({}, 세션 마지막 활동·문서 수정일)".format(
            start.date(), end.date(), timezone_name))
    elif periods:
        result.notices.append("기간 해석이 모호해 날짜 범위를 제한하지 않았습니다.")
    for match in literal_exclusion.finditer(query):
        result.exclude.append(match.group(1))
        result.labels.append('원문 문구 “{}” 제외'.format(match.group(1)))
    if ambiguous:
        result.notices.append("제외 조건의 의미가 모호해 후보를 넓게 유지했습니다. 문구를 명확히 제외하려면 따옴표로 지정해 주세요.")
    if len(kinds) > 1 or kind_negation:
        result.notices.append("자료 종류를 하나로 제한하지 않았습니다.")
    return result
