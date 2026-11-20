use crate::assets::{value_digest, VerifiedModel};
use crate::{require, ModelError, Result};
use minijinja::{context, Environment};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;
use tokenizers::Tokenizer;

/// Each instance has padding/truncation disabled and never mutates tokenization state.
#[derive(Clone)]
pub struct OfflineTokenizer {
    pub(crate) inner: Tokenizer,
    chat_template: Option<String>,
    pad_token_id: Option<u32>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TokenSpan {
    pub id: u32,
    pub start: usize,
    pub end: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptDescription {
    pub prompt_sha256: String,
    pub template_sha256: String,
    pub input_tokens: usize,
    pub answer_token_ids: BTreeMap<String, Vec<u32>>,
}

impl OfflineTokenizer {
    #[cfg(test)]
    pub(crate) fn synthetic() -> Self {
        let inner = Tokenizer::from_bytes(br#"{"version":"1.0","truncation":null,"padding":null,"added_tokens":[],"normalizer":null,"pre_tokenizer":{"type":"Whitespace"},"post_processor":null,"decoder":null,"model":{"type":"WordLevel","vocab":{"[UNK]":0,"x":1,"tail":2},"unk_token":"[UNK]"}}"#).unwrap();
        Self {
            inner,
            chat_template: None,
            pad_token_id: None,
        }
    }
    pub fn from_verified(model: &VerifiedModel) -> Result<Self> {
        let mut inner = Tokenizer::from_file(model.snapshot().join("tokenizer.json"))
            .map_err(|e| ModelError::new("INVALID_MODEL", e.to_string()))?;
        inner
            .with_truncation(None)
            .map_err(|e| ModelError::new("INVALID_MODEL", e.to_string()))?;
        inner.with_padding(None);
        let config: Value = serde_json::from_slice(&std::fs::read(
            model.snapshot().join("tokenizer_config.json"),
        )?)?;
        let pad_token_id = config
            .get("pad_token")
            .and_then(|v| {
                v.as_str()
                    .or_else(|| v.get("content").and_then(Value::as_str))
            })
            .and_then(|token| inner.token_to_id(token));
        Ok(Self {
            inner,
            pad_token_id,
            chat_template: config
                .get("chat_template")
                .and_then(Value::as_str)
                .map(str::to_string),
        })
    }
    pub fn encode(&self, text: &str, special: bool) -> Result<Vec<u32>> {
        self.inner
            .encode(text, special)
            .map(|value| value.get_ids().to_vec())
            .map_err(|e| ModelError::new("MODEL_TOKENIZATION", e.to_string()))
    }
    /// Right-truncate content before special-token postprocessing, without
    /// changing this tokenizer's shared padding/truncation state.
    pub fn encode_right_truncated(
        &self,
        text: &str,
        special: bool,
        max_tokens: usize,
    ) -> Result<Vec<u32>> {
        let added = self
            .inner
            .get_post_processor()
            .map(|processor| tokenizers::PostProcessor::added_tokens(processor, false))
            .unwrap_or(0);
        require(
            max_tokens > 0 && max_tokens >= added,
            "INVALID_MODEL_CONFIG",
            "token budget cannot accommodate special-token postprocessing",
        )?;
        let mut tokenizer = self.inner.clone();
        tokenizer
            .with_truncation(Some(tokenizers::TruncationParams {
                max_length: max_tokens,
                direction: tokenizers::TruncationDirection::Right,
                strategy: tokenizers::TruncationStrategy::LongestFirst,
                ..Default::default()
            }))
            .map_err(|error| ModelError::new("MODEL_TOKENIZATION", error.to_string()))?;
        tokenizer
            .encode(text, special)
            .map(|encoding| encoding.get_ids().to_vec())
            .map_err(|error| ModelError::new("MODEL_TOKENIZATION", error.to_string()))
    }
    /// Offsets use Unicode character positions, matching the Python molecularizer.
    pub fn spans(&self, text: &str) -> Result<Vec<TokenSpan>> {
        let encoded = self
            .inner
            .encode_char_offsets(text, false)
            .map_err(|e| ModelError::new("MODEL_TOKENIZATION", e.to_string()))?;
        Ok(encoded
            .get_ids()
            .iter()
            .zip(encoded.get_offsets())
            .map(|(id, (start, end))| TokenSpan {
                id: *id,
                start: *start,
                end: *end,
            })
            .collect())
    }
    pub fn decode(&self, tokens: &[u32], skip_special: bool) -> Result<String> {
        self.inner
            .decode(tokens, skip_special)
            .map_err(|e| ModelError::new("MODEL_TOKENIZATION", e.to_string()))
    }
    pub fn token_id(&self, token: &str) -> Option<u32> {
        self.inner.token_to_id(token)
    }
    pub fn pad_token_id(&self) -> Option<u32> {
        self.pad_token_id
    }
    pub fn render(
        &self,
        messages: &[Value],
        tools: Option<&[Value]>,
        thinking: bool,
    ) -> Result<String> {
        let template = self
            .chat_template
            .as_deref()
            .ok_or_else(|| ModelError::new("INVALID_MODEL", "chat template missing"))?;
        render_chat_template(template, messages, tools, thinking)
    }
    pub fn describe(
        &self,
        messages: &[Value],
        tools: Option<&[Value]>,
        thinking: bool,
        codes: &[String],
    ) -> Result<PromptDescription> {
        let prompt = self.render(messages, tools, thinking)?;
        let answer_token_ids = codes
            .iter()
            .map(|code| Ok((code.clone(), self.encode(code, false)?)))
            .collect::<Result<_>>()?;
        Ok(PromptDescription {
            prompt_sha256: value_digest(&Value::String(prompt.clone()))?,
            template_sha256: value_digest(&Value::String(self.chat_template.clone().unwrap()))?,
            input_tokens: self.encode(&prompt, true)?.len(),
            answer_token_ids,
        })
    }
}

/// Runs the verified tokenizer's template in a pure Rust environment with no file loader.
pub fn render_chat_template(
    template: &str,
    messages: &[Value],
    tools: Option<&[Value]>,
    thinking: bool,
) -> Result<String> {
    require(
        !messages.is_empty()
            && messages.iter().all(|message| {
                matches!(
                    message.get("role").and_then(Value::as_str),
                    Some("system" | "user" | "assistant" | "tool")
                ) && (message
                    .get("content")
                    .is_some_and(|value| value.is_string() || value.is_null())
                    || message.get("tool_calls").is_some_and(Value::is_array))
            }),
        "INVALID_MESSAGES",
        "messages must contain known roles and text or structured tool calls",
    )?;
    let mut environment = Environment::new();
    environment.set_unknown_method_callback(minijinja_contrib::pycompat::unknown_method_callback);
    environment.add_function(
        "raise_exception",
        |message: String| -> std::result::Result<String, minijinja::Error> {
            Err(minijinja::Error::new(
                minijinja::ErrorKind::InvalidOperation,
                message,
            ))
        },
    );
    // Transformers 4.57 replaces Jinja's HTML-safe filter with json.dumps.
    // Preserve field order, Unicode and Python's default comma/colon spaces.
    environment.add_filter(
        "tojson",
        |value: minijinja::Value| -> std::result::Result<String, minijinja::Error> {
            let json = serde_json::to_value(value).map_err(|e| {
                minijinja::Error::new(minijinja::ErrorKind::InvalidOperation, e.to_string())
            })?;
            python_json(&json).map_err(|e| {
                minijinja::Error::new(minijinja::ErrorKind::InvalidOperation, e.to_string())
            })
        },
    );
    environment
        .add_template("chat", template)
        .map_err(|e| ModelError::new("INVALID_CHAT_TEMPLATE", e.to_string()))?;
    environment
        .get_template("chat")
        .unwrap()
        .render(context! {
            messages => minijinja::Value::from_iter(messages.iter().map(template_value).collect::<Result<Vec<_>>>()?),
            tools => minijinja::Value::from_iter(tools.unwrap_or_default().iter().map(template_value).collect::<Result<Vec<_>>>()?), add_generation_prompt => true,
            enable_thinking => thinking, bos_token => (), eos_token => "<|im_end|>",
        })
        .map_err(|e| ModelError::new("INVALID_CHAT_TEMPLATE", e.to_string()))
}

fn template_value(value: &Value) -> Result<minijinja::Value> {
    use minijinja::Value as Jinja;
    Ok(match value {
        Value::Null => Jinja::from(()),
        Value::Bool(v) => Jinja::from(*v),
        Value::String(v) => Jinja::from(v.clone()),
        Value::Array(values) => Jinja::from_iter(
            values
                .iter()
                .map(template_value)
                .collect::<Result<Vec<_>>>()?,
        ),
        Value::Object(values) => Jinja::from_pairs(
            values
                .iter()
                .map(|(key, value)| Ok((key.clone(), template_value(value)?)))
                .collect::<Result<Vec<_>>>()?,
        ),
        Value::Number(number) => {
            // serde_json arbitrary_precision exposes Number's private wrapper
            // through Serde. Construct real Jinja numeric primitives instead.
            if let Some(v) = number.as_i64() {
                Jinja::from(v)
            } else if let Some(v) = number.as_u64() {
                Jinja::from(v)
            } else if let Some(v) = number.as_i128() {
                Jinja::from(v)
            } else if let Some(v) = number.as_u128() {
                Jinja::from(v)
            } else if number.is_f64() {
                Jinja::from(number.as_f64().ok_or_else(|| {
                    ModelError::new("INVALID_MESSAGES", "chat template number must be finite")
                })?)
            } else {
                return Err(ModelError::new(
                    "INVALID_MESSAGES",
                    "chat template integer exceeds native 128-bit range",
                ));
            }
        }
    })
}

fn python_json(value: &Value) -> Result<String> {
    Ok(match value {
        Value::Null => "null".into(),
        Value::Bool(v) => v.to_string(),
        Value::String(v) => serde_json::to_string(v)?,
        Value::Number(n) => {
            if n.is_f64() {
                python_float_json(&n.to_string())
            } else {
                n.to_string()
            }
        }
        Value::Array(values) => format!(
            "[{}]",
            values
                .iter()
                .map(python_json)
                .collect::<Result<Vec<_>>>()?
                .join(", ")
        ),
        Value::Object(values) => format!(
            "{{{}}}",
            values
                .iter()
                .map(|(key, value)| Ok(format!(
                    "{}: {}",
                    serde_json::to_string(key)?,
                    python_json(value)?
                )))
                .collect::<Result<Vec<_>>>()?
                .join(", ")
        ),
    })
}

// Python repr/json use fixed notation for decimal exponents -4..15 and padded
// scientific exponents elsewhere. Keep the shortest round-trip digits emitted
// by serde_json, but preserve Python's notation and integral-float .0 suffix.
fn python_float_json(raw: &str) -> String {
    let (sign, unsigned) = raw.strip_prefix('-').map(|s| ("-", s)).unwrap_or(("", raw));
    let (mantissa, extra) = unsigned
        .split_once(['e', 'E'])
        .map(|(m, e)| (m, e.parse::<i32>().unwrap()))
        .unwrap_or((unsigned, 0));
    let point = mantissa.find('.').unwrap_or(mantissa.len()) as i32;
    let digits: String = mantissa.chars().filter(|c| *c != '.').collect();
    let leading = digits.bytes().take_while(|c| *c == b'0').count();
    if leading == digits.len() {
        return format!("{sign}0.0");
    }
    let exponent = point - leading as i32 - 1 + extra;
    let digits = digits[leading..].trim_end_matches('0');
    let number = if !(-4..16).contains(&exponent) {
        let mantissa = if digits.len() > 1 {
            format!("{}.{}", &digits[..1], &digits[1..])
        } else {
            digits.into()
        };
        format!(
            "{mantissa}e{}{:02}",
            if exponent >= 0 { "+" } else { "-" },
            exponent.abs()
        )
    } else if exponent < 0 {
        format!("0.{}{}", "0".repeat((-exponent - 1) as usize), digits)
    } else {
        let point = exponent as usize + 1;
        if point >= digits.len() {
            format!("{}{}.0", digits, "0".repeat(point - digits.len()))
        } else {
            format!("{}.{}", &digits[..point], &digits[point..])
        }
    };
    format!("{sign}{number}")
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    // Public metadata from the pinned 4B revision, never a cached user artifact.
    const CONFIG: &str = include_str!("../tests/fixtures/qwen3-4b-tokenizer-config.json");
    fn template() -> String {
        serde_json::from_str::<Value>(CONFIG).unwrap()["chat_template"]
            .as_str()
            .unwrap()
            .into()
    }
    #[test]
    fn pinned_template_non_thinking_and_thinking() {
        let messages = [
            json!({"role":"system","content":"Grounded"}),
            json!({"role":"user","content":"안녕 <&>"}),
        ];
        let head = "<|im_start|>system\nGrounded<|im_end|>\n<|im_start|>user\n안녕 <&><|im_end|>\n<|im_start|>assistant\n";
        assert_eq!(
            render_chat_template(&template(), &messages, None, true).unwrap(),
            head
        );
        assert_eq!(
            render_chat_template(&template(), &messages, None, false).unwrap(),
            format!("{head}<think>\n\n</think>\n\n")
        );
    }
    #[test]
    fn pinned_template_structured_tool_exchange() {
        let messages = [
            json!({"role":"user","content":"Find"}),
            json!({"role":"assistant","content":"","tool_calls":[{"function":{"name":"lookup","arguments":{"query":"한글 <&>"}}}]}),
            json!({"role":"tool","content":"one"}),
            json!({"role":"tool","content":"two"}),
        ];
        let rendered = render_chat_template(
            &template(),
            &messages,
            Some(&[json!({"type":"function","function":{"name":"lookup"}})]),
            false,
        )
        .unwrap();
        assert!(rendered.contains("{\"type\": \"function\", \"function\": {\"name\": \"lookup\"}}"));
        assert!(rendered.contains("<tool_call>\n{\"name\": \"lookup\", \"arguments\": {\"query\": \"한글 <&>\"}}\n</tool_call>"));
        assert!(rendered.contains("<|im_start|>user\n<tool_response>\none\n</tool_response>\n<tool_response>\ntwo\n</tool_response><|im_end|>"));
    }
    #[test]
    fn json_does_not_add_spaces_inside_strings() {
        assert_eq!(
            python_json(&json!({"x":"a,b:c\\\"","y":[1,2]})).unwrap(),
            "{\"x\": \"a,b:c\\\\\\\"\", \"y\": [1, 2]}"
        );
    }
    #[test]
    fn offsets_count_unicode_characters() {
        let spans = OfflineTokenizer::synthetic().spans("가 x 😀").unwrap();
        assert_eq!(
            spans.iter().map(|x| (x.start, x.end)).collect::<Vec<_>>(),
            vec![(0, 1), (2, 3), (4, 5)]
        );
    }
    #[test]
    fn pinned_tools_and_template_arithmetic_receive_real_json_numbers() {
        // Frozen with Transformers4.57.6/Jinja3.1.6/Python3.11.15 using the
        // pinned public template; no model inference or application data.
        let input: Value = serde_json::from_str(include_str!(
            "../tests/fixtures/qwen3-numeric-tools-input.json"
        ))
        .unwrap();
        let messages = input["messages"].as_array().unwrap();
        let tools = input["tools"].as_array().unwrap();
        let rendered = render_chat_template(&template(), messages, Some(tools), false).unwrap();
        assert_eq!(
            rendered,
            include_str!("../tests/fixtures/qwen3-numeric-tools-prompt.txt")
        );
        assert!(rendered.contains("\"minimum\": 2"));
        assert!(rendered.contains("\"minimum\": 0.25"));
        assert!(rendered.contains("\"const\": 18446744073709551616"));
        assert!(rendered.contains("\"arguments\": {\"count\": 3, \"ratio\": 0.5}"));
        assert!(!rendered.contains("$serde_json"));
        assert!(rendered.contains("\"float_controls\": [1e-06, 1e+16, 1000000000000000.0, -0.0]"));
        assert_eq!(render_chat_template("{{ tools[0].function.parameters.properties.count.minimum + 1 }}|{{ messages[0].count + 2 }}",messages,Some(tools),false).unwrap(),"3|9");
    }
    #[test]
    fn bounded_tokenization_keeps_postprocessor_eos_and_shared_state() {
        let mut tokenizer = OfflineTokenizer::synthetic();
        let post = tokenizers::processors::template::TemplateProcessing::builder()
            .try_single("$A tail")
            .unwrap()
            .special_tokens(vec![("tail", 2)])
            .build()
            .unwrap();
        tokenizer.inner.with_post_processor(Some(post));
        assert_eq!(
            tokenizer
                .encode_right_truncated("x", true, 0)
                .unwrap_err()
                .code,
            "INVALID_MODEL_CONFIG"
        );
        assert_eq!(tokenizer.encode("x x x", true).unwrap(), vec![1, 1, 1, 2]);
        assert_eq!(
            tokenizer.encode_right_truncated("x x x", true, 3).unwrap(),
            vec![1, 1, 2]
        );
        assert_eq!(tokenizer.encode("x x x", true).unwrap(), vec![1, 1, 1, 2]);
    }
}
