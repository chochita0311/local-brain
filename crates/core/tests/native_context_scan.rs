use localbrain_core::backend::{
    contexts, db,
    ingest::{self, NoObservers, ScanControl},
    Config, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::os::unix::fs::symlink;
use std::{
    fs,
    path::Path,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
};
struct Fixture {
    _temp: tempfile::TempDir,
    config: Config,
    db: Connection,
}
impl Fixture {
    fn new() -> Self {
        let temp = tempfile::Builder::new()
            .prefix("lb-native-context-")
            .tempdir()
            .unwrap();
        let root = fs::canonicalize(temp.path()).unwrap();
        let config = Config::for_data_dir(root.join("data"));
        fs::create_dir_all(&config.home_dir).unwrap();
        db::initialize(&config).unwrap();
        let db = db::connect(&config).unwrap();
        Self {
            _temp: temp,
            config,
            db,
        }
    }
    fn folder(&self) -> std::path::PathBuf {
        let path = self.config.home_dir.join("registered");
        fs::create_dir_all(&path).unwrap();
        path
    }
    fn scan(&self, reader: &dyn contexts::scan::ContextReader, force: bool) -> (i64, i64, i64) {
        contexts::scan::scan_documents(
            &self.db,
            &self.config,
            force,
            None,
            &ScanControl::default(),
            &NoObservers,
            reader,
        )
        .unwrap()
    }
    fn count(&self, table: &str) -> i64 {
        self.db
            .query_row(&format!("SELECT count(*) FROM {table}"), [], |r| r.get(0))
            .unwrap()
    }
}
struct SyntheticReader {
    notes: Value,
    pdf: Option<String>,
    calls: AtomicUsize,
}
impl SyntheticReader {
    fn empty() -> Self {
        Self {
            notes: json!([]),
            pdf: None,
            calls: AtomicUsize::new(0),
        }
    }
}
impl contexts::scan::ContextReader for SyntheticReader {
    fn apple_notes(&self, control: &ScanControl) -> Result<Value> {
        control.check()?;
        self.calls.fetch_add(1, Ordering::SeqCst);
        Ok(self.notes.clone())
    }
    fn spotlight_pdf(&self, _: &Path, control: &ScanControl) -> Result<Option<String>> {
        control.check()?;
        self.calls.fetch_add(1, Ordering::SeqCst);
        Ok(self.pdf.clone())
    }
}
#[test]
fn registered_folder_scans_only_eligible_markdown_and_preserves_second_scan() {
    let f = Fixture::new();
    let root = f.folder();
    for dir in [
        ".hidden",
        "node_modules",
        "target",
        "vendor",
        "build",
        "dist",
        "__pycache__",
    ] {
        fs::create_dir(root.join(dir)).unwrap();
        fs::write(root.join(dir).join("excluded.md"), "private synthetic").unwrap();
    }
    fs::create_dir(root.join("sub")).unwrap();
    fs::write(root.join("first.md"), "# 한글 heading\r\nbody\rnext").unwrap();
    fs::write(root.join("sub/second.md"), "# Second\n").unwrap();
    fs::write(root.join("upper.MD"), "exclude").unwrap();
    fs::write(root.join(".hidden.md"), "exclude").unwrap();
    symlink(root.join("sub"), root.join("linked-directory")).unwrap();
    let id = contexts::add_context_root(&f.db, &f.config, root.to_str().unwrap()).unwrap();
    let reader = SyntheticReader::empty();
    assert_eq!(f.scan(&reader, false), (2, 0, 0));
    assert_eq!(reader.calls.load(Ordering::SeqCst), 0);
    assert_eq!(f.count("context_documents"), 2);
    assert_eq!(f.count("resource_documents"), 2);
    assert_eq!(f.count("source_files"), 2);
    let first = db::row(
        &f.db,
        "SELECT * FROM context_documents WHERE relative_path='first.md'",
        [],
    )
    .unwrap()
    .unwrap();
    assert_eq!(first["body"], "# 한글 heading\nbody\nnext");
    let before = db::rows(&f.db, "SELECT * FROM context_documents ORDER BY id", []).unwrap();
    assert_eq!(f.scan(&reader, false), (0, 2, 0));
    assert_eq!(
        db::rows(&f.db, "SELECT * FROM context_documents ORDER BY id", []).unwrap(),
        before
    );
    let tree = contexts::context_source_tree(&f.db, id, first["id"].as_i64()).unwrap();
    assert_eq!(tree[0]["kind"], "directory");
    assert_eq!(tree[1]["contains_selected"], true);
    assert_eq!(
        f.db.query_row(
            "SELECT count(*) FROM search_index WHERE entity_type='document'",
            [],
            |r| r.get::<_, i64>(0)
        )
        .unwrap(),
        2
    );
}
#[test]
fn vanished_document_removes_projection_and_binding_but_preserves_resource_identity() {
    let f = Fixture::new();
    let root = f.folder();
    let path = root.join("keep.md");
    fs::write(&path, "# Kept\ntext").unwrap();
    contexts::add_context_root(&f.db, &f.config, root.to_str().unwrap()).unwrap();
    let reader = SyntheticReader::empty();
    f.scan(&reader, false);
    let resources = f.count("reference_resources");
    fs::remove_file(&path).unwrap();
    assert_eq!(f.scan(&reader, false), (0, 0, 0));
    assert_eq!(f.count("context_documents"), 0);
    assert_eq!(f.count("resource_documents"), 0);
    assert_eq!(f.count("reference_resources"), resources);
    assert_eq!(f.count("source_files"), 0);
}
#[test]
fn source_order_removal_and_readding_retain_documents_and_user_position() {
    let f = Fixture::new();
    let root = f.folder();
    fs::write(root.join("one.md"), "# First").unwrap();
    let id = contexts::add_context_root(&f.db, &f.config, root.to_str().unwrap()).unwrap();
    let notes = contexts::add_apple_notes_source(&f.db).unwrap();
    let listed = contexts::list_context_sources(&f.db, &f.config).unwrap();
    let original = listed
        .iter()
        .map(|s| s["id"].as_i64().unwrap())
        .collect::<Vec<_>>();
    contexts::reorder_context_sources(&f.db, &[notes, id], &original).unwrap();
    assert!(contexts::reorder_context_sources(&f.db, &[id, notes], &original).is_err());
    assert!(
        contexts::add_context_root(&f.db, &f.config, root.join("child").to_str().unwrap()).is_err()
    );
    f.scan(&SyntheticReader::empty(), false);
    contexts::remove_context_root(&f.db, id, &NoObservers).unwrap();
    assert_eq!(f.count("context_documents"), 1);
    assert_eq!(f.count("resource_documents"), 1);
    assert_eq!(
        f.db.query_row(
            "SELECT count(*) FROM search_index WHERE entity_type='document'",
            [],
            |r| r.get::<_, i64>(0)
        )
        .unwrap(),
        0
    );
    assert_eq!(
        contexts::add_context_root(&f.db, &f.config, root.to_str().unwrap()).unwrap(),
        id
    );
    assert_eq!(
        contexts::get_context_root(&f.db, Some(id))
            .unwrap()
            .unwrap()["display_order"],
        1
    );
    assert_eq!(f.scan(&SyntheticReader::empty(), false), (1, 0, 0));
}
#[test]
fn individual_text_pdf_and_unsupported_files_keep_existing_type_and_readability_rules() {
    let f = Fixture::new();
    let path = f.config.home_dir.join("sample.c");
    fs::write(&path, "int main() {}\n").unwrap();
    let id = contexts::add_context_file(&f.db, &f.config, path.to_str().unwrap()).unwrap();
    let pdf = f.config.home_dir.join("sample.pdf");
    fs::write(&pdf, b"%PDF-1.0 synthetic").unwrap();
    let pdf_id = contexts::add_context_file(&f.db, &f.config, pdf.to_str().unwrap()).unwrap();
    let binary = f.config.home_dir.join("sample.bin");
    fs::write(&binary, [0u8, 255]).unwrap();
    let unsupported =
        contexts::add_context_file(&f.db, &f.config, binary.to_str().unwrap()).unwrap();
    let mut reader = SyntheticReader::empty();
    reader.pdf = Some("Synthetic Spotlight text".into());
    assert_eq!(f.scan(&reader, false), (2, 0, 0));
    let doc = db::row(
        &f.db,
        "SELECT * FROM context_documents WHERE context_root_id=?",
        [id],
    )
    .unwrap()
    .unwrap();
    assert_eq!(doc["content_type"], "text/x-c");
    assert_eq!(
        contexts::get_context_root(&f.db, Some(pdf_id))
            .unwrap()
            .unwrap()["status"],
        "ready"
    );
    assert_eq!(
        contexts::get_context_root(&f.db, Some(unsupported))
            .unwrap()
            .unwrap()["status"],
        "unreadable"
    );
    assert_eq!(f.count("context_documents"), 2);
    assert_eq!(fs::read(binary).unwrap(), [0, 255]);
}
#[test]
fn notes_uses_injected_data_and_preserves_virtual_identity_html_and_pruning() {
    let f = Fixture::new();
    let root = contexts::add_apple_notes_source(&f.db).unwrap();
    let reader = SyntheticReader {
        notes: json!([{"id":"x-coredata://note/a?b","title":"  A/B  ","account":"  Work  account  ","folders":["one/two"," 한글 "],"modified_at":"2026-11-01T01:02:03.123456Z","body":"<p>First &amp; second</p><div>한글</div>"}]),
        pdf: None,
        calls: AtomicUsize::new(0),
    };
    assert_eq!(f.scan(&reader, false), (1, 0, 0));
    let document = db::row(&f.db, "SELECT * FROM context_documents", [])
        .unwrap()
        .unwrap();
    assert_eq!(
        document["path"],
        "apple-notes://note/x-coredata%3A%2F%2Fnote%2Fa%3Fb"
    );
    assert_eq!(document["body"], "First & second\n한글");
    assert_eq!(document["title"], "A/B");
    assert!(document["relative_path"]
        .as_str()
        .unwrap()
        .starts_with("Work account/one_two/한글/A_B ["));
    assert_eq!(document["mtime_ns"], 1793494923123456000i64);
    let first = document["id"].clone();
    assert_eq!(f.scan(&reader, false), (1, 0, 0));
    assert_eq!(
        db::row(&f.db, "SELECT id FROM context_documents", [])
            .unwrap()
            .unwrap()["id"],
        first
    );
    assert_eq!(f.count("source_files"), 0);
    assert_eq!(f.scan(&SyntheticReader::empty(), false), (0, 0, 0));
    assert_eq!(f.count("context_documents"), 0);
    assert_eq!(
        contexts::get_context_root(&f.db, Some(root))
            .unwrap()
            .unwrap()["status"],
        "ready"
    );
}
#[test]
fn grouped_context_cancel_rolls_back_indexed_documents_and_keeps_originals() {
    let f = Fixture::new();
    let root = f.folder();
    fs::write(root.join("first.md"), "# First").unwrap();
    fs::write(root.join("second.md"), "# Second").unwrap();
    contexts::add_context_root(&f.db, &f.config, root.to_str().unwrap()).unwrap();
    let checks = Arc::new(AtomicUsize::new(0));
    let shared = checks.clone();
    let control = ScanControl {
        cancelled: Some(Arc::new(move || shared.fetch_add(1, Ordering::SeqCst) > 5)),
        progress: None,
    };
    let result = ingest::scan_context_sources_with_reader(
        &f.config,
        false,
        &control,
        &NoObservers,
        &SyntheticReader::empty(),
    );
    assert_eq!(result.unwrap_err().code, "interrupted");
    assert_eq!(f.count("context_documents"), 0);
    assert!(root.join("first.md").is_file());
    assert!(root.join("second.md").is_file());
}

#[test]
fn individual_markdown_keeps_its_explicit_content_type_even_without_os_mime_mapping() {
    let f = Fixture::new();
    let path = f.config.home_dir.join("individual.md");
    fs::write(&path, "# Individual title\ntext").unwrap();
    contexts::add_context_file(&f.db, &f.config, path.to_str().unwrap()).unwrap();
    assert_eq!(f.scan(&SyntheticReader::empty(), false), (1, 0, 0));
    let doc = db::row(&f.db, "SELECT * FROM context_documents", [])
        .unwrap()
        .unwrap();
    assert_eq!(doc["content_type"], "text/markdown");
    assert_eq!(doc["title"], "Individual title");
}
