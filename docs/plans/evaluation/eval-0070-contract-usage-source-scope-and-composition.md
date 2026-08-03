# EVAL-0070: Usage Source Scope And Composition — Contract

## Metadata

- ID: `eval-0070-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-75`
- Attempt: `1`
- Feature: [feat-0070-usage-source-scope-and-composition](../feature/feat-0070-usage-source-scope-and-composition.md)
- Spec: [spec-0070-usage-source-scope-and-composition](../spec/spec-0070-usage-source-scope-and-composition.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Usage query, Source health, dashboard handoff, and owner contracts
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Evaluated source-key fact ownership, accepted Source set, aggregate/source
  arithmetic, Usage versus Session denominator, health handoff, and preserved
  normalization/pricing contracts.

## Checks

- Source options derive in Source-ID order from registered Claude/Codex adapter
  sources; `All` is synthetic UI scope and unknown stable keys fall back to it.
- Exact selection and source composition use `sources.kind`; provider kind owns
  only shared adapter semantics and visual cue.
- Personal Codex and Codex Company remain independent facts and composition rows
  while both use Codex parsing, token normalization, and pricing rules.
- Synthetic three-source evidence proves `All` equals exact source sums for
  normalized tokens, estimated cost, Usage Records, primary-work Sessions, MTD,
  and every Daily history bucket.
- Direct Maintenance and Subsession Usage remains in totals; only the separately
  labeled Session count uses work/primary identity.
- Claude `<synthetic>` exclusion uses Claude provider semantics, so additional
  Claude roots cannot bypass it and non-Claude source labels cannot trigger it.
- Source trust consumes persistent latest scan attempt/success/status/error plus
  Source File evidence; failed source attempts preserve calculated Usage and last
  success.
- Price snapshots, Project attribution, coverage, activity segmentation,
  normalizer repair, and projection calculation remain unchanged.

## Evidence

- Full repository suite: 322 tests passed in 2.577 seconds.
- Focused Usage/UI/value/schema suite: 60 tests passed.
- Schema presentation and nine value dictionaries are current.
- Cleanup audit: 531 objects; keep 440, defer 91.
- Repository privacy and `git diff --check`: passed.

## Evidence Gaps

- Private Usage and Session homes were not read. Synthetic provider-sharing
  Sources exercise the same relational, normalization, and query boundaries.

## Findings

- None.

## Route

- Next action: `pass`.
