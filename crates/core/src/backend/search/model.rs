use super::{
    check_cancel, failure, index,
    molecules::{Profile, SearchTokenizer},
};
use crate::backend::{models, Config, Result};
use localbrain_models::{
    catalog::ModelKey,
    embedding::{DevicePreference, EncoderConfig, LocalEncoder},
    tokenizer::OfflineTokenizer,
    Cancellation,
};
use serde_json::Value;
use std::sync::{Arc, Condvar, Mutex};
pub trait Encoder: Send + Sync {
    fn contract(&self) -> Value;
    fn batch_size(&self) -> usize;
    fn tokenizer(&self, cancel: &Cancellation) -> Result<Arc<dyn SearchTokenizer>>;
    fn encode(&self, texts: &[String], query: bool, cancel: &Cancellation)
        -> Result<Vec<Vec<f32>>>;
}
struct Tokenizer(OfflineTokenizer);
impl SearchTokenizer for Tokenizer {
    fn count(&self, text: &str, special: bool) -> Result<usize> {
        Ok(self.0.encode(text, special).map_err(models::failure)?.len())
    }
    fn spans(&self, text: &str) -> Result<Vec<(usize, usize)>> {
        Ok(self
            .0
            .spans(text)
            .map_err(models::failure)?
            .into_iter()
            .map(|span| (span.start, span.end))
            .collect())
    }
}
#[derive(Default)]
struct Schedule {
    busy: bool,
    queries: usize,
}
struct Scheduler {
    state: Mutex<Schedule>,
    wake: Condvar,
}
struct Turn<'a>(&'a Scheduler);
impl Drop for Turn<'_> {
    fn drop(&mut self) {
        self.0
            .state
            .lock()
            .unwrap_or_else(|error| error.into_inner())
            .busy = false;
        self.0.wake.notify_all();
    }
}
pub struct NativeEncoder {
    model: Mutex<LocalEncoder>,
    splitter: Mutex<Option<Arc<dyn SearchTokenizer>>>,
    schedule: Scheduler,
    contract: Value,
    batch_size: usize,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) struct ExecutionOptions {
    pub device: DevicePreference,
    pub batch_size: usize,
}
impl NativeEncoder {
    pub fn new(config: &Config, profile: Profile, options: Option<EncoderConfig>) -> Result<Self> {
        Self::new_with_cancellation(config, profile, options, &localbrain_models::cancellation())
    }
    pub fn for_index(config: &Config, profile: Profile, cancel: &Cancellation) -> Result<Self> {
        check_cancel(cancel)?;
        Self::from_execution(config, profile, index::published_execution(config), cancel)
    }
    pub(super) fn from_execution(
        config: &Config,
        profile: Profile,
        execution: Option<ExecutionOptions>,
        cancel: &Cancellation,
    ) -> Result<Self> {
        let options = execution.map(|execution| EncoderConfig {
            device: execution.device,
            batch_size: execution.batch_size,
            ..EncoderConfig::default()
        });
        match Self::new_with_cancellation(config, profile, options.clone(), cancel) {
            // A different host may lack the old generation's device. The
            // full contract check refuses its vectors until they are rebuilt.
            Err(error) if error.code == "INVALID_DEVICE" && options.is_some() => {
                Self::new_with_cancellation(
                    config,
                    profile,
                    options.map(|options| EncoderConfig {
                        device: DevicePreference::Auto,
                        ..options
                    }),
                    cancel,
                )
            }
            result => result,
        }
    }
    pub fn new_with_cancellation(
        config: &Config,
        profile: Profile,
        options: Option<EncoderConfig>,
        cancel: &Cancellation,
    ) -> Result<Self> {
        check_cancel(cancel)?;
        profile.validate()?;
        let mut options = options.unwrap_or_else(|| EncoderConfig {
            batch_size: 8,
            ..EncoderConfig::default()
        });
        options.dimension = profile.dimension;
        options.max_tokens = 1024;
        options.batch_size = options.batch_size.max(1);
        let batch_size = options.batch_size;
        let verified =
            models::verify_model(config, ModelKey::Embedding, cancel).map_err(|error| {
                if error.code == "MODEL_CANCELLED" {
                    failure("SEARCH_INTERRUPTED")
                } else {
                    error
                }
            })?;
        check_cancel(cancel)?;
        let model = LocalEncoder::new(verified, options).map_err(models::failure)?;
        let mut contract = model.contract(true);
        for (key, value) in profile.index_contract().as_object().unwrap() {
            contract[key] = value.clone();
        }
        Ok(Self {
            model: Mutex::new(model),
            splitter: Mutex::new(None),
            schedule: Scheduler {
                state: Mutex::new(Schedule::default()),
                wake: Condvar::new(),
            },
            contract,
            batch_size,
        })
    }
    fn turn(&self, query: bool, cancel: &Cancellation) -> Result<Turn<'_>> {
        let mut state = self
            .schedule
            .state
            .lock()
            .unwrap_or_else(|error| error.into_inner());
        if query {
            state.queries += 1;
        }
        while state.busy || (!query && state.queries > 0) {
            if cancel.load(std::sync::atomic::Ordering::Acquire) {
                if query {
                    state.queries -= 1;
                }
                return Err(failure("SEARCH_INTERRUPTED"));
            }
            state = self
                .schedule
                .wake
                .wait_timeout(state, std::time::Duration::from_millis(50))
                .unwrap_or_else(|error| error.into_inner())
                .0;
        }
        if query {
            state.queries -= 1;
        }
        state.busy = true;
        Ok(Turn(&self.schedule))
    }
}
impl Encoder for NativeEncoder {
    fn contract(&self) -> Value {
        self.contract.clone()
    }
    fn batch_size(&self) -> usize {
        self.batch_size
    }
    fn tokenizer(&self, cancel: &Cancellation) -> Result<Arc<dyn SearchTokenizer>> {
        let _turn = self.turn(false, cancel)?;
        let mut splitter = self
            .splitter
            .lock()
            .unwrap_or_else(|error| error.into_inner());
        if splitter.is_none() {
            let mut model = self.model.lock().unwrap_or_else(|error| error.into_inner());
            let tokenizer = model.tokenizer(cancel).map_err(models::failure)?.clone();
            *splitter = Some(Arc::new(Tokenizer(tokenizer)));
        }
        Ok(splitter.as_ref().unwrap().clone())
    }
    fn encode(
        &self,
        texts: &[String],
        query: bool,
        cancel: &Cancellation,
    ) -> Result<Vec<Vec<f32>>> {
        let _turn = self.turn(query, cancel)?;
        self.model
            .lock()
            .unwrap_or_else(|error| error.into_inner())
            .encode_search(texts, query, cancel)
            .map_err(|error| {
                if error.code == "MODEL_CANCELLED" {
                    failure("SEARCH_INTERRUPTED")
                } else {
                    models::failure(error)
                }
            })
    }
}
