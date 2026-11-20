use super::{
    common::*,
    graph,
    inventory::{self, EXTRACTION, OWNER},
    store::{record_failure, Store},
};
use crate::backend::{clock, db, models, Config, Result};
use localbrain_models::{
    catalog::ModelKey,
    embedding::{EncoderConfig, LocalEncoder},
    Cancellation,
};
use rusqlite::params;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
    sync::Mutex,
};
pub trait SimulationEncoder: Send + Sync {
    fn contract(&self) -> Value;
    fn encode(&self, texts: &[String], cancel: &Cancellation) -> Result<Vec<Vec<f64>>>;
}
pub struct NativeSimulationEncoder {
    model: Mutex<LocalEncoder>,
    contract: Value,
}
impl NativeSimulationEncoder {
    pub fn from_manifest(
        manifest: &Path,
        hub_cache: &Path,
        options: EncoderConfig,
        cancel: &Cancellation,
    ) -> Result<Self> {
        let verified = localbrain_models::assets::verify_manifest(
            manifest,
            hub_cache,
            ModelKey::Embedding,
            cancel,
        )
        .map_err(models::failure)?;
        let model = LocalEncoder::new(verified, options).map_err(models::failure)?;
        let contract = model.contract(false);
        Ok(Self {
            model: Mutex::new(model),
            contract,
        })
    }
    /// Public model assets are verified before a caller can read private input.
    pub fn new(config: &Config, options: EncoderConfig, cancel: &Cancellation) -> Result<Self> {
        let verified = models::verify_model(config, ModelKey::Embedding, cancel)?;
        let model = LocalEncoder::new(verified, options).map_err(models::failure)?;
        let contract = model.contract(false);
        Ok(Self {
            model: Mutex::new(model),
            contract,
        })
    }
}
impl SimulationEncoder for NativeSimulationEncoder {
    fn contract(&self) -> Value {
        self.contract.clone()
    }
    fn encode(&self, texts: &[String], cancel: &Cancellation) -> Result<Vec<Vec<f64>>> {
        self.model
            .lock()
            .unwrap()
            .encode_exhaustive(texts, cancel)
            .map_err(models::failure)
    }
}
#[derive(Clone)]
pub struct SimulationOptions {
    pub chunk_chars: usize,
    pub batch_size: usize,
    pub parameters: Value,
    pub force: bool,
    pub cancel: Cancellation,
}
impl Default for SimulationOptions {
    fn default() -> Self {
        Self {
            chunk_chars: 1800,
            batch_size: 16,
            parameters: json!({"neighbors":8,"similarity":0.65,"area_resolution":0.6,"work_resolution":1.2,"seed":0}),
            force: false,
            cancel: localbrain_models::cancellation(),
        }
    }
}
pub fn vector_bytes(values: &[f64], dimension: usize) -> Result<Vec<u8>> {
    require(
        values.len() == dimension && values.iter().all(|value| value.is_finite()),
        "INVALID_VECTOR",
    )?;
    let norm = values.iter().map(|value| value * value).sum::<f64>().sqrt();
    require(norm > 0.0 && norm.is_finite(), "INVALID_VECTOR")?;
    Ok(values
        .iter()
        .flat_map(|value| ((*value / norm) as f32).to_ne_bytes())
        .collect())
}
pub fn load_vector(raw: &[u8], dimension: usize) -> Result<Vec<f32>> {
    require(raw.len() == dimension * 4, "INVALID_VECTOR")?;
    let vector = raw
        .chunks_exact(4)
        .map(|bytes| f32::from_ne_bytes(bytes.try_into().unwrap()))
        .collect::<Vec<_>>();
    vector_bytes(
        &vector
            .iter()
            .map(|value| f64::from(*value))
            .collect::<Vec<_>>(),
        dimension,
    )?;
    Ok(vector)
}
pub fn describe_groups(grouping: &Value, chunks: &[Value], sessions: &[Value]) -> Value {
    let Some(areas) = grouping["areas"].as_array() else {
        return json!({});
    };
    let by_session = sessions
        .iter()
        .map(|value| (value["key"].as_str().unwrap(), value))
        .collect::<BTreeMap<_, _>>();
    let mut by_input: BTreeMap<&str, Vec<&Value>> = BTreeMap::new();
    for chunk in chunks {
        by_input
            .entry(chunk["input_hash"].as_str().unwrap())
            .or_default()
            .push(chunk);
    }
    let mut membership: BTreeMap<String, usize> = BTreeMap::new();
    let mut descriptions = Vec::new();
    for area in areas {
        let evidence = area["members"]
            .as_array()
            .unwrap()
            .iter()
            .flat_map(|node| by_input[node.as_str().unwrap()].iter().copied())
            .collect::<Vec<_>>();
        let related = evidence
            .iter()
            .map(|chunk| chunk["session_key"].as_str().unwrap())
            .collect::<BTreeSet<_>>();
        for key in &related {
            *membership.entry((*key).into()).or_default() += 1;
        }
        let representative = evidence
            .iter()
            .min_by_key(|chunk| {
                (
                    chunk["at"].as_str().unwrap_or_default(),
                    chunk["key"].as_str().unwrap(),
                )
            })
            .unwrap();
        descriptions.push(json!({"area_id":area["id"],"session_keys":related,"representative_title":by_session[representative["session_key"].as_str().unwrap()]["title"],"label_basis":"source-session-title-not-area-name","representative_chunk":representative["key"],"observed_dates":evidence.iter().filter_map(|chunk|chunk["at"].as_str()).collect::<BTreeSet<_>>(),"lifecycle":"unknown"}));
    }
    json!({"single_session_areas":descriptions.iter().filter(|area|area["session_keys"].as_array().unwrap().len()==1).count(),"cross_session_areas":descriptions.iter().filter(|area|area["session_keys"].as_array().unwrap().len()>1).count(),"sessions_in_multiple_areas":membership.values().filter(|count|**count>1).count(),"areas":descriptions})
}
pub fn simulate(
    config: &Config,
    output: &Path,
    encoder: &dyn SimulationEncoder,
    options: &SimulationOptions,
) -> Result<Value> {
    require(
        (1..=256).contains(&options.batch_size),
        "INVALID_BATCH_SIZE",
    )?;
    graph::validate_parameters(&options.parameters)?;
    check_cancel(&options.cancel)?;
    let contract = encoder.contract();
    let dimension = contract["dimension"]
        .as_u64()
        .ok_or_else(|| failure("INVALID_MODEL"))? as usize;
    require(dimension > 0 && dimension <= 16384, "INVALID_MODEL")?;
    let namespace = digest(&json!([contract, EXTRACTION, options.chunk_chars]));
    let store = Store::open(
        config,
        output,
        &config.database_path,
        false,
        chrono::Utc::now(),
    )?;
    let output = &store.folder;
    let connection = store.connection.as_ref().unwrap();
    let started = clock::isoformat(chrono::Utc::now());
    let mut progress = json!({"owner":OWNER,"state":"inventory","started_at":started,"namespace":namespace,"encoded":0,"quality":"unassessed"});
    atomic_json(&output.join("progress.json"), &progress)?;
    let staged: Result<_> = (|| {
        let manifest = inventory::sync_inventory(
            connection,
            &config.database_path,
            options.chunk_chars,
            &options.cancel,
        )?;
        check_cancel(&options.cancel)?;
        if options.force {
            connection.execute("DELETE FROM embeddings WHERE namespace=?", [&namespace])?;
        }
        {
            let mut statement =
                connection.prepare("SELECT input_hash,vector FROM embeddings WHERE namespace=?")?;
            let mut rows = statement.query([&namespace])?;
            while let Some(row) = rows.next()? {
                let key: String = row.get(0)?;
                let bytes: Vec<u8> = row.get(1)?;
                if load_vector(&bytes, dimension).is_err() {
                    connection.execute(
                        "DELETE FROM embeddings WHERE namespace=? AND input_hash=?",
                        params![namespace, key],
                    )?;
                }
            }
        }
        let total: i64 =
            connection.query_row("SELECT COUNT(DISTINCT input_hash) FROM chunks", [], |row| {
                row.get(0)
            })?;
        let cached: i64 = connection.query_row(
            "SELECT COUNT(*) FROM embeddings WHERE namespace=?",
            [&namespace],
            |row| row.get(0),
        )?;
        progress["state"] = "embedding".into();
        progress["manifest"] = manifest.clone();
        progress["total_vectors"] = total.into();
        progress["reused"] = cached.into();
        atomic_json(&output.join("progress.json"), &progress)?;
        let mut after = String::new();
        let mut encoded = 0usize;
        loop {
            check_cancel(&options.cancel)?;
            let rows=db::rows(connection,"SELECT * FROM chunks c WHERE NOT EXISTS (SELECT 1 FROM embeddings e WHERE e.namespace=? AND e.input_hash=c.input_hash) AND c.input_hash>? GROUP BY input_hash ORDER BY input_hash LIMIT ?",params![namespace,after,options.batch_size])?;
            if rows.is_empty() {
                break;
            }
            let values = encoder
                .encode(
                    &inventory::source_texts(&config.database_path, &rows)?,
                    &options.cancel,
                )
                .map_err(|error| {
                    if error.code == "MODEL_CANCELLED" {
                        failure("SIMULATION_INTERRUPTED")
                    } else {
                        error
                    }
                })?;
            check_cancel(&options.cancel)?;
            require(values.len() == rows.len(), "INVALID_VECTOR")?;
            let vectors = values
                .iter()
                .map(|vector| vector_bytes(vector, dimension))
                .collect::<Result<Vec<_>>>()?;
            connection.execute_batch("BEGIN IMMEDIATE")?;
            let insert: Result<()> = (|| {
                for (row, vector) in rows.iter().zip(vectors) {
                    connection.execute(
                        "INSERT INTO embeddings VALUES (?,?,?)",
                        params![namespace, row["input_hash"].as_str(), vector],
                    )?;
                }
                Ok(())
            })();
            if let Err(error) = insert {
                connection.execute_batch("ROLLBACK")?;
                return Err(error);
            }
            connection.execute_batch("COMMIT")?;
            encoded += rows.len();
            after = rows.last().unwrap()["input_hash"]
                .as_str()
                .unwrap()
                .to_owned();
            progress["encoded"] = encoded.into();
            progress["updated_at"] = clock::isoformat(chrono::Utc::now()).into();
            atomic_json(&output.join("progress.json"), &progress)?;
        }
        progress["state"] = "grouping".into();
        atomic_json(&output.join("progress.json"), &progress)?;
        let mut vectors = BTreeMap::new();
        {
            let mut statement = connection.prepare(
                "SELECT input_hash,vector FROM embeddings WHERE namespace=? ORDER BY input_hash",
            )?;
            let mut rows = statement.query([&namespace])?;
            while let Some(row) = rows.next()? {
                let key: String = row.get(0)?;
                let bytes: Vec<u8> = row.get(1)?;
                vectors.insert(key, load_vector(&bytes, dimension)?);
            }
        }
        check_cancel(&options.cancel)?;
        let grouping = graph::group_vectors(&vectors, &options.parameters)?;
        require(
            inventory::scan_inventory(
                &config.database_path,
                options.chunk_chars,
                Some(&options.cancel),
                |_, _| Ok(()),
            )? == manifest,
            "SOURCE_CHANGED",
        )?;
        let chunks = db::rows(connection, "SELECT * FROM chunks ORDER BY key", [])?;
        let sessions = db::rows(connection, "SELECT * FROM sessions ORDER BY key", [])?;
        let previous_path = output.join("report.json");
        let previous = if previous_path.exists() {
            Some(read_json(&previous_path, 128 * 1024 * 1024)?)
        } else {
            None
        };
        let configuration = digest(&json!([namespace, options.parameters, grouping["engine"]]));
        let report = json!({"owner":OWNER,"created_at":clock::isoformat(chrono::Utc::now()),"quality":"unassessed","manifest":manifest,"model":contract,"configuration":configuration,"namespace":namespace,"parameters":options.parameters,"processing_complete":true,"lineage_status":"not_inferred","sessions":sessions,"chunks":chunks,"inspection":describe_groups(&grouping,&chunks,&sessions),"grouping":grouping,"cache":{"reused":cached,"encoded":encoded,"total":total},"comparison":{"previous_available":previous.is_some(),"same_input":previous.as_ref().is_some_and(|old|old["manifest"]==manifest),"same_configuration":previous.as_ref().is_some_and(|old|old["configuration"]==configuration),"same_grouping":previous.as_ref().is_some_and(|old|old["grouping"]==grouping)}});
        let previous = if let Some(previous) = previous {
            require(previous["owner"] == OWNER, "UNOWNED_OUTPUT")?;
            Some(stage_json(&output.join("previous-report.json"), &previous)?)
        } else {
            None
        };
        let pending_report = stage_json(&previous_path, &report)?;
        Ok((report, pending_report, previous))
    })();
    let result = staged
        .map_err(|error| check_cancel(&options.cancel).err().unwrap_or(error))
        .and_then(|(report, pending_report, previous)| {
            // Both reports are staged. After this check, finish publication.
            check_cancel(&options.cancel)?;
            if let Some(previous) = previous {
                previous.publish()?;
            }
            pending_report.publish()?;
            connection.execute("DELETE FROM embeddings WHERE namespace<>?", [&namespace])?;
            connection.execute_batch("VACUUM")?;
            progress["state"] = "complete".into();
            progress["finished_at"] = clock::isoformat(chrono::Utc::now()).into();
            atomic_json(&output.join("progress.json"), &progress)?;
            Ok(report)
        });
    if let Err(error) = &result {
        record_failure(output, &mut progress, error)?;
    }
    result
}
