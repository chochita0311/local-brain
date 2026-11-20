//! Tiny deterministic tensors and tokenizer; never read real user assets.
use candle_core::{DType, Device, Tensor};
use candle_nn::{Activation, VarBuilder};
use candle_transformers::models::qwen3;
use std::collections::HashMap;

pub fn tiny_config() -> qwen3::Config {
    qwen3::Config {
        vocab_size: 16,
        hidden_size: 4,
        intermediate_size: 6,
        num_hidden_layers: 1,
        num_attention_heads: 2,
        num_key_value_heads: 1,
        head_dim: 2,
        attention_bias: false,
        max_position_embeddings: 32,
        sliding_window: None,
        max_window_layers: 1,
        tie_word_embeddings: true,
        rope_theta: 10000.0,
        rms_norm_eps: 1e-6,
        use_sliding_window: false,
        hidden_act: Activation::Silu,
    }
}

pub fn tiny_weights(bare: bool) -> HashMap<String, Tensor> {
    let mut weights = HashMap::new();
    let prefix = if bare { "" } else { "model." };
    for (name, shape) in [
        ("embed_tokens.weight", vec![16, 4]),
        ("norm.weight", vec![4]),
        ("layers.0.input_layernorm.weight", vec![4]),
        ("layers.0.post_attention_layernorm.weight", vec![4]),
        ("layers.0.self_attn.q_proj.weight", vec![4, 4]),
        ("layers.0.self_attn.k_proj.weight", vec![2, 4]),
        ("layers.0.self_attn.v_proj.weight", vec![2, 4]),
        ("layers.0.self_attn.o_proj.weight", vec![4, 4]),
        ("layers.0.self_attn.q_norm.weight", vec![2]),
        ("layers.0.self_attn.k_norm.weight", vec![2]),
        ("layers.0.mlp.gate_proj.weight", vec![6, 4]),
        ("layers.0.mlp.up_proj.weight", vec![6, 4]),
        ("layers.0.mlp.down_proj.weight", vec![4, 6]),
    ] {
        let size: usize = shape.iter().product();
        let values = if shape.len() == 1 {
            vec![1f32; size]
        } else {
            (0..size)
                .map(|i| ((i * 7 + 3) % 23) as f32 / 23.0 - 0.3)
                .collect()
        };
        weights.insert(
            format!("{prefix}{name}"),
            Tensor::from_vec(values, shape, &Device::Cpu).unwrap(),
        );
    }
    weights
}

pub fn tiny_builder() -> VarBuilder<'static> {
    VarBuilder::from_tensors(tiny_weights(false), DType::F32, &Device::Cpu)
}
