//! Pure, source-local document references. No filesystem or network access.
use crate::backend::unicode::{casefold, lowercase, python_alnum, python_space, splitlines};
use crate::backend::{BackendError, Result};
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::sync::LazyLock;
use unicode_normalization::UnicodeNormalization;

static HEADING: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$").unwrap());
pub(super) static BLOCK_ID: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?:^|[ \t])\^([A-Za-z0-9][A-Za-z0-9_-]*)[ \t]*$").unwrap());

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarkdownDocumentReference {
    pub id: i64,
    pub context_root_id: i64,
    pub relative_path: String,
    pub title: String,
    pub body: String,
    pub content_type: String,
}
impl MarkdownDocumentReference {
    pub fn is_markdown(&self) -> bool {
        matches!(
            self.content_type.as_str(),
            "text/markdown" | "text/x-markdown"
        )
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarkdownReferenceResolution {
    pub state: String,
    pub label: String,
    pub document: Option<MarkdownDocumentReference>,
    pub fragment: Option<String>,
    pub href: Option<String>,
}
impl MarkdownReferenceResolution {
    fn state(state: &str, label: &str) -> Self {
        Self {
            state: state.into(),
            label: label.into(),
            document: None,
            fragment: None,
            href: None,
        }
    }
}

pub fn heading_slug(value: &str) -> String {
    let normalized = lowercase(value.nfkc().collect::<String>().trim_matches(python_space));
    let mut result = String::new();
    let mut separator = false;
    for ch in normalized
        .chars()
        .filter(|ch| python_alnum(*ch) || *ch == '_' || *ch == '-' || python_space(*ch))
    {
        if python_space(ch) || matches!(ch, '_' | '-') {
            separator = !result.is_empty();
        } else {
            if separator {
                result.push('-');
                separator = false;
            }
            result.push(ch);
        }
    }
    if result.is_empty() {
        "section".into()
    } else {
        result
    }
}
pub fn heading_anchor(value: &str, occurrence: usize) -> String {
    let base = format!("heading-{}", heading_slug(value));
    if occurrence <= 1 {
        base
    } else {
        format!("{base}-{occurrence}")
    }
}
pub fn block_anchor(value: &str) -> String {
    format!("block-{}", lowercase(value))
}

fn fence_character(line: &str) -> Option<char> {
    let line = line.trim_start_matches(python_space);
    let first = line.chars().next()?;
    if matches!(first, '`' | '~') && line.chars().take_while(|ch| *ch == first).count() >= 3 {
        Some(first)
    } else {
        None
    }
}
pub fn document_anchor_index(source: &str) -> (BTreeMap<String, String>, BTreeMap<String, String>) {
    let (mut headings, mut blocks, mut occurrences) = (
        BTreeMap::new(),
        BTreeMap::new(),
        BTreeMap::<String, usize>::new(),
    );
    let mut fence = None;
    for line in splitlines(source) {
        if let Some(marker) = fence_character(line) {
            if fence.is_none() {
                fence = Some(marker);
            } else if fence == Some(marker) {
                fence = None;
            }
            continue;
        }
        if fence.is_some() {
            continue;
        }
        if let Some(found) = HEADING.captures(line) {
            let title = found[2].trim_matches(python_space);
            let key = heading_slug(title);
            let count = occurrences.entry(key.clone()).or_default();
            *count += 1;
            headings
                .entry(key)
                .or_insert_with(|| heading_anchor(title, *count));
        }
        if let Some(found) = BLOCK_ID.captures(line) {
            let key = lowercase(&found[1]);
            blocks
                .entry(key.clone())
                .or_insert_with(|| block_anchor(&key));
        }
    }
    (headings, blocks)
}
pub fn resolve_document_fragment(source: &str, fragment: &str) -> Option<String> {
    let decoded = unquote(fragment);
    let decoded = decoded.trim_matches(python_space);
    if decoded.is_empty() {
        return None;
    }
    let (headings, blocks) = document_anchor_index(source);
    if let Some(block) = decoded.strip_prefix('^') {
        blocks.get(&lowercase(block)).cloned()
    } else {
        headings.get(&heading_slug(decoded)).cloned()
    }
}
pub fn extract_document_fragment(source: &str, fragment: Option<&str>) -> Option<String> {
    let Some(fragment) = fragment.filter(|x| !x.is_empty()) else {
        return Some(source.into());
    };
    let decoded = unquote(fragment);
    let decoded = decoded.trim_matches(python_space);
    let lines = splitlines(source);
    if let Some(identifier) = decoded.strip_prefix('^') {
        return lines.iter().find_map(|line| {
            let found = BLOCK_ID.captures(line)?;
            (lowercase(&found[1]) == lowercase(identifier)).then(|| {
                BLOCK_ID
                    .replace(line, "")
                    .trim_end_matches(python_space)
                    .to_string()
            })
        });
    }
    let slug = heading_slug(decoded);
    let mut start = None;
    let mut level = 0;
    for (index, line) in lines.iter().enumerate() {
        if let Some(found) = HEADING.captures(line) {
            let current = found[1].len();
            if start.is_none() && heading_slug(found[2].trim_matches(python_space)) == slug {
                start = Some(index);
                level = current;
                continue;
            }
            if let Some(start) = start {
                if current <= level {
                    return Some(
                        lines[start..index]
                            .join("\n")
                            .trim_matches(python_space)
                            .to_string(),
                    );
                }
            }
        }
    }
    start.map(|start| {
        lines[start..]
            .join("\n")
            .trim_matches(python_space)
            .to_string()
    })
}

/// urllib.parse.unquote-compatible percent decoding with UTF-8 replacement.
pub(super) fn unquote(value: &str) -> String {
    let mut result = Vec::with_capacity(value.len());
    let bytes = value.as_bytes();
    let mut index = 0;
    while index < bytes.len() {
        if bytes[index] == b'%' && index + 2 < bytes.len() {
            if let (Ok(a), Ok(b)) = (hex(bytes[index + 1]), hex(bytes[index + 2])) {
                result.push(a * 16 + b);
                index += 3;
                continue;
            }
        }
        result.push(bytes[index]);
        index += 1;
    }
    String::from_utf8_lossy(&result).into_owned()
}
fn hex(value: u8) -> std::result::Result<u8, ()> {
    match value {
        b'0'..=b'9' => Ok(value - b'0'),
        b'a'..=b'f' => Ok(value - b'a' + 10),
        b'A'..=b'F' => Ok(value - b'A' + 10),
        _ => Err(()),
    }
}
pub(super) fn scheme(value: &str) -> Option<String> {
    let (scheme, _) = value.split_once(':')?;
    (scheme
        .as_bytes()
        .first()
        .is_some_and(u8::is_ascii_alphabetic)
        && scheme
            .bytes()
            .all(|ch| ch.is_ascii_alphanumeric() || b"+.-".contains(&ch)))
    .then(|| scheme.to_ascii_lowercase())
}
pub(super) fn external_url(value: &str) -> bool {
    matches!(scheme(value).as_deref(), Some("http" | "https"))
        && value
            .split_once("://")
            .is_some_and(|(_, tail)| !tail.split(['/', '?', '#']).next().unwrap_or("").is_empty())
}
pub(super) fn suffix(path: &str) -> &str {
    let name = path.rsplit('/').next().unwrap_or(path);
    name.rfind('.')
        .filter(|index| *index > 0 && *index + 1 < name.len())
        .map_or("", |index| &name[index..])
}
pub(super) fn stem(path: &str) -> &str {
    let name = path.rsplit('/').next().unwrap_or(path);
    let ext = suffix(name);
    if ext.is_empty() {
        name
    } else {
        &name[..name.len() - ext.len()]
    }
}
fn normalized_path(path: &str, base: &str) -> Option<String> {
    if path.is_empty() || path.starts_with(['/', '\\']) || path.contains(['\\', '\0']) {
        return None;
    }
    let mut parts: Vec<&str> = base
        .split('/')
        .filter(|x| !matches!(*x, "" | "."))
        .collect();
    for part in path.split('/') {
        match part {
            "" | "." => {}
            ".." => {
                parts.pop()?;
            }
            part => parts.push(part),
        }
    }
    (!parts.is_empty()).then(|| parts.join("/"))
}
fn path_candidates(path: &str) -> Vec<String> {
    if matches!(
        suffix(path).to_ascii_lowercase().as_str(),
        ".md" | ".markdown" | ".mdown" | ".mkd"
    ) {
        vec![casefold(path)]
    } else {
        vec![casefold(path), casefold(&format!("{path}.md"))]
    }
}

#[derive(Debug, Clone)]
pub struct MarkdownReferenceContext {
    documents: Vec<MarkdownDocumentReference>,
    current_document_id: i64,
}
impl MarkdownReferenceContext {
    pub fn documents(&self) -> &[MarkdownDocumentReference] {
        &self.documents
    }
    pub fn current_document_id(&self) -> i64 {
        self.current_document_id
    }
    pub fn from_documents(
        documents: impl IntoIterator<Item = MarkdownDocumentReference>,
        current_document_id: i64,
    ) -> Result<Self> {
        let documents: Vec<_> = documents.into_iter().collect();
        if documents.is_empty()
            || documents
                .iter()
                .any(|document| document.context_root_id != documents[0].context_root_id)
            || !documents
                .iter()
                .any(|document| document.id == current_document_id)
        {
            return Err(BackendError::invalid("markdown_context","Markdown reference context must contain the current document in exactly one Local Context root"));
        }
        Ok(Self {
            documents,
            current_document_id,
        })
    }
    pub fn current_document(&self) -> &MarkdownDocumentReference {
        self.documents
            .iter()
            .find(|document| document.id == self.current_document_id)
            .expect("validated reference context")
    }
    pub fn for_document(&self, document_id: i64) -> Result<Self> {
        Self::from_documents(self.documents.clone(), document_id)
    }
    pub fn resolve(&self, target: &str, kind: &str) -> MarkdownReferenceResolution {
        let decoded = unquote(target);
        let decoded = decoded.trim_matches(python_space);
        let readable = if decoded.is_empty() { target } else { decoded };
        if scheme(decoded).is_some() {
            let mut resolution = MarkdownReferenceResolution::state(
                if external_url(decoded) {
                    "external"
                } else {
                    "unsafe"
                },
                readable,
            );
            if resolution.state == "external" {
                resolution.href = Some(decoded.into());
            }
            return resolution;
        }
        // Python's original resolver decodes once here and once when splitting.
        let split = unquote(decoded);
        let split = split.trim_matches(python_space);
        let (path, fragment) = split
            .split_once('#')
            .map_or((split, None), |(path, fragment)| {
                (path, (!fragment.is_empty()).then_some(fragment))
            });
        if path.starts_with(['/', '\\']) || path.contains('\0') {
            return MarkdownReferenceResolution::state("unsafe", readable);
        }
        let candidates: Vec<&MarkdownDocumentReference>;
        if path.is_empty() {
            candidates = vec![self.current_document()];
            if resolve_document_fragment(&candidates[0].body, fragment.unwrap_or("")).is_none() {
                return MarkdownReferenceResolution::state("missing", readable);
            }
        } else if kind == "markdown" || path.contains('/') || !suffix(path).is_empty() {
            let base = if kind == "markdown" {
                self.current_document()
                    .relative_path
                    .rsplit_once('/')
                    .map_or("", |(parent, _)| parent)
            } else {
                ""
            };
            let Some(path) = normalized_path(path, base) else {
                return MarkdownReferenceResolution::state("unsafe", readable);
            };
            let paths = path_candidates(&path);
            candidates = self
                .documents
                .iter()
                .filter(|document| paths.contains(&casefold(&document.relative_path)))
                .collect();
        } else {
            let lookup = casefold(path);
            candidates = self
                .documents
                .iter()
                .filter(|document| {
                    casefold(&document.title) == lookup
                        || casefold(stem(&document.relative_path)) == lookup
                })
                .collect();
        }
        if candidates.is_empty() {
            return MarkdownReferenceResolution::state("missing", readable);
        }
        if candidates.len() > 1 {
            return MarkdownReferenceResolution::state("ambiguous", readable);
        }
        let document = candidates[0];
        let mut href = format!("/documents/{}", document.id);
        if let Some(fragment) = fragment {
            let Some(anchor) = resolve_document_fragment(&document.body, fragment) else {
                return MarkdownReferenceResolution::state("missing", readable);
            };
            href.push('#');
            href.push_str(&anchor);
        }
        MarkdownReferenceResolution {
            state: "resolved".into(),
            label: readable.into(),
            document: Some(document.clone()),
            fragment: fragment.map(str::to_string),
            href: Some(href),
        }
    }
}
