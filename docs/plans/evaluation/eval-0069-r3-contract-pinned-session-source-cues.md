# EVAL-0069-R3: Pinned Session Source Cues — Contract

## Metadata

- ID: `eval-0069-r3-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-77`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-r3-pinned-session-source-cues](../spec/spec-0069-r3-pinned-session-source-cues.md)
- Execution Profile: `frontend-product`
- Surface Lane: Pinned Sessions presentation and owner-doc contracts
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Checks

- A positive Pinned projection contains no `pinned-session-provenance` element.
- `CX` and `CC` remain visible through the stable source-key cue macro, while the
  configured names remain in `sr-only` text inside the destination link.
- The displayed activity date remains present and Pinned ordering, identity,
  mutation, and source data contracts are unchanged.
- PRD, Feature, README, product, architecture, Design Constitution, and design
  governance now agree that ordinary and Pinned cards share compact provenance.
- SPEC-0069-R2 is explicitly superseded only for its incorrect Pinned exception.

## Evidence

- Positive rendered Pinned/UI contract set: 40 tests passed in 0.257s.
- Full repository suite: 322 tests passed in 2.430s.
- Privacy check: passed for 700 candidate files.
- `git diff --check`: passed.

## Findings

- None.

## Route

- Next action: `pass`.
