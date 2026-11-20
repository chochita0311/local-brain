use localbrain_core::backend::{
    google_drive::{
        self as drive,
        api::{Remote, Request, Response, Transport, API, BATCH},
    },
    BackendError, Result,
};
use md5::{Digest, Md5};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, VecDeque},
    fs,
    io::Cursor,
    sync::{Arc, Mutex},
};
struct Reply {
    status: u16,
    headers: BTreeMap<String, String>,
    body: Vec<u8>,
}
struct Queue {
    replies: Mutex<VecDeque<std::result::Result<Reply, BackendError>>>,
    calls: Mutex<Vec<Request>>,
}
impl Transport for Queue {
    fn open(&self, request: Request) -> Result<Response> {
        self.calls.lock().unwrap().push(request);
        let value = self
            .replies
            .lock()
            .unwrap()
            .pop_front()
            .expect("unexpected request")?;
        Ok(Response {
            code: value.status,
            headers: value.headers,
            body: Box::new(Cursor::new(value.body)),
        })
    }
}
fn reply(value: Value) -> std::result::Result<Reply, BackendError> {
    Ok(Reply {
        status: 200,
        headers: BTreeMap::new(),
        body: serde_json::to_vec(&value).unwrap(),
    })
}
fn raw(
    status: u16,
    headers: &[(&str, &str)],
    body: &[u8],
) -> std::result::Result<Reply, BackendError> {
    Ok(Reply {
        status,
        headers: headers
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_string()))
            .collect(),
        body: body.into(),
    })
}
fn make_api(replies: Vec<std::result::Result<Reply, BackendError>>) -> (API, Arc<Queue>) {
    let queue = Arc::new(Queue {
        replies: Mutex::new(replies.into()),
        calls: Mutex::new(vec![]),
    });
    let mut api = API::new(
        Arc::new(|| Ok("synthetic-token".into())),
        BTreeMap::from([("root".into(), "root-key".into())]),
        Arc::new(|| false),
        None,
        Some(queue.clone()),
    )
    .unwrap();
    api.sleeper = Arc::new(|_| {});
    (api, queue)
}
fn metadata(content: &[u8]) -> Value {
    json!({"id":"assigned-id","name":"demo","parents":["parent"],"size":content.len().to_string(),"md5Checksum":format!("{:x}",Md5::digest(content)),"version":"1"})
}
#[test]
fn endpoint_pagination_resource_keys_and_safe_error_classes() {
    let (api, queue) = make_api(vec![
        reply(json!({"files":[{"id":"child","resourceKey":"new-key"}],"nextPageToken":"next"})),
        reply(json!({"files":[]})),
    ]);
    assert_eq!(api.children("root").unwrap().len(), 1);
    let calls = queue.calls.lock().unwrap();
    assert!(calls[0].url.contains("supportsAllDrives=true"));
    assert!(calls[1].url.contains("pageToken=next"));
    assert_eq!(
        calls[0].headers["X-Goog-Drive-Resource-Keys"],
        "root/root-key"
    );
    drop(calls);
    for (method, url) in [
        ("PUT", BATCH),
        ("POST", "https://evil.test/upload"),
        ("GET", "https://www.googleapis.com.evil/drive/v3/files"),
    ] {
        assert_eq!(
            api.request(
                method,
                url,
                &BTreeMap::new(),
                None,
                None,
                &BTreeMap::new(),
                "read",
                &[],
                &[]
            )
            .err()
            .unwrap()
            .code,
            "endpoint"
        )
    }
    assert_eq!(queue.calls.lock().unwrap().len(), 2);
    for (status, reason, code, retry) in [
        (404, "", "unavailable", false),
        (403, "", "google_request", false),
        (403, "insufficientFilePermissions", "permission", false),
        (403, "rateLimitExceeded", "rate_limit", true),
        (401, "", "reauth", false),
        (503, "", "google_service", true),
    ] {
        let error = drive::api::api_error(
            status,
            &json!({"error":{"errors":[{"reason":reason}]}}),
            "create",
        );
        assert_eq!(error.code, code);
        assert_eq!(drive::retryable(&error), retry);
    }
    let (api, _) = make_api(vec![reply(json!({"files":[],"incompleteSearch":true}))]);
    assert_eq!(api.children("root").unwrap_err().code, "partial_listing");
}
#[test]
fn small_media_and_uncertain_create_reconcile_exact_assigned_id() {
    let content = b"\0\xffliteral\r\nbytes";
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("snapshot");
    fs::write(&path, content).unwrap();
    let digest = format!("{:x}", Md5::digest(content));
    for first in [
        reply(metadata(content)),
        Err(drive::error("network", "Disconnected", true)),
        raw(200, &[], b"{malformed"),
    ] {
        let uncertain =
            first.as_ref().is_err() || first.as_ref().is_ok_and(|r| r.body == b"{malformed");
        let mut replies = vec![first];
        if uncertain {
            replies.push(reply(metadata(content)));
        }
        let (api, queue) = make_api(replies);
        api.set_key("parent", "parent-key");
        let mut state = json!({});
        let mut checkpoints = vec![];
        let progress = Mutex::new(vec![]);
        let result = api
            .upload(
                "assigned-id",
                "demo",
                "parent",
                &path,
                &digest,
                false,
                &mut state,
                &mut |v| {
                    checkpoints.push(v.clone());
                    Ok(())
                },
                &|s, n| progress.lock().unwrap().push((s, n)),
            )
            .unwrap();
        assert_eq!(result["id"], "assigned-id");
        assert_eq!(checkpoints, vec![json!({})]);
        assert_eq!(
            *progress.lock().unwrap(),
            vec![(content.len() as u64, content.len() as u64)]
        );
        let calls = queue.calls.lock().unwrap();
        assert_eq!(calls.len(), if uncertain { 2 } else { 1 });
        assert_eq!(calls[0].method, "POST");
        assert!(calls[0].url.contains("uploadType=multipart"));
        assert!(calls[0].body.windows(content.len()).any(|w| w == content));
        assert!(calls[0].headers["X-Goog-Drive-Resource-Keys"].contains("parent/parent-key"));
        if uncertain {
            assert_eq!(calls[1].method, "GET");
            assert!(calls[1].url.contains("/assigned-id?"));
        }
    }
}
#[test]
fn resumable_lost_chunk_probes_before_resend_and_retains_or_clears_correct_state() {
    let content = b"abc";
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("snapshot");
    fs::write(&path, content).unwrap();
    let digest = format!("{:x}", Md5::digest(content));
    let session = "https://www.googleapis.com/upload/drive/v3/files?upload_id=synthetic";
    let (mut api, queue) = make_api(vec![
        raw(200, &[("Location", session)], b""),
        Err(drive::error("network", "lost", true)),
        raw(308, &[("Range", "bytes=0-1")], b""),
        reply(metadata(content)),
    ]);
    api.multipart_bytes = 0;
    let mut state = json!({});
    let mut checkpoints = vec![];
    api.upload(
        "assigned-id",
        "demo",
        "parent",
        &path,
        &digest,
        false,
        &mut state,
        &mut |v| {
            checkpoints.push(v.clone());
            Ok(())
        },
        &|_, _| {},
    )
    .unwrap();
    assert_eq!(checkpoints[0]["session"], session);
    assert!(state.get("session").is_none());
    let calls = queue.calls.lock().unwrap();
    assert_eq!(
        calls.iter().map(|r| r.method.as_str()).collect::<Vec<_>>(),
        vec!["POST", "PUT", "PUT", "PUT"]
    );
    assert_eq!(calls[2].headers["Content-Range"], "bytes */3");
    assert_eq!(calls[3].headers["Content-Range"], "bytes 2-2/3");
    assert_eq!(calls[3].body, b"c");
    drop(calls);
    let (api, queue) = make_api(vec![raw(410, &[], b"")]);
    let mut state = json!({"session":session,"upload_hash":digest});
    assert_eq!(
        api.upload(
            "assigned-id",
            "demo",
            "parent",
            &path,
            &digest,
            false,
            &mut state,
            &mut |_| Ok(()),
            &|_, _| {}
        )
        .unwrap_err()
        .code,
        "upload_expired"
    );
    assert!(state.get("session").is_none());
    assert_eq!(queue.calls.lock().unwrap().len(), 1);
}
fn batch(rows: &[(String, u16, Value)]) -> std::result::Result<Reply, BackendError> {
    let mut body = String::new();
    for (id, status, value) in rows {
        body.push_str(&format!("--reply\r\nContent-Type: application/http\r\nContent-ID: <{id}>\r\n\r\nHTTP/1.1 {status} Result\r\nContent-Type: application/json\r\n\r\n{value}\r\n"));
    }
    body.push_str("--reply--\r\n");
    raw(
        200,
        &[("Content-Type", "multipart/mixed; boundary=reply")],
        body.as_bytes(),
    )
}
#[test]
fn hundred_metadata_reads_are_bounded_correlated_one_use_and_partial_batches_fall_back() {
    let rows = (0..100)
        .rev()
        .map(|i| {
            (
                format!("response-localbrain-{i}"),
                200,
                json!({"id":format!("file-{i}"),"version":"1"}),
            )
        })
        .collect::<Vec<_>>();
    let (api, queue) = make_api(vec![
        batch(&rows),
        reply(json!({"id":"file-0","version":"2"})),
    ]);
    let ids = (0..100).map(|i| format!("file-{i}")).collect::<Vec<_>>();
    api.prefetch(&ids, &|_, _| {}).unwrap();
    for id in &ids {
        assert_eq!(api.get(id).unwrap()["id"], *id)
    }
    assert_eq!(queue.calls.lock().unwrap().len(), 1);
    assert_eq!(queue.calls.lock().unwrap()[0].url, BATCH);
    assert_eq!(api.get("file-0").unwrap()["version"], "2");
    let call = &queue.calls.lock().unwrap()[0];
    assert_eq!(
        String::from_utf8_lossy(&call.body)
            .matches("GET /drive/v3/files/")
            .count(),
        100
    );
    let (api, queue) = make_api(vec![
        batch(&[("unknown".into(), 200, json!({"id":"one"}))]),
        reply(json!({"id":"one","version":"fresh"})),
    ]);
    api.prefetch(&["one".into()], &|_, _| {}).unwrap();
    assert_eq!(api.get("one").unwrap()["version"], "fresh");
    assert_eq!(queue.calls.lock().unwrap().len(), 2);
    let (api, _) = make_api(vec![batch(&[
        ("response-localbrain-0".into(), 404, json!({"error":{}})),
        (
            "response-localbrain-1".into(),
            403,
            json!({"error":{"errors":[{"reason":"insufficientFilePermissions"}]}}),
        ),
    ])]);
    api.prefetch(&["missing".into(), "denied".into()], &|_, _| {})
        .unwrap();
    assert_eq!(api.get("missing").unwrap_err().code, "unavailable");
    assert_eq!(api.get("denied").unwrap_err().code, "permission");
}
#[test]
fn download_verifies_size_hash_and_source_version_before_completion() {
    let content = b"abc";
    let original = metadata(content);
    let mut after = original.clone();
    after["version"] = json!("2");
    let (api, _) = make_api(vec![raw(200, &[], content), reply(after)]);
    let temp = tempfile::tempdir().unwrap();
    assert_eq!(
        api.download(&original, &temp.path().join("stage"))
            .unwrap_err()
            .code,
        "source_changed"
    );
    let (api, queue) = make_api(vec![]);
    let mut too_large = original;
    too_large["size"] = json!(policy_limit() + 1);
    assert_eq!(
        api.download(&too_large, &temp.path().join("stage"))
            .unwrap_err()
            .code,
        "too_large"
    );
    assert!(queue.calls.lock().unwrap().is_empty());
}
fn policy_limit() -> u64 {
    drive::policy::MAX_FILE_BYTES
}
