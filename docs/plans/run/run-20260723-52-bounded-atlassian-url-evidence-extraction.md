# RUN-20260723-52: Bounded Atlassian URL Evidence Extraction

## Metadata

- ID: `run-20260723-52`
- Status: `passed`
- Feature: [feat-0047-bounded-atlassian-url-evidence-extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Active Spec: [spec-0047-bounded-atlassian-url-evidence-extraction](../spec/spec-0047-bounded-atlassian-url-evidence-extraction.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal And Selected Loop

- Add bounded, incremental, source-backed Atlassian URL evidence without external access, opaque payload retention, maintenance feedback, or stable Item mutation.
- Route: `Orchestrator → Spec Agent → Builder → Contract Evaluator → Functional Evaluator → Fix Agent if required`.

## Surface Lanes

- Bounded parsing:
  - path roots: parser dataclasses and Claude/Codex adapters
  - dependencies: approved FEAT-0047 and SPEC-0047
  - validation evidence: visible text and approved-result bounded fixtures
  - evaluator ownership: `contract`, `functional`
- Source-backed reconciliation:
  - path roots: evidence service and scanner hooks
  - dependencies: parsing lane and passed FEAT-0046
  - validation evidence: eligibility, fingerprints, configured mapping, replacement lifecycle, retention
  - evaluator ownership: `contract`, `functional`
- Durable ownership:
  - path roots: DDL, owner docs, generated schema and audit
  - dependencies: stable behavior
  - validation evidence: cardinality, cascade, counts, privacy, full regression
  - evaluator ownership: `contract`

## Contract Surfaces

- Parser-only candidate shape and allowlisted result traversal.
- Exactly-one Session/Document evidence ownership.
- Configured Site/service URL recognition.
- Source/extractor/configuration scan fingerprint.
- Stable Item reuse and derived evidence replacement.
- Zero external/model/organization/freshness side effects.

## Invocation Context

- Golden sources: approved FEAT-0047, SPEC-0047, PRD-0007, passed FEAT-0046, current ingestion and Context contracts.
- Relevant policies: Architecture, Privacy, Workspace And Session Activity, Local Context Corpus, Source Registry And Scans, Atlassian Source Memory.
- Optional skills or tools expected: no browser, live connector, company data, or model call.

## Current Artifacts

- Spec: [spec-0047-bounded-atlassian-url-evidence-extraction](../spec/spec-0047-bounded-atlassian-url-evidence-extraction.md)
- Contract evaluation: [PASS](../evaluation/eval-0047-contract-bounded-atlassian-url-evidence-extraction.md)
- Functional evaluation: [PASS](../evaluation/eval-0047-functional-bounded-atlassian-url-evidence-extraction.md)
- Initial Functional evaluation: [FAIL](../evaluation/eval-0047-functional-bounded-atlassian-url-evidence-extraction-attempt-1.md)
- Fix log: [Session source-file evidence cardinality](../fix/fix-0047-session-source-file-evidence-cardinality.md)

## Evaluation Coverage

- Contract:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: parser boundaries, fresh/additive SQLite, identity/cardinality, fingerprints, ownership, generated schema, privacy
  - Unverified claims: live connector/company data and visible product behavior are out of scope
  - Acceptance impact: none
- Functional:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: eight focused tests, shared-Session multi-file regression, changed/unchanged/removed Context state, complete 233-test suite
  - Unverified claims: no external or model process and no visible UI
  - Acceptance impact: none

## Current Route

- Next role: Orchestrator for FEAT-0048.
- Current blocker classification: none.
- In-run route: Attempt 1 Functional FAIL → FIX-0047 → Attempt 2 Contract PASS and Functional PASS.
- Post-run recommendation for human review: accept FEAT-0047 and continue the already approved sequential workflow with FEAT-0048.

## Attempts

- Attempt 1:
  - status: failed
  - outcome: Session-only scan cardinality caused unchanged multi-file Sessions to reparse
  - notes: classified as an implementation bug
- Attempt 2:
  - status: passed
  - outcome: source-path-aware Session scan/sighting identity plus complete bounded extraction contract
  - notes: eight focused tests and all 233 repository tests passed

## Post-Contract Regression Check

- Needed: yes.
- Result: passed.
- Notes: ingestion, shared Session source files, Usage repair, Session classification, Context scanning, schema consumers, generated artifacts, and privacy passed.

## Human Review Outcome

- Decision: Feature boundary and sequential execution approved on `2026-07-23`.
- Returned layer if any: none.
- Follow-up run: FEAT-0048 only after this Run passes.

## Continuity Notes

- `2026-07-23`: Run initialized after explicit owner approval of the recommended location marker and sequential workflow.
- `2026-07-23`: Attempt 1 failed on one multi-file Session implementation bug; FIX-0047 corrected the source-file cardinality without changing scope.
- `2026-07-23`: Attempt 2 passed every required evaluator and complete regression.
