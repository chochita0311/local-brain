//! Display Markdown syntax adapter. HTML is disabled in the grammar, so source
//! tags remain prose without suppressing Markdown between or inside those tags.
//! The presentation layer retains its existing event vocabulary and byte ranges.

use ::markdown::{mdast, Constructs, ParseOptions};
use pulldown_cmark::{Alignment, CodeBlockKind, Event, HeadingLevel, LinkType, Tag};
use std::{
    collections::{BTreeMap, BTreeSet},
    ops::Range,
};

pub(super) type SpannedEvent = (Event<'static>, Range<usize>);

#[derive(Clone)]
pub(super) struct Definition {
    url: String,
    title: Option<String>,
}
pub(super) type Definitions = BTreeMap<String, Definition>;
pub(super) struct Parsed {
    pub events: Vec<SpannedEvent>,
    pub definitions: Definitions,
}

fn options(inline: bool) -> ParseOptions {
    let mut options = ParseOptions {
        constructs: Constructs {
            html_flow: false,
            html_text: false,
            gfm_autolink_literal: false,
            ..Constructs::gfm()
        },
        gfm_strikethrough_single_tilde: false,
        ..ParseOptions::default()
    };
    if inline {
        let constructs = &mut options.constructs;
        constructs.block_quote = false;
        constructs.code_fenced = false;
        constructs.code_indented = false;
        constructs.gfm_footnote_definition = false;
        constructs.gfm_label_start_footnote = false;
        constructs.gfm_table = false;
        constructs.heading_atx = false;
        constructs.heading_setext = false;
        constructs.list_item = false;
        constructs.thematic_break = false;
    }
    options
}

pub(super) fn events(source: &str) -> Result<Vec<SpannedEvent>, ()> {
    Ok(parse(source)?.events)
}

pub(super) fn parse(source: &str) -> Result<Parsed, ()> {
    let options = options(false);
    let root = ::markdown::to_mdast(source, &options).map_err(|_| ())?;
    let mut definitions = BTreeMap::new();
    let mut named_notes = BTreeSet::new();
    collect_definitions(&root, &mut definitions, &mut named_notes);
    let mut adapter = Adapter {
        source,
        definitions,
        named_notes,
        events: Vec::new(),
    };
    adapter.node(&root)?;
    Ok(Parsed {
        events: adapter.events,
        definitions: adapter.definitions,
    })
}

pub(super) fn inline_events(
    source: &str,
    definitions: &Definitions,
) -> Result<Vec<SpannedEvent>, ()> {
    // Whitespace guards preserve leading/trailing inline prose and prevent a
    // definition-looking note body from becoming a block definition. NBSP is
    // inline whitespace but cannot be consumed as block indentation.
    const BEFORE: &str = "x\u{a0}";
    const AFTER: &str = "\u{a0}x";
    let mut input = format!("{BEFORE}{source}{AFTER}\n\n");
    for identifier in definitions.keys() {
        input.push_str(&format!("[{identifier}]: localbrain-reference\n"));
    }
    let mdast::Node::Root(root) = ::markdown::to_mdast(&input, &options(true)).map_err(|_| ())?
    else {
        return Err(());
    };
    let Some(mdast::Node::Paragraph(mut paragraph)) = root.children.into_iter().next() else {
        return Err(());
    };
    let Some(mdast::Node::Text(first)) = paragraph.children.first_mut() else {
        return Err(());
    };
    first.value = first.value.strip_prefix(BEFORE).ok_or(())?.to_string();
    first.position.as_mut().ok_or(())?.start.offset = BEFORE.len();
    let Some(mdast::Node::Text(last)) = paragraph.children.last_mut() else {
        return Err(());
    };
    last.value = last.value.strip_suffix(AFTER).ok_or(())?.to_string();
    last.position.as_mut().ok_or(())?.end.offset -= AFTER.len();
    paragraph
        .children
        .retain(|node| !matches!(node, mdast::Node::Text(text) if text.value.is_empty()));
    paragraph.position.as_mut().ok_or(())?.start.offset = BEFORE.len();
    paragraph.position.as_mut().ok_or(())?.end.offset = BEFORE.len() + source.len();
    let mut body = mdast::Node::Paragraph(paragraph);
    subtract_offsets(&mut body, BEFORE.len())?;
    let mut adapter = Adapter {
        source,
        definitions: definitions.clone(),
        named_notes: BTreeSet::new(),
        events: Vec::new(),
    };
    adapter.node(&body)?;
    Ok(adapter.events)
}

fn subtract_offsets(node: &mut mdast::Node, offset: usize) -> Result<(), ()> {
    let position = node.position_mut().ok_or(())?;
    position.start.offset = position.start.offset.checked_sub(offset).ok_or(())?;
    position.end.offset = position.end.offset.checked_sub(offset).ok_or(())?;
    if let Some(children) = node.children_mut() {
        for child in children {
            subtract_offsets(child, offset)?;
        }
    }
    Ok(())
}

fn collect_definitions(
    node: &mdast::Node,
    found: &mut Definitions,
    named_notes: &mut BTreeSet<String>,
) {
    if let mdast::Node::Definition(definition) = node {
        found
            .entry(definition.identifier.clone())
            .or_insert_with(|| Definition {
                url: definition.url.clone(),
                title: definition.title.clone(),
            });
    }
    if let mdast::Node::FootnoteDefinition(note) = node {
        named_notes.insert(note.label.as_ref().unwrap_or(&note.identifier).clone());
    }
    if let Some(children) = node.children() {
        for child in children {
            collect_definitions(child, found, named_notes);
        }
    }
}

struct Adapter<'a> {
    source: &'a str,
    definitions: Definitions,
    named_notes: BTreeSet<String>,
    events: Vec<SpannedEvent>,
}
impl Adapter<'_> {
    fn push(&mut self, event: Event<'static>, range: &Range<usize>) {
        self.events.push((event, range.clone()));
    }

    fn children(&mut self, children: &[mdast::Node]) -> Result<(), ()> {
        for child in children {
            self.node(child)?;
        }
        Ok(())
    }

    fn container(
        &mut self,
        tag: Tag<'static>,
        children: &[mdast::Node],
        range: &Range<usize>,
    ) -> Result<(), ()> {
        let end = tag.to_end();
        self.push(Event::Start(tag), range);
        self.children(children)?;
        self.push(Event::End(end), range);
        Ok(())
    }

    fn item(&mut self, item: &mdast::ListItem, tight: bool) -> Result<(), ()> {
        let range = position(item.position.as_ref())?;
        self.push(Event::Start(Tag::Item), &range);
        for (index, child) in item.children.iter().enumerate() {
            if let mdast::Node::Paragraph(paragraph) = child {
                let range = position(paragraph.position.as_ref())?;
                if !tight {
                    self.push(Event::Start(Tag::Paragraph), &range);
                }
                if index == 0 {
                    if let Some(checked) = item.checked {
                        self.push(Event::TaskListMarker(checked), &range);
                    }
                }
                self.children(&paragraph.children)?;
                if !tight {
                    self.push(Event::End(pulldown_cmark::TagEnd::Paragraph), &range);
                }
            } else {
                self.node(child)?;
            }
        }
        self.push(Event::End(pulldown_cmark::TagEnd::Item), &range);
        Ok(())
    }

    fn node(&mut self, node: &mdast::Node) -> Result<(), ()> {
        let range = position(node.position())?;
        match node {
            mdast::Node::Root(root) => self.children(&root.children)?,
            mdast::Node::Paragraph(paragraph) => {
                self.container(Tag::Paragraph, &paragraph.children, &range)?;
            }
            mdast::Node::Heading(heading) => {
                let level = match heading.depth {
                    1 => HeadingLevel::H1,
                    2 => HeadingLevel::H2,
                    3 => HeadingLevel::H3,
                    4 => HeadingLevel::H4,
                    5 => HeadingLevel::H5,
                    6 => HeadingLevel::H6,
                    _ => return Err(()),
                };
                self.container(
                    Tag::Heading {
                        level,
                        id: None,
                        classes: Vec::new(),
                        attrs: Vec::new(),
                    },
                    &heading.children,
                    &range,
                )?;
            }
            mdast::Node::Blockquote(quote) => {
                self.container(Tag::BlockQuote(None), &quote.children, &range)?;
            }
            mdast::Node::List(list) => {
                let start = list.ordered.then_some(u64::from(list.start.unwrap_or(1)));
                self.push(Event::Start(Tag::List(start)), &range);
                let tight = !list.spread
                    && !list
                        .children
                        .iter()
                        .any(|child| matches!(child, mdast::Node::ListItem(item) if item.spread));
                for child in &list.children {
                    let mdast::Node::ListItem(item) = child else {
                        return Err(());
                    };
                    self.item(item, tight)?;
                }
                self.push(Event::End(Tag::List(start).to_end()), &range);
            }
            mdast::Node::Code(code) => {
                let raw = self.source.get(range.clone()).ok_or(())?;
                let line = raw.split('\n').next().unwrap_or("");
                let indent = line.bytes().take_while(|ch| *ch == b' ').count();
                let fenced = code.lang.is_some()
                    || indent < 4
                        && line[indent..].starts_with(['`', '~'])
                        && line[indent..]
                            .bytes()
                            .take_while(|ch| *ch == line.as_bytes()[indent])
                            .count()
                            >= 3;
                let kind = if fenced {
                    let mut info = code.lang.clone().unwrap_or_default();
                    if let Some(meta) = &code.meta {
                        info.push(' ');
                        info.push_str(meta);
                    }
                    CodeBlockKind::Fenced(info.into())
                } else {
                    CodeBlockKind::Indented
                };
                let has_line = !code.value.is_empty()
                    || fenced && raw.bytes().filter(|ch| *ch == b'\n').take(2).count() == 2;
                self.push(Event::Start(Tag::CodeBlock(kind)), &range);
                let mut value = code.value.clone();
                if has_line {
                    value.push('\n');
                }
                self.push(Event::Text(value.into()), &range);
                self.push(Event::End(pulldown_cmark::TagEnd::CodeBlock), &range);
            }
            mdast::Node::Text(text) => {
                // mdast joins soft line breaks into Text, including decoded LF
                // entities. Only physical source line endings render as <br>.
                let raw = self.source.get(range.clone()).ok_or(())?;
                let breaks = text_line_breaks(raw, super::escaped_before(self.source, range.start));
                let mut breaks = breaks.into_iter();
                let mut start = 0;
                for (index, _) in text.value.match_indices('\n') {
                    if breaks.next().ok_or(())? {
                        if index > start {
                            self.push(
                                Event::Text(text.value[start..index].to_string().into()),
                                &range,
                            );
                        }
                        self.push(Event::SoftBreak, &range);
                        start = index + 1;
                    }
                }
                if start < text.value.len() {
                    self.push(Event::Text(text.value[start..].to_string().into()), &range);
                }
                if breaks.next().is_some() {
                    return Err(());
                }
            }
            mdast::Node::InlineCode(code) => {
                self.push(Event::Code(code.value.replace('\n', " ").into()), &range);
            }
            mdast::Node::Break(_) => self.push(Event::HardBreak, &range),
            mdast::Node::ThematicBreak(_) => self.push(Event::Rule, &range),
            mdast::Node::Emphasis(value) => {
                self.container(Tag::Emphasis, &value.children, &range)?;
            }
            mdast::Node::Strong(value) => {
                self.container(Tag::Strong, &value.children, &range)?;
            }
            mdast::Node::Delete(value) => {
                self.container(Tag::Strikethrough, &value.children, &range)?;
            }
            mdast::Node::Link(link) => {
                self.container(
                    Tag::Link {
                        link_type: LinkType::Inline,
                        dest_url: link.url.clone().into(),
                        title: link.title.clone().unwrap_or_default().into(),
                        id: "".into(),
                    },
                    &link.children,
                    &range,
                )?;
            }
            mdast::Node::LinkReference(link) => {
                let definition = self.definitions.get(link.identifier.as_str()).ok_or(())?;
                self.container(
                    Tag::Link {
                        link_type: reference_kind(link.reference_kind),
                        dest_url: definition.url.clone().into(),
                        title: definition.title.clone().unwrap_or_default().into(),
                        id: link.identifier.clone().into(),
                    },
                    &link.children,
                    &range,
                )?;
            }
            mdast::Node::Image(image) => self.image(&image.alt, &image.url, &range),
            mdast::Node::ImageReference(image) => {
                let definition = self.definitions.get(image.identifier.as_str()).ok_or(())?;
                self.image(&image.alt, &definition.url.clone(), &range);
            }
            mdast::Node::FootnoteDefinition(note) => {
                self.container(
                    Tag::FootnoteDefinition(
                        note.label
                            .as_ref()
                            .unwrap_or(&note.identifier)
                            .clone()
                            .into(),
                    ),
                    &note.children,
                    &range,
                )?;
            }
            mdast::Node::FootnoteReference(note) => {
                let label = note.label.as_ref().unwrap_or(&note.identifier);
                if self.named_notes.contains(label) {
                    self.push(Event::FootnoteReference(label.clone().into()), &range);
                } else {
                    self.push(
                        Event::Text(self.source.get(range.clone()).ok_or(())?.to_string().into()),
                        &range,
                    );
                }
            }
            mdast::Node::Table(table) => {
                let align = table
                    .align
                    .iter()
                    .map(|align| match align {
                        mdast::AlignKind::Left => Alignment::Left,
                        mdast::AlignKind::Center => Alignment::Center,
                        mdast::AlignKind::Right => Alignment::Right,
                        mdast::AlignKind::None => Alignment::None,
                    })
                    .collect();
                self.push(Event::Start(Tag::Table(align)), &range);
                for (index, child) in table.children.iter().enumerate() {
                    let mdast::Node::TableRow(row) = child else {
                        return Err(());
                    };
                    self.container(
                        if index == 0 {
                            Tag::TableHead
                        } else {
                            Tag::TableRow
                        },
                        &row.children,
                        &position(row.position.as_ref())?,
                    )?;
                }
                self.push(Event::End(pulldown_cmark::TagEnd::Table), &range);
            }
            mdast::Node::TableCell(cell) => {
                self.container(Tag::TableCell, &cell.children, &range)?;
            }
            mdast::Node::Definition(_) => {}
            // Disabled constructs must never silently become another syntax.
            _ => return Err(()),
        }
        Ok(())
    }

    fn image(&mut self, alt: &str, url: &str, range: &Range<usize>) {
        let tag = Tag::Image {
            link_type: LinkType::Inline,
            dest_url: url.to_string().into(),
            title: "".into(),
            id: "".into(),
        };
        let end = tag.to_end();
        self.push(Event::Start(tag), range);
        self.push(Event::Text(alt.to_string().into()), range);
        self.push(Event::End(end), range);
    }
}

fn position(position: Option<&::markdown::unist::Position>) -> Result<Range<usize>, ()> {
    let position = position.ok_or(())?;
    Ok(position.start.offset..position.end.offset)
}

fn reference_kind(kind: mdast::ReferenceKind) -> LinkType {
    match kind {
        mdast::ReferenceKind::Shortcut => LinkType::Shortcut,
        mdast::ReferenceKind::Collapsed => LinkType::Collapsed,
        mdast::ReferenceKind::Full => LinkType::Reference,
    }
}

fn text_line_breaks(raw: &str, escaped_start: bool) -> Vec<bool> {
    let bytes = raw.as_bytes();
    let mut breaks = Vec::new();
    // A Text node beginning with an escape starts at the escaped character,
    // rather than its preceding backslash, in markdown-rs's source positions.
    let mut index =
        usize::from(escaped_start && bytes.first().is_some_and(u8::is_ascii_punctuation));
    while index < bytes.len() {
        if bytes[index] == b'\\' && bytes.get(index + 1).is_some_and(u8::is_ascii_punctuation) {
            index += 2;
            continue;
        }
        if bytes[index] == b'\n' {
            breaks.push(true);
        } else if bytes[index] == b'&' {
            let tail = &raw[index..];
            if tail.starts_with("&NewLine;") {
                breaks.push(false);
                index += "&NewLine;".len();
                continue;
            }
            if tail.starts_with("&#") {
                if let Some(end) = tail.bytes().take(10).position(|ch| ch == b';') {
                    let digits = &tail[2..end];
                    let (digits, radix, limit) = digits
                        .strip_prefix(['x', 'X'])
                        .map_or((digits, 10, 7), |digits| (digits, 16, 6));
                    if !digits.is_empty()
                        && digits.len() <= limit
                        && digits.bytes().all(|ch| {
                            if radix == 16 {
                                ch.is_ascii_hexdigit()
                            } else {
                                ch.is_ascii_digit()
                            }
                        })
                        && u32::from_str_radix(digits, radix) == Ok(10)
                    {
                        breaks.push(false);
                        index += end + 1;
                        continue;
                    }
                }
            }
        }
        index += 1;
    }
    breaks
}
