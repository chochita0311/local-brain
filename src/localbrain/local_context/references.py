from dataclasses import dataclass
from pathlib import PurePosixPath
import re
import unicodedata
from typing import Dict, Iterable, Literal, Optional, Tuple
from urllib.parse import unquote, urlsplit


ReferenceState = Literal[
    "resolved", "external", "missing", "ambiguous", "unsafe", "no-source"
]


@dataclass(frozen=True)
class MarkdownDocumentReference:
    id: int
    context_root_id: int
    relative_path: str
    title: str
    body: str
    content_type: str = "text/markdown"

    @property
    def is_markdown(self) -> bool:
        return self.content_type in {"text/markdown", "text/x-markdown"}


@dataclass(frozen=True)
class MarkdownReferenceResolution:
    state: ReferenceState
    label: str
    document: Optional[MarkdownDocumentReference] = None
    fragment: Optional[str] = None
    href: Optional[str] = None


_HEADING_PREFIX_PATTERN = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_BLOCK_ID_PATTERN = re.compile(r"(?:^|[ \t])\^([A-Za-z0-9][A-Za-z0-9_-]*)[ \t]*$")
_ANCHOR_PUNCTUATION_PATTERN = re.compile(r"[^\w\s-]", flags=re.UNICODE)
_ANCHOR_SPACE_PATTERN = re.compile(r"[\s_-]+", flags=re.UNICODE)
_MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown", ".mkd"}


def heading_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = _ANCHOR_PUNCTUATION_PATTERN.sub("", normalized)
    normalized = _ANCHOR_SPACE_PATTERN.sub("-", normalized).strip("-")
    return normalized or "section"


def heading_anchor(value: str, occurrence: int = 1) -> str:
    base = "heading-{}".format(heading_slug(value))
    return base if occurrence <= 1 else "{}-{}".format(base, occurrence)


def block_anchor(value: str) -> str:
    return "block-{}".format(value.lower())


def document_anchor_index(source: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    headings: Dict[str, str] = {}
    blocks: Dict[str, str] = {}
    occurrences: Dict[str, int] = {}
    in_fence = False
    fence_marker = ""

    for line in source.splitlines():
        stripped = line.lstrip()
        fence_match = re.match(r"(`{3,}|~{3,})", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue

        heading_match = _HEADING_PREFIX_PATTERN.match(line)
        if heading_match:
            title = heading_match.group(2).strip()
            key = heading_slug(title)
            occurrences[key] = occurrences.get(key, 0) + 1
            headings.setdefault(key, heading_anchor(title, occurrences[key]))

        block_match = _BLOCK_ID_PATTERN.search(line)
        if block_match:
            identifier = block_match.group(1).lower()
            blocks.setdefault(identifier, block_anchor(identifier))

    return headings, blocks


def resolve_document_fragment(source: str, fragment: str) -> Optional[str]:
    decoded = unquote(fragment).strip()
    if not decoded:
        return None
    headings, blocks = document_anchor_index(source)
    if decoded.startswith("^"):
        return blocks.get(decoded[1:].lower())
    return headings.get(heading_slug(decoded))


def extract_document_fragment(source: str, fragment: Optional[str]) -> Optional[str]:
    if not fragment:
        return source
    decoded = unquote(fragment).strip()
    lines = source.splitlines()
    if decoded.startswith("^"):
        identifier = decoded[1:].lower()
        for index, line in enumerate(lines):
            match = _BLOCK_ID_PATTERN.search(line)
            if match and match.group(1).lower() == identifier:
                selected = _BLOCK_ID_PATTERN.sub("", line).rstrip()
                return selected
        return None

    target_slug = heading_slug(decoded)
    start = None
    level = None
    for index, line in enumerate(lines):
        match = _HEADING_PREFIX_PATTERN.match(line)
        if not match:
            continue
        current_level = len(match.group(1))
        if start is None and heading_slug(match.group(2).strip()) == target_slug:
            start = index
            level = current_level
            continue
        if start is not None and current_level <= int(level):
            return "\n".join(lines[start:index]).strip()
    if start is not None:
        return "\n".join(lines[start:]).strip()
    return None


def _split_target(value: str) -> Tuple[str, Optional[str]]:
    decoded = unquote(value).strip()
    if "#" not in decoded:
        return decoded, None
    path, fragment = decoded.split("#", 1)
    return path, fragment or None


def _normalized_source_path(path: str, base: PurePosixPath) -> Optional[str]:
    if not path or path.startswith(("/", "\\")) or "\\" in path or "\x00" in path:
        return None
    parts = list(base.parts)
    for part in PurePosixPath(path).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
            continue
        if part == "/":
            return None
        parts.append(part)
    if not parts:
        return None
    return PurePosixPath(*parts).as_posix()


def _path_candidates(path: str) -> Tuple[str, ...]:
    candidate = PurePosixPath(path)
    if candidate.suffix.lower() in _MARKDOWN_SUFFIXES:
        return (candidate.as_posix(),)
    return (candidate.as_posix(), "{}.md".format(candidate.as_posix()))


@dataclass(frozen=True)
class MarkdownReferenceContext:
    documents: Tuple[MarkdownDocumentReference, ...]
    current_document_id: int

    def __post_init__(self) -> None:
        if not self.documents:
            raise ValueError("Markdown reference context requires documents")
        root_ids = {document.context_root_id for document in self.documents}
        if len(root_ids) != 1:
            raise ValueError("Markdown reference context cannot mix Local Context roots")
        if self.current_document_id not in {document.id for document in self.documents}:
            raise ValueError("Current document is not part of the Local Context root")

    @classmethod
    def from_documents(
        cls,
        documents: Iterable[MarkdownDocumentReference],
        current_document_id: int,
    ) -> "MarkdownReferenceContext":
        return cls(tuple(documents), current_document_id)

    @property
    def current_document(self) -> MarkdownDocumentReference:
        for document in self.documents:
            if document.id == self.current_document_id:
                return document
        raise LookupError("Current document is unavailable")

    def for_document(self, document_id: int) -> "MarkdownReferenceContext":
        return MarkdownReferenceContext(self.documents, document_id)

    def resolve(self, target: str, kind: str = "wiki") -> MarkdownReferenceResolution:
        decoded = unquote(target).strip()
        readable = decoded or target
        parsed = urlsplit(decoded)
        if parsed.scheme:
            scheme = parsed.scheme.lower()
            if scheme in {"http", "https"} and parsed.netloc:
                return MarkdownReferenceResolution(
                    state="external", label=readable, href=decoded
                )
            return MarkdownReferenceResolution(state="unsafe", label=readable)

        path_value, fragment = _split_target(decoded)
        if path_value.startswith(("/", "\\")) or "\x00" in path_value:
            return MarkdownReferenceResolution(state="unsafe", label=readable)

        if not path_value:
            document = self.current_document
            anchor = resolve_document_fragment(document.body, fragment or "")
            if not anchor:
                return MarkdownReferenceResolution(state="missing", label=readable)
            return MarkdownReferenceResolution(
                state="resolved",
                label=readable,
                document=document,
                fragment=fragment,
                href="/documents/{}#{}".format(document.id, anchor),
            )

        matches = []
        if kind == "markdown":
            base = PurePosixPath(self.current_document.relative_path).parent
            normalized = _normalized_source_path(path_value, base)
            if normalized is None:
                return MarkdownReferenceResolution(state="unsafe", label=readable)
            candidates = {candidate.casefold() for candidate in _path_candidates(normalized)}
            matches = [
                document
                for document in self.documents
                if document.relative_path.casefold() in candidates
            ]
        elif "/" in path_value or PurePosixPath(path_value).suffix:
            normalized = _normalized_source_path(path_value, PurePosixPath("."))
            if normalized is None:
                return MarkdownReferenceResolution(state="unsafe", label=readable)
            candidates = {candidate.casefold() for candidate in _path_candidates(normalized)}
            matches = [
                document
                for document in self.documents
                if document.relative_path.casefold() in candidates
            ]
        else:
            lookup = path_value.casefold()
            matches = [
                document
                for document in self.documents
                if document.title.casefold() == lookup
                or PurePosixPath(document.relative_path).stem.casefold() == lookup
            ]

        if not matches:
            return MarkdownReferenceResolution(state="missing", label=readable)
        if len(matches) > 1:
            return MarkdownReferenceResolution(state="ambiguous", label=readable)

        document = matches[0]
        anchor = None
        if fragment:
            anchor = resolve_document_fragment(document.body, fragment)
            if not anchor:
                return MarkdownReferenceResolution(state="missing", label=readable)
        href = "/documents/{}".format(document.id)
        if anchor:
            href = "{}#{}".format(href, anchor)
        return MarkdownReferenceResolution(
            state="resolved",
            label=readable,
            document=document,
            fragment=fragment,
            href=href,
        )
