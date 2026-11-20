//! Native user commands share the same services as the HTTP host.
mod arguments;
mod model_registration;
mod search;
mod simulation;
mod storage;
mod terminal;
use arguments::{invalid, Arguments};
use localbrain_core::backend::{
    db,
    ingest::{self, ScanControl},
    integrations::ApplicationIngestion,
    learning, models, Config, Result,
};
use localbrain_models::{catalog::ModelKey, Cancellation};
use serde_json::{json, Value};
use std::{
    io::Read,
    sync::{atomic::Ordering, Arc, OnceLock},
};
pub type CommandResult = Result<i32>;
static INTERRUPT_TOKEN: OnceLock<Cancellation> = OnceLock::new();
extern "C" fn interrupt(_: libc::c_int) {
    // The CLI initializes the cell before installing the handler. Only the
    // nonblocking read and atomic store run here, using the same flag as the job.
    if let Some(token) = INTERRUPT_TOKEN.get() {
        token.store(true, Ordering::Release);
    }
}
pub(super) struct CancellationGuard {
    pub token: Cancellation,
    previous: libc::sigaction,
}
impl CancellationGuard {
    pub fn new() -> Result<Self> {
        let token = INTERRUPT_TOKEN
            .get_or_init(localbrain_models::cancellation)
            .clone();
        token.store(false, Ordering::Release);
        let mut previous = unsafe { std::mem::zeroed() };
        let mut action: libc::sigaction = unsafe { std::mem::zeroed() };
        action.sa_sigaction = interrupt as *const () as usize;
        unsafe {
            libc::sigemptyset(&mut action.sa_mask);
            if libc::sigaction(libc::SIGINT, &action, &mut previous) != 0 {
                return Err(std::io::Error::last_os_error().into());
            }
        }
        Ok(Self { token, previous })
    }
    pub fn interrupted(&self) -> bool {
        self.token.load(Ordering::Acquire)
    }
}
impl Drop for CancellationGuard {
    fn drop(&mut self) {
        unsafe {
            libc::sigaction(libc::SIGINT, &self.previous, std::ptr::null_mut());
        }
    }
}
fn print(value: &Value) {
    println!(
        "{}",
        serde_json::to_string_pretty(value).expect("JSON command result")
    );
}
fn model_key(key: &str) -> Result<ModelKey> {
    match key {
        "embedding" => Ok(ModelKey::Embedding),
        "4b" => Ok(ModelKey::Generation4b),
        "8b" => Ok(ModelKey::Generation8b),
        _ => Err(invalid("model must be embedding, 4b, or 8b")),
    }
}
fn models(config: &Config, raw: &[String]) -> CommandResult {
    if raw.first().is_some_and(|action| action == "registration") {
        return model_registration::run(config, &raw[1..]);
    }
    let args = Arguments::parse(raw, &["--offline"], &[])?;
    let action = args.positional(0)?;
    if action == "status" {
        args.count(1, 1)?;
        print(&models::model_status(config)?);
        return Ok(0);
    }
    args.count(2, 2)?;
    if !["install", "verify"].contains(&action) || (action == "verify" && args.flag("--offline")) {
        return Err(invalid("invalid model command"));
    }
    let key = model_key(args.positional(1)?)?;
    let cancel = CancellationGuard::new()?;
    let outcome = if action == "install" {
        models::install_model(
            config,
            key,
            args.flag("--offline"),
            None,
            None,
            &cancel.token,
            |_| {},
        )
    } else {
        models::verify_model(config, key, &cancel.token)
    };
    if cancel.interrupted() {
        println!("MODEL_INTERRUPTED");
        return Ok(130);
    }
    match outcome {
        Ok(_) => {
            println!(
                "{}",
                if action == "install" {
                    "MODEL_INSTALLED"
                } else {
                    "MODEL_VERIFIED"
                }
            );
            Ok(0)
        }
        Err(error) => {
            let code = if !error.code.is_empty()
                && error
                    .code
                    .bytes()
                    .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_')
            {
                error.code.as_str()
            } else {
                "MODEL_OPERATION_FAILED"
            };
            println!("{code}");
            Ok(2)
        }
    }
}
fn learning(config: &Config, raw: &[String]) -> CommandResult {
    let args = Arguments::parse(raw, &["--reviewed"], &[])?;
    args.count(2, 2)?;
    if args.positional(0)? != "import" || !args.flag("--reviewed") {
        return Err(invalid(
            "learning import requires a packet path and --reviewed",
        ));
    }
    let result = (|| -> Result<Value> {
        let mut content = vec![];
        std::fs::File::open(args.positional(1)?)?
            .take(2 * 1024 * 1024 + 1)
            .read_to_end(&mut content)?;
        if content.len() > 2 * 1024 * 1024 {
            return Err(localbrain_core::backend::BackendError::invalid(
                "learning",
                "패킷은 2 MiB 이하여야 합니다.",
            ));
        }
        let text = std::str::from_utf8(&content).map_err(|_| invalid("Packet is not UTF-8"))?;
        let packet = localbrain_core::backend::json::decode(text)?;
        learning::validate_packet(&packet, learning::today(&config.timezone_name)?)?;
        db::initialize(config)?;
        crate::state::immediate(config, |conn| {
            learning::import_packet(conn, &packet, &config.timezone_name)
        })
    })();
    match result {
        Ok(value) => {
            println!("{value}");
            Ok(0)
        }
        Err(error) => {
            println!(
                "{}",
                if error.code == "database" {
                    "수업을 저장하지 못했습니다. DB 상태를 확인한 뒤 같은 패킷으로 다시 시도해 주세요."
                } else if error.code == "learning" || error.code.starts_with("learning_") {
                    &error.message
                } else {
                    "패킷을 읽지 못했습니다. 파일과 JSON 형식을 확인해 주세요."
                }
            );
            Ok(2)
        }
    }
}
fn run(config: Config, raw: &[String], desktop: bool) -> CommandResult {
    if desktop {
        if !raw.is_empty() {
            return Err(invalid("unexpected desktop backend arguments"));
        }
        crate::host::serve(config, "127.0.0.1", 0, true, false)?;
        return Ok(0);
    }
    let Some(command) = raw.first().map(String::as_str) else {
        db::initialize(&config)?;
        println!("LocalBrain database initialized");
        return Ok(0);
    };
    let rest = &raw[1..];
    if raw
        .split(|arg| arg == "--")
        .next()
        .unwrap_or(&[])
        .iter()
        .any(|arg| ["--help", "-h"].contains(&arg.as_str()))
    {
        println!("{}", help(command));
        return Ok(0);
    }
    match command {
        "--version" | "-V" => {
            println!("LocalBrain 0.0.1");
            Ok(0)
        }
        "init" => {
            Arguments::parse(rest, &[], &[])?.count(0, 0)?;
            db::initialize(&config)?;
            println!("LocalBrain database initialized");
            Ok(0)
        }
        "serve" => {
            // Keep --access-log compatible with existing shell aliases; web
            // requests are visible by default, with an explicit quiet mode.
            let args = Arguments::parse(
                rest,
                &["--access-log", "--no-access-log"],
                &["--host", "--port"],
            )?;
            args.count(0, 0)?;
            let host = args.string("--host", "127.0.0.1");
            if !["127.0.0.1", "::1"].contains(&host.as_str()) {
                return Err(invalid("host must be 127.0.0.1 or ::1"));
            }
            let port = args.number::<u16>("--port", 8000)?;
            if port == 0 {
                return Err(invalid("port must be between 1 and 65535"));
            }
            crate::host::serve(config, &host, port, false, !args.flag("--no-access-log"))?;
            Ok(0)
        }
        "doctor" => {
            Arguments::parse(rest, &[], &[])?.count(0, 0)?;
            print(
                &json!({"platform":if cfg!(target_os="macos"){"Darwin"}else{std::env::consts::OS},"machine":if cfg!(target_arch="aarch64"){"arm64"}else{std::env::consts::ARCH},"backend":"rust","backend_version":env!("CARGO_PKG_VERSION"),"local_models":models::model_status(&config)?}),
            );
            Ok(0)
        }
        "models" => models(&config, rest),
        "learning" => learning(&config, rest),
        "terminal" => terminal::run(&config, rest),
        "storage" => storage::run(&config, rest),
        "search" => search::run(&config, rest),
        "simulate" if config.feature("auto_work") => simulation::run(&config, rest),
        "scan" => {
            let args = Arguments::parse(rest, &["--full"], &[])?;
            args.count(0, 0)?;
            let features = crate::state::FeatureBindings::for_config(&config)?;
            let observer =
                ApplicationIngestion::new(config.clone(), features.atlassian.into_iter().collect());
            let cancel = CancellationGuard::new()?;
            let token = cancel.token.clone();
            let control = ScanControl {
                cancelled: Some(Arc::new(move || token.load(Ordering::Acquire))),
                progress: None,
            };
            let scan = ingest::scan_all(&config, args.flag("--full"), &control, &observer);
            if cancel.interrupted() {
                eprintln!("스캔을 취소했습니다. 이미 완료한 소스의 기록은 유지됩니다.");
                return Ok(130);
            }
            let mut report = scan?;
            let refresh =
                localbrain_core::backend::search::refresh_after_scan(&config, &cancel.token);
            if cancel.interrupted() {
                eprintln!("검색 갱신을 취소했습니다. 가져온 기록은 유지됩니다.");
                return Ok(130);
            }
            match refresh {
                Ok(Some(refresh)) => report["natural_search"] = refresh,
                Ok(None) => {}
                Err(_) => {
                    report["natural_search"] =
                        json!({"state":"failed","error":"SEARCH_REFRESH_FAILED"})
                }
            }
            print(&report);
            Ok(0)
        }
        _ => Err(invalid("invalid command; use localbrain --help")),
    }
}
fn help(command: &str) -> &'static str {
    match command{
    "terminal"=>"usage: lb terminal {list,stop,service}\n  list [--json]\n  stop ID|--all [--json] [--yes] [--force]\n  service {install,status,start,stop,restart} [--json] [--yes] [--force]",
    "search"=>"usage: localbrain search {status,prepare,query}\n  prepare [--target 256|512|768] [--dimension 512|1024] [--overlap 0|64] [--cutoff N] [--device auto|mps|cpu] [--batch-size N] [--rebuild]\n  query TEXT [--mode dense|lexical|hybrid] [--cutoff N] [--limit N]",
    "learning"=>"usage: localbrain learning import PATH --reviewed",
    "models"=>"usage: localbrain models {status,install MODEL [--offline],verify MODEL}\n  MODEL: embedding, 4b, 8b\n  registration --root PATH [--verify] [--model Qwen/Qwen3-4B|Qwen/Qwen3-8B] [--xet-cache PATH]",
    "storage"=>"usage: localbrain storage {status,cleanup [--apply],migrate [--apply] [--include-development]}",
    "simulate"=>"usage: localbrain simulate [--database PATH] [--output PATH] [--inventory-only|--status|--purge] [--model-manifest PATH] [--device auto|cpu|mps|cuda] [--chunk-chars N] [--batch-size N] [--neighbors N] [--similarity N] [--area-resolution N] [--work-resolution N] [--force-reembed] [--show-counts]",
    _=>"usage: localbrain {init,serve,doctor,models,storage,scan,search,learning,terminal,simulate}\n  serve [--host 127.0.0.1|::1] [--port PORT] [--access-log|--no-access-log]\n  scan [--full]\n  --version"
}
}
fn entry_on_worker(desktop: bool) -> i32 {
    let args = match std::env::args_os()
        .skip(1)
        .map(|value| value.into_string())
        .collect::<std::result::Result<Vec<_>, _>>()
    {
        Ok(args) => args,
        Err(_) => {
            eprintln!("localbrain: error: arguments must be UTF-8");
            return 2;
        }
    };
    if args
        .first()
        .is_some_and(|arg| arg == "--install-search-model")
    {
        return models::download_worker();
    }
    if args.first().is_some_and(|arg| arg == "--auto-work-worker") {
        return localbrain_core::backend::auto_work::preview_worker();
    }
    if args
        .first()
        .is_some_and(|arg| arg == "--context-search-worker")
    {
        return localbrain_core::backend::context_search::context_search_worker();
    }
    if args.first().is_some_and(|arg| arg == "--schema-ddl") {
        return match db::effective_schema_sql() {
            Ok(sql) => {
                println!("{}", json!(sql));
                0
            }
            Err(_) => {
                eprintln!("SCHEMA_BUILD_FAILED");
                2
            }
        };
    }
    let mut config = match Config::from_env() {
        Ok(config) => config,
        Err(error) => {
            eprintln!("{}", error.message);
            return 2;
        }
    };
    if desktop {
        config.desktop = true;
        let features = config.feature_packages.clone();
        config = config
            .with_features(features)
            .expect("known desktop features");
    }
    match run(config, &args, desktop) {
        Ok(code) => code,
        Err(error) => {
            eprintln!(
                "{}",
                if error.code == "arguments" {
                    format!("localbrain: error: {}", error.message)
                } else if ["unavailable", "feature"].contains(&error.code.as_str()) {
                    error.message
                } else {
                    "LOCALBRAIN_OPERATION_FAILED".into()
                }
            );
            2
        }
    }
}
pub fn entry(desktop: bool) -> i32 {
    match localbrain_core::backend::worker_thread("localbrain-host")
        .spawn(move || entry_on_worker(desktop))
    {
        Ok(worker) => worker.join().unwrap_or(2),
        Err(_) => {
            eprintln!("LOCALBRAIN_STARTUP_FAILED");
            2
        }
    }
}
