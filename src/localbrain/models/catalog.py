"""Public pinned model identities and optional feature requirements."""

EMBEDDING_SCHEMA = "localbrain.semantic-model/v1"
EMBEDDING_ID = "Qwen/Qwen3-Embedding-0.6B"
EMBEDDING_REVISION = "b22da495047858cce924d27d76261e96be6febc0"
EMBEDDING_FINGERPRINT = "855cb5f83b4cbd18bbe1b00ba82945989abeb1acc3530455fb4886e456f5911f"
EMBEDDING_ASSETS = (
    "1_Pooling/config.json", "config.json", "config_sentence_transformers.json",
    "generation_config.json", "merges.txt", "model.safetensors", "modules.json",
    "tokenizer.json", "tokenizer_config.json", "vocab.json",
)
MODELS = {
    "embedding": {"id": EMBEDDING_ID, "slug": "qwen3-embedding-0-6b", "purpose": "full_history_affinity"},
    "4b": {"id": "Qwen/Qwen3-4B", "slug": "qwen3-4b", "purpose": "experimental_context_inference"},
    "8b": {"id": "Qwen/Qwen3-8B", "slug": "qwen3-8b", "purpose": "experimental_context_comparison"},
}
RUNTIME_MODULES = ("torch", "transformers", "huggingface_hub", "sentence_transformers", "numpy", "sklearn", "networkx")
