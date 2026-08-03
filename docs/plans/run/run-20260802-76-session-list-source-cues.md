# RUN-20260802-76: Session List Source Cues

## Metadata

- ID: `run-20260802-76`
- Status: `passed`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Active Spec: [spec-0069-r2-session-list-source-cues](../spec/spec-0069-r2-session-list-source-cues.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Goal

- Keep ordinary Sessions cards compact with accessible `CL`/`CX`/`CC` source
  cues and a blue Codex Company provenance treatment.

## Selected Loop

- Feature type: `product`
- Profile: `frontend-product`
- Lanes: inventory card structure → provenance tokens → owner docs
- Affected screen: `/sessions`
- Components: ordinary Session row, compact source cue, pinned cue
- Required evaluators: Contract, Design, Functional, UX Heuristic
- Current phase: complete

## Contract Surfaces

- source-key cue mapping and accessible label
- ordinary inventory-card metadata boundary
- semantic provenance token ownership

## Current Artifacts

- Spec: [spec-0069-r2-session-list-source-cues](../spec/spec-0069-r2-session-list-source-cues.md)
- Evaluations:
  - [Contract](../evaluation/eval-0069-r2-contract-session-list-source-cues.md)
  - [Design](../evaluation/eval-0069-r2-design-session-list-source-cues.md)
  - [Functional](../evaluation/eval-0069-r2-functional-session-list-source-cues.md)
  - [UX heuristic](../evaluation/eval-0069-r2-ux-session-list-source-cues.md)
- Fix log: none

## Evidence Plan

- Render synthetic Claude, personal Codex, and Codex Company inventory rows.
- Assert `CL`/`CX`/`CC`, no visible ordinary-row source-name element, retained
  screen-reader source label, and unchanged pinned/Subsession visible labels.
- Verify semantic-token references, relevant Session UI tests, full repository
  tests, and privacy checks.
- Attempt browser evidence through the required Browser skill; if its control
  capability remains unavailable, record partial visual/interaction coverage
  without claiming rendered geometry.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: all four evaluators passed; Design and UX retain explicit partial
    browser-evidence coverage
  - notes: 322 repository tests and privacy checks passed

## Post-Contract Regression Check

- Needed: yes
- Result: passed; source/template/token owner assumptions are aligned, 322 tests
  pass, and the privacy check passes for 694 candidate files

## Human Review Outcome

- Decision: owner directly approved the corrected ordinary-card presentation.
- Follow-up run: none unless evaluation finds a bounded defect

## Continuity Notes

- `2026-08-02`: Orchestrator selected Frontend Product. Browser skill is active,
  but the required in-app browser control capability is unavailable in this
  session, so rendered evidence is currently a known partial-coverage gap.
- `2026-08-02`: attempt 1 passed. Synthetic rendered HTML verifies `CL`/`CX`/`CC`,
  ordinary-card visible-label suppression, accessible configured labels, and
  pinned/Subsession boundary preservation; the full 322-test suite passes.
- `2026-08-02`: post-run owner review invalidated the assumption that Pinned
  Sessions should retain a visible source label. RUN-20260802-77 supersedes only
  that projection; the ordinary-card cue and token results remain valid.
