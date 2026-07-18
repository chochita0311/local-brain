# EVAL-0020: Usage And Cost Fact Contract — Contract Attempt 4

## Metadata

- ID: `eval-0020-contract-attempt-4`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-27`
- Attempt: `4`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: immutable request-context pricing → calculator v2 → corrective Codex repair
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Model-specific context thresholds, base and above-threshold component rates, per-Fact tier selection, immutable snapshot ownership, calculator versioning, and the bounded Attempt 4 corrective repair.

## Checks

- Verified each Usage Fact selects its price tier independently from normalized non-cached input plus cache read.
- Verified the exact threshold remains on the base tier and only a strictly greater context uses the long-context tier.
- Verified compaction can return a later Fact in the same Session to the base tier; no Session, day, or month receives one inherited tier.
- Verified reasoning remains a subset of output and is not charged as an additional component.
- Verified the new snapshot freezes both tiers and their thresholds while prior snapshots remain unchanged.
- Verified calculator v2 is assigned only through the tiered snapshot and Attempt 4 Codex producer; Claude and historical snapshot contracts remain intact.
- Verified ordinary synchronization does not reprice history and the approved versioned repair is the sole bounded corrective exception.
- Reconciled Feature, Spec, Product, Architecture, PRD, roadmap, backlog, Run, evaluation, and fix-note wording.

## Evidence

- Boundary tests cover exact-threshold base pricing, one-token-above long-context pricing, and a later post-compaction return to base pricing.
- Frozen price tests cover GPT-5.5 and the supported GPT-5.6 Sol, Terra, and Luna model tiers.
- A fixed completed local-date boundary matched the installed offline ccusage report exactly for every Codex token dimension and monthly estimated cost.
- The complete repository suite passed with 82 tests; compilation and diff validation also passed.
- Private source paths and aggregate values were used only for local validation and are not copied into tracked evidence.

## Evidence Gaps

- None for the approved foundation contract.
- Acceptance impact: `not applicable`.

## Contract Evidence

- Producer surface: `ingest/codex.py` assigns the tiered immutable snapshot and versioned normalizer.
- Persistence surfaces: `schema.sql`, compatible migrations, model-price rows, snapshot metadata, and source-level repair.
- Calculator surface: `usage.py` derives the request-context tier and stores calculator v2 provenance.
- Consumer surfaces: source-neutral usage queries and Sessions Dashboard aggregates remain unchanged.

## Findings

- No remaining contract defect, spec gap, or planning gap in FEAT-0020 scope.
- The estimate remains a local trend value rather than billed spend, but its frozen request-tier boundary now matches the selected ccusage reference without creating a runtime dependency.

## Regression Notes

- Attempt 3 direct-event-first normalization, cumulative fallback, replay exclusion, model resolution, Claude pricing, Project snapshots, activity segmentation, and dashboard aggregation remain unchanged.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: Attempt 4 replaces Attempt 3 as the current FEAT-0020 price-contract acceptance evidence; Attempt 3 remains the token-normalization foundation.
