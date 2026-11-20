use super::super::common::*;
use crate::backend::{html, BackendError, Result};
use pulldown_cmark::{Event, Parser, Tag, TagEnd};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::sync::LazyLock;

pub const NORMALIZER_VERSION: &str = "localbrain.atlassian-normalizer.v1";
pub const NORMALIZED_DOCUMENT_SCHEMA: &str = "localbrain.atlassian-normalized.v1";
pub const SOURCE_FORMATS: &[&str] = &[
    "jira_adf",
    "confluence_adf",
    "confluence_html",
    "confluence_markdown",
    "plain_text",
];
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct NormalizedContent {
    pub source_format: String,
    pub source_body: String,
    pub source_hash: String,
    pub normalized_document_json: String,
    pub normalized_text: String,
    pub warning: Option<String>,
}
static INLINE_SPACES: LazyLock<regex::Regex> =
    LazyLock::new(|| regex::Regex::new(r"[ \t]+").unwrap());
fn append_block(blocks: &mut Vec<Value>, kind: &str, text: &str) {
    let text = INLINE_SPACES.replace_all(text, " ");
    let text = trim(&text);
    if !text.is_empty() {
        blocks.push(json!({"type":kind,"text":text}));
    }
}
fn inline_text(root: &Value, warnings: &mut Vec<String>) -> Result<String> {
    const KNOWN: &[&str] = &[
        "doc",
        "paragraph",
        "heading",
        "blockquote",
        "codeBlock",
        "bulletList",
        "orderedList",
        "listItem",
        "table",
        "tableRow",
        "tableCell",
        "tableHeader",
        "panel",
        "expand",
        "rule",
        "mediaSingle",
        "mediaGroup",
        "status",
    ];
    let mut output = String::new();
    let mut pending = vec![root];
    while let Some(node) = pending.pop() {
        if !node.is_object() {
            warnings.push("ignored non-object ADF node".into());
            continue;
        }
        let kind = &node["type"];
        if kind == "text" {
            if truth(&node["text"]) {
                output.push_str(&python_string(&node["text"]));
            }
            continue;
        }
        if kind == "hardBreak" {
            output.push('\n');
            continue;
        }
        if matches!(kind, Value::Array(_) | Value::Object(_)) {
            return Err(BackendError::invalid(
                "invalid-content",
                format!(
                    "unhashable type: '{}'",
                    if kind.is_array() { "list" } else { "dict" }
                ),
            ));
        }
        if kind
            .as_str()
            .is_some_and(|s| ["mention", "emoji", "inlineCard"].contains(&s))
            && node["attrs"].is_object()
        {
            if let Some(value) = ["text", "displayName", "shortName", "url"]
                .iter()
                .find_map(|key| node["attrs"][*key].as_str().filter(|s| !s.is_empty()))
            {
                output.push_str(value);
                continue;
            }
        }
        if let Some(children) = node["content"].as_array() {
            pending.extend(children.iter().rev());
            continue;
        }
        if !kind.as_str().is_some_and(|s| KNOWN.contains(&s)) {
            warnings.push(format!(
                "unsupported ADF node: {}",
                if truth(kind) {
                    python_string(kind)
                } else {
                    "unknown".into()
                }
            ));
        }
    }
    Ok(output)
}
fn adf(root: &Value, blocks: &mut Vec<Value>, warnings: &mut Vec<String>) -> Result<()> {
    const BLOCKS: &[&str] = &[
        "paragraph",
        "heading",
        "blockquote",
        "codeBlock",
        "listItem",
        "tableCell",
        "tableHeader",
        "panel",
        "expand",
    ];
    const NESTED: &[&str] = &[
        "bulletList",
        "orderedList",
        "table",
        "tableRow",
        "panel",
        "expand",
    ];
    const CONTAINERS: &[&str] = &[
        "doc",
        "bulletList",
        "orderedList",
        "table",
        "tableRow",
        "mediaSingle",
        "mediaGroup",
        "text",
        "hardBreak",
        "mention",
        "emoji",
        "inlineCard",
        "rule",
        "status",
    ];
    let mut pending = vec![root];
    while let Some(node) = pending.pop() {
        if !node.is_object() {
            warnings.push("ignored non-object ADF node".into());
            continue;
        }
        let kind = if truth(&node["type"]) {
            python_string(&node["type"])
        } else {
            "unknown".into()
        };
        let children = node["content"].as_array().map(Vec::as_slice).unwrap_or(&[]);
        if BLOCKS.contains(&kind.as_str()) {
            let mut text = String::new();
            for child in children {
                text.push_str(&inline_text(child, warnings)?);
            }
            append_block(blocks, &kind, &text);
            pending.extend(children.iter().rev().filter(|child| {
                child.is_object() && child["type"].as_str().is_some_and(|s| NESTED.contains(&s))
            }));
        } else {
            if !CONTAINERS.contains(&kind.as_str()) {
                warnings.push(format!("unsupported ADF node: {kind}"));
            }
            pending.extend(children.iter().rev());
        }
    }
    Ok(())
}
struct HtmlBlocks {
    blocks: Vec<Value>,
    parts: Vec<String>,
    ignored: usize,
    warnings: Vec<String>,
}
impl HtmlBlocks {
    fn flush(&mut self) {
        append_block(&mut self.blocks, "html", &self.parts.join(" "));
        self.parts.clear();
    }
}
const BLOCK_TAGS: &[&str] = &[
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "div",
    "dl",
    "dt",
    "dd",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
];
const IGNORED_TAGS: &[&str] = &[
    "script", "style", "form", "iframe", "object", "embed", "template",
];
impl html::Visitor for HtmlBlocks {
    fn start(&mut self, tag: &str, _: &[(String, Option<String>)]) -> Result<()> {
        if IGNORED_TAGS.contains(&tag) {
            self.ignored += 1;
            self.warnings
                .push(format!("ignored active HTML tag: {tag}"));
            return Ok(());
        }
        if self.ignored == 0 && BLOCK_TAGS.contains(&tag) {
            self.flush();
        }
        Ok(())
    }
    fn end(&mut self, tag: &str) -> Result<()> {
        if IGNORED_TAGS.contains(&tag) {
            self.ignored = self.ignored.saturating_sub(1);
            return Ok(());
        }
        if self.ignored == 0 && BLOCK_TAGS.contains(&tag) {
            self.flush();
        }
        Ok(())
    }
    fn data(&mut self, text: &str) -> Result<()> {
        if self.ignored == 0 && !text.is_empty() {
            self.parts.push(text.into());
        }
        Ok(())
    }
}
fn markdown(source: &str) -> (Vec<Value>, Vec<String>) {
    let mut blocks = vec![];
    let mut warnings = vec![];
    let mut inline = String::new();
    let mut code = None::<String>;
    let mut image_depth = 0;
    let mut html_depth = 0;
    for event in Parser::new(source) {
        match event {
            Event::Start(Tag::CodeBlock(_)) => {
                append_block(&mut blocks, "markdown", &inline);
                inline.clear();
                code = Some(String::new());
            }
            Event::End(TagEnd::CodeBlock) => {
                if let Some(text) = code.take() {
                    append_block(&mut blocks, "code", &text);
                }
            }
            Event::Start(Tag::HtmlBlock) => {
                append_block(&mut blocks, "markdown", &inline);
                inline.clear();
                html_depth += 1;
                warnings.push("ignored HTML block".into());
            }
            Event::End(TagEnd::HtmlBlock) => {
                html_depth -= 1;
            }
            Event::Start(Tag::Image { .. }) => {
                image_depth += 1;
            }
            Event::End(TagEnd::Image) => {
                image_depth -= 1;
            }
            Event::Text(value) => {
                if let Some(code) = code.as_mut() {
                    code.push_str(&value);
                } else if image_depth == 0 && html_depth == 0 {
                    inline.push_str(&value);
                }
            }
            Event::Code(value) => {
                if image_depth == 0 && html_depth == 0 {
                    inline.push_str(&value);
                }
            }
            Event::SoftBreak | Event::HardBreak => {
                if image_depth == 0 && html_depth == 0 {
                    inline.push('\n');
                }
            }
            Event::InlineHtml(_) => {
                warnings.push("ignored inline HTML".into());
            }
            Event::Html(_) => {
                if html_depth == 0 {
                    warnings.push("ignored HTML block".into());
                }
            }
            Event::Start(
                Tag::Paragraph
                | Tag::Heading { .. }
                | Tag::BlockQuote(_)
                | Tag::List(_)
                | Tag::Item,
            )
            | Event::End(
                TagEnd::Paragraph
                | TagEnd::Heading(_)
                | TagEnd::BlockQuote(_)
                | TagEnd::List(_)
                | TagEnd::Item,
            ) => {
                append_block(&mut blocks, "markdown", &inline);
                inline.clear();
            }
            _ => {}
        }
    }
    append_block(&mut blocks, "markdown", &inline);
    (blocks, warnings)
}
pub fn normalize_atlassian_content(format: &str, content: &Value) -> Result<NormalizedContent> {
    if !SOURCE_FORMATS.contains(&format) {
        return Err(fail(
            "unsupported-content-format",
            "Unsupported Atlassian content format",
        ));
    }
    let mut blocks = vec![];
    let mut warnings = vec![];
    let body = match format {
        "jira_adf" | "confluence_adf" => {
            if !content.is_object() {
                return Err(fail("invalid-content", "ADF content must be an object"));
            }
            let body = json_size(content, "ADF content", 2_000_000, "invalid-input")?;
            adf(content, &mut blocks, &mut warnings)?;
            body
        }
        "confluence_html" => {
            let body = content
                .as_str()
                .ok_or_else(|| fail("invalid-content", "Confluence HTML content must be text"))?;
            let mut parser = HtmlBlocks {
                blocks: vec![],
                parts: vec![],
                ignored: 0,
                warnings: vec![],
            };
            html::visit(body, html::Finish::Close, &mut parser)
                .map_err(|_| fail("invalid-content", "Confluence HTML could not be parsed"))?;
            parser.flush();
            blocks = parser.blocks;
            warnings = parser.warnings;
            body.into()
        }
        "confluence_markdown" => {
            let body = content.as_str().ok_or_else(|| {
                fail(
                    "invalid-content",
                    "Confluence Markdown content must be text",
                )
            })?;
            let normalized = markdown(body);
            blocks = normalized.0;
            warnings = normalized.1;
            body.into()
        }
        _ => {
            let body = content
                .as_str()
                .ok_or_else(|| fail("invalid-content", "Plain content must be text"))?;
            static PARAGRAPHS: LazyLock<regex::Regex> = LazyLock::new(|| {
                regex::Regex::new(r"\n[\t\n\x0b\x0c\r\x1c-\x1f \x{85}\x{a0}\x{1680}\x{2000}-\x{200a}\x{2028}\x{2029}\x{202f}\x{205f}\x{3000}]*\n").unwrap()
            });
            for paragraph in PARAGRAPHS.split(body) {
                append_block(&mut blocks, "plain", paragraph);
            }
            body.into()
        }
    };
    if body.len() > 2_000_000 {
        return Err(fail(
            "invalid-content",
            "Atlassian content exceeds 2000000 bytes",
        ));
    }
    let mut unique = vec![];
    for warning in warnings {
        if !unique.contains(&warning) {
            unique.push(warning.chars().take(200).collect::<String>());
        }
        if unique.len() >= 20 {
            break;
        }
    }
    let warning = (!unique.is_empty()).then(|| unique.join("; "));
    let normalized_text = blocks
        .iter()
        .map(|v| v["text"].as_str().unwrap())
        .collect::<Vec<_>>()
        .join("\n\n");
    let document = json!({"schema":NORMALIZED_DOCUMENT_SCHEMA,"blocks":blocks,"warnings":unique});
    Ok(NormalizedContent {
        source_format: format.into(),
        source_hash: format!("{:x}", Sha256::digest(body.as_bytes())),
        source_body: body,
        normalized_document_json: json_size(
            &document,
            "normalized document",
            2_000_000,
            "invalid-input",
        )?,
        normalized_text,
        warning,
    })
}
