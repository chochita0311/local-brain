//! Read-only data-model guide, derived from the documented schema snapshot.
use serde_json::{json, Value};
use std::{collections::BTreeSet, path::Path, sync::OnceLock};
fn nonempty(value: &Value, key: &str) -> bool {
    value[key]
        .as_str()
        .is_some_and(|value| !value.trim_matches(super::unicode::python_space).is_empty())
}
pub fn valid_manifest(manifest: &Value) -> bool {
    let baseline = &manifest["baseline"];
    let subjects = &manifest["subjects"];
    let tables = &manifest["tables"];
    let relationships = &manifest["relationships"];
    if manifest["schema"] != "localbrain.schema-presentation.v1"
        || manifest["derived"] != true
        || !nonempty(baseline, "id")
        || ![
            "ordinary_table_count",
            "fts5_table_count",
            "physical_foreign_key_count",
            "explicit_index_count",
            "subject_count",
        ]
        .iter()
        .all(|key| baseline[key].as_u64().is_some())
        || !baseline["sources"].as_array().is_some_and(|sources| {
            !sources.is_empty()
                && sources.iter().all(|source| {
                    nonempty(source, "path")
                        && nonempty(source, "role")
                        && source["sha256"]
                            .as_str()
                            .is_some_and(|value| value.chars().count() == 64)
                })
        })
        || !nonempty(&manifest["global"], "mermaid")
    {
        return false;
    }
    let (Some(subjects), Some(tables), Some(physical), Some(application)) = (
        subjects.as_array(),
        tables.as_array(),
        relationships["physical"].as_array(),
        relationships["application"].as_array(),
    ) else {
        return false;
    };
    if subjects.len() as u64 != baseline["subject_count"].as_u64().unwrap()
        || tables.len() as u64
            != baseline["ordinary_table_count"].as_u64().unwrap()
                + baseline["fts5_table_count"].as_u64().unwrap()
        || physical.len() as u64 != baseline["physical_foreign_key_count"].as_u64().unwrap()
    {
        return false;
    }
    if !physical.iter().chain(application).all(|item| {
        nonempty(item, "source_table")
            && nonempty(item, "target_table")
            && item["enforcement"]
                .as_str()
                .is_some_and(|value| ["sqlite-foreign-key", "application"].contains(&value))
    }) {
        return false;
    }
    if !subjects.iter().all(|subject| {
        ["id", "label", "document", "mermaid"]
            .iter()
            .all(|key| nonempty(subject, key))
            && subject["table_ids"].as_array().is_some_and(|ids| {
                !ids.is_empty()
                    && ids
                        .iter()
                        .all(|id| id.as_str().is_some_and(|id| !id.is_empty()))
            })
    }) {
        return false;
    }
    if !tables.iter().all(|table| {
        table["kind"]
            .as_str()
            .is_some_and(|kind| ["ordinary", "fts5"].contains(&kind))
            && ["id", "subject_id", "semantic_document"]
                .iter()
                .all(|key| nonempty(table, key))
            && table["columns"].as_array().is_some_and(|columns| {
                !columns.is_empty()
                    && columns.iter().all(|column| {
                        nonempty(column, "name")
                            && column.get("type").is_some()
                            && column["not_null"].is_boolean()
                            && column.get("default_sql").is_some()
                            && column["primary_key_position"].as_i64().is_some()
                            && nonempty(column, "semantic_contract")
                    })
            })
            && table["constraints"].as_object().is_some_and(|map| {
                ["primary_key", "unique", "checks", "documented"]
                    .iter()
                    .all(|key| map.contains_key(*key))
            })
            && table["indexes"].is_array()
            && table["foreign_keys"].is_array()
            && [
                "purpose_and_authority",
                "lifecycle_contract",
                "class",
                "rebuildability",
                "class_contract",
                "producers",
                "consumers",
                "deletion_effect",
                "recovery_path",
                "schema_ownership",
                "documented_constraints",
            ]
            .iter()
            .all(|key| nonempty(&table["semantics"], key))
    }) {
        return false;
    }
    let table_ids = tables
        .iter()
        .map(|table| table["id"].as_str().unwrap())
        .collect::<BTreeSet<_>>();
    let subject_ids = subjects
        .iter()
        .map(|subject| subject["id"].as_str().unwrap())
        .collect::<BTreeSet<_>>();
    let mut owned = subjects
        .iter()
        .flat_map(|subject| {
            subject["table_ids"]
                .as_array()
                .unwrap()
                .iter()
                .map(|id| id.as_str().unwrap())
        })
        .collect::<Vec<_>>();
    owned.sort();
    table_ids.len() == tables.len()
        && subject_ids.len() == subjects.len()
        && owned == table_ids.into_iter().collect::<Vec<_>>()
        && tables.iter().all(|table| {
            subjects
                .iter()
                .find(|subject| subject["id"] == table["subject_id"])
                .is_some_and(|subject| {
                    subject["table_ids"]
                        .as_array()
                        .unwrap()
                        .contains(&table["id"])
                })
        })
}
pub fn load_schema_presentation(path: &Path) -> Value {
    let bytes = match std::fs::read(path) {
        Ok(bytes) => bytes,
        Err(_) => return json!({"available":false,"error_code":"manifest-unavailable"}),
    };
    match serde_json::from_slice::<Value>(&bytes) {
        Ok(manifest) if valid_manifest(&manifest) => json!({"available":true,"manifest":manifest}),
        _ => json!({"available":false,"error_code":"manifest-invalid"}),
    }
}
pub fn schema_href(area: Option<&str>, table: Option<&str>) -> String {
    let mut params = vec![];
    if let Some(area) = area {
        params.push(("area", area.into()));
    }
    if let Some(table) = table {
        params.push(("table", table.into()));
    }
    if params.is_empty() {
        "/schema".into()
    } else {
        format!("/schema?{}", super::search::urlencode(&params))
    }
}
pub fn build_schema_explorer_view(
    manifest: &Value,
    area: Option<&str>,
    table: Option<&str>,
) -> Value {
    let selected_subject = area.and_then(|area| {
        manifest["subjects"]
            .as_array()?
            .iter()
            .find(|subject| subject["id"] == area)
    });
    let mut notice = if area.is_some() && selected_subject.is_none() {
        json!({"code":"invalid-area","message":"해당 주제 영역을 찾을 수 없어 전체 모델을 표시합니다."})
    } else {
        Value::Null
    };
    let mut selected_table = None;
    if let Some(subject) = selected_subject {
        if let Some(table) = table {
            selected_table = manifest["tables"]
                .as_array()
                .unwrap()
                .iter()
                .find(|candidate| {
                    candidate["id"] == table && candidate["subject_id"] == subject["id"]
                });
            if selected_table.is_none() {
                notice = json!({"code":"invalid-table","message":"해당 영역에서 테이블을 찾을 수 없어 영역 개요를 표시합니다."});
            }
        }
    } else if table.is_some() && notice.is_null() {
        notice = json!({"code":"table-requires-area","message":"테이블을 보려면 먼저 주제 영역을 선택하세요."});
    }
    let subjects = manifest["subjects"]
        .as_array()
        .unwrap()
        .iter()
        .map(|subject| {
            let mut subject = subject.clone();
            subject["href"] = json!(schema_href(subject["id"].as_str(), None));
            subject["current"] =
                json!(selected_subject.is_some_and(|selected| selected["id"] == subject["id"]));
            subject
        })
        .collect::<Vec<_>>();
    let selected_view = subjects.iter().find(|subject| subject["current"] == true);
    let tables=selected_subject.map(|subject|subject["table_ids"].as_array().unwrap().iter().map(|id|{let table=manifest["tables"].as_array().unwrap().iter().find(|table|table["id"]==*id).unwrap();json!({"id":id,"kind":table["kind"],"column_count":table["columns"].as_array().unwrap().len(),"purpose":table["semantics"]["purpose_and_authority"],"href":schema_href(subject["id"].as_str(),id.as_str()),"current":selected_table.is_some_and(|table|table["id"]==*id)})}).collect::<Vec<_>>()).unwrap_or_default();
    let mut relationships = json!({"physical":[],"application":[]});
    if let Some(table) = selected_table {
        for kind in ["physical", "application"] {
            relationships[kind] = json!(manifest["relationships"][kind]
                .as_array()
                .unwrap()
                .iter()
                .filter(|item| item["source_table"] == table["id"]
                    || item["target_table"] == table["id"])
                .collect::<Vec<_>>());
        }
    }
    let mut baseline = manifest["baseline"].clone();
    baseline["object_count"] = json!(
        baseline["ordinary_table_count"].as_u64().unwrap()
            + baseline["fts5_table_count"].as_u64().unwrap()
    );
    json!({"available":true,"schema":manifest["schema"],"mode":if selected_table.is_some(){"table"}else if selected_subject.is_some(){"area"}else{"global"},"notice":notice,"baseline":baseline,"subjects":subjects,"selected_subject":selected_view,"area_tables":tables,"selected_table":selected_table,"relationships":relationships,"diagram":selected_view.map(|subject|&subject["mermaid"]).unwrap_or(&manifest["global"]["mermaid"]),"diagram_label":selected_view.map(|subject|format!("{} 관계 모델",subject["label"].as_str().unwrap())).unwrap_or_else(||"전체 LocalBrain 데이터 모델".into()),"global_href":schema_href(None,None)})
}
pub fn schema_explorer_page_data(area: Option<&str>, table: Option<&str>) -> Value {
    static MANIFEST: OnceLock<Value> = OnceLock::new();
    let manifest = MANIFEST.get_or_init(|| {
        serde_json::from_str(include_str!("../../resources/schema-presentation.json"))
            .expect("compiled schema presentation")
    });
    if !valid_manifest(manifest) {
        return json!({"available":false,"error_code":"manifest-invalid","message":"스키마 설명을 불러올 수 없습니다. 패키지 데이터가 갱신된 뒤 다시 시도하세요."});
    }
    build_schema_explorer_view(manifest, area, table)
}
