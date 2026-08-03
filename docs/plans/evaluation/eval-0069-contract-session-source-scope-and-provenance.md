# EVAL-0069: Session Source Scope And Provenance — Contract

## Metadata

- ID: `eval-0069-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-74`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-session-source-scope-and-provenance](../spec/spec-0069-session-source-scope-and-provenance.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Session query, route, provenance, and durable owner contracts
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Evaluated registry-derived scope identity, denominator parity, no-age-cutoff
  behavior, provenance ownership, URL normalization, and existing Session policy.

## Checks

- `전체` is followed by registered source options in Source-ID order; filters and
  URLs use stable `sources.kind`, never provider kind.
- Personal Codex and Codex Company reuse the Codex provider cue while remaining
  independent query, count, Project, pagination, and URL scopes.
- Headline, inventory, pagination, and Project grouping use the same
  `session_class = work` plus `session_role = primary` denominator.
- An old synthetic 2024 company Session remains counted, proving that Sessions
  inventory does not apply an age cutoff.
- Maintenance and Subsession records remain excluded from the primary
  denominator, while direct-child disclosure remains parent-owned.
- Unknown Source keys and missing workspace IDs normalize to valid URLs and
  preserve the other valid scope without carrying page state.
- Source display labels travel through inventory, pin, parent/child, and detail
  projections; direct details retain selected scope only as return orientation.

## Evidence

- Full repository suite: 318 tests passed in 2.276 seconds.
- Schema presentation and nine value dictionaries are current.
- Cleanup audit: 531 objects; keep 440, defer 91.
- Privacy check: passed for 678 candidate files.
- `git diff --check`: passed.

## Evidence Gaps

- Real private Session homes were not read; deterministic synthetic records cover
  source overlap, historical dates, denominator exclusions, and navigation.

## Findings

- None.

## Route

- Next action: `pass`.
