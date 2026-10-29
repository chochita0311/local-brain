# SPEC-0015 R2: Codex Empty Page Control

## Metadata

- ID: `spec-0015-r2`
- Status: `approved`
- Run ID: `run-20261029-227`
- Attempt: `1`
- Parent Feature: [FEAT-0015](../feature/feat-0015-session-subsession-source-contract.md)
- Parent PRD: [PRD-0002](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: data normalization → existing Session presentation verification → docs
- Required Evaluators: contract, functional, design, interaction
- Created: `2026-10-29`

## Authority And Boundary

The owner requested correction of the confirmed leading empty-page control in
Session conversations. This bounded parser correction supplements the source
contract and the authored/generated-input normalization approved in
[RUN-161](../run/run-20261016-161-session-parsing-and-search-closeout.md).
The current [Session normalization owner](../../policies/project/data-model/workspace-and-session-activity.md#conversation-normalization-and-empty-sources)
remains canonical. This is not a revision of FEAT-0018's presentation-only tool-row
filter, and does not authorize hiding arbitrary message text in templates.

## Acceptance Contract

- Recognize a complete standalone `external_codex_apps_open_page` envelope whose
  JSON payload is exactly one `page_id` field with the value `null`.
- Reject duplicate keys, malformed JSON, missing or extra fields, arrays and
  non-null page IDs as unrecognized forms; retain their literal text.
- Apply the existing per-block generated-context filter to both Codex
  `event_msg` user messages and `response_item` user-message content blocks,
  including legacy/response counterparts and repeated controls.
- Exclude recognized controls from normalized messages, title selection,
  question/event counts, search text and message-derived reference evidence.
  Keep adjacent authored blocks and all actual questions and replies in order.
- Preserve quoted, fenced, embedded and assistant-authored examples. Preserve
  the native JSONL, source identity, Usage Records and user-owned pins/links.
- Advance only the Codex Session parser contract so the next ordinary Sync
  repairs unchanged personal and company Codex files. Keep Usage normalization
  and its stored snapshots unchanged, with no duplicate import on another Sync.
- Reuse existing meaningful/parsed-empty reconciliation for a source containing
  only the recognized control; add no new deletion or retention policy.
- Preserve current Sessions inventory/detail layout, navigation and role frames.
- Parser selection continues to use `provider_kind`; source IDs keep profiles
  distinct and labels or root-folder names do not select an adapter. Verify
  arbitrary named/renamed Codex profiles through current source configuration.

## Evaluation

- Contract: narrow recognition and refusal predicates, counterpart behavior,
  native-source preservation, stable identities and independent Usage freshness.
- Functional: leading/repeated/mixed controls; literal and malformed boundaries;
  unchanged-file upgrade on both Codex profiles; search/count/detail consistency.
- Design and interaction: inspect the existing inventory and detail in a local
  browser with synthetic data, including literal examples and inventory return.
- Use synthetic tracked fixtures only; original private evidence stays outside
  Git. The initial attempt keeps real source inspection read-only. The owner's
  follow-up authorizes normal Session Sync in the existing local web runtime
  and its required restart if stale; the same source/Usage/identity safeguards
  apply. Native app build remains outside this Run. Commit and publication were
  excluded from the initial attempts; the owner's later closeout request
  authorizes them after review and required checks in RUN-227 attempt 4.

## Open Blockers

- None. Non-null page states and unrelated CRLF recognition remain outside this
  observed empty-page correction.
