use super::{
    escape,
    highlight::{canonical, label, language},
    highlight_code,
    references::*,
    MarkdownOptions, MarkdownProperty, MarkdownRenderResult,
};
use crate::backend::{
    unicode::{casefold, lowercase, python_space, splitlines_keepends},
    yaml::{safe_load, SafeYaml},
};
use pulldown_cmark::{Alignment, CodeBlockKind, Event, Tag, TagEnd};
use regex::Regex;
use std::{
    collections::{BTreeMap, BTreeSet},
    ops::Range,
    sync::LazyLock,
};

mod parser;

const MAX_INLINE_NOTE_DEPTH: usize = 64;

#[derive(Clone)]
struct Node {
    tag: Option<Tag<'static>>,
    event: Option<Event<'static>>,
    children: Vec<Node>,
    range: Range<usize>,
}
fn nodes(
    events: &mut std::iter::Peekable<impl Iterator<Item = (Event<'static>, Range<usize>)>>,
) -> Vec<Node> {
    let mut result = Vec::new();
    while let Some((event, range)) = events.next() {
        match event {
            Event::End(_) => break,
            Event::Start(tag) => result.push(Node {
                tag: Some(tag),
                event: None,
                children: nodes(events),
                range,
            }),
            event => result.push(Node {
                tag: None,
                event: Some(event),
                children: Vec::new(),
                range,
            }),
        }
    }
    result
}
#[derive(Clone)]
enum Extension {
    Highlight(String),
    Tag(String),
    Math(String, bool),
    Wiki(String, bool),
    Footnote { index: usize, sub: usize },
}
struct InlineNote {
    source: String,
    nodes: Vec<Node>,
}
enum FootnoteSlot {
    Named { label: String, count: usize },
    Inline(InlineNote),
}
#[derive(Default)]
struct Footnotes {
    named: BTreeMap<String, usize>,
    slots: Vec<FootnoteSlot>,
}
impl Footnotes {
    fn named_reference(&mut self, label: &str) -> Result<(usize, usize), ()> {
        let index = if let Some(index) = self.named.get(label) {
            *index
        } else {
            let index = self.slots.len();
            self.slots.push(FootnoteSlot::Named {
                label: label.to_string(),
                count: 0,
            });
            self.named.insert(label.to_string(), index);
            index
        };
        let Some(FootnoteSlot::Named { count, .. }) = self.slots.get_mut(index) else {
            // The legacy plugin also fails when an inline note overwrote the
            // named slot and a later reference asks for its missing counter.
            return Err(());
        };
        let sub = *count;
        *count += 1;
        Ok((index, sub))
    }
    fn publish_inline(&mut self, index: usize, body: InlineNote) -> Result<(), ()> {
        let body = FootnoteSlot::Inline(body);
        if index == self.slots.len() {
            self.slots.push(body);
        } else {
            // Preserve the original plugin's reserve -> parse -> publish order:
            // nested notes can occupy this slot before the outer note replaces it.
            *self.slots.get_mut(index).ok_or(())? = body;
        }
        Ok(())
    }
}
struct Prepared {
    source: String,
    body_end: usize,
    prefix: String,
    extensions: Vec<(String, Extension)>,
    footnotes: Footnotes,
    named_notes: BTreeSet<String>,
    references: parser::Definitions,
    removed_lines: Vec<(usize, usize)>,
}
fn marker(prepared: &mut Prepared, raw: &str, extension: Extension) {
    let key = format!("{}{}END", prepared.prefix, prepared.extensions.len());
    prepared.source.push_str(&key);
    let inline_note = matches!(extension, Extension::Footnote { .. });
    prepared.extensions.push((raw.into(), extension));
    if inline_note {
        let lines = raw.bytes().filter(|ch| *ch == b'\n').count();
        if lines > 0 {
            let previous = prepared.removed_lines.last().map_or(0, |(_, total)| *total);
            prepared
                .removed_lines
                .push((prepared.source.len(), previous + lines));
        }
        return;
    }
    for ch in raw.chars() {
        if ch == '\n' {
            prepared.source.push('\n');
        }
    }
}
fn escaped_before(source: &str, index: usize) -> bool {
    source[..index]
        .bytes()
        .rev()
        .take_while(|ch| *ch == b'\\')
        .count()
        % 2
        == 1
}
fn is_inline_tag(tag: TagEnd) -> bool {
    matches!(
        tag,
        TagEnd::Emphasis
            | TagEnd::Strong
            | TagEnd::Strikethrough
            | TagEnd::Superscript
            | TagEnd::Subscript
            | TagEnd::Link
            | TagEnd::Image
    )
}
struct CodeProtection {
    blocks: Vec<Range<usize>>,
    inline_scopes: Vec<Range<usize>>,
    backtick_runs: BTreeMap<usize, Vec<usize>>,
    named_notes: BTreeSet<String>,
    references: parser::Definitions,
}
fn code_protection(
    source: &str,
    inline: Option<&parser::Definitions>,
) -> Result<CodeProtection, ()> {
    let mut blocks = Vec::new();
    let mut inline_scopes = Vec::new();
    let mut inline_scope: Option<Range<usize>> = None;
    let mut in_code_block = false;
    let mut named_notes = BTreeSet::new();
    let parsed = if let Some(references) = inline {
        parser::Parsed {
            events: parser::inline_events(source, references)?,
            definitions: BTreeMap::new(),
        }
    } else {
        parser::parse(source)?
    };
    for (event, range) in parsed.events {
        let boundary = match &event {
            Event::Start(tag) => !is_inline_tag(tag.to_end()),
            Event::End(tag) => !is_inline_tag(*tag),
            Event::Rule | Event::Html(_) => true,
            _ => false,
        };
        if boundary {
            if let Some(scope) = inline_scope.take() {
                inline_scopes.push(scope);
            }
        }
        match event {
            Event::Start(Tag::CodeBlock(_)) => {
                blocks.push(range);
                in_code_block = true;
            }
            Event::End(TagEnd::CodeBlock) => in_code_block = false,
            Event::Start(Tag::FootnoteDefinition(name)) => {
                named_notes.insert(name.to_string());
            }
            Event::Text(_)
            | Event::Code(_)
            | Event::InlineHtml(_)
            | Event::SoftBreak
            | Event::HardBreak
            | Event::FootnoteReference(_)
            | Event::TaskListMarker(_)
                if !in_code_block =>
            {
                if let Some(scope) = &mut inline_scope {
                    scope.end = range.end;
                } else {
                    inline_scope = Some(range);
                }
            }
            _ => {}
        }
    }
    if let Some(scope) = inline_scope {
        inline_scopes.push(scope);
    }
    // Index whole runs once, including escaped runs: a backslash inside code is
    // literal and cannot escape its closing delimiter. Lookups stay bounded even
    // with many unmatched openers or extensions that consume earlier delimiters.
    let mut backtick_runs: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    let mut index = 0;
    while let Some(offset) = source[index..].find('`') {
        let start = index + offset;
        let count = source[start..].bytes().take_while(|ch| *ch == b'`').count();
        backtick_runs.entry(count).or_default().push(start);
        index = start + count;
    }
    Ok(CodeProtection {
        blocks,
        inline_scopes,
        backtick_runs,
        named_notes,
        references: parsed.definitions,
    })
}
fn extension_at(
    source: &str,
    index: usize,
    line_start: usize,
    inline_only: bool,
) -> Option<(usize, Extension)> {
    let rest = &source[index..];
    let first = rest.chars().next()?;
    let embed = rest.starts_with("![[");
    let prefix = if embed { 3 } else { 2 };
    if embed || rest.starts_with("[[") {
        if let Some(end) = rest[prefix..].find("]]").map(|end| end + prefix + 2) {
            let inner = &rest[prefix..end - 2];
            if !inner.contains('\n') && !inner.trim_matches(python_space).is_empty() {
                return Some((
                    index + end,
                    Extension::Wiki(inner.trim_matches(python_space).into(), embed),
                ));
            }
        }
    }
    if let Some(highlight) = rest.strip_prefix("==") {
        if let Some(end) = highlight.find("==") {
            if end > 0 && !highlight[..end].contains('\n') {
                return Some((
                    index + end + 4,
                    Extension::Highlight(highlight[..end].into()),
                ));
            }
        }
    }
    if !inline_only
        && rest.starts_with("$$")
        && source[line_start..index]
            .trim_matches(python_space)
            .is_empty()
    {
        if let Some(end) = rest[2..].find("$$").map(|end| end + 2) {
            let line = rest[end + 2..].split('\n').next().unwrap_or("");
            let content = &rest[2..end];
            if line.trim_matches(python_space).is_empty() && !content.contains("\n\n") {
                return Some((
                    index + end + 2,
                    Extension::Math(content.trim_matches(python_space).into(), true),
                ));
            }
        }
    }
    if first == '$' && !rest.starts_with("$$") {
        let previous = source[..index].chars().next_back();
        let next = rest[1..].chars().next();
        if !previous.is_some_and(|ch| ch.is_ascii_digit())
            && next.is_some_and(|ch| !python_space(ch) && ch != '$')
        {
            let closing = rest[1..]
                .char_indices()
                .find_map(|(offset, ch)| {
                    if ch == '\n' {
                        Some(None)
                    } else if ch == '$' && !escaped_before(rest, offset + 1) {
                        Some(Some(offset + 1))
                    } else {
                        None
                    }
                })
                .flatten();
            if let Some(end) = closing {
                if end > 1
                    && !rest[..end].chars().next_back().is_some_and(python_space)
                    && !rest[end + 1..]
                        .chars()
                        .next()
                        .is_some_and(|ch| ch.is_ascii_digit())
                {
                    return Some((index + end + 1, Extension::Math(rest[1..end].into(), false)));
                }
            }
        }
    }
    if first == '#'
        && (index == 0
            || source[..index]
                .chars()
                .next_back()
                .is_some_and(python_space))
    {
        let end = rest[1..]
            .char_indices()
            .find_map(|(offset, ch)| {
                (python_space(ch) || "#.,!?;:()[]{}<>".contains(ch)).then_some(offset + 1)
            })
            .unwrap_or(rest.len());
        let tag = &rest[1..end];
        if !tag.is_empty()
            && tag.chars().any(|ch| {
                matches!(
                    unicode_general_category::get_general_category(ch),
                    unicode_general_category::GeneralCategory::UppercaseLetter
                        | unicode_general_category::GeneralCategory::LowercaseLetter
                        | unicode_general_category::GeneralCategory::TitlecaseLetter
                        | unicode_general_category::GeneralCategory::ModifierLetter
                        | unicode_general_category::GeneralCategory::OtherLetter
                )
            })
        {
            return Some((index + end, Extension::Tag(tag.into())));
        }
    }
    None
}
fn backtick_end(
    protection: &CodeProtection,
    index: usize,
    count: usize,
    limit: usize,
) -> Option<usize> {
    let runs = protection.backtick_runs.get(&count)?;
    let next = runs.partition_point(|start| *start < index + count);
    let end = runs.get(next)? + count;
    (end <= limit).then_some(end)
}
fn destination_end(source: &str, index: usize) -> Option<usize> {
    if source.as_bytes().get(index) != Some(&b'(') || !source[..index].ends_with(']') {
        return None;
    }
    let mut depth = 0;
    for (offset, ch) in source[index..].char_indices() {
        if ch == '(' && !escaped_before(source, index + offset) {
            depth += 1;
        } else if ch == ')' && !escaped_before(source, index + offset) {
            depth -= 1;
            if depth == 0 {
                return Some(index + offset + 1);
            }
        }
    }
    None
}
fn inline_note_end(
    source: &str,
    index: usize,
    limit: usize,
    protection: &CodeProtection,
) -> Option<usize> {
    let source = &source[..limit];
    let mut cursor = index + 2;
    let mut depth = 1;
    let mut line_start = source[..cursor].rfind('\n').map_or(0, |index| index + 1);
    while cursor < limit {
        let ch = source[cursor..].chars().next()?;
        if !escaped_before(source, cursor) {
            if ch == '`' {
                let count = source[cursor..]
                    .bytes()
                    .take_while(|ch| *ch == b'`')
                    .count();
                let end = backtick_end(protection, cursor, count, limit).unwrap_or(cursor + count);
                if let Some(newline) = source[cursor..end].rfind('\n') {
                    line_start = cursor + newline + 1;
                }
                cursor = end;
                continue;
            }
            if let Some(end) = destination_end(source, cursor) {
                if let Some(newline) = source[cursor..end].rfind('\n') {
                    line_start = cursor + newline + 1;
                }
                cursor = end;
                continue;
            }
            if let Some((end, _)) = extension_at(source, cursor, line_start, true) {
                cursor = end;
                continue;
            }
            if ch == '[' {
                depth += 1;
            } else if ch == ']' {
                depth -= 1;
                if depth == 0 {
                    return Some(cursor + 1);
                }
            }
        }
        cursor += ch.len_utf8();
        if ch == '\n' {
            line_start = cursor;
        }
    }
    None
}
fn prepare(source: &str) -> Result<Prepared, ()> {
    let mut prefix = "LOCALBRAINMARKER".to_string();
    while source.contains(&prefix) {
        prefix.push('X');
    }
    let mut prepared = Prepared {
        source: String::new(),
        body_end: 0,
        prefix,
        extensions: Vec::new(),
        footnotes: Footnotes::default(),
        named_notes: BTreeSet::new(),
        references: BTreeMap::new(),
        removed_lines: Vec::new(),
    };
    prepare_segment(source, &mut prepared, false, 0)?;
    prepared.body_end = prepared.source.len();
    for slot in &mut prepared.footnotes.slots {
        if let FootnoteSlot::Inline(body) = slot {
            let start = prepared.source.len();
            prepared.source.push_str(&body.source);
            offset_nodes(&mut body.nodes, start);
        }
    }
    Ok(prepared)
}
fn offset_nodes(nodes: &mut [Node], offset: usize) {
    for node in nodes {
        node.range.start += offset;
        node.range.end += offset;
        offset_nodes(&mut node.children, offset);
    }
}
fn prepare_inline_note(
    source: &str,
    prepared: &mut Prepared,
    inline_note_depth: usize,
) -> Result<InlineNote, ()> {
    // Excessive nesting is an explicit failure boundary; never rely on catching
    // a stack overflow or omit part of the original source.
    if inline_note_depth >= MAX_INLINE_NOTE_DEPTH {
        return Err(());
    }
    let outer_source = std::mem::take(&mut prepared.source);
    let outer_lines = std::mem::take(&mut prepared.removed_lines);
    let result = prepare_segment(source, prepared, true, inline_note_depth + 1);
    let source = std::mem::replace(&mut prepared.source, outer_source);
    prepared.removed_lines = outer_lines;
    result?;
    let events = parser::inline_events(&source, &prepared.references)?;
    let body = nodes(&mut events.into_iter().peekable());
    if body.len() != 1 || !matches!(body[0].tag, Some(Tag::Paragraph)) {
        return Err(());
    }
    Ok(InlineNote {
        source,
        nodes: body,
    })
}
fn prepare_segment(
    source: &str,
    prepared: &mut Prepared,
    inline_only: bool,
    inline_note_depth: usize,
) -> Result<(), ()> {
    // The parser owns block code and inline block boundaries, including tight
    // lists without Paragraph events. Inline delimiters are matched at the real
    // preprocessing cursor because earlier extensions can consume backticks.
    let protection = code_protection(source, inline_only.then_some(&prepared.references))?;
    if !inline_only {
        prepared.named_notes = protection.named_notes.clone();
        prepared.references = protection.references.clone();
    }
    let mut code_ranges = protection.blocks.iter().peekable();
    let mut inline_scopes = protection.inline_scopes.iter().peekable();
    let mut index = 0;
    let mut line_start = 0;
    while index < source.len() {
        while code_ranges.peek().is_some_and(|range| range.start < index) {
            code_ranges.next();
        }
        if let Some(range) = code_ranges.peek().filter(|range| range.start == index) {
            let end = range.end;
            let raw = &source[index..end];
            prepared.source.push_str(raw);
            if let Some(newline) = raw.rfind('\n') {
                line_start = index + newline + 1;
            }
            index = end;
            code_ranges.next();
            continue;
        }
        let rest = &source[index..];
        let first = rest.chars().next().unwrap();
        if first == '`' && !escaped_before(source, index) {
            let count = rest.bytes().take_while(|ch| *ch == b'`').count();
            while inline_scopes.peek().is_some_and(|scope| scope.end <= index) {
                inline_scopes.next();
            }
            let end = inline_scopes
                .peek()
                .filter(|scope| scope.start <= index)
                .and_then(|scope| backtick_end(&protection, index, count, scope.end))
                .unwrap_or(index + count);
            let raw = &source[index..end];
            prepared.source.push_str(raw);
            if let Some(newline) = raw.rfind('\n') {
                line_start = index + newline + 1;
            }
            index = end;
            continue;
        }
        if !escaped_before(source, index) {
            // A Markdown destination is data for the link rule, never inline syntax.
            if let Some(end) = destination_end(source, index) {
                let raw = &source[index..end];
                prepared.source.push_str(raw);
                if let Some(newline) = raw.rfind('\n') {
                    line_start = index + newline + 1;
                }
                index = end;
                continue;
            }
            if rest.starts_with("^[") {
                while inline_scopes.peek().is_some_and(|scope| scope.end <= index) {
                    inline_scopes.next();
                }
                if let Some(end) = inline_scopes
                    .peek()
                    .filter(|scope| scope.start <= index)
                    .and_then(|scope| inline_note_end(source, index, scope.end, &protection))
                {
                    let slot = prepared.footnotes.slots.len();
                    let body = prepare_inline_note(
                        &source[index + 2..end - 1],
                        prepared,
                        inline_note_depth,
                    )?;
                    prepared.footnotes.publish_inline(slot, body)?;
                    let raw = &source[index..end];
                    marker(
                        prepared,
                        raw,
                        Extension::Footnote {
                            index: slot,
                            sub: 0,
                        },
                    );
                    if let Some(newline) = raw.rfind('\n') {
                        line_start = index + newline + 1;
                    }
                    index = end;
                    continue;
                }
            }
            if rest.starts_with("[^") {
                while inline_scopes.peek().is_some_and(|scope| scope.end <= index) {
                    inline_scopes.next();
                }
                if let Some(end) = rest.find(']') {
                    let label = &rest[2..end];
                    if !label.chars().any(|ch| matches!(ch, ' ' | '\n'))
                        && prepared.named_notes.contains(label)
                        && inline_scopes
                            .peek()
                            .is_some_and(|scope| scope.start <= index)
                    {
                        let (slot, sub) = prepared.footnotes.named_reference(label)?;
                        marker(
                            prepared,
                            &rest[..end + 1],
                            Extension::Footnote { index: slot, sub },
                        );
                        index += end + 1;
                        continue;
                    }
                }
            }
            if let Some((end, extension)) = extension_at(source, index, line_start, inline_only) {
                let raw = &source[index..end];
                marker(prepared, raw, extension);
                if let Some(newline) = raw.rfind('\n') {
                    line_start = index + newline + 1;
                }
                index = end;
                continue;
            }
        }
        prepared.source.push(first);
        index += first.len_utf8();
        if first == '\n' {
            line_start = index;
        }
    }
    Ok(())
}

pub fn render_markdown(source: &str, options: &MarkdownOptions<'_>) -> MarkdownRenderResult {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        render(
            source,
            options,
            0,
            &options
                .reference_context
                .map(|context| vec![context.current_document_id()])
                .unwrap_or_default(),
        )
    }))
    .unwrap_or_else(|_| {
        let (body, properties) = properties(source);
        let body = strip_comments(&body);
        fallback(&body, properties)
    })
}
fn fallback(source: &str, properties: Vec<MarkdownProperty>) -> MarkdownRenderResult {
    MarkdownRenderResult {
        html: format!(
            "<pre class=\"markdown-render-fallback\">{}</pre>",
            escape(source)
        ),
        state: "fallback".into(),
        properties,
    }
}
fn render(
    source: &str,
    options: &MarkdownOptions<'_>,
    depth: usize,
    stack: &[i64],
) -> MarkdownRenderResult {
    if source.is_empty() {
        return MarkdownRenderResult {
            html: String::new(),
            state: "empty".into(),
            properties: Vec::new(),
        };
    }
    let (body, properties) = properties(source);
    let body = strip_comments(&body);
    if body.is_empty() {
        return MarkdownRenderResult {
            html: String::new(),
            state: if properties.is_empty() {
                "empty"
            } else {
                "ready"
            }
            .into(),
            properties,
        };
    }
    let normalized = body
        .replace("\r\n", "\n")
        .replace('\r', "\n")
        .replace('\0', "\u{fffd}");
    let Ok(prepared) = prepare(&normalized) else {
        return fallback(&body, properties);
    };
    let Ok(events) = parser::events(&prepared.source[..prepared.body_end]) else {
        return fallback(&body, properties);
    };
    if events
        .iter()
        .any(|(event, _)| matches!(event, Event::FootnoteReference(_)))
    {
        return fallback(&body, properties);
    }
    let tree = nodes(&mut events.into_iter().peekable());
    let mut definitions = BTreeMap::new();
    collect_note_definitions(&tree, &mut definitions);
    let mut renderer = Renderer {
        prepared: &prepared,
        original: &normalized,
        options,
        depth,
        stack,
        headings: BTreeMap::new(),
        definitions,
        table_head: false,
        table_alignments: Vec::new(),
        table_column: 0,
    };
    let html = renderer.render_nodes(&tree) + &renderer.render_footnotes();
    MarkdownRenderResult {
        html,
        state: "ready".into(),
        properties,
    }
}
fn properties(source: &str) -> (String, Vec<MarkdownProperty>) {
    let lines = splitlines_keepends(source);
    if lines
        .first()
        .is_none_or(|line| line.trim_matches(python_space) != "---")
    {
        return (source.into(), Vec::new());
    }
    let Some(end) = lines.iter().enumerate().skip(1).find_map(|(index, line)| {
        matches!(line.trim_matches(python_space), "---" | "...").then_some(index)
    }) else {
        return (source.into(), Vec::new());
    };
    let payload = lines[1..end].concat();
    let Ok(SafeYaml::Mapping(values)) = safe_load(&payload) else {
        return (source.into(), Vec::new());
    };
    if values
        .iter()
        .any(|(key, value)| key.as_str().is_none() || value.has_recursive_alias())
    {
        return (source.into(), Vec::new());
    }
    let properties = values
        .into_iter()
        .map(|(key, value)| MarkdownProperty {
            name: key.as_str().unwrap().into(),
            value: value.property_value(),
        })
        .collect();
    (lines[end + 1..].concat(), properties)
}
fn strip_comments(source: &str) -> String {
    let mut result = String::new();
    let (mut comment, mut fence) = (false, None);
    for line in splitlines_keepends(source) {
        let stripped = line.trim_start_matches(python_space);
        let found = stripped
            .chars()
            .next()
            .filter(|ch| matches!(ch, '`' | '~'))
            .filter(|ch| stripped.chars().take_while(|value| value == ch).count() >= 3);
        if !comment {
            if let Some(found) = found {
                if fence.is_none() {
                    fence = Some(found);
                } else if fence == Some(found) {
                    fence = None;
                }
                result.push_str(line);
                continue;
            }
        }
        if fence.is_some() {
            result.push_str(line);
            continue;
        }
        let (mut index, mut ticks) = (0, 0);
        while index < line.len() {
            let rest = &line[index..];
            if comment {
                if let Some(end) = rest.find("%%") {
                    comment = false;
                    index += end + 2;
                } else {
                    if line.ends_with('\n') {
                        result.push('\n');
                    }
                    break;
                }
                continue;
            }
            if rest.starts_with('`') {
                let run = rest.bytes().take_while(|ch| *ch == b'`').count();
                if ticks == 0 {
                    ticks = run;
                } else if ticks == run {
                    ticks = 0;
                }
                result.push_str(&rest[..run]);
                index += run;
                continue;
            }
            if ticks == 0 && rest.starts_with("%%") {
                comment = true;
                index += 2;
                continue;
            }
            let ch = rest.chars().next().unwrap();
            result.push(ch);
            index += ch.len_utf8();
        }
    }
    result
}
fn plain(nodes: &[Node]) -> String {
    nodes
        .iter()
        .map(|node| match &node.event {
            Some(
                Event::Text(value)
                | Event::Code(value)
                | Event::Html(value)
                | Event::InlineHtml(value),
            ) => value.to_string(),
            Some(Event::SoftBreak | Event::HardBreak) => "\n".into(),
            _ => plain(&node.children),
        })
        .collect()
}
static CALLOUT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^\[!([A-Za-z0-9_-]+)\]([+-])?(?:[ \t]+([^\n]+))?").unwrap());
static SESSION: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^/sessions/[1-9][0-9]*$").unwrap());
static APP_ROUTE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^/(?:help(?:/[a-z-]+)?|sessions-dashboard|sessions|projects|context|context-search|natural-search|terminal|settings)$").unwrap()
});

struct Renderer<'a, 'b> {
    prepared: &'a Prepared,
    original: &'a str,
    options: &'a MarkdownOptions<'b>,
    depth: usize,
    stack: &'a [i64],
    headings: BTreeMap<String, usize>,
    definitions: BTreeMap<String, Vec<Node>>,
    table_head: bool,
    table_alignments: Vec<Alignment>,
    table_column: usize,
}
impl Renderer<'_, '_> {
    fn render_nodes(&mut self, nodes: &[Node]) -> String {
        nodes.iter().map(|node| self.render_node(node)).collect()
    }
    fn render_node(&mut self, node: &Node) -> String {
        if let Some(tag) = &node.tag {
            return match tag {
                Tag::Paragraph => {
                    let content = plain(&node.children);
                    if content.trim_matches(python_space).starts_with("$$")
                        && content.trim_matches(python_space).ends_with("$$")
                    {
                        let literal = self.container_paragraph_source(node);
                        let literal = literal.trim_matches(python_space);
                        if literal.len() >= 4
                            && literal.starts_with("$$")
                            && literal.ends_with("$$")
                        {
                            return math(
                                literal[2..literal.len() - 2].trim_matches(python_space),
                                true,
                            );
                        }
                    }
                    if let Some(index) = self.sole_marker(content.trim_matches(python_space)) {
                        if matches!(
                            self.prepared.extensions[index].1,
                            Extension::Wiki(_, true) | Extension::Math(_, true)
                        ) {
                            return self.extension(index, true);
                        }
                    }
                    let (mut children, identifier) = self.block_id(&node.children);
                    let body = self.render_nodes(&children);
                    children.clear();
                    format!(
                        "<p{}>{body}</p>\n",
                        identifier.map_or(String::new(), |id| format!(
                            " id=\"{}\"",
                            escape(&block_anchor(&id))
                        ))
                    )
                }
                Tag::Heading { level, .. } => {
                    let removed = self
                        .prepared
                        .removed_lines
                        .partition_point(|(offset, _)| *offset <= node.range.start);
                    let removed = removed
                        .checked_sub(1)
                        .map_or(0, |index| self.prepared.removed_lines[index].1);
                    let line = removed
                        + self.prepared.source[..node.range.start.min(self.prepared.source.len())]
                            .bytes()
                            .filter(|ch| *ch == b'\n')
                            .count();
                    let original = self
                        .original
                        .split('\n')
                        .nth(line)
                        .unwrap_or("")
                        .trim_start_matches(' ');
                    let title = if original.starts_with('#') {
                        original
                            .trim_start_matches('#')
                            .trim_start_matches([' ', '\t'])
                            .trim_end_matches([' ', '\t', '#'])
                    } else {
                        original
                    };
                    let key = heading_slug(title);
                    let count = self.headings.entry(key).or_default();
                    *count += 1;
                    let anchor = heading_anchor(title, *count);
                    let (children, block) = self.block_id(&node.children);
                    let anchor = block.map_or(anchor, |block| block_anchor(&block));
                    let body = self.render_nodes(&children);
                    format!("<{level} id=\"{}\">{body}</{level}>\n", escape(&anchor))
                }
                Tag::BlockQuote(_) => {
                    let callout = node
                        .children
                        .first()
                        .filter(|node| matches!(node.tag, Some(Tag::Paragraph)))
                        .and_then(|first| {
                            CALLOUT.captures(&plain(&first.children)).map(|capture| {
                                (
                                    capture[1].to_ascii_lowercase(),
                                    capture.get(2).map(|v| v.as_str().to_string()),
                                    capture.get(3).map_or_else(
                                        || title_case(&capture[1].replace('-', " ")),
                                        |v| {
                                            self.restore(v.as_str())
                                                .trim_matches(python_space)
                                                .to_string()
                                        },
                                    ),
                                )
                            })
                        });
                    if let Some((kind, fold, title)) = callout {
                        let first = &node.children[0];
                        let mut children = first.children.clone();
                        let boundary = children.iter().position(|child| {
                            matches!(child.event, Some(Event::SoftBreak | Event::HardBreak))
                        });
                        let rest = if let Some(boundary) = boundary {
                            self.render_nodes(&children.split_off(boundary))
                        } else {
                            String::new()
                        };
                        let tail = self.render_nodes(&node.children[1..]);
                        format!("<blockquote class=\"markdown-callout markdown-callout-{kind}\" data-callout=\"{kind}\"{}>\n<p><span class=\"markdown-callout-title\">{}</span>{rest}</p>\n{tail}</blockquote>\n",fold.map_or(String::new(),|fold|format!(" data-callout-fold=\"{fold}\"")),escape(&title))
                    } else {
                        format!(
                            "<blockquote>\n{}</blockquote>\n",
                            self.render_nodes(&node.children)
                        )
                    }
                }
                Tag::CodeBlock(kind) => {
                    let code = plain(&node.children);
                    if let CodeBlockKind::Fenced(info) = kind {
                        self.fence(&code, info)
                    } else {
                        format!("<pre><code>{}</code></pre>\n", escape(&code))
                    }
                }
                Tag::HtmlBlock => format!("<p>{}</p>\n", self.render_nodes(&node.children)),
                Tag::List(start) => {
                    let task = node.children.iter().any(contains_task);
                    let name = if start.is_some() { "ol" } else { "ul" };
                    let start = start
                        .filter(|start| *start != 1)
                        .map_or(String::new(), |start| format!(" start=\"{start}\""));
                    format!(
                        "<{name}{start}{}>\n{}</{name}>\n",
                        if task {
                            " class=\"contains-task-list\""
                        } else {
                            ""
                        },
                        self.render_nodes(&node.children)
                    )
                }
                Tag::Item => format!(
                    "<li{}>{}</li>\n",
                    if node.children.iter().any(|node| matches!(
                        node.event,
                        Some(Event::TaskListMarker(_))
                    ) || matches!(
                        node.tag,
                        Some(Tag::Paragraph)
                    ) && node
                        .children
                        .iter()
                        .any(|child| matches!(child.event, Some(Event::TaskListMarker(_)))))
                    {
                        " class=\"task-list-item\""
                    } else {
                        ""
                    },
                    self.render_nodes(&node.children)
                ),
                Tag::Emphasis => format!("<em>{}</em>", self.render_nodes(&node.children)),
                Tag::Strong => format!("<strong>{}</strong>", self.render_nodes(&node.children)),
                Tag::Strikethrough => format!("<s>{}</s>", self.render_nodes(&node.children)),
                Tag::Link {
                    dest_url, title, ..
                } => {
                    let body = self.render_nodes(&node.children);
                    let decoded = unquote(dest_url);
                    let decoded = decoded.trim_matches(python_space);
                    if matches!(
                        scheme(decoded).as_deref(),
                        Some("javascript" | "vbscript" | "data" | "file")
                    ) {
                        escape(
                            &self.restore(
                                self.prepared
                                    .source
                                    .get(node.range.clone())
                                    .unwrap_or(decoded),
                            ),
                        )
                    } else {
                        self.link(decoded, &body, title)
                    }
                }
                Tag::Image { .. } => deferred(
                    "Image",
                    self.restore(&plain(&node.children))
                        .trim_matches(python_space),
                ),
                Tag::Table(alignments) => {
                    let previous =
                        std::mem::replace(&mut self.table_alignments, alignments.clone());
                    let body = self.render_nodes(&node.children);
                    self.table_alignments = previous;
                    format!("<div class=\"markdown-table-scroll\"><table>\n{body}</tbody></table></div>\n")
                }
                Tag::TableHead => {
                    self.table_head = true;
                    self.table_column = 0;
                    let body = self.render_nodes(&node.children);
                    self.table_head = false;
                    format!("<thead>\n<tr>{body}</tr>\n</thead>\n<tbody>\n")
                }
                Tag::TableRow => {
                    self.table_column = 0;
                    format!("<tr>{}</tr>\n", self.render_nodes(&node.children))
                }
                Tag::TableCell => {
                    let tag = if self.table_head { "th" } else { "td" };
                    let alignment = match self.table_alignments.get(self.table_column) {
                        Some(Alignment::Left) => " style=\"text-align:left\"",
                        Some(Alignment::Center) => " style=\"text-align:center\"",
                        Some(Alignment::Right) => " style=\"text-align:right\"",
                        _ => "",
                    };
                    self.table_column += 1;
                    format!(
                        "<{tag}{alignment}>{}</{tag}>",
                        self.render_nodes(&node.children)
                    )
                }
                Tag::FootnoteDefinition(_) => String::new(),
                _ => self.render_nodes(&node.children),
            };
        }
        match node.event.as_ref().unwrap(){
            Event::Text(value)=>self.text(value),Event::Code(value)=>format!("<code>{}</code>",escape(value)),Event::Html(value)|Event::InlineHtml(value)=>self.text(value),
            Event::SoftBreak|Event::HardBreak=>"<br />\n".into(),Event::Rule=>"<hr />\n".into(),
            Event::TaskListMarker(checked)=>format!("<input class=\"task-list-item-checkbox\"{} disabled=\"disabled\" type=\"checkbox\">",if *checked{" checked=\"checked\""}else{""}),
            Event::FootnoteReference(name)=>escape(&format!("[^{name}]")),
            _=>String::new(),
        }
    }
    fn block_id(&self, nodes: &[Node]) -> (Vec<Node>, Option<String>) {
        let mut children = nodes.to_vec();
        for node in children.iter_mut().rev() {
            if let Some(Event::Text(value)) = &node.event {
                if let Some(found) = BLOCK_ID.captures(value) {
                    let identifier = found[1].to_string();
                    let body = BLOCK_ID
                        .replace(value, "")
                        .trim_end_matches(python_space)
                        .to_string();
                    node.event = Some(Event::Text(body.into()));
                    return (children, Some(identifier));
                }
                break;
            }
        }
        (children, None)
    }
    fn container_paragraph_source(&self, node: &Node) -> String {
        let raw = self.prepared.source.get(node.range.clone()).unwrap_or("");
        let prefix = self.prepared.source[..node.range.start]
            .rsplit('\n')
            .next()
            .unwrap_or("");
        let quotes = prefix.chars().filter(|ch| *ch == '>').count();
        let indent = prefix.chars().count();
        let lines: Vec<_> = raw
            .split_inclusive('\n')
            .enumerate()
            .map(|(index, line)| {
                if index == 0 {
                    return line.to_string();
                }
                let mut line = line;
                if quotes > 0 {
                    for _ in 0..quotes {
                        line = line.trim_start_matches([' ', '\t']);
                        if let Some(rest) = line.strip_prefix('>') {
                            line = rest.strip_prefix(' ').unwrap_or(rest);
                        } else {
                            break;
                        }
                    }
                } else {
                    let bytes = line
                        .char_indices()
                        .take_while(|(_, ch)| matches!(ch, ' ' | '\t'))
                        .take(indent)
                        .last()
                        .map_or(0, |(index, ch)| index + ch.len_utf8());
                    line = &line[bytes..];
                }
                line.to_string()
            })
            .collect();
        self.restore(&lines.concat())
    }
    fn sole_marker(&self, text: &str) -> Option<usize> {
        text.strip_prefix(&self.prepared.prefix)?
            .strip_suffix("END")?
            .parse::<usize>()
            .ok()
            .filter(|index| *index < self.prepared.extensions.len())
    }
    fn text(&mut self, text: &str) -> String {
        let mut result = String::new();
        let mut remaining = text;
        while let Some(start) = remaining.find(&self.prepared.prefix) {
            result.push_str(&escape(&remaining[..start]));
            let tail = &remaining[start..];
            if let Some(end) = tail.find("END").map(|index| index + 3) {
                if let Some(index) = self.sole_marker(&tail[..end]) {
                    result.push_str(&self.extension(index, false));
                    remaining = &tail[end..];
                    continue;
                }
            }
            result.push_str(&escape(tail));
            return result;
        }
        result.push_str(&escape(remaining));
        result
    }
    fn restore(&self, text: &str) -> String {
        let mut text = text.to_string();
        for (index, (raw, _)) in self.prepared.extensions.iter().enumerate() {
            text = text.replace(&format!("{}{index}END", self.prepared.prefix), raw);
        }
        text
    }
    fn extension(&mut self, index: usize, block: bool) -> String {
        match self.prepared.extensions[index].1.clone() {
            Extension::Highlight(value) => format!("<mark>{}</mark>", escape(&value)),
            Extension::Tag(value) => format!(
                "<span class=\"markdown-tag\" data-tag=\"{}\">#{}</span>",
                escape(&casefold(&value)),
                escape(&value)
            ),
            Extension::Math(value, display) => math(&value, display),
            Extension::Wiki(value, embed) => self.wiki(&value, embed, block),
            Extension::Footnote { index, sub } => Self::footnote_reference(index, sub),
        }
    }
    fn footnote_reference(index: usize, sub: usize) -> String {
        let number = index + 1;
        let suffix = if sub == 0 {
            String::new()
        } else {
            format!(":{sub}")
        };
        format!("<sup class=\"footnote-ref\"><a href=\"#fn{number}\" id=\"fnref{number}{suffix}\">[{number}{suffix}]</a></sup>")
    }
    fn link(&self, target: &str, body: &str, title: &str) -> String {
        if external_url(target) {
            return external(target, body);
        }
        if scheme(target).is_some() {
            return state_body(body, "unsafe");
        }
        if let Some(fragment) = target.strip_prefix('#') {
            return if let Some(anchor) = resolve_document_fragment(self.original, fragment) {
                internal(&format!("#{anchor}"), body, title)
            } else {
                state_body(body, "missing")
            };
        }
        let session =
            self.options.trusted_session_routes.contains(target) && SESSION.is_match(target);
        let app = self.options.app_doc_routes.contains(target) && APP_ROUTE.is_match(target);
        if session || app {
            let mut target = target.to_string();
            if app && target.starts_with("/help") {
                if let Some(language) = self
                    .options
                    .app_doc_language
                    .filter(|language| matches!(*language, "ko" | "en"))
                {
                    target.push_str("?lang=");
                    target.push_str(language);
                }
            }
            return internal(&target, body, title);
        }
        let Some(context) = self.options.reference_context else {
            return state_body(body, "no-source");
        };
        let resolution = context.resolve(target, "markdown");
        if resolution.state == "resolved" {
            internal(resolution.href.as_deref().unwrap_or(""), body, title)
        } else {
            state_body(body, &resolution.state)
        }
    }
    fn wiki(&mut self, value: &str, embed: bool, block: bool) -> String {
        let (target, label) = wiki_target(value);
        if embed && (attachment(&target) || scheme(&unquote(&target)).is_some()) {
            return deferred("Attachment", &label);
        }
        let Some(context) = self.options.reference_context else {
            if !embed {
                if let Some(fragment) = target.strip_prefix('#') {
                    if let Some(anchor) = resolve_document_fragment(self.original, fragment) {
                        return internal(&format!("#{anchor}"), &escape(&label), "");
                    }
                }
            }
            return reference_state(&label, "no-source", embed);
        };
        let resolution = context.resolve(&target, "wiki");
        if !embed {
            return match resolution.state.as_str() {
                "resolved" => internal(
                    resolution.href.as_deref().unwrap_or(""),
                    &escape(&label),
                    "",
                ),
                "external" => external(resolution.href.as_deref().unwrap_or(""), &escape(&label)),
                _ => reference_state(&label, &resolution.state, false),
            };
        }
        let Some(document) = resolution
            .document
            .filter(|_| resolution.state == "resolved")
        else {
            return reference_state(&label, &resolution.state, true);
        };
        if !document.is_markdown() {
            return deferred("Attachment", &label);
        }
        let href = resolution.href.unwrap_or_default();
        if !block {
            return format!("<span class=\"markdown-note-embed-inline\" data-reference-state=\"resolved\"><a href=\"{}\">[Embedded note: {}]</a></span>",escape(&href),escape(&label));
        }
        if self.stack.contains(&document.id) {
            return reference_state(&label, "cycle", true);
        }
        if self.depth >= 3 {
            return reference_state(&label, "depth-limit", true);
        }
        let Some(source) =
            extract_document_fragment(&document.body, resolution.fragment.as_deref())
        else {
            return reference_state(&label, "missing", true);
        };
        let Ok(context) = context.for_document(document.id) else {
            return reference_state(&label, "missing", true);
        };
        let mut stack = self.stack.to_vec();
        stack.push(document.id);
        let options = MarkdownOptions {
            reference_context: Some(&context),
            ..Default::default()
        };
        let nested = render(&source, &options, self.depth + 1, &stack);
        format!("<article class=\"markdown-note-embed\" data-reference-state=\"resolved\" data-document-id=\"{}\"><header class=\"markdown-note-embed-header\"><a href=\"{}\">{}</a></header><div class=\"markdown-note-embed-body\">{}</div></article>",document.id,escape(&href),escape(&document.title),nested.html)
    }
    fn fence(&self, code: &str, info: &str) -> String {
        let requested = lowercase(language(info));
        let canonical = canonical(&requested);
        let class = language_class(&requested);
        let display = if requested.is_empty() {
            "Code"
        } else {
            canonical.map_or(requested.as_str(), label)
        };
        format!("<figure class=\"markdown-code-block\"{}><figcaption class=\"markdown-code-label\">{}</figcaption><pre><code{}>{}</code></pre></figure>\n",
            if class.is_empty(){String::new()}else{format!(" data-language=\"{}\"",escape(canonical.unwrap_or(&class)))},escape(display),if class.is_empty(){String::new()}else{format!(" class=\"language-{}\"",escape(&class))},highlight_code(code,&requested))
    }
    fn render_footnotes(&mut self) -> String {
        let prepared = self.prepared;
        if prepared.footnotes.slots.is_empty() {
            return String::new();
        }
        let mut result = "<hr class=\"footnotes-sep\" />\n<section class=\"footnotes\">\n<ol class=\"footnotes-list\">\n".to_string();
        for (slot, note) in prepared.footnotes.slots.iter().enumerate() {
            let index = slot + 1;
            let (mut body, count) = match note {
                FootnoteSlot::Inline(note) => (
                    format!("<p>{}</p>\n", self.render_nodes(&note.nodes[0].children)),
                    1,
                ),
                FootnoteSlot::Named { label, count } => {
                    let nodes = self.definitions.get(label).cloned().unwrap_or_default();
                    (self.render_nodes(&nodes), (*count).max(1))
                }
            };
            let links = (0..count)
                .map(|sub| {
                    let suffix = if sub == 0 {
                        String::new()
                    } else {
                        format!(":{sub}")
                    };
                    format!(" <a href=\"#fnref{index}{suffix}\" class=\"footnote-backref\">↩︎</a>")
                })
                .collect::<String>();
            if body.ends_with("</p>\n") {
                body.insert_str(body.len() - 5, &links);
            } else {
                body.push_str(&links);
            }
            result.push_str(&format!(
                "<li id=\"fn{index}\" class=\"footnote-item\">{body}</li>\n"
            ));
        }
        result.push_str("</ol>\n</section>\n");
        result
    }
}
fn collect_note_definitions(nodes: &[Node], definitions: &mut BTreeMap<String, Vec<Node>>) {
    for node in nodes {
        if let Some(Tag::FootnoteDefinition(name)) = &node.tag {
            definitions.insert(name.to_string(), node.children.clone());
        }
        collect_note_definitions(&node.children, definitions);
    }
}
fn contains_task(node: &Node) -> bool {
    matches!(node.event, Some(Event::TaskListMarker(_))) || node.children.iter().any(contains_task)
}
fn language_class(value: &str) -> String {
    let mut result = String::new();
    let mut dash = false;
    for ch in value.chars() {
        if ch.is_ascii_lowercase() || ch.is_ascii_digit() || matches!(ch, '_' | '-') {
            if dash && !result.is_empty() {
                result.push('-');
            }
            dash = false;
            result.push(ch);
        } else {
            dash = true;
        }
    }
    result.trim_matches('-').chars().take(40).collect()
}
fn title_case(value: &str) -> String {
    value
        .split_whitespace()
        .map(|word| {
            let mut chars = word.chars();
            chars.next().map_or(String::new(), |first| {
                first
                    .to_uppercase()
                    .chain(chars.flat_map(char::to_lowercase))
                    .collect()
            })
        })
        .collect::<Vec<_>>()
        .join(" ")
}
fn wiki_target(value: &str) -> (String, String) {
    if let Some((target, label)) = value.split_once('|') {
        let target = target.trim_matches(python_space);
        let label = label.trim_matches(python_space);
        return (
            target.into(),
            if label.is_empty() { target } else { label }.into(),
        );
    }
    let target = value.trim_matches(python_space);
    let path = target.split('#').next().unwrap_or("");
    let label = if path.is_empty() {
        target.trim_start_matches(['#', '^'])
    } else {
        stem(path)
    };
    (
        target.into(),
        if label.is_empty() { target } else { label }.into(),
    )
}
fn attachment(target: &str) -> bool {
    let decoded = unquote(target);
    let path = decoded.split('#').next().unwrap_or("");
    let suffix = suffix(path).to_ascii_lowercase();
    !suffix.is_empty() && !matches!(suffix.as_str(), ".md" | ".markdown" | ".mdown" | ".mkd")
}
fn deferred(kind: &str, label: &str) -> String {
    format!("<span class=\"markdown-image-deferred\" data-markdown-image-deferred=\"true\" aria-label=\"{} rendering deferred\">[{} deferred{}]</span>",escape(kind),escape(kind),if label.is_empty(){String::new()}else{format!(": {}",escape(label))})
}
fn state_body(body: &str, state: &str) -> String {
    format!("<span class=\"markdown-reference markdown-reference-{state}\" data-reference-state=\"{state}\">{body}</span>")
}
fn reference_state(label: &str, state: &str, embed: bool) -> String {
    format!("<span class=\"markdown-reference markdown-reference-{} markdown-reference-{state}\" data-reference-state=\"{state}\">{}</span>",if embed{"embed"}else{"link"},escape(label))
}
fn internal(href: &str, body: &str, title: &str) -> String {
    format!("<a class=\"markdown-reference markdown-reference-internal\" data-reference-state=\"resolved\" href=\"{}\"{}>{body}</a>",escape(href),if title.is_empty(){String::new()}else{format!(" title=\"{}\"",escape(title))})
}
fn external(href: &str, body: &str) -> String {
    format!("<a class=\"markdown-reference markdown-reference-external\" data-reference-state=\"external\" data-external-link=\"true\" href=\"{}\" target=\"_blank\" rel=\"noopener noreferrer external\">{body}</a>",escape(href))
}

const MATH_ELEMENTS: &[&str] = &[
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
];
const MATH_ATTRIBUTES: &[&str] = &[
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
];
fn validated_math(value: &str) -> bool {
    let Ok(document) = roxmltree::Document::parse(value) else {
        return false;
    };
    document
        .descendants()
        .filter(|node| node.is_element())
        .all(|node| {
            node.tag_name().namespace() == Some("http://www.w3.org/1998/Math/MathML")
                && MATH_ELEMENTS.contains(&node.tag_name().name())
                && node.attributes().all(|attribute| {
                    attribute.namespace().is_none() && MATH_ATTRIBUTES.contains(&attribute.name())
                })
        })
}
fn math(content: &str, display: bool) -> String {
    let tag = if display { "div" } else { "span" };
    let style = if display {
        latex2mathml::DisplayStyle::Block
    } else {
        latex2mathml::DisplayStyle::Inline
    };
    match latex2mathml::latex_to_mathml(content, style) {
        Ok(value) if validated_math(&value) => {
            format!("<{tag} class=\"markdown-math\">{value}</{tag}>")
        }
        _ => format!(
            "<{tag} class=\"markdown-math markdown-math-fallback\">{}</{tag}>",
            escape(content)
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn mathml_refuses_foreign_elements_attributes_and_namespaces() {
        assert!(validated_math("<math xmlns=\"http://www.w3.org/1998/Math/MathML\" display=\"inline\"><mi>x</mi></math>"));
        for value in["<math xmlns=\"http://www.w3.org/1998/Math/MathML\" href=\"file:///synthetic\"><mi>x</mi></math>",
            "<math xmlns=\"http://www.w3.org/1998/Math/MathML\"><script>bad</script></math>","<math><mi>x</mi></math>",
            "<math xmlns=\"http://www.w3.org/1998/Math/MathML\"><mi xmlns=\"urn:foreign\">x</mi></math>"]{assert!(!validated_math(value));}
    }
}
