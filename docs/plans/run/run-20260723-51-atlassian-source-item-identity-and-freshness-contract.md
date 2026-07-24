# RUN-20260723-51: Atlassian Source Item Identity And Freshness Contract

## Metadata

- ID: `run-20260723-51`
- Status: `passed`
- Feature: [feat-0046-atlassian-source-item-identity-and-freshness-contract](../feature/feat-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Active Spec: [spec-0046-atlassian-source-item-identity-and-freshness-contract](../spec/spec-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal And Selected Loop

- Establish stable Atlassian Site/Space/Item identity, remote/local ownership, freshness, retained content, and FTS projection while preserving every existing External Resource identity and relation.
- Route: `Orchestrator → Spec Agent → Builder → Contract Evaluator → Functional Evaluator → Fix Agent if required`.

## Surface Lanes

- Identity and compatible upgrade:
  - path roots: schema, database startup/migration, External Resource creation
  - dependencies: approved FEAT-0046 and SPEC-0046
  - validation evidence: fresh/upgrade schema, strict one-to-one binding, scoped uniqueness, backup, exact row/link preservation
  - evaluator ownership: `contract`, `functional`
- Remote ownership and freshness:
  - path roots: Atlassian domain APIs and tests
  - dependencies: identity lane, passed FEAT-0044 and FEAT-0045
  - validation evidence: Site/Space/Item identity, stubs, aliases, collisions, remote/local isolation, derived state matrix
  - evaluator ownership: `contract`, `functional`
- Content normalization and FTS:
  - path roots: deterministic normalizer, hashes, search projection and rebuild
  - dependencies: identity and ownership lanes
  - validation evidence: Jira/Confluence formats, coverage gating, no-change suppression, retained rows, query/rebuild behavior
  - evaluator ownership: `contract`, `functional`
- Durable docs and generated schema:
  - path roots: owner docs, schema presentation, cleanup decision ledger
  - dependencies: stable implementation
  - validation evidence: subject maps/counts, generated parity, privacy, Mermaid, links, and diff checks
  - evaluator ownership: `contract`

## Contract Surfaces

- Stable External Resource ID and strict one-to-one Atlassian extension.
- Source Instance → Site → optional Space → Item containment.
- Site-scoped normalized URL aliases and confirmed remote identity.
- Remote metadata/content versus local Resource ownership.
- Derived freshness and retained last-known state.
- Deterministic ADF/HTML/Markdown/plain normalization and indexed-only FTS.
- Relationship-preserving compatible migration and generated schema consumers.

## Invocation Context

- Golden sources: approved FEAT-0046, SPEC-0046, PRD-0007, passed FEAT-0044/0045, current External Resource and FTS implementation.
- Relevant policies: Architecture, Privacy, Data Model, Work Organization And Resources, Derived Retrieval Index, Source Registry And Scans, execution-loop governance.
- Optional skills or tools expected: no live external connector, company content, or model call is required.

## Current Artifacts

- Spec: [spec-0046-atlassian-source-item-identity-and-freshness-contract](../spec/spec-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Contract evaluation: [PASS](../evaluation/eval-0046-contract-atlassian-source-item-identity-and-freshness-contract.md)
- Functional evaluation: [PASS](../evaluation/eval-0046-functional-atlassian-source-item-identity-and-freshness-contract.md)
- Fix log: not created

## Evaluation Coverage

- Contract:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: source inspection, fresh/compatible SQLite, file-backed backup and repair, identity/collision/retention/projection contracts, generated schema and durable owners
  - Unverified claims: live company reads and visible product Features are out of scope
  - Acceptance impact: none
- Functional:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: 21 focused Atlassian tests, temporary upgraded files, deterministic Jira/Confluence normalization, freshness clocks, FTS lifecycle, complete 225-test suite and repository checks
  - Unverified claims: no live Gateway, company content, model, or visible UI path was exercised
  - Acceptance impact: none

## Current Route

- Next role: Human owner for result acceptance, then Orchestrator for FEAT-0047 boundary review if requested.
- Current blocker classification: none.
- In-run route: Attempt 1 implementation → Contract PASS → Functional PASS.
- Post-run recommendation for human review: accept FEAT-0046; do not start FEAT-0047 or later Features without separate approval.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: complete strict one-to-one identity, Site/Space containment, URL/remote-state/content separation, compatible migration, freshness, normalization, retention, and FTS contract
  - notes: 21 focused tests and the complete 225-test suite passed without a Fix Agent route

## Post-Contract Regression Check

- Needed: yes.
- Result: passed.
- Notes: schema/document parity, retrieval and Workstream guards, generated presentation/audit, nine Mermaid diagrams, privacy, compilation, diff checks, and all 225 tests passed.

## Human Review Outcome

- Decision: Feature boundary and execution were approved on `2026-07-23`.
- Returned layer if any: none.
- Follow-up run: none.

## Continuity Notes

- `2026-07-23`: Run initialized after explicit owner approval of the remaining table/cardinality decision and request to proceed.
- `2026-07-23`: Attempt 1 passed Contract and Functional evaluation with complete synthetic foundation evidence and no live external or model call.
