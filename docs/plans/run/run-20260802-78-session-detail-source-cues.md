# RUN-20260802-78: Session Detail Source Cues

## Metadata

- ID: `run-20260802-78`
- Status: `passed`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Active Spec: [spec-0069-r4-session-detail-source-cues](../spec/spec-0069-r4-session-detail-source-cues.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Goal

- Render Codex Company as `CC` in primary Session detail, normalized Subsession
  detail, and parent-detail Subsession rows.

## Selected Loop

- Feature type: `product`
- Profile: `frontend-product`
- Lanes: Session detail → Subsession detail/list → owner docs
- Affected routes: `/sessions/{id}` and lazy Subsession detail
- Components: detail heading source cue and Subsession list cue
- Required evaluators: Contract, Design, Functional, UX Heuristic
- Current phase: complete

## Contract Surfaces

- detail template source-cue macro and source-key classes
- primary/child route projection fields
- visible and accessible provenance continuity

## Current Artifacts

- Spec: [spec-0069-r4-session-detail-source-cues](../spec/spec-0069-r4-session-detail-source-cues.md)
- Evaluations:
  - [Contract](../evaluation/eval-0069-r4-contract-session-detail-source-cues.md)
  - [Design](../evaluation/eval-0069-r4-design-session-detail-source-cues.md)
  - [Functional](../evaluation/eval-0069-r4-functional-session-detail-source-cues.md)
  - [UX heuristic](../evaluation/eval-0069-r4-ux-session-detail-source-cues.md)
- Fix log: none

## Evidence Plan

- Render synthetic company primary and normalized child detail routes and assert
  `CC` despite `provider_kind = codex`.
- Statically verify the lazy template uses the same source-key contract.
- Run detail/UI tests, full repository tests, privacy, and diff checks.
- Attempt Browser-skill evidence; record partial design/UX coverage if its required
  in-app control capability remains unavailable.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: all four evaluators passed; Design and UX retain explicit partial
    browser-evidence coverage
  - notes: 323 repository tests, privacy, and diff checks passed

## Post-Contract Regression Check

- Needed: yes
- Result: passed; company primary, child row, and normalized child detail fixtures,
  323 repository tests, privacy checks, and `git diff --check` pass

## Human Review Outcome

- Decision: owner requires `CC` parity on Session and Subsession detail.
- Follow-up run: none unless evaluation finds a bounded defect

## Continuity Notes

- `2026-08-02`: Orchestrator selected Frontend Product. Browser skill is active,
  but its required in-app control capability is unavailable in this session.
- `2026-08-02`: attempt 1 passed. All Session and Subsession templates now share
  the stable source-key cue contract; company primary, child-row, and child-detail
  fixtures render `CC` despite their shared Codex provider kind.
