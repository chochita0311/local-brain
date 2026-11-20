use super::{
    check_cancel,
    conditions::{focus_query, interpret},
    digest, failure,
    index::{
        database_binding, file_stamp, folder, lexical_tokens, meta, open_index, FileStamp, OWNER,
    },
    model::Encoder,
    molecules::Profile,
    quote,
    source::{read_sources, Source},
    urlencode,
};
use crate::backend::{db, Config, Result};
use localbrain_models::Cancellation;
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
    time::Instant,
};
pub type DatabaseStamp = Vec<Option<FileStamp>>;

pub fn database_stamp(path: &Path) -> DatabaseStamp {
    [
        path.to_owned(),
        PathBuf::from(format!("{}-wal", path.display())),
    ]
    .iter()
    .map(|path| file_stamp(path))
    .collect()
}
#[derive(Default)]
struct State {
    stamp: Option<FileStamp>,
    source_stamp: Option<DatabaseStamp>,
    connection: Option<Connection>,
    metadata: Value,
    vectors: Vec<Vec<f32>>,
    ids: Vec<i64>,
    parent_keys: Vec<String>,
    body_hashes: Vec<String>,
    parents: BTreeMap<String, (String, Value)>,
    sources: BTreeMap<String, Source>,
    revisions: BTreeMap<String, String>,
    coverage: Value,
}
pub struct Retriever {
    config: Config,
    profile: Mutex<Profile>,
    encoder: Arc<dyn Encoder>,
    state: Mutex<State>,
}
impl Retriever {
    pub fn new(config: Config, profile: Profile, encoder: Arc<dyn Encoder>) -> Self {
        Self {
            config,
            profile: Mutex::new(profile),
            encoder,
            state: Mutex::new(State::default()),
        }
    }
    pub fn set_profile(&self, profile: Profile) {
        *self.profile.lock().unwrap_or_else(|e| e.into_inner()) = profile;
    }
    pub fn close(&self) {
        let mut state = self.state.lock().unwrap_or_else(|e| e.into_inner());
        state.connection = None;
        state.stamp = None;
    }
    fn load(&self, state: &mut State, profile: Profile) -> Result<()> {
        let path = folder(&self.config).join("index.sqlite3");
        let stamp = file_stamp(&path).ok_or_else(|| failure("SEARCH_INDEX_UNAVAILABLE"))?;
        if state.stamp == Some(stamp) {
            return Ok(());
        }
        let connection = open_index(&path)?;
        connection.execute_batch("BEGIN")?;
        let metadata = meta(&connection)?;
        let mut contract = self.encoder.contract();
        for (key, value) in profile.index_contract().as_object().unwrap() {
            contract[key] = value.clone();
        }
        let expected = digest(&contract)?;
        if metadata["owner"] != OWNER
            || metadata["complete"] != true
            || metadata["binding"] != database_binding(&self.config)?
            || metadata["identity"] != expected
        {
            return Err(failure("SEARCH_INDEX_INCOMPATIBLE"));
        }
        let mut vectors = Vec::new();
        let mut ids = Vec::new();
        let mut parents = Vec::new();
        let mut bodies = Vec::new();
        {
            let mut statement=connection.prepare("SELECT f.id,f.parent_key,f.body_hash,v.value FROM fragments f JOIN vectors v ON v.input_hash=f.input_hash ORDER BY f.id")?;
            let mut cursor = statement.query([])?;
            while let Some(row) = cursor.next()? {
                let bytes = row.get::<_, Vec<u8>>(3)?;
                if bytes.len() != profile.dimension * 4 {
                    return Err(failure("INVALID_SEARCH_VECTORS"));
                }
                let vector = bytes
                    .chunks_exact(4)
                    .map(|bytes| f32::from_le_bytes(bytes.try_into().unwrap()))
                    .collect::<Vec<_>>();
                let norm = vector.iter().map(|value| value * value).sum::<f32>().sqrt();
                if vector.iter().any(|value| !value.is_finite())
                    || !norm.is_finite()
                    || (norm - 1.0).abs() > 0.00011
                {
                    return Err(failure("INVALID_SEARCH_VECTORS"));
                }
                vectors.push(vector);
                ids.push(row.get(0)?);
                parents.push(row.get(1)?);
                bodies.push(row.get(2)?);
            }
        }
        let parent_data = db::rows(&connection, "SELECT * FROM parents", [])?
            .into_iter()
            .map(|row| {
                Ok((
                    row["key"]
                        .as_str()
                        .ok_or_else(|| failure("INVALID_SEARCH_INDEX"))?
                        .to_string(),
                    (
                        row["revision"]
                            .as_str()
                            .ok_or_else(|| failure("INVALID_SEARCH_INDEX"))?
                            .to_string(),
                        serde_json::from_str(
                            row["metadata"]
                                .as_str()
                                .ok_or_else(|| failure("INVALID_SEARCH_INDEX"))?,
                        )?,
                    ),
                ))
            })
            .collect::<Result<BTreeMap<_, _>>>()?;
        state.connection = Some(connection);
        state.stamp = Some(stamp);
        state.metadata = metadata;
        state.vectors = vectors;
        state.ids = ids;
        state.parent_keys = parents;
        state.body_hashes = bodies;
        state.parents = parent_data;
        Ok(())
    }
    fn current(&self, state: &mut State) -> Result<()> {
        let stamp = database_stamp(&self.config.database_path);
        if state.source_stamp.as_ref() != Some(&stamp) {
            let (sources, coverage) = read_sources(&self.config, None)?;
            state.revisions = sources
                .iter()
                .map(|source| Ok((source.key.clone(), source.revision()?)))
                .collect::<Result<_>>()?;
            state.sources = sources
                .into_iter()
                .map(|source| (source.key.clone(), source))
                .collect();
            state.coverage = coverage;
            state.source_stamp = Some(stamp);
        }
        Ok(())
    }
    pub fn search(
        &self,
        query: &str,
        mode: &str,
        cutoff: Option<f64>,
        page: usize,
        page_size: usize,
    ) -> Result<Value> {
        self.search_with_cancellation(
            query,
            mode,
            cutoff,
            page,
            page_size,
            &localbrain_models::cancellation(),
        )
    }
    pub fn search_with_cancellation(
        &self,
        query: &str,
        mode: &str,
        cutoff: Option<f64>,
        page: usize,
        page_size: usize,
        cancel: &Cancellation,
    ) -> Result<Value> {
        check_cancel(cancel)?;
        if !["dense", "lexical", "hybrid"].contains(&mode) {
            return Err(failure("INVALID_SEARCH_MODE"));
        }
        if query.chars().count() > 300 || page < 1 || !(1..=100).contains(&page_size) {
            return Err(failure("INVALID_SEARCH_QUERY"));
        }
        let profile = *self.profile.lock().unwrap_or_else(|e| e.into_inner());
        let cutoff = cutoff.unwrap_or(profile.cutoff);
        if !cutoff.is_finite() || !(0.0..=1.0).contains(&cutoff) {
            return Err(failure("INVALID_SEARCH_CUTOFF"));
        }
        let started = Instant::now();
        let mut state = self.state.lock().unwrap_or_else(|e| e.into_inner());
        self.load(&mut state, profile)?;
        check_cancel(cancel)?;
        self.current(&mut state)?;
        let conditions = interpret(query, &self.config.timezone_name, None)?;
        let mut valid = BTreeSet::new();
        for (key, (revision, data)) in &state.parents {
            check_cancel(cancel)?;
            if state.revisions.get(key) != Some(revision) || !conditions.matches(data) {
                continue;
            }
            if !conditions.exclude.is_empty() {
                let source = &state.sources[key];
                let text = crate::backend::unicode::casefold(&format!(
                    "{}\n{}",
                    source.title,
                    source
                        .blocks
                        .iter()
                        .map(|block| block["text"].as_str().unwrap_or(""))
                        .collect::<Vec<_>>()
                        .join("\n")
                ));
                if conditions
                    .exclude
                    .iter()
                    .any(|excluded| text.contains(&crate::backend::unicode::casefold(excluded)))
                {
                    continue;
                }
            }
            valid.insert(key.clone());
        }
        let indices = state
            .parent_keys
            .iter()
            .enumerate()
            .filter_map(|(index, key)| valid.contains(key).then_some(index))
            .collect::<Vec<_>>();
        let mut scores = vec![0_f32; state.ids.len()];
        let mut ranks = scores.clone();
        let mut views = vec![query.to_string()];
        let trimmed = query.trim_matches(crate::backend::unicode::python_space);
        if mode == "hybrid" && conditions.notices.is_empty() {
            let focused = focus_query(query);
            if focused != trimmed {
                views.push(focused);
            }
        }
        let encode_started = Instant::now();
        let encoded = mode != "lexical" && !indices.is_empty() && !trimmed.is_empty();
        if encoded {
            let mut vectors = self.encoder.encode(&views, true, cancel)?;
            check_cancel(cancel)?;
            if vectors.len() != views.len()
                || vectors.iter().any(|vector| {
                    vector.len() != profile.dimension
                        || vector.iter().any(|value| !value.is_finite())
                })
            {
                return Err(failure("INVALID_SEARCH_VECTORS"));
            }
            for vector in &mut vectors {
                let norm = vector.iter().map(|value| value * value).sum::<f32>().sqrt();
                if !norm.is_finite() || norm <= 0.0 {
                    return Err(failure("INVALID_SEARCH_VECTORS"));
                }
                for value in vector {
                    *value /= norm;
                }
            }
            for index in &indices {
                check_cancel(cancel)?;
                let similarities = vectors
                    .iter()
                    .map(|query| {
                        state.vectors[*index]
                            .iter()
                            .zip(query)
                            .map(|(left, right)| left * right)
                            .sum::<f32>()
                    })
                    .collect::<Vec<_>>();
                scores[*index] = similarities
                    .iter()
                    .copied()
                    .fold(f32::NEG_INFINITY, f32::max);
                ranks[*index] = similarities.iter().sum::<f32>() / similarities.len() as f32;
            }
        }
        let encoded_at = Instant::now();
        let exact = if !trimmed.is_empty()
            && trimmed
                .bytes()
                .all(|ch| ch.is_ascii_alphanumeric() || b"_./:+-".contains(&ch))
            && query.bytes().any(|ch| ch.is_ascii_alphabetic())
        {
            crate::backend::unicode::casefold(trimmed)
        } else {
            String::new()
        };
        let mut lexical = BTreeMap::new();
        if mode == "lexical" || (mode == "hybrid" && !exact.is_empty()) {
            let mut seen = BTreeSet::new();
            let words = lexical_tokens(query)
                .into_iter()
                .filter(|word| seen.insert(word.clone()))
                .collect::<Vec<_>>();
            let expression = words
                .iter()
                .map(|word| format!("\"{}\"", word.replace('"', "\"\"")))
                .collect::<Vec<_>>()
                .join(" OR ");
            if !expression.is_empty() && !valid.is_empty() {
                let rows=db::rows(state.connection.as_ref().unwrap(),"SELECT terms.rowid,bm25(terms) AS score FROM terms JOIN fragments f ON f.id=terms.rowid WHERE terms MATCH ? AND f.parent_key IN (SELECT value FROM json_each(?)) ORDER BY score,terms.rowid LIMIT 500",params![expression,serde_json::to_string(&valid)?])?;
                for (rank, row) in rows.iter().enumerate() {
                    lexical.insert(row["rowid"].as_i64().unwrap(), rank + 1);
                }
            }
        }
        let mut admitted = Vec::new();
        for index in indices {
            check_cancel(cancel)?;
            let rowid = state.ids[index];
            let lexical_rank = lexical.get(&rowid);
            if mode == "lexical" {
                if let Some(rank) = lexical_rank {
                    admitted.push((1.0 / (60.0 + *rank as f64), index, "lexical"));
                }
                continue;
            }
            let mut reason = "semantic";
            if (scores[index] as f64) < cutoff {
                if mode != "hybrid" || exact.is_empty() || lexical_rank.is_none() {
                    continue;
                }
                let row = db::row(
                    state.connection.as_ref().unwrap(),
                    "SELECT text,context FROM fragments WHERE id=?",
                    [rowid],
                )?
                .ok_or_else(|| failure("SEARCH_INDEX_UNAVAILABLE"))?;
                let text = crate::backend::unicode::casefold(&format!(
                    "{}\n{}",
                    row["context"].as_str().unwrap(),
                    row["text"].as_str().unwrap()
                ));
                if !word_match(&text, &exact) {
                    continue;
                }
                reason = "exact";
            }
            admitted.push((ranks[index] as f64, index, reason));
        }
        admitted.sort_by(|left, right| {
            right
                .0
                .total_cmp(&left.0)
                .then_with(|| state.parent_keys[left.1].cmp(&state.parent_keys[right.1]))
                .then_with(|| state.ids[left.1].cmp(&state.ids[right.1]))
        });
        let mut groups: Vec<(String, Value, Vec<i64>, BTreeSet<String>)> = Vec::new();
        let mut group_indices = BTreeMap::new();
        for (rank, index, reason) in admitted {
            let key = &state.parent_keys[index];
            let group = if let Some(index) = group_indices.get(key) {
                *index
            } else {
                let mut value = state.parents[key].1.clone();
                value["score"] = round(scores[index] as f64, 5).into();
                value["rank_score"] = rank.into();
                value["match_reason"] = reason.into();
                groups.push((key.clone(), value, Vec::new(), BTreeSet::new()));
                let index = groups.len() - 1;
                group_indices.insert(key.clone(), index);
                index
            };
            if groups[group].2.len() < 3 && groups[group].3.insert(state.body_hashes[index].clone())
            {
                groups[group].2.push(state.ids[index]);
            }
        }
        let total = groups.len();
        let offset = (page - 1)
            .checked_mul(page_size)
            .ok_or_else(|| failure("INVALID_SEARCH_QUERY"))?;
        let return_url = format!(
            "/natural-search?{}",
            urlencode(&[("q", query.into()), ("page", page.to_string())])
        );
        let mut results = Vec::new();
        for (_, mut item, ids, _) in groups.into_iter().skip(offset).take(page_size) {
            check_cancel(cancel)?;
            let mut evidence = Vec::new();
            let entity = item["entity_id"]
                .as_i64()
                .map(|id| id.to_string())
                .unwrap_or_else(|| item["entity_id"].as_str().unwrap_or("").to_string());
            let anchor = format!("natural-result-{}-{entity}", item["kind"].as_str().unwrap());
            let result_return = format!("{return_url}#{anchor}");
            for rowid in ids {
                let row = db::row(
                    state.connection.as_ref().unwrap(),
                    "SELECT * FROM fragments WHERE id=?",
                    [rowid],
                )?
                .ok_or_else(|| failure("SEARCH_INDEX_UNAVAILABLE"))?;
                let locator: Value = serde_json::from_str(row["locator"].as_str().unwrap())?;
                let block = locator["block_id"]
                    .as_str()
                    .map(str::to_owned)
                    .unwrap_or_else(|| locator["block_id"].to_string());
                let href = if item["kind"] == "session" {
                    format!(
                        "/sessions/{entity}?{}#event-{}",
                        urlencode(&[("search_return", result_return.clone())]),
                        quote(&block)
                    )
                } else {
                    format!(
                        "/natural-search/evidence/{rowid}?{}",
                        urlencode(&[
                            (
                                "generation",
                                state.metadata["generation"].as_str().unwrap_or("").into()
                            ),
                            ("return_to", result_return.clone())
                        ])
                    )
                };
                evidence.push(json!({"id":rowid,"text":row["text"],"locator":locator,"generation":state.metadata["generation"],"href":href}));
            }
            item["href"] = evidence
                .first()
                .map(|value| value["href"].clone())
                .unwrap_or(Value::Null);
            item["anchor"] = anchor.into();
            item["evidence"] = evidence.into();
            results.push(item);
        }
        let current = state
            .parents
            .iter()
            .filter(|(key, (revision, _))| state.revisions.get(*key) == Some(revision))
            .count();
        let mut coverage = state.coverage.clone();
        coverage["indexed_parents"] = current.into();
        coverage["fragments"] = state.ids.len().into();
        Ok(
            json!({"results":results,"total":total,"page":page,"page_size":page_size,"conditions":conditions,"mode":mode,"cutoff":cutoff,"ranking":if mode=="lexical"{"lexical-bm25-v1"}else if mode=="dense"{"semantic-cosine-v2"}else{"semantic-dual-view-v3"},"coverage":coverage,"partial":current!=state.sources.len(),"timing":{"query_views":if encoded{views.len()}else{0},"query_encode_and_dot_ms":round((encoded_at-encode_started).as_secs_f64()*1000.0,2),"total_ms":round(started.elapsed().as_secs_f64()*1000.0,2)}}),
        )
    }
    pub fn evidence(&self, rowid: i64, generation: &str) -> Result<Value> {
        let profile = *self.profile.lock().unwrap_or_else(|e| e.into_inner());
        let mut state = self.state.lock().unwrap_or_else(|e| e.into_inner());
        self.load(&mut state, profile)?;
        self.current(&mut state)?;
        if state.metadata["generation"] != generation {
            return Err(failure("SEARCH_EVIDENCE_CHANGED"));
        }
        let row = db::row(
            state.connection.as_ref().unwrap(),
            "SELECT * FROM fragments WHERE id=?",
            [rowid],
        )?
        .ok_or_else(|| failure("SEARCH_EVIDENCE_CHANGED"))?;
        let key = row["parent_key"].as_str().unwrap();
        let parent = state
            .parents
            .get(key)
            .ok_or_else(|| failure("SEARCH_EVIDENCE_CHANGED"))?;
        if state.revisions.get(key) != Some(&parent.0) {
            return Err(failure("SEARCH_EVIDENCE_CHANGED"));
        }
        Ok(
            json!({"source":parent.1,"text":row["text"],"context":row["context"],"locator":serde_json::from_str::<Value>(row["locator"].as_str().unwrap())?}),
        )
    }
}
fn word_match(text: &str, word: &str) -> bool {
    let word_char = |ch: char| crate::backend::unicode::python_alnum(ch) || ch == '_';
    text.match_indices(word).any(|(start, _)| {
        !text[..start].chars().next_back().is_some_and(word_char)
            && !text[start + word.len()..]
                .chars()
                .next()
                .is_some_and(word_char)
    })
}
fn round(value: f64, places: i32) -> f64 {
    let scale = 10_f64.powi(places);
    (value * scale).round_ties_even() / scale
}
