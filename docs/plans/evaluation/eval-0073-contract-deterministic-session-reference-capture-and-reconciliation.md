# EVAL-0073: Deterministic Session Reference Capture And Reconciliation — Contract

## Metadata

- ID: `eval-0073-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260803-83`
- Attempt: `1`
- Feature: [feat-0073-deterministic-session-reference-capture-and-reconciliation](../feature/feat-0073-deterministic-session-reference-capture-and-reconciliation.md)
- Spec: [spec-0073-deterministic-session-reference-capture-and-reconciliation](../spec/spec-0073-deterministic-session-reference-capture-and-reconciliation.md)
- Execution Profile: `foundation-contract`
- Surface Lane: provider candidates → target resolution → source reconciliation → read projection
- Evidence Coverage: `complete`
- Created: `2026-08-03`

## Checks

- Claude and Codex adapters produce one shared ephemeral candidate vocabulary;
  stable Source ID continues to isolate personal Codex and Codex Company rows.
- Visible mention, approved call/result, completed success/failure, malformed,
  missing, unknown, and Maintenance/Subsession boundaries fail closed without
  retaining opaque payloads.
- Generic HTTP(S) identity removes userinfo, query, and fragment data. Markdown
  resolution is exact against eligible Documents, while configured Atlassian
  URL/key/page identity reuses the existing local Item rather than creating a
  query-variant duplicate.
- `source_files.session_id` plus `reference_contract_version` converge on fresh
  and compatible databases without rewriting retained file rows. The physical
  Session FK uses `SET NULL`, and `idx_source_files_session` is created only
  after compatible columns exist.
- File-scoped replacement and Session-scoped finalization preserve multi-file
  ownership. Partial/error Sessions reconstruct current siblings before the
  100-target selection; deterministic evidence keys include source-path identity.
- Detail projection reads normalized database rows only and exposes one target,
  bounded evidence counts, success-over-failure truth, safe destination, totals,
  and partial/error state without opening Session files.
- Data Model, Architecture, Privacy, Schema Presentation, value dictionaries,
  nine Mermaid definitions, and cleanup audit agree on 39 manifest tables, 426
  columns, 38 named indexes, 49 physical relations, and 24 application relations.

## Evidence

- Focused provider/resolver/reconciler/schema/source-sync/Usage set: 53 tests
  passed; final parser/resolver privacy-fixture check: 18 tests passed.
- Full repository suite: 343 tests passed.
- Schema presentation and value dictionaries are current; the 576-object cleanup
  audit reports 479 keep and 97 defer decisions with no active change/removal.
- Repository privacy passed for 734 candidate files; Mermaid and diff checks
  passed.

## Findings

- None.

## Route

- Next action: `pass`; Functional evaluation may close FEAT-0073.
