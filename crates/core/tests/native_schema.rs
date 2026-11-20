use localbrain_core::backend::{db, references, schema};
use serde_json::Value;
#[test]
fn native_schema_navigation_matches_complete_frozen_python_views() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/native-schema-view.json")).unwrap();
    assert!(schema::valid_manifest(&fixture["manifest"]));
    for case in fixture["cases"].as_array().unwrap() {
        let value = schema::build_schema_explorer_view(
            &fixture["manifest"],
            case["area"].as_str(),
            case["table"].as_str(),
        );
        assert_eq!(
            references::hash_payload(&value),
            case["sha256"],
            "area={} table={}",
            case["area"],
            case["table"]
        );
    }
    let compiled: Value =
        serde_json::from_str(include_str!("../resources/schema-presentation.json")).unwrap();
    assert!(schema::valid_manifest(&compiled));
    assert!(schema::schema_explorer_page_data(None, None)["available"] == true);
}
#[test]
fn build_tools_rehydrate_actual_effective_native_schema_without_runtime_data() {
    let statements = db::effective_schema_sql().unwrap();
    assert!(statements.len() > 50);
    let conn = rusqlite::Connection::open_in_memory().unwrap();
    conn.execute_batch(&statements.join(";\n")).unwrap();
    let count: i64 = conn
        .query_row(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
            [],
            |row| row.get(0),
        )
        .unwrap();
    assert!(count > 40);
    assert!(conn
        .prepare("SELECT display_title,session_role,index_policy FROM sessions")
        .is_ok());
}

#[test]
fn schema_loader_retains_missing_and_malformed_manifest_states() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("schema.json");
    let missing = schema::load_schema_presentation(&path);
    assert_eq!(missing["available"], false);
    assert_eq!(missing["error_code"], "manifest-unavailable");
    std::fs::write(&path, "not-json").unwrap();
    let invalid = schema::load_schema_presentation(&path);
    assert_eq!(invalid["available"], false);
    assert_eq!(invalid["error_code"], "manifest-invalid");
    let original: Value =
        serde_json::from_str(include_str!("../resources/schema-presentation.json")).unwrap();
    for index in 0..3 {
        let mut value = original.clone();
        match index {
            0 => value["schema"] = "localbrain.schema-presentation.v2".into(),
            1 => {
                value.as_object_mut().unwrap().remove("global");
            }
            _ => {
                value["subjects"][0]["table_ids"]
                    .as_array_mut()
                    .unwrap()
                    .pop();
            }
        }
        std::fs::write(&path, serde_json::to_vec(&value).unwrap()).unwrap();
        let invalid = schema::load_schema_presentation(&path);
        assert_eq!(invalid["available"], false, "mutation{index}");
        assert_eq!(invalid["error_code"], "manifest-invalid", "mutation{index}");
    }
    std::fs::write(&path, serde_json::to_vec(&original).unwrap()).unwrap();
    let valid = schema::load_schema_presentation(&path);
    assert_eq!(valid["available"], true);
    assert_eq!(valid["manifest"], original);
}
