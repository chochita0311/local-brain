//! Settings semantics and normal publication. Syntax/platform callbacks have no write authority.
mod native;
mod native_toml;
mod values;
mod wire;
use crate::{files, settings, Context};
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::os::fd::{AsRawFd, BorrowedFd};
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::Path;
use values::Arena;

pub use native::{
    decode_toml_document, decode_toml_exchange, encode_toml_document, native_call,
    native_call_tagged, native_call_with_options, NativeOptions,
};
pub(crate) use native::{decode_toml_for_validation, toml_schema_version};
pub use wire::serve;
pub type Result<T> = std::result::Result<T, Fault>;
const KEYS: [&str; 7] = [
    "startup_screen",
    "timezone",
    "session_sync_enabled",
    "session_sync_minutes",
    "context_sync_enabled",
    "context_sync_minutes",
    "onboarding_completed",
];
const READ_ERROR: &str = "로컬 설정을 읽지 못했습니다. 기존 파일을 확인해 주세요.";
const CONFLICT: &str = "다른 창에서 설정이 변경되었습니다. 다시 불러온 뒤 저장해 주세요.";

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Fault {
    pub kind: String,
    pub code: String,
    pub message: String,
    pub errno: Option<i32>,
    pub commit: String,
}
impl Fault {
    fn new(kind: &str, code: &str, message: &str) -> Self {
        Self {
            kind: kind.into(),
            code: code.into(),
            message: message.into(),
            errno: None,
            commit: "not-started".into(),
        }
    }
    fn prefs(message: &str) -> Self {
        Self::new("preferences", "invalid", message)
    }
    fn protocol() -> Self {
        Self::new(
            "transport",
            "protocol",
            "설정 실행부의 응답을 확인할 수 없습니다.",
        )
    }
    fn io(error: std::io::Error) -> Self {
        let mut fault = Self::new("io", "io", "설정 파일을 저장하지 못했습니다.");
        fault.errno = error.raw_os_error();
        fault
    }
    fn parse(value: Value) -> Result<Self> {
        let fault: Self = serde_json::from_value(value).map_err(|_| Self::protocol())?;
        if !["preferences", "terminal", "transport", "io"].contains(&fault.kind.as_str())
            || !["not-started", "not-published", "unknown", "published"]
                .contains(&fault.commit.as_str())
        {
            return Err(Self::protocol());
        }
        Ok(fault)
    }
}
impl From<crate::Error> for Fault {
    fn from(error: crate::Error) -> Self {
        Self::new(error.kind, &error.code, &error.message)
    }
}
impl std::fmt::Display for Fault {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.message)
    }
}
impl std::error::Error for Fault {}

trait Codec {
    fn call(&mut self, operation: &str, value: Value) -> Result<Value>;
    fn cancelled(&self) -> bool;
}

struct Scope {
    context: Context,
    default_zone: Arena,
    host_package_root: Option<std::path::PathBuf>,
    host_data_dir: Option<std::path::PathBuf>,
}
impl Scope {
    fn parse(value: Value) -> Result<Self> {
        wire::exact(&value, &["dataDir", "cacheDir", "homeDir", "defaultZone"])?;
        let context: Context = serde_json::from_value(json!({"dataDir":value["dataDir"],"cacheDir":value["cacheDir"],"homeDir":value["homeDir"]})).map_err(|_| Fault::protocol())?;
        context.validate().map_err(Fault::from)?;
        Ok(Self {
            context,
            default_zone: Arena::parse(value["defaultZone"].clone())?,
            host_package_root: std::env::var_os("LOCALBRAIN_HOST_PACKAGE_ROOT").map(Into::into),
            host_data_dir: std::env::var_os("LOCALBRAIN_HOST_DATA_DIR").map(Into::into),
        })
    }
}

pub fn capabilities(build: &str) -> Value {
    json!({"contract":1,"codec":1,"build":build,"target":"aarch64-apple-darwin","minimumOs":"14.0","operations":wire::OPERATIONS})
}

fn zone_valid(arena: &Arena, id: usize, codec: &mut dyn Codec) -> Result<bool> {
    codec
        .call("timezone.valid", arena.exchange(id)?)?
        .as_bool()
        .ok_or_else(Fault::protocol)
}
fn defaults(scope: &Scope, codec: &mut dyn Codec) -> Result<Arena> {
    let zone =
        if scope.default_zone.kind(0) == "string" && zone_valid(&scope.default_zone, 0, codec)? {
            scope.default_zone.text(0).unwrap().to_owned()
        } else {
            "UTC".into()
        };
    let mut result = Arena::table();
    for (key, kind, value) in [
        ("startup_screen", "string", json!("sessions")),
        ("timezone", "string", json!(zone)),
        ("session_sync_enabled", "boolean", json!(true)),
        ("session_sync_minutes", "integer", json!("10")),
        ("context_sync_enabled", "boolean", json!(true)),
        ("context_sync_minutes", "integer", json!("30")),
        ("onboarding_completed", "boolean", json!(false)),
    ] {
        let id = result.add(kind, value);
        result.set(0, key, id)?;
    }
    Ok(result)
}
fn validate(values: &Arena, codec: &mut dyn Codec) -> Result<()> {
    let startup = values.text(values.require("startup_screen")?);
    if !startup.is_some_and(|s| ["sessions", "sessions-dashboard", "context"].contains(&s)) {
        return Err(Fault::prefs("시작 화면을 선택해 주세요."));
    }
    let zone = values.require("timezone")?;
    if !["string", "surrogate-string"].contains(&values.kind(zone)) {
        return Err(Fault::prefs("시간대는 IANA 이름으로 입력해 주세요."));
    }
    if !zone_valid(values, zone, codec)? {
        return Err(Fault::prefs(
            "올바른 시간대를 입력해 주세요. 예: Asia/Seoul",
        ));
    }
    for key in [
        "session_sync_enabled",
        "context_sync_enabled",
        "onboarding_completed",
    ] {
        if values.kind(values.require(key)?) != "boolean" {
            return Err(Fault::prefs("켜기/끄기 값을 확인해 주세요."));
        }
    }
    for key in ["session_sync_minutes", "context_sync_minutes"] {
        let id = values.require(key)?;
        if values.kind(id) != "integer"
            || !values
                .scalar(id)
                .as_i64()
                .is_some_and(|n| (10..=1440).contains(&n))
        {
            return Err(Fault::prefs(
                "동기화 간격은 10분부터 1,440분 사이의 정수로 입력해 주세요.",
            ));
        }
    }
    Ok(())
}
fn common_json(values: &Arena) -> Result<Value> {
    let mut result = Map::new();
    for key in KEYS {
        result.insert(key.into(), values.scalar(values.require(key)?));
    }
    Ok(Value::Object(result))
}

struct Snapshot {
    raw: Arena,
    common: Arena,
    revision: String,
}
fn read_current(scope: &Scope, codec: &mut dyn Codec) -> Result<Snapshot> {
    let path = scope.context.data_dir.join("settings.toml");
    let bytes = match fs::metadata(&path) {
        Ok(_) => fs::read(&path).map_err(|_| Fault::prefs(READ_ERROR))?,
        Err(error)
            if [
                Some(libc::ENOENT),
                Some(libc::ENOTDIR),
                Some(libc::EBADF),
                Some(libc::ELOOP),
            ]
            .contains(&error.raw_os_error()) =>
        {
            vec![]
        }
        Err(_) => return Err(Fault::prefs(READ_ERROR)),
    };
    let text = std::str::from_utf8(&bytes).map_err(|_| Fault::prefs(READ_ERROR))?;
    let raw = Arena::parse(codec.call("toml.decode", json!(text))?)?;
    if raw.kind(0) != "table"
        || !raw
            .get(0, "schema_version")
            .is_some_and(|id| raw.kind(id) == "integer" && raw.scalar(id) == 1)
    {
        return Err(Fault::prefs(
            "이 앱이 지원하지 않는 설정 버전입니다. 기존 파일을 보존합니다.",
        ));
    }
    let mut common = defaults(scope, codec)?;
    for key in KEYS {
        if let Some(id) = raw.get(0, key) {
            let new = common.import(&raw, id)?;
            common.set(0, key, new)?;
        }
    }
    validate(&common, codec)?;
    Ok(Snapshot {
        raw,
        common,
        revision: files::digest(&bytes),
    })
}
fn public(snapshot: &Snapshot, raw: bool) -> Result<Value> {
    let mut source = Map::new();
    for key in KEYS {
        source.insert(
            key.into(),
            json!(if snapshot.raw.get(0, key).is_some() {
                "saved"
            } else {
                "default"
            }),
        );
    }
    let values = common_json(&snapshot.common)?;
    let mut result =
        json!({"saved":values,"effective":values,"source":source,"revision":snapshot.revision});
    if raw {
        result["raw"] = snapshot.raw.exchange(0)?;
    }
    Ok(result)
}
fn preflight(args: &Arena) -> Result<()> {
    let changes = args.require("changes")?;
    if args.kind(changes) != "table"
        || args
            .entries(changes)?
            .iter()
            .any(|(key, _)| !KEYS.contains(&key.as_str()))
    {
        return Err(Fault::prefs("지원하지 않는 설정 항목입니다."));
    }
    Ok(())
}
fn revision(args: &Arena, current: &Snapshot) -> Result<()> {
    if args.text(args.require("revision")?) != Some(&current.revision) {
        return Err(Fault::prefs(CONFLICT));
    }
    Ok(())
}
fn terminal(
    scope: &Scope,
    snapshot: &Snapshot,
    operation: &str,
    args: &Arena,
    codec: &mut dyn Codec,
) -> Result<Value> {
    // Installation/original-path identity is supplied by the trusted host,
    // never settings arguments. Keep this after common/revision validation.
    if scope
        .host_package_root
        .as_ref()
        .is_some_and(|root| scope.context.data_dir.starts_with(root))
        || scope.host_data_dir.as_ref().is_some_and(|path| {
            fs::symlink_metadata(path).is_ok_and(|info| info.file_type().is_symlink())
        })
    {
        return Err(crate::Error::identity().into());
    }
    let raw = &snapshot.raw;
    let table = raw.get(0, "terminal");
    let mut section = json!({"kind":match table { None => "missing", Some(id) if raw.kind(id) == "table" => "table", _ => "invalid" }});
    for key in ["cwd", "shell"] {
        section[key] = match table.and_then(|id| raw.get(id, key)) {
            None => json!({"kind":"missing"}),
            Some(id) if raw.kind(id) == "string" => {
                json!({"kind":"string","value":raw.text(id).unwrap()})
            }
            Some(_) => json!({"kind":"invalid"}),
        };
    }
    let mut request = json!({"revision":snapshot.revision,"section":section});
    match operation {
        "terminal.launch" => {
            if let Some(id) = args.get(0, "cwdOverride") {
                request["cwdOverride"] = args.scalar(id);
            }
        }
        "terminal.save" => {
            request["cwd"] = args.scalar(args.require("cwd")?);
            request["shell"] = args.scalar(args.require("shell")?);
        }
        _ => {}
    }
    let control_operation = match operation {
        "terminal.launch" => "settings.launch",
        "terminal.save" => "settings.prepare",
        _ => "settings.read",
    };
    // Preserve the former control envelope's exact JSON syntax/size refusal,
    // including malformed proposed values, before terminal value validation.
    let mut legacy = Arena::from_json(json!({"wire":1,"id":"0".repeat(32),"context":{
            "dataDir":scope.context.data_dir,"cacheDir":scope.context.cache_dir,"homeDir":scope.context.home_dir},
        "operation":control_operation,"arguments":request}))?;
    legacy.reorder(0, &["wire", "id", "context", "operation", "arguments"])?;
    let context_id = legacy.require("context")?;
    legacy.reorder(context_id, &["dataDir", "cacheDir", "homeDir"])?;
    let arguments_id = legacy.require("arguments")?;
    legacy.reorder(arguments_id, &["revision", "section"])?;
    let section_id = legacy
        .get(arguments_id, "section")
        .ok_or_else(Fault::protocol)?;
    legacy.reorder(section_id, &["kind", "cwd", "shell"])?;
    let mut nonfinite = false;
    for key in ["cwd", "shell", "cwdOverride"] {
        if let Some(id) = args.get(0, key) {
            nonfinite |= args.has_nonfinite(id)?;
            let imported = legacy.import(args, id)?;
            legacy.set(arguments_id, key, imported)?;
        }
    }
    let length = codec
        .call("json.measure", legacy.exchange(0)?)?
        .as_u64()
        .ok_or_else(Fault::protocol)?;
    if length > crate::MAX_REQUEST as u64 {
        return Err(crate::Error::terminal("invalid", "요청이 너무 큽니다.").into());
    }
    if nonfinite {
        return Err(crate::Error::terminal(
            "protocol",
            "터미널 실행부의 응답 형식을 확인할 수 없습니다.",
        )
        .into());
    }
    settings::execute(
        &scope.context,
        match operation {
            "terminal.launch" => "settings.launch",
            "terminal.save" => "settings.prepare",
            _ => "settings.read",
        },
        &request,
    )
    .map_err(Fault::from)
}
fn terminal_read(scope: &Scope, codec: &mut dyn Codec, args: &Arena) -> Result<Value> {
    let current = read_current(scope, codec)?;
    let mut result = terminal(scope, &current, "terminal.read", args, codec)?;
    result["preferences"] = public(&current, false)?;
    Ok(result)
}

fn verify_lease(scope: &Scope, fd: Option<i32>) -> Result<()> {
    let fd = fd.filter(|fd| *fd > 2).ok_or_else(Fault::protocol)?;
    if unsafe { libc::fcntl(fd, libc::F_GETFL) } & libc::O_ACCMODE != libc::O_RDWR {
        return Err(Fault::protocol());
    }
    // Borrow, then duplicate the same open description; never reopen or unlock it.
    let file = File::from(
        unsafe { BorrowedFd::borrow_raw(fd) }
            .try_clone_to_owned()
            .map_err(|_| Fault::protocol())?,
    );
    let actual = file.metadata().map_err(|_| Fault::protocol())?;
    let expected = fs::symlink_metadata(scope.context.data_dir.join("operations.lock"))
        .map_err(|_| Fault::protocol())?;
    if !actual.is_file()
        || !expected.is_file()
        || actual.dev() != expected.dev()
        || actual.ino() != expected.ino()
        || actual.uid() != unsafe { libc::getuid() }
        || unsafe { libc::flock(file.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0
    {
        return Err(Fault::protocol());
    }
    Ok(())
}

struct Temporary {
    path: std::path::PathBuf,
    identity: (u64, u64),
}
impl Drop for Temporary {
    fn drop(&mut self) {
        if fs::symlink_metadata(&self.path)
            .is_ok_and(|m| m.is_file() && (m.dev(), m.ino()) == self.identity)
        {
            let _ = fs::remove_file(&self.path);
        }
    }
}
fn publish(
    path: &Path,
    text: &str,
    id: &str,
    codec: &dyn Codec,
    committed: &mut bool,
) -> Result<()> {
    let parent = path.parent().ok_or_else(Fault::protocol)?;
    fs::DirBuilder::new()
        .recursive(true)
        .mode(0o700)
        .create(parent)
        .map_err(Fault::io)?;
    if fs::symlink_metadata(path).is_ok_and(|m| m.file_type().is_symlink()) {
        return Err(Fault::prefs(
            "설정 파일의 심볼릭 링크는 저장 대상으로 사용할 수 없습니다.",
        ));
    }
    // Match the former eight-byte suffix budget, even near macOS PATH_MAX.
    let digest = files::digest(id.as_bytes());
    let number = u64::from_str_radix(&digest[..12], 16).map_err(|_| Fault::protocol())?;
    let alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    let suffix: String = (0..8)
        .map(|i| alphabet[((number >> (42 - i * 6)) & 63) as usize] as char)
        .collect();
    let temporary = parent.join(format!(".settings.toml-{suffix}"));
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(&temporary)
        .map_err(Fault::io)?;
    let info = file.metadata().map_err(Fault::io)?;
    let _guard = Temporary {
        path: temporary.clone(),
        identity: (info.dev(), info.ino()),
    };
    file.set_permissions(fs::Permissions::from_mode(0o600))
        .map_err(Fault::io)?;
    file.write_all(text.as_bytes())
        .and_then(|_| files::sync_posix(&file))
        .map_err(Fault::io)?;
    if codec.cancelled() {
        return Err(Fault::protocol());
    }
    fs::rename(&temporary, path).map_err(Fault::io)?;
    *committed = true;
    File::open(parent)
        .and_then(|file| files::sync_posix(&file))
        .map_err(Fault::io)
}

fn execute(
    scope: &Scope,
    operation: &str,
    input: Value,
    lease: Option<i32>,
    id: &str,
    codec: &mut dyn Codec,
) -> Result<(Value, bool)> {
    let args = Arena::parse(input)?;
    let (allowed, required): (&[&str], &[&str]) = match operation {
        "common.defaults" | "common.read" | "terminal.read" => (&[], &[]),
        "common.preflight" => (&["changes"], &["changes"]),
        "common.save" => (&["changes", "revision"], &["changes", "revision"]),
        "terminal.launch" => (&["cwdOverride"], &[]),
        "terminal.save" => (&["cwd", "shell", "revision"], &["cwd", "shell", "revision"]),
        _ => return Err(Fault::protocol()),
    };
    args.keys(allowed, required)?;
    let mut committed = false;
    let mutation = operation.ends_with(".save");
    let result = (|| {
        if codec.cancelled() {
            return Err(Fault::protocol());
        }
        if operation == "common.preflight" {
            if lease.is_some() {
                return Err(Fault::protocol());
            }
            preflight(&args)?;
            return Ok(json!({"valid":true}));
        }
        if mutation {
            verify_lease(scope, lease)?;
        } else if lease.is_some() {
            return Err(Fault::protocol());
        }
        match operation {
            "common.defaults" => common_json(&defaults(scope, codec)?),
            "common.read" => public(&read_current(scope, codec)?, true),
            "terminal.read" => terminal_read(scope, codec, &args),
            "terminal.launch" => {
                terminal(scope, &read_current(scope, codec)?, operation, &args, codec)
            }
            "common.save" | "terminal.save" => {
                if operation == "common.save" {
                    preflight(&args)?;
                }
                let mut current = read_current(scope, codec)?;
                revision(&args, &current)?;
                if operation == "common.save" {
                    for (key, child) in args.entries(args.require("changes")?)? {
                        let new = current.common.import(&args, child)?;
                        current.common.set(0, &key, new)?;
                    }
                    validate(&current.common, codec)?;
                    for key in KEYS {
                        let new = current
                            .raw
                            .import(&current.common, current.common.require(key)?)?;
                        current.raw.set(0, key, new)?;
                    }
                } else {
                    let prepared = terminal(scope, &current, operation, &args, codec)?;
                    let table = if let Some(table) = current.raw.get(0, "terminal") {
                        table
                    } else {
                        let table = current.raw.add("table", json!([]));
                        current.raw.set(0, "terminal", table)?;
                        table
                    };
                    for key in ["cwd", "shell"] {
                        let new = current.raw.add("string", prepared["patch"][key].clone());
                        current.raw.set(table, key, new)?;
                    }
                    if current.raw.get(0, "onboarding_completed").is_none() {
                        let new = current.raw.import(
                            &current.common,
                            current.common.require("onboarding_completed")?,
                        )?;
                        current.raw.set(0, "onboarding_completed", new)?;
                    }
                }
                current
                    .raw
                    .reorder(0, &["schema_version", "onboarding_completed"])?;
                let encoded = codec.call("toml.encode", current.raw.exchange(0)?)?;
                let text = encoded.as_str().ok_or_else(Fault::protocol)?;
                publish(
                    &scope.context.data_dir.join("settings.toml"),
                    text,
                    id,
                    codec,
                    &mut committed,
                )?;
                if operation == "common.save" {
                    Ok(json!({"committed":true}))
                } else {
                    terminal_read(scope, codec, &Arena::table())
                }
            }
            _ => Err(Fault::protocol()),
        }
    })();
    result.map(|value| (value, committed)).map_err(|mut error| {
        if committed {
            error.commit = "published".into();
        } else if mutation {
            error.commit = "not-published".into();
        }
        error
    })
}
