use crate::{
    boolean, fields, files, payload, process, string, Context, Error, Result, MANAGER_PROTOCOL,
};
use serde_json::{json, Value};
use std::fs;
use std::io::{Read, Write};
use std::os::fd::FromRawFd;
use std::os::unix::fs::{FileTypeExt, MetadataExt};
use std::os::unix::net::UnixStream;
use std::os::unix::process::CommandExt;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

pub const MAX_FRAME: usize = 2 * 1024 * 1024;
#[derive(Clone)]
pub struct Service {
    pub context: Context,
    pub root: PathBuf,
    pub scope_hash: String,
    label: String,
}
impl Service {
    pub fn new(context: Context) -> Result<Self> {
        context.validate()?;
        files::private_location(&context.data_dir, &context.home_dir)?;
        files::private_location(&context.cache_dir, &context.home_dir)?;
        let short = files::digest(context.data_dir.to_string_lossy().as_bytes());
        let root = context.cache_dir.join(format!("terminal-{}", &short[..10]));
        files::location(&root)?;
        if root
            .join("control.sock")
            .as_os_str()
            .as_encoded_bytes()
            .len()
            >= 104
        {
            return Err(Error::terminal(
                "path_too_long",
                "캐시 경로가 너무 깁니다. 짧은 캐시 경로를 선택해 주세요.",
            ));
        }
        let label = format!(
            "dev.localbrain.terminal.{}",
            &files::digest(root.to_string_lossy().as_bytes())[..16]
        );
        let scope_hash = payload::scope(&context);
        let service = Self {
            context,
            root,
            scope_hash,
            label,
        };
        service.check_scope()?;
        Ok(service)
    }
    fn check_scope(&self) -> Result<()> {
        if let Some(value) = files::read_json(&self.root.join("scope.json"), 16384)? {
            if value
                != json!({"schema":1,"dataDir":self.context.data_dir,"cacheDir":self.context.cache_dir,"scopeHash":self.scope_hash})
            {
                return Err(Error::identity());
            }
        }
        Ok(())
    }
    pub fn connect(&self, timeout: Duration) -> Result<UnixStream> {
        let path = self.root.join("control.sock");
        let info = fs::symlink_metadata(&path).map_err(|_| Error::unavailable())?;
        if !info.file_type().is_socket() || info.uid() != files::uid() || info.mode() & 0o077 != 0 {
            return Err(Error::identity());
        }
        // std's UnixStream has no connect deadline. Nonblocking connect bounds a full backlog too.
        let fd = unsafe { libc::socket(libc::AF_UNIX, libc::SOCK_STREAM, 0) };
        if fd < 0 {
            return Err(Error::unavailable());
        }
        let stream = unsafe { UnixStream::from_raw_fd(fd) };
        if unsafe { libc::fcntl(fd, libc::F_SETFD, libc::FD_CLOEXEC) } < 0 {
            return Err(Error::unavailable());
        }
        stream
            .set_nonblocking(true)
            .map_err(|_| Error::unavailable())?;
        let mut address: libc::sockaddr_un = unsafe { std::mem::zeroed() };
        address.sun_family = libc::AF_UNIX as _;
        let bytes = path.as_os_str().as_encoded_bytes();
        for (slot, byte) in address.sun_path.iter_mut().zip(bytes) {
            *slot = *byte as _;
        }
        #[cfg(target_os = "macos")]
        {
            address.sun_len = std::mem::size_of::<libc::sockaddr_un>() as _;
        }
        let result = unsafe {
            libc::connect(
                fd,
                (&address as *const libc::sockaddr_un).cast(),
                std::mem::size_of_val(&address) as _,
            )
        };
        if result != 0 {
            let code = std::io::Error::last_os_error().raw_os_error();
            if !matches!(code, Some(libc::EINPROGRESS) | Some(libc::EAGAIN)) {
                return Err(Error::unavailable());
            }
            let mut poll = libc::pollfd {
                fd,
                events: libc::POLLOUT,
                revents: 0,
            };
            if unsafe {
                libc::poll(
                    &mut poll,
                    1,
                    timeout.as_millis().min(i32::MAX as u128) as i32,
                )
            } <= 0
            {
                return Err(Error::unavailable());
            }
            let mut error: libc::c_int = 0;
            let mut length = std::mem::size_of_val(&error) as libc::socklen_t;
            if unsafe {
                libc::getsockopt(
                    fd,
                    libc::SOL_SOCKET,
                    libc::SO_ERROR,
                    (&mut error as *mut libc::c_int).cast(),
                    &mut length,
                )
            } != 0
                || error != 0
            {
                return Err(Error::unavailable());
            }
        }
        stream
            .set_nonblocking(false)
            .map_err(|_| Error::unavailable())?;
        stream
            .set_read_timeout(Some(timeout))
            .and_then(|_| stream.set_write_timeout(Some(timeout)))
            .map_err(|_| Error::unavailable())?;
        Ok(stream)
    }
    pub fn rpc(
        &self,
        method: &str,
        params: &Value,
        generation: Option<&str>,
        timeout: Duration,
    ) -> Result<Value> {
        let mut connection = self.connect(timeout)?;
        self.exchange(&mut connection, method, params, generation)
    }
    pub fn exchange(
        &self,
        connection: &mut UnixStream,
        method: &str,
        params: &Value,
        generation: Option<&str>,
    ) -> Result<Value> {
        let mut request =
            serde_json::to_vec(&json!({"method":method,"params":params,"generation":generation}))
                .map_err(|_| Error::invalid())?;
        if request.len() > 256 * 1024 {
            return Err(Error::invalid());
        }
        request.push(b'\n');
        connection
            .write_all(&request)
            .map_err(|_| Error::unavailable())?;
        let mut bytes = Vec::new();
        let mut chunk = [0u8; 65536];
        loop {
            let count = connection
                .read(&mut chunk)
                .map_err(|_| Error::unavailable())?;
            if count == 0 {
                return Err(Error::terminal("disconnected", "서비스 연결이 끊겼습니다."));
            }
            bytes.extend_from_slice(&chunk[..count]);
            if bytes.len() > MAX_FRAME + 1 {
                return Err(Error::terminal("protocol", "서비스 응답이 너무 큽니다."));
            }
            if let Some(index) = bytes.iter().position(|b| *b == b'\n') {
                if index + 1 != bytes.len() {
                    return Err(Error::invalid());
                }
                break;
            }
        }
        let reply: Value = serde_json::from_slice(&bytes)
            .map_err(|_| Error::terminal("protocol", "서비스 응답을 확인할 수 없습니다."))?;
        match reply.get("ok").and_then(Value::as_bool) {
            Some(true) => reply.get("result").cloned().ok_or_else(Error::invalid),
            Some(false) => {
                let e = reply
                    .get("error")
                    .filter(|e| e.is_object())
                    .ok_or_else(Error::invalid)?;
                Err(Error::terminal(
                    e.get("code")
                        .and_then(Value::as_str)
                        .unwrap_or("runtime_error"),
                    e.get("message")
                        .and_then(Value::as_str)
                        .unwrap_or("터미널 요청 실패"),
                ))
            }
            None => Err(Error::terminal(
                "protocol",
                "서비스 응답을 확인할 수 없습니다.",
            )),
        }
    }
    fn identity(&self) -> Result<Option<Value>> {
        let Some(value) = files::read_json(&self.root.join("identity.json"), 4096)? else {
            return Ok(None);
        };
        fields(
            &value,
            &[
                "pid",
                "born",
                "birthFormat",
                "generation",
                "version",
                "build",
                "scopeHash",
                "helperProtocol",
                "checkpointVersion",
                "unicodeVersion",
            ],
        )?;
        if value
            .get("pid")
            .and_then(Value::as_i64)
            .is_none_or(|p| p < 2 || p > i32::MAX as i64)
            || value
                .get("generation")
                .and_then(Value::as_str)
                .is_none_or(|s| s.len() != 32 || !s.bytes().all(|c| c.is_ascii_hexdigit()))
            || value
                .get("build")
                .and_then(Value::as_str)
                .is_none_or(|s| !payload::hex_id(s))
        {
            return Err(Error::identity());
        }
        Ok(Some(value))
    }
    pub fn status(&self) -> Result<Value> {
        let source = payload::Payload::source()?;
        let selected = payload::selected(&self.root, &self.scope_hash)?;
        let installed = selected.is_some();
        let ready = source.is_some();
        let identity = self.identity()?;
        match self.rpc("status", &json!({}), None, Duration::from_secs(1)) {
            Ok(mut status) => {
                let id = identity.ok_or_else(Error::identity)?;
                if ["pid", "generation", "version", "build"]
                    .iter()
                    .any(|k| id.get(k) != status.get(k))
                {
                    return Err(Error::identity());
                }
                let version = status
                    .get("version")
                    .and_then(Value::as_u64)
                    .ok_or_else(Error::identity)?;
                let known = version == 1 || version == MANAGER_PROTOCOL;
                let mut compatible = false;
                if version == MANAGER_PROTOCOL {
                    for key in [
                        "scopeHash",
                        "helperProtocol",
                        "checkpointVersion",
                        "unicodeVersion",
                    ] {
                        if id.get(key) != status.get(key) {
                            return Err(Error::identity());
                        }
                    }
                    if id.get("scopeHash").and_then(Value::as_str) != Some(&self.scope_hash)
                        || id.get("helperProtocol").and_then(Value::as_u64) != Some(1)
                        || id.get("checkpointVersion").and_then(Value::as_str) != Some("xterm6-v3")
                        || id.get("unicodeVersion").and_then(Value::as_str) != Some("11")
                    {
                        return Err(Error::identity());
                    }
                    compatible = status["leaseHeld"] == true
                        && selected.as_ref().is_some_and(|p| {
                            status.get("build").and_then(Value::as_str)
                                == Some(p.manifest.payload_id.as_str())
                        })
                        && source.as_ref().is_none_or(|p| {
                            status.get("build").and_then(Value::as_str)
                                == Some(p.manifest.payload_id.as_str())
                        });
                }
                status["state"] = json!(if compatible {
                    "running"
                } else {
                    "incompatible"
                });
                status["installed"] = json!(installed);
                status["bundleReady"] = json!(ready);
                status["supported"] = json!(known);
                Ok(status)
            }
            Err(_) => {
                if self.launchd_job()?.is_some_and(|active| active) {
                    return Ok(
                        json!({"running":null,"state":"unknown","installed":installed,"bundleReady":ready,"supported":true}),
                    );
                }
                if let Some(id) = identity {
                    let pid = id["pid"].as_i64().ok_or_else(Error::identity)? as i32;
                    let table = process::snapshot()?;
                    let current = table.iter().find(|r| r.pid == pid);
                    let gone = current.is_none()
                        || current.is_some_and(|r| {
                            r.dead
                                || id.get("birthFormat").and_then(Value::as_str)
                                    == Some("utc-lstart-v1")
                                    && id
                                        .get("born")
                                        .and_then(Value::as_str)
                                        .is_some_and(|b| b != r.born)
                        });
                    if gone {
                        return Ok(
                            json!({"running":false,"state":"stopped","installed":installed,"bundleReady":ready,"supported":true,"unclean":true}),
                        );
                    }
                    Ok(
                        json!({"running":null,"state":"unknown","installed":installed,"bundleReady":ready,"supported":true}),
                    )
                } else if self.root.join("control.sock").exists() {
                    Ok(
                        json!({"running":null,"state":"unknown","installed":installed,"bundleReady":ready,"supported":true}),
                    )
                } else {
                    Ok(
                        json!({"running":false,"state":"stopped","installed":installed,"bundleReady":ready,"supported":true}),
                    )
                }
            }
        }
    }
    pub fn list(&self) -> Result<Value> {
        let status = self.status()?;
        if status["state"] == "stopped" {
            return Ok(
                json!({"running":false,"generation":null,"revision":0,"tabs":[],"terminals":[],"service":status}),
            );
        }
        if !matches!(status["state"].as_str(), Some("running" | "incompatible"))
            || status["supported"] != true
        {
            return Err(Error::unavailable());
        }
        let mut list = self.rpc(
            "list",
            &json!({}),
            status["generation"].as_str(),
            Duration::from_secs(8),
        )?;
        list["service"] = status;
        Ok(list)
    }
    pub fn dependencies(&self) -> Result<Value> {
        let bundle = payload::Payload::source()?.is_some();
        let installed = payload::selected(&self.root, &self.scope_hash)?.is_some();
        Ok(
            json!({"node":bundle||installed,"npm":bundle||installed,"installed":installed,"bundleReady":bundle,"supported":cfg!(target_os="macos")}),
        )
    }
    pub fn use_payload(&self) -> Result<Option<files::Lock>> {
        payload::selected(&self.root, &self.scope_hash)?
            .map(|p| payload::lease(&self.root, &p.manifest.payload_id, false, false))
            .transpose()
    }
    fn lock(&self) -> Result<files::Lock> {
        files::private_dir(&self.root)?;
        files::Lock::acquire(&self.root.join("control.lock"), true, true)
    }
    fn prepare(&self) -> Result<payload::Payload> {
        let source=payload::Payload::source()?.ok_or_else(||Error::terminal("setup_required","앱의 터미널 구성요소가 필요합니다. 개발 빌드에서는 터미널 runtime을 먼저 빌드해 주세요."))?;
        let payload = source.prepare(&self.root)?;
        files::private_dir(&self.root.join("leases"))?;
        let _lease = payload::lease(&self.root, &payload.manifest.payload_id, false, true)?;
        files::atomic_json(
            &self.root.join("scope.json"),
            &json!({"schema":1,"dataDir":self.context.data_dir,"cacheDir":self.context.cache_dir,"scopeHash":self.scope_hash}),
        )?;
        files::atomic_json(
            &self.root.join("selection.json"),
            &json!({"schema":1,"scopeHash":self.scope_hash,"payloadId":payload.manifest.payload_id}),
        )?;
        let quote = |s: &str| format!("'{}'", s.replace('\'', "'\"'\"'"));
        let launcher = format!(
            "#!/bin/sh\nunset LOCALBRAIN_TERMINAL_BUNDLE LOCALBRAIN_TERMINAL_RUNTIME\nexec {} manage {} \"$@\"\n",
            quote(
                &payload
                    .root
                    .join("bin/localbrain-runtime")
                    .to_string_lossy()
            ),
            quote(&self.root.to_string_lossy())
        );
        files::atomic_bytes(
            &self.root.join("localbrain-terminal"),
            launcher.as_bytes(),
            0o700,
        )?;
        Ok(payload)
    }
    fn save_loss(&self) -> Result<()> {
        if let Some(id) = self.identity()? {
            files::private_dir(&self.root.join("losses"))?;
            let build = id["build"].as_str().ok_or_else(Error::identity)?;
            let name = if id["version"] == 1 {
                format!("legacy-{build}")
            } else {
                build.into()
            };
            files::atomic_json(
                &self.root.join("losses").join(format!("{name}.json")),
                &json!({"schema":1,"scopeHash":self.scope_hash,"identity":id}),
            )?;
        }
        Ok(())
    }
    fn launcher(&self) -> Result<String> {
        match std::env::var("LOCALBRAIN_TERMINAL_LAUNCHER")
            .ok()
            .as_deref()
        {
            Some("process") => Ok("process".into()),
            Some("launchd") | None if cfg!(target_os = "macos") => Ok("launchd".into()),
            _ => Err(Error::terminal(
                "unsupported",
                "터미널은 macOS에서 사용할 수 있습니다.",
            )),
        }
    }
    fn bootout(&self) -> Result<()> {
        let target = format!("gui/{}/{}", files::uid(), self.label);
        let _ = process::run(
            Command::new("/bin/launchctl").args(["bootout", &target]),
            Duration::from_secs(5),
            65536,
        );
        Ok(())
    }
    fn launchd_job(&self) -> Result<Option<bool>> {
        if self.launcher()? != "launchd" {
            return Ok(None);
        }
        let target = format!("gui/{}/{}", files::uid(), self.label);
        let (status, bytes) = process::run_status(
            Command::new("/bin/launchctl").args(["print", &target]),
            Duration::from_secs(2),
            65536,
        )?;
        if status.code() == Some(113) {
            return Ok(None);
        }
        if !status.success() {
            return Err(Error::unavailable());
        }
        let text = std::str::from_utf8(&bytes).map_err(|_| Error::unavailable())?;
        let inactive = text
            .lines()
            .any(|line| matches!(line.trim(), "state = not running" | "state = exited"));
        let pid = text.lines().any(|line| line.trim().starts_with("pid = "));
        Ok(Some(!inactive || pid))
    }
    fn start_locked(&self, launch: Option<&Value>) -> Result<Value> {
        let status = self.status()?;
        if status["state"] == "running" {
            if status.get("stopping") == Some(&json!(true)) {
                return Err(Error::terminal("stopping", "서비스를 중지하고 있습니다."));
            }
            return Ok(status);
        }
        if status["running"] != false {
            return Err(Error::unavailable());
        }
        // This is the authoritative stopped branch under control.lock. A live
        // manager may have stopped after the caller's optimistic preflight.
        if let Some(arguments) = launch {
            self.validate_cold_launch(arguments)?;
        }
        if status["unclean"] == true {
            self.save_loss()?;
        }
        let payload = self.prepare()?;
        for name in ["identity.json", "control.sock"] {
            let path = self.root.join(name);
            if let Ok(info) = fs::symlink_metadata(&path) {
                if info.file_type().is_symlink()
                    || info.uid() != files::uid()
                    || !(info.is_file() || info.file_type().is_socket())
                {
                    return Err(Error::identity());
                }
                fs::remove_file(path).map_err(|_| Error::identity())?;
            }
        }
        let arguments: Vec<String> = [
            payload.root.join("bin/node"),
            payload.root.join("manager/manager.cjs"),
            self.root.clone(),
            payload.root.join("bin/localbrain-runtime"),
            payload.root.clone(),
        ]
        .iter()
        .map(|p| p.to_string_lossy().into_owned())
        .chain([self.scope_hash.clone()])
        .collect();
        let mut environment = serde_json::Map::new();
        for key in [
            "HOME", "PATH", "SHELL", "LANG", "LC_ALL", "LC_CTYPE", "ZDOTDIR", "TMPDIR",
        ] {
            if let Ok(value) = std::env::var(key) {
                environment.insert(key.into(), json!(value));
            }
        }
        environment.insert("HOME".into(), json!(self.context.home_dir));
        environment
            .entry("PATH")
            .or_insert(json!("/usr/bin:/bin:/usr/sbin:/sbin"));
        environment.entry("LANG").or_insert(json!("en_US.UTF-8"));
        if self.launcher()? == "launchd" {
            self.bootout()?;
            let escape = |text: &str| -> Result<String> {
                if text
                    .chars()
                    .any(|c| c < ' ' && !matches!(c, '\n' | '\t' | '\r'))
                {
                    return Err(Error::invalid());
                }
                Ok(text
                    .replace('&', "&amp;")
                    .replace('<', "&lt;")
                    .replace('>', "&gt;")
                    .replace('"', "&quot;"))
            };
            let mut plist=format!("<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"><plist version=\"1.0\"><dict><key>Label</key><string>{}</string><key>ProgramArguments</key><array>",escape(&self.label)?);
            for argument in &arguments {
                plist.push_str(&format!("<string>{}</string>", escape(argument)?));
            }
            plist.push_str("</array><key>EnvironmentVariables</key><dict>");
            for (key, value) in &environment {
                plist.push_str(&format!(
                    "<key>{}</key><string>{}</string>",
                    escape(key)?,
                    escape(value.as_str().ok_or_else(Error::invalid)?)?
                ));
            }
            plist.push_str("</dict><key>RunAtLoad</key><true/><key>KeepAlive</key><false/><key>StandardOutPath</key><string>/dev/null</string><key>StandardErrorPath</key><string>/dev/null</string><key>Umask</key><integer>63</integer></dict></plist>");
            let path = self
                .root
                .join(format!("launch-{}.plist", files::random_id()?));
            files::atomic_bytes(&path, plist.as_bytes(), 0o600)?;
            let result = process::run(
                Command::new("/bin/launchctl").args([
                    "bootstrap",
                    &format!("gui/{}", files::uid()),
                    &path.to_string_lossy(),
                ]),
                Duration::from_secs(10),
                65536,
            );
            let _ = files::owned_remove_file(&path);
            result.map_err(|_| {
                Error::terminal("start_failed", "백그라운드 서비스를 시작하지 못했습니다.")
            })?;
        } else {
            let mut command = Command::new(&arguments[0]);
            command
                .args(&arguments[1..])
                .env_clear()
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null());
            for (key, value) in &environment {
                command.env(key, value.as_str().ok_or_else(Error::invalid)?);
            }
            // setsid is async-signal-safe; controlled process mode is only selected by the test host.
            unsafe {
                command.pre_exec(|| {
                    if libc::setsid() < 0 {
                        Err(std::io::Error::last_os_error())
                    } else {
                        Ok(())
                    }
                });
            }
            let _child = command.spawn().map_err(|_| {
                Error::terminal("start_failed", "백그라운드 서비스를 시작하지 못했습니다.")
            })?;
        }
        let deadline = Instant::now() + Duration::from_secs(10);
        while Instant::now() < deadline {
            let state = self.status()?;
            if state["state"] == "running" {
                return Ok(state);
            }
            std::thread::sleep(Duration::from_millis(50));
        }
        Err(Error::terminal(
            "start_failed",
            "서비스의 시작을 확인하지 못했습니다.",
        ))
    }
    fn stop_locked(&self, force: bool, expected: Option<&Value>) -> Result<Value> {
        let status = self.status()?;
        if status["state"] == "stopped" {
            if status["unclean"] == true {
                return Err(Error::identity());
            }
            if let Some(e) = expected {
                validate_expected(e, &Value::Null, &[])?;
            }
            if self.launcher()? == "launchd" {
                self.bootout()?;
            }
            return Ok(json!({"stopped":true}));
        }
        if !matches!(status["state"].as_str(), Some("running" | "incompatible"))
            || status["supported"] != true
        {
            return Err(Error::unavailable());
        }
        let generation = status["generation"].as_str().ok_or_else(Error::identity)?;
        let list = self.rpc("list", &json!({}), Some(generation), Duration::from_secs(8))?;
        let ids = terminal_ids(&list)?;
        if let Some(e) = expected {
            validate_expected(e, &status["generation"], &ids)?;
        }
        let identity = self.identity()?.ok_or_else(Error::identity)?;
        if ["pid", "generation", "build"]
            .iter()
            .any(|k| identity.get(k) != status.get(k))
        {
            return Err(Error::identity());
        }
        let pid = identity["pid"].as_i64().ok_or_else(Error::identity)? as i32;
        let table = process::snapshot()?;
        if identity.get("birthFormat").and_then(Value::as_str) != Some("utc-lstart-v1")
            || !table.iter().any(|p| {
                p.pid == pid
                    && !p.dead
                    && Some(p.born.as_str()) == identity.get("born").and_then(Value::as_str)
            })
        {
            return Err(Error::identity());
        }
        self.rpc(
            "shutdown",
            &json!({"force":force,"expected":{"generation":generation,"terminals":ids}}),
            Some(generation),
            Duration::from_secs(12),
        )?;
        let deadline = Instant::now() + Duration::from_secs(5);
        while Instant::now() < deadline {
            let alive = unsafe { libc::kill(pid, 0) } == 0;
            let gone = if !alive {
                true
            } else if !self.root.join("control.sock").exists() {
                process::snapshot()?
                    .iter()
                    .find(|p| p.pid == pid)
                    .is_none_or(|p| {
                        p.dead
                            || Some(p.born.as_str()) != identity.get("born").and_then(Value::as_str)
                    })
            } else {
                false
            };
            if !self.root.join("control.sock").exists() && gone {
                if self.launcher()? == "launchd" {
                    self.bootout()?;
                }
                return Ok(json!({"stopped":true,"generation":generation}));
            }
            std::thread::sleep(Duration::from_millis(50));
        }
        Err(Error::terminal(
            "stop_failed",
            "서비스의 종료를 확인하지 못했습니다.",
        ))
    }
    pub fn execute(&self, operation: &str, args: &Value) -> Result<Value> {
        match operation {
            "service.status" => {
                fields(args, &[])?;
                self.status()
            }
            "terminal.list" => {
                fields(args, &[])?;
                self.list()
            }
            "service.dependencies" => {
                fields(args, &[])?;
                self.dependencies()
            }
            "service.install" | "service.start" => {
                fields(args, &[])?;
                let _lock = self.lock()?;
                if operation == "service.start" {
                    self.start_locked(None)
                } else {
                    if self.status()?["running"] != false {
                        return Err(Error::terminal("busy", "서비스를 중지한 뒤 설치해 주세요."));
                    }
                    self.prepare()?;
                    Ok(json!({"installed":true}))
                }
            }
            "service.stop" | "service.restart" => {
                fields(args, &["force", "expected"])?;
                let force = boolean(args, "force")?;
                let _lock = self.lock()?;
                let result = self.stop_locked(force, args.get("expected"))?;
                if operation == "service.restart" {
                    self.start_locked(None)
                } else {
                    Ok(result)
                }
            }
            "terminal.create" => {
                fields(
                    args,
                    &["key", "cwd", "shell", "cols", "rows", "tabId", "direction"],
                )?;
                if self.status()?["running"] == false {
                    self.validate_cold_launch(args)?;
                }
                let _lock = self.lock()?;
                let status = self.start_locked(Some(args))?;
                self.rpc(
                    "create",
                    args,
                    status["generation"].as_str(),
                    Duration::from_secs(8),
                )
            }
            "terminal.stop" => {
                fields(args, &["id", "all", "force", "expected"])?;
                self.known_rpc("stop", args, None)
            }
            "tab.action" => {
                fields(args, &["id", "action", "name", "expected", "force"])?;
                self.known_rpc("tab", args, None)
            }
            "manager.rpc" => {
                fields(args, &["method", "params", "generation"])?;
                let method = string(args, "method")?;
                if ![
                    "status", "list", "create", "tab", "stop", "claim", "read", "input", "binary",
                    "resize", "release", "shutdown",
                ]
                .contains(&method)
                {
                    return Err(Error::invalid());
                }
                let params = args
                    .get("params")
                    .filter(|p| p.is_object())
                    .ok_or_else(Error::invalid)?;
                self.known_rpc(
                    method,
                    params,
                    args.get("generation").and_then(Value::as_str),
                )
            }
            "runtime.retire" => {
                let preview = args
                    .get("preview")
                    .and_then(Value::as_bool)
                    .ok_or_else(Error::invalid)?;
                if !self.root.exists() {
                    return if preview {
                        Ok(json!({"state":"absent","receipt":null,"protected":[]}))
                    } else {
                        Err(Error::identity())
                    };
                }
                if files::read_json(&self.root.join("scope.json"), 16384)?.is_none() {
                    return Err(Error::identity());
                }
                let _lock = files::Lock::acquire(&self.root.join("control.lock"), true, false)?;
                let state = self.status()?;
                if state["state"] == "unknown" {
                    return Err(Error::unavailable());
                }
                if self.launchd_job()?.is_some() {
                    return Err(Error::terminal(
                        "busy",
                        "백그라운드 서비스를 명시적으로 중지한 뒤 정리해 주세요.",
                    ));
                }
                payload::retire(
                    &self.root,
                    &self.scope_hash,
                    args,
                    state["state"] == "stopped" && state["unclean"] != true,
                )
            }
            _ => Err(Error::invalid()),
        }
    }
    fn known_rpc(&self, method: &str, params: &Value, generation: Option<&str>) -> Result<Value> {
        if method == "stop" {
            validate_stop_targets(params)?;
        }
        let status = self.status()?;
        let known = status["version"] == 1 || status["version"] == MANAGER_PROTOCOL;
        let permitted = status["state"] == "running"
            || (status["state"] == "incompatible"
                && known
                && (matches!(method, "status" | "list" | "stop" | "shutdown")
                    || method == "tab" && params["action"] == "stop"));
        if !permitted || status["supported"] != true {
            return Err(Error::unavailable());
        }
        let _lease = self.use_payload()?;
        self.rpc(
            method,
            params,
            generation.or_else(|| status["generation"].as_str()),
            Duration::from_secs(if method == "status" {
                1
            } else if matches!(method, "read" | "shutdown") {
                12
            } else {
                8
            }),
        )
    }
    fn validate_cold_launch(&self, args: &Value) -> Result<()> {
        let key = string(args, "key")?;
        if !(16..=128).contains(&key.len())
            || !key.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
        {
            return Err(Error::invalid());
        }
        for (field, low, high) in [("cols", 10.0, 240.0), ("rows", 4.0, 80.0)] {
            if let Some(value) = args.get(field).filter(|v| !v.is_null()) {
                let number = value
                    .as_f64()
                    .filter(|n| n.is_finite() && n.fract() == 0.0 && *n >= low && *n <= high)
                    .ok_or_else(Error::invalid)?;
                let _ = number;
            }
        }
        // No tab can exist in a stopped generation. Keep Node's falsy defaults.
        if args
            .get("tabId")
            .is_some_and(|v| !v.is_null() && v != false && v != 0 && v != "")
        {
            return Err(Error::terminal("not_found", "탭을 찾을 수 없습니다."));
        }
        let cwd = match args.get("cwd") {
            None => "",
            Some(v) => v.as_str().ok_or_else(Error::invalid)?,
        };
        let shell = match args.get("shell") {
            None => "",
            Some(v) => v.as_str().ok_or_else(Error::invalid)?,
        };
        if [cwd, shell]
            .iter()
            .any(|s| s.encode_utf16().count() > 4096 || s.contains('\0'))
        {
            return Err(Error::invalid());
        }
        let folder = if cwd.is_empty() || cwd == "~" {
            self.context.home_dir.clone()
        } else if cwd.starts_with("~/") {
            PathBuf::from(format!("{}{}", self.context.home_dir.display(), &cwd[1..]))
        } else {
            let path = PathBuf::from(cwd);
            if path.is_absolute() {
                path
            } else {
                let base = if self.launcher()? == "launchd" {
                    PathBuf::from("/")
                } else {
                    std::env::current_dir().map_err(|_| Error::invalid())?
                };
                base.join(path)
            }
        };
        let shell = if shell.is_empty() {
            std::env::var("SHELL")
                .ok()
                .filter(|s| !s.is_empty())
                .unwrap_or_else(|| "/bin/zsh".into())
        } else {
            shell.into()
        };
        let mut normalized = PathBuf::from("/");
        for component in folder.components() {
            match component {
                std::path::Component::Normal(part) => normalized.push(part),
                std::path::Component::ParentDir => {
                    normalized.pop();
                }
                std::path::Component::RootDir | std::path::Component::CurDir => {}
                _ => return Err(Error::invalid()),
            }
        }
        if !files::accessible_directory(&normalized)
            || !files::absolute_executable(std::path::Path::new(&shell))
        {
            return Err(Error::terminal(
                "invalid",
                "작업 폴더와 셸 실행 파일을 확인해 주세요.",
            ));
        }
        Ok(())
    }
}
fn validate_stop_targets(params: &Value) -> Result<()> {
    fields(params, &["id", "all", "force", "expected"])?;
    boolean(params, "force")?;
    if boolean(params, "all")? {
        if params.get("id").is_some_and(|v| !v.is_null())
            || !params.get("expected").is_some_and(Value::is_object)
        {
            return Err(Error::invalid());
        }
    } else if params
        .get("id")
        .and_then(Value::as_str)
        .is_none_or(str::is_empty)
    {
        return Err(Error::invalid());
    }
    Ok(())
}
pub fn terminal_ids(list: &Value) -> Result<Vec<String>> {
    list.get("terminals")
        .and_then(Value::as_array)
        .ok_or_else(Error::identity)?
        .iter()
        .map(|t| {
            t.get("id")
                .and_then(Value::as_str)
                .map(str::to_owned)
                .ok_or_else(Error::identity)
        })
        .collect()
}
fn validate_expected(expected: &Value, generation: &Value, ids: &[String]) -> Result<()> {
    fields(expected, &["generation", "terminals"])?;
    if !expected
        .get("generation")
        .is_some_and(|v| v.is_null() || v.is_string())
    {
        return Err(Error::invalid());
    }
    let given = expected
        .get("terminals")
        .and_then(Value::as_array)
        .filter(|v| v.len() <= 32)
        .ok_or_else(Error::invalid)?;
    let values: Vec<_> = given
        .iter()
        .map(|v| {
            v.as_str()
                .filter(|s| !s.is_empty())
                .map(str::to_owned)
                .ok_or_else(Error::invalid)
        })
        .collect::<Result<_>>()?;
    let mut a = values.clone();
    a.sort();
    let mut b = ids.to_vec();
    b.sort();
    if values
        .iter()
        .collect::<std::collections::BTreeSet<_>>()
        .len()
        != values.len()
        || a != b
        || expected.get("generation") != Some(generation)
    {
        return Err(Error::terminal(
            "conflict",
            "실행 목록이 변경되었습니다. 범위를 다시 확인해 주세요.",
        ));
    }
    Ok(())
}
