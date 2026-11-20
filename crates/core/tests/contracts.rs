use localbrain_core::{files, payload, settings, Context, Request, MAX_REQUEST};
use serde_json::{json, Value};
use std::fs;
use std::os::unix::fs::{symlink, PermissionsExt};
use std::path::PathBuf;

struct Fixture {
    root: PathBuf,
    context: Context,
}
impl Fixture {
    fn new() -> Self {
        let root = fs::canonicalize(std::env::temp_dir())
            .unwrap()
            .join(format!("lb-core-{}", files::random_id().unwrap()));
        fs::create_dir(&root).unwrap();
        fs::set_permissions(&root, fs::Permissions::from_mode(0o700)).unwrap();
        let context = Context {
            data_dir: root.join("data"),
            cache_dir: root.join("cache"),
            home_dir: root.clone(),
        };
        Self { root, context }
    }
    fn request(&self) -> Value {
        json!({"wire":1,"id":"request","context":{"dataDir":self.context.data_dir,"cacheDir":self.context.cache_dir,"homeDir":self.context.home_dir},"operation":"service.status","arguments":{}})
    }
    fn settings(&self) -> Value {
        json!({"revision":files::digest(b""),"section":{"kind":"missing","cwd":{"kind":"missing"},"shell":{"kind":"missing"}}})
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.root).unwrap();
    }
}

#[test]
fn wire_rejects_bool_unknown_fields_operations_and_relative_context() {
    let f = Fixture::new();
    assert!(Request::parse(&serde_json::to_vec(&f.request()).unwrap()).is_ok());
    for (key, value) in [
        ("wire", json!(true)),
        ("wire", json!(2)),
        ("unknown", json!(1)),
        ("operation", json!("shell.exec")),
        ("id", json!("")),
        ("id", json!("a".repeat(129))),
    ] {
        let mut request = f.request();
        request[key] = value;
        assert!(
            Request::parse(&serde_json::to_vec(&request).unwrap()).is_err(),
            "{key}"
        );
    }
    let mut request = f.request();
    request["context"]["dataDir"] = json!("relative");
    assert!(Request::parse(&serde_json::to_vec(&request).unwrap()).is_err());
    let mut request = f.request();
    request["arguments"] = json!({"shell":"/bin/sh"});
    assert!(Request::parse(&serde_json::to_vec(&request).unwrap()).is_err());
}

#[test]
fn wire_byte_limit_and_utf8_id_are_exact() {
    let f = Fixture::new();
    let mut request = f.request();
    request["id"] = json!("한".repeat(42));
    assert!(Request::parse(&serde_json::to_vec(&request).unwrap()).is_ok());
    request["id"] = json!("한".repeat(43));
    assert!(Request::parse(&serde_json::to_vec(&request).unwrap()).is_err());
    assert!(Request::parse(&vec![b' '; MAX_REQUEST + 1]).is_err());
}

#[test]
fn settings_read_does_not_create_paths_and_does_not_validate_cache() {
    let mut f = Fixture::new();
    f.context.cache_dir = f.root.join(".git/broken-cache");
    let value = settings::execute(&f.context, "settings.read", &f.settings()).unwrap();
    assert_eq!(value["cwd"], json!(f.root));
    assert!(!f.context.data_dir.exists());
    assert!(!f.context.cache_dir.exists());
}

#[test]
fn typed_invalid_and_stale_revision_are_preferences_errors() {
    let f = Fixture::new();
    let mut args = f.settings();
    args["section"]["cwd"] = json!({"kind":"invalid"});
    assert_eq!(
        settings::execute(&f.context, "settings.read", &args)
            .unwrap_err()
            .kind,
        "preferences"
    );
    args = f.settings();
    args["revision"] = json!(files::digest(b"stale"));
    assert_eq!(
        settings::execute(&f.context, "settings.read", &args)
            .unwrap_err()
            .kind,
        "preferences"
    );
    assert!(!f.context.data_dir.exists());
}

#[test]
fn actual_folder_override_does_not_require_deleted_unused_default() {
    let f = Fixture::new();
    let mut args = f.settings();
    args["section"] = json!({"kind":"table","cwd":{"kind":"string","value":f.root.join("deleted")},"shell":{"kind":"string","value":"/bin/sh"}});
    assert!(settings::execute(&f.context, "settings.launch", &args).is_err());
    args["cwdOverride"] = json!(f.root);
    assert_eq!(
        settings::execute(&f.context, "settings.launch", &args).unwrap()["cwd"],
        json!(f.root)
    );
    args["section"]["shell"]["value"] = json!("/synthetic/missing-shell");
    assert_eq!(
        settings::execute(&f.context, "settings.launch", &args)
            .unwrap_err()
            .kind,
        "preferences"
    );
}

#[test]
fn prepare_preserves_significant_spaces_and_returns_only_patch() {
    let f = Fixture::new();
    let cwd = f.root.join("folder ");
    fs::create_dir(&cwd).unwrap();
    let shell = f.root.join("shell ");
    symlink("/bin/sh", &shell).unwrap();
    let mut args = f.settings();
    args["cwd"] = json!(cwd);
    args["shell"] = json!(shell);
    let value = settings::execute(&f.context, "settings.prepare", &args).unwrap();
    assert_eq!(value["patch"], json!({"cwd":cwd,"shell":shell}));
    assert_eq!(value["scopeHash"], json!(payload::scope(&f.context)));
    assert!(!f.context.data_dir.exists());
}

#[test]
fn storage_rejects_git_symlink_hardlink_and_shared_lock_contention() {
    let f = Fixture::new();
    let repository = f.root.join("repository");
    fs::create_dir(&repository).unwrap();
    fs::write(repository.join(".git"), b"worktree").unwrap();
    assert!(files::location(&repository.join("data")).is_err());
    let alias = f.root.join("alias");
    symlink(&f.root, &alias).unwrap();
    assert!(files::location(&alias.join("data")).is_err());
    let lock = f.root.join("use.lock");
    let _shared = files::Lock::acquire(&lock, false, true).unwrap();
    assert_eq!(
        files::Lock::acquire(&lock, true, false).err().unwrap().code,
        "busy"
    );
    let link = f.root.join("hardlink");
    fs::hard_link(&lock, &link).unwrap();
    assert!(files::Lock::acquire(&link, false, false).is_err());
}

#[test]
fn payload_identity_is_recursive_sorted_body_without_its_own_id() {
    let first: Value =
        serde_json::from_str(r#"{"z":{"b":2,"a":1},"payloadId":"ignored","a":0}"#).unwrap();
    let second: Value = serde_json::from_str(r#"{"a":0,"z":{"a":1,"b":2}}"#).unwrap();
    assert_eq!(
        payload::manifest_id(&first).unwrap(),
        payload::manifest_id(&second).unwrap()
    );
    let mut changed = second;
    changed["z"]["a"] = json!(2);
    assert_ne!(
        payload::manifest_id(&first).unwrap(),
        payload::manifest_id(&changed).unwrap()
    );
}
