#![cfg(unix)]

use localbrain_core::process;
use std::{process::Command, time::Duration};

const CHILD_CASE: &str = "LOCALBRAIN_NATIVE_PROCESS_ENV_TEST_CASE";
const NON_UTC: &str = "UTC-09";

fn isolated_case(case: &str) {
    let output = Command::new(std::env::current_exe().unwrap())
        .args(["--exact", "isolated_environment_child", "--nocapture"])
        .env_clear()
        .env(CHILD_CASE, case)
        .env("PATH", "/synthetic/inherited/path")
        .env("HOME", "/synthetic/inherited/home")
        .env("LANG", "C")
        .env("LC_ALL", "C")
        .env("TZ", NON_UTC)
        .env("LOCALBRAIN_UNTRUSTED_INHERITED", "must-not-leak")
        .env("LOCALBRAIN_EXPLICIT_REMOVED", "inherited-value")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{case}: {}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn explicit_command_environment_survives_inherited_environment_filtering() {
    isolated_case("overrides");
}

#[test]
fn process_snapshot_birth_matches_independent_utc_ps_under_non_utc_environment() {
    isolated_case("snapshot");
}

#[test]
fn isolated_environment_child() {
    let Ok(case) = std::env::var(CHILD_CASE) else {
        return;
    };
    assert_eq!(std::env::var("TZ").unwrap(), NON_UTC);
    assert_eq!(
        std::env::var("LOCALBRAIN_UNTRUSTED_INHERITED").unwrap(),
        "must-not-leak"
    );
    match case.as_str() {
        "overrides" => {
            let (status, output) = process::run_status(
                Command::new("/bin/sh")
                    .args([
                        "-c",
                        "printf '%s\\n' \"${TZ-unset}\" \"${LOCALBRAIN_EXPLICIT_SCOPE-unset}\" \"${HOME-unset}\" \"${LOCALBRAIN_UNTRUSTED_INHERITED-unset}\" \"${LOCALBRAIN_EXPLICIT_REMOVED-unset}\" \"$PATH\"",
                    ])
                    .env("TZ", "UTC")
                    .env("LOCALBRAIN_EXPLICIT_SCOPE", "synthetic trusted 값")
                    .env("PATH", "/synthetic/trusted/path")
                    .env_remove("HOME")
                    .env("LOCALBRAIN_EXPLICIT_REMOVED", "temporary")
                    .env_remove("LOCALBRAIN_EXPLICIT_REMOVED"),
                Duration::from_secs(5),
                4096,
            )
            .unwrap();
            assert!(status.success());
            assert_eq!(
                output,
                "UTC\nsynthetic trusted 값\nunset\nunset\nunset\n/synthetic/trusted/path\n"
                    .as_bytes()
            );
            // The runner changes only the Command, never the calling process.
            assert_eq!(std::env::var("TZ").unwrap(), NON_UTC);
            assert_eq!(std::env::var("HOME").unwrap(), "/synthetic/inherited/home");
        }
        "snapshot" => {
            let pid = std::process::id();
            let birth = |timezone: &str| {
                let output = Command::new("/bin/ps")
                    .args(["-p", &pid.to_string(), "-o", "lstart="])
                    .env_clear()
                    .env("LC_ALL", "C")
                    .env("TZ", timezone)
                    .output()
                    .unwrap();
                assert!(output.status.success());
                String::from_utf8(output.stdout)
                    .unwrap()
                    .split_whitespace()
                    .collect::<Vec<_>>()
                    .join(" ")
            };
            let utc = birth("UTC");
            let non_utc = birth(NON_UTC);
            assert_ne!(utc, non_utc, "the independent timezone probe must differ");
            let record = process::snapshot()
                .unwrap()
                .into_iter()
                .find(|record| record.pid == i32::try_from(pid).unwrap())
                .unwrap();
            assert_eq!(record.born, utc);
            assert!(!record.dead);
            assert_eq!(std::env::var("TZ").unwrap(), NON_UTC);
        }
        _ => panic!("unknown isolated environment case"),
    }
}
