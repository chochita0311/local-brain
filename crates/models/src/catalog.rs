use crate::{ModelError, Result};
use serde::{Deserialize, Serialize};

pub const EMBEDDING_SCHEMA: &str = "localbrain.semantic-model/v1";
pub const GENERATION_OWNER: &str = "localbrain.work-context-model.v1";
pub const GENERATION_HUB_OWNER: &str = "localbrain.work-context-model.v2";
pub const EMBEDDING_FINGERPRINT: &str =
    "855cb5f83b4cbd18bbe1b00ba82945989abeb1acc3530455fb4886e456f5911f";

#[derive(Debug, Copy, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ModelKey {
    #[serde(rename = "embedding")]
    Embedding,
    #[serde(rename = "4b")]
    Generation4b,
    #[serde(rename = "8b")]
    Generation8b,
}

impl ModelKey {
    pub const ALL: [Self; 3] = [Self::Embedding, Self::Generation4b, Self::Generation8b];
    pub fn parse(value: &str) -> Result<Self> {
        match value {
            "embedding" | "Qwen/Qwen3-Embedding-0.6B" => Ok(Self::Embedding),
            "4b" | "Qwen/Qwen3-4B" => Ok(Self::Generation4b),
            "8b" | "Qwen/Qwen3-8B" => Ok(Self::Generation8b),
            _ => Err(ModelError::new(
                "INVALID_MODEL",
                "model is outside the pinned catalog",
            )),
        }
    }
    pub fn spec(self) -> ModelSpec {
        match self {
            Self::Embedding => ModelSpec {
                key: self,
                id: "Qwen/Qwen3-Embedding-0.6B",
                revision: "b22da495047858cce924d27d76261e96be6febc0",
                slug: "qwen3-embedding-0-6b",
                purpose: "full_history_affinity",
                assets: EMBEDDING_ASSETS,
                hashes: &[],
                aggregate: Some(EMBEDDING_FINGERPRINT),
            },
            Self::Generation4b => ModelSpec {
                key: self,
                id: "Qwen/Qwen3-4B",
                revision: "1cfa9a7208912126459214e8b04321603b3df60c",
                slug: "qwen3-4b",
                purpose: "experimental_context_inference",
                assets: GENERATION_4B_ASSETS,
                hashes: GENERATION_4B_HASHES,
                aggregate: None,
            },
            Self::Generation8b => ModelSpec {
                key: self,
                id: "Qwen/Qwen3-8B",
                revision: "b968826d9c46dd6066d109eabc6255188de91218",
                slug: "qwen3-8b",
                purpose: "experimental_context_comparison",
                assets: GENERATION_8B_ASSETS,
                hashes: GENERATION_8B_HASHES,
                aggregate: None,
            },
        }
    }
}

#[derive(Debug, Copy, Clone)]
pub struct ModelSpec {
    pub key: ModelKey,
    pub id: &'static str,
    pub revision: &'static str,
    pub slug: &'static str,
    pub purpose: &'static str,
    pub(crate) assets: &'static [&'static str],
    pub(crate) hashes: &'static [(&'static str, &'static str)],
    pub(crate) aggregate: Option<&'static str>,
}

impl ModelSpec {
    pub fn assets(&self) -> &'static [&'static str] {
        self.assets
    }
    pub fn pinned_hash(&self, name: &str) -> Option<&'static str> {
        self.hashes
            .iter()
            .find(|(path, _)| *path == name)
            .map(|(_, hash)| *hash)
    }
    pub fn snapshot_relative(&self) -> String {
        format!(
            "models--{}/snapshots/{}",
            self.id.replace('/', "--"),
            self.revision
        )
    }
    pub fn experiment_suspended(&self) -> bool {
        self.key != ModelKey::Embedding
    }
}

const EMBEDDING_ASSETS: &[&str] = &[
    "1_Pooling/config.json",
    "config.json",
    "config_sentence_transformers.json",
    "generation_config.json",
    "merges.txt",
    "model.safetensors",
    "modules.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
];
const GENERATION_4B_ASSETS: &[&str] = &[
    "LICENSE",
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
    "model.safetensors.index.json",
    "model-00001-of-00003.safetensors",
    "model-00002-of-00003.safetensors",
    "model-00003-of-00003.safetensors",
];
const GENERATION_8B_ASSETS: &[&str] = &[
    "LICENSE",
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
    "model.safetensors.index.json",
    "model-00001-of-00005.safetensors",
    "model-00002-of-00005.safetensors",
    "model-00003-of-00005.safetensors",
    "model-00004-of-00005.safetensors",
    "model-00005-of-00005.safetensors",
];
const GENERATION_4B_HASHES: &[(&str, &str)] = &[
    (
        "model-00001-of-00003.safetensors",
        "328a91d3122359d5547f9d79521205bc0a46e1f79a792dfe650e99fc2d651223",
    ),
    (
        "model-00002-of-00003.safetensors",
        "6cd087b316306a68c562436b5492edbcf6e16c6dba3a1308279caa5a58e21ca5",
    ),
    (
        "model-00003-of-00003.safetensors",
        "e4bf436957184f4eeb86a80e9db394503f1f56446b2e6b7edeac5b81470f4ca1",
    ),
    (
        "tokenizer.json",
        "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
    ),
];
const GENERATION_8B_HASHES: &[(&str, &str)] = &[
    (
        "model-00001-of-00005.safetensors",
        "31d6a825ae35f11fb85b195b4c42c146c051e446433125a215336abdf95cbf5f",
    ),
    (
        "model-00002-of-00005.safetensors",
        "5991236cea6fe21f3d43cab0f0e84448734fbbe0789816202989f2ddc9d18282",
    ),
    (
        "model-00003-of-00005.safetensors",
        "c5185c4794be2d8a9784d5753c9922db38df478ce11f9ed0b415b7304d896836",
    ),
    (
        "model-00004-of-00005.safetensors",
        "b5ee7de71fbf17db3d5704e0c8f2bc7d005ca9e1d7ca2aeb19827b0cfcaa917a",
    ),
    (
        "model-00005-of-00005.safetensors",
        "20c2d6366ab85c90786ccdd829cd2b9e7d30ef3b2ebbb998280e7e4014b542ff",
    ),
    (
        "tokenizer.json",
        "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
    ),
];
