# FIX-0022: Usage Normalizer Contract Repair

## Metadata

- ID: `fix-0022-usage-normalizer-contract-repair`
- Status: `complete`
- Run ID: `run-20260718-25`
- Attempt: `2`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: source normalization and derived-fact repair
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Input Reports

- Human runtime review found Codex below Claude despite higher observed account activity.
- A private metadata-only audit found materially more positive Codex cumulative observations than persisted latest-per-turn facts, proving that same-turn overwrite caused substantial undercounting.
- A private Claude comparison with ccusage found one deduplicated record whose aggregate cache-create value was zero while its nested ephemeral breakdown was positive, producing a small bounded difference.
- Persistence audit found that ordinary synchronization skips unchanged healthy files and forced parsing does not delete obsolete fact identities, so a parser-only correction could double count.

## Fix Scope

- Replace Codex latest-per-turn normalization with monotonic cumulative deltas.
- Add the bounded Claude zero-aggregate cache-create fallback.
- Add adapter contract versions to source files and Usage Facts.
- Reparse every file for an affected source and reconcile their complete derived-fact union transactionally while preserving historical price and Project snapshots.
- Refresh the private local database only after automated validation and create a local backup before the repair.

## Exclusions

- No user-facing reset button.
- No runtime ccusage dependency or remote price lookup.
- No retroactive price-catalog update for unknown Codex models.
- No change to activity-time, Session hierarchy, or Project reconciliation policy.

## Remaining Issues

- Later official-adapter evidence invalidated the cumulative-only Codex repair basis: `last_token_usage` is the primary event delta and cumulative subtraction is only a fallback.
- The installed ccusage comparison also showed that dated `codex-auto-review` fallback mapping, current model-price coverage, and the configured fast service tier materially affect the trend estimate.
- These are SPEC-0020 gaps rather than safe implementation-only fixes. A second versioned repair and runtime refresh remain paused for human approval.

## Return Decision

- `re-evaluate`

## Continuity Notes

- `2026-07-18`: opened after human post-run review approved a corrected Spec and live local repair.
- `2026-07-18`: completed after source-level union repair, active-file append detection, 76 passing tests, private all-source synchronization, repeat-scan verification, database integrity verification, and successful dashboard route rendering.
- `2026-07-18`: superseded as current acceptance evidence by a later ccusage source/report comparison; the historical changes remain implemented until a corrected Spec and repair are approved.
