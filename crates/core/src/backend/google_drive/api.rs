//! Pinned Google endpoints with bounded media, explicit retries and resumable recovery.
use super::{
    array, error, number,
    policy::{self, FOLDER, MAX_FILE_BYTES},
    require, retryable, text,
};
use crate::backend::{BackendError, Result};
use md5::{Digest, Md5};
use serde_json::{json, Value};
use sha2::Sha256;
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::File,
    io::{Read, Seek, SeekFrom, Write},
    path::Path,
    sync::{Arc, LazyLock, Mutex},
    time::Duration,
};
pub const BASE: &str = "https://www.googleapis.com/drive/v3/";
pub const UPLOAD: &str = "https://www.googleapis.com/upload/drive/v3/files";
pub const BATCH: &str = "https://www.googleapis.com/batch/drive/v3";
pub const FIELDS:&str="id,name,mimeType,parents,size,md5Checksum,sha256Checksum,version,trashed,resourceKey,driveId,capabilities,appProperties";
pub const MULTIPART_BYTES: u64 = 5_000_000;
type BatchResponse = (BTreeMap<String, Result<Value>>, bool);
static QUERY_RESOURCE_ID: LazyLock<regex::Regex> =
    LazyLock::new(|| regex::Regex::new("'([A-Za-z0-9_-]+)'").unwrap());
static BATCH_STATUS: LazyLock<regex::Regex> =
    LazyLock::new(|| regex::Regex::new(r"^HTTP/\d(?:\.\d)?\s+(\d{3})\b").unwrap());
pub struct Request {
    pub method: String,
    pub url: String,
    pub headers: BTreeMap<String, String>,
    pub body: Vec<u8>,
}
pub struct Response {
    pub code: u16,
    pub headers: BTreeMap<String, String>,
    pub body: Box<dyn Read + Send>,
}
impl Response {
    pub fn header(&self, name: &str) -> &str {
        self.headers
            .iter()
            .find(|(k, _)| k.eq_ignore_ascii_case(name))
            .map(|(_, v)| v.as_str())
            .unwrap_or("")
    }
    fn bytes(&mut self, limit: u64) -> Result<Vec<u8>> {
        let mut bytes = Vec::new();
        self.body
            .by_ref()
            .take(limit)
            .read_to_end(&mut bytes)
            .map_err(|_| network())?;
        Ok(bytes)
    }
}
pub trait Transport: Send + Sync {
    fn open(&self, request: Request) -> Result<Response>;
    fn close(&self) {}
}
pub struct NativeTransport {
    client: Mutex<Option<reqwest::blocking::Client>>,
}
impl NativeTransport {
    pub fn new() -> Result<Self> {
        let client = reqwest::blocking::Client::builder()
            .timeout(Duration::from_secs(30))
            .pool_max_idle_per_host(policy::PUBLISH_WORKERS)
            .redirect(reqwest::redirect::Policy::none())
            .build()
            .map_err(|_| network())?;
        Ok(Self {
            client: Mutex::new(Some(client)),
        })
    }
}
impl Transport for NativeTransport {
    fn open(&self, request: Request) -> Result<Response> {
        let client = self
            .client
            .lock()
            .unwrap()
            .clone()
            .ok_or_else(|| error("cancelled", "Google 연결을 중단했습니다.", false))?;
        let mut builder = client
            .request(
                reqwest::Method::from_bytes(request.method.as_bytes()).map_err(|_| network())?,
                &request.url,
            )
            .body(request.body);
        for (k, v) in request.headers {
            builder = builder.header(k, v)
        }
        let response=builder.send().map_err(|e|{let mut cause:Option<&(dyn std::error::Error+'static)>=Some(&e);while let Some(value)=cause{let lower=value.to_string().to_ascii_lowercase();if lower.contains("certificate")||lower.contains("unknownissuer")||lower.contains("unknown issuer"){return error("tls","Google 연결의 인증서를 확인하지 못했습니다. 이 기기의 신뢰 인증서와 네트워크 설정을 확인해 주세요.",false)}cause=value.source();}network()})?;
        let code = response.status().as_u16();
        let headers = response
            .headers()
            .iter()
            .map(|(k, v)| (k.as_str().into(), v.to_str().unwrap_or("").into()))
            .collect();
        Ok(Response {
            code,
            headers,
            body: Box::new(response),
        })
    }
    fn close(&self) {
        self.client.lock().unwrap().take();
    }
}
fn network() -> BackendError {
    error(
        "network",
        "Google Drive에 연결하지 못했습니다. 연결 상태를 확인해 주세요.",
        true,
    )
}
pub fn api_error(status: u16, body: &Value, operation: &str) -> BackendError {
    let reason = body["error"]["errors"][0]["reason"].as_str().unwrap_or("");
    match status{401=>error("reauth","Google 연결을 다시 확인해 주세요. 필요한 경우 다시 로그인해 주세요.",false),429=>error("rate_limit","Google API 호출 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.",true),_ if status>=500=>error("google_service","Google Drive 요청을 완료하지 못했습니다. 잠시 후 다시 시도해 주세요.",true),404=>error("unavailable","현재 Google 계정으로 이 폴더·파일을 확인할 수 없습니다. URL과 공유 권한을 확인해 주세요.",false),_=>match reason{"rateLimitExceeded"|"userRateLimitExceeded"|"dailyLimitExceeded"=>error("rate_limit","Google API 호출 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.",true),"insufficientFilePermissions"=>{let label=match operation{"create"=>"새 폴더·파일을 추가","update"=>"파일을 수정","rename"=>"항목의 이름을 변경","move"=>"항목을 이동","restore"=>"항목을 복원","trash"=>"항목을 휴지통으로 이동",_=>"요청한 작업을 실행"};error("permission",&format!("이 위치에서 {label}할 수 없습니다. 대상의 편집 권한을 확인해 주세요."),false)},"storageQuotaExceeded"|"teamDriveFileLimitExceeded"=>error("google_quota","Google Drive 저장 한도를 확인해 주세요.",false),"insufficientPermissions"|"appNotAuthorizedToFile"=>error("scope","gcloud 로그인에 Drive 접근 권한이 필요합니다. Google 로그인을 다시 진행해 주세요.",false),_=>error("google_request","Google Drive 요청을 완료하지 못했습니다. 대상과 앱 권한을 확인해 주세요.",false)}}
}
pub trait Remote: Send + Sync {
    fn check(&self) -> Result<()>;
    fn get(&self, id: &str) -> Result<Value>;
    fn children(&self, id: &str) -> Result<Vec<Value>>;
    fn new_id(&self) -> Result<String>;
    fn create_folder(&self, id: &str, name: &str, parent: &str) -> Result<Value>;
    fn metadata(&self, id: &str, name: &str, parent: &str, current: &Value) -> Result<Value>;
    fn trash(&self, id: &str) -> Result<Value>;
    #[expect(
        clippy::too_many_arguments,
        reason = "Preserves the explicit service boundary and existing caller contract."
    )]
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
    ) -> Result<Value>;
    fn download(&self, metadata: &Value, destination: &Path) -> Result<String>;
    fn about(&self) -> Result<Value>;
    fn set_key(&self, _id: &str, _key: &str) {}
    fn prefetch(&self, ids: &[String], progress: &dyn Fn(usize, usize)) -> Result<()> {
        self.check()?;
        progress(0, ids.len());
        Ok(())
    }
    fn invalidate(&self, _ids: &[String]) {}
    fn close(&self) {}
}
type Token = Arc<dyn Fn() -> Result<String> + Send + Sync>;
type Cancel = Arc<dyn Fn() -> bool + Send + Sync>;
type Refresh = Arc<dyn Fn() -> Result<()> + Send + Sync>;
#[derive(Default)]
struct State {
    keys: BTreeMap<String, String>,
    ids: Vec<String>,
    metadata: BTreeMap<String, std::result::Result<Value, BackendError>>,
}
pub struct API {
    token: Token,
    cancel: Cancel,
    refresh: Option<Refresh>,
    transport: Arc<dyn Transport>,
    owns_transport: bool,
    root_keys: BTreeSet<String>,
    state: Mutex<State>,
    pub sleeper: Arc<dyn Fn(f64) + Send + Sync>,
    pub multipart_bytes: u64,
}
impl API {
    pub fn new(
        token: Token,
        keys: BTreeMap<String, String>,
        cancel: Cancel,
        refresh: Option<Refresh>,
        transport: Option<Arc<dyn Transport>>,
    ) -> Result<Self> {
        let root_keys = keys.keys().cloned().collect();
        let owns_transport = transport.is_none();
        Ok(Self {
            token,
            cancel,
            refresh,
            transport: match transport {
                Some(t) => t,
                None => Arc::new(NativeTransport::new()?),
            },
            owns_transport,
            root_keys,
            state: Mutex::new(State {
                keys,
                ..State::default()
            }),
            sleeper: Arc::new(|seconds| std::thread::sleep(Duration::from_secs_f64(seconds))),
            multipart_bytes: MULTIPART_BYTES,
        })
    }
    pub fn identifier(value: &str) -> Result<&str> {
        require(
            policy::identifier(value),
            "identifier",
            "Google 항목 식별자를 확인하지 못했습니다.",
        )?;
        Ok(value)
    }
    #[expect(
        clippy::too_many_arguments,
        reason = "Preserves the explicit service boundary and existing caller contract."
    )]
    pub fn request(
        &self,
        method: &str,
        path: &str,
        query: &BTreeMap<String, String>,
        data: Option<&Value>,
        bytes: Option<&[u8]>,
        headers: &BTreeMap<String, String>,
        operation: &str,
        accepted: &[u16],
        resource_ids: &[&str],
    ) -> Result<Response> {
        let mut url = if path.starts_with("https://") {
            path.to_owned()
        } else {
            format!("{BASE}{path}")
        };
        let parsed = url::Url::parse(&url)
            .map_err(|_| error("endpoint", "Google API 주소를 확인하지 못했습니다.", false))?;
        let authority = url
            .strip_prefix("https://")
            .and_then(|s| s.split(['/', '?', '#']).next());
        let allowed = parsed.path().starts_with("/drive/v3/")
            || parsed.path().starts_with("/upload/drive/v3/")
            || (method == "POST" && url == BATCH);
        require(
            parsed.scheme() == "https" && authority == Some("www.googleapis.com") && allowed,
            "endpoint",
            "Google API 주소를 확인하지 못했습니다.",
        )?;
        if !query.is_empty() {
            url.push(if url.contains('?') { '&' } else { '?' });
            let pairs = query
                .iter()
                .map(|(k, v)| (k.as_str(), v.clone()))
                .collect::<Vec<_>>();
            url.push_str(&crate::backend::search::urlencode(&pairs))
        }
        let body = match data {
            Some(v) => crate::backend::json::encode_http(v)?.into_bytes(),
            None => bytes.unwrap_or(&[]).to_vec(),
        };
        let mut last = network();
        for attempt in 0..4 {
            self.check()?;
            let mut request_headers = headers.clone();
            request_headers.insert(
                "Authorization".into(),
                format!("Bearer {}", (self.token)()?),
            );
            if data.is_some() {
                request_headers.insert(
                    "Content-Type".into(),
                    "application/json; charset=utf-8".into(),
                );
            }
            let keys = self.state.lock().unwrap().keys.clone();
            if !keys.is_empty() {
                let mut relevant = self.root_keys.clone();
                relevant.insert(parsed.path().rsplit('/').next().unwrap_or("").into());
                relevant.extend(resource_ids.iter().map(|s| s.to_string()));
                if let Some(q) = query.get("q") {
                    for cap in QUERY_RESOURCE_ID.captures_iter(q) {
                        relevant.insert(cap[1].into());
                    }
                }
                if let Some(v) = data {
                    relevant.extend(
                        array(&v["parents"])
                            .iter()
                            .filter_map(Value::as_str)
                            .map(str::to_owned),
                    );
                }
                for name in ["addParents", "removeParents"] {
                    if let Some(v) = query.get(name) {
                        relevant.extend(v.split(',').map(str::to_owned));
                    }
                }
                request_headers.insert(
                    "X-Goog-Drive-Resource-Keys".into(),
                    relevant
                        .iter()
                        .filter_map(|id| {
                            keys.get(id)
                                .filter(|key| !key.is_empty())
                                .map(|key| format!("{id}/{key}"))
                        })
                        .collect::<Vec<_>>()
                        .join(","),
                );
            }
            match self.transport.open(Request {
                method: method.into(),
                url: url.clone(),
                headers: request_headers,
                body: body.clone(),
            }) {
                Ok(response)
                    if (200..300).contains(&response.code) || accepted.contains(&response.code) =>
                {
                    return Ok(response)
                }
                Ok(mut response) => {
                    let code = response.code;
                    let payload = response
                        .bytes(65536)
                        .ok()
                        .and_then(|b| {
                            std::str::from_utf8(&b)
                                .ok()
                                .and_then(|s| crate::backend::json::decode(s).ok())
                        })
                        .unwrap_or(json!({}));
                    last = api_error(code, &payload, operation);
                    if code == 401 && attempt == 0 {
                        if let Some(refresh) = &self.refresh {
                            refresh()?;
                            continue;
                        }
                    }
                }
                Err(e) => last = e,
            }
            if !retryable(&last) || !matches!(method, "GET" | "PATCH") || attempt == 3 {
                return Err(last);
            }
            (self.sleeper)(((1u64 << attempt).min(8)) as f64 + jitter());
        }
        Err(last)
    }
    fn json_request(
        &self,
        method: &str,
        path: &str,
        query: BTreeMap<String, String>,
        data: Option<&Value>,
        operation: &str,
    ) -> Result<Value> {
        let mut response = self.request(
            method,
            path,
            &query,
            data,
            None,
            &BTreeMap::new(),
            operation,
            &[],
            &[],
        )?;
        let raw = response.bytes(4_000_000)?;
        std::str::from_utf8(&raw)
            .ok()
            .and_then(|s| crate::backend::json::decode(s).ok())
            .ok_or_else(|| {
                error(
                    "response",
                    "Google Drive 응답을 확인하지 못했습니다. 기존 사본을 보존합니다.",
                    false,
                )
            })
    }
    fn media_result(mut response: Response) -> Value {
        response
            .bytes(1_000_000)
            .ok()
            .and_then(|b| {
                std::str::from_utf8(&b)
                    .ok()
                    .and_then(|s| crate::backend::json::decode(s).ok())
            })
            .filter(Value::is_object)
            .unwrap_or(json!({}))
    }
    fn acknowledged(response: &Response, size: u64) -> Result<u64> {
        let range = response.header("Range");
        let received = if range.is_empty() {
            Some(0)
        } else {
            range
                .strip_prefix("bytes=0-")
                .filter(|n| !n.is_empty() && n.bytes().all(|b| b.is_ascii_digit()))
                .and_then(|n| n.parse::<u64>().ok())
                .and_then(|n| n.checked_add(1))
        };
        require(
            received.is_some_and(|n| n <= size),
            "upload_offset",
            "Google 업로드 진행 상태를 확인하지 못했습니다.",
        )?;
        Ok(received.unwrap())
    }
    #[expect(
        clippy::too_many_arguments,
        reason = "Preserves the explicit service boundary and existing caller contract."
    )]
    fn resumable_upload(
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
        let size = path.metadata()?.len();
        let mut session = if state["upload_hash"] == digest {
            text(state, "session").to_owned()
        } else {
            String::new()
        };
        let mut probe = !session.is_empty();
        if session.is_empty() {
            let mut metadata = json!({"name":name});
            if !existing {
                metadata["id"] = json!(id);
                metadata["parents"] = json!([parent])
            }
            let response = self.request(
                if existing { "PATCH" } else { "POST" },
                &format!(
                    "{UPLOAD}{}",
                    if existing {
                        format!("/{}", Self::identifier(id)?)
                    } else {
                        String::new()
                    }
                ),
                &map(&[
                    ("uploadType", "resumable"),
                    ("supportsAllDrives", "true"),
                    ("fields", FIELDS),
                ]),
                Some(&metadata),
                None,
                &map(&[
                    ("X-Upload-Content-Length", &size.to_string()),
                    ("X-Upload-Content-Type", "application/octet-stream"),
                ]),
                if existing { "update" } else { "create" },
                &[],
                &[],
            )?;
            session = response.header("Location").into();
            state["session"] = json!(session);
            state["upload_hash"] = json!(digest);
            checkpoint(state)?;
        }
        let (mut failures, mut stalled, mut offset) = (0, 0, 0);
        loop {
            self.check()?;
            if probe {
                let response = self.request(
                    "PUT",
                    &session,
                    &BTreeMap::new(),
                    None,
                    Some(b""),
                    &map(&[("Content-Range", &format!("bytes */{size}"))]),
                    "read",
                    &[308, 404, 410],
                    &[],
                )?;
                if matches!(response.code, 200 | 201) {
                    return Ok(Self::media_result(response));
                }
                if matches!(response.code, 404 | 410) {
                    state.as_object_mut().unwrap().remove("session");
                    checkpoint(state)?;
                    return Err(error(
                        "upload_expired",
                        "업로드 세션이 만료되었습니다. 다음 실행에서 이어서 확인합니다.",
                        true,
                    ));
                }
                offset = Self::acknowledged(&response, size)?;
                progress(offset, size);
                probe = false
            }
            let mut file = File::open(path)?;
            file.seek(SeekFrom::Start(offset))?;
            let mut chunk = Vec::new();
            file.take((1024 * 1024).min(size - offset))
                .read_to_end(&mut chunk)?;
            let mut headers = map(&[("Content-Type", "application/octet-stream")]);
            if !chunk.is_empty() {
                headers.insert(
                    "Content-Range".into(),
                    format!("bytes {offset}-{}/{size}", offset + chunk.len() as u64 - 1),
                );
            }
            match self.request(
                "PUT",
                &session,
                &BTreeMap::new(),
                None,
                Some(&chunk),
                &headers,
                "read",
                &[308],
                &[],
            ) {
                Ok(response) => {
                    if matches!(response.code, 200 | 201) {
                        return Ok(Self::media_result(response));
                    }
                    let next = Self::acknowledged(&response, size)?;
                    if next <= offset {
                        stalled += 1;
                        if stalled >= 3 {
                            return Err(error("upload_stalled","업로드 수신량이 늘지 않아 중단했습니다. 연결 상태를 확인하고 다시 실행하면 이어서 확인합니다.",false));
                        }
                        probe = true;
                        (self.sleeper)((1u64 << (stalled - 1)) as f64)
                    } else {
                        offset = next;
                        stalled = 0;
                        progress(offset, size)
                    }
                    failures = 0
                }
                Err(e) => {
                    if !retryable(&e) || failures >= 3 {
                        return Err(e);
                    }
                    (self.sleeper)((1u64 << failures) as f64 + jitter());
                    failures += 1;
                    probe = true
                }
            }
        }
    }
}
fn map(pairs: &[(&str, &str)]) -> BTreeMap<String, String> {
    pairs
        .iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect()
}
fn jitter() -> f64 {
    let bytes = uuid::Uuid::new_v4();
    f64::from(u32::from_le_bytes(
        bytes.as_bytes()[..4].try_into().unwrap(),
    )) / (u32::MAX as f64 + 1.0)
}
impl Remote for API {
    fn check(&self) -> Result<()> {
        require(!(self.cancel)(), "cancelled", "동기화를 중단했습니다.")
    }
    fn about(&self) -> Result<Value> {
        Ok(
            self.json_request("GET", "about", map(&[("fields", "user")]), None, "read")?["user"]
                .clone(),
        )
    }
    fn get(&self, id: &str) -> Result<Value> {
        self.check()?;
        if let Some(value) = self.state.lock().unwrap().metadata.remove(id) {
            return value;
        }
        let value = self.json_request(
            "GET",
            &format!("files/{}", Self::identifier(id)?),
            map(&[("fields", FIELDS), ("supportsAllDrives", "true")]),
            None,
            "read",
        )?;
        if !text(&value, "resourceKey").is_empty() {
            self.set_key(text(&value, "id"), text(&value, "resourceKey"))
        }
        Ok(value)
    }
    fn children(&self, parent: &str) -> Result<Vec<Value>> {
        let mut page = String::new();
        let mut seen = BTreeSet::new();
        let mut result = Vec::new();
        loop {
            let mut query = map(&[
                (
                    "q",
                    &format!(
                        "'{}' in parents and trashed = false",
                        Self::identifier(parent)?
                    ),
                ),
                (
                    "fields",
                    &format!("nextPageToken,incompleteSearch,files({FIELDS})"),
                ),
                ("pageSize", "1000"),
                ("supportsAllDrives", "true"),
                ("includeItemsFromAllDrives", "true"),
            ]);
            if !page.is_empty() {
                query.insert("pageToken".into(), page);
            }
            let value = self.json_request("GET", "files", query, None, "read")?;
            require(
                value["incompleteSearch"] != true && value["files"].is_array(),
                "partial_listing",
                "폴더 목록을 모두 확인하지 못했습니다. 기존 사본을 보존합니다.",
            )?;
            for item in array(&value["files"]) {
                if !text(item, "resourceKey").is_empty() {
                    self.set_key(text(item, "id"), text(item, "resourceKey"));
                }
            }
            result.extend_from_slice(array(&value["files"]));
            page = text(&value, "nextPageToken").into();
            if page.is_empty() {
                return Ok(result);
            }
            require(
                seen.insert(page.clone()),
                "partial_listing",
                "폴더 목록이 완전하지 않습니다. 기존 사본을 보존합니다.",
            )?
        }
    }
    fn new_id(&self) -> Result<String> {
        let empty = self.state.lock().unwrap().ids.is_empty();
        if empty {
            let value = self.json_request(
                "GET",
                "files/generateIds",
                map(&[("count", "100"), ("space", "drive"), ("type", "files")]),
                None,
                "read",
            )?;
            self.state.lock().unwrap().ids = array(&value["ids"])
                .iter()
                .filter_map(Value::as_str)
                .map(str::to_owned)
                .collect();
        }
        let id = self.state.lock().unwrap().ids.pop().ok_or_else(|| {
            error(
                "response",
                "Google 파일 식별자를 준비하지 못했습니다.",
                false,
            )
        })?;
        Self::identifier(&id)?;
        Ok(id)
    }
    fn create_folder(&self, id: &str, name: &str, parent: &str) -> Result<Value> {
        self.invalidate(&[id.into()]);
        match self.json_request(
            "POST",
            "files",
            map(&[("fields", FIELDS), ("supportsAllDrives", "true")]),
            Some(&json!({"id":id,"name":name,"mimeType":FOLDER,"parents":[parent]})),
            "create",
        ) {
            Ok(v) => Ok(v),
            Err(e) => {
                if let Ok(v) = self.get(id) {
                    if v["name"] == name
                        && array(&v["parents"]).contains(&json!(parent))
                        && v["trashed"] != true
                        && v["mimeType"] == FOLDER
                    {
                        return Ok(v);
                    }
                }
                Err(e)
            }
        }
    }
    fn metadata(&self, id: &str, name: &str, parent: &str, current: &Value) -> Result<Value> {
        self.invalidate(&[id.into()]);
        let mut query = map(&[("fields", FIELDS), ("supportsAllDrives", "true")]);
        let mut operation = if current["trashed"] == true {
            "restore"
        } else {
            "rename"
        };
        if current["parents"] != json!([parent]) {
            query.insert("addParents".into(), parent.into());
            query.insert(
                "removeParents".into(),
                array(&current["parents"])
                    .iter()
                    .filter_map(Value::as_str)
                    .collect::<Vec<_>>()
                    .join(","),
            );
            operation = "move"
        }
        self.json_request(
            "PATCH",
            &format!("files/{}", Self::identifier(id)?),
            query,
            Some(&json!({"name":name,"trashed":false})),
            operation,
        )
    }
    fn trash(&self, id: &str) -> Result<Value> {
        self.invalidate(&[id.into()]);
        self.json_request(
            "PATCH",
            &format!("files/{}", Self::identifier(id)?),
            map(&[("fields", FIELDS), ("supportsAllDrives", "true")]),
            Some(&json!({"trashed":true})),
            "trash",
        )
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
        self.invalidate(&[id.into()]);
        let size = path.metadata()?.len();
        require(
            size <= MAX_FILE_BYTES,
            "too_large",
            "앱의 파일당 100MB 제한을 초과합니다.",
        )?;
        let mut result = if size <= self.multipart_bytes
            && !(state
                .get("session")
                .is_some_and(|v| !v.is_null() && v != "")
                && state["upload_hash"] == digest)
        {
            let mut media = Vec::new();
            File::open(path)?
                .take(self.multipart_bytes + 1)
                .read_to_end(&mut media)?;
            require(
                media.len() as u64 == size,
                "source_changed",
                "전송 전에 업로드 사본의 크기가 바뀌었습니다. 다시 비교해 주세요.",
            )?;
            let boundary = format!("localbrain_{}", uuid::Uuid::new_v4().simple());
            let mut metadata = json!({"name":name});
            if !existing {
                metadata["id"] = json!(id);
                metadata["parents"] = json!([parent])
            }
            let mut body=format!("--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{}\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n",crate::backend::json::encode_http(&metadata)?).into_bytes();
            body.extend(media);
            body.extend(format!("\r\n--{boundary}--\r\n").as_bytes());
            let request = self.request(
                if existing { "PATCH" } else { "POST" },
                &format!(
                    "{UPLOAD}{}",
                    if existing {
                        format!("/{}", Self::identifier(id)?)
                    } else {
                        String::new()
                    }
                ),
                &map(&[
                    ("uploadType", "multipart"),
                    ("supportsAllDrives", "true"),
                    ("fields", FIELDS),
                ]),
                None,
                Some(&body),
                &map(&[(
                    "Content-Type",
                    &format!("multipart/related; boundary={boundary}"),
                )]),
                if existing { "update" } else { "create" },
                &[],
                &[parent, id],
            );
            let request = request.and_then(|mut response| {
                let bytes = response.bytes(4_000_000)?;
                std::str::from_utf8(&bytes)
                    .ok()
                    .and_then(|s| crate::backend::json::decode(s).ok())
                    .ok_or_else(|| {
                        error(
                            "response",
                            "Google Drive 응답을 확인하지 못했습니다. 기존 사본을 보존합니다.",
                            false,
                        )
                    })
            });
            match request {
                Ok(value) => value,
                Err(e) => {
                    if !retryable(&e) && e.code != "response" {
                        return Err(e);
                    }
                    match self.get(id) {
                        Ok(v) if v["md5Checksum"] == digest && number(&v["size"]) == Some(size) => {
                            v
                        }
                        _ => return Err(e),
                    }
                }
            }
        } else {
            self.resumable_upload(
                id, name, parent, path, digest, existing, state, checkpoint, progress,
            )?
        };
        if result["md5Checksum"] != digest || number(&result["size"]) != Some(size) {
            result = self.get(id)?
        }
        require(
            result["md5Checksum"] == digest && number(&result["size"]) == Some(size),
            "integrity",
            "전송한 내용의 일치를 확인하지 못했습니다. 완료로 기록하지 않습니다.",
        )?;
        state.as_object_mut().unwrap().remove("session");
        state.as_object_mut().unwrap().remove("upload_hash");
        checkpoint(state)?;
        progress(size, size);
        Ok(result)
    }
    fn download(&self, metadata: &Value, destination: &Path) -> Result<String> {
        require(
            number(&metadata["size"]).is_none_or(|n| n <= MAX_FILE_BYTES),
            "too_large",
            "앱의 파일당 100MB 제한을 초과합니다. 기존 사본을 보존합니다.",
        )?;
        let mut response = self.request(
            "GET",
            &format!("files/{}", Self::identifier(text(metadata, "id"))?),
            &map(&[("alt", "media"), ("supportsAllDrives", "true")]),
            None,
            None,
            &BTreeMap::new(),
            "read",
            &[],
            &[],
        )?;
        let (mut md5, mut sha, mut total) = (Md5::new(), Sha256::new(), 0);
        let mut output = File::create(destination)?;
        loop {
            self.check()?;
            let mut buffer = vec![0; ((1024 * 1024).min(MAX_FILE_BYTES - total + 1)) as usize];
            let n = response.body.read(&mut buffer).map_err(|_| network())?;
            if n == 0 {
                break;
            }
            total += n as u64;
            require(
                total <= MAX_FILE_BYTES,
                "too_large",
                "수신 중 파일당 100MB 제한을 초과했습니다. 기존 사본을 보존합니다.",
            )?;
            output.write_all(&buffer[..n])?;
            md5.update(&buffer[..n]);
            sha.update(&buffer[..n]);
        }
        require(
            number(&metadata["size"]).is_none_or(|n| n == total),
            "integrity",
            "다운로드 크기가 원격 정보와 다릅니다. 기존 사본을 보존합니다.",
        )?;
        let digest = format!("{:x}", md5.finalize());
        let verified = if !text(metadata, "md5Checksum").is_empty() {
            digest == metadata["md5Checksum"]
        } else if !text(metadata, "sha256Checksum").is_empty() {
            format!("{:x}", sha.finalize()) == metadata["sha256Checksum"]
        } else {
            false
        };
        require(
            verified,
            "integrity",
            "다운로드 내용의 일치를 확인하지 못했습니다. 기존 사본을 보존합니다.",
        )?;
        let after = self.get(text(metadata, "id"))?;
        if after["trashed"] == true
            || after["version"] != metadata["version"]
            || after["md5Checksum"] != metadata["md5Checksum"]
        {
            return Err(error(
                "source_changed",
                "다운로드 중 원본이 바뀌었습니다. 다음 실행에서 다시 비교합니다.",
                true,
            ));
        }
        Ok(digest)
    }
    fn set_key(&self, id: &str, key: &str) {
        self.state
            .lock()
            .unwrap()
            .keys
            .insert(id.into(), key.into());
    }
    fn invalidate(&self, ids: &[String]) {
        let mut state = self.state.lock().unwrap();
        for id in ids {
            state.metadata.remove(id);
        }
    }
    fn prefetch(&self, ids: &[String], progress: &dyn Fn(usize, usize)) -> Result<()> {
        self.check()?;
        let mut seen = BTreeSet::new();
        let mut identifiers = Vec::new();
        for id in ids {
            Self::identifier(id)?;
            if seen.insert(id) {
                identifiers.push(id.clone());
            }
        }
        self.state.lock().unwrap().metadata.clear();
        let mut completed = 0;
        for batch in identifiers.chunks(100) {
            self.check()?;
            let boundary = format!("localbrain_{}", uuid::Uuid::new_v4().simple());
            let keys = self.state.lock().unwrap().keys.clone();
            let mut expected = BTreeMap::new();
            let mut body = Vec::new();
            for (index, id) in batch.iter().enumerate() {
                let content_id = format!("localbrain-{index}");
                expected.insert(format!("response-{content_id}"), id.clone());
                let path = format!(
                    "/drive/v3/files/{id}?{}",
                    crate::backend::search::urlencode(&[
                        ("fields", FIELDS.into()),
                        ("supportsAllDrives", "true".into())
                    ])
                );
                let mut relevant = self.root_keys.clone();
                relevant.insert(id.clone());
                let key_header = relevant
                    .iter()
                    .filter_map(|id| {
                        keys.get(id)
                            .filter(|v| !v.is_empty())
                            .map(|key| format!("{id}/{key}"))
                    })
                    .collect::<Vec<_>>()
                    .join(",");
                let header = if key_header.is_empty() {
                    String::new()
                } else {
                    format!("X-Goog-Drive-Resource-Keys: {key_header}\r\n")
                };
                body.extend(format!("--{boundary}\r\nContent-Type: application/http\r\nContent-ID: <{content_id}>\r\n\r\nGET {path} HTTP/1.1\r\n{header}\r\n").as_bytes());
            }
            body.extend(format!("--{boundary}--\r\n").as_bytes());
            let result = (|| -> Result<BatchResponse> {
                let mut response = self.request(
                    "POST",
                    BATCH,
                    &BTreeMap::new(),
                    None,
                    Some(&body),
                    &map(&[(
                        "Content-Type",
                        &format!("multipart/mixed; boundary={boundary}"),
                    )]),
                    "read",
                    &[],
                    &[],
                )?;
                let content_type = response.header("Content-Type").to_owned();
                let raw = response.bytes(8_000_001)?;
                require(raw.len() <= 8_000_000, "response", "Invalid batch")?;
                parse_batch(&content_type, &raw, &expected)
            })();
            match result {
                Ok((values, reauth)) => {
                    self.check()?;
                    if reauth {
                        if let Some(refresh) = &self.refresh {
                            refresh()?;
                        }
                    }
                    completed += values.len();
                    let mut state = self.state.lock().unwrap();
                    for value in values.values().filter_map(|v| v.as_ref().ok()) {
                        if !text(value, "resourceKey").is_empty() {
                            state.keys.insert(
                                text(value, "id").into(),
                                text(value, "resourceKey").into(),
                            );
                        }
                    }
                    state.metadata.extend(values);
                }
                Err(e) if ["cancelled", "reauth", "scope", "tls"].contains(&e.code.as_str()) => {
                    return Err(e)
                }
                Err(_) => {}
            }
            progress(completed, identifiers.len());
        }
        Ok(())
    }
    fn close(&self) {
        if self.owns_transport {
            self.transport.close()
        }
    }
}
impl Drop for API {
    fn drop(&mut self) {
        self.close()
    }
}

/// Strict correlation keeps a malformed or partial batch from becoming absence evidence.
fn parse_batch(
    content_type: &str,
    raw: &[u8],
    expected: &BTreeMap<String, String>,
) -> Result<BatchResponse> {
    let invalid = || error("response", "Invalid batch", false);
    let mut fields = content_type.split(';');
    require(
        fields
            .next()
            .is_some_and(|s| s.trim().eq_ignore_ascii_case("multipart/mixed")),
        "response",
        "Invalid batch",
    )?;
    let boundary = fields
        .find_map(|field| {
            field
                .trim()
                .split_once('=')
                .filter(|(k, _)| k.eq_ignore_ascii_case("boundary"))
                .map(|(_, v)| v.trim().trim_matches('"'))
        })
        .filter(|v| !v.is_empty() && !v.contains(['\r', '\n']))
        .ok_or_else(invalid)?;
    let raw = std::str::from_utf8(raw).map_err(|_| invalid())?;
    let normalized = raw.replace("\r\n", "\n");
    let marker = format!("--{boundary}");
    let mut parts = normalized.split(&marker);
    require(
        parts.next().is_some_and(|v| v.trim().is_empty()),
        "response",
        "Invalid batch",
    )?;
    let (mut seen, mut values, mut reauth, mut ended) =
        (BTreeSet::new(), BTreeMap::new(), false, false);
    for part in parts {
        if let Some(ending) = part.strip_prefix("--") {
            require(ending.trim().is_empty(), "response", "Invalid batch")?;
            ended = true;
            break;
        }
        let part = part.strip_prefix('\n').ok_or_else(invalid)?;
        let (headers, payload) = part.split_once("\n\n").ok_or_else(invalid)?;
        let headers = headers
            .lines()
            .map(|s| {
                s.split_once(':')
                    .ok_or_else(invalid)
                    .map(|(k, v)| (k.to_ascii_lowercase(), v.trim()))
            })
            .collect::<Result<BTreeMap<_, _>>>()?;
        let content_id = headers
            .get("content-id")
            .map(|v| v.trim().trim_matches(['<', '>']))
            .ok_or_else(invalid)?;
        require(
            expected.contains_key(content_id)
                && seen.insert(content_id.to_owned())
                && headers
                    .get("content-type")
                    .is_some_and(|v| v.eq_ignore_ascii_case("application/http")),
            "response",
            "Invalid batch",
        )?;
        let (status, payload) = payload.split_once("\n\n").ok_or_else(invalid)?;
        let line = status.lines().next().ok_or_else(invalid)?;
        let captures = BATCH_STATUS.captures(line).ok_or_else(invalid)?;
        let status = captures[1].parse::<u16>().map_err(|_| invalid())?;
        let value = crate::backend::json::decode(payload.trim_end()).map_err(|_| invalid())?;
        let id = &expected[content_id];
        match status {
            200 => {
                require(
                    value.is_object() && value["id"] == *id,
                    "response",
                    "Invalid batch",
                )?;
                values.insert(id.clone(), Ok(value));
            }
            403 | 404 => {
                let err = api_error(status, &value, "read");
                if ["permission", "unavailable", "google_request"].contains(&err.code.as_str()) {
                    values.insert(id.clone(), Err(err));
                }
            }
            401 => reauth = true,
            _ => {}
        }
    }
    require(
        ended && seen.len() == expected.len(),
        "response",
        "Invalid batch",
    )?;
    Ok((values, reauth))
}
