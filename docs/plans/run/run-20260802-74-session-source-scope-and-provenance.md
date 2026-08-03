# RUN-20260802-74: Session Source Scope And Provenance

## Metadata

- ID: `run-20260802-74`
- Status: `passed`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Active Spec: [spec-0069-session-source-scope-and-provenance](../spec/spec-0069-session-source-scope-and-provenance.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Goal

- Browse all retained primary work Sessions or one stable local AI Source while
  preserving readable provenance and navigation orientation.

## Selected Loop

- Feature type: `product`
- Profile: `fullstack-product`
- Lanes: query/route → inventory presentation → detail presentation → docs
- Affected screens: `/sessions`, `/sessions/{id}`, normalized and lazy Subsession
  detail, and pinned projection within Sessions
- Components: source controls, metrics, rows, Subsession disclosures, pin list,
  detail header/backlinks
- Required evaluators: Contract, Design, Functional, UX Heuristic
- Current phase: complete

## Contract Surfaces

- stable-key source option and GET normalization
- eligible-primary-work denominator and exact source filtering
- provenance read models and scoped inventory/detail navigation

## Current Artifacts

- Spec: [spec-0069-session-source-scope-and-provenance](../spec/spec-0069-session-source-scope-and-provenance.md)
- Evaluations:
  - [Contract](../evaluation/eval-0069-contract-session-source-scope-and-provenance.md)
  - [Design](../evaluation/eval-0069-design-session-source-scope-and-provenance.md)
  - [Functional](../evaluation/eval-0069-functional-session-source-scope-and-provenance.md)
  - [UX heuristic](../evaluation/eval-0069-ux-session-source-scope-and-provenance.md)
- Fix log: none

## Evaluation Coverage

- Contract: PASS.
- Design: PASS WITH SUGGESTIONS; required browser capability unavailable, so
  rendered four-width evidence remains explicit follow-up.
- Functional: PASS.
- UX heuristic: PASS WITH SUGGESTIONS; direct browser interaction remains
  explicit follow-up.

## Current Route

- Next role: Orchestrator — enter approved FEAT-0070
- Blocker classification: none
- Post-run recommendation: pass and continue the approved dependency chain

## Attempts

- Attempt 1:
  - status: passed
  - outcome: all source-level evaluators passed; 318 repository tests and privacy
    checks passed
  - notes: Browser skill remains selected for presentation evaluation, with its
    required in-app control capability currently unavailable

## Post-Contract Regression Check

- Needed: yes
- Result: passed; 318 tests and repository privacy check passed

## Human Review Outcome

- Decision: owner pre-approved dependency-ordered execution through FEAT-0070.
- Follow-up run: FEAT-0070 only after this run passes

## Continuity Notes

- `2026-08-02`: Orchestrator selected Fullstack Product with four ordered lanes
  and the full evaluator set.
- `2026-08-02`: registry-driven scopes, exact per-source counts, readable
  provenance, and detail navigation passed attempt 1.
- `2026-08-02`: owner review later replaced the ordinary inventory-card portion
  of this Run's presentation contract. RUN-20260802-76 supersedes that portion;
  the source-scope, query, pinned, Subsession, and detail results remain valid.
