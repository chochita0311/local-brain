# EVAL-0069-R2: Session List Source Cues — Contract

## Metadata

- ID: `eval-0069-r2-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-76`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-r2-session-list-source-cues](../spec/spec-0069-r2-session-list-source-cues.md)
- Execution Profile: `frontend-product`
- Surface Lane: inventory cue, semantic provenance token, and owner-doc contracts
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Evaluated source-key cue ownership, accessible-label preservation, ordinary-card
  suppression, semantic-token ownership, and projection boundaries.

## Checks

- The template maps stable `codex-company` to `CC` before considering its shared
  `codex` provider kind; personal `codex` remains `CX` and Claude remains `CL`.
- Ordinary Session rows no longer render `session-provenance`, while the same link
  retains configured `source_name` and Session role in `sr-only` text.
- Pinned and Subsession projections retain their visible configured source names.
- Codex Company components consume reusable semantic aliases; those aliases point
  to the existing blue primitives, and component selectors contain no raw color.
- PRD, Feature, README, product, architecture, Design Constitution, and design
  governance agree on the corrected presentation boundary.

## Evidence

- Synthetic rendered-template and UI contract tests: 40 passed initially.
- Session inventory, contract, pin, and UI regression set: 53 passed in 0.318s.
- Full repository suite: 322 passed in 2.396s.
- Privacy check: passed for 694 candidate files.

## Evidence Gaps

- None for the declared template, token, accessibility, and owner-doc contracts.

## Findings

- None.

## Route

- Next action: `pass`.
