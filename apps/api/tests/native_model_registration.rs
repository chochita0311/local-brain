//! Synthetic compatibility cases. Every install path refuses before HTTPS;
//! snapshots contain only tiny dummy bytes, never real model assets.
#![cfg(unix)]
use localbrain_core::backend::Config;
use localbrain_models::catalog::{ModelKey, GENERATION_HUB_OWNER, GENERATION_OWNER};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs::{self, OpenOptions},
    io::{BufRead, BufReader, Read},
    os::{
        fd::AsRawFd,
        unix::fs::{symlink, OpenOptionsExt, PermissionsExt},
    },
    path::{Path, PathBuf},
    process::{Child, Command, Output, Stdio},
};

const PRIVATE_SENTINEL: &str = "synthetic-private-registration-marker-do-not-echo";
struct Host {
    root: tempfile::TempDir,
    config: Config,
}
impl Host {
    fn new() -> Self {
        let root = tempfile::Builder::new()
            .prefix("lb-registration-")
            .tempdir_in("/private/tmp")
            .unwrap();
        let config = Config::for_data_dir(root.path().join("data"));
        private_dir(&config.home_dir);
        Self { root, config }
    }
    fn path(&self, name: &str) -> PathBuf {
        self.root.path().join(name)
    }
    fn command(&self) -> Command {
        let mut command = Command::new(env!("CARGO_BIN_EXE_localbrain"));
        self.environment(&mut command);
        command.args(["models", "registration"]);
        command
    }
    fn environment(&self, command: &mut Command) {
        command
            .env_clear()
            .env("PATH", "/usr/bin:/bin")
            .env("HOME", &self.config.home_dir)
            .env("SHELL", "/bin/sh")
            .env("LOCALBRAIN_DATA_DIR", &self.config.data_dir)
            .env("LOCALBRAIN_CACHE_DIR", &self.config.cache_dir)
            .env("LOCALBRAIN_DEVELOPMENT_DIR", &self.config.development_dir)
            .env("LOCALBRAIN_CONTEXT_ROOT", &self.config.context_root)
            .env("LOCALBRAIN_CLAUDE_ROOT", &self.config.claude_root)
            .env("LOCALBRAIN_CODEX_ROOT", &self.config.codex_root)
            .env("HF_HOME", &self.config.hf_home)
            .env("HF_HUB_CACHE", &self.config.hf_hub_cache)
            .stdin(Stdio::null());
    }
    fn run(&self, args: &[&str]) -> Output {
        self.command().args(args).output().unwrap()
    }
    fn registration(&self, name: &str, key: ModelKey) -> PathBuf {
        let root = self.path(name);
        private_dir(&root);
        let spec = key.spec();
        private_json(
            &root.join("owner.json"),
            &json!({"owner":GENERATION_OWNER,"model":spec.id,"revision":spec.revision}),
        );
        root
    }
    fn dummy_snapshot(&self, key: ModelKey) -> PathBuf {
        let snapshot = self
            .config
            .hf_hub_cache
            .join(key.spec().snapshot_relative());
        private_dir(&snapshot);
        for name in key.spec().assets() {
            let file = snapshot.join(name);
            if let Some(parent) = file.parent() {
                private_dir(parent);
            }
            private_bytes(&file, PRIVATE_SENTINEL.as_bytes());
        }
        snapshot
    }
    fn assert_no_application_state(&self) {
        assert!(!self.config.database_path.exists());
        assert!(!self.config.data_dir.exists());
        assert!(!self.config.cache_dir.exists());
    }
}
fn private_dir(path: &Path) {
    fs::create_dir_all(path).unwrap();
    fs::set_permissions(path, fs::Permissions::from_mode(0o700)).unwrap();
}
fn private_bytes(path: &Path, bytes: &[u8]) {
    fs::write(path, bytes).unwrap();
    fs::set_permissions(path, fs::Permissions::from_mode(0o600)).unwrap();
}
fn private_json(path: &Path, value: &Value) {
    private_bytes(path, &serde_json::to_vec(value).unwrap());
}
fn check(output: Output, code: i32, lines: &[&str]) {
    assert_eq!(
        output.status.code(),
        Some(code),
        "stdout={:?} stderr={:?}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        String::from_utf8(output.stdout)
            .unwrap()
            .lines()
            .collect::<Vec<_>>(),
        lines
    );
    assert!(
        output.stderr.is_empty(),
        "stderr={:?}",
        String::from_utf8_lossy(&output.stderr)
    );
}
fn tree(path: &Path) -> BTreeMap<String, (u32, String)> {
    fn walk(root: &Path, path: &Path, out: &mut BTreeMap<String, (u32, String)>) {
        if !path.exists() && !path.is_symlink() {
            return;
        }
        let info = path.symlink_metadata().unwrap();
        let name = path
            .strip_prefix(root)
            .unwrap()
            .to_string_lossy()
            .into_owned();
        let identity = if info.file_type().is_symlink() {
            format!("link:{}", fs::read_link(path).unwrap().display())
        } else if info.is_dir() {
            "directory".into()
        } else {
            format!("{:x}", Sha256::digest(fs::read(path).unwrap()))
        };
        out.insert(name, (info.permissions().mode() & 0o777, identity));
        if info.is_dir() {
            for entry in fs::read_dir(path).unwrap() {
                walk(root, &entry.unwrap().path(), out);
            }
        }
    }
    let mut out = BTreeMap::new();
    walk(path, path, &mut out);
    out
}

#[test]
fn malformed_arguments_refuse_before_status_or_filesystem_mutation() {
    let h = Host::new();
    let root = h.path("new-registration");
    let root = root.to_str().unwrap();
    for args in [
        vec![],
        vec!["--root"],
        vec!["--root", "--verify"],
        vec!["--root", root, "--model"],
        vec!["--root", root, "--xet-cache"],
        vec!["--root", root, "--model", "4b"],
        vec!["--root", root, "--model", "Qwen/Qwen3-Embedding-0.6B"],
        vec!["--root", root, "--unknown", PRIVATE_SENTINEL],
        vec!["--root", root, "unexpected"],
    ] {
        check(h.run(&args), 2, &["INVALID_ARGUMENTS"]);
        assert!(!Path::new(root).exists());
        assert!(!h.config.hf_hub_cache.exists());
        h.assert_no_application_state();
    }
}
#[test]
fn root_admission_and_owner_checks_preserve_private_inputs_without_echo() {
    let h = Host::new();
    let root = h.path("missing-parent/registration");
    check(
        h.run(&["--root", root.to_str().unwrap(), "--verify"]),
        2,
        &["MODEL_VERIFYING", "INVALID_MODEL_ROOT"],
    );
    check(
        h.run(&["--root", "relative-registration", "--verify"]),
        2,
        &["MODEL_VERIFYING", "INVALID_MODEL_ROOT"],
    );
    let target = h.registration("target", ModelKey::Generation4b);
    let alias = h.path("alias");
    symlink(&target, &alias).unwrap();
    let before = tree(&target);
    check(
        h.run(&["--root", alias.to_str().unwrap(), "--verify"]),
        2,
        &["MODEL_VERIFYING", "INVALID_MODEL_ROOT"],
    );
    assert_eq!(tree(&target), before);
    let foreign = h.registration("foreign", ModelKey::Generation4b);
    private_json(
        &foreign.join("owner.json"),
        &json!({"owner":PRIVATE_SENTINEL,"model":"Qwen/Qwen3-4B","revision":ModelKey::Generation4b.spec().revision}),
    );
    let before = tree(&foreign);
    check(
        h.run(&["--root", foreign.to_str().unwrap(), "--verify"]),
        2,
        &["MODEL_VERIFYING", "UNOWNED_MODEL"],
    );
    assert_eq!(tree(&foreign), before);
    let public = h.registration("public-mode", ModelKey::Generation4b);
    fs::set_permissions(&public, fs::Permissions::from_mode(0o755)).unwrap();
    let before = tree(&public);
    check(
        h.run(&["--root", public.to_str().unwrap(), "--verify"]),
        2,
        &["MODEL_VERIFYING", "UNOWNED_MODEL"],
    );
    assert_eq!(tree(&public), before);
    h.assert_no_application_state();
    assert!(!h.config.hf_hub_cache.exists());
}
#[test]
fn verify_infers_either_full_model_id_and_never_creates_locks_or_cache() {
    let h = Host::new();
    for key in [ModelKey::Generation4b, ModelKey::Generation8b] {
        let root = h.registration(key.spec().slug, key);
        private_json(
            &root.join("model.json"),
            &json!({"owner":"foreign-synthetic","model_id":key.spec().id,"revision":key.spec().revision,"private":PRIVATE_SENTINEL}),
        );
        let before = tree(&root);
        check(
            h.run(&["--root", root.to_str().unwrap(), "--verify"]),
            2,
            &["MODEL_VERIFYING", "INVALID_MODEL"],
        );
        check(
            h.run(&[
                "--ro",
                root.to_str().unwrap(),
                "--ver",
                "--xet-cache",
                "relative-and-unused",
            ]),
            2,
            &["MODEL_VERIFYING", "INVALID_MODEL"],
        );
        check(
            h.run(&[
                "--root",
                root.to_str().unwrap(),
                "--verify",
                "--model",
                key.spec().id,
            ]),
            2,
            &["MODEL_VERIFYING", "INVALID_MODEL"],
        );
        let other = if key == ModelKey::Generation4b {
            ModelKey::Generation8b
        } else {
            ModelKey::Generation4b
        };
        check(
            h.run(&[
                "--root",
                root.to_str().unwrap(),
                "--verify",
                "--model",
                other.spec().id,
            ]),
            2,
            &["MODEL_VERIFYING", "MODEL_MISMATCH"],
        );
        if key == ModelKey::Generation8b {
            check(
                h.run(&["--root", root.to_str().unwrap()]),
                2,
                &["MODEL_INSTALLING", "MODEL_MISMATCH"],
            );
        }
        assert_eq!(tree(&root), before);
        assert!(!root.join("install.lock").exists());
    }
    assert!(!h.config.hf_hub_cache.exists());
    h.assert_no_application_state();
}
#[test]
fn unsafe_metadata_and_unrelated_entries_are_refused_before_inventory() {
    let h = Host::new();
    for shape in [
        "symlink",
        "hardlink",
        "public-mode",
        "bad-json",
        "extra-entry",
    ] {
        let root = h.registration(shape, ModelKey::Generation4b);
        let model = root.join("model.json");
        match shape {
            "symlink" => {
                let outside = h.path("outside-model.json");
                private_bytes(&outside, PRIVATE_SENTINEL.as_bytes());
                symlink(outside, &model).unwrap();
            }
            "hardlink" => {
                let outside = h.path("linked-model.json");
                private_bytes(&outside, PRIVATE_SENTINEL.as_bytes());
                fs::hard_link(outside, &model).unwrap();
            }
            "public-mode" => {
                private_bytes(&model, PRIVATE_SENTINEL.as_bytes());
                fs::set_permissions(&model, fs::Permissions::from_mode(0o644)).unwrap();
            }
            "bad-json" => private_bytes(&model, PRIVATE_SENTINEL.as_bytes()),
            _ => private_bytes(
                &root.join("unrelated-private-note.txt"),
                PRIVATE_SENTINEL.as_bytes(),
            ),
        };
        let before = tree(&root);
        let expected = if shape == "extra-entry" {
            "UNOWNED_MODEL"
        } else if shape == "bad-json" {
            "MODEL_INSTALL_FAILED"
        } else {
            "UNOWNED_OUTPUT"
        };
        check(
            h.run(&["--root", root.to_str().unwrap(), "--verify"]),
            2,
            &["MODEL_VERIFYING", expected],
        );
        assert_eq!(tree(&root), before);
    }
    assert!(!h.config.hf_hub_cache.exists());
    h.assert_no_application_state();
}
#[test]
fn busy_registration_refuses_before_transfer_admission_or_cache_creation() {
    let h = Host::new();
    let root = h.registration("arbitrary-private-registration", ModelKey::Generation4b);
    let transfer = h.path("transfer");
    private_dir(&transfer);
    let lock = OpenOptions::new()
        .read(true)
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(root.join("install.lock"))
        .unwrap();
    assert_eq!(
        unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) },
        0
    );
    let before = tree(&root);
    check(
        h.run(&[
            "--root",
            root.to_str().unwrap(),
            "--xet-cache",
            transfer.to_str().unwrap(),
        ]),
        2,
        &["MODEL_INSTALLING", "MODEL_BUSY"],
    );
    assert_eq!(tree(&root), before);
    assert!(fs::read_dir(&transfer).unwrap().next().is_none());
    assert!(!h.config.hf_hub_cache.exists());
    h.assert_no_application_state();
}
#[test]
fn transfer_guard_runs_only_for_missing_transport_and_preserves_partial_registration() {
    let h = Host::new();
    let root = h.path("registration-not-data-models");
    let transfer = h.path("nonempty-transfer");
    private_dir(&transfer);
    private_bytes(
        &transfer.join("private-sentinel.txt"),
        PRIVATE_SENTINEL.as_bytes(),
    );
    let before = tree(&transfer);
    check(
        h.run(&[
            "--root",
            root.to_str().unwrap(),
            "--model",
            "Qwen/Qwen3-8B",
            "--xet-cache",
            transfer.to_str().unwrap(),
        ]),
        2,
        &["MODEL_INSTALLING", "UNOWNED_TRANSFER_CACHE"],
    );
    assert_eq!(tree(&transfer), before);
    assert!(root.join("owner.json").is_file());
    assert!(root.join("install.lock").is_file());
    assert!(!root.join("model.json").exists());
    let marker: Value =
        serde_json::from_slice(&fs::read(root.join("owner.json")).unwrap()).unwrap();
    assert_eq!(marker["model"], "Qwen/Qwen3-8B");
    let snapshot = h
        .config
        .hf_hub_cache
        .join(ModelKey::Generation8b.spec().snapshot_relative());
    assert!(snapshot.is_dir());
    assert!(fs::read_dir(snapshot).unwrap().next().is_none());
    h.assert_no_application_state();
    let h = Host::new();
    let root = h.path("default-four-b");
    let transfer = h.path("bad-transfer");
    private_dir(&transfer);
    fs::set_permissions(&transfer, fs::Permissions::from_mode(0o755)).unwrap();
    check(
        h.run(&[
            "--root",
            root.to_str().unwrap(),
            "--xet-cache",
            transfer.to_str().unwrap(),
        ]),
        2,
        &["MODEL_INSTALLING", "UNOWNED_TRANSFER_CACHE"],
    );
    let marker: Value =
        serde_json::from_slice(&fs::read(root.join("owner.json")).unwrap()).unwrap();
    assert_eq!(marker["model"], "Qwen/Qwen3-4B");
    assert!(!transfer.join("owner.json").exists());
    let h = Host::new();
    h.dummy_snapshot(ModelKey::Generation4b);
    let root = h.path("complete-dummy-cache");
    let invalid_transfer = h.path("does-not-exist");
    check(
        h.run(&[
            "--root",
            root.to_str().unwrap(),
            "--xet-cache",
            invalid_transfer.to_str().unwrap(),
        ]),
        2,
        &["MODEL_INSTALLING", "MODEL_ASSETS_CHANGED"],
    );
    assert!(!invalid_transfer.exists());
    assert!(!root.join("model.json").exists());
    h.assert_no_application_state();
}

struct OwnedChild(Option<Child>);
impl Drop for OwnedChild {
    fn drop(&mut self) {
        if let Some(child) = self.0.as_mut() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}
#[test]
fn native_sigint_retains_interrupted_lines_and_does_not_publish_a_registration() {
    let h = Host::new();
    let root = h.registration("interrupt-metadata-only", ModelKey::Generation4b);
    let model = root.join("model.json");
    let value = json!({"owner":GENERATION_HUB_OWNER,"model_id":"Qwen/Qwen3-4B","revision":ModelKey::Generation4b.spec().revision,"snapshot":"missing","private":PRIVATE_SENTINEL,"padding":"x".repeat(16*1024*1024)});
    private_json(&model, &value);
    let size = fs::metadata(&model).unwrap().len();
    let mut child = OwnedChild(Some(
        h.command()
            .args(["--root", root.to_str().unwrap(), "--verify"])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap(),
    ));
    let stdout = child.0.as_mut().unwrap().stdout.take().unwrap();
    let mut stdout = BufReader::new(stdout);
    let mut first = String::new();
    stdout.read_line(&mut first).unwrap();
    assert_eq!(first, "MODEL_VERIFYING\n");
    std::thread::sleep(std::time::Duration::from_millis(5));
    assert_eq!(
        unsafe { libc::kill(child.0.as_ref().unwrap().id() as i32, libc::SIGINT) },
        0
    );
    let mut rest = String::new();
    stdout.read_to_string(&mut rest).unwrap();
    let output = child.0.take().unwrap().wait_with_output().unwrap();
    assert_eq!(
        output.status.code(),
        Some(130),
        "first={first:?} rest={rest:?} stderr={:?}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(rest, "MODEL_INTERRUPTED\n");
    assert!(output.stderr.is_empty());
    assert_eq!(fs::metadata(model).unwrap().len(), size);
    assert!(!root.join("install.lock").exists());
    assert!(!h.config.hf_hub_cache.exists());
    h.assert_no_application_state();
}
