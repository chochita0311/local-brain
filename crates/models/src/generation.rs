//! Offline generation primitives for the suspended 4B/8B experiments.
//! Exposing this engine does not admit or activate either experimental producer.
use crate::assets::{value_digest, VerifiedModel};
use crate::catalog::ModelKey;
use crate::embedding::{
    device_name, read_qwen_config, resolve_device, runtime_identity, DevicePreference,
};
use crate::tokenizer::{OfflineTokenizer, PromptDescription};
use crate::{check_cancel, require, Cancellation, ModelError, Result};
use candle_core::{DType, Device, Tensor};
use candle_nn::VarBuilder;
use candle_transformers::{
    generation::{LogitsProcessor, Sampling},
    models::qwen3,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::time::{Duration, Instant};

pub const OUTPUT_PROTOCOL: &str = "qwen-final-only.v1";
pub const CHOICE_PROTOCOL: &str = "work-context-choice-trie.v1";

#[derive(Debug, Copy, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Decoding {
    Greedy,
    Sampled,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SamplingSettings {
    pub temperature: f64,
    pub top_p: f64,
    pub top_k: usize,
    pub seed: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GenerationSettings {
    pub thinking: bool,
    pub decoding: Decoding,
    pub sampling: Option<SamplingSettings>,
    pub max_tokens: usize,
    pub max_output: usize,
    pub max_seconds: u64,
    pub output_protocol: String,
}

impl Default for GenerationSettings {
    fn default() -> Self {
        Self::new(false, Decoding::Greedy, None, None, 180).unwrap()
    }
}
impl GenerationSettings {
    pub fn new(
        thinking: bool,
        decoding: Decoding,
        max_tokens: Option<usize>,
        max_output: Option<usize>,
        max_seconds: u64,
    ) -> Result<Self> {
        let (combined, output) = if thinking {
            (16384, 8192)
        } else {
            (8192, 2048)
        };
        let settings = Self {
            thinking,
            decoding,
            sampling: if decoding == Decoding::Sampled {
                Some(SamplingSettings {
                    temperature: if thinking { 0.6 } else { 0.7 },
                    top_p: if thinking { 0.95 } else { 0.8 },
                    top_k: 20,
                    seed: "sha256-system-and-content-prefix32".into(),
                })
            } else {
                None
            },
            max_tokens: max_tokens.unwrap_or(combined),
            max_output: max_output.unwrap_or(output),
            max_seconds,
            output_protocol: OUTPUT_PROTOCOL.into(),
        };
        settings.validate()?;
        Ok(settings)
    }
    pub fn validate(&self) -> Result<()> {
        let (combined, output) = if self.thinking {
            (16384, 8192)
        } else {
            (8192, 2048)
        };
        let expected_sampling = if self.decoding == Decoding::Sampled {
            Some(SamplingSettings {
                temperature: if self.thinking { 0.6 } else { 0.7 },
                top_p: if self.thinking { 0.95 } else { 0.8 },
                top_k: 20,
                seed: "sha256-system-and-content-prefix32".into(),
            })
        } else {
            None
        };
        require(
            (!self.thinking || self.decoding == Decoding::Sampled)
                && (1024..=combined).contains(&self.max_tokens)
                && (128..=output).contains(&self.max_output)
                && self.max_output < self.max_tokens
                && (1..=180).contains(&self.max_seconds)
                && self.sampling == expected_sampling
                && self.output_protocol == OUTPUT_PROTOCOL,
            "INVALID_MODEL_CONFIG",
            "generation settings must match accepted budgets and decoding policy",
        )
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerationMetrics {
    pub seconds: f64,
    pub input_tokens: usize,
    pub output_tokens: usize,
    pub reasoning_tokens: usize,
    pub final_tokens: usize,
    pub max_rss_native: i64,
    pub rss_unit: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerationResult {
    pub text: String,
    pub metrics: GenerationMetrics,
    pub contract: Value,
}

pub struct LocalGenerator {
    verified: VerifiedModel,
    device: Device,
    dtype: DType,
    settings: GenerationSettings,
    tokenizer: Option<OfflineTokenizer>,
    eos: BTreeSet<u32>,
    model: Option<qwen3::ModelForCausalLM>,
}

impl LocalGenerator {
    pub fn new(
        verified: VerifiedModel,
        device: DevicePreference,
        settings: GenerationSettings,
    ) -> Result<Self> {
        require(
            verified.key() != ModelKey::Embedding,
            "MODEL_MISMATCH",
            "generation requires the pinned 4B or 8B assets",
        )?;
        settings.validate()?;
        let device = resolve_device(device)?;
        let dtype = if device.is_cpu() {
            DType::F32
        } else {
            DType::BF16
        };
        Ok(Self {
            verified,
            device,
            dtype,
            settings,
            tokenizer: None,
            eos: BTreeSet::new(),
            model: None,
        })
    }
    pub fn is_loaded(&self) -> bool {
        self.model.is_some()
    }
    pub fn contract(&self) -> Value {
        let mut value = serde_json::to_value(&self.settings).expect("finite fixed settings");
        let object = value.as_object_mut().unwrap();
        let identity = self.verified.identity();
        object.insert("model".into(), json!(identity.model_id));
        object.insert("revision".into(), json!(identity.resolved_revision));
        object.insert("fingerprint".into(), json!(identity.fingerprint));
        object.insert("device".into(), json!(device_name(&self.device)));
        object.insert(
            "dtype".into(),
            json!(if self.device.is_cpu() {
                "float32"
            } else {
                "bfloat16"
            }),
        );
        object.insert(
            "native_runtime".into(),
            json!("localbrain.generation.candle-qwen3.v1"),
        );
        object.insert(
            "runtime".into(),
            runtime_identity(
                &self.device,
                if self.device.is_cpu() {
                    "float32"
                } else {
                    "bfloat16"
                },
            ),
        );
        object.insert(
            "sampling_rng".into(),
            json!("candle-0.10.0-rand-0.9.5-StdRng-ChaCha12"),
        );
        object.insert("experiment_suspended".into(), json!(true));
        value
    }
    fn load_tokenizer(&mut self, cancel: &Cancellation) -> Result<()> {
        check_cancel(cancel)?;
        if self.tokenizer.is_some() {
            return Ok(());
        }
        self.verified.reverify(cancel)?;
        let tokenizer = OfflineTokenizer::from_verified(&self.verified)?;
        require(
            tokenizer.token_id("</think>") == Some(151668)
                && tokenizer.token_id("<think>") == Some(151667),
            "INVALID_MODEL",
            "pinned Qwen thinking token IDs differ",
        )?;
        let value: Value = serde_json::from_slice(&std::fs::read(
            self.verified.snapshot().join("generation_config.json"),
        )?)?;
        let eos = value
            .get("eos_token_id")
            .ok_or_else(|| ModelError::new("INVALID_MODEL", "EOS token IDs missing"))?;
        let ids = if let Some(id) = eos.as_u64() {
            vec![id]
        } else {
            eos.as_array()
                .ok_or_else(|| ModelError::new("INVALID_MODEL", "invalid EOS token IDs"))?
                .iter()
                .map(|id| {
                    id.as_u64()
                        .ok_or_else(|| ModelError::new("INVALID_MODEL", "invalid EOS token ID"))
                })
                .collect::<Result<Vec<_>>>()?
        };
        self.eos = ids
            .into_iter()
            .map(|id| {
                u32::try_from(id)
                    .map_err(|_| ModelError::new("INVALID_MODEL", "invalid EOS token ID"))
            })
            .collect::<Result<_>>()?;
        require(!self.eos.is_empty(), "INVALID_MODEL", "EOS tokens missing")?;
        self.tokenizer = Some(tokenizer);
        Ok(())
    }
    fn load(&mut self, cancel: &Cancellation) -> Result<()> {
        check_cancel(cancel)?;
        if self.model.is_some() {
            return Ok(());
        }
        self.load_tokenizer(cancel)?;
        self.verified.reverify(cancel)?;
        let config = read_qwen_config(self.verified.snapshot())?;
        require(
            config.max_position_embeddings >= self.settings.max_tokens,
            "INVALID_MODEL_CONFIG",
            "model position budget is too small",
        )?;
        let builder = unsafe {
            VarBuilder::from_mmaped_safetensors(
                &self.verified.weight_files(),
                self.dtype,
                &self.device,
            )?
        };
        let model = qwen3::ModelForCausalLM::new(&config, builder)?;
        check_cancel(cancel)?;
        self.model = Some(model);
        Ok(())
    }
    pub fn describe_prompt(
        &mut self,
        system: &str,
        content: &str,
        codes: &[String],
        cancel: &Cancellation,
    ) -> Result<PromptDescription> {
        self.load_tokenizer(cancel)?;
        self.tokenizer.as_ref().unwrap().describe(
            &[
                json!({"role":"system","content":system}),
                json!({"role":"user","content":content}),
            ],
            None,
            self.settings.thinking,
            codes,
        )
    }
    pub fn generate(
        &mut self,
        system: &str,
        content: &str,
        cancel: &Cancellation,
    ) -> Result<GenerationResult> {
        self.generate_messages(
            &[
                json!({"role":"system","content":system}),
                json!({"role":"user","content":content}),
            ],
            None,
            cancel,
        )
    }
    pub fn generate_messages(
        &mut self,
        messages: &[Value],
        tools: Option<&[Value]>,
        cancel: &Cancellation,
    ) -> Result<GenerationResult> {
        let started = Instant::now();
        self.load_tokenizer(cancel)?;
        let tokenizer = self.tokenizer.as_ref().unwrap();
        let prompt = tokenizer.render(messages, tools, self.settings.thinking)?;
        let input = tokenizer.encode(&prompt, true)?;
        require(
            input
                .len()
                .checked_add(self.settings.max_output)
                .is_some_and(|x| x <= self.settings.max_tokens),
            "CONTEXT_TOO_LARGE",
            "rendered prompt plus reserved output exceeds the context budget",
        )?;
        let seed = stable_seed(messages, tools)?;
        self.load(cancel)?;
        let tokens = self.decode_tokens(&input, self.settings.max_output, seed, None, cancel)?;
        let (answer, reasoning) = final_token_ids(&tokens, self.settings.thinking, &self.eos)?;
        let text = self
            .tokenizer
            .as_ref()
            .unwrap()
            .decode(answer, true)?
            .trim()
            .to_string();
        let metrics = metrics(started, input.len(), tokens.len(), reasoning, answer.len());
        Ok(GenerationResult {
            text,
            metrics,
            contract: self.contract(),
        })
    }
    pub fn choose(
        &mut self,
        system: &str,
        content: &str,
        codes: &[String],
        max_code_chars: usize,
        cancel: &Cancellation,
    ) -> Result<GenerationResult> {
        require(
            !self.settings.thinking && self.settings.decoding == Decoding::Greedy,
            "INVALID_MODEL_CONFIG",
            "constrained choices require greedy non-thinking mode",
        )?;
        validate_codes(codes, max_code_chars)?;
        let started = Instant::now();
        self.load_tokenizer(cancel)?;
        let tokenizer = self.tokenizer.as_ref().unwrap();
        let mut encoded = BTreeMap::new();
        for code in codes {
            let tokens = tokenizer.encode(code, false)?;
            require(
                tokenizer.decode(&tokens, false)? == *code,
                "INVALID_CHOICES",
                "code does not round trip through the pinned tokenizer",
            )?;
            encoded.insert(code.clone(), tokens);
        }
        let trie = ChoiceTrie::new(encoded, self.eos.clone(), max_code_chars)?;
        let prompt = tokenizer.render(
            &[
                json!({"role":"system","content":system}),
                json!({"role":"user","content":content}),
            ],
            None,
            false,
        )?;
        let input = tokenizer.encode(&prompt, true)?;
        require(
            input
                .len()
                .checked_add(trie.max_output())
                .is_some_and(|x| x <= self.settings.max_tokens),
            "CONTEXT_TOO_LARGE",
            "rendered prompt plus finite choice grammar exceeds context budget",
        )?;
        self.load(cancel)?;
        let tokens = self.decode_tokens(&input, trie.max_output(), 0, Some(&trie), cancel)?;
        let text = trie.answer(&tokens)?.to_string();
        let metrics = metrics(started, input.len(), tokens.len(), 0, tokens.len());
        Ok(GenerationResult {
            text,
            metrics,
            contract: self.contract(),
        })
    }
    fn decode_tokens(
        &mut self,
        input: &[u32],
        limit: usize,
        seed: u64,
        trie: Option<&ChoiceTrie>,
        cancel: &Cancellation,
    ) -> Result<Vec<u32>> {
        require(
            !input.is_empty(),
            "INVALID_MESSAGES",
            "rendered prompt is empty",
        )?;
        let model = self.model.as_mut().unwrap();
        model.clear_kv_cache();
        let deadline = Instant::now() + Duration::from_secs(self.settings.max_seconds);
        let mut tokens = Vec::with_capacity(limit);
        let mut rng = LogitsProcessor::from_sampling(seed, Sampling::All { temperature: 1.0 });
        let result = (|| -> Result<()> {
            for index in 0..limit {
                check_cancel(cancel)?;
                if Instant::now() >= deadline {
                    break;
                }
                let (current, offset) = if index == 0 {
                    (input, 0)
                } else {
                    (&tokens[tokens.len() - 1..], input.len() + tokens.len() - 1)
                };
                let current = Tensor::from_slice(current, (1, current.len()), &self.device)?;
                let logits = model
                    .forward(&current, offset)?
                    .squeeze(0)?
                    .squeeze(0)?
                    .to_dtype(DType::F32)?;
                let next = if let Some(trie) = trie {
                    greedy_allowed(&logits, &trie.allowed(&tokens)?)?
                } else if let Some(sampling) = &self.settings.sampling {
                    rng.sample(&filtered_sampling_logits(&logits, sampling)?)?
                } else {
                    greedy_allowed(&logits, &[])?
                };
                tokens.push(next);
                if self.eos.contains(&next) {
                    break;
                }
            }
            self.device.synchronize()?;
            check_cancel(cancel)
        })();
        // No partial output or reasoning remains attached to the generator on refusal.
        model.clear_kv_cache();
        result?;
        Ok(tokens)
    }
}

pub fn stable_seed(messages: &[Value], tools: Option<&[Value]>) -> Result<u64> {
    let value = if messages.len() == 2 && tools.is_none_or(|x| x.is_empty()) {
        Value::Array(
            messages
                .iter()
                .map(|x| x.get("content").cloned().unwrap_or(Value::Null))
                .collect(),
        )
    } else {
        Value::Array(messages.to_vec())
    };
    let hash = value_digest(&value)?;
    u64::from_str_radix(&hash[..8], 16)
        .map_err(|e| ModelError::new("INVALID_MESSAGES", e.to_string()))
}

pub fn final_token_ids<'a>(
    tokens: &'a [u32],
    thinking: bool,
    eos: &BTreeSet<u32>,
) -> Result<(&'a [u32], usize)> {
    require(
        tokens.last().is_some_and(|id| eos.contains(id)),
        "OUTPUT_TRUNCATED",
        "response did not finish with EOS",
    )?;
    if thinking {
        require(
            tokens.iter().filter(|id| **id == 151668).count() == 1,
            "INVALID_THINKING_PROTOCOL",
            "thinking response requires one closing delimiter",
        )?;
        let boundary = tokens.iter().position(|id| *id == 151668).unwrap() + 1;
        require(
            boundary < tokens.len() - 1,
            "INVALID_THINKING_PROTOCOL",
            "final answer is empty",
        )?;
        Ok((&tokens[boundary..], boundary))
    } else {
        require(
            !tokens.contains(&151668) && !tokens.contains(&151667),
            "INVALID_THINKING_PROTOCOL",
            "non-thinking response contains a thinking delimiter",
        )?;
        Ok((tokens, 0))
    }
}

pub fn validate_codes(codes: &[String], max_code_chars: usize) -> Result<()> {
    let unique: BTreeSet<_> = codes.iter().collect();
    require(
        matches!(max_code_chars, 8 | 32)
            && (1..=128).contains(&codes.len())
            && unique.len() == codes.len()
            && codes.iter().all(|code| {
                (1..=max_code_chars).contains(&code.len())
                    && code
                        .bytes()
                        .all(|c| c.is_ascii_alphanumeric() || matches!(c, b'_' | b'-'))
            }),
        "INVALID_CHOICES",
        "choices require unique finite ASCII answer codes",
    )
}

#[derive(Debug, Default)]
struct ChoiceNode {
    children: BTreeMap<u32, ChoiceNode>,
    answer: Option<String>,
}
#[derive(Debug)]
pub struct ChoiceTrie {
    root: ChoiceNode,
    eos: BTreeSet<u32>,
    max_output: usize,
}
impl ChoiceTrie {
    pub fn new(
        encoded: BTreeMap<String, Vec<u32>>,
        eos: BTreeSet<u32>,
        max_code_chars: usize,
    ) -> Result<Self> {
        validate_codes(&encoded.keys().cloned().collect::<Vec<_>>(), max_code_chars)?;
        require(!eos.is_empty(), "INVALID_CHOICES", "EOS tokens missing")?;
        let mut trie = Self {
            root: ChoiceNode::default(),
            eos,
            max_output: 1,
        };
        for (code, tokens) in encoded {
            require(
                (1..=8).contains(&tokens.len()) && !tokens.iter().any(|id| trie.eos.contains(id)),
                "INVALID_CHOICES",
                "code tokenization is empty, too long or contains EOS",
            )?;
            trie.max_output = trie.max_output.max(tokens.len() + 1);
            let mut node = &mut trie.root;
            for token in tokens {
                node = node.children.entry(token).or_default();
            }
            require(
                node.answer.is_none(),
                "INVALID_CHOICES",
                "different codes have identical tokenization",
            )?;
            node.answer = Some(code);
        }
        Ok(trie)
    }
    pub fn max_output(&self) -> usize {
        self.max_output
    }
    fn node(&self, prefix: &[u32]) -> Result<&ChoiceNode> {
        let mut node = &self.root;
        for token in prefix {
            node = node.children.get(token).ok_or_else(|| {
                ModelError::new(
                    "INVALID_CHOICE_OUTPUT",
                    "token is outside the choice grammar",
                )
            })?;
        }
        Ok(node)
    }
    pub fn allowed(&self, prefix: &[u32]) -> Result<Vec<u32>> {
        let node = self.node(prefix)?;
        let mut tokens: BTreeSet<_> = node.children.keys().copied().collect();
        if node.answer.is_some() {
            tokens.extend(&self.eos);
        }
        Ok(tokens.into_iter().collect())
    }
    pub fn answer(&self, tokens: &[u32]) -> Result<&str> {
        require(
            tokens.last().is_some_and(|id| self.eos.contains(id)),
            "OUTPUT_TRUNCATED",
            "choice did not finish with EOS",
        )?;
        self.node(&tokens[..tokens.len() - 1])?
            .answer
            .as_deref()
            .ok_or_else(|| ModelError::new("INVALID_CHOICE_OUTPUT", "choice is incomplete"))
    }
}

fn greedy_allowed(logits: &Tensor, allowed: &[u32]) -> Result<u32> {
    let values = logits.to_vec1::<f32>()?;
    let candidates: Vec<_> = if allowed.is_empty() {
        (0..values.len() as u32).collect()
    } else {
        allowed.to_vec()
    };
    require(
        !candidates.is_empty() && candidates.iter().all(|id| (*id as usize) < values.len()),
        "INVALID_CHOICES",
        "choice token is outside vocabulary",
    )?;
    require(
        candidates.iter().all(|id| values[*id as usize].is_finite()),
        "MODEL_INFERENCE",
        "logits contain non-finite values",
    )?;
    candidates
        .into_iter()
        .max_by(|a, b| {
            values[*a as usize]
                .total_cmp(&values[*b as usize])
                .then_with(|| b.cmp(a))
        })
        .ok_or_else(|| ModelError::new("MODEL_INFERENCE", "empty vocabulary"))
}

fn filtered_sampling_logits(logits: &Tensor, settings: &SamplingSettings) -> Result<Tensor> {
    let mut values = (logits / settings.temperature)?.to_vec1::<f32>()?;
    require(
        !values.is_empty() && values.iter().all(|x| x.is_finite()),
        "MODEL_INFERENCE",
        "sampling logits must be finite",
    )?;
    let mut order: Vec<_> = (0..values.len()).collect();
    order.sort_by(|a, b| values[*b].total_cmp(&values[*a]).then_with(|| a.cmp(b)));
    let threshold = values[order[settings.top_k.min(order.len()) - 1]];
    for value in &mut values {
        if *value < threshold {
            *value = f32::NEG_INFINITY;
        }
    }
    let tensor = Tensor::from_vec(values.clone(), values.len(), logits.device())?;
    let probabilities = candle_nn::ops::softmax_last_dim(&tensor)?.to_vec1::<f32>()?;
    // Transformers applies top-p after renormalizing the top-k distribution.
    // Candle's combined top-k/top-p helper does not, so keep these two stages explicit.
    order.sort_by(|a, b| {
        probabilities[*a]
            .total_cmp(&probabilities[*b])
            .then_with(|| a.cmp(b))
    });
    let mut cumulative = 0f32;
    for index in order.iter().take(order.len() - 1) {
        cumulative += probabilities[*index];
        if cumulative <= 1.0 - settings.top_p as f32 {
            values[*index] = f32::NEG_INFINITY;
        }
    }
    Ok(Tensor::from_vec(
        values.clone(),
        values.len(),
        logits.device(),
    )?)
}

fn metrics(
    started: Instant,
    input: usize,
    output: usize,
    reasoning: usize,
    final_tokens: usize,
) -> GenerationMetrics {
    #[cfg(unix)]
    let max_rss = {
        let mut usage = std::mem::MaybeUninit::<libc::rusage>::zeroed();
        if unsafe { libc::getrusage(libc::RUSAGE_SELF, usage.as_mut_ptr()) } == 0 {
            unsafe { usage.assume_init().ru_maxrss }
        } else {
            0
        }
    };
    #[cfg(not(unix))]
    let max_rss = 0;
    GenerationMetrics {
        seconds: (started.elapsed().as_secs_f64() * 1000.).round() / 1000.,
        input_tokens: input,
        output_tokens: output,
        reasoning_tokens: reasoning,
        final_tokens,
        max_rss_native: max_rss,
        rss_unit: if cfg!(target_os = "macos") {
            "bytes"
        } else {
            "KiB"
        }
        .into(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn settings_and_thinking_protocol() {
        assert!(GenerationSettings::new(true, Decoding::Greedy, None, None, 180).is_err());
        assert!(
            GenerationSettings::new(false, Decoding::Greedy, Some(1024), Some(1024), 180).is_err()
        );
        let eos = BTreeSet::from([151645]);
        assert_eq!(
            final_token_ids(&[7, 151668, 8, 151645], true, &eos).unwrap(),
            (&[8, 151645][..], 2)
        );
        assert!(final_token_ids(&[151668, 151645], true, &eos).is_err());
        assert!(final_token_ids(&[151667, 8, 151645], false, &eos).is_err());
        assert!(final_token_ids(&[8], false, &eos).is_err());
    }
    #[test]
    fn choice_prefix_and_eos_are_both_legal() {
        let trie = ChoiceTrie::new(
            BTreeMap::from([("A".into(), vec![3]), ("AB".into(), vec![3, 4])]),
            BTreeSet::from([9]),
            8,
        )
        .unwrap();
        assert_eq!(trie.allowed(&[3]).unwrap(), vec![4, 9]);
        assert_eq!(trie.answer(&[3, 9]).unwrap(), "A");
        assert_eq!(trie.answer(&[3, 4, 9]).unwrap(), "AB");
        assert!(trie.answer(&[3, 4]).is_err());
        assert!(trie.allowed(&[5]).is_err());
    }
    #[test]
    fn sampling_normalizes_topk_before_topp() {
        let settings = SamplingSettings {
            temperature: 1.0,
            top_k: 2,
            top_p: 0.8,
            seed: String::new(),
        };
        let logits = Tensor::from_vec(vec![0f32; 100], 100, &Device::Cpu).unwrap();
        // Ties are preserved by top-k, as in Transformers; top-p removes the bottom mass.
        let filtered = filtered_sampling_logits(&logits, &settings)
            .unwrap()
            .to_vec1::<f32>()
            .unwrap();
        assert!(filtered.iter().filter(|x| x.is_finite()).count() <= 81);
        let logits = Tensor::from_vec(
            (0..100)
                .map(|x| {
                    if x == 0 {
                        0.1
                    } else if x == 1 {
                        0.0
                    } else {
                        -0.1
                    }
                })
                .collect::<Vec<f32>>(),
            100,
            &Device::Cpu,
        )
        .unwrap();
        let filtered = filtered_sampling_logits(&logits, &settings)
            .unwrap()
            .to_vec1::<f32>()
            .unwrap();
        assert_eq!(filtered.iter().filter(|x| x.is_finite()).count(), 2);
    }
    #[test]
    fn tiny_native_incremental_logits_match_a_fresh_full_forward() {
        let config = crate::test_support::tiny_config();
        let prototype =
            qwen3::ModelForCausalLM::new(&config, crate::test_support::tiny_builder()).unwrap();
        let mut incremental = prototype.clone();
        incremental
            .forward(
                &Tensor::from_slice(&[1u32, 2], (1, 2), &Device::Cpu).unwrap(),
                0,
            )
            .unwrap();
        let step = incremental
            .forward(
                &Tensor::from_slice(&[3u32], (1, 1), &Device::Cpu).unwrap(),
                2,
            )
            .unwrap();
        let full = prototype
            .clone()
            .forward(
                &Tensor::from_slice(&[1u32, 2, 3], (1, 3), &Device::Cpu).unwrap(),
                0,
            )
            .unwrap();
        let difference = (&step - &full)
            .unwrap()
            .abs()
            .unwrap()
            .max_all()
            .unwrap()
            .to_scalar::<f32>()
            .unwrap();
        assert!(
            difference < 1e-5,
            "incremental/full difference {difference}"
        );
        incremental.clear_kv_cache();
        let reset = incremental
            .forward(
                &Tensor::from_slice(&[1u32, 2, 3], (1, 3), &Device::Cpu).unwrap(),
                0,
            )
            .unwrap();
        assert_eq!(
            reset.flatten_all().unwrap().to_vec1::<f32>().unwrap(),
            full.flatten_all().unwrap().to_vec1::<f32>().unwrap()
        );
    }
    #[test]
    fn deterministic_sampling_and_finite_greedy_choices() {
        let logits = Tensor::from_vec(vec![0f32, 0., 4., 3., 1.], 5, &Device::Cpu).unwrap();
        assert_eq!(greedy_allowed(&logits, &[0, 1, 3]).unwrap(), 3);
        let mut first = LogitsProcessor::from_sampling(42, Sampling::All { temperature: 1.0 });
        let mut second = LogitsProcessor::from_sampling(42, Sampling::All { temperature: 1.0 });
        let first: Vec<_> = (0..30).map(|_| first.sample(&logits).unwrap()).collect();
        let second: Vec<_> = (0..30).map(|_| second.sample(&logits).unwrap()).collect();
        assert_eq!(first, second);
    }
}
