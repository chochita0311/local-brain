# RUN-20260718-20: Usage And Cost Fact Contract

## Metadata

- ID: `run-20260718-20`
- Status: `complete`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Active Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Deliver and verify the source-neutral usage fact, immutable price snapshot, and canonical trend-cost contract required by every later PRD-0004 Feature.

## Selected Loop

- Feature type: `foundation`
- Surface: `data`
- Surface lanes: source normalization → persistence and pricing → durable contract
- Required evaluators: `contract`, `functional`
- Current phase: complete; post-run private validation later returned the usage normalizer contract to Spec

## Surface Lanes

- Source normalization:
  - path roots: `src/localbrain/ingest/`
  - dependencies: approved SPEC-0020
  - validation evidence: synthetic parser capability and identity fixtures
  - evaluator ownership: `contract`, `functional`
- Persistence and pricing:
  - path roots: `src/localbrain/usage.py`, `src/localbrain/schema.sql`, `src/localbrain/db.py`
  - dependencies: normalized usage values
  - validation evidence: deterministic calculation, immutable snapshots, migration, and repeat-scan fixtures
  - evaluator ownership: `contract`, `functional`
- Contract ownership:
  - path roots: `docs/policies/project/`
  - dependencies: settled implementation names
  - validation evidence: producer, storage, rebuild, and consumer parity
  - evaluator ownership: `contract`

## Contract Surfaces

- `ParsedUsageFact`, Claude and Codex usage producers, `usage_facts`, immutable model-price rows, calculation states, deterministic IDs, and rescan behavior.

## Invocation Context

- Golden sources: approved PRD and Feature, inspected local JSONL shapes, installed ccusage 20.0.14 reference behavior.
- Relevant policies: Project Architecture, Product Model, Privacy And Data Handling, foundation-contract profile.
- Optional skills or tools expected: OpenAI documentation skill was used to verify Codex-local format context without transmitting local records.

## Current Artifacts

- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Contract evaluation: [eval-0020-contract-usage-and-cost-fact-contract](../evaluation/eval-0020-contract-usage-and-cost-fact-contract.md)
- Functional evaluation: [eval-0020-functional-usage-and-cost-fact-contract](../evaluation/eval-0020-functional-usage-and-cost-fact-contract.md)
- Fix log: not created

## Evaluation Coverage

- Contract:
  - Result: `FAIL`
  - Evidence Coverage: `partial`
  - Environments or states checked: source inspection, synthetic adapters, fresh and upgraded SQLite, policy parity
  - Unverified claims: none
  - Acceptance impact: not applicable
- Functional:
  - Result: `FAIL`
  - Evidence Coverage: `partial`
  - Environments or states checked: parser, persistence, pricing, repeat scan, price change, unknown, malformed, and regression suite
  - Unverified claims: none
  - Acceptance impact: not applicable

## Current Route

- Next role: Spec Agent for corrected SPEC-0020
- Current blocker classification: `spec gap`
- In-run route: post-run return to Spec
- Post-run recommendation for human review: superseded by RUN-20260718-25 Attempt 2

## Attempts

- Attempt 1:
  - status: invalidated after completion
  - outcome: synthetic checks passed, but private live validation exposed an incorrect latest-per-turn Codex assumption and incomplete repair semantics
  - notes: RUN-20260718-25 owns the corrected cumulative-delta and source-level repair contract

## Post-Contract Regression Check

- Needed: yes
- Result: failed after private post-run validation
- Notes: unrelated regressions remained green, but the owning usage contract was incomplete.

## Human Review Outcome

- Decision: returned to Spec after human review
- Returned layer if any: SPEC-0020
- Follow-up run: RUN-20260718-25

## Continuity Notes

- `2026-07-18`: Orchestrator confirmed the foundation-contract profile, three-lane order, and Contract plus Functional evaluator set.
- `2026-07-18`: Builder, Contract Evaluator, and Functional Evaluator completed Attempt 1 with no fix loop required.
- `2026-07-18`: later private live validation invalidated Attempt 1; its evaluator reports now route to the corrected Attempt 2 rather than remaining acceptance evidence.
