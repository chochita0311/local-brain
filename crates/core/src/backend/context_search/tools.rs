//! Read-only tools scoped to server-admitted sources; original files remain external.
use super::{chars, require};
use crate::backend::{
    db, models, sources::registry::PythonText, storage::files, unicode, Config, Result,
};
use rusqlite::{Connection, OpenFlags};
use serde_json::{json, Value};
#[cfg(unix)]
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::{
    collections::BTreeMap,
    fs::{self, OpenOptions},
    io::Read,
    path::{Component, Path, PathBuf},
    time::{Duration, Instant},
};
pub const MAX_READ: usize = 2 * 1024 * 1024;
pub const MAX_FILES: usize = 5000;
pub const MAX_MATCHES: usize = 40;
pub const MAX_TEXT: usize = 10000;
pub const MAX_SEARCH_BYTES: usize = 32 * 1024 * 1024;
/// Reading received folders never constructs/initializes a Drive store or authenticates.
pub trait DriveCatalog: Send + Sync {
    fn connections(&self) -> Result<Value>;
    fn get(&self, key: &str, default: Value) -> Result<Value>;
    fn jobs(&self, id: &str) -> Result<Value>;
}
fn database(path: &Path) -> Result<Connection> {
    let db = Connection::open_with_flags(files::resolve(path)?, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
    db.busy_timeout(Duration::from_secs(10))?;
    Ok(db)
}
fn symlink(path: &Path) -> bool {
    fs::symlink_metadata(path).is_ok_and(|m| m.file_type().is_symlink())
}
fn s<'a>(value: &'a Value, key: &str) -> &'a str {
    value[key].as_str().unwrap_or("")
}
fn valid_id(value: &str) -> bool {
    !value.is_empty()
        && value
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || c == b'-' || c == b'_')
}
pub fn source_catalog(config: &Config, drive: Option<&dyn DriveCatalog>) -> Result<Vec<Value>> {
    let excluded = [
        &config.data_dir,
        &config.cache_dir,
        &config.development_dir,
        &models::hub_cache_root(config)?,
    ]
    .into_iter()
    .map(|p| files::resolve(p))
    .collect::<Result<Vec<_>>>()?;
    let connection = database(&config.database_path)?;
    let mut sources = Vec::new();
    for row in db::rows(&connection,"SELECT id,label,path,source_type FROM context_roots WHERE enabled=1 AND readable=1 ORDER BY id",[])? {
  let path=Path::new(s(&row,"path"));let name=row["label"].as_str().filter(|s|!s.is_empty()).unwrap_or_else(||path.file_name().and_then(|s|s.to_str()).unwrap_or(""));
  let mut source=json!({"id":format!("context-{}",row["id"]),"name":name,"kind":"local","context_id":row["id"],"database":config.database_path});
  match s(&row,"source_type") {"apple_notes"=>{source["mode"]=json!("documents");sources.push(source)},kind@("folder"|"file")=>{
   let candidate=files::resolve(&files::expand(path,config))?;let expected=if kind=="file" {candidate.is_file()}else{candidate.is_dir()};
   if expected&&!excluded.iter().any(|root|candidate.starts_with(root)) {source["mode"]=json!("files");source["root"]=json!(candidate);source["single_file"]=json!(kind=="file");source["excluded"]=json!(excluded);sources.push(source)}
  },_=>{}}
 }
    if let Some(drive) = drive {
        for connection in drive.connections()?.as_array().into_iter().flatten() {
            let id = s(connection, "id");
            let publishers = drive.get(&format!("publishers:{id}"), json!([]))?;
            for (key, job) in drive.jobs(id)?.as_object().into_iter().flatten() {
                let Some(publisher) = key.strip_prefix("receive:") else {
                    continue;
                };
                if !valid_id(id) || !valid_id(publisher) {
                    continue;
                }
                let root = config
                    .data_dir
                    .join("external-sources/google-drive")
                    .join(id)
                    .join(publisher);
                if root.is_dir() && !root.ancestors().take(3).any(symlink) {
                    let digest =
                        localbrain_models::assets::sha256(format!("{id}:{publisher}").as_bytes());
                    let name = publishers
                        .as_array()
                        .into_iter()
                        .flatten()
                        .find(|p| s(p, "id") == publisher)
                        .and_then(|p| p.get("name"))
                        .cloned()
                        .unwrap_or(json!("받은 폴더"));
                    sources.push(json!({"id":format!("drive-{}",&digest[..16]),"name":name,"kind":"received","mode":"files","root":files::resolve(&root)?,"single_file":false,"observed_at":job.get("last_success"),"syncing":truth(job.get("selected"))}));
                }
            }
        }
    }
    Ok(sources)
}
pub fn public_sources(sources: &[Value]) -> Vec<Value> {
    sources
        .iter()
        .map(|s| {
            let mut v = serde_json::Map::new();
            for key in ["id", "name", "kind", "observed_at", "syncing"] {
                if let Some(value) = s.get(key) {
                    v.insert(key.into(), value.clone());
                }
            }
            Value::Object(v)
        })
        .collect()
}
pub(crate) fn truth(v: Option<&Value>) -> bool {
    v.is_some_and(|v| match v {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
        Value::Number(n) => n.to_string() != "0",
    })
}
pub struct FileTools {
    sources: Vec<Value>,
    pub evidence: Vec<Value>,
    keys: BTreeMap<(String, String, String, usize), usize>,
    walk_limited: bool,
}
impl FileTools {
    pub fn new(sources: &[Value]) -> Result<Self> {
        let mut normalized = Vec::new();
        for source in sources {
            let mut source = source.clone();
            if !s(&source, "root").is_empty() {
                source["root"] = json!(files::resolve(Path::new(s(&source, "root")))?)
            }
            if let Some(index) = normalized
                .iter()
                .position(|v: &Value| v["id"] == source["id"])
            {
                normalized[index] = source
            } else {
                normalized.push(source)
            }
        }
        Ok(Self {
            sources: normalized,
            evidence: Vec::new(),
            keys: BTreeMap::new(),
            walk_limited: false,
        })
    }
    fn source(&self, key: Option<&Value>) -> Result<Value> {
        let source = key
            .and_then(Value::as_str)
            .and_then(|key| self.sources.iter().find(|v| s(v, "id") == key));
        require(source.is_some(), "선택된 자료 범위에서 소스를 골라 주세요.")?;
        Ok(source.unwrap().clone())
    }
    fn path(&self, source: &Value, relative: &str) -> Result<PathBuf> {
        let root = Path::new(s(source, "root"));
        let rel = Path::new(relative);
        require(
            !relative.is_empty()
                && !rel.is_absolute()
                && !rel.components().any(|c| match c {
                    Component::ParentDir => true,
                    Component::Normal(p) => p.to_string_lossy().starts_with(".localbrain-drive-"),
                    _ => false,
                }),
            "자료 안의 상대 파일 경로를 지정해 주세요.",
        )?;
        require(
            !symlink(root) && files::resolve(root)? == root,
            "자료 경로가 바뀌어 읽지 않았습니다.",
        )?;
        let single = source["single_file"].as_bool().unwrap_or(root.is_file());
        require(
            single == root.is_file(),
            "선택한 자료의 파일·폴더 유형이 바뀌었습니다.",
        )?;
        let boundary = if single {
            root.parent().unwrap_or(root)
        } else {
            root
        };
        require(
            !single || Some(relative) == root.file_name().and_then(|s| s.to_str()),
            "선택한 파일만 읽을 수 있습니다.",
        )?;
        let mut current = boundary.to_owned();
        for part in rel.components() {
            current.push(part);
            require(!symlink(&current), "링크 경로는 읽지 않습니다.")?
        }
        let path = boundary.join(relative);
        let resolved = files::resolve(&path)?;
        require(
            resolved.starts_with(files::resolve(boundary)?) && path.is_file(),
            "자료 안의 읽을 수 있는 파일을 선택해 주세요.",
        )?;
        require(
            !source["excluded"]
                .as_array()
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .any(|p| resolved.starts_with(p)),
            "앱 런타임·공용 모델 캐시는 자료로 읽지 않습니다.",
        )?;
        Ok(path)
    }
    fn list(&mut self, source: &Value) -> Result<Vec<(String, String)>> {
        if source["mode"] == "documents" {
            return db::rows(&database(Path::new(s(source,"database")))?,"SELECT id,title FROM context_documents WHERE context_root_id=? ORDER BY id LIMIT ?",rusqlite::params![source["context_id"].as_i64(),(MAX_FILES+1)as i64])?.iter().map(|r|Ok((format!("document-{}",r["id"]),s(r,"title").to_owned()))).collect();
        }
        let root = Path::new(s(source, "root"));
        require(
            !symlink(root) && files::resolve(root)? == root,
            "자료 경로가 바뀌었습니다.",
        )?;
        require(
            source["single_file"].as_bool().unwrap_or(root.is_file()) == root.is_file(),
            "선택한 자료의 파일·폴더 유형이 바뀌었습니다.",
        )?;
        if root.is_file() {
            let name = root.file_name().unwrap().to_string_lossy().into_owned();
            return Ok(vec![(name.clone(), name)]);
        }
        require(root.is_dir(), "자료 폴더를 읽을 수 없습니다.")?;
        let mut found = Vec::new();
        let mut pending = vec![root.to_owned()];
        let started = Instant::now();
        let mut walked = 0;
        while let Some(parent) = pending.pop() {
            walked += 1;
            if walked > MAX_FILES || started.elapsed() > Duration::from_secs(2) {
                self.walk_limited = true;
                break;
            }
            let entries = match fs::read_dir(&parent) {
                Ok(v) => v,
                Err(_) => {
                    self.walk_limited = true;
                    continue;
                }
            };
            let (mut dirs, mut regular) = (Vec::new(), Vec::new());
            for entry in entries {
                let Ok(entry) = entry else {
                    self.walk_limited = true;
                    continue;
                };
                let path = entry.path();
                if symlink(&path) {
                    continue;
                }
                if path.is_dir() {
                    let resolved = files::resolve(&path)?;
                    if !source["excluded"]
                        .as_array()
                        .into_iter()
                        .flatten()
                        .filter_map(Value::as_str)
                        .any(|p| resolved.starts_with(p))
                    {
                        dirs.push(path)
                    }
                } else if path.is_file()
                    && !entry
                        .file_name()
                        .to_string_lossy()
                        .starts_with(".localbrain-drive-")
                {
                    regular.push(path)
                }
            }
            dirs.sort();
            regular.sort();
            pending.extend(dirs.into_iter().rev());
            for path in regular {
                found.push((
                    path.strip_prefix(root)
                        .unwrap()
                        .to_string_lossy()
                        .into_owned(),
                    path.file_name().unwrap().to_string_lossy().into_owned(),
                ));
                if found.len() > MAX_FILES {
                    return Ok(found);
                }
            }
        }
        Ok(found)
    }
    fn text(&self, source: &Value, relative: &str) -> Result<(String, bool, String)> {
        if source["mode"] == "documents" {
            let id = relative
                .strip_prefix("document-")
                .filter(|s| !s.is_empty() && s.chars().all(unicode::python_digit))
                .and_then(|s| s.parse::<i64>().ok());
            require(id.is_some(), "문서 목록의 파일 식별자를 사용해 주세요.")?;
            let row=db::row(&database(Path::new(s(source,"database")))?,"SELECT substr(d.body,1,?) body,length(d.body) size,d.mtime_ns FROM context_documents d JOIN context_roots r ON r.id=d.context_root_id WHERE d.id=? AND r.id=? AND r.enabled=1 AND r.readable=1",rusqlite::params![MAX_READ as i64,id,source["context_id"].as_i64()])?;
            require(row.is_some(), "현재 읽을 수 없는 문서입니다.")?;
            let row = row.unwrap();
            return Ok((
                s(&row, "body").to_owned(),
                row["size"].as_u64().unwrap_or(0) > MAX_READ as u64,
                row["mtime_ns"].to_string(),
            ));
        }
        let path = self.path(source, relative)?;
        let before = fs::metadata(&path)?;
        let mut options = OpenOptions::new();
        options.read(true);
        #[cfg(unix)]
        options.custom_flags(libc::O_NOFOLLOW);
        let file = options.open(&path)?;
        require(
            stamp(&file.metadata()?) == stamp(&before),
            "읽기 전에 자료가 바뀌었습니다.",
        )?;
        let mut raw = Vec::new();
        file.take(MAX_READ as u64 + 1).read_to_end(&mut raw)?;
        self.path(source, relative)?;
        let after = fs::metadata(&path)?;
        require(
            stamp(&before) == stamp(&after),
            "읽는 중 자료가 바뀌었습니다. 다시 읽어 주세요.",
        )?;
        let partial = raw.len() > MAX_READ;
        let version = mtime(&before).to_string();
        match decode_text(&raw[..raw.len().min(MAX_READ)], !partial) {
            Ok(text) => Ok((text, partial, version)),
            Err(_) => {
                if source.get("context_id").is_some()
                    && path
                        .extension()
                        .is_some_and(|v| v.eq_ignore_ascii_case("pdf"))
                {
                    let row=db::row(&database(Path::new(s(source,"database")))?,"SELECT substr(body,1,?) body,length(body) size FROM context_documents WHERE context_root_id=? AND path=? AND mtime_ns=?",rusqlite::params![MAX_READ as i64,source["context_id"].as_i64(),path.to_string_lossy(),mtime(&before).to_string()])?;
                    if let Some(row) = row.filter(|row| !s(row, "body").is_empty()) {
                        return Ok((
                            s(&row, "body").to_owned(),
                            row["size"].as_u64().unwrap_or(0) > MAX_READ as u64,
                            version,
                        ));
                    }
                }
                require(false, "이 파일은 현재 텍스트로 읽을 수 없습니다.")?;
                unreachable!()
            }
        }
    }
    fn reference(
        &mut self,
        source: &Value,
        path: &str,
        line: usize,
        text: &str,
        version: &str,
    ) -> Value {
        let key = (
            s(source, "id").to_owned(),
            path.into(),
            version.into(),
            line,
        );
        let next = self.evidence.len();
        let index = *self.keys.entry(key).or_insert(next);
        let value = json!({"ref":format!("S{}",index+1),"source":source["name"],"path":path,"line":line,"text":chars(text,1600),"version":version});
        if index == next {
            self.evidence.push(value.clone())
        } else {
            self.evidence[index] = value.clone()
        }
        value
    }
    pub fn call(&mut self, name: &str, arguments: &Value) -> Result<Value> {
        let args = arguments.as_object();
        require(args.is_some(), "도구 인자를 확인해 주세요.")?;
        let args = args.unwrap();
        let allowed = |keys: &[&str]| args.keys().all(|k| keys.contains(&k.as_str()));
        match name {
            "list_sources" => {
                require(args.is_empty(), "자료 목록에는 인자가 필요하지 않습니다.")?;
                Ok(json!({"sources":public_sources(&self.sources)}))
            }
            "list_files" => {
                require(
                    allowed(&["source", "offset"]),
                    "파일 목록 인자를 확인해 주세요.",
                )?;
                let source = self.source(args.get("source"))?;
                let offset = args
                    .get("offset")
                    .unwrap_or(&Value::from(0))
                    .as_u64()
                    .filter(|n| *n <= MAX_FILES as u64);
                require(offset.is_some(), "파일 목록 위치를 확인해 주세요.")?;
                let offset = offset.unwrap() as usize;
                let files = self.list(&source)?;
                Ok(
                    json!({"source":source["id"],"offset":offset,"files":files.iter().take(MAX_FILES).skip(offset).take(150).map(|(p,n)|json!({"path":p,"name":n})).collect::<Vec<_>>(),"next_offset":if files.len().min(MAX_FILES)>offset+150 {Some(offset+150)}else{None},"limited":self.walk_limited||files.len()>MAX_FILES}),
                )
            }
            "search_text" => {
                require(allowed(&["query", "source"]), "검색 인자를 확인해 주세요.")?;
                let query = args
                    .get("query")
                    .and_then(Value::as_str)
                    .filter(|q| !q.py_trim().is_empty() && q.chars().count() <= 200);
                require(query.is_some(), "짧은 검색어를 지정해 주세요.")?;
                let query = unicode::casefold(query.unwrap());
                let sources = if args.contains_key("source") {
                    vec![self.source(args.get("source"))?]
                } else {
                    self.sources.clone()
                };
                let (mut matches, mut scanned, mut unreadable, mut limited, mut total) =
                    (Vec::new(), 0, 0, false, 0);
                let started = Instant::now();
                for source in sources {
                    let files = match self.list(&source) {
                        Ok(files) => files,
                        Err(_) => {
                            unreadable += 1;
                            limited = true;
                            continue;
                        }
                    };
                    limited |= self.walk_limited || files.len() > MAX_FILES;
                    for (relative, _) in files.iter().take(MAX_FILES) {
                        if scanned + unreadable >= MAX_FILES
                            || total >= MAX_SEARCH_BYTES
                            || started.elapsed() >= Duration::from_secs(6)
                        {
                            return Ok(
                                json!({"matches":matches,"scanned":scanned,"unreadable":unreadable,"limited":true}),
                            );
                        }
                        let (text, partial, version) = match self.text(&source, relative) {
                            Ok(value) => value,
                            Err(_) => {
                                unreadable += 1;
                                continue;
                            }
                        };
                        scanned += 1;
                        total += text.len();
                        limited |= partial;
                        let lines = unicode::splitlines(&text);
                        if let Some(index) = lines
                            .iter()
                            .position(|line| unicode::casefold(line).contains(&query))
                        {
                            let start = index.saturating_sub(2);
                            let excerpt =
                                chars(&lines[start..lines.len().min(index + 3)].join("\n"), 1600);
                            let mut value =
                                self.reference(&source, relative, start + 1, &excerpt, &version);
                            value["source_id"] = source["id"].clone();
                            value["match_line"] = json!(index + 1);
                            matches.push(value)
                        }
                        if matches.len() >= MAX_MATCHES {
                            return Ok(
                                json!({"matches":matches,"scanned":scanned,"unreadable":unreadable,"limited":true}),
                            );
                        }
                    }
                }
                Ok(
                    json!({"matches":matches,"scanned":scanned,"unreadable":unreadable,"limited":limited}),
                )
            }
            "read_file" => {
                require(
                    allowed(&["source", "path", "start_line", "end_line"]),
                    "읽기 인자를 확인해 주세요.",
                )?;
                let source = self.source(args.get("source"))?;
                let relative = args.get("path").and_then(Value::as_str);
                let start = args.get("start_line").unwrap_or(&Value::from(1)).as_u64();
                let end = args.get("end_line").unwrap_or(&Value::from(100)).as_u64();
                require(
                    relative.is_some()
                        && start
                            .zip(end)
                            .is_some_and(|(s, e)| s >= 1 && s <= e && e <= s.saturating_add(199)),
                    "파일과 최대200줄의 읽기 구간을 지정해 주세요.",
                )?;
                let (relative, start, end) = (
                    relative.unwrap(),
                    start.unwrap() as usize,
                    end.unwrap() as usize,
                );
                let (text, partial, version) = self.text(&source, relative)?;
                let lines = unicode::splitlines(&text);
                let chunk = lines
                    .iter()
                    .skip(start - 1)
                    .take(end - start + 1)
                    .copied()
                    .collect::<Vec<_>>()
                    .join("\n");
                if chunk.is_empty() {
                    return Ok(
                        json!({"text":"","limited":partial,"message":"해당 구간에 읽을 내용이 없습니다."}),
                    );
                }
                let mut value = self.reference(&source, relative, start, &chunk, &version);
                value["text"] = json!(chars(&chunk, MAX_TEXT));
                value["source_id"] = source["id"].clone();
                value["limited"] =
                    json!(partial || chunk.chars().count() > MAX_TEXT || end < lines.len());
                Ok(value)
            }
            _ => {
                require(false, "허용되지 않은 도구입니다.")?;
                unreachable!()
            }
        }
    }
}
#[cfg(unix)]
fn mtime(meta: &fs::Metadata) -> i128 {
    meta.mtime() as i128 * 1_000_000_000 + meta.mtime_nsec() as i128
}
#[cfg(unix)]
fn stamp(meta: &fs::Metadata) -> (u64, u64, u64, i128) {
    (meta.dev(), meta.ino(), meta.len(), mtime(meta))
}
fn decode_text(raw: &[u8], final_chunk: bool) -> Result<String> {
    if raw.starts_with(b"\xff\xfe") || raw.starts_with(b"\xfe\xff") {
        let little = raw.starts_with(b"\xff\xfe");
        let mut words = raw[2..]
            .chunks_exact(2)
            .map(|b| {
                if little {
                    u16::from_le_bytes([b[0], b[1]])
                } else {
                    u16::from_be_bytes([b[0], b[1]])
                }
            })
            .collect::<Vec<_>>();
        if !final_chunk && words.last().is_some_and(|w| (0xd800..=0xdbff).contains(w)) {
            words.pop();
        }
        require(!final_chunk || raw.len().is_multiple_of(2), "UTF16")?;
        return String::from_utf16(&words).map_err(|_| super::error("TOOL", "UTF16"));
    }
    require(!raw.iter().take(8192).any(|b| *b == 0), "BINARY")?;
    let raw = raw.strip_prefix(b"\xef\xbb\xbf").unwrap_or(raw);
    match std::str::from_utf8(raw) {
        Ok(s) => Ok(s.into()),
        Err(error) if !final_chunk && error.error_len().is_none() => {
            Ok(std::str::from_utf8(&raw[..error.valid_up_to()])
                .unwrap()
                .into())
        }
        Err(_) => Err(super::error("TOOL", "UTF8")),
    }
}
pub fn tool_schemas() -> Vec<Value> {
    serde_json::from_str(include_str!("tool-schemas.json")).expect("static tool schemas")
}
