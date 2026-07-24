# RUN-20260723-54: Explicit Atlassian Refresh And Preview

## Metadata

- ID: `run-20260723-54`
- Status: `passed`
- Feature: [feat-0049-explicit-atlassian-refresh-and-preview](../feature/feat-0049-explicit-atlassian-refresh-and-preview.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Active Spec: [spec-0049-explicit-atlassian-refresh-and-preview](../spec/spec-0049-explicit-atlassian-refresh-and-preview.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal And Selected Loop

- Deliver exact local refresh previews, one bounded mixed-instance maintenance handoff, validated Atlassian result application, and reviewable recovery without hidden external or model activity.
- Route: `Orchestrator → Spec Agent → scope/manifest Builder → application/UI Builder → Contract Evaluator → Design Evaluator → Functional Evaluator → UX Heuristic Evaluator → Fix Agent if required`.

## Surface Lanes

- Scope and preview:
  - path roots: `atlassian_refresh.py`, Workstream/Thread links, preview routes/tests
  - validation evidence: exact membership, deduplication, selection defaults, request counts, zero remote preview activity
  - evaluator ownership: `contract`, `functional`
- Run and application:
  - path roots: `external_sync.py`, `runner.py`, `atlassian.py`, refresh result coordinator
  - validation evidence: old/new manifest compatibility, mixed-instance authorization, 20-call boundary, idempotent atomic application, last-known retention
  - evaluator ownership: `contract`, `functional`
- Interaction:
  - path roots: Atlassian/Workstream contextual links, refresh preview, Run result/retry, route-scoped client, shared CSS
  - validation evidence: consequence clarity, selection, progress/partial/retry, focus/history, `1440`/`920`/`700`/`320`
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable docs:
  - path roots: Product, Architecture, Privacy, Maintenance Runner, Atlassian and Maintenance data-model owners
  - validation evidence: owner parity, Mermaid, generated schema, privacy, complete regression
  - evaluator ownership: `contract`

## Contract Surfaces

- Refresh scope/read model, calculated request plans, additive per-target Source Instance manifest, external-sync projection, stable result mapping, preview/start/retry routes, contextual links, and common Run progress.

## Invocation Context

- Golden sources: approved PRD-0007, FEAT-0049, SPEC-0049, passed FEAT-0044 through FEAT-0048, current provider policy, current Workstream link and Run contracts.
- Relevant policies: Design Constitution, Design Evaluation, Interaction Evaluation, Architecture, Privacy, Atlassian Source Memory, Maintenance Execution, Maintenance Task Runner.
- Skills/tools: continue `screen-alignment` in `extend` mode; local browser rendering with synthetic data only; no company content retrieval.

## Current Artifacts

- Spec: [spec-0049-explicit-atlassian-refresh-and-preview](../spec/spec-0049-explicit-atlassian-refresh-and-preview.md)
- Contract evaluation: [eval-0049-contract-explicit-atlassian-refresh-and-preview](../evaluation/eval-0049-contract-explicit-atlassian-refresh-and-preview.md) — `PASS`
- Design evaluation: [eval-0049-design-explicit-atlassian-refresh-and-preview](../evaluation/eval-0049-design-explicit-atlassian-refresh-and-preview.md) — `PASS`
- Functional evaluation: [eval-0049-functional-explicit-atlassian-refresh-and-preview](../evaluation/eval-0049-functional-explicit-atlassian-refresh-and-preview.md) — `PASS`
- UX heuristic evaluation: [eval-0049-ux-explicit-atlassian-refresh-and-preview](../evaluation/eval-0049-ux-explicit-atlassian-refresh-and-preview.md) — `PASS`
- Fix log: not created

## Evaluation Coverage

- Contract: `PASS`; scope, mixed-source authorization, atomic application, and owner-doc parity are complete.
- Design: `PASS`; hierarchy, semantic states, long content, and responsive containment are complete.
- Functional: `PASS`; 250 tests plus privacy, schema, Mermaid, JavaScript, audit, and diff checks pass.
- UX heuristic: `PASS`; explicit scope, read consequence, selection override, unavailable recovery, and contextual continuity are clear.

## Current Route

- Next role: Orchestrator, release FEAT-0050 after dependency verification.
- Current blocker classification: none.
- In-run route: attempt 1 accepted.
- Post-run recommendation for human review: accept; no fix loop required.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: all required evaluators returned `PASS`
  - notes: Delivered the Thread preview, 20-request product batch, mixed-instance one-Run extension, Jira known-selected scope, one-page Confluence catalog boundary, atomic result application, and responsive interaction.

## Post-Contract Regression Check

- Needed: yes.
- Result: passed.
- Notes: FEAT-0045 single-source Runs, FEAT-0046 application, FEAT-0048 registration/partial discovery, Workstream links, Run console/cancellation, Usage, generated schema, and shared shell remain current in the 250-test suite.

## Human Review Outcome

- Decision: sequential execution and recommended open decisions approved on `2026-07-23`.
- Returned layer if any: none.
- Follow-up run: FEAT-0050 only after this Run passes.

## Continuity Notes

- `2026-07-23`: Run initialized immediately after FEAT-0048 passed; the foundation mismatch between one-source FEAT-0045 envelopes and multi-source all-known scope is resolved additively rather than weakening the Feature or creating hidden fan-out Runs.
