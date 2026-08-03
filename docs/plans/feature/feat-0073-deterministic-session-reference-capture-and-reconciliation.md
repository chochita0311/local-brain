# FEAT-0073: Deterministic Session Reference Capture And Reconciliation

## Metadata

- ID: `feat-0073`
- Status: `passed`
- Type: `foundation`
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0013: Session-Centric Related Context Evidence](../prd/prd-0013-session-centric-related-context-evidence.md)
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Goal

- Produce and reconcile the approved Session reference evidence during local AI
  Session synchronization so later detail reads remain bounded, deterministic,
  and independent of source-file or large-message reparsing.

## Acceptance Contract

- Claude and Codex provider adapters produce equivalent FEAT-0072 evidence
  semantics while every registered source instance retains independent source
  provenance.
- Eligible visible user and assistant messages contribute bounded safe HTTP(S)
  URL and explicit Markdown-reference candidates.
- Initial approved resource-read adapters recognize configured Atlassian Item
  read operations from authoritative tool calls and match their corresponding
  result by source-native tool-call identity.
- A completed non-error result produces successful read evidence. Supported
  attempts with only matching error results produce failure-only evidence. A
  missing, malformed, or unmatched result never produces false success.
- Approved tool-result observations use only allowlisted bounded identity fields;
  tool inputs and results are not copied as evidence bodies.
- Absolute Markdown paths resolve only by exact eligible path. Relative paths
  resolve exactly against Session `cwd`. Bare `*.md` names resolve only when one
  eligible Document in the Session workspace matches. Missing or ambiguous
  targets remain unresolved without fuzzy or cross-root guessing.
- Workspace participates only in resolving an explicit Markdown mention. It does
  not emit automatic same-workspace candidates.
- Generic URL identity is limited to safe HTTP(S) data. Credentials, fragments,
  and opaque query material are omitted unless a specific approved adapter owns
  a bounded identity allowlist.
- Repeated references deduplicate by target while distinct completed read calls
  and normalized evidence locations remain countable. Replay, compaction, and
  repeat scan do not inflate counts.
- Synchronization retains at most `100` unique targets per Session reference
  family and records the observed total plus partial state when the bound is
  exceeded.
- Changed source files reconcile removed, changed, and new derived evidence.
  Source deletion removes Session-owned evidence through existing reconciliation
  without deleting shared Resource or user-managed state.
- Extractor/version changes trigger deterministic repair. A failed parse or
  evidence reconciliation retains prior valid evidence as stale/partial and
  reports bounded source health.
- Maintenance Sessions and Subsessions produce no initial reference evidence for
  the primary Session consumer.
- Detail-page requests consume normalized evidence and never parse authoritative
  JSONL or normalized multi-megabyte message bodies.
- Capture and reconciliation perform no external request, MCP call, model call,
  embedding request, remote refresh, capability inspection, organization
  mutation, or source-file write.

## Scope Boundary

- In:
  - Claude and Codex visible mention extraction
  - safe URL and exact Markdown candidate normalization
  - allowlisted Atlassian read-call/result correlation
  - success and failure-only evidence
  - bounded approved tool-result identity observations
  - target deduplication and count semantics
  - per-source fingerprint/version repair
  - changed, stale, partial, missing, and deleted source reconciliation
  - bounded read projection for the product consumer
- Out:
  - Related Context markup, copy, disclosure, or styling
  - conversation anchors or scrolling
  - Subsession aggregation
  - generic interpretation of unknown MCP tools
  - full payload retention or arbitrary filesystem/repository scan
  - key-only Atlassian discovery
  - remote read, refresh, enrichment, or semantic resolution

## Surface Lanes

- Provider extraction lane:
  - path roots: `src/localbrain/ingest/common.py`, Claude/Codex adapters, and
    parser fixtures
  - dependencies: FEAT-0072 evidence contract
  - expected evidence: supported mention, read success/failure, tool-result,
    maintenance, Subsession, malformed, and unsupported shapes
  - evaluator ownership: `contract`, `functional`
- Target resolution lane:
  - path roots: Session reference normalization, Local Context lookup, safe URL
    identity, and focused tests
  - dependencies: provider extraction lane and current Resource/Document identity
  - expected evidence: exact, missing, ambiguous, unsafe, and bounded resolution
  - evaluator ownership: `contract`, `functional`
- Reconciliation lane:
  - path roots: scanner persistence, source fingerprints, stale repair, deletion,
    source health, and integration tests
  - dependencies: extraction and resolution lanes
  - expected evidence: repeat, change, removal, parser-version, partial failure,
    100-target boundary, and large-source behavior
  - evaluator ownership: `functional`
- Read-projection lane:
  - path roots: bounded Session reference queries consumed by FEAT-0074
  - dependencies: persisted reconciled evidence
  - expected evidence: stable order, totals, partial state, and zero source parse
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- Claude and Codex parsed reference candidate shape.
- Approved tool operation allowlist and call/result correlation.
- Markdown and safe URL resolution boundary.
- Evidence fingerprint/extractor version and source health.
- Persistence producer contract from FEAT-0072.
- Bounded projection shape, totals, ordering inputs, stale/partial state, and
  deletion behavior.

## Required Evaluators

- `contract`: adapter equivalence, allowlist, resolver boundary, persistence
  producer contract, privacy, and projection shape.
- `functional`: extraction, correlation, counts, bounds, repeat scan, repair,
  source failure, removal, deletion, and large-source behavior.

## State Expectations

- Unchanged: current fingerprint and evidence version skip reparsing.
- Changed: current authoritative evidence replaces the prior derived set.
- Success: supported target and outcome produce normalized evidence.
- Failure-only: supported deterministic target retains failed-read evidence.
- Unsupported/ambiguous: no target relation is produced.
- Partial/stale: prior valid evidence remains with explicit source health.
- Deleted: Session-derived evidence disappears with the owning source projection;
  shared state remains.

## Dependencies

- FEAT-0072 must be `passed` before this Feature enters build.
- Current multi-source Session settings and synchronization from PRD-0012 remain
  authoritative.

## Likely Affected Surfaces

- `src/localbrain/ingest/common.py`
- `src/localbrain/ingest/claude.py`
- `src/localbrain/ingest/codex.py`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/atlassian_evidence.py` or its approved generalized owner
- Session reference query/resolution module selected by FEAT-0072
- source health and schema/data-model consumers
- parser, scanner, source sync, evidence, privacy, and query tests
- affected product, architecture, privacy, and data-model owner docs

## Pass Or Fail Checks

- Pass if synthetic Claude, personal Codex, and Codex Company sources produce
  equivalent evidence meaning with distinct source provenance.
- Pass if successful, failed, missing-result, malformed, unknown-tool, visible
  mention, approved-result, and Markdown cases classify truthfully.
- Pass if exact absolute, relative, and unique bare-name Markdown references
  resolve and ambiguous or missing candidates do not.
- Pass if repeat text, replay, compaction, and rescan do not inflate distinct
  call/location counts.
- Pass if the 100-target bound reports total and partial state explicitly.
- Pass if changed, removed, deleted, parser-version, failed-source, and recovery
  cases preserve the FEAT-0072 lifecycle.
- Pass if large Sessions are processed during synchronization and detail reads
  issue no source-file or message-body parse.
- Pass if no external/model work, opaque payload retention, same-workspace
  candidate generation, Maintenance evidence, or Subsession roll-up occurs.

## Regression Surfaces

- Multi-source Claude/Codex synchronization and health.
- Meaningful Session eligibility and stale source deletion.
- FEAT-0047 Atlassian evidence and stable Resource reuse.
- Usage normalization and Activity Event storage.
- Local Context scanning and exact Document identity.
- Maintenance and Subsession classification.
- Repository privacy and database integrity.

## Harness Trace

- Active spec doc: [SPEC-0073](../spec/spec-0073-deterministic-session-reference-capture-and-reconciliation.md)
- Active run: [RUN-20260803-83](../run/run-20260803-83-deterministic-session-reference-capture-and-reconciliation.md)
- Execution profile: `foundation-contract`
- Latest evaluator reports: [Contract PASS](../evaluation/eval-0073-contract-deterministic-session-reference-capture-and-reconciliation.md)
  and [Functional PASS](../evaluation/eval-0073-functional-deterministic-session-reference-capture-and-reconciliation.md).
- Latest fix note: not created.

## Open Review Decisions

- None inside the proposed boundary. Adapter details and physical ownership must
  follow the passed FEAT-0072 contract rather than reopening it in Spec work.

## Continuity Notes

- `2026-08-03`: initial draft proposed after PRD-0013 approval; execution remains
  blocked on human Feature-boundary review and passed FEAT-0072 dependency.
- `2026-08-03`: owner approved the Feature boundary. Execution remains queued
  behind a passed FEAT-0072 contract.
- `2026-08-03`: FEAT-0072 passed. This Feature entered the loop under
  `foundation-contract`; implementation must preserve multi-file native Session
  identity through explicit source-file mapping and reference contract version.
- `2026-08-03`: Attempt 1 passed Contract and Functional evaluation with shared
  Claude/Codex candidates, exact/safe resolution, bounded multi-file
  reconciliation, database-only projection, 343 repository tests, and all
  generated/privacy checks green.
