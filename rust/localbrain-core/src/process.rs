use crate::{Error, Result};
use serde::Serialize;
use std::io::Read;
use std::process::{Command, ExitStatus, Stdio};
use std::time::{Duration, Instant};

pub fn run(command: &mut Command, timeout: Duration, limit: usize) -> Result<Vec<u8>> {
    let (status, bytes) = run_status(command, timeout, limit)?;
    if !status.success() {
        return Err(Error::unavailable());
    }
    Ok(bytes)
}
pub fn run_status(
    command: &mut Command,
    timeout: Duration,
    limit: usize,
) -> Result<(ExitStatus, Vec<u8>)> {
    let mut child = command
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|_| Error::unavailable())?;
    let mut stdout = child.stdout.take().ok_or_else(Error::unavailable)?;
    let mut stderr = child.stderr.take().ok_or_else(Error::unavailable)?;
    let output = std::thread::spawn(move || {
        let mut bytes = Vec::new();
        stdout
            .by_ref()
            .take(limit as u64 + 1)
            .read_to_end(&mut bytes)
            .map(|_| bytes)
    });
    let errors = std::thread::spawn(move || {
        let mut bytes = Vec::new();
        stderr
            .by_ref()
            .take(65537)
            .read_to_end(&mut bytes)
            .map(|_| bytes)
    });
    let deadline = Instant::now() + timeout;
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break Ok(status),
            Ok(None) if Instant::now() < deadline => std::thread::sleep(Duration::from_millis(5)),
            _ => {
                let _ = child.kill();
                let _ = child.wait();
                break Err(Error::unavailable());
            }
        }
    };
    let out = output
        .join()
        .map_err(|_| Error::unavailable())?
        .map_err(|_| Error::unavailable())?;
    let err = errors
        .join()
        .map_err(|_| Error::unavailable())?
        .map_err(|_| Error::unavailable())?;
    if out.len() > limit || err.len() > 65536 {
        return Err(Error::unavailable());
    }
    Ok((status?, out))
}
#[derive(Debug, Clone, Serialize)]
pub struct Record {
    pub pid: i32,
    pub parent: i32,
    pub group: i32,
    pub session: Option<i32>,
    pub born: String,
    pub dead: bool,
}
pub fn snapshot() -> Result<Vec<Record>> {
    let output = run(
        Command::new("/bin/ps")
            .args(["-axo", "pid=,ppid=,pgid=,lstart=,stat="])
            .env("LC_ALL", "C")
            .env("TZ", "UTC"),
        Duration::from_secs(2),
        8 * 1024 * 1024,
    )?;
    let text = std::str::from_utf8(&output).map_err(|_| Error::unavailable())?;
    let mut records = Vec::new();
    for line in text.lines() {
        let Some(mut record) = parse_row(line)? else {
            continue;
        };
        let session = unsafe { libc::getsid(record.pid) };
        let session = if session >= 0 {
            Some(session)
        } else {
            match std::io::Error::last_os_error().raw_os_error() {
                Some(libc::ESRCH) => continue,
                Some(libc::EPERM) => None,
                _ => return Err(Error::unavailable()),
            }
        };
        record.session = session;
        records.push(record);
    }
    Ok(records)
}

fn parse_row(line: &str) -> Result<Option<Record>> {
    let fields: Vec<_> = line.split_whitespace().collect();
    if fields.len() < 9 {
        return Ok(None);
    }
    let number = |index: usize| {
        fields[index]
            .parse::<i32>()
            .map_err(|_| Error::unavailable())
    };
    let pid = number(0)?;
    if pid <= 1 {
        return Ok(None);
    }
    Ok(Some(Record {
        pid,
        parent: number(1)?,
        group: number(2)?,
        session: None,
        born: fields[3..8].join(" "),
        dead: fields[8].contains('Z'),
    }))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn short_process_rows_are_skipped_but_numeric_corruption_fails() {
        assert!(parse_row("123 1").unwrap().is_none());
        assert!(parse_row("").unwrap().is_none());
        let row = parse_row("123 1 123 Thu Nov 12 15:42:08 2026 Z")
            .unwrap()
            .unwrap();
        assert_eq!(row.born, "Thu Nov 12 15:42:08 2026");
        assert!(row.dead);
        assert!(parse_row("123 invalid 123 Thu Nov 12 15:42:08 2026 Ss").is_err());
    }
}
