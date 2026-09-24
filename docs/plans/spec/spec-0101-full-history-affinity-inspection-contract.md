# SPEC-0101: Full-History Affinity Inspection Contract

## Metadata

- ID: `spec-0101`
- Status: `approved`
- Feature: [FEAT-0101](../feature/feat-0101-full-history-affinity-inspection-contract.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Run: [RUN-114](../run/run-20260923-114-full-history-affinity-inspection.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Attempt: `1`
- Created: `2026-09-23`

## Read Boundary

`session_affinity.py` reads only FEAT-0097's source-bound simulation owner and
original SQLite records. A nonblocking shared writer lock protects a complete
read; opening this consumer never creates a file, renews expiry or computes a
vector/community. Validate owner, database binding, expiry, report size (128 MiB),
producer/authority, full coverage, membership partitions and configuration.
Unknown/corrupt content fails closed with fixed non-private state text.

One process-local derived index may cache the current report, keyed by its file
signature and source DB/WAL signatures. A changed key triggers exhaustive source
inventory, not a sample; source signatures must remain stable through validation.
No filesystem cache or new persistent owner is introduced. Exact displayed
passages are independently resolved and revision-checked from current SQLite.

## Projection And Navigation

- Initial RUN-114 version `localbrain.session-affinity.v1`; the additive `v2`
  presentation in [SPEC-0104](spec-0104-temporal-affinity-flow.md) separates full
  map scope from text pages. Source/read authority is unchanged. Snapshot
  identity binds manifest and
  model/grouping configuration. Membership IDs remain snapshot-scoped.
- Coarse groups, finer groups and Session evidence form three observational
  scales. All occurrences of shared vectors and multi-group Sessions survive.
- Deterministic 24-item text-list pages and eight-occurrence evidence pages;
  graph paging was the initial RUN-114 projection, superseded by SPEC-0104's
  continuous canvas after owner review.
  Title search filters the complete level. An explicit inventory view enumerates
  all stored Sessions, including excluded and no-text records.
- Undirected edges aggregate actual input similarity across matching memberships;
  edge weights are maxima, not confidence or causation. No fabricated temporal
  links. Totals precede display filtering; fragmentation/overlap remain visible.
- Selection is separate from expansion. Native snapshot-scoped URLs own scope,
  pick, search and pages; obsolete snapshot/selection is explicit, never remapped.
- Return original role, character offsets and observation time beside verified
  literal text. Removed/revoked/changed evidence has no valid quote/source anchor.
- States: `missing`, `busy`, `current`, `stale`, `expired`, `invalid`,
  `unavailable`, `empty`, `selection-stale`. Stale hides map/evidence while showing
  old/current coverage and added/changed/removed occurrence counts. No auto-rerun.

## Verification

Passed RUN-113 closes real replay dependency. Synthetic tests cover complete
enumeration beyond 60 Sessions, duplicated vectors, overlap, paging, unknown
dates, exclusions, valid empty, source mutation/removal/append, configuration and
selection changes, corrupt/oversize/symlink report, expiry, shared-reader/writer
locking and source immutability. Actual readiness probes expose no private text.
Contract and Functional must pass before the UI consumes this implementation.

## Open Blockers

None. No UI, model admission, source expansion or organization mutation here.
