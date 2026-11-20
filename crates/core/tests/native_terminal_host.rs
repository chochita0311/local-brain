use localbrain_core::backend::{
    preferences,
    terminal::{presentation, shell, TerminalService},
    terminal_workspaces, Config,
};
use serde_json::{json, Value};
use std::{os::unix::fs::PermissionsExt, process::Command};
fn setup() -> (tempfile::TempDir, Config) {
    let root = tempfile::Builder::new()
        .prefix("lb-t-")
        .tempdir_in("/private/tmp")
        .unwrap();
    std::fs::set_permissions(root.path(), std::fs::Permissions::from_mode(0o700)).unwrap();
    let config = Config::for_data_dir(root.path().join("d"));
    std::fs::create_dir(&config.home_dir).unwrap();
    std::fs::set_permissions(&config.home_dir, std::fs::Permissions::from_mode(0o700)).unwrap();
    (root, config)
}
#[test]
fn terminal_listing_stays_passive_and_independent_of_database() {
    let (_root, config) = setup();
    let terminal = TerminalService::new(&config).unwrap();
    let value = terminal.list().unwrap();
    assert_eq!(value["running"], false);
    assert_eq!(value["terminals"], json!([]));
    assert!(!config.database_path.exists());
    assert!(!terminal.root.exists());
    assert!(!config.data_dir.exists());
    assert!(terminal
        .call(
            "manager.rpc",
            json!({"method":"not-a-method","params":{},"generation":null})
        )
        .is_err());
    assert!(!terminal.root.exists());
}

#[test]
fn saved_terminal_workspaces_require_owner_only_permissions() {
    let (_root, config) = setup();
    let contents = json!({"schema":1,"generation":null,"items":[
        {"id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","name":"Synthetic Workspace","cwd":"","tabs":[]}
    ]});
    let path = config.data_dir.join("terminal-workspaces.json");
    localbrain_core::backend::storage::files::atomic_write(&path, contents.to_string().as_bytes())
        .unwrap();
    let state = json!({"generation":null,"tabs":[],"terminals":[]});
    assert_eq!(
        terminal_workspaces::read_workspaces(&config, &state)["items"],
        contents["items"]
    );

    std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o644)).unwrap();
    let projected = terminal_workspaces::read_workspaces(&config, &state);
    assert_eq!(projected["items"], json!([]));
    assert!(projected["error"].is_string());
    assert!(terminal_workspaces::change_workspaces(
        &config,
        || Ok(state.clone()),
        "reconcile",
        &json!({"generation":null})
    )
    .is_err());
    assert_eq!(
        std::fs::read_to_string(&path).unwrap(),
        contents.to_string()
    );
}
#[test]
fn native_terminal_preferences_share_common_revision_and_preserve_other_sections() {
    let (_root, config) = setup();
    let common = preferences::read_preferences(&config).unwrap();
    preferences::save_preferences(
        &config,
        &json!({"onboarding_completed":true}),
        &common["revision"],
    )
    .unwrap();
    let old = preferences::terminal_read(&config).unwrap();
    let saved = preferences::terminal_save(
        &config,
        &json!({"cwd":config.home_dir,"shell":"/bin/zsh"}),
        &old["revision"],
    )
    .unwrap();
    assert_eq!(saved["cwd"], json!(config.home_dir));
    assert_ne!(saved["revision"], old["revision"]);
    assert_eq!(
        preferences::effective_preferences(&config).unwrap()["onboarding_completed"],
        true
    );
    assert_eq!(
        preferences::terminal_launch(&config).unwrap(),
        json!({"cwd":config.home_dir,"shell":"/bin/zsh"})
    );
    assert_eq!(
        preferences::terminal_save(
            &config,
            &json!({"cwd":config.home_dir,"shell":"/bin/zsh"}),
            &old["revision"]
        )
        .unwrap_err()
        .status,
        409
    );
    assert!(!config.database_path.exists());
}
#[test]
fn preferences_accept_parent_components_and_keep_final_symlink_check() {
    let (root, config) = setup();
    let initial = preferences::read_preferences(&config).unwrap();
    preferences::save_preferences(
        &config,
        &json!({"onboarding_completed":true}),
        &initial["revision"],
    )
    .unwrap();
    std::fs::create_dir(root.path().join("anchor")).unwrap();
    let mut alias = config.clone();
    alias.data_dir = root.path().join("anchor/../d");
    assert_eq!(
        preferences::effective_preferences(&alias).unwrap()["onboarding_completed"],
        true
    );
    assert!(preferences::terminal_read(&alias).is_ok());

    std::os::unix::fs::symlink(&config.data_dir, root.path().join("link")).unwrap();
    for suffix in ["anchor/../link", "anchor/../link/.", "anchor/../link/"] {
        alias.data_dir = root.path().join(suffix);
        assert!(preferences::terminal_read(&alias).is_err(), "{suffix}");
    }
}
#[test]
fn shared_tab_order_preserves_workspace_and_hidden_tab_boundaries() {
    let (root, _config) = setup();
    let generation = "0123456789abcdef0123456789abcdef";
    let tabs = vec![
        json!({"id":"a","cwd":"/one","workspaceId":"one"}),
        json!({"id":"b","cwd":"/two","workspaceId":"one"}),
        json!({"id":"c","cwd":"/two","workspaceId":"two"}),
    ];
    assert_eq!(
        presentation::save_order(root.path(), generation, &tabs, &json!(["b", "a", "c"])).unwrap()
            ["order"],
        json!(["b", "a", "c"])
    );
    assert_eq!(
        presentation::load_order(root.path(), generation, &tabs)["order"],
        json!(["b", "a", "c"])
    );
    assert!(
        presentation::save_order(root.path(), generation, &tabs, &json!(["c", "a", "b"])).is_err()
    );
    let mut hidden = tabs.clone();
    hidden[0]["hidden"] = json!(true);
    assert!(
        presentation::save_order(root.path(), generation, &hidden, &json!(["a", "b", "c"]))
            .is_err()
    );
    assert_eq!(
        presentation::load_order(root.path(), "fedcba9876543210fedcba9876543210", &tabs)["order"],
        json!(["a", "b", "c"])
    );
    std::fs::set_permissions(
        root.path().join("view-order.json"),
        std::fs::Permissions::from_mode(0o644),
    )
    .unwrap();
    assert_eq!(
        presentation::load_order(root.path(), generation, &tabs)["error"],
        "저장한 탭 순서를 읽지 못했습니다."
    );
}
#[test]
fn native_zsh_shim_is_immutable_and_preserves_synthetic_startup_scope() {
    let (_root, config) = setup();
    let launcher = shell::integrated_shell(&config, &json!("/bin/zsh")).unwrap();
    let path = std::path::Path::new(launcher.as_str().unwrap());
    let dir = path.parent().unwrap();
    shell::verify(dir).unwrap();
    assert_eq!(path.metadata().unwrap().permissions().mode() & 0o777, 0o700);
    std::fs::write(
        config.home_dir.join(".zshenv"),
        "typeset -g SYNTHETIC_STARTUP='kept'\n",
    )
    .unwrap();
    let output = Command::new(path)
        .args([
            "-lc",
            "print -r -- \"$SYNTHETIC_STARTUP:${ZDOTDIR-unset}:$SHELL\"",
        ])
        .env_clear()
        .env("HOME", &config.home_dir)
        .env("PATH", "/usr/bin:/bin")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        String::from_utf8(output.stdout).unwrap().trim(),
        "kept:unset:/bin/zsh"
    );
    assert_eq!(
        shell::integrated_shell(&config, &launcher).unwrap(),
        launcher
    );
    std::fs::write(dir.join("hooks.zsh"), "changed").unwrap();
    assert!(shell::integrated_shell(&config, &json!("/bin/zsh")).is_err());
    assert!(shell::integrated_shell(&config, &launcher).is_err());
    assert_eq!(
        std::fs::read_to_string(dir.join("hooks.zsh")).unwrap(),
        "changed"
    );
    assert_eq!(
        shell::integrated_shell(&config, &Value::Null).unwrap(),
        Value::Null
    );
}
