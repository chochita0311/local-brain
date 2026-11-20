//! Opt-in numerical proof using only explicitly supplied, already cached public weights.
//! This test never installs/registers assets or accesses an application corpus.
use localbrain_models::embedding::{token_windows, DevicePreference, EncoderConfig, LocalEncoder};
use localbrain_models::{assets::verify_cached, cancellation, catalog::ModelKey};
use serde_json::{json, Value};
use std::{fs, path::PathBuf, time::Instant};

#[test]
#[ignore = "requires explicit pinned public cache and private proof output; performs real inference"]
fn cached_embedding_numerical_proof() {
    let cache = PathBuf::from(
        std::env::var_os("LOCALBRAIN_REAL_MODEL_CACHE").expect("explicit cache required"),
    );
    let output = PathBuf::from(
        std::env::var_os("LOCALBRAIN_MODEL_PROOF_OUTPUT").expect("explicit proof output required"),
    );
    assert!(
        !output
            .canonicalize()
            .unwrap()
            .starts_with(cache.canonicalize().unwrap()),
        "proof output must be outside the model cache"
    );
    let corpus_text = include_str!("fixtures/embedding-proof-inputs.json");
    let corpus: Value = serde_json::from_str(corpus_text).unwrap();
    fs::write(output.join("synthetic-corpus.json"), corpus_text).unwrap();
    let documents: Vec<String> = serde_json::from_value(corpus["documents"].clone()).unwrap();
    let queries: Vec<String> = serde_json::from_value(corpus["queries"].clone()).unwrap();
    let long = corpus["long"].as_str().unwrap().to_string();
    let budget_exact = corpus["budget_exact"].as_str().unwrap().to_string();
    let budget_above = corpus["budget_above"].as_str().unwrap().to_string();
    let post_strip = corpus["post_strip_boundary"].as_str().unwrap().to_string();
    let device = match std::env::var("LOCALBRAIN_REAL_MODEL_DEVICE").as_deref() {
        Ok("cpu") => DevicePreference::Cpu,
        Ok("mps") => DevicePreference::Mps,
        _ => panic!("explicit cpu/mps device required"),
    };
    let cancel = cancellation();
    let started = Instant::now();
    let verified = verify_cached(ModelKey::Embedding, &cache, &cancel).unwrap();
    let verification_seconds = started.elapsed().as_secs_f64();
    let mut profiles = Vec::new();
    for dimension in [512, 1024] {
        let started = Instant::now();
        let mut encoder = LocalEncoder::new(
            verified.clone(),
            EncoderConfig {
                device,
                dimension,
                ..Default::default()
            },
        )
        .unwrap();
        let construction_seconds = started.elapsed().as_secs_f64();
        let started = Instant::now();
        let tokenizer = encoder.tokenizer(&cancel).unwrap();
        let document_tokens: Vec<_> = documents
            .iter()
            .map(|s| tokenizer.encode(s, true).unwrap())
            .collect();
        let query_tokens: Vec<_> = queries
            .iter()
            .map(|s| {
                tokenizer
                    .encode(
                        &format!("{}{}", localbrain_models::embedding::QUERY_INSTRUCTION, s),
                        true,
                    )
                    .unwrap()
            })
            .collect();
        let windows: Vec<_> = token_windows(&long, tokenizer, 1024, &cancel)
            .unwrap()
            .into_iter()
            .map(|(s, w)| json!({"text":s,"weight":w}))
            .collect();
        let boundary_token_counts = [
            tokenizer.encode(&budget_exact, true).unwrap().len(),
            tokenizer.encode(&budget_above, true).unwrap().len(),
        ];
        assert_eq!(boundary_token_counts, [1024, 1025]);
        let post_strip_counts = [
            tokenizer.encode(&post_strip, true).unwrap().len(),
            tokenizer.encode(post_strip.trim(), true).unwrap().len(),
        ];
        assert_eq!(post_strip_counts, [1024, 1025]);
        let tokenizer_seconds = started.elapsed().as_secs_f64();
        let boundary_model_tokens = [&budget_exact, &post_strip]
            .iter()
            .map(|text| {
                tokenizer
                    .encode_right_truncated(text.trim(), true, 1024)
                    .unwrap()
            })
            .collect::<Vec<_>>();
        let started = Instant::now();
        let first = encoder
            .encode_search(&documents[..1], false, &cancel)
            .unwrap();
        let cold_first_seconds = started.elapsed().as_secs_f64();
        let started = Instant::now();
        let document_vectors = encoder.encode_search(&documents, false, &cancel).unwrap();
        let warm_documents_seconds = started.elapsed().as_secs_f64();
        let started = Instant::now();
        let query_vectors = encoder.encode_search(&queries, true, &cancel).unwrap();
        let warm_queries_seconds = started.elapsed().as_secs_f64();
        for vector in document_vectors.iter().chain(&query_vectors) {
            assert_eq!(vector.len(), dimension);
            assert!(vector.iter().all(|x| x.is_finite()));
            let norm = vector
                .iter()
                .map(|x| f64::from(*x).powi(2))
                .sum::<f64>()
                .sqrt();
            assert!((norm - 1.).abs() < 2e-5, "normalized output: {norm}");
        }
        for (a, b) in first[0].iter().zip(&document_vectors[0]) {
            assert!(
                (*a - *b).abs() < 1e-6,
                "independent sequence changed output"
            );
        }
        let over_budget = encoder
            .encode_search(std::slice::from_ref(&long), false, &cancel)
            .unwrap_err();
        let boundary_above = encoder
            .encode_search(std::slice::from_ref(&budget_above), false, &cancel)
            .unwrap_err();
        let boundary_vector = encoder
            .encode_search(&[budget_exact.clone(), post_strip.clone()], false, &cancel)
            .unwrap();
        let started = Instant::now();
        let exhaustive = encoder
            .encode_exhaustive(std::slice::from_ref(&long), &cancel)
            .unwrap();
        let exhaustive_seconds = started.elapsed().as_secs_f64();
        cancel.store(true, std::sync::atomic::Ordering::Release);
        let cancelled = encoder
            .encode_search(&documents, false, &cancel)
            .unwrap_err();
        assert_eq!(cancelled.code, "MODEL_CANCELLED");
        cancel.store(false, std::sync::atomic::Ordering::Release);
        profiles.push(json!({"dimension":dimension, "contract":encoder.contract(true),
            "construction_seconds":construction_seconds,"tokenizer_seconds":tokenizer_seconds,
            "cold_first_seconds":cold_first_seconds,"warm_documents_seconds":warm_documents_seconds,
            "warm_queries_seconds":warm_queries_seconds,"exhaustive_seconds":exhaustive_seconds,
            "document_tokens":document_tokens,"query_tokens":query_tokens,"windows":windows,
            "boundary_token_counts":boundary_token_counts,"post_strip_counts":post_strip_counts,"boundary_model_tokens":boundary_model_tokens,"boundary_above_code":boundary_above.code,"boundary_vector":boundary_vector,"cancel_code":cancelled.code,
            "first":first,"documents":document_vectors,"queries":query_vectors,"exhaustive":exhaustive,
            "over_budget_code":over_budget.code}));
        fs::write(
            output.join(format!("native-{:?}-{}.json", device, dimension)),
            serde_json::to_vec_pretty(profiles.last().unwrap()).unwrap(),
        )
        .unwrap();
    }
    fs::write(output.join(format!("native-{:?}.json",device)), serde_json::to_vec_pretty(&json!({
        "verification_seconds":verification_seconds,"identity":verified.identity(),"files":verified.files(),"profiles":profiles,
        "profile":if cfg!(debug_assertions){"debug"}else{"release"}, "toolchain_environment":std::env::var("RUSTUP_TOOLCHAIN").ok(), "cache_access":"read-only pinned public original assets"
    })).unwrap()).unwrap();
}
