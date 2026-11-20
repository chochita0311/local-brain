//! Versioned private sync metadata; no credentials or document text are stored.
use super::{
    array, error,
    policy::{is_symlink, private_dir, root_url, safe_name},
    require, text,
};
use crate::backend::{db, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Map, Value};
use std::os::unix::fs::PermissionsExt;
use std::{
    collections::BTreeSet,
    fs,
    path::{Path, PathBuf},
    sync::Mutex,
    time::Duration,
};
#[derive(Clone, Default)]
pub struct Manifest {
    pub values: Map<String, Value>,
    dirty: BTreeSet<String>,
}
impl Manifest {
    pub fn insert(&mut self, key: String, value: Value) {
        self.dirty.insert(key.clone());
        self.values.insert(key, value);
    }
    pub fn remove(&mut self, key: &str) -> Option<Value> {
        self.dirty.insert(key.into());
        self.values.remove(key)
    }
    pub fn get(&self, key: &str) -> Option<&Value> {
        self.values.get(key)
    }
    pub fn is_dirty(&self) -> bool {
        !self.dirty.is_empty()
    }
}
pub struct Store {
    pub root: PathBuf,
    pub path: PathBuf,
    lock: Mutex<()>,
}
impl Store {
    pub fn new(data: &Path) -> Result<Self> {
        let root = private_dir(&data.join("google-drive"))?;
        let path = root.join("sync.sqlite3");
        require(
            !is_symlink(&path),
            "unsafe_path",
            "동기화 상태 파일의 링크를 처리할 수 없습니다.",
        )?;
        let store = Self {
            root,
            path,
            lock: Mutex::new(()),
        };
        store.with_db(|db|{let version:i64=db.query_row("PRAGMA user_version",[],|r|r.get(0))?;require(matches!(version,0|1),"state_version","지원하지 않는 Drive 상태 버전입니다. 기존 상태를 보존합니다.")?;db.execute_batch("CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value TEXT NOT NULL);CREATE TABLE IF NOT EXISTS items(namespace TEXT NOT NULL,key TEXT NOT NULL,value TEXT NOT NULL,PRIMARY KEY(namespace,key));PRAGMA user_version=1;")?;Ok(())})?;
        fs::set_permissions(&store.path, fs::Permissions::from_mode(0o600))?;
        Ok(store)
    }
    fn with_db<T>(&self, f: impl FnOnce(&Connection) -> Result<T>) -> Result<T> {
        let _lock = self.lock.lock().unwrap();
        require(
            !is_symlink(&self.path),
            "unsafe_path",
            "동기화 상태 파일의 링크를 처리할 수 없습니다.",
        )?;
        let db = Connection::open(&self.path)?;
        db.busy_timeout(Duration::from_secs(10))?;
        db.execute_batch("BEGIN")?;
        match f(&db) {
            Ok(value) => {
                db.execute_batch("COMMIT")?;
                Ok(value)
            }
            Err(e) => {
                let _ = db.execute_batch("ROLLBACK");
                Err(e)
            }
        }
    }
    fn get_db(db: &Connection, key: &str, default: Value) -> Result<Value> {
        let row = db::row(db, "SELECT value FROM state WHERE key=?", [key])?;
        row.map(|v| crate::backend::json::decode(text(&v, "value")))
            .unwrap_or(Ok(default))
    }
    fn put_db(db: &Connection, key: &str, value: &Value) -> Result<()> {
        db.execute(
            "INSERT INTO state VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            params![key, crate::backend::json::encode_http(value)?],
        )?;
        Ok(())
    }
    pub fn get(&self, key: &str, default: Value) -> Result<Value> {
        self.with_db(|db| Self::get_db(db, key, default))
    }
    pub fn put(&self, key: &str, value: &Value) -> Result<()> {
        self.with_db(|db| Self::put_db(db, key, value))
    }
    pub fn connections(&self) -> Result<Value> {
        self.get("connections", json!([]))
    }
    pub fn connection(&self, id: &str) -> Result<Value> {
        array(&self.connections()?)
            .iter()
            .find(|v| text(v, "id") == id)
            .cloned()
            .ok_or_else(|| error("missing_connection", "저장된 연결을 선택해 주세요.", false))
    }
    pub fn add(&self, url: &str, target: &str) -> Result<Value> {
        let (root_id, key) = root_url(url)?;
        safe_name(target)?;
        self.with_db(|db|{let mut connections=Self::get_db(db,"connections",json!([]))?;require(!array(&connections).iter().any(|c|c["root_id"]==root_id),"duplicate_root","이미 등록한 루트입니다. 기존 연결을 선택해 주세요.")?;let value=json!({"id":uuid::Uuid::new_v4().simple().to_string(),"url":url,"root_id":root_id,"resource_key":key,"target":target,"target_id":null,"account":null});connections.as_array_mut().ok_or_else(||error("state_version","지원하지 않는 Drive 상태 버전입니다. 기존 상태를 보존합니다.",false))?.push(value.clone());Self::put_db(db,"connections",&connections)?;Ok(value)})
    }
    pub fn update_connection(&self, connection: &Value) -> Result<()> {
        self.with_db(|db| {
            let connections = Self::get_db(db, "connections", json!([]))?;
            Self::put_db(
                db,
                "connections",
                &json!(array(&connections)
                    .iter()
                    .map(|c| if c["id"] == connection["id"] {
                        connection
                    } else {
                        c
                    })
                    .collect::<Vec<_>>()),
            )
        })
    }
    pub fn jobs(&self, id: &str) -> Result<Value> {
        self.get(
            &format!("jobs:{id}"),
            json!({"upload":{"selected":false,"auto":false,"interval":360,"sources":[]}}),
        )
    }
    pub fn save_jobs(&self, id: &str, jobs: &Value) -> Result<()> {
        self.put(&format!("jobs:{id}"), jobs)
    }
    pub fn manifest(&self, id: &str, job: &str) -> Result<Manifest> {
        self.with_db(|db| {
            let mut values = Map::new();
            for row in db::rows(
                db,
                "SELECT key,value FROM items WHERE namespace=?",
                [format!("{id}:{job}")],
            )? {
                values.insert(
                    text(&row, "key").into(),
                    crate::backend::json::decode(text(&row, "value"))?,
                );
            }
            Ok(Manifest {
                values,
                dirty: BTreeSet::new(),
            })
        })
    }
    pub fn checkpoint(
        &self,
        id: &str,
        job: &str,
        entries: &mut Manifest,
        touched: Option<&str>,
    ) -> Result<()> {
        let mut keys = entries.dirty.clone();
        if let Some(key) = touched.filter(|key| entries.values.contains_key(*key)) {
            keys.insert(key.into());
        }
        self.with_db(|db|{for key in &keys{if let Some(value)=entries.values.get(key){db.execute("INSERT INTO items VALUES(?,?,?) ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value",params![format!("{id}:{job}"),key,crate::backend::json::encode_http(value)?])?;}else{db.execute("DELETE FROM items WHERE namespace=? AND key=?",params![format!("{id}:{job}"),key])?;}}Ok(())})?;
        entries.dirty.clear();
        Ok(())
    }
}
impl crate::backend::context_search::tools::DriveCatalog for Store {
    fn connections(&self) -> Result<Value> {
        self.connections()
    }
    fn get(&self, key: &str, default: Value) -> Result<Value> {
        self.get(key, default)
    }
    fn jobs(&self, id: &str) -> Result<Value> {
        self.jobs(id)
    }
}
