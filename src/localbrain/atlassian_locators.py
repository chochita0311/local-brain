import ipaddress
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote, unquote_to_bytes, urlsplit, urlunsplit


ATLASSIAN_LOCATOR_VERSION = "localbrain.atlassian-locator.v1"
MAX_LOCATOR_CODE_POINTS = 8_000
MAX_IDENTITY_CODE_POINTS = 300
MAX_QUERY_PAIRS = 64

_PROJECT_KEY = re.compile(r"[A-Z][A-Z0-9_]*\Z")
_ISSUE_KEY = re.compile(r"[A-Z][A-Z0-9_]*-[1-9][0-9]*\Z")
_DECIMAL = re.compile(r"[0-9]+\Z")
_BAD_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_TO_ASCII_LOWER = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"
)
_TO_ASCII_UPPER = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
)


def _ascii_lower(value: str) -> str:
    return value.translate(_TO_ASCII_LOWER)


def _ascii_upper(value: str) -> str:
    return value.translate(_TO_ASCII_UPPER)


@dataclass(frozen=True)
class AtlassianLocatorResult:
    kind: str
    service: Optional[str] = None
    family: Optional[str] = None
    normalized_domain: Optional[str] = None
    canonical_base_url: Optional[str] = None
    safe_locator_url: Optional[str] = None
    item_identity_kind: Optional[str] = None
    item_identity: Optional[str] = None
    reference_kind: Optional[str] = None
    reference_identity: Optional[str] = None
    container_hint: Optional[str] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class _NormalizedUrl:
    normalized_domain: str
    canonical_base_url: str
    path: str
    segments: tuple[str, ...]
    query_pairs: tuple[tuple[str, str], ...]
    query_overflow: bool


@dataclass(frozen=True)
class _Classification:
    result: AtlassianLocatorResult
    item_container_hint: Optional[str] = None
    page_title_hint: Optional[str] = None


def _terminal(kind: str, reason: str) -> _Classification:
    return _Classification(
        AtlassianLocatorResult(kind=kind, reason=reason)
    )


def _strict_unquote(value: str, *, plus: bool = False) -> Optional[str]:
    if _BAD_PERCENT_ESCAPE.search(value):
        return None
    encoded = value.replace("+", "%20") if plus else value
    try:
        return unquote_to_bytes(encoded).decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None


def _query_pairs(query: str) -> tuple[tuple[tuple[str, str], ...], bool]:
    if not query:
        return (), False
    raw_parts = query.split("&", MAX_QUERY_PAIRS)
    overflow = len(raw_parts) > MAX_QUERY_PAIRS
    pairs = []
    for part in raw_parts[:MAX_QUERY_PAIRS]:
        name, separator, value = part.partition("=")
        if not separator:
            value = ""
        decoded_name = _strict_unquote(name, plus=True)
        if decoded_name is None:
            continue
        pairs.append((_ascii_lower(decoded_name), value))
    return tuple(pairs), overflow


def _normalize_url(value: object) -> Optional[_NormalizedUrl]:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or len(cleaned) > MAX_LOCATOR_CODE_POINTS:
        return None
    if any(
        unicodedata.category(character).startswith("C")
        for character in cleaned
    ):
        return None
    try:
        parsed = urlsplit(cleaned)
        port = parsed.port
    except ValueError:
        return None
    scheme = parsed.scheme.lower()
    if (
        scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    if parsed.hostname.endswith(".."):
        return None
    raw_host = parsed.hostname[:-1] if parsed.hostname.endswith(".") else parsed.hostname
    if not raw_host:
        return None
    try:
        if ":" in raw_host:
            host = str(ipaddress.ip_address(raw_host)).lower()
        else:
            host = raw_host.encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError):
        return None
    if ":" not in host:
        if len(host) > 253:
            return None
        labels = host.split(".")
        if any(
            not 1 <= len(label) <= 63
            or re.fullmatch(
                r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label
            )
            is None
            for label in labels
        ):
            return None
        if all(character in "0123456789." for character in host):
            try:
                ipaddress.ip_address(host)
            except ValueError:
                return None
    default_port = (scheme == "http" and port == 80) or (
        scheme == "https" and port == 443
    )
    rendered_host = "[{}]".format(host) if ":" in host else host
    domain = host
    if port is not None and not default_port:
        rendered_host = "{}:{}".format(rendered_host, port)
        domain = "{}:{}".format(host, port)
    path = parsed.path or "/"
    if any(unicodedata.category(character).startswith("C") for character in path):
        return None
    if path != "/":
        path = path.rstrip("/") or "/"
    raw_segments = path[1:].split("/") if path.startswith("/") else path.split("/")
    if raw_segments == [""]:
        raw_segments = []
    base = urlunsplit((scheme, rendered_host, "", "", ""))
    if len(base) > MAX_LOCATOR_CODE_POINTS:
        return None
    pairs, query_overflow = _query_pairs(parsed.query)
    return _NormalizedUrl(
        normalized_domain=domain,
        canonical_base_url=base,
        path=path,
        segments=tuple(raw_segments),
        query_pairs=pairs,
        query_overflow=query_overflow,
    )


def _decoded_segment(value: str) -> tuple[Optional[str], bool]:
    decoded = _strict_unquote(value)
    if decoded is None:
        return None, True
    return decoded, False


def _project_key(value: str) -> tuple[Optional[str], bool]:
    decoded, unsafe = _decoded_segment(value)
    if unsafe:
        return None, True
    assert decoded is not None
    candidate = _ascii_upper(decoded)
    if not 1 <= len(candidate) <= MAX_IDENTITY_CODE_POINTS:
        return None, False
    return (candidate, False) if _PROJECT_KEY.fullmatch(candidate) else (None, False)


def _issue_key(value: str) -> tuple[Optional[str], bool]:
    decoded, unsafe = _decoded_segment(value)
    if unsafe:
        return None, True
    assert decoded is not None
    candidate = _ascii_upper(decoded)
    if not 1 <= len(candidate) <= MAX_IDENTITY_CODE_POINTS:
        return None, False
    return (candidate, False) if _ISSUE_KEY.fullmatch(candidate) else (None, False)


def _canonical_decimal(decoded: str) -> Optional[str]:
    if (
        not 1 <= len(decoded) <= MAX_IDENTITY_CODE_POINTS
        or not _DECIMAL.fullmatch(decoded)
        or not any(character != "0" for character in decoded)
    ):
        return None
    return decoded.lstrip("0")


def _decimal_identity(value: str, *, query: bool = False) -> tuple[Optional[str], bool]:
    if query:
        decoded = _strict_unquote(value, plus=True)
        if decoded is None:
            return None, True
    else:
        decoded, unsafe = _decoded_segment(value)
        if unsafe:
            return None, True
        assert decoded is not None
    return _canonical_decimal(decoded), False


def _normalized_text_identity(value: str) -> tuple[Optional[str], bool]:
    decoded, unsafe = _decoded_segment(value)
    if unsafe:
        return None, True
    assert decoded is not None
    normalized = unicodedata.normalize("NFKC", decoded)
    if (
        not 1 <= len(normalized) <= MAX_IDENTITY_CODE_POINTS
        or not normalized.strip()
        or normalized in {".", ".."}
        or "/" in normalized
        or "\\" in normalized
        or any(
            unicodedata.category(character).startswith("C")
            for character in normalized
        )
    ):
        return None, False
    return normalized, False


def _query_values(
    normalized: _NormalizedUrl, names: tuple[str, ...]
) -> tuple[list[str], bool]:
    if normalized.query_overflow:
        return [], False
    allowed = {_ascii_lower(name) for name in names}
    values = []
    for name, raw_value in normalized.query_pairs:
        if name not in allowed:
            continue
        decoded = _strict_unquote(raw_value, plus=True)
        if decoded is None:
            return [], True
        values.append(decoded)
    return values, False


def _unsafe_allowlisted_query(normalized: _NormalizedUrl) -> bool:
    path_only = _NormalizedUrl(
        normalized_domain=normalized.normalized_domain,
        canonical_base_url=normalized.canonical_base_url,
        path=normalized.path,
        segments=normalized.segments,
        query_pairs=(),
        query_overflow=False,
    )
    lower = tuple(_ascii_lower(segment) for segment in normalized.segments)
    path_item = _path_item(path_only)
    path_family = _structure_or_site(path_only)
    allowed = set()
    if lower == ("browse",) or (
        path_item is not None
        and path_item.result.kind == "item"
        and path_item.result.service == "jira"
    ) or (
        path_family is not None
        and path_family.result.kind in {"structure", "site"}
        and path_family.result.service == "jira"
    ):
        allowed.add("selectedissue")
    if lower == ("secure", "rapidboard.jspa"):
        allowed.update({"rapidview", "projectkey"})
    if lower in {
        ("issues",),
        ("secure", "issuenavigator.jspa"),
        ("secure", "managefilters.jspa"),
    }:
        allowed.update({"filter", "requestid", "filterid"})
    if lower == ("secure", "dashboard.jspa"):
        allowed.add("selectpageid")
    _context, confluence_segments = _confluence_context(normalized.segments)
    confluence_lower = tuple(
        _ascii_lower(segment) for segment in confluence_segments
    )
    if confluence_lower in {
        ("viewpage.action",),
        ("pages", "viewpage.action"),
    }:
        allowed.add("pageid")
    if not allowed:
        return False
    for name, raw_value in normalized.query_pairs:
        if name not in allowed:
            continue
        decoded = _strict_unquote(raw_value, plus=True)
        if decoded is None:
            return True
    return False


def _one_query_issue(normalized: _NormalizedUrl) -> tuple[Optional[str], bool]:
    values, unsafe = _query_values(normalized, ("selectedIssue",))
    if unsafe:
        return None, True
    if len(values) != 1:
        return None, False
    candidate = _ascii_upper(values[0])
    if not 1 <= len(candidate) <= MAX_IDENTITY_CODE_POINTS:
        return None, False
    return (candidate, False) if _ISSUE_KEY.fullmatch(candidate) else (None, False)


def _one_query_decimal(
    normalized: _NormalizedUrl, names: tuple[str, ...]
) -> tuple[Optional[str], bool]:
    values, unsafe = _query_values(normalized, names)
    if unsafe:
        return None, True
    if len(values) != 1:
        return None, False
    return _canonical_decimal(values[0]), False


def _one_query_project_hint(
    normalized: _NormalizedUrl,
) -> tuple[Optional[str], bool]:
    values, unsafe = _query_values(normalized, ("projectKey",))
    if unsafe:
        return None, True
    if len(values) != 1:
        return None, False
    candidate = _ascii_upper(values[0])
    if not 1 <= len(candidate) <= MAX_IDENTITY_CODE_POINTS:
        return None, False
    return (candidate, False) if _PROJECT_KEY.fullmatch(candidate) else (None, False)


def _recognized(
    normalized: _NormalizedUrl,
    *,
    kind: str,
    service: str,
    family: str,
    safe_path: str,
    safe_query: str = "",
    item_identity_kind: Optional[str] = None,
    item_identity: Optional[str] = None,
    reference_kind: Optional[str] = None,
    reference_identity: Optional[str] = None,
    container_hint: Optional[str] = None,
    item_container_hint: Optional[str] = None,
    page_title_hint: Optional[str] = None,
) -> _Classification:
    safe_url = normalized.canonical_base_url + safe_path
    if safe_query:
        safe_url += "?" + safe_query
    if len(safe_url) > MAX_LOCATOR_CODE_POINTS:
        return _terminal("unsafe", "unsafe-url")
    return _Classification(
        AtlassianLocatorResult(
            kind=kind,
            service=service,
            family=family,
            normalized_domain=normalized.normalized_domain,
            canonical_base_url=normalized.canonical_base_url,
            safe_locator_url=safe_url,
            item_identity_kind=item_identity_kind,
            item_identity=item_identity,
            reference_kind=reference_kind,
            reference_identity=reference_identity,
            container_hint=container_hint,
        ),
        item_container_hint=item_container_hint,
        page_title_hint=page_title_hint,
    )


def _item(
    normalized: _NormalizedUrl,
    *,
    service: str,
    identity_kind: str,
    identity: str,
    container_hint: Optional[str] = None,
    page_title_hint: Optional[str] = None,
    confluence_context: str = "",
) -> _Classification:
    safe_query = ""
    if service == "jira":
        path = "/browse/{}".format(identity)
    elif container_hint is not None:
        path = "{}/spaces/{}/pages/{}".format(
            confluence_context,
            quote(container_hint, safe=""),
            identity,
        )
    else:
        path = "{}/pages/viewpage.action".format(confluence_context)
        safe_query = "pageId={}".format(identity)
    return _recognized(
        normalized,
        kind="item",
        service=service,
        family=identity_kind,
        safe_path=path,
        safe_query=safe_query,
        item_identity_kind=identity_kind,
        item_identity=identity,
        item_container_hint=container_hint,
        page_title_hint=page_title_hint,
    )


def _structure(
    normalized: _NormalizedUrl,
    *,
    service: str,
    family: str,
    identity: str,
    safe_path: str,
    safe_query: str = "",
    container_hint: Optional[str] = None,
) -> _Classification:
    return _recognized(
        normalized,
        kind="structure",
        service=service,
        family=family,
        safe_path=safe_path,
        safe_query=safe_query,
        reference_kind=family,
        reference_identity=identity,
        container_hint=container_hint,
    )


def _site(
    normalized: _NormalizedUrl, *, service: str, family: str, safe_path: str
) -> _Classification:
    return _recognized(
        normalized,
        kind="site",
        service=service,
        family=family,
        safe_path=safe_path,
    )


def _confluence_context(
    segments: tuple[str, ...],
) -> tuple[str, tuple[str, ...]]:
    if segments and _ascii_lower(segments[0]) in {"wiki", "confluence"}:
        context = "/{}".format(_ascii_lower(segments[0]))
        return context, segments[1:]
    return "", segments


def _path_item(normalized: _NormalizedUrl) -> Optional[_Classification]:
    segments = normalized.segments
    lower = tuple(_ascii_lower(segment) for segment in segments)
    jira_patterns = (
        (("browse",), 2, None),
        (("issues",), 2, None),
        (("jira", "core", "projects"), 6, 3),
        (("jira", "software", "projects"), 6, 3),
        (("jira", "software", "c", "projects"), 7, 4),
        (("jira", "servicedesk", "projects"), 6, 3),
    )
    for prefix, expected_length, project_index in jira_patterns:
        if lower[: len(prefix)] != prefix or len(segments) != expected_length:
            continue
        issue_index = expected_length - 1
        if project_index is not None:
            project, unsafe = _project_key(segments[project_index])
            if unsafe:
                return _terminal("unsafe", "unsafe-url")
            if project is None or lower[project_index + 1] != "issues":
                continue
        issue, unsafe = _issue_key(segments[issue_index])
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if issue is not None:
            return _item(
                normalized,
                service="jira",
                identity_kind="jira_issue",
                identity=issue,
                container_hint=issue.rsplit("-", 1)[0],
            )

    if lower[:3] == ("servicedesk", "customer", "portal") and len(segments) == 5:
        portal, portal_unsafe = _decimal_identity(segments[3])
        issue, issue_unsafe = _issue_key(segments[4])
        if portal_unsafe or issue_unsafe:
            return _terminal("unsafe", "unsafe-url")
        if portal is not None and issue is not None:
            return _item(
                normalized,
                service="jira",
                identity_kind="jira_issue",
                identity=issue,
                container_hint=issue.rsplit("-", 1)[0],
            )

    confluence_context, confluence_segments = _confluence_context(segments)
    confluence_lower = tuple(_ascii_lower(segment) for segment in confluence_segments)
    page_id_raw = None
    space_hint = None
    title_hint = None
    if (
        len(confluence_segments) in {4, 5}
        and confluence_lower[0] == "spaces"
        and confluence_lower[2] == "pages"
    ):
        page_id_raw = confluence_segments[3]
        decoded_space, unsafe_space = _normalized_text_identity(
            confluence_segments[1]
        )
        if unsafe_space:
            return _terminal("unsafe", "unsafe-url")
        space_hint = decoded_space
        if len(confluence_segments) == 5:
            decoded_title, unsafe_title = _decoded_segment(confluence_segments[4])
            if not unsafe_title and decoded_title:
                title_hint = unicodedata.normalize("NFKC", decoded_title)
    elif (
        len(confluence_segments) in {2, 3}
        and confluence_lower[0] == "pages"
    ):
        page_id_raw = confluence_segments[1]
        if len(confluence_segments) == 3:
            decoded_title, unsafe_title = _decoded_segment(confluence_segments[2])
            if not unsafe_title and decoded_title:
                title_hint = unicodedata.normalize("NFKC", decoded_title)
    if page_id_raw is not None:
        page_id, unsafe = _decimal_identity(page_id_raw)
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if page_id is not None:
            return _item(
                normalized,
                service="confluence",
                identity_kind="confluence_page",
                identity=page_id,
                container_hint=space_hint,
                page_title_hint=title_hint,
                confluence_context=confluence_context,
            )
    return None


def _query_item(
    normalized: _NormalizedUrl,
    structure: Optional[_Classification],
) -> Optional[_Classification]:
    lower = tuple(_ascii_lower(segment) for segment in normalized.segments)
    jira_family = lower == ("browse",) or (
        structure is not None
        and structure.result.kind in {"structure", "site"}
        and structure.result.service == "jira"
    )
    if jira_family:
        issue, unsafe = _one_query_issue(normalized)
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if issue is not None:
            return _item(
                normalized,
                service="jira",
                identity_kind="jira_issue",
                identity=issue,
                container_hint=issue.rsplit("-", 1)[0],
            )
    confluence_context, segments = _confluence_context(normalized.segments)
    confluence_lower = tuple(_ascii_lower(segment) for segment in segments)
    if confluence_lower in {("viewpage.action",), ("pages", "viewpage.action")}:
        page_id, unsafe = _one_query_decimal(normalized, ("pageId",))
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if page_id is not None:
            return _item(
                normalized,
                service="confluence",
                identity_kind="confluence_page",
                identity=page_id,
                confluence_context=confluence_context,
            )
    return None


def _structure_or_site(normalized: _NormalizedUrl) -> Optional[_Classification]:
    segments = normalized.segments
    lower = tuple(_ascii_lower(segment) for segment in segments)

    if lower == ("secure", "rapidboard.jspa"):
        board_id, unsafe = _one_query_decimal(normalized, ("rapidView",))
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if board_id is None:
            return _site(
                normalized,
                service="jira",
                family="jira_board",
                safe_path="/secure/RapidBoard.jspa",
            )
        project_hint, hint_unsafe = _one_query_project_hint(normalized)
        if hint_unsafe:
            return _terminal("unsafe", "unsafe-url")
        query = "rapidView={}".format(board_id)
        if project_hint is not None:
            query += "&projectKey={}".format(project_hint)
        return _structure(
            normalized,
            service="jira",
            family="jira_board",
            identity=board_id,
            safe_path="/secure/RapidBoard.jspa",
            safe_query=query,
            container_hint=project_hint,
        )

    filter_paths = {
        ("issues",),
        ("secure", "issuenavigator.jspa"),
        ("secure", "managefilters.jspa"),
    }
    if lower in filter_paths:
        filter_id, unsafe = _one_query_decimal(
            normalized, ("filter", "requestId", "filterId")
        )
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if filter_id is None:
            return _site(
                normalized,
                service="jira",
                family="jira_filter",
                safe_path="/issues",
            )
        return _structure(
            normalized,
            service="jira",
            family="jira_filter",
            identity=filter_id,
            safe_path="/issues",
            safe_query="filter={}".format(filter_id),
        )

    if lower == ("secure", "dashboard.jspa"):
        dashboard_id, unsafe = _one_query_decimal(
            normalized, ("selectPageId",)
        )
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if dashboard_id is None:
            return _site(
                normalized,
                service="jira",
                family="jira_dashboard",
                safe_path="/secure/Dashboard.jspa",
            )
        return _structure(
            normalized,
            service="jira",
            family="jira_dashboard",
            identity=dashboard_id,
            safe_path="/secure/Dashboard.jspa",
            safe_query="selectPageId={}".format(dashboard_id),
        )

    if lower[:3] == ("servicedesk", "customer", "portal"):
        if len(segments) < 4:
            return _site(
                normalized,
                service="jira",
                family="jira_service_portal",
                safe_path="/servicedesk/customer/portal",
            )
        portal_id, unsafe = _decimal_identity(segments[3])
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if portal_id is None:
            return _site(
                normalized,
                service="jira",
                family="jira_service_portal",
                safe_path="/servicedesk/customer/portal",
            )
        return _structure(
            normalized,
            service="jira",
            family="jira_service_portal",
            identity=portal_id,
            safe_path="/servicedesk/customer/portal/{}".format(portal_id),
        )

    if lower[:3] == ("jira", "servicedesk", "projects"):
        if len(segments) < 4:
            return None
        project, unsafe = _project_key(segments[3])
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if project is None:
            return None
        return _structure(
            normalized,
            service="jira",
            family="jira_service_project",
            identity=project,
            safe_path="/jira/servicedesk/projects/{}".format(project),
            container_hint=project,
        )

    project_prefixes = (
        ("projects",),
        ("jira", "core", "projects"),
        ("jira", "software", "projects"),
        ("jira", "software", "c", "projects"),
        ("plugins", "servlet", "project-config"),
    )
    for prefix in project_prefixes:
        if lower[: len(prefix)] != prefix:
            continue
        project_index = len(prefix)
        if len(segments) <= project_index:
            return None
        project, project_unsafe = _project_key(segments[project_index])
        if project_unsafe:
            return _terminal("unsafe", "unsafe-url")
        board_index = project_index + 1
        modern_board = (
            prefix
            in {
                ("jira", "software", "projects"),
                ("jira", "software", "c", "projects"),
            }
            and len(segments) > board_index
            and lower[board_index] == "boards"
        )
        if modern_board:
            if project is None:
                return None
            if len(segments) <= board_index + 1:
                return _site(
                    normalized,
                    service="jira",
                    family="jira_board",
                    safe_path="/jira/software/projects/{}/boards".format(
                        project
                    ),
                )
            board_id, board_unsafe = _decimal_identity(segments[board_index + 1])
            if board_unsafe:
                return _terminal("unsafe", "unsafe-url")
            if board_id is None:
                return _site(
                    normalized,
                    service="jira",
                    family="jira_board",
                    safe_path="/jira/software/projects/{}/boards".format(
                        project
                    ),
                )
            return _structure(
                normalized,
                service="jira",
                family="jira_board",
                identity=board_id,
                safe_path="/jira/software/projects/{}/boards/{}".format(
                    project, board_id
                ),
                container_hint=project,
            )
        if project is None:
            return None
        return _structure(
            normalized,
            service="jira",
            family="jira_project",
            identity=project,
            safe_path="/projects/{}".format(project),
            container_hint=project,
        )

    confluence_context, confluence_segments = _confluence_context(segments)
    confluence_lower = tuple(_ascii_lower(segment) for segment in confluence_segments)
    if confluence_lower in {("viewpage.action",), ("pages", "viewpage.action")}:
        return None
    if confluence_lower and confluence_lower[0] == "pages":
        return None
    if (
        len(confluence_lower) >= 3
        and confluence_lower[0] == "spaces"
        and confluence_lower[2] == "pages"
    ):
        return None
    if confluence_lower and confluence_lower[0] in {"spaces", "display"}:
        if len(confluence_segments) < 2:
            return None
        excluded_descendants = {
            "attachment",
            "attachments",
            "blog",
            "blogs",
            "database",
            "databases",
            "embed",
            "embeds",
            "whiteboard",
            "whiteboards",
        }
        if any(
            segment in excluded_descendants
            for segment in confluence_lower[2:]
        ):
            return None
        space, unsafe = _normalized_text_identity(confluence_segments[1])
        if unsafe:
            return _terminal("unsafe", "unsafe-url")
        if space is None:
            return None
        return _structure(
            normalized,
            service="confluence",
            family="confluence_space",
            identity=space,
            safe_path="{}/spaces/{}".format(
                confluence_context, quote(space, safe="")
            ),
            container_hint=space,
        )
    return None


def _classify(value: object) -> _Classification:
    normalized = _normalize_url(value)
    if normalized is None:
        return _terminal("unsafe", "unsafe-url")
    if any(_ascii_lower(segment) == "rest" for segment in normalized.segments):
        return _terminal("unsupported", "unsupported-url")
    if _unsafe_allowlisted_query(normalized):
        return _terminal("unsafe", "unsafe-url")

    path_item = _path_item(normalized)
    if path_item is not None:
        return path_item
    structure = _structure_or_site(normalized)
    if structure is not None and structure.result.kind == "unsafe":
        return structure
    query_item = _query_item(normalized, structure)
    if query_item is not None:
        return query_item
    if structure is not None:
        return structure
    return _terminal("unsupported", "unsupported-url")


def describe_atlassian_url(value: object) -> AtlassianLocatorResult:
    return _classify(value).result


def atlassian_item_container_hint(value: object) -> Optional[str]:
    classified = _classify(value)
    if classified.result.kind != "item":
        return None
    return classified.item_container_hint


def atlassian_page_title_hint(value: object) -> Optional[str]:
    classified = _classify(value)
    if classified.result.kind != "item" or classified.result.service != "confluence":
        return None
    value = classified.page_title_hint
    if not value or any(
        unicodedata.category(character).startswith("C") for character in value
    ):
        return None
    return value[:500]


def atlassian_locator_identity(
    locator: AtlassianLocatorResult,
) -> Optional[tuple[str, ...]]:
    if locator.kind == "item":
        assert locator.normalized_domain
        assert locator.service
        assert locator.item_identity_kind
        assert locator.item_identity
        return (
            ATLASSIAN_LOCATOR_VERSION,
            locator.normalized_domain,
            locator.service,
            "item",
            locator.item_identity_kind,
            locator.item_identity,
        )
    if locator.kind == "structure":
        assert locator.normalized_domain
        assert locator.service
        assert locator.reference_kind
        assert locator.reference_identity
        return (
            ATLASSIAN_LOCATOR_VERSION,
            locator.normalized_domain,
            locator.service,
            "structure",
            locator.reference_kind,
            locator.reference_identity,
        )
    if locator.kind == "site":
        assert locator.normalized_domain
        assert locator.service
        assert locator.family
        return (
            ATLASSIAN_LOCATOR_VERSION,
            locator.normalized_domain,
            locator.service,
            "site",
            locator.family,
        )
    return None
