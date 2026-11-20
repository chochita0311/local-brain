use localbrain_core::backend::{db, Config};
use rusqlite::Connection;
use serde_json::json;
use std::fs;
fn fixture() -> (tempfile::TempDir, Config) {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    let mut schema = db::SCHEMA.to_string();
    for name in [
        "reference_resources",
        "resource_documents",
        "resource_local_paths",
        "resource_external_links",
        "session_reference_evidence",
        "external_resource_content",
        "external_resource_notes",
    ] {
        let pattern = regex::Regex::new(&format!(
            r"(?s)CREATE TABLE IF NOT EXISTS {} \(.*?\n\);\n",
            name
        ))
        .unwrap();
        assert!(pattern.is_match(&schema));
        schema = pattern.replace(&schema, "").into_owned();
    }
    schema = schema.replace(
        "    resource_id INTEGER REFERENCES reference_resources(id) ON DELETE RESTRICT,\n",
        "",
    );
    schema = regex::Regex::new(
        r"(?s)CREATE INDEX IF NOT EXISTS idx_session_reference_evidence_\w+\n.*?;\n",
    )
    .unwrap()
    .replace_all(&schema, "")
    .into_owned();
    let connection = db::connect(&config).unwrap();
    connection
        .execute_batch(&format!("{OLD}\n{schema}"))
        .unwrap();
    connection.execute_batch(SEED).unwrap();
    connection.execute("INSERT INTO atlassian_item_content(external_resource_id,source_format,source_body,source_hash,normalized_document_json,normalized_text,normalizer_version,applied_at) VALUES (40,'plain_text','Preserved body',?,'{}','Preserved body','synthetic','fixed')",["a".repeat(64)]).unwrap();
    connection.execute("INSERT INTO atlassian_item_local_state(external_resource_id,note) VALUES (40,'Preserve user note')",[]).unwrap();
    for (id, kind, key, document, external, locator) in [
        (1, "context_document", "document:20", Some(20), None, None),
        (
            2,
            "atlassian_item",
            "atlassian:40",
            None,
            Some(40),
            Some("https://jira.example.test/browse/SYN-1"),
        ),
        (
            3,
            "url",
            "url:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            None,
            None,
            Some("https://jira.example.test/issues/SYN-1"),
        ),
    ] {
        connection.execute("INSERT INTO session_reference_evidence(id,session_id,source_path,source_event_id,source_line,evidence_ordinal,target_kind,target_key,context_document_id,external_resource_id,evidence_kind,observed_identity,normalized_url,extractor_version,evidence_key,first_observed_at,last_observed_at) VALUES (?,10,'/synthetic/s1.jsonl','event',?,1,?,?,?,?,'user_mention','Original observation',?,'v3',?,'first','last')",rusqlite::params![id,id,kind,key,document,external,locator,id.to_string().repeat(64)]).unwrap();
    }
    connection.execute("INSERT INTO session_reference_scans(session_id,source_fingerprint,extractor_version,status,observed_target_count,retained_target_count,scanned_at) VALUES (10,?,'v3','ok',3,3,'before')",["a".repeat(64)]).unwrap();
    drop(connection);
    (root, config)
}
#[test]
fn shared_resource_upgrade_preserves_curated_rows_payload_notes_and_evidence_ids() {
    let (_root, config) = fixture();
    let connection = db::connect(&config).unwrap();
    let mut before = std::collections::BTreeMap::new();
    for table in [
        "context_documents",
        "local_resources",
        "external_resources",
        "workstreams",
    ] {
        before.insert(
            table,
            db::rows(
                &connection,
                &format!("SELECT * FROM {table} ORDER BY id"),
                [],
            )
            .unwrap(),
        );
    }
    let body = db::rows(&connection, "SELECT * FROM atlassian_item_content", []).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    for (table, rows) in before {
        assert_eq!(
            db::rows(
                &connection,
                &format!("SELECT * FROM {table} ORDER BY id"),
                []
            )
            .unwrap(),
            rows,
            "{table}"
        );
    }
    assert_eq!(
        db::rows(&connection, "SELECT * FROM external_resource_content", []).unwrap(),
        body
    );
    assert_eq!(
        db::row(
            &connection,
            "SELECT note FROM external_resource_notes WHERE external_resource_id=40",
            []
        )
        .unwrap()
        .unwrap()["note"],
        "Preserve user note"
    );
    let evidence = db::rows(
        &connection,
        "SELECT id,resource_id,observed_identity FROM session_reference_evidence ORDER BY id",
        [],
    )
    .unwrap();
    assert_eq!(evidence.len(), 3);
    assert_eq!(evidence[0]["id"], 1);
    assert_eq!(evidence[1]["resource_id"], evidence[2]["resource_id"]);
    assert_eq!(evidence[0]["observed_identity"], "Original observation");
    assert_eq!(
        db::row(
            &connection,
            "SELECT observed_target_count,retained_target_count FROM session_reference_scans",
            []
        )
        .unwrap()
        .unwrap(),
        json!({"observed_target_count":2,"retained_target_count":2})
    );
    let links = db::rows(
        &connection,
        "SELECT id,resource_id FROM workstream_links ORDER BY id",
        [],
    )
    .unwrap();
    assert_eq!(links[0]["resource_id"], links[1]["resource_id"]);
    let backup = std::path::PathBuf::from(format!(
        "{}-pre-shared-resources-v1.bak",
        config.database_path.display()
    ));
    let saved = fs::read(&backup).unwrap();
    assert!(db::row(
        &Connection::open(&backup).unwrap(),
        "SELECT 1 FROM sqlite_master WHERE name='atlassian_item_content'",
        []
    )
    .unwrap()
    .is_some());
    drop(connection);
    db::initialize(&config).unwrap();
    assert_eq!(fs::read(backup).unwrap(), saved);
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::rows(
            &connection,
            "SELECT id,resource_id,observed_identity FROM session_reference_evidence ORDER BY id",
            []
        )
        .unwrap(),
        evidence
    );
    connection
        .execute_batch("DELETE FROM atlassian_items; DELETE FROM atlassian_sites")
        .unwrap();
    assert_eq!(
        db::rows(&connection, "SELECT * FROM external_resource_content", []).unwrap(),
        body
    );
    assert_eq!(
        connection
            .query_row(
                "SELECT COUNT(*) FROM session_reference_evidence",
                [],
                |row| row.get::<_, i64>(0)
            )
            .unwrap(),
        3
    );
}
#[test]
fn partial_reference_counts_keep_observed_total_and_require_rescan() {
    let (_root, config) = fixture();
    let connection = db::connect(&config).unwrap();
    connection.execute("UPDATE session_reference_scans SET status='partial',observed_target_count=101,retained_target_count=100",[]).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    assert_eq!(db::row(&connection,"SELECT status,observed_target_count,retained_target_count,error_code FROM session_reference_scans",[]).unwrap().unwrap(),json!({"status":"error","observed_target_count":101,"retained_target_count":2,"error_code":"resource-identity-migration"}));
}
#[test]
fn conflicting_external_payload_rolls_back_all_shared_resource_steps() {
    let (_root, config) = fixture();
    let connection = db::connect(&config).unwrap();
    let start = db::SCHEMA
        .find("CREATE TABLE IF NOT EXISTS external_resource_content (")
        .unwrap();
    let end = db::SCHEMA[start..].find("\n);").unwrap() + start + 3;
    connection.execute_batch(&db::SCHEMA[start..end]).unwrap();
    connection.execute("INSERT INTO external_resource_content SELECT external_resource_id,source_format,'Conflicting body',source_hash,normalized_document_json,normalized_text,normalizer_version,normalization_warning,remote_version,remote_updated_at,applied_at,search_projection_hash,updated_at FROM atlassian_item_content",[]).unwrap();
    let before = db::rows(
        &connection,
        "SELECT * FROM session_reference_evidence ORDER BY id",
        [],
    )
    .unwrap();
    drop(connection);
    assert!(db::initialize(&config).is_err());
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::rows(
            &connection,
            "SELECT * FROM session_reference_evidence ORDER BY id",
            []
        )
        .unwrap(),
        before
    );
    assert!(db::row(
        &connection,
        "SELECT 1 FROM sqlite_master WHERE name='reference_resources'",
        []
    )
    .unwrap()
    .is_none());
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM atlassian_item_content", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
}
const SEED: &str = r###"
INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'context','Synthetic','/synthetic');
INSERT INTO context_roots(id,path,label) VALUES (1,'/synthetic','Synthetic');
INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (10,1,'s1','/synthetic/s1.jsonl','Session 1'),(11,1,'s2','/synthetic/s2.jsonl','Session 2');
INSERT INTO context_documents(id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash) VALUES (20,1,1,'/synthetic/guide.md','guide.md','Guide','Synthetic body',14,1,'hash');
INSERT INTO local_resources(id,path,resource_type,title,summary,discovered_by) VALUES (30,'/synthetic/guide.md','file','Manual label','Manual note','user');
INSERT INTO external_resources(id,resource_type,title,url,summary,source_role) VALUES (40,'jira_issue','Manual issue','https://jira.example.test/browse/SYN-1','Preserve note','user');
INSERT INTO atlassian_sites(id,normalized_domain,canonical_base_url) VALUES (50,'jira.example.test','https://jira.example.test');
INSERT INTO atlassian_items(external_resource_id,site_id,service,item_type,remote_key) VALUES (40,50,'jira','jira_issue','SYN-1');
INSERT INTO workstreams(id,name,summary) VALUES (60,'Pilot','Manual work note');
INSERT INTO workstream_links(id,workstream_id,entity_type,entity_id,relation_type,confidence,linked_by) VALUES (70,60,'local','30','reference',0.8,'user'),(71,60,'document','20','evidence',1,'user');
"###;
const OLD: &str = r###"-- Pre-REFACTOR-0005 DDL retained to verify the preserving migration.

CREATE TABLE IF NOT EXISTS session_reference_evidence (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL
        REFERENCES sessions(id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    source_event_id TEXT,
    source_line INTEGER NOT NULL CHECK(source_line > 0),
    evidence_ordinal INTEGER NOT NULL CHECK(evidence_ordinal > 0),
    target_kind TEXT NOT NULL
        CHECK(target_kind IN ('url', 'context_document', 'atlassian_item')),
    target_key TEXT NOT NULL,
    context_document_id INTEGER
        REFERENCES context_documents(id) ON DELETE CASCADE,
    external_resource_id INTEGER
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    evidence_kind TEXT NOT NULL
        CHECK(
            evidence_kind IN (
                'user_mention',
                'assistant_mention',
                'tool_result',
                'resource_read'
            )
        ),
    read_outcome TEXT
        CHECK(read_outcome IS NULL OR read_outcome IN ('success', 'failure')),
    observed_identity TEXT NOT NULL,
    normalized_url TEXT,
    tool_name TEXT,
    tool_call_id TEXT,
    observed_at TEXT,
    extractor_version TEXT NOT NULL,
    evidence_key TEXT NOT NULL UNIQUE,
    first_observed_at TEXT NOT NULL,
    last_observed_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(source_path) > 0 AND length(source_path) <= 8000),
    CHECK(
        source_event_id IS NULL
        OR (length(source_event_id) > 0 AND length(source_event_id) <= 1000)
    ),
    CHECK(length(target_key) > 0 AND length(target_key) <= 300),
    CHECK(length(observed_identity) > 0 AND length(observed_identity) <= 500),
    CHECK(
        normalized_url IS NULL
        OR (length(normalized_url) > 0 AND length(normalized_url) <= 8000)
    ),
    CHECK(tool_name IS NULL OR (length(tool_name) > 0 AND length(tool_name) <= 200)),
    CHECK(
        tool_call_id IS NULL
        OR (length(tool_call_id) > 0 AND length(tool_call_id) <= 500)
    ),
    CHECK(length(extractor_version) > 0 AND length(extractor_version) <= 80),
    CHECK(length(evidence_key) = 64),
    CHECK(
        (
            target_kind = 'url'
            AND context_document_id IS NULL
            AND external_resource_id IS NULL
            AND normalized_url IS NOT NULL
        )
        OR (
            target_kind = 'context_document'
            AND context_document_id IS NOT NULL
            AND external_resource_id IS NULL
            AND normalized_url IS NULL
        )
        OR (
            target_kind = 'atlassian_item'
            AND context_document_id IS NULL
            AND external_resource_id IS NOT NULL
            AND normalized_url IS NOT NULL
        )
    ),
    CHECK(
        (
            evidence_kind IN ('user_mention', 'assistant_mention')
            AND read_outcome IS NULL
            AND tool_name IS NULL
            AND tool_call_id IS NULL
        )
        OR (
            evidence_kind = 'tool_result'
            AND read_outcome IS NULL
            AND tool_name IS NOT NULL
            AND tool_call_id IS NOT NULL
        )
        OR (
            evidence_kind = 'resource_read'
            AND read_outcome IS NOT NULL
            AND tool_name IS NOT NULL
            AND tool_call_id IS NOT NULL
        )
    )
);

CREATE TABLE IF NOT EXISTS atlassian_item_content (
    external_resource_id INTEGER PRIMARY KEY
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    source_format TEXT NOT NULL
        CHECK(
            source_format IN (
                'jira_adf',
                'confluence_adf',
                'confluence_html',
                'confluence_markdown',
                'plain_text'
            )
        ),
    source_body TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    normalized_document_json TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    normalizer_version TEXT NOT NULL,
    normalization_warning TEXT,
    remote_version TEXT,
    remote_updated_at TEXT,
    applied_at TEXT NOT NULL,
    search_projection_hash TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(source_hash) = 64),
    CHECK(search_projection_hash IS NULL OR length(search_projection_hash) = 64)
);

CREATE TABLE IF NOT EXISTS atlassian_item_local_state (
    external_resource_id INTEGER PRIMARY KEY
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(note) <= 50000)
);
"###;
