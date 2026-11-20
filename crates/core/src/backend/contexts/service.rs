use crate::backend::ingest::IngestionObserver;
use crate::backend::rendering::references::{MarkdownDocumentReference, MarkdownReferenceContext};
use crate::backend::{db, now, BackendError, Config, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};
const ORDER:&str="context_roots.display_order IS NULL,context_roots.display_order,CASE context_roots.source_type WHEN 'folder' THEN 0 WHEN 'apple_notes' THEN 1 ELSE 2 END,context_roots.label,context_roots.path";
fn canonical(path: &str, file: bool, config: &Config) -> Result<PathBuf> {
    let path = crate::backend::ingest::storage::expand(path, config)?;
    let info = match fs::metadata(&path) {
        Ok(v) => v,
        Err(error) if matches!(error.raw_os_error(), Some(libc::ENOENT | libc::ENOTDIR)) => {
            return Err(BackendError::invalid(
                "context_path",
                if file {
                    "File does not exist"
                } else {
                    "Folder does not exist"
                },
            ))
        }
        Err(error) => return Err(error.into()),
    };
    if (file && !info.is_file()) || (!file && !info.is_dir()) {
        return Err(BackendError::invalid(
            "context_path",
            if file {
                "Local Context file must be a file"
            } else {
                "Local Context root must be a folder"
            },
        ));
    }
    Ok(fs::canonicalize(path)?)
}
fn text(path: &Path) -> Result<&str> {
    path.to_str().ok_or_else(|| {
        BackendError::invalid("context_unicode", "Context path is not valid Unicode")
    })
}
pub fn reorder_context_sources(
    connection: &Connection,
    source_ids: &[i64],
    expected: &[i64],
) -> Result<()> {
    let current = db::rows(
        connection,
        &format!("SELECT id FROM context_roots WHERE enabled=1 ORDER BY {ORDER}"),
        [],
    )?
    .into_iter()
    .map(|r| r["id"].as_i64().unwrap())
    .collect::<Vec<_>>();
    if current != expected {
        return Err(BackendError::conflict(
            "목록이 변경되었습니다. 새 목록을 확인한 뒤 다시 이동해 주세요.",
        ));
    }
    let ids = source_ids.iter().copied().collect::<BTreeSet<_>>();
    if ids.len() != source_ids.len() || ids != current.iter().copied().collect() {
        return Err(BackendError::invalid(
            "context_order",
            "등록된 Local Context 전체의 순서를 지정해 주세요.",
        ));
    }
    for (index, id) in source_ids.iter().enumerate() {
        connection.execute(
            "UPDATE context_roots SET display_order=? WHERE id=?",
            params![index as i64, id],
        )?;
    }
    Ok(())
}
pub fn add_context_root(connection: &Connection, config: &Config, path: &str) -> Result<i64> {
    let candidate = canonical(path, false, config)?;
    let path = text(&candidate)?;
    for row in db::rows(
        connection,
        "SELECT path FROM context_roots WHERE enabled=1 AND source_type='folder' AND path!=?",
        [path],
    )? {
        let prior = Path::new(row["path"].as_str().unwrap());
        if prior.starts_with(&candidate) || candidate.starts_with(prior) {
            return Err(BackendError::invalid(
                "context_overlap",
                format!(
                    "Folder overlaps an existing Local Context root: {}",
                    prior.display()
                ),
            ));
        }
    }
    let label = candidate
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or(path);
    if let Some(row) = db::row(
        connection,
        "SELECT id FROM context_roots WHERE path=?",
        [path],
    )? {
        let id = row["id"].as_i64().unwrap();
        connection.execute("UPDATE context_roots SET enabled=1,label=?,source_type='folder',readable=1,status='ready',error=NULL,updated_at=? WHERE id=?",params![label,now(),id])?;
        Ok(id)
    } else {
        connection.execute(
            "INSERT INTO context_roots(path,label,source_type,updated_at) VALUES(?,?,'folder',?)",
            params![path, label, now()],
        )?;
        Ok(connection.last_insert_rowid())
    }
}
pub fn add_context_file(connection: &Connection, config: &Config, path: &str) -> Result<i64> {
    let candidate = canonical(path, true, config)?;
    let path = text(&candidate)?;
    for row in db::rows(
        connection,
        "SELECT path FROM context_roots WHERE enabled=1 AND source_type='folder'",
        [],
    )? {
        let prior = Path::new(row["path"].as_str().unwrap());
        if candidate != prior && candidate.starts_with(prior) {
            return Err(BackendError::invalid(
                "context_overlap",
                format!(
                    "File is already covered by Local Context folder: {}",
                    prior.display()
                ),
            ));
        }
    }
    let label = candidate.file_name().and_then(|s| s.to_str()).unwrap_or("");
    if let Some(row) = db::row(
        connection,
        "SELECT id FROM context_roots WHERE path=?",
        [path],
    )? {
        let id = row["id"].as_i64().unwrap();
        connection.execute("UPDATE context_roots SET enabled=1,label=?,source_type='file',readable=1,status='pending',error=NULL,updated_at=? WHERE id=?",params![label,now(),id])?;
        Ok(id)
    } else {
        connection.execute("INSERT INTO context_roots(path,label,source_type,status,updated_at) VALUES(?,?,'file','pending',?)",params![path,label,now()])?;
        Ok(connection.last_insert_rowid())
    }
}
pub fn add_apple_notes_source(connection: &Connection) -> Result<i64> {
    if let Some(row) = db::row(
        connection,
        "SELECT id FROM context_roots WHERE path='apple-notes://default'",
        [],
    )? {
        let id = row["id"].as_i64().unwrap();
        connection.execute("UPDATE context_roots SET enabled=1,label='Apple Notes',source_type='apple_notes',readable=1,status='pending',error=NULL,updated_at=? WHERE id=?",params![now(),id])?;
        Ok(id)
    } else {
        connection.execute("INSERT INTO context_roots(path,label,source_type,status,updated_at) VALUES('apple-notes://default','Apple Notes','apple_notes','pending',?)",[now()])?;
        Ok(connection.last_insert_rowid())
    }
}
pub fn remove_context_root(
    connection: &Connection,
    id: i64,
    observer: &dyn IngestionObserver,
) -> Result<()> {
    if db::row(
        connection,
        "SELECT id FROM context_roots WHERE id=? AND enabled=1",
        [id],
    )?
    .is_none()
    {
        return Err(BackendError::not_found("Local Context root not found"));
    }
    observer.context_root_removed(connection, id)?;
    connection.execute("DELETE FROM search_index WHERE entity_type='document' AND entity_id IN(SELECT CAST(id AS TEXT) FROM context_documents WHERE context_root_id=?)",[id])?;
    connection.execute("DELETE FROM source_files WHERE path IN(SELECT path FROM context_documents WHERE context_root_id=?)",[id])?;
    connection.execute(
        "UPDATE context_roots SET enabled=0,updated_at=? WHERE id=?",
        params![now(), id],
    )?;
    Ok(())
}
pub fn list_context_sources(connection: &Connection, config: &Config) -> Result<Vec<Value>> {
    let mut rows=db::rows(connection,&format!("SELECT context_roots.*,COUNT(context_documents.id) AS document_count,COALESCE(SUM(context_documents.size_bytes),0) AS total_bytes,MAX(context_documents.mtime_ns) AS latest_mtime_ns FROM context_roots LEFT JOIN context_documents ON context_documents.context_root_id=context_roots.id WHERE context_roots.enabled=1 GROUP BY context_roots.id ORDER BY {ORDER}"),[])?;
    for row in &mut rows {
        if row["source_type"] == "apple_notes" {
            row["display_path"] = json!("Notes.app");
            row["exists_now"] = json!(Path::new("/System/Applications/Notes.app").exists());
        } else {
            let path = PathBuf::from(row["path"].as_str().unwrap());
            row["display_path"] = json!(path
                .strip_prefix(&config.home_dir)
                .ok()
                .map(|p| if p.as_os_str().is_empty() {
                    "~".into()
                } else {
                    format!("~/{}", p.display())
                })
                .unwrap_or_else(|| path.display().to_string()));
            row["exists_now"] = json!(if row["source_type"] == "file" {
                path.is_file()
            } else {
                path.is_dir()
            });
        }
    }
    Ok(rows)
}
pub fn list_context_roots(connection: &Connection, config: &Config) -> Result<Vec<Value>> {
    list_context_sources(connection, config)
}
pub fn get_context_root(connection: &Connection, id: Option<i64>) -> Result<Option<Value>> {
    match id {
        Some(id) => db::row(
            connection,
            "SELECT * FROM context_roots WHERE id=? AND enabled=1",
            [id],
        ),
        None => Ok(None),
    }
}
#[derive(Default)]
struct Tree {
    directories: BTreeMap<String, Tree>,
    documents: Vec<Value>,
}
impl Tree {
    fn materialize(mut self, selected: Option<i64>) -> Vec<Value> {
        let mut out = vec![];
        for (name, child) in self.directories {
            let children = child.materialize(selected);
            let contains = children.iter().any(|c| c["contains_selected"] == true);
            out.push(json!({"kind":"directory","name":name,"children":children,"contains_selected":contains}));
        }
        self.documents.sort_by(|a, b| {
            (a["title"].as_str(), a["relative_path"].as_str())
                .cmp(&(b["title"].as_str(), b["relative_path"].as_str()))
        });
        for mut doc in self.documents {
            doc["kind"] = json!("document");
            doc["name"] = json!(doc["relative_path"]
                .as_str()
                .unwrap()
                .rsplit('/')
                .next()
                .unwrap_or(""));
            doc["contains_selected"] = json!(doc["id"].as_i64() == selected);
            out.push(doc);
        }
        out
    }
}
pub fn context_source_tree(
    connection: &Connection,
    id: i64,
    selected: Option<i64>,
) -> Result<Vec<Value>> {
    let mut root = Tree::default();
    for row in db::rows(connection,"SELECT id,title,relative_path,content_type FROM context_documents WHERE context_root_id=? ORDER BY relative_path,title",[id])?{let path=row["relative_path"].as_str().unwrap().to_owned();let parts=path.split('/').filter(|s|!s.is_empty()&&*s!=".").collect::<Vec<_>>();let mut node=&mut root;for part in &parts[..parts.len().saturating_sub(1)]{node=node.directories.entry(part.to_string()).or_default();}node.documents.push(row);}
    Ok(root.materialize(selected))
}
pub fn build_markdown_reference_context(
    connection: &Connection,
    id: i64,
) -> Result<Option<MarkdownReferenceContext>> {
    let Some(current)=db::row(connection,"SELECT context_documents.id,context_documents.context_root_id FROM context_documents JOIN context_roots ON context_roots.id=context_documents.context_root_id WHERE context_documents.id=? AND context_roots.enabled=1 AND context_roots.source_type='folder'",[id])?else{return Ok(None);};
    let documents=db::rows(connection,"SELECT id,context_root_id,relative_path,title,body,content_type FROM context_documents WHERE context_root_id=? ORDER BY relative_path,id",[current["context_root_id"].as_i64()])?.into_iter().map(serde_json::from_value::<MarkdownDocumentReference>).collect::<std::result::Result<Vec<_>,_>>()?;
    Ok(Some(MarkdownReferenceContext::from_documents(
        documents, id,
    )?))
}

pub fn context_document_preview(connection: &Connection, document: &Value) -> Result<Value> {
    let mut view = document.clone();
    let id = view["id"]
        .as_i64()
        .ok_or_else(|| BackendError::invalid("document", "Document identity is invalid"))?;
    let references = build_markdown_reference_context(connection, id)?;
    let rendered = crate::backend::rendering::render_markdown(
        view["body"].as_str().unwrap_or(""),
        &crate::backend::rendering::MarkdownOptions {
            reference_context: references.as_ref(),
            ..Default::default()
        },
    );
    view["rendered_body"] = json!(rendered.html);
    view["render_state"] = json!(rendered.state);
    view["render_properties"] = serde_json::to_value(rendered.properties)?;
    Ok(view)
}
pub fn context_document_reader(connection: &Connection, document: &Value) -> Result<Value> {
    let view = context_document_preview(connection, document)?;
    let mut source = get_context_root(connection, view["context_root_id"].as_i64())?;
    let has_tree = source
        .as_ref()
        .is_some_and(|s| s["source_type"] == "folder");
    let tree = if has_tree {
        context_source_tree(
            connection,
            source.as_ref().unwrap()["id"].as_i64().unwrap(),
            view["id"].as_i64(),
        )?
    } else {
        vec![]
    };
    let href = if let Some(source) = source.as_mut() {
        let id = source["id"].as_i64().unwrap();
        let count: i64 = connection.query_row(
            "SELECT count(*) FROM context_documents WHERE context_root_id=?",
            [id],
            |r| r.get(0),
        )?;
        source["document_count"] = json!(count);
        format!("/context?root={id}&document={}", view["id"])
    } else {
        "/context".into()
    };
    Ok(
        json!({"document":view,"context_source":source,"context_tree":tree,"has_context_tree":has_tree,"return_href":href}),
    )
}
