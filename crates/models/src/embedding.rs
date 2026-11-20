//! Qwen3 last-token embeddings from the original verified safetensors.
use crate::assets::{value_digest, ModelIdentity, VerifiedModel};
use crate::catalog::ModelKey;
use crate::tokenizer::OfflineTokenizer;
use crate::{check_cancel, require, Cancellation, ModelError, Result};
use candle_core::{DType, Device, IndexOp, Tensor};
use candle_nn::VarBuilder;
use candle_transformers::models::qwen3;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub const QUERY_INSTRUCTION: &str = "Instruct: Given a search query, retrieve relevant passages from work sessions and documents that answer the query.\nQuery: ";
pub const NATIVE_EMBEDDING_RUNTIME: &str = "localbrain.embedding.candle-qwen3.v1";
pub const MAX_BATCH_SIZE: usize = 64;

#[derive(Debug, Copy, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DevicePreference {
    Auto,
    Cpu,
    Mps,
    Cuda,
}

pub(crate) fn resolve_device(preference: DevicePreference) -> Result<Device> {
    fn metal() -> Result<Device> {
        #[cfg(target_os = "macos")]
        if candle_metal_kernels::metal::Device::system_default().is_none() {
            return Err(ModelError::new(
                "INVALID_DEVICE",
                "Metal device 0 is unavailable in this process",
            ));
        }
        // Candle 0.10 indexes the enumerated device vector with swap_remove;
        // restricted processes with no visible Metal device panic there.
        // Keep explicit selection fallible and Auto's CPU fallback usable.
        std::panic::catch_unwind(|| Device::new_metal(0))
            .map_err(|_| {
                ModelError::new(
                    "INVALID_DEVICE",
                    "Candle 0.10.0 could not initialize Metal device 0 in this process",
                )
            })?
            .map_err(|error| ModelError::new("INVALID_DEVICE", error.to_string()))
    }
    match preference {
        DevicePreference::Cpu => Ok(Device::Cpu),
        DevicePreference::Mps => metal(),
        DevicePreference::Cuda => {
            Device::new_cuda(0).map_err(|e| ModelError::new("INVALID_DEVICE", e.to_string()))
        }
        DevicePreference::Auto => Ok(metal()
            .or_else(|_| {
                Device::new_cuda(0).map_err(|e| ModelError::new("INVALID_DEVICE", e.to_string()))
            })
            .unwrap_or(Device::Cpu)),
    }
}

pub(crate) fn device_name(device: &Device) -> &'static str {
    if device.is_cpu() {
        "cpu"
    } else if device.is_metal() {
        "mps"
    } else {
        "cuda"
    }
}

pub(crate) fn runtime_identity(device: &Device, dtype: &str) -> Value {
    json!({"engine":"candle", "candle_core":"0.10.0", "candle_nn":"0.10.0", "candle_transformers":"0.10.0",
        "tokenizers":"0.22.2", "minijinja":"3.1.0", "architecture":std::env::consts::ARCH,
        "candle_metal_kernels":if device.is_metal(){Some("0.10.2")}else{None},
        "os":std::env::consts::OS, "byteorder": if cfg!(target_endian="little") {"little"}else{"big"},
        "device":device_name(device), "dtype":dtype,
        "cpu_matmul":if device.is_cpu() {Some(if candle_core::utils::has_accelerate() {"apple-accelerate-src-0.3.2"} else if candle_core::utils::has_mkl() {"intel-mkl"} else {"candle-gemm"})} else {None},
        "attention":"candle-qwen3-standard-matmul"})
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncoderConfig {
    pub device: DevicePreference,
    pub dimension: usize,
    pub max_tokens: usize,
    /// Maximum rows per length-sorted batch. Right-padding is strictly after
    /// original positions; causal attention and per-row pooling exclude it.
    pub batch_size: usize,
}
impl Default for EncoderConfig {
    fn default() -> Self {
        Self {
            device: DevicePreference::Auto,
            dimension: 512,
            max_tokens: 1024,
            batch_size: 4,
        }
    }
}
impl EncoderConfig {
    pub fn validate(&self) -> Result<()> {
        require(
            (32..=1024).contains(&self.dimension)
                && (128..=8192).contains(&self.max_tokens)
                && (1..=MAX_BATCH_SIZE).contains(&self.batch_size),
            "INVALID_MODEL_CONFIG",
            "invalid embedding dimension, token budget or batch size",
        )
    }
}

pub struct LocalEncoder {
    verified: VerifiedModel,
    config: EncoderConfig,
    device: Device,
    tokenizer: Option<OfflineTokenizer>,
    // The prototype is never forwarded. Clones share immutable weight tensors,
    // with independent initially empty caches for each input sequence.
    prototype: Option<crate::qwen3_batch::Model>,
}

impl LocalEncoder {
    pub fn new(verified: VerifiedModel, config: EncoderConfig) -> Result<Self> {
        require(
            verified.key() == ModelKey::Embedding,
            "MODEL_MISMATCH",
            "embedding model required",
        )?;
        config.validate()?;
        let device = resolve_device(config.device)?;
        Ok(Self {
            verified,
            config,
            device,
            tokenizer: None,
            prototype: None,
        })
    }
    pub fn is_loaded(&self) -> bool {
        self.prototype.is_some()
    }
    pub fn identity(&self) -> &ModelIdentity {
        self.verified.identity()
    }
    /// Runtime is intentionally different from Python: callers must rebuild old indices.
    pub fn contract(&self, strict_search: bool) -> Value {
        json!({"model_id":self.identity().model_id,"resolved_revision":self.identity().resolved_revision,
            "fingerprint":self.identity().fingerprint,"dimension":self.config.dimension,"max_tokens":self.config.max_tokens,
            "token_windows":if strict_search {"one-molecule-one-vector-v1"} else {"exhaustive-character-bisection.v1"},
            "query_instruction":if strict_search {QUERY_INSTRUCTION}else{""},"dtype":"float32",
            "pooling":"last-token", "normalization":"truncate-dimension-then-l2",
            "input_preprocessing":"sentence-transformers-python3.11-whitespace-strip",
            "post_strip_tokenization":"tokenizer-right-truncate-before-special-postprocessing",
            "window_accumulation":"float32-weight-then-float64-sum",
            "backbone_compatibility":"localbrain.qwen3-broadcast-mask.v2",
            "batching":"length-ascending-causal-right-padding.v1", "batch_size":self.config.batch_size,
            "positions":"fixed-rope-original-valid-token-positions",
            "native_runtime":NATIVE_EMBEDDING_RUNTIME,"runtime":runtime_identity(&self.device,"float32")})
    }
    pub fn contract_fingerprint(&self, strict_search: bool) -> Result<String> {
        value_digest(&self.contract(strict_search))
    }
    pub fn tokenizer(&mut self, cancel: &Cancellation) -> Result<&OfflineTokenizer> {
        check_cancel(cancel)?;
        if self.tokenizer.is_none() {
            self.verified.reverify_tokenizer(cancel)?;
            self.tokenizer = Some(OfflineTokenizer::from_verified(&self.verified)?);
        }
        Ok(self.tokenizer.as_ref().unwrap())
    }
    fn load(&mut self, cancel: &Cancellation) -> Result<()> {
        check_cancel(cancel)?;
        if self.prototype.is_some() {
            return Ok(());
        }
        self.tokenizer(cancel)?;
        self.verified.reverify(cancel)?;
        let snapshot = self.verified.snapshot();
        validate_pooling(snapshot)?;
        let config = read_qwen_config(snapshot)?;
        require(
            config.hidden_size == 1024 && self.config.dimension <= config.hidden_size,
            "INVALID_MODEL",
            "unexpected embedding hidden size",
        )?;
        // The accepted files have just been hashed. Candle owns the maps during load;
        // the application never writes model assets during inference.
        let builder = unsafe {
            VarBuilder::from_mmaped_safetensors(
                &self.verified.weight_files(),
                DType::F32,
                &self.device,
            )?
        };
        require(
            builder.contains_tensor("embed_tokens.weight"),
            "INVALID_MODEL",
            "pinned embedding backbone tensor names are missing",
        )?;
        // The pinned sentence-transformers export stores a bare backbone, while
        // Candle's shared Qwen3 model queries names under `model.`.
        let builder =
            builder.rename_f(|name| name.strip_prefix("model.").unwrap_or(name).to_string());
        let model = crate::qwen3_batch::Model::new(&config, builder)?;
        check_cancel(cancel)?;
        self.prototype = Some(model);
        Ok(())
    }
    /// Search rejects raw inputs above 1024 tokens and never windows them. It
    /// preserves ST's separate strip/right-truncation stage for admitted inputs,
    /// returning one normalized f32 vector and adding the instruction for queries.
    pub fn encode_search(
        &mut self,
        texts: &[String],
        query: bool,
        cancel: &Cancellation,
    ) -> Result<Vec<Vec<f32>>> {
        require(
            matches!(self.config.dimension, 512 | 1024) && self.config.max_tokens == 1024,
            "INVALID_SEARCH_PROFILE",
            "search requires dimension 512/1024 and 1024 input tokens",
        )?;
        check_cancel(cancel)?;
        if texts.is_empty() {
            return Ok(Vec::new());
        }
        let inputs: Vec<_> = texts
            .iter()
            .map(|text| {
                if query {
                    format!("{QUERY_INSTRUCTION}{text}")
                } else {
                    text.clone()
                }
            })
            .collect();
        let max_tokens = self.config.max_tokens;
        let tokenizer = self.tokenizer(cancel)?;
        let raw_tokens: Vec<_> = inputs
            .iter()
            .map(|input| tokenizer.encode(input, true))
            .collect::<Result<_>>()?;
        require(
            raw_tokens.iter().all(|input| input.len() <= 1024),
            "SEARCH_INPUT_TOO_LONG",
            "search input exceeds 1024 tokens",
        )?;
        // The Python boundary checks the original input's budget first. The
        // pinned Sentence Transformers module then applies Python str.strip()
        // before model tokenization, including for each exhaustive window.
        let tokens: Vec<_> = inputs
            .iter()
            .zip(raw_tokens)
            .map(|(input, raw)| model_tokens(tokenizer, input, raw, max_tokens))
            .collect::<Result<_>>()?;
        self.load(cancel)?;
        self.encode_token_batches(&tokens, cancel)
    }
    /// Legacy affinity contract: normalized window vectors are token-weighted and
    /// summed in f64, without a final normalization and without losing a tail.
    pub fn encode_exhaustive(
        &mut self,
        texts: &[String],
        cancel: &Cancellation,
    ) -> Result<Vec<Vec<f64>>> {
        check_cancel(cancel)?;
        if texts.is_empty() {
            return Ok(Vec::new());
        }
        self.load(cancel)?;
        let mut result = vec![vec![0f64; self.config.dimension]; texts.len()];
        let mut inputs = Vec::new();
        let mut owners = Vec::new();
        let tokenizer = self.tokenizer.as_ref().unwrap();
        let max_tokens = self.config.max_tokens;
        for (index, text) in texts.iter().enumerate() {
            let parts = collect_token_windows(text, tokenizer, max_tokens, cancel, |part, raw| {
                (part, raw)
            })?;
            for (text, raw) in parts {
                let weight = raw.len().max(1);
                let tokens = model_tokens(tokenizer, text, raw, max_tokens)?;
                inputs.push(tokens);
                owners.push((index, weight));
                if inputs.len() >= self.config.batch_size {
                    self.accumulate_windows(&inputs, &owners, &mut result, cancel)?;
                    inputs.clear();
                    owners.clear();
                }
            }
        }
        self.accumulate_windows(&inputs, &owners, &mut result, cancel)?;
        Ok(result)
    }
    fn accumulate_windows(
        &self,
        inputs: &[Vec<u32>],
        owners: &[(usize, usize)],
        result: &mut [Vec<f64>],
        cancel: &Cancellation,
    ) -> Result<()> {
        for (vector, (index, weight)) in self
            .encode_token_batches(inputs, cancel)?
            .into_iter()
            .zip(owners)
        {
            for (sum, value) in result[*index].iter_mut().zip(vector) {
                // NumPy rounds vector * weight in f32, then accumulates in f64.
                *sum += f64::from(value * (*weight as f32));
            }
        }
        Ok(())
    }
    fn encode_token_batches(
        &self,
        inputs: &[Vec<u32>],
        cancel: &Cancellation,
    ) -> Result<Vec<Vec<f32>>> {
        check_cancel(cancel)?;
        require(
            inputs
                .iter()
                .all(|tokens| !tokens.is_empty() && tokens.len() <= self.config.max_tokens),
            "TOKEN_WINDOW_UNAVAILABLE",
            "empty or over-budget token input",
        )?;
        let pad = self
            .tokenizer
            .as_ref()
            .and_then(OfflineTokenizer::pad_token_id)
            .ok_or_else(|| {
                ModelError::new(
                    "INVALID_MODEL",
                    "pinned embedding tokenizer pad token is missing",
                )
            })?;
        let mut indices: Vec<_> = (0..inputs.len()).collect();
        // Keep a final partial batch with the longest inputs; descending order
        // would fill their expensive padding with otherwise short sequences.
        indices.sort_by_key(|index| (inputs[*index].len(), *index));
        let mut result = vec![None; inputs.len()];
        for batch in indices.chunks(self.config.batch_size) {
            let length = inputs[*batch.last().unwrap()].len();
            check_cancel(cancel)?;
            let mut model = self.prototype.as_ref().unwrap().clone();
            let mut values = vec![pad; batch.len() * length];
            for (position, index) in batch.iter().enumerate() {
                values[position * length..position * length + inputs[*index].len()]
                    .copy_from_slice(&inputs[*index]);
            }
            let input = Tensor::from_vec(values, (batch.len(), length), &self.device)?;
            let hidden = model.forward(&input, 0)?;
            for (position, index) in batch.iter().enumerate() {
                // Original tokens occupy positions 0..len. A causal query
                // there cannot attend future right-padding. Dynamic RoPE
                // scaling is refused by read_qwen_config before loading.
                let valid = hidden
                    .narrow(0, position, 1)?
                    .narrow(1, 0, inputs[*index].len())?;
                result[*index] = Some(last_token_vector(&valid, self.config.dimension)?);
            }
            self.device.synchronize()?;
            check_cancel(cancel)?;
        }
        Ok(result.into_iter().map(Option::unwrap).collect())
    }
}

fn python_strip(text: &str) -> &str {
    // Frozen Python 3.11 / Unicode 14 str.isspace(), including the four C0
    // separators that are outside Unicode's White_Space property.
    text.trim_matches(|c| {
        matches!(c,
        '\u{0009}'..='\u{000d}' | '\u{001c}'..='\u{0020}' | '\u{0085}' |
        '\u{00a0}' | '\u{1680}' | '\u{2000}'..='\u{200a}' | '\u{2028}' |
        '\u{2029}' | '\u{202f}' | '\u{205f}' | '\u{3000}')
    })
}

fn model_tokens(
    tokenizer: &OfflineTokenizer,
    text: &str,
    raw_tokens: Vec<u32>,
    max_tokens: usize,
) -> Result<Vec<u32>> {
    let stripped = python_strip(text);
    // Admission already checked the raw budget. Reuse those IDs only when
    // stripping leaves the input unchanged.
    if stripped.len() == text.len() {
        return Ok(raw_tokens);
    }
    let tokens = tokenizer.encode(stripped, true)?;
    // Frozen ST5.1.2 Transformer.tokenize applies right truncation after strip.
    // Raw search input is checked separately above. Removing leading whitespace
    // can increase BPE token count (" accountability" is 2 tokens, unspaced 3).
    // Preserve previously admitted raw<=1024 inputs at this second stage.
    if tokens.len() <= max_tokens {
        Ok(tokens)
    } else {
        tokenizer.encode_right_truncated(stripped, true, max_tokens)
    }
}

pub fn token_windows<'a>(
    text: &'a str,
    tokenizer: &OfflineTokenizer,
    max_tokens: usize,
    cancel: &Cancellation,
) -> Result<Vec<(&'a str, usize)>> {
    collect_token_windows(text, tokenizer, max_tokens, cancel, |part, tokens| {
        (part, tokens.len().max(1))
    })
}

fn collect_token_windows<'a, T>(
    text: &'a str,
    tokenizer: &OfflineTokenizer,
    max_tokens: usize,
    cancel: &Cancellation,
    accepted: impl Fn(&'a str, Vec<u32>) -> T,
) -> Result<Vec<T>> {
    require(
        max_tokens > 0,
        "INVALID_MODEL_CONFIG",
        "token budget must be positive",
    )?;
    let mut pending = vec![text];
    let mut result = Vec::new();
    while let Some(part) = pending.pop() {
        check_cancel(cancel)?;
        let tokens = tokenizer.encode(part, true)?;
        if tokens.len() <= max_tokens {
            result.push(accepted(part, tokens));
        } else {
            let length = part.chars().count();
            require(
                length > 1,
                "TOKEN_WINDOW_UNAVAILABLE",
                "one character exceeds the token budget",
            )?;
            let middle = part.char_indices().nth(length / 2).unwrap().0;
            pending.push(&part[middle..]);
            pending.push(&part[..middle]);
        }
    }
    Ok(result)
}

pub(crate) fn read_qwen_config(snapshot: &std::path::Path) -> Result<qwen3::Config> {
    let value: Value = serde_json::from_slice(&std::fs::read(snapshot.join("config.json"))?)?;
    require(
        value.get("model_type").and_then(Value::as_str) == Some("qwen3")
            && value.get("auto_map").is_none()
            && value.get("rope_scaling").is_none_or(Value::is_null),
        "INVALID_MODEL",
        "unsupported Qwen3 architecture or remote code",
    )?;
    let config: qwen3::Config = serde_json::from_value(value)?;
    require(
        config.hidden_size > 0
            && config.num_attention_heads > 0
            && config.num_key_value_heads > 0
            && config
                .num_attention_heads
                .is_multiple_of(config.num_key_value_heads)
            && config.head_dim > 0
            && config.head_dim.is_multiple_of(2)
            && config.max_position_embeddings > 0
            && !config.use_sliding_window,
        "INVALID_MODEL",
        "unsupported Qwen3 dimensions or sliding-window attention",
    )?;
    Ok(config)
}

fn validate_pooling(snapshot: &std::path::Path) -> Result<()> {
    let pooling: Value =
        serde_json::from_slice(&std::fs::read(snapshot.join("1_Pooling/config.json"))?)?;
    let modules: Value = serde_json::from_slice(&std::fs::read(snapshot.join("modules.json"))?)?;
    let expected_modules = [
        "sentence_transformers.models.Transformer",
        "sentence_transformers.models.Pooling",
        "sentence_transformers.models.Normalize",
    ];
    require(
        modules.as_array().is_some_and(|xs| {
            xs.len() == 3
                && xs
                    .iter()
                    .zip(expected_modules)
                    .all(|(x, expected)| x.get("type").and_then(Value::as_str) == Some(expected))
        }) && pooling
            .get("word_embedding_dimension")
            .and_then(Value::as_u64)
            == Some(1024)
            && pooling
                .get("pooling_mode_lasttoken")
                .and_then(Value::as_bool)
                == Some(true)
            && pooling.get("include_prompt").and_then(Value::as_bool) == Some(true)
            && [
                "pooling_mode_cls_token",
                "pooling_mode_mean_tokens",
                "pooling_mode_max_tokens",
                "pooling_mode_mean_sqrt_len_tokens",
                "pooling_mode_weightedmean_tokens",
            ]
            .iter()
            .all(|key| pooling.get(key).and_then(Value::as_bool) == Some(false)),
        "INVALID_MODEL",
        "pinned embedding pipeline must use last-token pooling and normalization",
    )
}

fn last_token_vector(hidden: &Tensor, dimension: usize) -> Result<Vec<f32>> {
    let (batch, tokens, width) = hidden.dims3()?;
    require(
        batch == 1 && tokens > 0 && dimension > 0 && dimension <= width,
        "MODEL_INFERENCE",
        "invalid embedding shape",
    )?;
    let vector = hidden
        .i((0, tokens - 1))?
        .narrow(0, 0, dimension)?
        .to_dtype(DType::F32)?;
    let norm = vector.sqr()?.sum_all()?.sqrt()?.to_scalar::<f32>()?;
    require(
        norm.is_finite() && norm > 0.0,
        "MODEL_INFERENCE",
        "embedding norm must be finite and nonzero",
    )?;
    let output = (vector / f64::from(norm))?.to_vec1::<f32>()?;
    require(
        output.iter().all(|x| x.is_finite()),
        "MODEL_INFERENCE",
        "embedding contains non-finite values",
    )?;
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[cfg(target_os = "macos")]
    #[test]
    fn no_visible_metal_device_is_explicit_error_or_auto_cpu() {
        if candle_metal_kernels::metal::Device::system_default().is_none() {
            assert_eq!(
                resolve_device(DevicePreference::Mps).unwrap_err().code,
                "INVALID_DEVICE"
            );
            assert!(resolve_device(DevicePreference::Auto).unwrap().is_cpu());
        }
    }
    fn tokenizer_lifetime_fixture() -> (tempfile::TempDir, VerifiedModel) {
        let dir = tempfile::tempdir().unwrap();
        let snapshot = dir.path().join("snapshot");
        std::fs::create_dir(&snapshot).unwrap();
        std::fs::write(snapshot.join("config.json"), br#"{"model_type":"qwen3"}"#).unwrap();
        std::fs::write(
            snapshot.join("tokenizer.json"),
            OfflineTokenizer::synthetic()
                .inner
                .to_string(false)
                .unwrap(),
        )
        .unwrap();
        std::fs::write(
            snapshot.join("tokenizer_config.json"),
            br#"{"pad_token":"[UNK]"}"#,
        )
        .unwrap();
        std::fs::write(
            snapshot.join("model.safetensors"),
            b"original synthetic weights",
        )
        .unwrap();
        let verified = crate::assets::fixture_verified(
            &snapshot,
            &[
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "model.safetensors",
            ],
        );
        (dir, verified)
    }
    #[test]
    fn tokenizer_revalidation_refuses_changed_json_and_config() {
        for name in ["tokenizer.json", "tokenizer_config.json"] {
            let (_dir, verified) = tokenizer_lifetime_fixture();
            verified.reverify(&crate::cancellation()).unwrap();
            let path = verified.snapshot().join(name);
            let mut bytes = std::fs::read(&path).unwrap();
            bytes[0] = b'[';
            std::fs::write(path, bytes).unwrap();
            let mut encoder = LocalEncoder::new(
                verified,
                EncoderConfig {
                    device: DevicePreference::Cpu,
                    ..Default::default()
                },
            )
            .unwrap();
            assert_eq!(
                encoder
                    .tokenizer(&crate::cancellation())
                    .err()
                    .unwrap()
                    .code,
                "MODEL_ASSETS_CHANGED"
            );
            assert!(!encoder.is_loaded());
        }
    }
    #[test]
    fn tokenizer_success_never_grants_changed_weights_inference() {
        let (_dir, verified) = tokenizer_lifetime_fixture();
        let cancel = crate::cancellation();
        verified.reverify(&cancel).unwrap();
        std::fs::write(
            verified.snapshot().join("model.safetensors"),
            b"modified synthetic weights",
        )
        .unwrap();
        let mut encoder = LocalEncoder::new(
            verified,
            EncoderConfig {
                device: DevicePreference::Cpu,
                ..Default::default()
            },
        )
        .unwrap();
        assert_eq!(
            encoder
                .tokenizer(&cancel)
                .unwrap()
                .encode("x", true)
                .unwrap(),
            vec![1]
        );
        assert!(!encoder.is_loaded());
        assert_eq!(
            encoder
                .encode_search(&["x".into()], false, &cancel)
                .unwrap_err()
                .code,
            "MODEL_ASSETS_CHANGED"
        );
        assert!(!encoder.is_loaded());
    }
    #[test]
    fn transformer_strips_python_whitespace_without_changing_window_weights() {
        assert_eq!(python_strip("\u{001c}\u{0085}\u{3000}alpha \n"), "alpha");
        assert_eq!(
            python_strip("\u{200b}alpha\u{200b}"),
            "\u{200b}alpha\u{200b}"
        );
        assert_eq!(python_strip(" alpha beta "), "alpha beta");
        let weight = 515usize;
        let value = 0.12345679f32;
        assert_ne!(
            f64::from(value * weight as f32),
            f64::from(value) * weight as f64
        );
    }
    #[test]
    fn last_token_pooling_truncates_before_normalizing() {
        let tensor =
            Tensor::from_vec(vec![9f32, 9., 9., 3., 4., 12.], (1, 2, 3), &Device::Cpu).unwrap();
        assert_eq!(last_token_vector(&tensor, 2).unwrap(), vec![0.6, 0.8]);
        let full = last_token_vector(&tensor, 3).unwrap();
        assert!((full[2] - 12. / 13.).abs() < 1e-6);
    }
    #[test]
    fn unicode_windows_cover_every_character_and_tail() {
        let tokenizer = OfflineTokenizer::synthetic();
        let text = "가 x 😀 x tail";
        let parts = token_windows(text, &tokenizer, 2, &crate::cancellation()).unwrap();
        assert_eq!(
            parts.iter().map(|(text, _)| *text).collect::<String>(),
            text
        );
        assert!(parts.iter().all(|(text, weight)| *weight
            == tokenizer.encode(text, true).unwrap().len().max(1)
            && *weight <= 2));
        assert!(parts.last().unwrap().0.ends_with("tail"));
    }
    #[test]
    fn tiny_native_backbone_is_independent_between_sequences() {
        let directory = tempfile::tempdir().unwrap();
        let weights = directory.path().join("tiny.safetensors");
        candle_core::safetensors::save(&crate::test_support::tiny_weights(true), &weights).unwrap();
        let builder = unsafe {
            VarBuilder::from_mmaped_safetensors(&[weights], DType::F32, &Device::Cpu).unwrap()
        }
        .rename_f(|name| name.strip_prefix("model.").unwrap_or(name).into());
        let prototype = qwen3::Model::new(&crate::test_support::tiny_config(), builder).unwrap();
        let input = Tensor::from_slice(&[1u32, 2, 3], (1, 3), &Device::Cpu).unwrap();
        let first = prototype.clone().forward(&input, 0).unwrap();
        let _other = prototype
            .clone()
            .forward(
                &Tensor::from_slice(&[6u32, 7], (1, 2), &Device::Cpu).unwrap(),
                0,
            )
            .unwrap();
        let repeated = prototype.clone().forward(&input, 0).unwrap();
        let vector = last_token_vector(&first, 4).unwrap();
        assert_eq!(vector, last_token_vector(&repeated, 4).unwrap());
        assert!((vector.iter().map(|x| x * x).sum::<f32>() - 1.0).abs() < 1e-5);
        assert!(vector.iter().all(|x| x.is_finite()));
    }

    #[test]
    fn equal_length_batch_matches_original_single_sequence_backbone() {
        let config = crate::test_support::tiny_config();
        let builder = crate::test_support::tiny_builder();
        let original = qwen3::Model::new(&config, builder.clone()).unwrap();
        let compatibility = crate::qwen3_batch::Model::new(&config, builder).unwrap();
        let inputs = [[1u32, 2, 3], [6, 7, 8]];
        let batch = Tensor::from_vec(
            inputs.into_iter().flatten().collect::<Vec<_>>(),
            (2, 3),
            &Device::Cpu,
        )
        .unwrap();
        // Freeze the upstream failure that necessitates the narrowly owned copy.
        let upstream = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            original.clone().forward(&batch, 0)
        }));
        assert!(matches!(upstream, Err(_) | Ok(Err(_))));
        let actual = compatibility.clone().forward(&batch, 0).unwrap();
        for (index, tokens) in inputs.iter().enumerate() {
            let single = original
                .clone()
                .forward(
                    &Tensor::from_slice(tokens, (1, 3), &Device::Cpu).unwrap(),
                    0,
                )
                .unwrap();
            let a = last_token_vector(&actual.narrow(0, index, 1).unwrap(), 4).unwrap();
            let b = last_token_vector(&single, 4).unwrap();
            for (a, b) in a.iter().zip(b) {
                assert!((a - b).abs() < 1e-6);
            }
        }
    }
    #[test]
    fn mixed_length_right_padding_cannot_change_valid_token_states() {
        let config = crate::test_support::tiny_config();
        let builder = crate::test_support::tiny_builder();
        let original = qwen3::Model::new(&config, builder.clone()).unwrap();
        let compatibility = crate::qwen3_batch::Model::new(&config, builder).unwrap();
        let inputs = [vec![1u32, 2, 3], vec![6, 7]];
        for padding in [0, 15] {
            let batch =
                Tensor::from_slice(&[1u32, 2, 3, 6, 7, padding], (2, 3), &Device::Cpu).unwrap();
            let actual = compatibility.clone().forward(&batch, 0).unwrap();
            for (index, tokens) in inputs.iter().enumerate() {
                let single = original
                    .clone()
                    .forward(
                        &Tensor::from_slice(tokens, (1, tokens.len()), &Device::Cpu).unwrap(),
                        0,
                    )
                    .unwrap();
                let valid = actual
                    .narrow(0, index, 1)
                    .unwrap()
                    .narrow(1, 0, tokens.len())
                    .unwrap();
                let a = valid.flatten_all().unwrap().to_vec1::<f32>().unwrap();
                let b = single.flatten_all().unwrap().to_vec1::<f32>().unwrap();
                for (a, b) in a.iter().zip(b) {
                    assert!((a - b).abs() < 1e-5);
                }
            }
        }
    }
}
