use super::{
    arguments::{invalid, Arguments},
    CancellationGuard, CommandResult,
};
use localbrain_core::backend::{
    search::{self, index, model::NativeEncoder, retrieval::Retriever, Profile, SearchService},
    Result,
};
use localbrain_models::embedding::{DevicePreference, EncoderConfig};
use serde_json::Value;
use std::{io::Write, sync::Arc};
pub(super) fn device(value: &str) -> Result<DevicePreference> {
    match value {
        "auto" => Ok(DevicePreference::Auto),
        "cpu" => Ok(DevicePreference::Cpu),
        "mps" => Ok(DevicePreference::Mps),
        "cuda" => Ok(DevicePreference::Cuda),
        _ => Err(invalid("invalid device")),
    }
}
pub fn run(config: &localbrain_core::backend::Config, raw: &[String]) -> CommandResult {
    let args = Arguments::parse(
        raw,
        &["--rebuild"],
        &[
            "--target",
            "--dimension",
            "--overlap",
            "--cutoff",
            "--device",
            "--batch-size",
            "--mode",
            "--limit",
        ],
    )?;
    let action = args.positional(0)?;
    let cancel = CancellationGuard::new()?;
    let result = (|| -> Result<Option<Value>> {
        match action {
            "status" => {
                args.count(1, 1)?;
                println!("{}", SearchService::new(config.clone()).status()?);
            }
            "prepare" => {
                args.count(1, 1)?;
                let profile = Profile {
                    target: args.number("--target", 512)?,
                    dimension: args.number("--dimension", 512)?,
                    overlap: args.number("--overlap", 0)?,
                    cutoff: args.number("--cutoff", Profile::default().cutoff)?,
                };
                profile.validate()?;
                let requested = args.string("--device", "auto");
                if requested == "cuda" {
                    return Err(invalid("search device must be auto, mps, or cpu"));
                }
                let batch = args.number::<usize>("--batch-size", 8)?;
                let encoder = NativeEncoder::new_with_cancellation(
                    config,
                    profile,
                    Some(EncoderConfig {
                        device: device(&requested)?,
                        dimension: profile.dimension,
                        max_tokens: 1024,
                        batch_size: batch,
                    }),
                    &cancel.token,
                )?;
                index::save_settings(config, profile, true)?;
                let mut last = None;
                index::prepare(
                    config,
                    &encoder,
                    profile,
                    &cancel.token,
                    args.flag("--rebuild"),
                    &mut |value| {
                        let bucket = value["parents"].as_u64().unwrap_or(0) / 25;
                        if last != Some(bucket) || value["state"] != "preparing" {
                            println!("{value}");
                            let _ = std::io::stdout().flush();
                            last = Some(bucket);
                        }
                    },
                )?;
            }
            "query" => {
                args.count(2, 2)?;
                return index::read_published(config, || {
                    let (settings, profile) = index::read_settings(config)?;
                    if settings["enabled"] != true {
                        return Err(search::failure("SEARCH_DISABLED"));
                    }
                    let encoder =
                        Arc::new(NativeEncoder::for_index(config, profile, &cancel.token)?);
                    let retriever = Retriever::new(config.clone(), profile, encoder);
                    retriever
                        .search_with_cancellation(
                            args.positional(1)?,
                            &args.string("--mode", "hybrid"),
                            args.value("--cutoff")
                                .map(|_| args.number::<f64>("--cutoff", profile.cutoff))
                                .transpose()?,
                            1,
                            args.number("--limit", 20)?,
                            &cancel.token,
                        )
                        .map(Some)
                });
            }
            _ => return Err(invalid("invalid search command")),
        }
        Ok(None)
    })();
    if cancel.interrupted() {
        println!("SEARCH_INTERRUPTED");
        return Ok(130);
    }
    match result {
        Ok(response) => {
            if let Some(response) = response {
                println!("{response}");
            }
            Ok(0)
        }
        Err(error) if error.code == "arguments" => Err(error),
        Err(error) => {
            let code = if [
                "SEARCH_DISABLED",
                "SEARCH_MODEL_MISSING",
                "SEARCH_BUSY",
                "SEARCH_INDEX_UNAVAILABLE",
                "SEARCH_INDEX_INCOMPATIBLE",
                "INVALID_SEARCH_PROFILE",
                "INVALID_SEARCH_CUTOFF",
                "INVALID_SEARCH_QUERY",
                "INVALID_SEARCH_SETTINGS",
                "SEARCH_INPUT_TOO_LONG",
            ]
            .contains(&error.code.as_str())
            {
                &error.code
            } else {
                "SEARCH_OPERATION_FAILED"
            };
            println!("{code}");
            Ok(2)
        }
    }
}
