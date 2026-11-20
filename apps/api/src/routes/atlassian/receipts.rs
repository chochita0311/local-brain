use base64::Engine;
use localbrain_core::backend::Result;
use serde_json::Value;
use std::{
    collections::VecDeque,
    io::Read,
    sync::Mutex,
    time::{Duration, Instant},
};
struct Receipt {
    token: String,
    return_to: String,
    report: Value,
    expires_at: Instant,
}
#[derive(Default)]
pub struct SyncReceipts {
    entries: Mutex<VecDeque<Receipt>>,
}
impl SyncReceipts {
    pub fn store(&self, report: &Value, return_to: &str) -> Result<String> {
        self.store_at(report, return_to, Instant::now())
    }
    fn store_at(&self, report: &Value, return_to: &str, at: Instant) -> Result<String> {
        let mut entries = self
            .entries
            .lock()
            .unwrap_or_else(|error| error.into_inner());
        entries.retain(|entry| entry.expires_at > at);
        let token = loop {
            let mut bytes = [0u8; 24];
            std::fs::File::open("/dev/urandom")?.read_exact(&mut bytes)?;
            let token = base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(bytes);
            if !entries.iter().any(|entry| entry.token == token) {
                break token;
            }
        };
        entries.push_back(Receipt {
            token: token.clone(),
            return_to: return_to.into(),
            report: report.clone(),
            expires_at: at + Duration::from_secs(300),
        });
        while entries.len() > 32 {
            entries.pop_front();
        }
        Ok(token)
    }
    pub fn report(&self, token: Option<&str>, return_to: &str) -> Option<Value> {
        self.report_at(token.unwrap_or(""), return_to, Instant::now())
    }
    fn report_at(&self, token: &str, return_to: &str, at: Instant) -> Option<Value> {
        if token.len() != 32
            || !token
                .bytes()
                .all(|ch| ch.is_ascii_alphanumeric() || b"_-".contains(&ch))
        {
            return None;
        }
        let mut entries = self
            .entries
            .lock()
            .unwrap_or_else(|error| error.into_inner());
        entries.retain(|entry| entry.expires_at > at);
        entries
            .iter()
            .find(|entry| entry.token == token && entry.return_to == return_to)
            .map(|entry| entry.report.clone())
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    #[test]
    fn sync_results_are_query_bound_expiring_and_bounded_without_consuming_on_read() {
        let receipts = SyncReceipts::default();
        let at = Instant::now();
        let token = receipts
            .store_at(&json!({"scanned":7}), "/atlassian?view=jira", at)
            .unwrap();
        assert_eq!(token.len(), 32);
        assert!(receipts
            .report_at(&token, "/atlassian?view=wiki", at)
            .is_none());
        for _ in 0..2 {
            assert_eq!(
                receipts
                    .report_at(&token, "/atlassian?view=jira", at)
                    .unwrap()["scanned"],
                7
            );
        }
        assert!(receipts
            .report_at(
                &token,
                "/atlassian?view=jira",
                at + Duration::from_secs(300)
            )
            .is_none());
        let first = receipts.store_at(&json!({}), "/atlassian", at).unwrap();
        for _ in 0..32 {
            receipts.store_at(&json!({}), "/atlassian", at).unwrap();
        }
        assert!(receipts.report_at(&first, "/atlassian", at).is_none());
        assert!(receipts
            .report_at(&"x".repeat(33), "/atlassian", at)
            .is_none());
    }
}
