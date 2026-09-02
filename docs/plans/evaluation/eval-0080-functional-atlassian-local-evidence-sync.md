# EVAL-0080 Functional: Atlassian Local Evidence Sync

## Metadata

- ID: `eval-0080-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260829-90`
- Attempt: `1`
- Feature: [FEAT-0080](../feature/feat-0080-atlassian-local-evidence-sync.md)
- Spec: [SPEC-0080](../spec/spec-0080-atlassian-local-evidence-sync.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `persisted-source reconciliation; Sync route; Explorer refresh`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- Eligible primary work Sessions consume only the retained reference-scan URL
  projection. Resource reads, key-only rows, missing or stale projections, and
  ineligible Sessions produce the approved bounded outcomes without opening
  raw JSONL, source files, or Activity Event bodies.
- Enabled, readable, ready Documents scan persisted bodies in 64-KiB chunks.
  Tests cover a URL split across chunks, stable line and occurrence identity,
  the deterministic first-500 evidence set, exact overflow counting, complete
  cleanup, failed-pass retention, and unchanged repeat with zero data writes.
- Recognition tests cover Jira and Confluence identity bounds, unsupported
  routes, unsafe and percent-expanded normalized URLs, configured and ambiguous
  Sites, invalid locations, and zero/one/multiple compatible bindings for both
  Session and Document inputs.
- The action freezes configured scope plus the complete start-time Session and
  Document ID sets. It fetches and processes IDs in batches of 100; a later
  deletion remains an unavailable source outcome and an after-start insertion
  is excluded from that action.
- Reconciliation preserves exact Item identity and all local, remote,
  classification, organization, and Refresh owners. Changed Document evidence
  and Item-URL observations update only their owned latest spelling/time fields;
  current Document repeats and Session merge-only reuse remain read-only.
- Source savepoints isolate failure and commit successful peers. Dedicated
  tests cover partial, unavailable, all-failed, fatal action, idempotent repeat,
  nonblocking single-flight busy, and a committed peer surviving later failure.
- Enhanced POST returns the exact wrapped report with `200`, busy with `409`,
  and validation with `422`. Ordinary POST uses `303` plus a bound five-minute
  receipt; tampering, expiry, eviction, restart, unsafe return state, repeated
  fields, unknown fields, and the 8-KiB form ceiling are bounded before work.
- Browser execution verified changed, zero, partial, fatal, busy, fragment-GET
  failure, and no-script states. Successful named refresh preserved the
  selected Item, URL/history, page/list/detail/hierarchy scroll, and focus; busy
  performed no Explorer GET, and refresh failure retained the report with an
  explicit local reload path.
- The focused evidence/Sync/route suite passed `31/31`, the broader Atlassian
  and UI regression set passed `146/146`, and the full repository suite passed
  `428/428`. JavaScript syntax, privacy, schema/data-model checks, and
  `git diff --check` also passed; the only runtime warning is the pre-existing
  Starlette `TemplateResponse` deprecation notice.

## Findings

- None.

## Route

- Next action: `pass`
