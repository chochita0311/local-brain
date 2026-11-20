use localbrain_core::{
    files, payload, process, service::Service, stream::Lines, Context, Request, MAX_REPLY,
};
use serde_json::{json, Value};
use std::io::{IsTerminal, Read, Write};
use std::path::PathBuf;
use std::sync::atomic::AtomicBool;

fn manage(root: PathBuf, args: Vec<String>) -> Result<i32, Box<dyn std::error::Error>> {
    let json_output = args.iter().any(|a| a == "--json");
    if args.iter().any(|a| a == "--help" || a == "-h") {
        println!("사용법: localbrain-terminal list | stop ID/--all | service status/start/stop/restart/install [--json] [--yes] [--force]");
        return Ok(0);
    }
    match manage_inner(root, args) {
        Ok(code) => Ok(code),
        Err(error) => {
            let (code, message) = error
                .downcast_ref::<localbrain_core::Error>()
                .map(|e| (e.code.as_str(), e.message.as_str()))
                .unwrap_or(("runtime_error", "터미널 작업을 완료하지 못했습니다."));
            if json_output {
                eprintln!("{}", json!({"error":{"code":code,"message":message}}));
            } else {
                eprintln!("{message}");
            }
            Ok(1)
        }
    }
}
fn manage_inner(root: PathBuf, mut args: Vec<String>) -> Result<i32, Box<dyn std::error::Error>> {
    files::location(&root)?;
    let scope = files::read_json(&root.join("scope.json"), 16384)?
        .ok_or_else(localbrain_core::Error::identity)?;
    let data = scope["dataDir"]
        .as_str()
        .ok_or_else(localbrain_core::Error::identity)?;
    let cache = scope["cacheDir"]
        .as_str()
        .ok_or_else(localbrain_core::Error::identity)?;
    let context = Context {
        data_dir: data.into(),
        cache_dir: cache.into(),
        home_dir: std::env::var_os("HOME")
            .map(PathBuf::from)
            .ok_or_else(localbrain_core::Error::identity)?,
    };
    let service = Service::new(context)?;
    if service.root != root {
        return Err(localbrain_core::Error::identity().into());
    }
    let mut json_output = false;
    let mut yes = false;
    let mut force = false;
    args.retain(|a| match a.as_str() {
        "--json" => {
            json_output = true;
            false
        }
        "--yes" => {
            yes = true;
            false
        }
        "--force" => {
            force = true;
            false
        }
        _ => true,
    });
    let parsed = match args
        .iter()
        .map(String::as_str)
        .collect::<Vec<_>>()
        .as_slice()
    {
        ["list"] => Some(("terminal.list", json!({}), false)),
        ["stop", "--all"] => Some(("terminal.stop", json!({"all":true,"force":force}), true)),
        ["stop", id] if !id.starts_with('-') => Some((
            "terminal.stop",
            json!({"id":id,"all":false,"force":force}),
            false,
        )),
        ["service", action]
            if ["status", "install", "start", "stop", "restart"].contains(action) =>
        {
            Some((
                match *action {
                    "status" => "service.status",
                    "install" => "service.install",
                    "start" => "service.start",
                    "stop" => "service.stop",
                    _ => "service.restart",
                },
                if matches!(*action, "stop" | "restart") {
                    json!({"force":force})
                } else {
                    json!({})
                },
                matches!(*action, "stop" | "restart"),
            ))
        }
        _ => None,
    };
    let Some((operation, mut arguments, destructive)) = parsed else {
        eprintln!("사용법: localbrain-terminal list | stop ID/--all | service status/start/stop/restart/install [--json] [--yes] [--force]");
        return Ok(2);
    };
    if (yes || force)
        && !matches!(
            operation,
            "terminal.stop" | "service.stop" | "service.restart"
        )
    {
        eprintln!("종료 옵션은 stop/restart에서만 사용할 수 있습니다.");
        return Ok(2);
    }
    if destructive {
        let list = service.list()?;
        if list["service"]["unclean"] == true {
            return Err(localbrain_core::Error::identity().into());
        }
        let terms = list["terminals"]
            .as_array()
            .ok_or_else(localbrain_core::Error::identity)?;
        let count = terms.iter().filter(|t| t["state"] == "running").count();
        if count > 0 && !yes {
            if !std::io::stdin().is_terminal() {
                return Err(localbrain_core::Error::terminal(
                    "confirmation_required",
                    "--yes를 사용해 종료 범위를 확인해 주세요.",
                )
                .into());
            }
            eprint!("터미널 {count}개를 종료할까요? [y/N] ");
            let mut answer = String::new();
            std::io::stdin().read_line(&mut answer)?;
            if !matches!(answer.trim().to_lowercase().as_str(), "y" | "yes") {
                return Err(localbrain_core::Error::terminal("cancelled", "취소했습니다.").into());
            }
        }
        arguments["expected"] = json!({"generation":list["generation"],"terminals":terms.iter().map(|t|t["id"].clone()).collect::<Vec<_>>()});
        if operation == "terminal.stop" && list["running"] == false {
            if json_output {
                println!("{}", list);
            } else {
                println!("서비스 중지됨");
            }
            return Ok(0);
        }
    }
    match service.execute(operation, &arguments) {
        Ok(value) => {
            if json_output {
                println!("{}", serde_json::to_string(&value)?);
            } else if operation == "terminal.list" {
                for t in value["terminals"]
                    .as_array()
                    .ok_or_else(localbrain_core::Error::identity)?
                {
                    println!(
                        "{}\t{}\t{}\t{}",
                        t["id"].as_str().unwrap_or(""),
                        t["state"].as_str().unwrap_or(""),
                        t["name"].as_str().unwrap_or(""),
                        t["cwd"].as_str().unwrap_or("")
                    );
                }
            } else {
                println!(
                    "{}",
                    value.get("state").and_then(Value::as_str).unwrap_or("완료")
                );
            }
            Ok(
                if matches!(
                    value.get("state").and_then(Value::as_str),
                    Some("unknown" | "incompatible")
                ) {
                    1
                } else {
                    0
                },
            )
        }
        Err(error) => {
            if json_output {
                eprintln!(
                    "{}",
                    json!({"error":{"code":error.code,"message":error.message}})
                );
            } else {
                eprintln!("{error}");
            }
            Ok(1)
        }
    }
}
fn main() -> std::process::ExitCode {
    let result = (|| -> Result<i32, Box<dyn std::error::Error>> {
        let mut args = std::env::args().skip(1);
        let command = args.next();
        // Common settings never acquire a Terminal payload lease, including
        // standalone bundles placed beneath a directory named "payloads".
        if command.as_deref() == Some("preferences") {
            let arguments: Vec<String> = args.collect();
            if arguments == ["--capabilities"] {
                println!(
                    "{}",
                    localbrain_core::preferences::capabilities(env!("LOCALBRAIN_CORE_BUILD"))
                );
            } else {
                localbrain_core::preferences::serve(&arguments)?;
            }
            return Ok(0);
        }
        let _lease = payload::execution_lease()?;
        match command.as_deref() {
            Some("payload-lease") if args.next().is_none() => {
                if _lease.is_none() {
                    return Err(localbrain_core::Error::identity().into());
                }
                println!("ready");
                std::io::stdout().flush()?;
                std::io::copy(&mut std::io::stdin(), &mut std::io::sink())?;
                Ok(0)
            }
            Some("process-snapshot") if args.next().is_none() => {
                println!("{}", serde_json::to_string(&process::snapshot()?)?);
                Ok(0)
            }
            Some("manage") => {
                let root = args.next().ok_or_else(localbrain_core::Error::invalid)?;
                manage(PathBuf::from(root), args.collect())
            }
            Some("control") if args.next().is_none() => {
                let mut bytes = Vec::new();
                std::io::stdin()
                    .take(localbrain_core::MAX_REQUEST as u64 + 2)
                    .read_to_end(&mut bytes)?;
                if bytes.pop() != Some(b'\n') || bytes.contains(&b'\n') {
                    return Err(localbrain_core::Error::invalid().into());
                }
                let request = Request::parse(&bytes)?;
                if request.operation == "terminal.stream" {
                    return Err(localbrain_core::Error::invalid().into());
                }
                let response = serde_json::to_string(&request.response())?;
                if response.len() > MAX_REPLY {
                    return Err(localbrain_core::Error::invalid().into());
                }
                println!("{response}");
                Ok(0)
            }
            Some("stream") if args.next().is_none() => {
                let mut lines = Lines::stdin()?;
                let first = lines
                    .next(&AtomicBool::new(false))?
                    .ok_or_else(localbrain_core::Error::invalid)?;
                let request = Request::parse(&first)?;
                match localbrain_core::stream::run(request, lines) {
                    Ok(code) => Ok(code),
                    Err(error) => {
                        println!(
                            "{}",
                            json!({"type":"error","code":error.code,"message":error.message})
                        );
                        Ok(0)
                    }
                }
            }
            _ => Err(localbrain_core::Error::invalid().into()),
        }
    })();
    match result {
        Ok(code) => std::process::ExitCode::from(code as u8),
        Err(error) => {
            eprintln!("{error}");
            std::process::ExitCode::from(1)
        }
    }
}
