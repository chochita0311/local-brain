//! Shared, pure Markdown presentation. Original source is never changed or fetched.
mod highlight;
mod markdown;
pub mod references;
pub use highlight::highlight_code;
pub use markdown::render_markdown;
use references::MarkdownReferenceContext;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MarkdownProperty {
    pub name: String,
    pub value: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MarkdownRenderResult {
    pub html: String,
    pub state: String,
    pub properties: Vec<MarkdownProperty>,
}

#[derive(Default)]
pub struct MarkdownOptions<'a> {
    pub reference_context: Option<&'a MarkdownReferenceContext>,
    pub trusted_session_routes: BTreeSet<String>,
    pub app_doc_routes: BTreeSet<String>,
    pub app_doc_language: Option<&'a str>,
}
pub(crate) fn escape(value: &str) -> String {
    let mut result = String::with_capacity(value.len());
    for ch in value.chars() {
        match ch {
            '&' => result.push_str("&amp;"),
            '<' => result.push_str("&lt;"),
            '>' => result.push_str("&gt;"),
            '"' => result.push_str("&quot;"),
            '\'' => result.push_str("&#39;"),
            ch => result.push(ch),
        }
    }
    result
}
