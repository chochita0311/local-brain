use super::{digest, failure, pattern, source::Source};
use crate::backend::Result;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{collections::BTreeMap, sync::LazyLock};
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
#[serde(default, deny_unknown_fields)]
pub struct Profile {
    pub target: usize,
    pub dimension: usize,
    pub overlap: usize,
    pub cutoff: f64,
}
impl Default for Profile {
    fn default() -> Self {
        Self {
            target: 512,
            dimension: 512,
            overlap: 0,
            cutoff: 0.45,
        }
    }
}
impl Profile {
    pub fn validate(&self) -> Result<()> {
        if ![256, 512, 768].contains(&self.target)
            || ![512, 1024].contains(&self.dimension)
            || ![0, 64].contains(&self.overlap)
            || !self.cutoff.is_finite()
            || !(0.0..=1.0).contains(&self.cutoff)
        {
            return Err(failure("INVALID_SEARCH_PROFILE"));
        }
        Ok(())
    }
    pub fn index_contract(&self) -> Value {
        json!({"splitter":"structural-spans-v1","target":self.target,"dimension":self.dimension,"overlap":self.overlap,"body_max":768,"context_max":128,"input_max":1024})
    }
}
pub trait SearchTokenizer: Send + Sync {
    fn count(&self, text: &str, special: bool) -> Result<usize>;
    fn spans(&self, text: &str) -> Result<Vec<(usize, usize)>>;
}
pub fn slice(value: &str, start: usize, end: usize) -> String {
    value
        .chars()
        .skip(start)
        .take(end.saturating_sub(start))
        .collect()
}
pub fn bounded_context(
    tokenizer: &dyn SearchTokenizer,
    text: &str,
    limit: usize,
) -> Result<(String, bool)> {
    if tokenizer.count(text, false)? <= limit {
        return Ok((text.into(), false));
    }
    let (mut low, mut high) = (0, text.chars().count());
    while low < high {
        let middle = (low + high).div_ceil(2);
        if tokenizer.count(&slice(text, 0, middle), false)? <= limit {
            low = middle
        } else {
            high = middle - 1
        }
    }
    Ok((slice(text, 0, low), true))
}
static BREAKS: LazyLock<fancy_regex::Regex> =
    LazyLock::new(|| pattern(r"\n\s*\n|\n(?=#{1,6} |[-*] |\d+[.)] )|(?<=[.!?。！？])\s+"));
pub fn split_spans(
    text: &str,
    tokenizer: &dyn SearchTokenizer,
    profile: Profile,
) -> Result<Vec<(usize, usize)>> {
    profile.validate()?;
    let offsets = tokenizer.spans(text)?;
    let length = text.chars().count();
    if offsets.is_empty() {
        return Ok(if length > 0 {
            vec![(0, length)]
        } else {
            vec![]
        });
    }
    let starts = offsets.iter().map(|pair| pair.0).collect::<Vec<_>>();
    let breaks = BREAKS
        .find_iter(text)
        .map(|result| {
            result
                .map(|found| text[..found.end()].chars().count())
                .map_err(|_| failure("SEARCH_SPLIT_FAILED"))
        })
        .collect::<Result<Vec<_>>>()?;
    let mut start = 0;
    let mut result = Vec::new();
    while start < length {
        let index = starts.partition_point(|value| *value < start);
        let mut end;
        if offsets.len().saturating_sub(index) <= profile.target {
            end = length;
        } else {
            let desired = offsets[(index + profile.target).min(offsets.len() - 1)].0;
            let ceiling = offsets[(index + 768).min(offsets.len() - 1)].0;
            let floor = offsets[(index + profile.target / 2).min(offsets.len() - 1)].0;
            end = breaks
                .iter()
                .copied()
                .filter(|value| *value > start && *value <= ceiling && *value >= floor)
                .min_by_key(|value| value.abs_diff(desired))
                .unwrap_or(desired)
                .max(start + 1);
        }
        while tokenizer.count(&slice(text, start, end), false)? > 768 {
            end = start + ((end - start) / 2).max(1);
        }
        result.push((start, end));
        if end == length {
            break;
        }
        if profile.overlap != 0 {
            let end_index = starts.partition_point(|value| *value < end);
            let overlap = offsets[(index + 1).max(end_index.saturating_sub(profile.overlap))].0;
            start = (start + 1).max(end.min(overlap));
        } else {
            start = end;
        }
    }
    Ok(result)
}
pub fn molecularize(
    source: &Source,
    tokenizer: &dyn SearchTokenizer,
    profile: Profile,
) -> Result<Vec<Value>> {
    let mut result = Vec::new();
    for_each_molecule(source, tokenizer, profile, |value| {
        result.push(value);
        Ok(())
    })?;
    Ok(result)
}
pub fn for_each_molecule(
    source: &Source,
    tokenizer: &dyn SearchTokenizer,
    profile: Profile,
    mut visit: impl FnMut(Value) -> Result<()>,
) -> Result<()> {
    let mut ordinal = 0;
    let mut previous: Option<&Value> = None;
    let mut contexts: BTreeMap<String, (String, bool)> = BTreeMap::new();
    for block in &source.blocks {
        let text = block["text"]
            .as_str()
            .ok_or_else(|| failure("INVALID_SEARCH_SOURCE"))?;
        let context_event = if block["role"] == "assistant" {
            previous
                .map(|value| value["id"].clone())
                .unwrap_or(Value::Null)
        } else {
            Value::Null
        };
        let key = serde_json::to_string(&context_event)?;
        if !contexts.contains_key(&key) {
            let mut prefix = format!("Title: {}", source.title);
            if !context_event.is_null() {
                prefix.push_str("\nPrevious request: ");
                prefix.push_str(previous.unwrap()["text"].as_str().unwrap());
            }
            contexts.insert(key.clone(), bounded_context(tokenizer, &prefix, 128)?);
        }
        let (prefix, limited) = &contexts[&key];
        for (start, end) in split_spans(text, tokenizer, profile)? {
            let body = slice(text, start, end);
            let input = format!("{prefix}\n\n{body}");
            if tokenizer.count(&input, true)? > 1024 {
                return Err(failure("MOLECULE_INPUT_TOO_LONG"));
            }
            let locator = json!({"block_id":block["id"],"role":block["role"],"start":start,"end":end,"line_start":slice(text,0,start).matches('\n').count()+1,"line_end":slice(text,0,end).matches('\n').count()+1,"context_event":context_event,"context_limited":limited});
            visit(
                json!({"ordinal":ordinal,"text":body,"context":prefix,"input":input,"input_hash":digest(&json!(input))?,"body_hash":digest(&json!(body))?,"locator":locator}),
            )?;
            ordinal += 1;
        }
        if block["role"] == "user" {
            previous = Some(block);
        }
    }
    Ok(())
}
