use super::arguments::{invalid, Arguments};
use localbrain_core::{
    backend::{terminal::TerminalService, Config},
    Error, Result,
};
use serde_json::{json, Value};
use std::io::{IsTerminal, Write};
fn execute(config: &Config, args: &Arguments) -> Result<Value> {
    let command = args
        .positionals
        .first()
        .map(String::as_str)
        .ok_or_else(Error::invalid)?;
    let action = args.positionals.get(1).map(String::as_str);
    if !["list", "stop", "service"].contains(&command)
        || (command == "service"
            && !action.is_some_and(|action| {
                ["install", "status", "start", "stop", "restart"].contains(&action)
            }))
    {
        return Err(Error::invalid());
    }
    let service = TerminalService::new(config)?;
    let destructive = (command == "stop" && args.flag("--all"))
        || (command == "service" && [Some("stop"), Some("restart")].contains(&action));
    let mut current = Value::Null;
    let mut expected = Value::Null;
    if destructive {
        current = service.list()?;
        if current["service"]["unclean"] == true {
            return Err(Error::terminal(
                "identity",
                "이전 작업의 종료를 확인할 수 없습니다. 해당 프로그램에서 확인해 주세요.",
            ));
        }
        let terminals = current["terminals"].as_array().ok_or_else(Error::invalid)?;
        let count = terminals
            .iter()
            .filter(|terminal| terminal["state"] == "running")
            .count();
        if count > 0 && !args.flag("--yes") {
            if !std::io::stdin().is_terminal() {
                return Err(Error::terminal(
                    "confirmation_required",
                    "--yes를 사용해 종료 범위를 확인해 주세요.",
                ));
            }
            eprint!("터미널 {count}개를 종료할까요? [y/N] ");
            let _ = std::io::stderr().flush();
            let mut answer = String::new();
            std::io::stdin()
                .read_line(&mut answer)
                .map_err(|_| Error::unavailable())?;
            if !["y", "yes"].contains(&answer.trim().to_lowercase().as_str()) {
                return Err(Error::terminal("cancelled", "취소했습니다."));
            }
        }
        expected = json!({"generation":current["generation"],"terminals":terminals.iter().map(|terminal|&terminal["id"]).collect::<Vec<_>>()});
    }
    match command {
        "list" => service.list(),
        "stop" => {
            if args.flag("--all") && current["running"] != true {
                return Ok(current);
            }
            let mut params =
                json!({"id":action,"all":args.flag("--all"),"force":args.flag("--force")});
            if args.flag("--all") {
                params["expected"] = expected;
            }
            service.rpc("stop", params, None)
        }
        _ => service.call(
            &format!("service.{}", action.unwrap()),
            if [Some("stop"), Some("restart")].contains(&action) {
                json!({"force":args.flag("--force"),"expected":expected})
            } else {
                json!({})
            },
        ),
    }
}
pub fn run(config: &Config, raw: &[String]) -> super::CommandResult {
    if config.desktop || !cfg!(target_os = "macos") {
        eprintln!("Terminal is available in the macOS web edition.");
        return Ok(2);
    }
    let args = Arguments::parse(raw, &["--json", "--yes", "--force", "--all"], &[])?;
    let command = args.positional(0)?;
    match command {
        "list" => {
            args.count(1, 1)?;
            if args.flag("--all") || args.flag("--yes") || args.flag("--force") {
                return Err(invalid("unrecognized terminal list option"));
            }
        }
        "stop" => {
            args.count(1, 2)?;
            if (args.positionals.len() == 2) == args.flag("--all") {
                return Err(invalid("choose one terminal id or --all"));
            }
        }
        "service" => {
            args.count(2, 2)?;
            if args.flag("--all") {
                return Err(invalid("unrecognized service option"));
            }
            if !["stop", "restart"].contains(&args.positionals[1].as_str())
                && (args.flag("--yes") || args.flag("--force"))
            {
                return Err(invalid("unrecognized service option"));
            }
        }
        _ => return Err(invalid("invalid terminal command")),
    }
    match execute(config, &args) {
        Ok(result) => {
            if args.flag("--json") {
                println!("{}", result);
            } else if command == "list" {
                let terminals = result["terminals"].as_array().cloned().unwrap_or_default();
                for terminal in &terminals {
                    let suffix = if terminal["error"]
                        .as_bool()
                        .unwrap_or(!terminal["error"].is_null() && terminal["error"] != "")
                    {
                        " · 종료 확인 필요"
                    } else if terminal["inputError"].as_bool().unwrap_or(
                        !terminal["inputError"].is_null() && terminal["inputError"] != "",
                    ) {
                        " · 입력 오류"
                    } else {
                        ""
                    };
                    println!(
                        "{}\t{}{suffix}\t{}\t{}",
                        terminal["id"].as_str().unwrap_or(""),
                        terminal["state"].as_str().unwrap_or(""),
                        terminal["name"].as_str().unwrap_or(""),
                        terminal["cwd"].as_str().unwrap_or("")
                    );
                }
                if terminals.is_empty() {
                    println!(
                        "{}",
                        if result["service"]["unclean"] == true {
                            "서비스 비정상 종료 · 이전 작업은 별도 확인 필요"
                        } else if result["running"] != true {
                            "서비스 중지됨"
                        } else {
                            "터미널 없음"
                        }
                    );
                }
            } else if command == "service" && args.positionals[1] == "status" {
                println!(
                    "{}",
                    if result["unclean"] == true {
                        "비정상 종료 · 이전 작업은 별도 확인 필요"
                    } else {
                        match result["state"].as_str() {
                            Some("running") => "실행 중",
                            Some("stopped") => "중지됨",
                            Some("unsupported") => "macOS 웹 전용",
                            Some("incompatible") => "버전 확인 필요",
                            _ => "상태 미확인",
                        }
                    }
                );
            } else {
                println!("완료");
            }
            Ok(
                if result["state"]
                    .as_str()
                    .is_some_and(|state| ["unknown", "incompatible"].contains(&state))
                {
                    1
                } else {
                    0
                },
            )
        }
        Err(error) => {
            if args.flag("--json") {
                eprintln!(
                    "{}",
                    json!({"error":{"code":error.code,"message":error.message}})
                );
            } else {
                eprintln!("{}", error.message);
            }
            Ok(1)
        }
    }
}
