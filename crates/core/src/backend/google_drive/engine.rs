//! Explicit directional mirrors. Durable assigned IDs precede remote mutations;
//! complete scans and confirmed source removals alone authorize deletion.
use super::{
    api::Remote,
    array, error, number,
    policy::*,
    require,
    store::{Manifest, Store},
    text,
};
use crate::backend::Result;
use md5::{Digest, Md5};
use serde_json::{json, Map, Value};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    path::{Path, PathBuf},
    sync::Arc,
};
pub fn content_hash(path: &Path) -> Result<String> {
    let mut digest = Md5::new();
    let mut file = File::open(path)?;
    let mut buffer = vec![0; 1024 * 1024];
    loop {
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        digest.update(&buffer[..n]);
    }
    Ok(format!("{:x}", digest.finalize()))
}
pub fn remote_inventory(api: &dyn Remote, folder: &str) -> Result<Map<String, Value>> {
    let mut entries = Map::new();
    let mut seen = BTreeSet::from([folder.to_owned()]);
    let mut pending = vec![(folder.to_owned(), String::new())];
    while let Some((parent, prefix)) = pending.pop() {
        let mut names = BTreeSet::new();
        for mut item in api.children(&parent)? {
            let name = safe_name(text(&item, "name"))?.to_owned();
            require(
                names.insert(name_key(&name)?) && seen.insert(text(&item, "id").into()),
                "duplicate_path",
                "원격 폴더의 중복 이름·경로를 안전하게 동기화할 수 없습니다.",
            )?;
            let relative = format!("{prefix}{name}");
            let folder = item["mimeType"] == FOLDER;
            item["path"] = json!(relative);
            item["kind"] = json!(if folder { "folder" } else { "file" });
            if folder {
                require(
                    item["capabilities"]["canListChildren"] != false,
                    "partial_listing",
                    "읽을 수 없는 하위 폴더가 있어 기존 사본을 보존합니다.",
                )?;
                pending.push((text(&item, "id").into(), format!("{relative}/")));
            }
            entries.insert(text(&item, "id").into(), item);
        }
    }
    Ok(entries)
}
pub struct Engine {
    pub store: Arc<Store>,
    pub data_dir: PathBuf,
    pub stage: PathBuf,
}
impl Engine {
    pub fn new(store: Arc<Store>, data_dir: PathBuf) -> Result<Self> {
        let stage = private_dir(&store.root.join("staging"))?;
        for entry in fs::read_dir(&stage)? {
            let entry = entry?;
            if entry.file_name().to_string_lossy().starts_with("snapshot-")
                && entry.path().is_file()
                && !is_symlink(&entry.path())
            {
                fs::remove_file(entry.path())?;
            }
        }
        let pending = store.get("download-staging", json!([]))?;
        let copies = data_dir.join("external-sources/google-drive");
        for name in array(&pending).iter().filter_map(Value::as_str) {
            let path = Path::new(name);
            if path.starts_with(&copies)
                && path
                    .file_name()
                    .is_some_and(|n| n.to_string_lossy().starts_with(".localbrain-drive-"))
            {
                if let Ok(relative) = path.strip_prefix(&copies) {
                    if let Ok(checked) = local_path(&copies, &relative.to_string_lossy()) {
                        let owned = checked.metadata().is_ok_and(|m| {
                            m.is_file() && m.nlink() == 1 && m.uid() == unsafe { libc::getuid() }
                        });
                        if owned {
                            let _ = fs::remove_file(checked);
                        }
                    }
                }
            }
        }
        store.put("download-staging", &json!([]))?;
        let engine = Self {
            store,
            data_dir,
            stage,
        };
        engine.recover_commit()?;
        Ok(engine)
    }
    pub fn recover_commit(&self) -> Result<()> {
        let pending = self.store.get("receive-commit", Value::Null)?;
        if pending.is_null() {
            return Ok(());
        }
        let root = self
            .data_dir
            .join("external-sources/google-drive")
            .join(text(&pending, "connection_id"))
            .join(text(&pending, "publisher_id"));
        let record = &pending["record"];
        let target = local_path(&root, text(record, "path"))?;
        if target.is_file()
            && target.metadata()?.len() <= MAX_FILE_BYTES
            && content_hash(&target)? == record["hash"]
        {
            let mut manifest = self
                .store
                .manifest(text(&pending, "connection_id"), text(&pending, "job"))?;
            manifest.insert(text(&pending, "file_id").into(), record.clone());
            self.store.checkpoint(
                text(&pending, "connection_id"),
                text(&pending, "job"),
                &mut manifest,
                None,
            )?;
        }
        self.store.put("receive-commit", &Value::Null)
    }
    pub fn snapshot(
        &self,
        entry: &Value,
        stage: bool,
    ) -> Result<(Option<tempfile::NamedTempFile>, String)> {
        let path = Path::new(text(entry, "local"));
        require(
            !path.ancestors().any(is_symlink),
            "local_changed",
            "로컬 경로가 링크로 바뀌었습니다. 기존 사본을 보존합니다.",
        )?;
        let mut file = OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_NOFOLLOW)
            .open(path)?;
        let info = file.metadata()?;
        if !info.is_file() || entry["stamp"] != stamp(&info) {
            return Err(error(
                "source_changed",
                "전송 전에 로컬 원본이 바뀌었습니다. 다시 비교해 주세요.",
                true,
            ));
        }
        require(
            info.len() <= MAX_FILE_BYTES,
            "too_large",
            "앱의 파일당 100MB 제한을 초과합니다.",
        )?;
        let mut output = if stage {
            Some(
                tempfile::Builder::new()
                    .prefix("snapshot-")
                    .tempfile_in(&self.stage)?,
            )
        } else {
            None
        };
        let (mut digest, mut total) = (Md5::new(), 0);
        loop {
            let mut buffer = vec![0; ((1024 * 1024).min(MAX_FILE_BYTES - total + 1)) as usize];
            let n = file.read(&mut buffer)?;
            if n == 0 {
                break;
            }
            total += n as u64;
            require(
                total <= MAX_FILE_BYTES,
                "too_large",
                "읽는 중 파일당 100MB 제한을 초과했습니다.",
            )?;
            digest.update(&buffer[..n]);
            if let Some(out) = &mut output {
                out.write_all(&buffer[..n])?;
            }
        }
        if stamp(&file.metadata()?) != entry["stamp"]
            || stamp(&fs::symlink_metadata(path)?) != entry["stamp"]
        {
            return Err(error(
                "source_changed",
                "읽는 중 로컬 원본이 바뀌었습니다. 기존 사본을 보존합니다.",
                true,
            ));
        }
        Ok((output, format!("{:x}", digest.finalize())))
    }
    fn save(
        &self,
        id: &str,
        job: &str,
        manifest: &mut Manifest,
        key: &str,
        record: &Value,
    ) -> Result<()> {
        if manifest.get(key) != Some(record) {
            manifest.insert(key.into(), record.clone());
        }
        if manifest.is_dirty() {
            self.store.checkpoint(id, job, manifest, Some(key))?;
        }
        Ok(())
    }
    pub fn publish(
        &self,
        connection: &mut Value,
        sources: &[Value],
        api: &dyn Remote,
        progress: &(dyn Fn(Value) + Sync),
    ) -> Result<Value> {
        progress(
            json!({"stage":"scanning","processed":0,"total":null,"current":"","current_bytes":0,"file_bytes":0}),
        );
        let (inventory, errors) = local_inventory(sources, &|| api.check().is_err())?;
        progress(
            json!({"stage":"preparing","total":inventory.len(),"transferred":0,"changed":0,"excluded":errors.len()}),
        );
        let cid = text(connection, "id").to_owned();
        let manifest = self.store.manifest(&cid, "upload")?;
        let root = api.get(text(connection, "root_id"))?;
        require(
            root["trashed"] != true && root["mimeType"] == FOLDER,
            "root",
            "공유 루트 폴더를 확인할 수 없습니다. 기존 사본을 보존합니다.",
        )?;
        if text(connection, "target_id").is_empty() {
            let targets = api
                .children(text(&root, "id"))?
                .into_iter()
                .filter(|c| c["name"] == connection["target"])
                .collect::<Vec<_>>();
            require(
                targets.len() <= 1 && targets.iter().all(|t| t["mimeType"] == FOLDER),
                "duplicate_path",
                "내 대상 폴더 이름이 겹칩니다. 이름을 확인해 주세요.",
            )?;
            connection["target_id"] = if let Some(target) = targets.first() {
                target["id"].clone()
            } else {
                json!(api.new_id()?)
            };
            connection["target_pending"] = json!(targets.is_empty());
            self.store.update_connection(connection)?;
        }
        if connection["target_pending"] == true {
            api.create_folder(
                text(connection, "target_id"),
                text(connection, "target"),
                text(&root, "id"),
            )?;
            connection["target_pending"] = json!(false);
            self.store.update_connection(connection)?;
        }
        let target = api.get(text(connection, "target_id"))?;
        require(
            array(&target["parents"]).contains(&root["id"]) && target["trashed"] != true,
            "target_changed",
            "내 대상 폴더의 위치·휴지통 상태를 확인해 주세요.",
        )?;
        let selected = sources
            .iter()
            .map(|v| {
                v["id"]
                    .as_str()
                    .map(str::to_owned)
                    .unwrap_or_else(|| v["id"].to_string())
            })
            .collect::<BTreeSet<_>>();
        let known = manifest
            .values
            .values()
            .filter(|v| selected.contains(text(v, "source_id")))
            .filter_map(|v| {
                v["remote_id"]
                    .as_str()
                    .filter(|s| !s.is_empty())
                    .map(str::to_owned)
            })
            .collect::<Vec<_>>();
        if !known.is_empty() {
            progress(
                json!({"stage":"remote","current":"","remote_checked":0,"remote_total":known.iter().collect::<BTreeSet<_>>().len()}),
            );
            api.prefetch(&known, &|checked, total| {
                progress(json!({"remote_checked":checked,"remote_total":total}))
            })?;
        }
        let mut identities: BTreeMap<(String, String), usize> = BTreeMap::new();
        for item in inventory.values() {
            *identities
                .entry((
                    text(item, "source_id").into(),
                    text(item, "identity").into(),
                ))
                .or_default() += 1;
        }
        let mut prior: BTreeMap<(String, String), Vec<String>> = BTreeMap::new();
        for (key, item) in &manifest.values {
            prior
                .entry((
                    text(item, "source_id").into(),
                    text(item, "identity").into(),
                ))
                .or_default()
                .push(key.clone());
        }
        let state = std::sync::Mutex::new(PublishState {
            manifest,
            used: BTreeSet::new(),
            verified: BTreeSet::new(),
            failed: BTreeSet::new(),
            parents: BTreeMap::from([(text(&target, "id").to_owned(), target)]),
            errors,
            changed: 0,
            copied: 0,
            processed: 0,
            active: 0,
        });
        let listings = std::sync::Mutex::new(BTreeMap::new());
        let context = PublishContext {
            engine: self,
            cid: &cid,
            target: text(connection, "target_id"),
            api,
            progress,
            prior: &prior,
            identities: &identities,
            state: &state,
            listings: &listings,
        };
        let mut ordered = inventory.iter().collect::<Vec<_>>();
        ordered.sort_by_key(|(_, v)| {
            (
                text(v, "path").matches('/').count(),
                v["kind"] != "folder",
                text(v, "path"),
            )
        });
        let mut folder_groups: BTreeMap<usize, Vec<(&String, &Value)>> = BTreeMap::new();
        let mut regular = Vec::new();
        for pair in ordered {
            if pair.1["kind"] == "folder" {
                folder_groups
                    .entry(text(pair.1, "path").matches('/').count())
                    .or_default()
                    .push(pair)
            } else {
                regular.push(pair)
            }
        }
        for group in folder_groups.values() {
            context.run_group(group)?;
        }
        context.run_group(&regular)?;
        let PublishState {
            mut manifest,
            used,
            failed,
            mut errors,
            mut changed,
            copied,
            ..
        } = state.into_inner().unwrap();
        progress(
            json!({"stage":"checking","processed":inventory.len(),"current":"","current_bytes":0,"file_bytes":0,"uploading":false,"active_items":0,"transferred":copied,"changed":changed,"excluded":errors.len()}),
        );
        let (fresh, _) = local_inventory(sources, &|| api.check().is_err())?;
        let stable = inventory.len() == fresh.len()
            && inventory.iter().all(|(k, v)| {
                fresh
                    .get(k)
                    .is_some_and(|f| f["stamp"] == v["stamp"] && f["kind"] == v["kind"])
            });
        if !stable {
            errors.push(json!({"path":"","message":"동기화 중 로컬 구성이 바뀌어 삭제 반영을 보류했습니다."}));
        }
        let mut blocked = inventory
            .values()
            .filter(|v| !v["error"].is_null())
            .map(|v| text(v, "path").to_owned())
            .collect::<Vec<_>>();
        blocked.extend(failed);
        let mut stale = manifest
            .values
            .iter()
            .filter(|(k, v)| {
                selected.contains(text(v, "source_id"))
                    && !inventory.contains_key(*k)
                    && !used.contains(*k)
                    && !blocked
                        .iter()
                        .any(|p| v["path"] == *p || text(v, "path").starts_with(&format!("{p}/")))
            })
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect::<Vec<_>>();
        stale.sort_by_key(|(_, v)| std::cmp::Reverse(text(v, "path").matches('/').count()));
        if stable {
            for (key, item) in stale {
                api.check()?;
                if let Some(replacement) = item["replacement"].as_str() {
                    if !manifest
                        .get(replacement)
                        .is_some_and(|v| v["complete"] == true)
                    {
                        continue;
                    }
                }
                if item["kind"] == "folder"
                    && manifest.values.iter().any(|(k, v)| {
                        k != &key
                            && text(v, "path").starts_with(&format!("{}/", text(&item, "path")))
                    })
                {
                    continue;
                }
                let result: Result<()> = (|| {
                    progress(
                        json!({"stage":"cleanup","current":item["path"],"changed":changed,"excluded":errors.len()}),
                    );
                    if item["kind"] == "folder" {
                        require(
                            api.children(text(&item, "remote_id"))?.is_empty(),
                            "unmanaged_children",
                            "원격 폴더에 남은 항목이 있어 폴더의 휴지통 이동을 보류했습니다.",
                        )?;
                    }
                    api.trash(text(&item, "remote_id"))?;
                    manifest.remove(&key);
                    self.store
                        .checkpoint(&cid, "upload", &mut manifest, Some(&key))?;
                    Ok(())
                })();
                match result {
                    Ok(()) => changed += 1,
                    Err(e) => errors.push(json!({"path":item["path"],"message":e.message})),
                }
            }
        }
        progress(
            json!({"stage":"finishing","current":"","transferred":copied,"changed":changed,"excluded":errors.len()}),
        );
        Ok(json!({"transferred":copied,"changed":changed,"excluded":errors.len(),"errors":errors}))
    }
    pub fn receive(
        &self,
        connection: &Value,
        publisher_id: &str,
        api: &dyn Remote,
    ) -> Result<Value> {
        self.recover_commit()?;
        let cid = text(connection, "id");
        let job = format!("receive:{publisher_id}");
        let mut manifest = self.store.manifest(cid, &job)?;
        let publisher = api.get(publisher_id)?;
        require(
            publisher["mimeType"] == FOLDER
                && array(&publisher["parents"]).contains(&connection["root_id"]),
            "publisher_changed",
            "선택한 폴더의 공유 루트와 위치를 확인해 주세요. 기존 사본을 보존합니다.",
        )?;
        require(
            publisher["trashed"] == true || publisher["capabilities"]["canListChildren"] != false,
            "partial_listing",
            "수신 폴더의 하위 목록을 읽을 수 없습니다. 기존 사본을 보존합니다.",
        )?;
        let entries = if publisher["trashed"] == true {
            Map::new()
        } else {
            remote_inventory(api, publisher_id)?
        };
        let destination = private_dir(
            &self
                .data_dir
                .join("external-sources/google-drive")
                .join(cid)
                .join(publisher_id),
        )?;
        let (mut errors, mut changed, mut copied) = (Vec::new(), 0, 0);
        let mut old_paths = manifest
            .values
            .values()
            .filter(|v| !text(v, "prior_path").is_empty())
            .map(|v| (text(v, "prior_path").to_owned(), text(v, "kind").to_owned()))
            .collect::<Vec<_>>();
        let mut owned = manifest
            .values
            .values()
            .map(|v| text(v, "path").to_owned())
            .collect::<BTreeSet<_>>();
        let final_paths = entries
            .values()
            .map(|v| text(v, "path").to_owned())
            .collect::<BTreeSet<_>>();
        let known_folders = manifest
            .values
            .iter()
            .filter(|(_, v)| v["kind"] == "folder")
            .map(|(k, _)| k.clone())
            .collect::<BTreeSet<_>>();
        let mut deleted = BTreeSet::new();
        for (file_id, item) in &manifest.values {
            if entries.contains_key(file_id) {
                continue;
            }
            api.check()?;
            if publisher["trashed"] == true {
                deleted.insert(file_id.clone());
                continue;
            }
            match api.get(file_id).and_then(|v|still_inside(&v,api,publisher_id,&entries,&known_folders,&BTreeSet::new())){Ok(false)=>{deleted.insert(file_id.clone());},Ok(true)=>errors.push(json!({"path":item["path"],"message":"원격 목록과 항목의 위치가 일치하지 않아 기존 사본을 보존합니다."})),Err(e)=>errors.push(json!({"path":item["path"],"message":e.message}))}
        }
        let mut succeeded = BTreeSet::new();
        let mut ordered = entries.iter().collect::<Vec<_>>();
        ordered.sort_by_key(|(_, v)| {
            (
                text(v, "path").matches('/').count(),
                v["kind"] != "folder",
                text(v, "path"),
            )
        });
        for (file_id, item) in ordered {
            api.check()?;
            let old = manifest.get(file_id).cloned().unwrap_or(json!({}));
            let result = (|| -> Result<()> {
                let target = local_path(&destination, text(item, "path"))?;
                require(
                    !target.exists()
                        || owned.contains(text(item, "path"))
                        || (item["kind"] == "folder" && target.is_dir()),
                    "unmanaged_path",
                    "수신 경로에 별도로 만든 항목이 있어 덮어쓰지 않았습니다.",
                )?;
                if item["kind"] == "folder" {
                    if target.is_file() {
                        self.remove_replaced(
                            &destination,
                            text(item, "path"),
                            &deleted,
                            cid,
                            &job,
                            &mut manifest,
                        )?;
                    }
                    private_dir(&target)?;
                } else {
                    require(
                        !text(item, "mimeType").starts_with("application/vnd.google-apps."),
                        "unsupported",
                        "Google 고유 문서·바로가기는 파일 내보내기를 자동 추가하지 않습니다.",
                    )?;
                    require(
                        number(&item["size"]).is_none_or(|n| n <= MAX_FILE_BYTES),
                        "too_large",
                        "앱의 파일당 100MB 제한을 초과합니다. 기존 사본을 보존합니다.",
                    )?;
                    let original = if old.as_object().is_some_and(|v| !v.is_empty()) {
                        Some(local_path(&destination, text(&old, "path"))?)
                    } else {
                        None
                    };
                    let mut digest = text(item, "md5Checksum").to_owned();
                    let reusable = original.as_ref().is_some_and(|p| {
                        p.is_file() && p.metadata().is_ok_and(|m| m.len() <= MAX_FILE_BYTES)
                    }) && !digest.is_empty()
                        && original
                            .as_ref()
                            .is_some_and(|p| content_hash(p).is_ok_and(|h| h == digest));
                    if !(reusable && original.as_ref() == Some(&target)) {
                        private_dir(target.parent().unwrap())?;
                        let temp = tempfile::Builder::new()
                            .prefix(".localbrain-drive-")
                            .tempfile_in(target.parent().unwrap())?;
                        let temp_path = temp.path().to_owned();
                        self.store.put("download-staging", &json!([temp_path]))?;
                        let staged = (|| -> Result<()> {
                            if reusable {
                                fs::copy(original.as_ref().unwrap(), &temp_path)?;
                                require(
                                    content_hash(&temp_path)? == digest,
                                    "local_changed",
                                    "수신 사본이 변경되어 다시 비교해야 합니다.",
                                )?;
                            } else {
                                digest = api.download(item, &temp_path)?;
                                copied += 1;
                            }
                            api.check()?;
                            local_path(&destination, text(item, "path"))?;
                            fs::set_permissions(&temp_path, fs::Permissions::from_mode(0o600))?;
                            File::open(&temp_path)?.sync_all()?;
                            if target.is_dir() {
                                self.remove_replaced(
                                    &destination,
                                    text(item, "path"),
                                    &deleted,
                                    cid,
                                    &job,
                                    &mut manifest,
                                )?;
                            }
                            let mut record = json!({"path":item["path"],"kind":"file","hash":digest,"version":item.get("version"),"complete":true});
                            if old.as_object().is_some_and(|v| !v.is_empty())
                                && old["path"] != item["path"]
                            {
                                record["prior_path"] = old["path"].clone();
                            }
                            self.store.put("receive-commit",&json!({"connection_id":cid,"publisher_id":publisher_id,"job":job,"file_id":file_id,"record":record}))?;
                            fs::rename(&temp_path, &target)?;
                            File::open(target.parent().unwrap())?.sync_all()?;
                            changed += 1;
                            Ok(())
                        })();
                        drop(temp);
                        self.store.put("download-staging", &json!([]))?;
                        staged?;
                    }
                }
                if old.as_object().is_some_and(|v| !v.is_empty()) && old["path"] != item["path"] {
                    old_paths.push((text(&old, "path").into(), text(&old, "kind").into()));
                }
                let mut record = json!({"path":item["path"],"kind":item["kind"],"hash":item.get("md5Checksum"),"version":item.get("version"),"complete":true});
                if old.as_object().is_some_and(|v| !v.is_empty()) && old["path"] != item["path"] {
                    record["prior_path"] = old["path"].clone();
                }
                manifest.insert(file_id.clone(), record);
                self.store
                    .checkpoint(cid, &job, &mut manifest, Some(file_id))?;
                self.store.put("receive-commit", &Value::Null)?;
                succeeded.insert(text(item, "path").to_owned());
                owned.insert(text(item, "path").to_owned());
                Ok(())
            })();
            if let Err(e) = result {
                errors.push(json!({"path":item["path"],"message":if ["io","database","json"].contains(&e.code.as_str()){"수신 항목을 저장하지 못했습니다. 기존 사본을 보존합니다."}else{&e.message}}));
            }
        }
        let mut removed = deleted
            .iter()
            .filter_map(|id| manifest.get(id).map(|v| (id.clone(), v.clone())))
            .collect::<Vec<_>>();
        removed.sort_by_key(|(_, v)| std::cmp::Reverse(text(v, "path").matches('/').count()));
        for (file_id, item) in removed {
            api.check()?;
            let result = (|| -> Result<()> {
                let path = local_path(&destination, text(&item, "path"))?;
                if !final_paths.contains(text(&item, "path")) {
                    Self::remove_owned(&path, text(&item, "kind"))?;
                    changed += 1;
                } else if !succeeded.contains(text(&item, "path")) {
                    return Ok(());
                }
                manifest.remove(&file_id);
                self.store
                    .checkpoint(cid, &job, &mut manifest, Some(&file_id))?;
                Ok(())
            })();
            if let Err(e) = result {
                errors.push(json!({"path":item["path"],"message":if e.code=="io"{"수신 항목을 제거하지 못했습니다."}else{&e.message}}));
            }
        }
        old_paths.sort_by_key(|(p, _)| std::cmp::Reverse(p.matches('/').count()));
        for (relative, kind) in old_paths {
            if final_paths.contains(&relative) {
                continue;
            }
            let result = (|| -> Result<()> {
                Self::remove_owned(&local_path(&destination, &relative)?, &kind)?;
                let changed = manifest
                    .values
                    .iter()
                    .filter(|(_, v)| v["prior_path"] == relative)
                    .map(|(k, v)| (k.clone(), v.clone()))
                    .collect::<Vec<_>>();
                for (key, mut value) in changed {
                    value.as_object_mut().unwrap().remove("prior_path");
                    manifest.insert(key, value);
                }
                self.store.checkpoint(cid, &job, &mut manifest, None)
            })();
            if result.is_err() {
                errors.push(json!({"path":relative,"message":"이전 수신 경로를 정리하지 못했습니다. 별도 파일이 있는지 확인해 주세요."}));
            }
        }
        Ok(
            json!({"transferred":copied,"changed":changed,"excluded":errors.len(),"errors":errors,"destination":destination}),
        )
    }
    fn remove_replaced(
        &self,
        destination: &Path,
        relative: &str,
        deleted: &BTreeSet<String>,
        cid: &str,
        job: &str,
        manifest: &mut Manifest,
    ) -> Result<()> {
        let mut candidates = deleted
            .iter()
            .filter_map(|id| {
                manifest
                    .get(id)
                    .filter(|v| {
                        v["path"] == relative
                            || text(v, "path").starts_with(&format!("{relative}/"))
                    })
                    .map(|v| (id.clone(), v.clone()))
            })
            .collect::<Vec<_>>();
        candidates.sort_by_key(|(_, v)| std::cmp::Reverse(text(v, "path").matches('/').count()));
        for (id, item) in candidates {
            Self::remove_owned(
                &local_path(destination, text(&item, "path"))?,
                text(&item, "kind"),
            )?;
            manifest.remove(&id);
            self.store.checkpoint(cid, job, manifest, None)?;
        }
        Ok(())
    }
    pub fn remove_owned(path: &Path, kind: &str) -> Result<()> {
        if kind == "folder" {
            if path.exists() {
                fs::remove_dir(path)?;
            }
        } else {
            require(
                !path.exists() || path.is_file(),
                "type_changed",
                "로컬 사본의 유형이 바뀌어 보존했습니다.",
            )?;
            match fs::remove_file(path) {
                Ok(()) => {}
                Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
                Err(e) => return Err(e.into()),
            }
        }
        Ok(())
    }
}
fn still_inside(
    value: &Value,
    api: &dyn Remote,
    publisher: &str,
    entries: &Map<String, Value>,
    folders: &BTreeSet<String>,
    visited: &BTreeSet<String>,
) -> Result<bool> {
    if value["trashed"] == true {
        return Ok(false);
    }
    let mut visited = visited.clone();
    require(
        visited.insert(text(value, "id").into()),
        "partial_listing",
        "원격 폴더 위치를 확인하지 못했습니다.",
    )?;
    for parent in array(&value["parents"]).iter().filter_map(Value::as_str) {
        if parent == publisher || entries.contains_key(parent) {
            return Ok(true);
        }
        if folders.contains(parent)
            && still_inside(
                &api.get(parent)?,
                api,
                publisher,
                entries,
                folders,
                &visited,
            )?
        {
            return Ok(true);
        }
    }
    Ok(false)
}
/// Shared checkpoint state is locked only while assigning/committing metadata.
/// Independent media operations run concurrently, at most eight per depth group.
struct PublishState {
    manifest: Manifest,
    used: BTreeSet<String>,
    verified: BTreeSet<String>,
    failed: BTreeSet<String>,
    parents: BTreeMap<String, Value>,
    errors: Vec<Value>,
    changed: usize,
    copied: usize,
    processed: usize,
    active: usize,
}
struct PublishContext<'a> {
    engine: &'a Engine,
    cid: &'a str,
    target: &'a str,
    api: &'a dyn Remote,
    progress: &'a (dyn Fn(Value) + Sync),
    prior: &'a BTreeMap<(String, String), Vec<String>>,
    identities: &'a BTreeMap<(String, String), usize>,
    state: &'a std::sync::Mutex<PublishState>,
    listings: &'a std::sync::Mutex<BTreeMap<String, Vec<Value>>>,
}
impl PublishContext<'_> {
    fn run_group(&self, entries: &[(&String, &Value)]) -> Result<()> {
        for batch in entries.chunks(PUBLISH_WORKERS) {
            self.api.check()?;
            let result = std::thread::scope(|scope| {
                let mut handles = Vec::new();
                let mut spawn_error = None;
                for (key, item) in batch {
                    match crate::backend::worker_thread("drive-publish")
                        .spawn_scoped(scope, move || self.sync_item(key, item))
                    {
                        Ok(handle) => handles.push(handle),
                        Err(e) => {
                            spawn_error = Some(e.into());
                            break;
                        }
                    }
                }
                let mut result = spawn_error.map_or(Ok(()), Err);
                for handle in handles {
                    match handle.join() {
                        Ok(Ok(())) => {}
                        Ok(Err(e)) => {
                            if result.is_ok() {
                                result = Err(e)
                            }
                        }
                        Err(_) => {
                            if result.is_ok() {
                                result = Err(error(
                                    "sync",
                                    "동기화를 완료하지 못했습니다. 기존 사본과 설정을 보존합니다.",
                                    false,
                                ))
                            }
                        }
                    }
                }
                result
            });
            result?;
        }
        Ok(())
    }
    fn sync_item(&self, key: &str, item: &Value) -> Result<()> {
        self.api.check()?;
        {
            let mut state = self.state.lock().unwrap();
            state.active += 1;
            (self.progress)(
                json!({"stage":"syncing","processed":state.processed,"current":item["path"],"current_bytes":0,"uploading":false,"active_items":state.active,"file_bytes":if item["kind"]=="file"{item["size"].clone()}else{json!(0)},"transferred":state.copied,"changed":state.changed,"excluded":state.errors.len()}),
            );
        }
        let mut replacement_folder = false;
        let result = (|| -> Result<()> {
            let identity = (
                text(item, "source_id").to_owned(),
                text(item, "identity").to_owned(),
            );
            let candidates = self.prior.get(&identity).cloned().unwrap_or_default();
            let (parent, mut record, mut newly) = {
                let mut state = self.state.lock().unwrap();
                if !item["error"].is_null() {
                    if !state.manifest.values.contains_key(key)
                        && candidates.len() == 1
                        && self.identities.get(&identity) == Some(&1)
                    {
                        if let Some(mut value) = state.manifest.remove(&candidates[0]) {
                            value["path"] = item["path"].clone();
                            state.manifest.insert(key.into(), value);
                            self.engine.store.checkpoint(
                                self.cid,
                                "upload",
                                &mut state.manifest,
                                Some(key),
                            )?;
                        }
                    }
                    state.used.insert(key.into());
                    return Ok(());
                }
                let old_key = if state.manifest.values.contains_key(key) {
                    Some(key.to_owned())
                } else if candidates.len() == 1
                    && self.identities.get(&identity) == Some(&1)
                    && !state.used.contains(&candidates[0])
                {
                    Some(candidates[0].clone())
                } else {
                    None
                };
                let mut old = old_key
                    .as_ref()
                    .and_then(|k| state.manifest.get(k))
                    .cloned()
                    .unwrap_or(json!({}));
                if let Some(k) = &old_key {
                    state.used.insert(k.clone());
                }
                let parent_path = text(item, "path")
                    .rsplit_once('/')
                    .map(|(p, _)| p)
                    .unwrap_or("");
                let parent_key = format!("{}:{parent_path}", text(item, "source_id"));
                let parent = if parent_path.is_empty() {
                    self.target.to_owned()
                } else {
                    require(
                        state.verified.contains(&parent_key),
                        "parent_incomplete",
                        "상위 폴더의 동기화를 먼저 완료해야 합니다.",
                    )?;
                    text(
                        state.manifest.get(&parent_key).ok_or_else(|| {
                            error(
                                "parent_incomplete",
                                "상위 폴더의 동기화를 먼저 완료해야 합니다.",
                                false,
                            )
                        })?,
                        "remote_id",
                    )
                    .to_owned()
                };
                if old.as_object().is_some_and(|v| !v.is_empty()) && old["kind"] != item["kind"] {
                    replacement_folder = old["kind"] == "folder";
                    let mut retired = old;
                    retired["replacement"] = json!(key);
                    state
                        .manifest
                        .insert(format!("retired:{}", text(&retired, "remote_id")), retired);
                    old = json!({});
                }
                let mut record = old;
                for name in ["source_id", "identity", "path", "kind"] {
                    record[name] = item[name].clone();
                }
                let newly = text(&record, "remote_id").is_empty();
                if newly {
                    record["remote_id"] = json!(self.api.new_id()?);
                    record["complete"] = json!(false);
                }
                if let Some(old_key) = old_key.filter(|old| old != key) {
                    state.manifest.remove(&old_key);
                }
                state.used.insert(key.into());
                self.engine
                    .save(self.cid, "upload", &mut state.manifest, key, &record)?;
                (parent, record, newly)
            };
            let name = text(item, "path").rsplit('/').next().unwrap();
            let mut current = None;
            if !newly {
                match self.api.get(text(&record, "remote_id")) {
                    Ok(value) => current = Some(value),
                    Err(e) => {
                        if e.code != "unavailable" {
                            return Err(e);
                        }
                        if record["complete"] == true {
                            let caps =
                                self.state.lock().unwrap().parents[&parent]["capabilities"].clone();
                            if caps["canListChildren"] != true || caps["canAddChildren"] != true {
                                return Err(e);
                            }
                            let mut listings = self.listings.lock().unwrap();
                            if !listings.contains_key(&parent) {
                                listings.insert(parent.clone(), self.api.children(&parent)?);
                            }
                            if listings[&parent].iter().any(|child| {
                                child["id"] == record["remote_id"]
                                    || name_key(text(child, "name")).ok() == name_key(name).ok()
                            }) {
                                return Err(e);
                            }
                            drop(listings);
                            record["remote_id"] = json!(self.api.new_id()?);
                            record["complete"] = json!(false);
                            newly = true;
                            for field in ["hash", "version", "session", "upload_hash"] {
                                record.as_object_mut().unwrap().remove(field);
                            }
                            self.engine.save(
                                self.cid,
                                "upload",
                                &mut self.state.lock().unwrap().manifest,
                                key,
                                &record,
                            )?;
                        }
                    }
                }
            }
            if let Some(value) = &current {
                require(
                    (value["mimeType"] == FOLDER) == (item["kind"] == "folder"),
                    "type_changed",
                    "파일·폴더 유형이 바뀌었습니다. 기존 사본을 보존합니다.",
                )?;
            }
            let restored = current.as_ref().is_some_and(|v| v["trashed"] == true);
            if let Some(value) = current.as_ref().filter(|v| {
                v["name"] != name || v["parents"] != json!([parent]) || v["trashed"] == true
            }) {
                current =
                    Some(
                        self.api
                            .metadata(text(&record, "remote_id"), name, &parent, value)?,
                    );
                self.state.lock().unwrap().changed += 1;
            }
            if item["kind"] == "folder" {
                if current.is_none() {
                    current = Some(self.api.create_folder(
                        text(&record, "remote_id"),
                        name,
                        &parent,
                    )?);
                    if newly {
                        self.listings
                            .lock()
                            .unwrap()
                            .insert(text(&record, "remote_id").into(), vec![]);
                    }
                    self.state.lock().unwrap().changed += 1;
                }
                if restored {
                    let ids = self
                        .state
                        .lock()
                        .unwrap()
                        .manifest
                        .values
                        .values()
                        .filter(|v| {
                            v["source_id"] == item["source_id"]
                                && text(v, "path").starts_with(&format!("{}/", text(item, "path")))
                        })
                        .filter_map(|v| v["remote_id"].as_str().map(str::to_owned))
                        .collect::<Vec<_>>();
                    self.api.invalidate(&ids);
                }
            } else {
                let mut digest = None;
                if current.as_ref().is_some_and(|v| {
                    !text(v, "md5Checksum").is_empty()
                        && number(&v["size"]) == number(&item["size"])
                }) {
                    digest = Some(self.engine.snapshot(item, false)?.1);
                }
                if digest
                    .as_ref()
                    .is_none_or(|d| current.as_ref().is_none_or(|v| v["md5Checksum"] != *d))
                {
                    let (staged, hash) = self.engine.snapshot(item, true)?;
                    let staged = staged.unwrap();
                    let id = text(&record, "remote_id").to_owned();
                    let mut checkpoint = |value: &Value| {
                        self.engine.save(
                            self.cid,
                            "upload",
                            &mut self.state.lock().unwrap().manifest,
                            key,
                            value,
                        )
                    };
                    let transferred = |sent, size| {
                        let active = self.state.lock().unwrap().active;
                        (self.progress)(
                            json!({"current":item["path"],"uploading":true,"current_bytes":sent,"file_bytes":size,"active_items":active}),
                        );
                    };
                    transferred(0, number(&item["size"]).unwrap_or(0));
                    current = Some(self.api.upload(
                        &id,
                        name,
                        &parent,
                        staged.path(),
                        &hash,
                        current.is_some(),
                        &mut record,
                        &mut checkpoint,
                        &transferred,
                    )?);
                    self.state.lock().unwrap().copied += 1;
                    digest = Some(hash);
                }
                record["hash"] = json!(digest);
            }
            record["complete"] = json!(true);
            record["version"] = current
                .as_ref()
                .unwrap()
                .get("version")
                .cloned()
                .unwrap_or(Value::Null);
            let mut state = self.state.lock().unwrap();
            self.engine
                .save(self.cid, "upload", &mut state.manifest, key, &record)?;
            if item["kind"] == "folder" {
                state.verified.insert(key.into());
                state
                    .parents
                    .insert(text(&record, "remote_id").into(), current.unwrap());
            }
            Ok(())
        })();
        let cancelled = result
            .as_ref()
            .err()
            .filter(|e| e.code == "cancelled")
            .cloned();
        let mut state = self.state.lock().unwrap();
        if let Err(e) = result {
            if e.code != "cancelled" {
                state.errors.push(json!({"path":item["path"],"message":if ["io","database"].contains(&e.code.as_str()){"로컬 항목을 처리하지 못했습니다. 기존 사본을 보존합니다."}else{&e.message}}));
                if item["kind"] == "folder" || replacement_folder {
                    state.failed.insert(text(item, "path").into());
                }
            }
        }
        state.processed += 1;
        state.active -= 1;
        (self.progress)(
            json!({"processed":state.processed,"current":item["path"],"uploading":false,"current_bytes":0,"file_bytes":0,"active_items":state.active,"transferred":state.copied,"changed":state.changed,"excluded":state.errors.len()}),
        );
        match cancelled {
            Some(e) => Err(e),
            None => Ok(()),
        }
    }
}
