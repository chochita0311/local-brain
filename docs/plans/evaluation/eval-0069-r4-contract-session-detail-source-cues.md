# EVAL-0069-R4: Session Detail Source Cues — Contract

## Metadata

- ID: `eval-0069-r4-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-78`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-r4-session-detail-source-cues](../spec/spec-0069-r4-session-detail-source-cues.md)
- Execution Profile: `frontend-product`
- Surface Lane: Session detail and Subsession source-cue contracts
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Checks

- Session inventory, Session detail, normalized Subsession detail, detail child
  rows, and lazy Subsession presentation import one shared source-cue macro.
- That macro chooses `CC` from `source_kind = codex-company` before considering
  the shared `provider_kind = codex` adapter identity.
- Detail heading and child-row provenance classes use stable source identity.
- Configured source labels remain in visible recovery metadata and accessible
  text; route, query, conversation, parent/child, and pin contracts are unchanged.
- README, PRD, Feature, product, architecture, Design Constitution, and design
  governance agree on the all-projection source-key icon rule.

## Evidence

- Targeted route/detail/UI set: 51 tests passed.
- Full repository suite: 323 tests passed.
- Privacy and diff checks passed.

## Findings

- None.

## Route

- Next action: `pass`.
