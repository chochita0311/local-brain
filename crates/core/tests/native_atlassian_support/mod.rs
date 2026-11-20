//! Shared complete-call fixture replay; server-generated time alone is normalized.
use localbrain_core::backend::{clock, db, Result};
use rusqlite::{params_from_iter, types::Value as SqlValue, Connection};
use serde_json::{json, Map, Value};
use std::time::{SystemTime, UNIX_EPOCH};
pub fn restore(db: &Connection, state: &Value) {
    db.execute_batch("PRAGMA foreign_keys=OFF").unwrap();
    for (table, rows) in state.as_object().unwrap() {
        if table == "sqlite_sequence" {
            db.execute("DELETE FROM sqlite_sequence", []).unwrap();
        }
        for row in rows.as_array().unwrap() {
            let row = row.as_object().unwrap();
            let keys = row.keys().map(String::as_str).collect::<Vec<_>>();
            let values = keys
                .iter()
                .map(|key| match &row[*key] {
                    Value::Null => SqlValue::Null,
                    Value::String(s) => SqlValue::Text(s.clone()),
                    Value::Number(n) => n
                        .as_i64()
                        .map(SqlValue::Integer)
                        .unwrap_or_else(|| SqlValue::Real(n.as_f64().unwrap())),
                    other => panic!("unexpected SQL scalar {other}"),
                })
                .collect::<Vec<_>>();
            let columns = keys
                .iter()
                .map(|k| if *k == "__rowid__" { "rowid" } else { k })
                .collect::<Vec<_>>();
            db.execute(
                &format!(
                    "INSERT INTO \"{table}\"({}) VALUES ({})",
                    columns.join(","),
                    vec!["?"; keys.len()].join(",")
                ),
                params_from_iter(values),
            )
            .unwrap();
        }
    }
    db.execute_batch("PRAGMA foreign_keys=ON").unwrap();
}
fn snapshot(db: &Connection) -> Value {
    let tables = db::rows(db,"SELECT name FROM sqlite_schema WHERE type='table' AND (name NOT LIKE 'sqlite_%' OR name='sqlite_sequence') ORDER BY name",[]).unwrap();
    let mut out = Map::new();
    for table in tables {
        let table = table["name"].as_str().unwrap();
        if table.starts_with("search_index_") {
            continue;
        }
        let prefix = if table == "search_index" {
            "rowid AS __rowid__, "
        } else {
            ""
        };
        let rows = db::rows(db, &format!("SELECT {prefix}* FROM \"{table}\""), []).unwrap();
        if !rows.is_empty() {
            out.insert(table.into(), json!(rows));
        }
    }
    Value::Object(out)
}
fn normalized(mut value: Value, windows: &[(f64, f64)]) -> Value {
    let mut stack = vec![&mut value];
    while let Some(value) = stack.pop() {
        match value {
            Value::String(text) => {
                let parsed = clock::parse_timestamp(text).or_else(|| {
                    chrono::NaiveDateTime::parse_from_str(text, "%Y-%m-%d %H:%M:%S")
                        .ok()
                        .map(|v| v.and_utc())
                });
                if parsed.is_some_and(|time| {
                    windows.iter().any(|(start, end)| {
                        let t = time.timestamp_micros() as f64 / 1e6;
                        t >= *start && t <= *end
                    })
                }) {
                    *text = "__server_generated_time__".into();
                }
            }
            Value::Array(values) => stack.extend(values),
            Value::Object(values) => stack.extend(values.values_mut()),
            _ => {}
        }
    }
    value
}

pub fn replay(cases: &[Value], call: impl Fn(&Connection, &str, &Value) -> Result<Value>) {
    let capture_start = cases
        .iter()
        .map(|v| v["started"].as_f64().unwrap())
        .fold(f64::INFINITY, f64::min)
        - 2.0;
    let capture_end = cases
        .iter()
        .map(|v| v["finished"].as_f64().unwrap())
        .fold(0.0, f64::max)
        + 2.0;
    let started = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64()
        - 2.0;
    let mut failures = vec![];
    for (i, case) in cases.iter().enumerate() {
        let db = Connection::open_in_memory().unwrap();
        db.execute_batch(db::SCHEMA).unwrap();
        if let Some(before) = case.get("before") {
            restore(&db, before);
        }
        let changes = db.total_changes();
        let result = call(&db, case["operation"].as_str().unwrap(), &case["values"]);
        if case["changes"] == 0 {
            assert_eq!(
                db.total_changes(),
                changes,
                "read-only call {}",
                case["case"]
            );
        }
        let end = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs_f64()
            + 2.0;
        let windows = [(capture_start, capture_end), (started, end)];
        let actual = match result {
            Ok(v) => json!({"expected":v}),
            Err(e) => {
                json!({"error":{"code":if case["error"]["code"].is_null(){Value::Null}else{json!(e.code)},"message":e.message}})
            }
        };
        let expected = if let Some(error) = case.get("error") {
            json!({"error":{"code":error["code"],"message":error["message"]}})
        } else {
            json!({"expected":case["expected"]})
        };
        let a = normalized(actual, &windows);
        let e = normalized(expected, &windows);
        if a != e {
            failures.push(format!(
                "case{i} {} {} result\nactual:{a}\nexpected:{e}",
                case["case"], case["operation"]
            ));
            continue;
        }
        if let Some(after) = case.get("after") {
            let actual = normalized(snapshot(&db), &windows);
            let expected = normalized(after.clone(), &windows);
            if actual != expected {
                for table in expected
                    .as_object()
                    .unwrap()
                    .keys()
                    .chain(actual.as_object().unwrap().keys())
                {
                    if actual[table] != expected[table] {
                        failures.push(format!(
                            "case{i} {} {} table={table}\nactual:{}\nexpected:{}",
                            case["case"], case["operation"], actual[table], expected[table]
                        ));
                        break;
                    }
                }
            }
        }
    }
    assert!(
        failures.is_empty(),
        "{} failures:\n{}",
        failures.len(),
        failures.join("\n\n")
    );
}
