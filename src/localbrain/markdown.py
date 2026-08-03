from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Any, Literal, Optional, Tuple
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ElementTree

from latex2mathml.converter import convert as latex_to_mathml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from markupsafe import Markup, escape
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.dollarmath.index import math_inline_dollar
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
import yaml

from .markdown_references import (
    MarkdownReferenceContext,
    block_anchor,
    document_anchor_index,
    extract_document_fragment,
    heading_anchor,
    heading_slug,
    resolve_document_fragment,
)


RenderState = Literal["ready", "empty", "fallback"]


@dataclass(frozen=True)
class MarkdownProperty:
    name: str
    value: str


@dataclass(frozen=True)
class MarkdownRenderResult:
    html: Markup
    state: RenderState
    properties: Tuple[MarkdownProperty, ...] = ()


_LANGUAGE_ALIASES = {
    "bash": "bash",
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    "console": "console",
    "python": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "sql": "sql",
    "html": "html",
    "css": "css",
    "markdown": "markdown",
    "md": "markdown",
    "diff": "diff",
    "text": "text",
    "plaintext": "text",
}

_LANGUAGE_LABELS = {
    "bash": "Shell",
    "console": "Console",
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "json": "JSON",
    "yaml": "YAML",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "markdown": "Markdown",
    "diff": "Diff",
    "text": "Text",
}

_LANGUAGE_CLASS_PATTERN = re.compile(r"[^a-z0-9_-]+")
_BLOCK_ID_PATTERN = re.compile(r"(?:^|[ \t])\^([A-Za-z0-9][A-Za-z0-9_-]*)[ \t]*$")
_CALLOUT_PATTERN = re.compile(
    r"^\[!([A-Za-z0-9_-]+)\]([+-])?(?:[ \t]+([^\n]+))?"
)
_TAG_PATTERN = re.compile(r"#([^\s#.,!?;:()\[\]{}<>]+)")
_SAFE_CALLOUT_PATTERN = re.compile(r"[^a-z0-9_-]+")
_MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown", ".mkd"}
_DEFERRED_ATTACHMENT_SUFFIXES = {
    ".avif",
    ".bmp",
    ".canvas",
    ".gif",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".pdf",
    ".png",
    ".svg",
    ".wav",
    ".webm",
    ".webp",
}
_PYGMENTS_FORMATTER = HtmlFormatter(nowrap=True)
_SINGLE_LINE_MATH_RULE = math_inline_dollar(
    allow_space=False,
    allow_digits=False,
    allow_double=False,
)
_MAX_EMBED_DEPTH = 3
_MATHML_NAMESPACE = "http://www.w3.org/1998/Math/MathML"
_MATHML_ELEMENTS = {
    "math",
    "menclose",
    "merror",
    "mfenced",
    "mfrac",
    "mi",
    "mlabeledtr",
    "mmultiscripts",
    "mn",
    "mo",
    "mover",
    "mpadded",
    "mphantom",
    "mprescripts",
    "mroot",
    "mrow",
    "ms",
    "mspace",
    "msqrt",
    "mstyle",
    "msub",
    "msubsup",
    "msup",
    "mtable",
    "mtd",
    "mtext",
    "mtr",
    "munder",
    "munderover",
    "none",
}
_MATHML_ATTRIBUTES = {
    "accent",
    "accentunder",
    "align",
    "bevelled",
    "charalign",
    "columnalign",
    "columnlines",
    "columnspacing",
    "columnspan",
    "columnwidth",
    "crossout",
    "decimalpoint",
    "denomalign",
    "depth",
    "dir",
    "display",
    "edge",
    "equalcolumns",
    "equalrows",
    "fence",
    "form",
    "frame",
    "framespacing",
    "groupalign",
    "height",
    "indentalign",
    "indentshift",
    "linebreak",
    "linebreakstyle",
    "linethickness",
    "lspace",
    "mathsize",
    "mathvariant",
    "maxsize",
    "minlabelspacing",
    "minsize",
    "movablelimits",
    "notation",
    "numalign",
    "open",
    "overflow",
    "position",
    "rowalign",
    "rowlines",
    "rowspacing",
    "rowspan",
    "rspace",
    "scriptlevel",
    "scriptminsize",
    "scriptsizemultiplier",
    "selection",
    "separator",
    "separators",
    "shift",
    "side",
    "stackalign",
    "stretchy",
    "subscriptshift",
    "superscriptshift",
    "symmetric",
    "voffset",
    "width",
}


def _normalize_language(info: str) -> str:
    if not info.strip():
        return ""
    return info.strip().split(None, 1)[0].lower()


def _language_class(value: str) -> str:
    normalized = _LANGUAGE_CLASS_PATTERN.sub("-", value).strip("-")
    return normalized[:40]


def _highlight_with_pygments(code: str, language: str) -> str:
    lexer = get_lexer_by_name(language)
    return highlight(code, lexer, _PYGMENTS_FORMATTER)


def _render_fence(renderer, tokens, idx, options, env) -> str:
    token: Token = tokens[idx]
    requested_language = _normalize_language(token.info)
    canonical_language = _LANGUAGE_ALIASES.get(requested_language)
    language_class = _language_class(requested_language)
    display_label = (
        _LANGUAGE_LABELS.get(canonical_language, requested_language)
        if requested_language
        else "Code"
    )

    highlighted = None
    if canonical_language and canonical_language != "text":
        try:
            highlighted = _highlight_with_pygments(token.content, canonical_language)
        except Exception:
            highlighted = None

    code_html = highlighted if highlighted is not None else str(escape(token.content))
    class_attribute = (
        ' class="language-{}"'.format(escape(language_class))
        if language_class
        else ""
    )
    data_attribute = (
        ' data-language="{}"'.format(escape(canonical_language or language_class))
        if language_class
        else ""
    )

    return (
        '<figure class="markdown-code-block"{}>'
        '<figcaption class="markdown-code-label">{}</figcaption>'
        '<pre><code{}>{}</code></pre>'
        "</figure>\n"
    ).format(data_attribute, escape(display_label), class_attribute, code_html)


def _render_deferred_image(renderer, tokens, idx, options, env) -> str:
    token: Token = tokens[idx]
    alt_text = renderer.renderInlineAsText(token.children, options, env).strip()
    return _deferred_marker("Image", alt_text)


def _render_table_open(renderer, tokens, idx, options, env) -> str:
    return '<div class="markdown-table-scroll"><table>\n'


def _render_table_close(renderer, tokens, idx, options, env) -> str:
    return "</table></div>\n"


def _deferred_marker(kind: str, label: str) -> str:
    readable_text = "{} deferred".format(kind)
    if label:
        readable_text = "{} deferred: {}".format(kind, label)
    return (
        '<span class="markdown-image-deferred" '
        'data-markdown-image-deferred="true" '
        'aria-label="{} rendering deferred">[{}]</span>'
    ).format(escape(kind), escape(readable_text))


def _validated_mathml(value: str) -> str:
    root = ElementTree.fromstring(value)
    for element in root.iter():
        if not element.tag.startswith("{{{}}}".format(_MATHML_NAMESPACE)):
            raise ValueError("Foreign MathML element")
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name not in _MATHML_ELEMENTS:
            raise ValueError("Unsupported MathML element")
        for attribute in element.attrib:
            if attribute.startswith("{"):
                raise ValueError("Namespaced MathML attribute")
            if attribute.lower().startswith("on") or attribute not in _MATHML_ATTRIBUTES:
                raise ValueError("Unsupported MathML attribute")
    ElementTree.register_namespace("", _MATHML_NAMESPACE)
    return ElementTree.tostring(root, encoding="unicode", method="xml")


def _render_math(content: str, options: dict) -> str:
    display_mode = bool(options.get("display_mode"))
    try:
        mathml = _validated_mathml(
            latex_to_mathml(
                content,
                display="block" if display_mode else "inline",
            )
        )
    except Exception:
        tag = "div" if display_mode else "span"
        return '<{} class="markdown-math markdown-math-fallback">{}</{}>'.format(
            tag, escape(content), tag
        )
    tag = "div" if display_mode else "span"
    return '<{} class="markdown-math">{}</{}>'.format(tag, mathml, tag)


def _same_line_math_rule(state, silent: bool) -> bool:
    """Keep inline dollar math from consuming technical text across lines."""
    start = state.pos
    if state.src[start] != "$":
        return False

    newline = state.src.find("\n", start + 1)
    closing = state.src.find("$", start + 1)
    while closing >= 0:
        backslashes = 0
        cursor = closing - 1
        while cursor >= 0 and state.src[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            break
        closing = state.src.find("$", closing + 1)

    if closing < 0 or (newline >= 0 and closing > newline):
        return False
    return _SINGLE_LINE_MATH_RULE(state, silent)


def _highlight_rule(state, silent: bool) -> bool:
    start = state.pos
    if not state.src.startswith("==", start):
        return False
    end = state.src.find("==", start + 2)
    if end <= start + 2 or "\n" in state.src[start + 2 : end]:
        return False
    if not silent:
        opening = state.push("mark_open", "mark", 1)
        opening.markup = "=="
        text = state.push("text", "", 0)
        text.content = state.src[start + 2 : end]
        closing = state.push("mark_close", "mark", -1)
        closing.markup = "=="
    state.pos = end + 2
    return True


def _tag_rule(state, silent: bool) -> bool:
    start = state.pos
    if state.src[start] != "#":
        return False
    if start > 0 and not state.src[start - 1].isspace():
        return False
    match = _TAG_PATTERN.match(state.src, start)
    if not match or not any(character.isalpha() for character in match.group(1)):
        return False
    if not silent:
        token = state.push("obsidian_tag", "", 0)
        token.content = match.group(1)
    state.pos = match.end()
    return True


def _render_tag(renderer, tokens, idx, options, env) -> str:
    tag = tokens[idx].content
    return '<span class="markdown-tag" data-tag="{}">#{}</span>'.format(
        escape(tag.casefold()), escape(tag)
    )


def _wiki_reference_rule(state, silent: bool) -> bool:
    start = state.pos
    is_embed = state.src.startswith("![[", start)
    prefix_length = 3 if is_embed else 2
    if not is_embed and not state.src.startswith("[[", start):
        return False
    end = state.src.find("]]", start + prefix_length)
    if end < 0 or "\n" in state.src[start + prefix_length : end]:
        return False
    content = state.src[start + prefix_length : end].strip()
    if not content:
        return False
    if not silent:
        token = state.push("obsidian_embed" if is_embed else "obsidian_link", "", 0)
        token.content = content
    state.pos = end + 2
    return True


def _wiki_embed_block_rule(state, start_line: int, end_line: int, silent: bool) -> bool:
    start = state.bMarks[start_line] + state.tShift[start_line]
    maximum = state.eMarks[start_line]
    content = state.src[start:maximum].strip()
    if not (content.startswith("![[") and content.endswith("]]")):
        return False
    inner = content[3:-2].strip()
    if not inner or "]]" in inner:
        return False
    if silent:
        return True
    token = state.push("obsidian_embed", "", 0)
    token.content = inner
    token.block = True
    token.map = [start_line, start_line + 1]
    state.line = start_line + 1
    return True


def _wiki_target_and_label(content: str) -> Tuple[str, str]:
    if "|" in content:
        target, label = content.split("|", 1)
        return target.strip(), label.strip() or target.strip()
    target = content.strip()
    path_part = target.split("#", 1)[0]
    if path_part:
        label = PurePosixPath(path_part).stem
    else:
        label = target.lstrip("#^")
    return target, label or target


def _reference_state_span(label: str, state: str, *, embed: bool = False) -> str:
    role = "embed" if embed else "link"
    return (
        '<span class="markdown-reference markdown-reference-{} markdown-reference-{}" '
        'data-reference-state="{}">{}</span>'
    ).format(role, escape(state), escape(state), escape(label))


def _render_wiki_link(renderer, tokens, idx, options, env) -> str:
    target, label = _wiki_target_and_label(tokens[idx].content)
    context = env.get("reference_context")
    if context is None:
        if target.startswith("#"):
            anchor = resolve_document_fragment(env.get("anchor_source", ""), target[1:])
            if anchor:
                return (
                    '<a class="markdown-reference markdown-reference-internal" '
                    'data-reference-state="resolved" href="#{}">{}</a>'
                ).format(escape(anchor), escape(label))
        return _reference_state_span(label, "no-source")
    resolution = context.resolve(target, kind="wiki")
    if resolution.state == "resolved":
        return (
            '<a class="markdown-reference markdown-reference-internal" '
            'data-reference-state="resolved" href="{}">{}</a>'
        ).format(escape(resolution.href), escape(label))
    if resolution.state == "external":
        return _external_anchor(resolution.href or "", label)
    return _reference_state_span(label, resolution.state)


def _attachment_like(target: str) -> bool:
    path = unquote(target).split("#", 1)[0]
    suffix = PurePosixPath(path).suffix.lower()
    return suffix in _DEFERRED_ATTACHMENT_SUFFIXES or (
        bool(suffix) and suffix not in _MARKDOWN_SUFFIXES
    )


def _render_wiki_embed(renderer, tokens, idx, options, env) -> str:
    target, label = _wiki_target_and_label(tokens[idx].content)
    if _attachment_like(target) or urlsplit(unquote(target)).scheme:
        return _deferred_marker("Attachment", label)

    context = env.get("reference_context")
    if context is None:
        return _reference_state_span(label, "no-source", embed=True)
    resolution = context.resolve(target, kind="wiki")
    if resolution.state != "resolved" or resolution.document is None:
        return _reference_state_span(label, resolution.state, embed=True)
    if not resolution.document.is_markdown:
        return _deferred_marker("Attachment", label)

    if not tokens[idx].block:
        return (
            '<span class="markdown-note-embed-inline" data-reference-state="resolved">'
            '<a href="{}">[Embedded note: {}]</a></span>'
        ).format(escape(resolution.href), escape(label))

    depth = int(env.get("embed_depth", 0))
    stack = tuple(env.get("embed_stack", (context.current_document_id,)))
    if resolution.document.id in stack:
        return _reference_state_span(label, "cycle", embed=True)
    if depth >= _MAX_EMBED_DEPTH:
        return _reference_state_span(label, "depth-limit", embed=True)

    selected_source = extract_document_fragment(
        resolution.document.body, resolution.fragment
    )
    if selected_source is None:
        return _reference_state_span(label, "missing", embed=True)
    nested = render_markdown(
        selected_source,
        reference_context=context.for_document(resolution.document.id),
        _embed_depth=depth + 1,
        _embed_stack=stack + (resolution.document.id,),
    )
    return (
        '<article class="markdown-note-embed" data-reference-state="resolved" '
        'data-document-id="{}">'
        '<header class="markdown-note-embed-header"><a href="{}">{}</a></header>'
        '<div class="markdown-note-embed-body">{}</div>'
        "</article>"
    ).format(
        resolution.document.id,
        escape(resolution.href),
        escape(resolution.document.title),
        nested.html,
    )


def _external_anchor(href: str, label: str) -> str:
    return (
        '<a class="markdown-reference markdown-reference-external" '
        'data-reference-state="external" data-external-link="true" '
        'href="{}" target="_blank" rel="noopener noreferrer external">{}</a>'
    ).format(escape(href), escape(label))


def _render_link_open(renderer, tokens, idx, options, env) -> str:
    token = tokens[idx]
    href = token.attrGet("href") or ""
    decoded = unquote(href).strip()
    parsed = urlsplit(decoded)
    close_tags = env.setdefault("link_close_tags", [])

    if parsed.scheme:
        if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
            token.attrSet("href", decoded)
            token.attrSet("class", "markdown-reference markdown-reference-external")
            token.attrSet("data-reference-state", "external")
            token.attrSet("data-external-link", "true")
            token.attrSet("target", "_blank")
            token.attrSet("rel", "noopener noreferrer external")
            close_tags.append("a")
            return renderer.renderToken(tokens, idx, options, env)
        close_tags.append("span")
        return '<span class="markdown-reference markdown-reference-unsafe" data-reference-state="unsafe">'

    if decoded.startswith("#"):
        source = env.get("anchor_source", "")
        anchor = resolve_document_fragment(source, decoded[1:])
        if anchor:
            token.attrSet("href", "#{}".format(anchor))
            token.attrSet("class", "markdown-reference markdown-reference-internal")
            token.attrSet("data-reference-state", "resolved")
            close_tags.append("a")
            return renderer.renderToken(tokens, idx, options, env)
        close_tags.append("span")
        return '<span class="markdown-reference markdown-reference-missing" data-reference-state="missing">'

    context = env.get("reference_context")
    if context is None:
        close_tags.append("span")
        return '<span class="markdown-reference markdown-reference-no-source" data-reference-state="no-source">'
    resolution = context.resolve(decoded, kind="markdown")
    if resolution.state == "resolved":
        token.attrSet("href", resolution.href or "")
        token.attrSet("class", "markdown-reference markdown-reference-internal")
        token.attrSet("data-reference-state", "resolved")
        close_tags.append("a")
        return renderer.renderToken(tokens, idx, options, env)
    close_tags.append("span")
    return (
        '<span class="markdown-reference markdown-reference-{}" '
        'data-reference-state="{}">'
    ).format(escape(resolution.state), escape(resolution.state))


def _render_link_close(renderer, tokens, idx, options, env) -> str:
    close_tags = env.get("link_close_tags", [])
    tag = close_tags.pop() if close_tags else "a"
    return "</{}>".format(tag)


def _strip_block_id(token: Token) -> Optional[str]:
    if token.children is None:
        return None
    for child in reversed(token.children):
        if child.type != "text":
            continue
        match = _BLOCK_ID_PATTERN.search(child.content)
        if not match:
            return None
        child.content = _BLOCK_ID_PATTERN.sub("", child.content).rstrip()
        token.content = _BLOCK_ID_PATTERN.sub("", token.content).rstrip()
        return match.group(1)
    return None


def _structure_rule(state) -> None:
    heading_counts = {}
    tokens = state.tokens
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and index + 1 < len(tokens):
            inline = tokens[index + 1]
            if inline.type == "inline":
                key = heading_slug(inline.content)
                heading_counts[key] = heading_counts.get(key, 0) + 1
                token.attrSet("id", heading_anchor(inline.content, heading_counts[key]))

        if token.type == "inline" and index > 0:
            identifier = _strip_block_id(token)
            if identifier and tokens[index - 1].nesting == 1:
                tokens[index - 1].attrSet("id", block_anchor(identifier))

        if token.type != "blockquote_open":
            continue
        depth = 1
        inline = None
        for nested in tokens[index + 1 :]:
            if nested.type == "blockquote_open":
                depth += 1
            elif nested.type == "blockquote_close":
                depth -= 1
                if depth == 0:
                    break
            elif depth == 1 and nested.type == "inline" and inline is None:
                inline = nested
        if inline is None or inline.children is None:
            continue
        match = _CALLOUT_PATTERN.match(inline.content)
        if not match:
            continue
        callout_type = _SAFE_CALLOUT_PATTERN.sub("-", match.group(1).lower()).strip("-")
        title = (match.group(3) or match.group(1).replace("-", " ").title()).strip()
        token.attrSet("class", "markdown-callout markdown-callout-{}".format(callout_type))
        token.attrSet("data-callout", callout_type)
        if match.group(2):
            token.attrSet("data-callout-fold", match.group(2))
        for child in inline.children:
            if child.type == "text" and child.content.startswith(match.group(0)):
                child.content = child.content[len(match.group(0)) :].lstrip()
                break
        inline.content = inline.content[len(match.group(0)) :].lstrip()
        title_token = Token("obsidian_callout_title", "", 0)
        title_token.content = title
        inline.children.insert(0, title_token)


def _render_callout_title(renderer, tokens, idx, options, env) -> str:
    return '<span class="markdown-callout-title">{}</span>'.format(
        escape(tokens[idx].content)
    )


def _build_renderer() -> MarkdownIt:
    renderer = MarkdownIt(
        "commonmark",
        {
            "breaks": True,
            "html": False,
            "linkify": False,
            "typographer": False,
        },
    )
    renderer.enable(["table", "strikethrough"])
    renderer.use(footnote_plugin)
    renderer.use(tasklists_plugin, enabled=False, label=False)
    renderer.use(
        dollarmath_plugin,
        allow_space=False,
        allow_digits=False,
        allow_blank_lines=False,
        renderer=_render_math,
    )
    renderer.inline.ruler.at("math_inline", _same_line_math_rule)
    renderer.block.ruler.before(
        "paragraph", "obsidian_embed_block", _wiki_embed_block_rule
    )
    renderer.inline.ruler.before("emphasis", "obsidian_highlight", _highlight_rule)
    renderer.inline.ruler.before("link", "obsidian_wiki_reference", _wiki_reference_rule)
    renderer.inline.ruler.before("emphasis", "obsidian_tag", _tag_rule)
    renderer.core.ruler.after("inline", "obsidian_structure", _structure_rule)
    renderer.add_render_rule("fence", _render_fence)
    renderer.add_render_rule("image", _render_deferred_image)
    renderer.add_render_rule("table_open", _render_table_open)
    renderer.add_render_rule("table_close", _render_table_close)
    renderer.add_render_rule("obsidian_tag", _render_tag)
    renderer.add_render_rule("obsidian_link", _render_wiki_link)
    renderer.add_render_rule("obsidian_embed", _render_wiki_embed)
    renderer.add_render_rule("obsidian_callout_title", _render_callout_title)
    renderer.add_render_rule("link_open", _render_link_open)
    renderer.add_render_rule("link_close", _render_link_close)
    return renderer


def _property_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return "[{}]".format(", ".join(_property_value(item) for item in value))
    if isinstance(value, dict):
        return "{{{}}}".format(
            ", ".join(
                "{}: {}".format(key, _property_value(item))
                for key, item in value.items()
            )
        )
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def _extract_properties(source: str) -> Tuple[str, Tuple[MarkdownProperty, ...]]:
    lines = source.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return source, ()
    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            closing = index
            break
    if closing is None:
        return source, ()
    payload = "".join(lines[1:closing])
    try:
        parsed = yaml.safe_load(payload)
    except yaml.YAMLError:
        return source, ()
    if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
        return source, ()
    properties = tuple(
        MarkdownProperty(name=key, value=_property_value(value))
        for key, value in parsed.items()
    )
    return "".join(lines[closing + 1 :]), properties


def _strip_obsidian_comments(source: str) -> str:
    output = []
    in_comment = False
    in_fence = False
    fence_character = ""
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        fence = re.match(r"(`{3,}|~{3,})", stripped)
        if not in_comment and fence:
            marker = fence.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_character = marker
            elif marker == fence_character:
                in_fence = False
                fence_character = ""
            output.append(line)
            continue
        if in_fence:
            output.append(line)
            continue

        index = 0
        code_ticks = 0
        while index < len(line):
            if in_comment:
                end = line.find("%%", index)
                if end < 0:
                    if line.endswith("\n"):
                        output.append("\n")
                    index = len(line)
                else:
                    in_comment = False
                    index = end + 2
                continue
            if line[index] == "`":
                end = index
                while end < len(line) and line[end] == "`":
                    end += 1
                run = end - index
                if code_ticks == 0:
                    code_ticks = run
                elif code_ticks == run:
                    code_ticks = 0
                output.append(line[index:end])
                index = end
                continue
            if code_ticks == 0 and line.startswith("%%", index):
                in_comment = True
                index += 2
                continue
            output.append(line[index])
            index += 1
    return "".join(output)


_MARKDOWN = _build_renderer()


def render_markdown(
    source: str,
    *,
    reference_context: Optional[MarkdownReferenceContext] = None,
    _embed_depth: int = 0,
    _embed_stack: Tuple[int, ...] = (),
) -> MarkdownRenderResult:
    if not isinstance(source, str):
        raise TypeError("Markdown source must be a string")
    if source == "":
        return MarkdownRenderResult(html=Markup(""), state="empty")

    render_source, properties = _extract_properties(source)
    render_source = _strip_obsidian_comments(render_source)
    if render_source == "":
        return MarkdownRenderResult(
            html=Markup(""),
            state="ready" if properties else "empty",
            properties=properties,
        )

    embed_stack = _embed_stack
    if reference_context is not None and not embed_stack:
        embed_stack = (reference_context.current_document_id,)
    env = {
        "reference_context": reference_context,
        "anchor_source": render_source,
        "embed_depth": _embed_depth,
        "embed_stack": embed_stack,
    }
    try:
        rendered = _MARKDOWN.render(render_source, env)
    except Exception:
        fallback = '<pre class="markdown-render-fallback">{}</pre>'.format(
            escape(render_source)
        )
        return MarkdownRenderResult(
            html=Markup(fallback), state="fallback", properties=properties
        )

    return MarkdownRenderResult(
        html=Markup(rendered), state="ready", properties=properties
    )
