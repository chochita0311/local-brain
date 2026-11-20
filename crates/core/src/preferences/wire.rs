//! Framed local codec channel, independent of terminal manager transports.
use super::{execute, Codec, Fault, Result, Scope};
use crate::files::digest;
use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Read, Write};
use std::os::fd::FromRawFd;
use std::os::unix::fs::FileTypeExt;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};

const MAX_FRAME: usize = 128 * 1024;
const CHUNK: usize = 16 * 1024;
pub const OPERATIONS: [&str; 7] = [
    "common.defaults",
    "common.read",
    "common.preflight",
    "common.save",
    "terminal.read",
    "terminal.launch",
    "terminal.save",
];

pub fn exact(value: &Value, keys: &[&str]) -> Result<()> {
    let object = value.as_object().ok_or_else(Fault::protocol)?;
    if object.len() != keys.len() || object.keys().any(|key| !keys.contains(&key.as_str())) {
        return Err(Fault::protocol());
    }
    Ok(())
}

struct Channel {
    input: BufReader<std::io::Stdin>,
    output: std::io::Stdout,
    id: String,
    sequence: u64,
    cancelled: Arc<AtomicBool>,
}

impl Channel {
    fn read(&mut self) -> Result<Value> {
        let mut bytes = vec![];
        (&mut self.input)
            .take((MAX_FRAME + 1) as u64)
            .read_until(b'\n', &mut bytes)
            .map_err(|_| Fault::protocol())?;
        if bytes.len() > MAX_FRAME || bytes.last() != Some(&b'\n') {
            return Err(Fault::protocol());
        }
        let frame: Value = serde_json::from_slice(&bytes).map_err(|_| Fault::protocol())?;
        if frame.get("wire").and_then(Value::as_u64) != Some(1)
            || frame.get("id").and_then(Value::as_str) != Some(&self.id)
            || frame.get("type").and_then(Value::as_str).is_none()
        {
            return Err(Fault::protocol());
        }
        Ok(frame)
    }
    fn send(&mut self, mut frame: Value) -> Result<()> {
        frame["wire"] = json!(1);
        frame["id"] = json!(self.id);
        let mut bytes = serde_json::to_vec(&frame).map_err(|_| Fault::protocol())?;
        bytes.push(b'\n');
        if bytes.len() > MAX_FRAME {
            return Err(Fault::protocol());
        }
        self.output
            .write_all(&bytes)
            .and_then(|_| self.output.flush())
            .map_err(|_| Fault::protocol())
    }
    fn receive_stream(&mut self, name: &str) -> Result<Value> {
        let begin = self.read()?;
        exact(
            &begin,
            &["wire", "id", "type", "stream", "length", "encoding"],
        )?;
        if begin["type"] != "begin" || begin["stream"] != name || begin["encoding"] != "utf8" {
            return Err(Fault::protocol());
        }
        let length = begin["length"].as_u64().ok_or_else(Fault::protocol)?;
        let mut bytes = Vec::new();
        let mut sequence = 0;
        loop {
            let frame = self.read()?;
            if frame["stream"] != name {
                return Err(Fault::protocol());
            }
            if frame["type"] == "end" {
                exact(&frame, &["wire", "id", "type", "stream", "sha256"])?;
                if bytes.len() as u64 != length || frame["sha256"] != digest(&bytes) {
                    return Err(Fault::protocol());
                }
                return serde_json::from_slice(&bytes).map_err(|_| Fault::protocol());
            }
            exact(&frame, &["wire", "id", "type", "stream", "seq", "data"])?;
            let text = frame["data"].as_str().ok_or_else(Fault::protocol)?;
            if frame["type"] != "chunk"
                || frame["seq"].as_u64() != Some(sequence)
                || text.is_empty()
                || text.len() > CHUNK
                || (bytes.len() as u64).saturating_add(text.len() as u64) > length
            {
                return Err(Fault::protocol());
            }
            bytes.extend_from_slice(text.as_bytes());
            sequence += 1;
        }
    }
    fn send_stream(&mut self, name: &str, value: &Value) -> Result<()> {
        let text = serde_json::to_string(value).map_err(|_| Fault::protocol())?;
        self.send(json!({"type":"begin","stream":name,"length":text.len(),"encoding":"utf8"}))?;
        let mut begin = 0;
        let mut sequence = 0;
        while begin < text.len() {
            let mut end = (begin + CHUNK).min(text.len());
            while !text.is_char_boundary(end) {
                end -= 1;
            }
            self.send(
                json!({"type":"chunk","stream":name,"seq":sequence,"data":&text[begin..end]}),
            )?;
            begin = end;
            sequence += 1;
        }
        self.send(json!({"type":"end","stream":name,"sha256":digest(text.as_bytes())}))
    }
}

impl Codec for Channel {
    fn call(&mut self, operation: &str, value: Value) -> Result<Value> {
        let seq = self.sequence;
        self.sequence += 1;
        let input = format!("codec-{seq}-input");
        let output = format!("codec-{seq}-output");
        self.send(json!({"type":"codec","seq":seq,"operation":operation,"inputStream":input}))?;
        self.send_stream(&input, &value)?;
        let frame = self.read()?;
        exact(
            &frame,
            &["wire", "id", "type", "seq", "ok", "outputStream", "error"],
        )?;
        if frame["type"] != "codec-result" || frame["seq"].as_u64() != Some(seq) {
            return Err(Fault::protocol());
        }
        match frame["ok"].as_bool() {
            Some(true) if frame["outputStream"] == output && frame["error"].is_null() => {
                self.receive_stream(&output)
            }
            Some(false) if frame["outputStream"].is_null() => {
                Fault::parse(frame["error"].clone()).and_then(Err)
            }
            _ => Err(Fault::protocol()),
        }
    }
    fn cancelled(&self) -> bool {
        self.cancelled.load(Ordering::Acquire)
    }
}

pub fn serve(arguments: &[String]) -> Result<()> {
    if !(arguments.len() == 2 || arguments.len() == 4)
        || arguments[0] != "--parent-fd"
        || (arguments.len() == 4 && arguments[2] != "--lease-fd")
    {
        return Err(Fault::protocol());
    }
    let parent: i32 = arguments[1].parse().map_err(|_| Fault::protocol())?;
    let lease = if arguments.len() == 4 {
        Some(arguments[3].parse::<i32>().map_err(|_| Fault::protocol())?)
    } else {
        None
    };
    if parent <= 2 || lease.is_some_and(|fd| fd <= 2 || fd == parent) {
        return Err(Fault::protocol());
    }
    if unsafe { libc::fcntl(parent, libc::F_GETFD) } == -1 {
        return Err(Fault::protocol());
    }
    let mut pipe = unsafe { std::fs::File::from_raw_fd(parent) };
    if !pipe
        .metadata()
        .map_err(|_| Fault::protocol())?
        .file_type()
        .is_fifo()
        || unsafe { libc::fcntl(parent, libc::F_GETFL) } & libc::O_ACCMODE != libc::O_RDONLY
    {
        return Err(Fault::protocol());
    }
    let cancelled = Arc::new(AtomicBool::new(false));
    let flag = Arc::clone(&cancelled);
    std::thread::spawn(move || {
        // The fixed trusted argv transfers ownership of this inherited pipe end.
        let mut byte = [0];
        let _ = pipe.read(&mut byte);
        flag.store(true, Ordering::Release);
    });
    let mut channel = Channel {
        input: BufReader::new(std::io::stdin()),
        output: std::io::stdout(),
        id: String::new(),
        sequence: 0,
        cancelled,
    };
    // Read the first frame separately because it establishes the request identity.
    let mut bytes = vec![];
    (&mut channel.input)
        .take((MAX_FRAME + 1) as u64)
        .read_until(b'\n', &mut bytes)
        .map_err(|_| Fault::protocol())?;
    if bytes.len() > MAX_FRAME || bytes.last() != Some(&b'\n') {
        return Err(Fault::protocol());
    }
    let call: Value = serde_json::from_slice(&bytes).map_err(|_| Fault::protocol())?;
    exact(
        &call,
        &[
            "wire",
            "id",
            "type",
            "contract",
            "operation",
            "context",
            "argsStream",
        ],
    )?;
    let id = call["id"]
        .as_str()
        .filter(|s| !s.is_empty() && s.chars().count() <= 128)
        .ok_or_else(Fault::protocol)?;
    channel.id = id.into();
    let result = (|| {
        if call["wire"].as_u64() != Some(1)
            || call["contract"].as_u64() != Some(1)
            || call["type"] != "call"
            || call["argsStream"] != "arguments"
        {
            return Err(Fault::protocol());
        }
        let operation = call["operation"]
            .as_str()
            .filter(|s| OPERATIONS.contains(s))
            .ok_or_else(Fault::protocol)?;
        let scope = Scope::parse(call["context"].clone())?;
        let args = channel.receive_stream("arguments")?;
        let id = channel.id.clone();
        execute(&scope, operation, args, lease, &id, &mut channel)
    })();
    match result {
        Ok((value, committed)) => {
            channel.send(json!({"type":"result","resultStream":"result","commit":if committed {"published"} else {"none"}}))?;
            channel.send_stream("result", &value)
        }
        Err(error) => channel.send(json!({"type":"error","error":error})),
    }
}
