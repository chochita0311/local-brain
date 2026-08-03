# EVAL-0069-R5: Session Detail Metadata And Subsession Stats — Contract

## Metadata

- ID: `eval-0069-r5-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260803-81`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-r5-session-detail-metadata-and-subsession-stats](../spec/spec-0069-r5-session-detail-metadata-and-subsession-stats.md)
- Execution Profile: `frontend-product`
- Surface Lane: detail child projection and accessible source identity
- Evidence Coverage: `complete`
- Created: `2026-08-03`

## Checks

- `user_message_count` is read from the existing direct-child Session row and
  added only to the detail view model; no schema, parser, denominator, or stored
  value changed. Lazy Claude child summaries derive the same value from already
  parsed `message + user` events.
- Configured source labels remain in `sr-only` cue text, including the registered
  `source.kind` fallback in the normalized detail template.
- Visible configured source copy is absent from the primary heading, normalized
  and lazy Subsession eyebrows, and parent-detail child metadata.
- PRD, Feature, product, architecture, README, Design Constitution, and design
  governance agree on the compact detail provenance and child-stat order.

## Evidence

- Focused Session/UI suite: 50 tests passed.
- Final full repository suite: 327 tests passed.
- Value-registry and owner-doc contract checks passed after the bounded
  accessibility-fallback correction.
- Privacy check passed for 722 candidate files; `git diff --check` passed.

## Findings

- Attempt 1 initially removed the registered `source.kind` fallback together with
  the visible eyebrow. Classification: implementation bug. The fallback was
  restored only inside accessible text and both failing contract checks passed.

## Route

- Next action: `pass`.
