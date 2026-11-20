use chrono::{DateTime, NaiveDate, Utc};
use localbrain_core::backend::learning::*;
use rusqlite::Connection;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn now(value: &str) -> DateTime<Utc> {
    DateTime::parse_from_rfc3339(value)
        .unwrap()
        .with_timezone(&Utc)
}
fn day(value: &str) -> NaiveDate {
    NaiveDate::parse_from_str(value, "%Y-%m-%d").unwrap()
}
fn connection() -> Connection {
    let db = Connection::open_in_memory().unwrap();
    db.pragma_update(None, "foreign_keys", "ON").unwrap();
    db.execute_batch(include_str!("../resources/schema.sql"))
        .unwrap();
    db
}
fn hash(value: &str) -> String {
    format!("{:x}", Sha256::digest(value.as_bytes()))
}
fn packet() -> Value {
    json!({"version":1,"lessons":[{
    "key":"demo-http","title":"Demo HTTP lesson","topic":"HTTP","why":"Invented read-only report","explanation":"A safe method requests read-only semantics.","reviewed_by":"owner","version_status":"unverified","applicability":"Synthetic local example",
    "sources":[{"id":"work","kind":"work","title":"Demo report","locator":"synthetic report","checked_on":"2020-01-01","version":"demo","snapshot":"GET /report"},
        {"id":"official","kind":"official","title":"HTTP semantics","locator":"RFC9110","checked_on":"2020-01-01","version":"unknown","snapshot":"Safe semantics are read-only.","url":"https://example.test/official/http"}],
    "questions":[{"id":"q1","kind":"recall","prompt":"What does safe mean?","hint":"Requested semantics","answer":"Read-only request semantics.","source_ids":["official"]}]}]})
}
fn scene_packet() -> Value {
    let mut packet = packet();
    packet["version"] = json!(2);
    let lesson = &mut packet["lessons"][0];
    lesson["sources"][0]["snapshot"] = json!("  GET /report\n");
    lesson["scene"] = json!({"kind":"command","source_id":"work","origin":"source","title":"Preserved command","language":"Shell / Bash","context":"Synthetic fixture context","conditions":"No command is executed by this test.","captured_at":"2020-01-02T03:04:05Z","occurred_on":null,"code":"echo demo\n","execution":"reported","output":""});
    lesson["selection"] = json!({"signal":"requested","reason":"Explicit synthetic fixture"});
    lesson["authorship"] =
        json!({"author":"owner","method":"manual","reviewer":"owner","authored_on":"2020-01-02"});
    let question = &mut lesson["questions"][0];
    question["source_ids"] = json!(["work", "official"]);
    question["concept_id"] = json!("http");
    question["depth"] = json!("understand");
    question["focus_lines"] = json!([1]);
    question["rationale"] = json!("Synthetic understanding check");
    question["rubric"] = json!(["Requested read-only semantics."]);
    packet
}
fn fields(token: &str) -> Value {
    json!({"action":"answer","submission_key":token,"question_id":"q1","answer":"Read-only semantics","confidence":"high","hint_used":"0"})
}
fn import(db: &Connection, packet: &Value) -> i64 {
    import_packet_at(db, packet, "UTC", now("2026-11-18T12:00:00Z")).unwrap();
    db.query_row("SELECT max(id) FROM learning_lessons", [], |row| row.get(0))
        .unwrap()
}

#[test]
fn normalized_revision_hashes_match_frozen_python311_oracles() {
    // Recorded from the original validate_packet + sorted compact ensure_ascii=False JSON.
    let v1 = validate_packet(&packet(), day("2026-11-18"))
        .unwrap()
        .remove(0);
    assert_eq!(
        hash(&canonical_json(&v1).unwrap()),
        "75830c68c9aecebef2c5ab1db53bcda28d7fee27064bbe9cb41134e33bab35b5"
    );
    let v2 = validate_packet(&scene_packet(), day("2026-11-18"))
        .unwrap()
        .remove(0);
    assert_eq!(
        hash(&canonical_json(&v2).unwrap()),
        "7c618d94864a48617ae4783d828c25449ea770ba42d7156958df71f097fb18bf"
    );
    assert_eq!(v2["sources"][0]["snapshot"], "  GET /report\n");
    assert_eq!(v2["scene"]["captured_at"], "2020-01-02T03:04:05+00:00");
    assert!(v2.get("article").is_none());
    let mut diff = scene_packet();
    let scene = &mut diff["lessons"][0]["scene"];
    for field in ["code", "execution", "output"] {
        scene.as_object_mut().unwrap().remove(field);
    }
    let before = "one\ntwo";
    let after = "one\nthree";
    scene["kind"] = json!("diff");
    scene["language"] = json!("Rust");
    scene["repo"] = json!("synthetic-repo");
    scene["path"] = json!("x.rs");
    scene["before_ref"] = json!(format!("sha256:{}", hash(before)));
    scene["after_ref"] = json!("1".repeat(40));
    scene["git_state"] = json!("unstaged");
    scene["before"] = json!(before);
    scene["after"] = json!(after);
    let normalized = validate_packet(&diff, day("2026-11-18")).unwrap().remove(0);
    assert_eq!(
        hash(&canonical_json(&normalized).unwrap()),
        "66b111189288319d1899381c1183cd706e6d685cf8e1605d67b2597bd66e73d7"
    );
    assert_eq!(
        normalized["scene"]["code_sha256"],
        "d2f2aa3af93ad5a1f2fdd032552007dd763f88ef4b1bdf188b8638332f0a7e20"
    );
}
#[test]
fn revisions_append_and_old_reimport_never_rolls_current_back() {
    let db = connection();
    let original = packet();
    assert_eq!(
        import_packet_at(&db, &original, "UTC", now("2026-11-18T12:00:00Z")).unwrap()["inserted"],
        1
    );
    let first = lesson_by_id(&db, 1).unwrap()["packet_json"].clone();
    let mut revised = original.clone();
    revised["lessons"][0]["explanation"] = json!("Revised, reviewed explanation.");
    assert_eq!(
        import_packet_at(&db, &revised, "UTC", now("2026-11-18T12:00:00Z")).unwrap()["inserted"],
        1
    );
    assert_eq!(
        import_packet_at(&db, &original, "UTC", now("2026-11-18T12:00:00Z")).unwrap()["unchanged"],
        1
    );
    assert_eq!(lesson_by_id(&db, 1).unwrap()["packet_json"], first);
    let library = library_at(&db, "UTC", now("2026-11-18T12:00:00Z")).unwrap();
    assert_eq!(library.len(), 1);
    assert_eq!(library[0]["id"], 2);
}
#[test]
fn invalid_whole_packet_and_missing_work_links_write_nothing() {
    let db = connection();
    let mut raw = packet();
    let mut invalid = raw["lessons"][0].clone();
    invalid["key"] = json!("demo-invalid");
    invalid["questions"][0]["source_ids"] = json!(["missing"]);
    raw["lessons"].as_array_mut().unwrap().push(invalid);
    assert!(import_packet_at(&db, &raw, "UTC", now("2026-11-18T12:00:00Z")).is_err());
    assert_eq!(
        db.query_row("SELECT count(*) FROM learning_lessons", [], |row| row
            .get::<_, i64>(0))
            .unwrap(),
        0
    );
    let mut raw = packet();
    raw["lessons"][0]["sources"][0]["url"] = json!("/sessions/999999");
    assert!(import_packet_at(&db, &raw, "UTC", now("2026-11-18T12:00:00Z")).is_err());
    assert_eq!(
        db.query_row("SELECT count(*) FROM learning_lessons", [], |row| row
            .get::<_, i64>(0))
            .unwrap(),
        0
    );
}
#[test]
fn submissions_replay_and_self_assessment_is_one_way() {
    let db = connection();
    let lesson = import(&db, &packet());
    let answer = fields("demo-submission");
    let timestamp = now("2026-11-18T12:00:00Z");
    let attempt = submit_attempt_at(&db, lesson, &answer, timestamp).unwrap();
    assert_eq!(
        submit_attempt_at(&db, lesson, &answer, timestamp).unwrap(),
        attempt
    );
    let mut changed = answer.clone();
    changed["answer"] = json!("different");
    assert!(submit_attempt_at(&db, lesson, &changed, timestamp).is_err());
    assess_attempt_at(&db, lesson, attempt, "recalled", timestamp).unwrap();
    assess_attempt_at(&db, lesson, attempt, "recalled", timestamp).unwrap();
    assert!(assess_attempt_at(&db, lesson, attempt, "again", timestamp).is_err());
    assert_eq!(attempts_for(&db, lesson).unwrap().len(), 1);
    assert!(db
        .execute("DELETE FROM learning_lessons WHERE id=?", [lesson])
        .is_err());
}
#[test]
fn read_is_completed_without_answer_confidence_hint_or_recall_credit() {
    let db = connection();
    let lesson = import(&db, &packet());
    let timestamp = now("2026-11-18T12:00:00Z");
    let attempt=submit_attempt_at(&db,lesson,&json!({"action":"read","submission_key":"demo-read","question_id":"q1","from_note":"1","hint_used":"1"}),timestamp).unwrap();
    let saved = attempts_for(&db, lesson).unwrap().remove(0);
    assert_eq!(
        (
            saved["answer"].clone(),
            saved["confidence"].clone(),
            saved["hint_used"].clone(),
            saved["outcome"].clone()
        ),
        (json!(""), Value::Null, json!(0), json!("read"))
    );
    assert!(!saved["assessed_at"].is_null());
    assert!(assess_attempt_at(&db, lesson, attempt, "recalled", timestamp).is_err());
    assert_eq!(
        schedule(&[saved], "UTC", None).unwrap()["due"],
        "2026-11-19"
    );
}
#[test]
fn visibility_is_reversible_and_shared_across_revisions() {
    let db = connection();
    let lesson = import(&db, &packet());
    let timestamp = now("2026-11-18T12:00:00Z");
    set_visibility_at(&db, lesson, "hide", "UTC", timestamp).unwrap();
    let mut revised = packet();
    revised["lessons"][0]["title"] = json!("Revised demo");
    let newest = import(&db, &revised);
    assert_eq!(library_at(&db, "UTC", timestamp).unwrap()[0]["hidden"], 1);
    set_visibility_at(&db, newest, "restore", "UTC", timestamp).unwrap();
    let library = library_at(&db, "UTC", timestamp).unwrap();
    assert_eq!(library[0]["hidden"], 0);
    assert!(library[0]["snoozed_until"].is_null());
    set_visibility_at(
        &db,
        newest,
        "snooze",
        "Asia/Seoul",
        now("2026-11-18T16:00:00Z"),
    )
    .unwrap();
    assert_eq!(
        library_at(&db, "Asia/Seoul", now("2026-11-18T16:00:00Z")).unwrap()[0]["snoozed_until"],
        "2026-11-20"
    );
    assert!(attempts_for(&db, newest).unwrap().is_empty());
}
fn attempt(identifier: i64, stamp: &str, outcome: &str, hint: i64) -> Value {
    json!({"id":identifier,"question_id":"q1","submitted_at":stamp,"assessed_at":if outcome=="pending"{Value::Null}else{json!(stamp)},"outcome":outcome,"hint_used":hint})
}
#[test]
fn scheduling_uses_distinct_local_dates_and_conservative_help() {
    let a = attempt(1, "2026-11-01T12:00:00+00:00", "recalled", 0);
    let b = attempt(2, "2026-11-02T12:00:00+00:00", "recalled", 0);
    let c = attempt(3, "2026-11-03T12:00:00+00:00", "recalled", 0);
    assert_eq!(
        schedule(std::slice::from_ref(&a), "UTC", None).unwrap()["due"],
        "2026-11-04"
    );
    assert_eq!(
        schedule(&[a.clone(), b.clone()], "UTC", None).unwrap()["due"],
        "2026-11-09"
    );
    assert_eq!(
        schedule(&[a.clone(), b.clone(), c], "UTC", None).unwrap()["due"],
        "2026-11-24"
    );
    let same = attempt(4, "2026-11-02T13:00:00+00:00", "read", 0);
    let result = schedule(&[a, b, same], "UTC", None).unwrap();
    assert_eq!(result, json!({"due":"2026-11-03","days":2}));
    assert_eq!(
        local_day("2026-11-01T16:00:00+00:00", "Asia/Seoul").unwrap(),
        day("2026-11-02")
    );
}
#[test]
fn daily_selection_keeps_prior_pending_after_it_is_assessed_today() {
    let db = connection();
    let first = import(&db, &packet());
    let mut raw = packet();
    raw["lessons"][0]["key"] = json!("other-lesson");
    let second = import(&db, &raw);
    let yesterday = now("2026-11-17T12:00:00Z");
    let current = now("2026-11-18T12:00:00Z");
    let saved = submit_attempt_at(&db, second, &fields("prior-answer"), yesterday).unwrap();
    assert_eq!(
        daily_selection_at(&db, "UTC", current).unwrap()["reviews"][0]["id"],
        second
    );
    assess_attempt_at(&db, second, saved, "partial", current).unwrap();
    let selected = daily_selection_at(&db, "UTC", current).unwrap();
    assert_eq!(selected["selected_lessons"][0]["id"], second);
    assert_eq!(selected["all_done"], true);
    assert_ne!(first, second);
}
#[test]
fn scene_same_day_feedback_is_derived_without_changing_stored_hint() {
    let db = connection();
    let lesson = import(&db, &scene_packet());
    let current = now("2026-11-18T12:00:00Z");
    submit_attempt_at(
        &db,
        lesson,
        &json!({"action":"read","submission_key":"scene-read","question_id":"q1"}),
        current,
    )
    .unwrap();
    let answer = submit_attempt_at(&db, lesson, &fields("scene-answer"), current).unwrap();
    assess_attempt_at(&db, lesson, answer, "recalled", current).unwrap();
    let reader = reader_at(&db, lesson, "UTC", Some(answer), None, current).unwrap();
    assert_eq!(reader["feedback_assisted"], true);
    assert_eq!(reader["schedule"]["due"], "2026-11-19");
    assert_eq!(reader["attempt"]["hint_used"], 0);
    let default = reader_at(&db, lesson, "UTC", None, None, current).unwrap();
    assert_eq!(default["attempt"]["id"], answer);
    let mut note = fields("from-note");
    note["from_note"] = json!("1");
    let saved = submit_attempt_at(&db, lesson, &note, current).unwrap();
    assert_eq!(
        reader_at(&db, lesson, "UTC", Some(saved), None, current).unwrap()["attempt"]["hint_used"],
        1
    );
}
#[test]
fn depth_promotes_only_after_two_earlier_unassisted_dates() {
    let db = connection();
    let mut raw = scene_packet();
    let mut predict = raw["lessons"][0]["questions"][0].clone();
    predict["id"] = json!("q2");
    predict["depth"] = json!("predict");
    raw["lessons"][0]["questions"]
        .as_array_mut()
        .unwrap()
        .push(predict);
    let lesson = import(&db, &raw);
    for (token, date) in [
        ("first-day", "2026-11-15T12:00:00Z"),
        ("second-day", "2026-11-16T12:00:00Z"),
    ] {
        let saved = submit_attempt_at(&db, lesson, &fields(token), now(date)).unwrap();
        assess_attempt_at(&db, lesson, saved, "recalled", now(date)).unwrap();
    }
    let reader = reader_at(&db, lesson, "UTC", None, None, now("2026-11-18T12:00:00Z")).unwrap();
    assert_eq!(reader["question"]["id"], "q2");
    let explicit = reader_at(
        &db,
        lesson,
        "UTC",
        None,
        Some("q1"),
        now("2026-11-18T12:00:00Z"),
    )
    .unwrap();
    assert!(explicit["attempt"].is_null());
    assert_eq!(explicit["question"]["id"], "q1");
}
#[test]
fn scene_and_article_validation_preserve_provenance_and_reject_false_evidence() {
    let absent = validate_packet(&scene_packet(), day("2026-11-18"))
        .unwrap()
        .remove(0);
    let preview = presentation::present_note(&absent, "synthetic-preview").unwrap();
    assert_eq!(preview["preview_end"], 1);
    assert!(preview.get("article_intro").is_none());
    for invalid_article in [Value::Null, json!({})] {
        let mut raw = scene_packet();
        raw["lessons"][0]["article"] = invalid_article;
        assert!(validate_packet(&raw, day("2026-11-18")).is_err());
    }
    let mut raw = scene_packet();
    raw["lessons"][0]["scene"]["origin"] = json!("synthetic");
    assert!(validate_packet(&raw, day("2026-11-18")).is_err());
    raw["lessons"][0]["scene"]["execution"] = json!("suggested");
    assert!(validate_packet(&raw, day("2026-11-18")).is_ok());
    raw["lessons"][0]["questions"][0]["focus_lines"] = json!([true]);
    assert!(validate_packet(&raw, day("2026-11-18")).is_err());
    let mut raw = scene_packet();
    raw["lessons"][0]["article"] = json!({"intro":"Work **context**","code_range":[1,1],"sections":[{"id":"meaning","title":"Meaning","body":"A **safe** explanation.","source_ids":["official"]},{"id":"limits","title":"Limits","body":"Keep conditions.","source_ids":["official"]}],"takeaway":"A reusable distinction.","source_ids":["work","official"]});
    let normalized = validate_packet(&raw, day("2026-11-18")).unwrap().remove(0);
    let original = normalized.clone();
    let presented = presentation::present_note(&normalized, "synthetic-key").unwrap();
    assert_eq!(normalized, original);
    assert_eq!(presented["article_references"][0]["number"], 1);
    assert!(presented["article_intro"]
        .as_str()
        .unwrap()
        .contains("<strong>context</strong>"));
    assert_eq!(presented["preview_start"], 1);
    assert_eq!(presented["code_numbers"], "1");
    raw["lessons"][0]["article"]["code_range"] = json!([true, 1]);
    assert!(validate_packet(&raw, day("2026-11-18")).is_err());
}
#[test]
fn validation_diagnostics_never_echo_private_text() {
    let mut raw = packet();
    let sensitive = "SYNTHETIC-PRIVATE-MARKER";
    raw["lessons"][0]["sources"][1]["url"] = json!(format!("file:///{sensitive}"));
    let error = validate_packet(&raw, day("2026-11-18")).unwrap_err();
    assert!(!error.message.contains(sensitive));
    assert!(error.message.contains("source.url"));
}

#[test]
fn official_urls_preserve_urlsplit_admission_without_browser_url_repairs() {
    for rejected in [
        "https:///example.test/path",
        concat!("https://owner@", "example.test/path"),
        "https://example.test:444/path",
        "https://example.test/with space",
        "https://example.test\\path",
    ] {
        let mut raw = packet();
        raw["lessons"][0]["sources"][1]["url"] = json!(rejected);
        assert!(
            validate_packet(&raw, day("2026-11-18")).is_err(),
            "{rejected}"
        );
    }
    for accepted in [
        "HTTPS://example.test:443/path",
        "https://:@example.test/path",
        "https://[::1]:443/path",
    ] {
        let mut raw = packet();
        raw["lessons"][0]["sources"][1]["url"] = json!(accepted);
        assert!(
            validate_packet(&raw, day("2026-11-18")).is_ok(),
            "{accepted}"
        );
    }
}
