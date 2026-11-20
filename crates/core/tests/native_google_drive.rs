use localbrain_core::backend::{
    google_drive::{
        self as drive,
        api::Remote,
        engine::Engine,
        policy::{self, FOLDER},
        service::{ApiFactory, DriveService, SourceLoader},
        store::Store,
    },
    Config, Result,
};
use md5::{Digest, Md5};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicUsize, Ordering},
        Arc, Barrier, Mutex,
    },
};
fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Md5::digest(bytes))
}
#[derive(Default)]
struct Data {
    files: BTreeMap<String, Value>,
    bodies: BTreeMap<String, Vec<u8>>,
    sequence: usize,
    calls: Vec<(String, String)>,
    denied: BTreeSet<String>,
}
struct Fake {
    data: Mutex<Data>,
    cancelled: AtomicBool,
    fail_upload: AtomicBool,
    cancel_in_upload: AtomicBool,
    partial: AtomicBool,
    barrier: Mutex<Option<Arc<Barrier>>>,
    active: AtomicUsize,
    peak: AtomicUsize,
    publish_store: Mutex<Option<(Arc<Store>, String)>>,
}
impl Fake {
    fn new() -> Self {
        let fake = Self {
            data: Mutex::new(Data::default()),
            cancelled: AtomicBool::new(false),
            fail_upload: AtomicBool::new(false),
            cancel_in_upload: AtomicBool::new(false),
            partial: AtomicBool::new(false),
            barrier: Mutex::new(None),
            active: AtomicUsize::new(0),
            peak: AtomicUsize::new(0),
            publish_store: Mutex::new(None),
        };
        fake.data.lock().unwrap().files.insert(
            "root".into(),
            json!({"id":"root","name":"Shared","mimeType":FOLDER,"parents":[],"version":"1"}),
        );
        fake
    }
    fn body(&self, id: &str, name: &str, parent: &str, body: &[u8]) {
        let mut data = self.data.lock().unwrap();
        let version = data
            .files
            .get(id)
            .and_then(|v| v["version"].as_str())
            .and_then(|s| s.parse::<u64>().ok())
            .unwrap_or(0)
            + 1;
        data.bodies.insert(id.into(), body.to_vec());
        data.files.insert(id.into(),json!({"id":id,"name":name,"parents":[parent],"mimeType":"application/octet-stream","size":body.len().to_string(),"md5Checksum":hash(body),"version":version.to_string()}));
    }
}
impl Remote for Fake {
    fn check(&self) -> Result<()> {
        if self.cancelled.load(Ordering::Acquire) {
            Err(drive::error("cancelled", "Stopped", false))
        } else {
            Ok(())
        }
    }
    fn get(&self, id: &str) -> Result<Value> {
        self.check()?;
        let data = self.data.lock().unwrap();
        if data.denied.contains(id) {
            return Err(drive::error("unavailable", "Unavailable", false));
        }
        let mut value = data
            .files
            .get(id)
            .cloned()
            .ok_or_else(|| drive::error("unavailable", "Unavailable", false))?;
        if value["mimeType"] == FOLDER {
            value["capabilities"] = json!({"canListChildren":true,"canAddChildren":true});
        }
        let mut parents = value["parents"].as_array().cloned().unwrap_or_default();
        let mut seen = BTreeSet::new();
        while let Some(parent) = parents.pop() {
            if !seen.insert(parent.to_string()) {
                break;
            }
            if let Some(v) = parent.as_str().and_then(|p| data.files.get(p)) {
                if v["trashed"] == true {
                    value["trashed"] = json!(true);
                    break;
                }
                parents.extend(v["parents"].as_array().cloned().unwrap_or_default());
            }
        }
        Ok(value)
    }
    fn children(&self, parent: &str) -> Result<Vec<Value>> {
        self.check()?;
        if self.partial.load(Ordering::Acquire) {
            return Err(drive::error("partial_listing", "Incomplete", false));
        }
        let data = self.data.lock().unwrap();
        Ok(data
            .files
            .values()
            .filter(|v| {
                v["parents"]
                    .as_array()
                    .is_some_and(|a| a.contains(&json!(parent)))
                    && v["trashed"] != true
                    && !data.denied.contains(v["id"].as_str().unwrap())
            })
            .cloned()
            .collect())
    }
    fn new_id(&self) -> Result<String> {
        let mut data = self.data.lock().unwrap();
        data.sequence += 1;
        Ok(format!("generated-{}", data.sequence))
    }
    fn create_folder(&self, id: &str, name: &str, parent: &str) -> Result<Value> {
        self.check()?;
        {
            let mut data = self.data.lock().unwrap();
            data.calls.push(("mkdir".into(), id.into()));
            data.files.insert(
                id.into(),
                json!({"id":id,"name":name,"parents":[parent],"mimeType":FOLDER,"version":"1"}),
            );
        }
        self.get(id)
    }
    fn metadata(&self, id: &str, name: &str, parent: &str, _: &Value) -> Result<Value> {
        self.check()?;
        {
            let mut data = self.data.lock().unwrap();
            data.calls.push(("metadata".into(), id.into()));
            let file = data.files.get_mut(id).unwrap();
            file["name"] = json!(name);
            file["parents"] = json!([parent]);
            file["trashed"] = json!(false);
        }
        self.get(id)
    }
    fn trash(&self, id: &str) -> Result<Value> {
        self.check()?;
        {
            let mut data = self.data.lock().unwrap();
            data.calls.push(("trash".into(), id.into()));
            data.files.get_mut(id).unwrap()["trashed"] = json!(true);
        }
        self.get(id)
    }
    fn upload(
        &self,
        id: &str,
        name: &str,
        parent: &str,
        path: &Path,
        digest: &str,
        existing: bool,
        state: &mut Value,
        checkpoint: &mut dyn FnMut(&Value) -> Result<()>,
        progress: &dyn Fn(u64, u64),
    ) -> Result<Value> {
        self.check()?;
        if let Some((store, cid)) = &*self.publish_store.lock().unwrap() {
            let manifest = store.manifest(cid, "upload")?;
            assert!(manifest
                .values
                .values()
                .any(|v| v["remote_id"] == id && (existing || v["complete"] == false)));
        }
        state["session"] = json!(format!("synthetic-{id}"));
        checkpoint(state)?;
        let active = self.active.fetch_add(1, Ordering::AcqRel) + 1;
        self.peak.fetch_max(active, Ordering::AcqRel);
        let barrier = self.barrier.lock().unwrap().clone();
        if let Some(barrier) = barrier {
            barrier.wait();
        }
        if self.cancel_in_upload.load(Ordering::Acquire) {
            self.cancelled.store(true, Ordering::Release);
        }
        let result = (|| {
            self.check()?;
            if self.fail_upload.load(Ordering::Acquire) {
                return Err(drive::error("network", "Disconnected", true));
            }
            let bytes = fs::read(path)?;
            assert_eq!(hash(&bytes), digest);
            self.body(id, name, parent, &bytes);
            self.data
                .lock()
                .unwrap()
                .calls
                .push(("upload".into(), id.into()));
            state.as_object_mut().unwrap().remove("session");
            checkpoint(state)?;
            progress(bytes.len() as u64, bytes.len() as u64);
            self.get(id)
        })();
        self.active.fetch_sub(1, Ordering::AcqRel);
        result
    }
    fn download(&self, item: &Value, path: &Path) -> Result<String> {
        self.check()?;
        let id = item["id"].as_str().unwrap();
        let bytes = self.data.lock().unwrap().bodies[id].clone();
        fs::write(path, &bytes)?;
        self.data
            .lock()
            .unwrap()
            .calls
            .push(("download".into(), id.into()));
        Ok(hash(&bytes))
    }
    fn about(&self) -> Result<Value> {
        Ok(
            json!({"permissionId":"synthetic-user","displayName":"Synthetic","emailAddress":"account-one"}),
        )
    }
}
struct Fixture {
    _temp: tempfile::TempDir,
    root: PathBuf,
    data: PathBuf,
    store: Arc<Store>,
    engine: Engine,
    connection: Value,
    fake: Arc<Fake>,
    sources: Vec<Value>,
}
impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path().canonicalize().unwrap();
        let data = root.join("data");
        let store = Arc::new(Store::new(&data).unwrap());
        let connection = store
            .add(
                "https://drive.google.com/drive/folders/root?resourcekey=key",
                "publisher-self",
            )
            .unwrap();
        let engine = Engine::new(store.clone(), data.clone()).unwrap();
        let vault = root.join("vault");
        fs::create_dir(&vault).unwrap();
        let fake = Arc::new(Fake::new());
        *fake.publish_store.lock().unwrap() =
            Some((store.clone(), connection["id"].as_str().unwrap().into()));
        Self {
            _temp: temp,
            root,
            data,
            store,
            engine,
            connection,
            fake,
            sources: vec![json!({"id":1,"path":vault,"source_type":"folder","label":"Vault"})],
        }
    }
    fn vault(&self) -> PathBuf {
        self.root.join("vault")
    }
    fn publish(&mut self) -> Value {
        self.engine
            .publish(
                &mut self.connection,
                &self.sources,
                self.fake.as_ref(),
                &|_| {},
            )
            .unwrap()
    }
    fn manifest(&self) -> drive::store::Manifest {
        self.store
            .manifest(self.connection["id"].as_str().unwrap(), "upload")
            .unwrap()
    }
    fn received(&self) -> PathBuf {
        self.data
            .join("external-sources/google-drive")
            .join(self.connection["id"].as_str().unwrap())
            .join("peer")
    }
    fn receive(&self) -> Value {
        self.engine
            .receive(&self.connection, "peer", self.fake.as_ref())
            .unwrap()
    }
}
#[test]
fn policy_urls_names_sizes_calendar_and_persistent_versions() {
    let f = Fixture::new();
    assert_eq!(
        policy::root_url("https://drive.google.com/drive/u/0/folders/abc_12?resourcekey=key-1")
            .unwrap(),
        ("abc_12".into(), "key-1".into())
    );
    for value in [
        "abc_12",
        "http://drive.google.com/drive/folders/a",
        "https://drive.google.com.evil.test/drive/folders/a",
        "https://drive.google.com/drive/folders/a?resourcekey=x%2Fy",
        "https://DRIVE.google.com/drive/folders/a",
    ] {
        assert_eq!(policy::root_url(value).unwrap_err().code, "invalid_url")
    }
    for name in [".", "..", "x/escape", "x\\escape", "bad.", "bad ", "a\0"] {
        assert!(policy::safe_name(name).is_err())
    }
    assert_eq!(
        policy::name_key("Ä").unwrap(),
        policy::name_key("A\u{308}").unwrap()
    );
    let now = chrono::DateTime::parse_from_rfc3339("2026-10-28T01:20:00Z")
        .unwrap()
        .to_utc();
    for (minutes, expected) in [
        (15, "01:30"),
        (30, "01:30"),
        (60, "02:00"),
        (180, "03:00"),
        (360, "03:00"),
        (720, "03:00"),
        (1440, "15:00"),
    ] {
        assert_eq!(
            policy::next_slot(now, minutes, "Asia/Seoul")
                .unwrap()
                .format("%H:%M")
                .to_string(),
            expected
        )
    }
    for (at, expected) in [
        ("2026-03-08T06:59:00Z", "2026-03-08T07:00:00+00:00"),
        ("2026-11-01T05:50:00Z", "2026-11-01T06:00:00+00:00"),
    ] {
        let now = chrono::DateTime::parse_from_rfc3339(at).unwrap().to_utc();
        assert_eq!(
            policy::next_slot(now, 60, "America/New_York")
                .unwrap()
                .to_rfc3339(),
            expected
        )
    }
    let path = f.vault().join("limit");
    fs::File::create(&path)
        .unwrap()
        .set_len(policy::MAX_FILE_BYTES)
        .unwrap();
    assert!(policy::local_inventory(&f.sources, &|| false)
        .unwrap()
        .1
        .is_empty());
    fs::OpenOptions::new()
        .write(true)
        .open(&path)
        .unwrap()
        .set_len(policy::MAX_FILE_BYTES + 1)
        .unwrap();
    assert_eq!(
        policy::local_inventory(&f.sources, &|| false)
            .unwrap()
            .1
            .len(),
        1
    );
    f.store
        .put("checkpoint", &json!({"id":"synthetic"}))
        .unwrap();
    assert_eq!(
        Store::new(&f.data)
            .unwrap()
            .get("checkpoint", Value::Null)
            .unwrap()["id"],
        "synthetic"
    );
    let db = rusqlite::Connection::open(&f.store.path).unwrap();
    db.pragma_update(None, "user_version", 9).unwrap();
    assert_eq!(Store::new(&f.data).err().unwrap().code, "state_version");
}
#[test]
fn publish_diffs_moves_stopped_sources_and_failed_retries_preserve_assigned_ids() {
    let mut f = Fixture::new();
    let dir = f.vault().join("one");
    fs::create_dir(&dir).unwrap();
    fs::write(dir.join("a"), b"first").unwrap();
    assert_eq!(f.publish()["transferred"], 1);
    let before = f.manifest().values;
    let remote = before["1:vault/one/a"]["remote_id"]
        .as_str()
        .unwrap()
        .to_owned();
    let repeat = f.publish();
    assert_eq!(
        (
            repeat["transferred"].clone(),
            repeat["changed"].clone(),
            repeat["errors"].clone()
        ),
        (json!(0), json!(0), json!([]))
    );
    assert_eq!(before, f.manifest().values);
    fs::rename(&dir, f.vault().join("two")).unwrap();
    assert_eq!(f.publish()["transferred"], 0);
    assert_eq!(f.manifest().values["1:vault/two/a"]["remote_id"], remote);
    fs::write(f.vault().join("two/a"), b"change").unwrap();
    assert_eq!(f.publish()["transferred"], 1);
    f.engine
        .publish(&mut f.connection, &[], f.fake.as_ref(), &|_| {})
        .unwrap();
    assert_ne!(f.fake.get(&remote).unwrap()["trashed"], true);
    fs::remove_file(f.vault().join("two/a")).unwrap();
    f.publish();
    assert_eq!(f.fake.get(&remote).unwrap()["trashed"], true);
    fs::write(f.vault().join("pending"), b"new").unwrap();
    f.fake.fail_upload.store(true, Ordering::Release);
    assert!(!f.publish()["errors"].as_array().unwrap().is_empty());
    let id = f.manifest().values["1:vault/pending"]["remote_id"].clone();
    f.fake.fail_upload.store(false, Ordering::Release);
    f.engine = Engine::new(f.store.clone(), f.data.clone()).unwrap();
    assert_eq!(f.publish()["errors"], json!([]));
    assert_eq!(f.manifest().values["1:vault/pending"]["remote_id"], id);
    assert!(fs::read_dir(&f.engine.stage).unwrap().next().is_none());
}
#[test]
fn eight_independent_media_workers_overlap_and_checkpoint_only_verified_final_state() {
    let mut f = Fixture::new();
    for index in 0..16 {
        fs::write(f.vault().join(index.to_string()), format!("file-{index}")).unwrap();
    }
    *f.fake.barrier.lock().unwrap() = Some(Arc::new(Barrier::new(8)));
    let result = f.publish();
    assert_eq!(result["errors"], json!([]));
    assert_eq!(result["transferred"], 16);
    assert_eq!(f.fake.peak.load(Ordering::Acquire), 8);
    assert_eq!(f.fake.active.load(Ordering::Acquire), 0);
    assert!(f
        .manifest()
        .values
        .values()
        .all(|v| v["complete"] == true && v.get("session").is_none()));
}
#[test]
fn unavailable_parent_and_incomplete_scan_do_not_authorize_remote_trash() {
    let mut f = Fixture::new();
    fs::write(f.vault().join("old"), "keep").unwrap();
    f.publish();
    let before = f.manifest().values;
    let parent = before["1:vault"]["remote_id"].as_str().unwrap().to_owned();
    let old = before["1:vault/old"]["remote_id"]
        .as_str()
        .unwrap()
        .to_owned();
    f.fake.data.lock().unwrap().denied.insert(parent);
    fs::remove_file(f.vault().join("old")).unwrap();
    fs::write(f.vault().join("new"), "new").unwrap();
    f.fake.partial.store(true, Ordering::Release);
    assert!(!f.publish()["errors"].as_array().unwrap().is_empty());
    assert_ne!(f.fake.get(&old).unwrap()["trashed"], true);
    assert_eq!(f.manifest().values, before);
    fs::rename(f.vault(), f.root.join("moved")).unwrap();
    assert!(f
        .engine
        .publish(&mut f.connection, &f.sources, f.fake.as_ref(), &|_| {})
        .is_err());
    assert_ne!(f.fake.get(&old).unwrap()["trashed"], true);
}
#[test]
fn receive_preserves_unavailable_unmanaged_unsafe_and_unsupported_copies() {
    let f = Fixture::new();
    f.fake
        .create_folder("peer", "publisher-peer", "root")
        .unwrap();
    f.fake.create_folder("dir", "old", "peer").unwrap();
    f.fake.body("doc", "a", "dir", b"hello");
    assert_eq!(f.receive()["transferred"], 1);
    assert_eq!(fs::read(f.received().join("old/a")).unwrap(), b"hello");
    assert_eq!(f.receive()["transferred"], 0);
    {
        let mut data = f.fake.data.lock().unwrap();
        data.files.get_mut("dir").unwrap()["name"] = json!("new");
        data.files.get_mut("doc").unwrap()["name"] = json!("renamed");
    }
    assert_eq!(f.receive()["errors"], json!([]));
    assert!(!f.received().join("old").exists());
    assert_eq!(
        fs::read(f.received().join("new/renamed")).unwrap(),
        b"hello"
    );
    f.fake.data.lock().unwrap().denied.insert("doc".into());
    assert!(!f.receive()["errors"].as_array().unwrap().is_empty());
    assert_eq!(
        fs::read(f.received().join("new/renamed")).unwrap(),
        b"hello"
    );
    f.fake.data.lock().unwrap().denied.clear();
    fs::write(f.received().join("personal"), "unmanaged").unwrap();
    f.fake.body("foreign", "personal", "peer", b"remote");
    assert!(!f.receive()["errors"].as_array().unwrap().is_empty());
    assert_eq!(
        fs::read(f.received().join("personal")).unwrap(),
        b"unmanaged"
    );
    f.fake.data.lock().unwrap().files.insert("native".into(),json!({"id":"native","name":"native","parents":["peer"],"mimeType":"application/vnd.google-apps.document"}));
    assert!(!f.receive()["errors"].as_array().unwrap().is_empty());
    f.fake.trash("doc").unwrap();
    f.receive();
    assert!(!f.received().join("new/renamed").exists());
    assert!(f.received().join("personal").exists());
}
#[test]
fn receive_type_replacement_requires_confirmed_removal_and_recovers_atomic_commit() {
    let f = Fixture::new();
    f.fake.create_folder("peer", "peer", "root").unwrap();
    f.fake.body("old", "replace", "peer", b"old");
    f.receive();
    f.fake.trash("old").unwrap();
    f.fake.create_folder("dir", "replace", "peer").unwrap();
    f.fake.body("child", "child", "dir", b"child");
    assert_eq!(f.receive()["errors"], json!([]));
    assert_eq!(
        fs::read(f.received().join("replace/child")).unwrap(),
        b"child"
    );
    f.fake.trash("dir").unwrap();
    f.fake.body("new", "replace", "peer", b"new");
    assert_eq!(f.receive()["errors"], json!([]));
    assert_eq!(fs::read(f.received().join("replace")).unwrap(), b"new");
    let record = json!({"path":"recovered","kind":"file","hash":hash(b"commit"),"version":"1","complete":true});
    fs::write(f.received().join("recovered"), b"commit").unwrap();
    f.store.put("receive-commit",&json!({"connection_id":f.connection["id"],"publisher_id":"peer","job":"receive:peer","file_id":"recovered","record":record})).unwrap();
    Engine::new(f.store.clone(), f.data.clone()).unwrap();
    assert_eq!(
        f.store
            .manifest(f.connection["id"].as_str().unwrap(), "receive:peer")
            .unwrap()
            .values["recovered"],
        record
    );
    assert_eq!(
        f.store.get("receive-commit", Value::Null).unwrap(),
        Value::Null
    );
}
#[test]
fn service_status_is_cached_binding_is_pinned_and_fixed_slots_skip_missed_runs() {
    let f = Fixture::new();
    fs::write(f.vault().join("a"), "original").unwrap();
    let mut config = Config::for_data_dir(&f.data);
    config.timezone_name = "UTC".into();
    let remote = f.fake.clone();
    let factory: ApiFactory = Arc::new(move |_, _| Ok(remote.clone() as Arc<dyn Remote>));
    let sources = f.sources.clone();
    let loader: SourceLoader = Arc::new(move || Ok(sources.clone()));
    let service = DriveService::new(config, Some(factory), Some(loader), None).unwrap();
    let cid = f.connection["id"].as_str().unwrap();
    service
        .configure(
            cid,
            "upload",
            &json!({"sources":[1],"auto":true,"interval":15}),
        )
        .unwrap();
    assert_eq!(service.store.jobs(cid).unwrap()["upload"]["selected"], true);
    assert!(service
        .configure(cid, "upload", &json!({"sources":[true]}))
        .is_err());
    assert!(service
        .configure(cid, "upload", &json!({"selected":false}))
        .is_err());
    service
        .connected(cid, "account-one", "synthetic-token")
        .unwrap();
    let before = service.store.connection(cid).unwrap();
    assert_eq!(
        service
            .connected(cid, "account-two", "synthetic-token")
            .unwrap_err()
            .code,
        "account_changed"
    );
    assert_eq!(service.store.connection(cid).unwrap(), before);
    let count = f.fake.data.lock().unwrap().calls.len();
    let state = service.status().unwrap();
    assert_eq!(state["auth_mode"], "gcloud");
    assert_eq!(state["connections"][0]["jobs"]["upload"]["auto"], true);
    assert_eq!(f.fake.data.lock().unwrap().calls.len(), count);
    let at = |value: &str| {
        chrono::DateTime::parse_from_rfc3339(value)
            .unwrap()
            .to_utc()
    };
    service
        .schedule_once(at("2026-10-28T10:20:00Z"), "UTC", false)
        .unwrap();
    assert_eq!(
        service
            .store
            .get(&format!("slot:{cid}:upload"), Value::Null)
            .unwrap(),
        Value::Null
    );
    service
        .schedule_once(at("2026-10-28T10:30:00Z"), "UTC", false)
        .unwrap();
    service.wait_idle();
    let job = service.store.jobs(cid).unwrap()["upload"].clone();
    assert_eq!(job["status"], "complete");
    let success = job["last_success"].clone();
    assert!(success.is_string());
    let count = f.fake.data.lock().unwrap().calls.len();
    service
        .schedule_once(at("2026-10-28T10:30:01Z"), "UTC", false)
        .unwrap();
    assert_eq!(f.fake.data.lock().unwrap().calls.len(), count);
    service
        .schedule_once(at("2026-10-28T10:50:00Z"), "UTC", true)
        .unwrap();
    assert_eq!(f.fake.data.lock().unwrap().calls.len(), count);
    f.fake.data.lock().unwrap().denied.insert("root".into());
    service.run(cid, "upload").unwrap();
    service.wait_idle();
    assert_eq!(
        service.store.jobs(cid).unwrap()["upload"]["status"],
        "error"
    );
    assert_eq!(
        service.store.jobs(cid).unwrap()["upload"]["last_success"],
        success
    );
    service.stop();
}
#[test]
fn sdk_credentials_are_memory_only_pinned_and_refreshed_once_for_parallel_workers() {
    use drive::auth::{CommandOutput, CommandRunner, GcloudAuth};
    use std::{ffi::OsString, os::unix::fs::PermissionsExt, time::Duration};
    struct Runner {
        calls: AtomicUsize,
        arguments: Mutex<Vec<Vec<OsString>>>,
    }
    impl CommandRunner for Runner {
        fn run(
            &self,
            argv: &[OsString],
            env: &BTreeMap<OsString, OsString>,
            _: Duration,
            _: &AtomicBool,
        ) -> Result<CommandOutput> {
            self.calls.fetch_add(1, Ordering::AcqRel);
            self.arguments.lock().unwrap().push(argv.to_vec());
            assert!(!env.contains_key(&OsString::from("PYTHONPATH")));
            assert_eq!(
                env[&OsString::from("CLOUDSDK_AUTH_ACCESS_TOKEN")],
                OsString::from("")
            );
            assert_eq!(
                env[&OsString::from("CLOUDSDK_CORE_DISABLE_FILE_LOGGING")],
                OsString::from("true")
            );
            std::thread::sleep(Duration::from_millis(20));
            Ok(CommandOutput {
                code: 0,
                stdout: "synthetic-parallel-token\n".into(),
                stderr: String::new(),
            })
        }
    }
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().canonicalize().unwrap();
    let executable = root.join("synthetic-sdk");
    fs::write(&executable, "fixture; never executed").unwrap();
    fs::set_permissions(&executable, fs::Permissions::from_mode(0o700)).unwrap();
    let mut config = Config::for_data_dir(root.join("data"));
    config.gcloud_path = Some(executable);
    let runner = Arc::new(Runner {
        calls: AtomicUsize::new(0),
        arguments: Mutex::new(vec![]),
    });
    let auth = GcloudAuth::new(
        config.clone(),
        Arc::new(|_| Ok(Some("account-one".into()))),
        Arc::new(|_, _, _| Ok(())),
        Arc::new(|_, _| {}),
        Some(runner.clone()),
    );
    std::thread::scope(|scope| {
        let mut handles = vec![];
        for _ in 0..8 {
            let auth = auth.clone();
            handles.push(scope.spawn(move || auth.access_token("connection").unwrap()));
        }
        for handle in handles {
            assert_eq!(handle.join().unwrap(), "synthetic-parallel-token");
        }
    });
    assert_eq!(runner.calls.load(Ordering::Acquire), 1);
    assert_eq!(
        runner.arguments.lock().unwrap()[0][3],
        OsString::from("--account=account-one")
    );
    auth.invalidate("connection").unwrap();
    auth.access_token("connection").unwrap();
    assert_eq!(runner.calls.load(Ordering::Acquire), 2);
    auth.stop();
    assert_eq!(
        auth.access_token("connection").unwrap_err().code,
        "cancelled"
    );
    assert!(!config.data_dir.exists());
    for value in ["-account", "with space", "x\u{1c}y", ""] {
        assert!(drive::auth::account_name(value).is_err())
    }
    let error = drive::auth::sdk_error("invalid_grant PRIVATE-EMAIL SECRET-TOKEN");
    assert_eq!(error.code, "reauth");
    assert!(!error.message.contains("PRIVATE"));
    assert!(!error.message.contains("SECRET"));
}

#[test]
fn cancelled_parallel_workers_settle_before_stale_copy_deletion() {
    let mut f = Fixture::new();
    let old = f.vault().join("old");
    fs::write(&old, "keep").unwrap();
    f.publish();
    let remote = f.manifest().values["1:vault/old"]["remote_id"]
        .as_str()
        .unwrap()
        .to_owned();
    fs::remove_file(old).unwrap();
    for i in 0..16 {
        fs::write(f.vault().join(i.to_string()), "new").unwrap();
    }
    *f.fake.barrier.lock().unwrap() = Some(Arc::new(Barrier::new(8)));
    f.fake.cancel_in_upload.store(true, Ordering::Release);
    let caught = f
        .engine
        .publish(&mut f.connection, &f.sources, f.fake.as_ref(), &|_| {})
        .unwrap_err();
    assert_eq!(caught.code, "cancelled");
    assert_eq!(f.fake.active.load(Ordering::Acquire), 0);
    assert_ne!(f.fake.data.lock().unwrap().files[&remote]["trashed"], true);
    assert!(fs::read_dir(&f.engine.stage).unwrap().next().is_none());
}
