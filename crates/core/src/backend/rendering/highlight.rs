use super::escape;
use crate::backend::unicode::{lowercase, python_space};
use std::sync::LazyLock;
use syntect::{
    parsing::{ParseState, ScopeStack, SyntaxSet},
    util::LinesWithEndings,
};

pub(super) fn language(value: &str) -> &str {
    value
        .split(python_space)
        .find(|value| !value.is_empty())
        .unwrap_or("")
}
pub(super) fn canonical(value: &str) -> Option<&'static str> {
    match value {
        "bash" | "sh" | "shell" | "zsh" => Some("bash"),
        "console" => Some("console"),
        "python" | "py" => Some("python"),
        "java" => Some("java"),
        "go" => Some("go"),
        "javascript" | "js" => Some("javascript"),
        "typescript" | "ts" => Some("typescript"),
        "json" => Some("json"),
        "yaml" | "yml" => Some("yaml"),
        "sql" => Some("sql"),
        "html" => Some("html"),
        "css" => Some("css"),
        "markdown" | "md" => Some("markdown"),
        "diff" => Some("diff"),
        "text" | "plaintext" => Some("text"),
        _ => None,
    }
}
pub(super) fn label(value: &str) -> &str {
    match value {
        "bash" => "Shell",
        "console" => "Console",
        "python" => "Python",
        "java" => "Java",
        "go" => "Go",
        "javascript" => "JavaScript",
        "typescript" => "TypeScript",
        "json" => "JSON",
        "yaml" => "YAML",
        "sql" => "SQL",
        "html" => "HTML",
        "css" => "CSS",
        "markdown" => "Markdown",
        "diff" => "Diff",
        "text" => "Text",
        value => value,
    }
}
static SYNTAX: LazyLock<SyntaxSet> = LazyLock::new(SyntaxSet::load_defaults_newlines);
fn class(stack: &ScopeStack) -> Option<&'static str> {
    for scope in stack.as_slice().iter().rev() {
        let scope = scope.to_string();
        if scope.starts_with("comment") {
            return Some("c");
        }
        if scope.starts_with("constant.character.escape") {
            return Some("se");
        }
        if scope.starts_with("string") {
            return Some("s");
        }
        if scope.starts_with("constant.numeric") {
            return Some("m");
        }
        if scope.starts_with("keyword.operator") {
            return Some("o");
        }
        if scope.starts_with("keyword") || scope.starts_with("storage") {
            return Some("k");
        }
        if scope.starts_with("support.function") {
            return Some("nb");
        }
        if scope.starts_with("entity.name.function") {
            return Some("nf");
        }
        if scope.starts_with("entity.name.type") || scope.starts_with("support.type") {
            return Some("nc");
        }
        if scope.starts_with("entity.other.attribute-name") {
            return Some("na");
        }
        if scope.starts_with("entity.name.tag") {
            return Some("nt");
        }
        if scope.starts_with("variable") {
            return Some("nv");
        }
        if scope.starts_with("constant.language") {
            return Some("k");
        }
        if scope.starts_with("markup.inserted") {
            return Some("gi");
        }
        if scope.starts_with("markup.deleted") {
            return Some("gd");
        }
    }
    None
}
/// Explicit lexer allowlist and complete escaped fallback. Syntect scopes map
/// to the existing Pygments CSS roles, without inline styles or lexer guessing.
pub fn highlight_code(code: &str, requested: &str) -> String {
    let requested = lowercase(language(requested));
    let Some(canonical) = canonical(&requested).filter(|language| *language != "text") else {
        return escape(code);
    };
    let token = match canonical {
        "bash" | "console" => "sh",
        "python" => "py",
        "javascript" => "js",
        "typescript" => "ts",
        "markdown" => "md",
        value => value,
    };
    // Bundled Syntect sets may omit TypeScript. Its explicitly related JS
    // grammar still preserves keyword/string/number roles without guessing.
    let Some(syntax) = SYNTAX.find_syntax_by_token(token).or_else(|| {
        (canonical == "typescript")
            .then(|| SYNTAX.find_syntax_by_token("js"))
            .flatten()
    }) else {
        return escape(code);
    };
    let mut parser = ParseState::new(syntax);
    let mut stack = ScopeStack::new();
    let mut parts: Vec<(Option<&str>, String)> = Vec::new();
    for line in LinesWithEndings::from(code) {
        let Ok(operations) = parser.parse_line(line, &SYNTAX) else {
            return escape(code);
        };
        let mut previous = 0;
        for (index, operation) in operations {
            if index > previous {
                append(&mut parts, class(&stack), &line[previous..index]);
            }
            if stack.apply(&operation).is_err() {
                return escape(code);
            }
            previous = index;
        }
        if previous < line.len() {
            append(&mut parts, class(&stack), &line[previous..]);
        }
    }
    parts
        .into_iter()
        .map(|(class, text)| {
            if let Some(class) = class {
                format!("<span class=\"{class}\">{}</span>", escape(&text))
            } else {
                escape(&text)
            }
        })
        .collect()
}
fn append<'a>(parts: &mut Vec<(Option<&'a str>, String)>, class: Option<&'a str>, text: &str) {
    if let Some((last, value)) = parts.last_mut() {
        if *last == class {
            value.push_str(text);
            return;
        }
    }
    parts.push((class, text.into()));
}
