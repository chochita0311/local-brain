use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
pub const CANDIDATE_SKIP_KEYS: &[&str] = &[
    "key_only",
    "unsafe_url",
    "unsupported_locator",
    "unconfigured_domain",
    "ambiguous_site",
    "invalid_location",
];
pub const SOURCE_REASON_CODES: &[&str] = &[
    "ineligible-session",
    "disabled-document",
    "session-projection-missing",
    "session-projection-stale",
    "session-projection-error",
    "session-projection-partial",
    "context-unavailable",
    "document-url-limit",
    "unsafe-url",
    "unsupported-locator",
    "unconfigured-domain",
    "ambiguous-site",
    "invalid-location",
    "reconciliation-error",
    "identity-collision",
];
const COUNT_KEYS: &[&str] = &[
    "urls",
    "new_items",
    "reused_items",
    "new_evidence",
    "reused_evidence",
    "removed_evidence",
    "new_structure_references",
    "reused_structure_references",
    "new_structure_evidence",
    "reused_structure_evidence",
    "removed_structure_evidence",
    "site_only",
    "skipped",
];
pub(super) const SCOPE_KEYS: &[&str] = &[
    "session_projection_sources",
    "session_reference_overflow",
    "document_url_overflow",
];
fn zero(keys: &[&str]) -> Value {
    let mut result = json!({});
    for key in keys {
        result[*key] = json!(0);
    }
    result
}
pub(super) fn inc(value: &mut Value, key: &str, by: i64) {
    value[key] = json!(value[key].as_i64().expect("fixed report count") + by);
}
pub(super) struct SourceResult {
    pub kind: &'static str,
    pub local_id: i64,
    pub outcome: &'static str,
    pub reason_codes: Vec<String>,
    pub counts: Value,
    pub candidate_skips: Value,
    pub scope_limits: Value,
    pub admitted_urls: BTreeSet<String>,
    pub new_item_ids: BTreeSet<i64>,
    pub reused_item_ids: BTreeSet<i64>,
    pub new_structure_reference_ids: BTreeSet<i64>,
    pub reused_structure_reference_ids: BTreeSet<i64>,
    pub new_structure_evidence_keys: BTreeSet<String>,
    pub reused_structure_evidence_keys: BTreeSet<String>,
    pub removed_structure_evidence_keys: BTreeSet<String>,
    pub affected_structure_reference_ids: BTreeSet<i64>,
    pub seen_evidence: BTreeSet<String>,
    pub seen_session_locations: BTreeSet<String>,
    pub site_scope_updates: BTreeMap<(String, String), i64>,
    pub domain_site_updates: BTreeMap<String, i64>,
}
impl SourceResult {
    pub fn new(kind: &'static str, local_id: i64, outcome: &'static str) -> Self {
        Self {
            kind,
            local_id,
            outcome,
            reason_codes: vec![],
            counts: zero(COUNT_KEYS),
            candidate_skips: zero(CANDIDATE_SKIP_KEYS),
            scope_limits: zero(SCOPE_KEYS),
            admitted_urls: BTreeSet::new(),
            new_item_ids: BTreeSet::new(),
            reused_item_ids: BTreeSet::new(),
            new_structure_reference_ids: BTreeSet::new(),
            reused_structure_reference_ids: BTreeSet::new(),
            new_structure_evidence_keys: BTreeSet::new(),
            reused_structure_evidence_keys: BTreeSet::new(),
            removed_structure_evidence_keys: BTreeSet::new(),
            affected_structure_reference_ids: BTreeSet::new(),
            seen_evidence: BTreeSet::new(),
            seen_session_locations: BTreeSet::new(),
            site_scope_updates: BTreeMap::new(),
            domain_site_updates: BTreeMap::new(),
        }
    }
    pub fn reason(&mut self, code: &str) {
        assert!(SOURCE_REASON_CODES.contains(&code));
        if !self.reason_codes.iter().any(|s| s == code) {
            self.reason_codes.push(code.into());
        }
    }
    pub fn skip(&mut self, key: &str) {
        inc(&mut self.candidate_skips, key, 1);
        if key != "key_only" {
            self.reason(&key.replace('_', "-"));
        }
    }
    pub fn finish(&mut self) {
        self.counts["urls"] = json!(self.admitted_urls.len());
        self.counts["new_items"] = json!(self.new_item_ids.len());
        self.counts["reused_items"] =
            json!(self.reused_item_ids.difference(&self.new_item_ids).count());
        self.counts["new_structure_references"] = json!(self.new_structure_reference_ids.len());
        self.counts["reused_structure_references"] = json!(self
            .reused_structure_reference_ids
            .difference(&self.new_structure_reference_ids)
            .count());
        self.counts["new_structure_evidence"] = json!(self.new_structure_evidence_keys.len());
        self.counts["reused_structure_evidence"] = json!(self
            .reused_structure_evidence_keys
            .difference(&self.new_structure_evidence_keys)
            .count());
        self.counts["removed_structure_evidence"] =
            json!(self.removed_structure_evidence_keys.len());
        self.counts["skipped"] = json!(CANDIDATE_SKIP_KEYS
            .iter()
            .map(|k| self.candidate_skips[*k].as_i64().unwrap())
            .sum::<i64>());
    }
    pub fn public(&mut self) -> Value {
        self.finish();
        json!({"kind":self.kind,"local_id":self.local_id,"outcome":self.outcome,"counts":self.counts,"reason_codes":self.reason_codes})
    }
    pub fn unavailable(
        kind: &'static str,
        local_id: i64,
        outcome: &'static str,
        reason: &str,
    ) -> Self {
        let mut result = Self::new(kind, local_id, outcome);
        result.reason(reason);
        result
    }
}
pub(super) fn empty_report(status: &str) -> Value {
    json!({"status":status,"sources":{"considered":0,"eligible":0,"scanned":0,"partial":0,"unavailable":0,"failed":0,"excluded":0},"items":{"new":0,"reused":0},"evidence":{"new":0,"reused":0,"removed":0},"structure_references":{"new":0,"reused":0},"structure_evidence":{"new":0,"reused":0,"removed":0},"site_only":0,"candidate_skips":zero(CANDIDATE_SKIP_KEYS),"scope_limits":zero(SCOPE_KEYS),"source_outcomes":[]})
}
pub(super) struct ActionReport {
    pub report: Value,
    new_items: BTreeSet<i64>,
    reused_items: BTreeSet<i64>,
    new_refs: BTreeSet<i64>,
    reused_refs: BTreeSet<i64>,
    new_evidence: BTreeSet<String>,
    reused_evidence: BTreeSet<String>,
    removed_evidence: BTreeSet<String>,
}
impl ActionReport {
    pub fn new() -> Self {
        Self {
            report: empty_report("complete"),
            new_items: BTreeSet::new(),
            reused_items: BTreeSet::new(),
            new_refs: BTreeSet::new(),
            reused_refs: BTreeSet::new(),
            new_evidence: BTreeSet::new(),
            reused_evidence: BTreeSet::new(),
            removed_evidence: BTreeSet::new(),
        }
    }
    pub fn add(&mut self, mut result: SourceResult) {
        result.finish();
        let sources = &mut self.report["sources"];
        inc(sources, "considered", 1);
        inc(
            sources,
            if result.outcome == "excluded" {
                "excluded"
            } else {
                "eligible"
            },
            1,
        );
        if ["complete", "partial"].contains(&result.outcome) {
            inc(sources, "scanned", 1);
        }
        if ["partial", "unavailable", "failed"].contains(&result.outcome) {
            inc(sources, result.outcome, 1);
        }
        self.new_items.extend(result.new_item_ids.iter());
        self.reused_items.extend(result.reused_item_ids.iter());
        self.new_refs
            .extend(result.new_structure_reference_ids.iter());
        self.reused_refs
            .extend(result.reused_structure_reference_ids.iter());
        self.new_evidence
            .extend(result.new_structure_evidence_keys.iter().cloned());
        self.reused_evidence
            .extend(result.reused_structure_evidence_keys.iter().cloned());
        self.removed_evidence
            .extend(result.removed_structure_evidence_keys.iter().cloned());
        for (group, keys, counts) in [
            (
                "candidate_skips",
                CANDIDATE_SKIP_KEYS,
                &result.candidate_skips,
            ),
            ("scope_limits", SCOPE_KEYS, &result.scope_limits),
        ] {
            for key in keys {
                inc(&mut self.report[group], key, counts[*key].as_i64().unwrap());
            }
        }
        for key in ["new", "reused", "removed"] {
            inc(
                &mut self.report["evidence"],
                key,
                result.counts[format!("{key}_evidence")].as_i64().unwrap(),
            );
        }
        inc(
            &mut self.report,
            "site_only",
            result.counts["site_only"].as_i64().unwrap(),
        );
        self.report["source_outcomes"]
            .as_array_mut()
            .unwrap()
            .push(result.public());
    }
    pub fn finish(mut self) -> Value {
        self.report["items"]["new"] = json!(self.new_items.len());
        self.report["items"]["reused"] =
            json!(self.reused_items.difference(&self.new_items).count());
        self.report["structure_references"]["new"] = json!(self.new_refs.len());
        self.report["structure_references"]["reused"] =
            json!(self.reused_refs.difference(&self.new_refs).count());
        self.report["structure_evidence"]["new"] = json!(self.new_evidence.len());
        self.report["structure_evidence"]["reused"] =
            json!(self.reused_evidence.difference(&self.new_evidence).count());
        self.report["structure_evidence"]["removed"] = json!(self.removed_evidence.len());
        let sources = &self.report["sources"];
        self.report["status"] = json!(if sources["failed"].as_i64().unwrap() > 0
            && sources["scanned"] == 0
        {
            "failed"
        } else if ["partial", "unavailable", "failed"]
            .iter()
            .any(|k| sources[*k].as_i64().unwrap() > 0)
        {
            "partial"
        } else {
            "complete"
        });
        self.report
    }
}
