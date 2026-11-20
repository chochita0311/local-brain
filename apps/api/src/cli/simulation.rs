use super::{
    arguments::{invalid, Arguments},
    search::device,
    CancellationGuard, CommandResult,
};
use localbrain_core::backend::{
    auto_work::{self, NativeSimulationEncoder, SimulationOptions},
    models, BackendError, Config, Result,
};
use localbrain_models::{
    catalog::ModelKey,
    embedding::{EncoderConfig, MAX_BATCH_SIZE},
};
use serde_json::json;
use std::path::PathBuf;
pub fn run(config: &Config, raw: &[String]) -> CommandResult {
    let parsed = Arguments::parse(
        raw,
        &[
            "--inventory-only",
            "--status",
            "--purge",
            "--force-reembed",
            "--show-counts",
        ],
        &[
            "--database",
            "--output",
            "--model-manifest",
            "--device",
            "--chunk-chars",
            "--batch-size",
            "--neighbors",
            "--similarity",
            "--area-resolution",
            "--work-resolution",
        ],
    );
    let args = match parsed {
        Ok(args) => args,
        Err(_) => {
            println!("INVALID_ARGUMENTS");
            return Ok(2);
        }
    };
    if args.count(0, 0).is_err()
        || ["--inventory-only", "--status", "--purge"]
            .iter()
            .filter(|flag| args.flag(flag))
            .count()
            > 1
    {
        println!("INVALID_ARGUMENTS");
        return Ok(2);
    }
    let cancel = CancellationGuard::new()?;
    let result = (|| -> Result<()> {
        let mut config = config.clone();
        if let Some(database) = args.value("--database") {
            config.database_path = PathBuf::from(database);
        }
        let output = args
            .value("--output")
            .map(PathBuf::from)
            .unwrap_or_else(|| config.cache_dir.join("session-simulation"));
        if !args.flag("--status")
            && !args.flag("--purge")
            && output == config.cache_dir.join("session-simulation")
        {
            localbrain_core::backend::storage::files::private_directory(
                &config.cache_dir,
                &config,
            )?;
        }
        let show = args.flag("--show-counts");
        if args.flag("--status") {
            let progress = auto_work::simulation_status(&config, &output, None);
            if cancel.interrupted() {
                return Err(BackendError::invalid(
                    "SIMULATION_INTERRUPTED",
                    "SIMULATION_INTERRUPTED",
                ));
            }
            let progress = progress?;
            println!(
                "SIMULATION_{}",
                progress["state"].as_str().unwrap_or("").to_uppercase()
            );
            if show {
                println!(
                    "{}",
                    json!({"coverage":progress["manifest"].get("coverage").cloned().unwrap_or_else(||json!({})),"encoded":progress.get("encoded").cloned().unwrap_or(json!(0)),"reused":progress.get("reused").cloned().unwrap_or(json!(0)),"total_vectors":progress.get("total_vectors").cloned().unwrap_or(json!(0))})
                );
            }
            return Ok(());
        }
        if args.flag("--purge") {
            auto_work::purge(&config, &output, None)?;
            println!("SIMULATION_PURGED");
            return Ok(());
        }
        let chunk_chars = args.number::<usize>("--chunk-chars", 1800)?;
        if args.flag("--inventory-only") {
            let progress =
                auto_work::prepare_inventory(&config, &output, chunk_chars, None, &cancel.token)?;
            println!("SIMULATION_PREPARED");
            if show {
                println!("{}", progress["manifest"]["coverage"]);
            }
            return Ok(());
        }
        let batch_size = args.number::<usize>("--batch-size", 16)?;
        let parameters = json!({"neighbors":args.number::<usize>("--neighbors",8)?,"similarity":args.number::<f64>("--similarity",0.65)?,"area_resolution":args.number::<f64>("--area-resolution",0.6)?,"work_resolution":args.number::<f64>("--work-resolution",1.2)?,"seed":0});
        auto_work::graph::validate_parameters(&parameters)?;
        let options = EncoderConfig {
            device: device(&args.string("--device", "auto"))?,
            dimension: 1024,
            max_tokens: 1024,
            batch_size: batch_size.clamp(1, MAX_BATCH_SIZE),
        };
        let manifest = args
            .value("--model-manifest")
            .map(PathBuf::from)
            .unwrap_or(models::model_root(&config, ModelKey::Embedding)?.join("model.json"));
        if !manifest.is_file() {
            return Err(invalid("LOCAL_EMBEDDING_MODEL_REQUIRED"));
        }
        let encoder = NativeSimulationEncoder::from_manifest(
            &manifest,
            &models::hub_cache_root(&config)?,
            options,
            &cancel.token,
        )?;
        let report = auto_work::simulate(
            &config,
            &output,
            &encoder,
            &SimulationOptions {
                chunk_chars,
                batch_size,
                parameters,
                force: args.flag("--force-reembed"),
                cancel: cancel.token.clone(),
            },
        )?;
        println!("SIMULATION_COMPLETE_UNASSESSED");
        if show {
            println!(
                "{}",
                json!({"coverage":report["manifest"]["coverage"],"cache":report["cache"]})
            );
        }
        Ok(())
    })();
    match result {
        Ok(()) => Ok(0),
        Err(error)
            if matches!(
                error.code.as_str(),
                "SIMULATION_INTERRUPTED" | "MODEL_CANCELLED"
            ) =>
        {
            println!("SIMULATION_INTERRUPTED");
            Ok(130)
        }
        Err(error) => {
            let code = if error.code == "arguments" {
                if error.message == "LOCAL_EMBEDDING_MODEL_REQUIRED" {
                    "LOCAL_EMBEDDING_MODEL_REQUIRED"
                } else {
                    "INVALID_ARGUMENTS"
                }
            } else if error.message == error.code {
                &error.code
            } else {
                "SIMULATION_FAILED"
            };
            println!("{code}");
            Ok(2)
        }
    }
}
