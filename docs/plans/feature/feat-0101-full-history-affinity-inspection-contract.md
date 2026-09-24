# FEAT-0101: Full-History Affinity Inspection Contract

## Metadata

- ID: `feat-0101`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed` (`data`, `infra`)
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-23`
- Updated: `2026-09-23`
- User review status: approved by continuous-through-UI authorization, 2026-09-23.

## Goal

Make existing full-history embedding results safely consumable by an inspection
map without claiming that similarity communities are verified work areas or
efforts. Reuse FEAT-0097's simulation/cache owner rather than add another corpus,
vector store or production workflow identity system.

## Acceptance Contract

### 1. Revalidate Whole-History Coverage And Replay

- Admit the existing indexed Session population through the execution snapshot,
  using FEAT-0097's primary-work user/assistant text rules. Account for every
  Session, including explicit exclusions and no-eligible-text records. No first
  60, top-N, recent-only or folder-only substitute for the full population.
- The completed backfill is not evidence that its report matches today's source
  snapshot. Check freshness before consumption; report new/changed/removed input
  and exclusions without exposing private inventory in tracked output.
- Close FEAT-0097's outstanding **real unchanged-input and grouping-only replay**
  checks before this Feature passes. Both must reuse valid vectors with zero
  encoding calls; unchanged replay must reproduce grouping. Record observed
  results in that Feature's existing evaluation owner, not a fabricated PASS.
- If source deltas require preparation after execution approval, reuse the
  verified existing embedding runtime and encode only missing/changed inputs.
  No forced whole-corpus recalculation, new model or native-file rescan.
- Synthetic revision/removal/corruption tests establish invalidation without
  editing real source data. Confirm original-source immutability in live checks.

### 2. Expose Evidence, Not Invented Organization

- Version the read contract with source snapshot, model/chunk configuration,
  grouping parameters and producer identity. Preserve the existing
  `inferred-affinity-only` authority and `lineage_status=not_inferred` meaning.
- Distinguish Session count, chunk-occurrence count and unique embedded-input
  count. One cached vector can represent multiple identical-text occurrences;
  every occurrence retains its own exact Session/message provenance.
- Expose coarse communities, their existing finer subgroups and undirected
  similarity edges. Call them similarity groups/subgroups, not confirmed areas,
  efforts, continuation, branching, merging or current work state.
- Existing source-title labels remain explicitly representative labels, not
  generated category names. No LLM labeling or role/goal extractor is needed.
- Retain multi-group Session membership, singletons, exclusions and totals before
  display filtering. Surface fragmentation and cross-Session coverage. Neither
  a fixed desired cluster count nor automatic parameter search may conceal poor
  grouping or make a quality claim from a small rendered set.
- Return bounded overview, neighborhood and evidence views while making all
  admitted groups/occurrences reachable through deterministic paging or search.
  A viewport budget is not a semantic population limit.

### 3. Keep Selection And Freshness Honest

- Community IDs derived from membership are snapshot-scoped. Recalculation may
  change them; do not promote them to permanent flow IDs or silently map an old
  selection to the nearest new group.
- Bind view selections and source locators to their snapshot/configuration.
  Resolve evidence against the original current record and exact revision.
  Changed, removed, excluded or unavailable evidence is reported explicitly;
  never fuzzy-match a replacement quote or invent a valid source link.
- Define deterministic states: not prepared, preparing/busy, current, stale,
  expired, invalid/unavailable and valid empty. Stale output may remain visible
  only with its snapshot boundary; invalid source anchors cannot masquerade as
  current evidence. Busy reads must not observe a partially published report.
- Read-only consumers never ingest, encode, regroup or start background work.
  Preparation remains an explicit existing local command, outside page viewing.

### 4. Preserve One Finite Runtime Owner

- Reuse FEAT-0097's local, out-of-repository store, atomic report publication,
  lock/recovery, one previous report and 30-day inactive expiry contract.
- No permanent source-body copy, new SQLite organization table or second report
  ownership scheme. Rebuild derived read views from the owned report and source
  locators. Expired data produces a recoverable state, not an automatic rerun.
- Cache/report invalidation and cleanup must preserve active readers/writers and
  unrelated data. Track only synthetic examples and aggregate non-private checks.

## Scope Boundary

- In: consumer contract, full-population accounting, exact provenance,
  snapshot-scoped navigation, existing-cache replay and source-delta readiness.
- Out: UI, new inference models, relation judgments, goal/state extraction,
  training, Foundry changes, production identity, organization mutation,
  automatic refresh, remote access and legacy retirement.

## Surface Lanes

- Data: simulation inventory/report/cache ownership and read-model projection;
  contract and functional evidence covers counts, provenance and invalidation.
- Infra: existing command/runtime verification, replay and finite artifact
  lifecycle; source policy and interruption behavior must remain intact.

## Contract Surfaces

Existing simulation reports/cache namespace, source locators, read-model version,
snapshot-scoped selection/paging and readiness states. Exact field/schema/API
shapes belong in the Spec after approval; these authority and behavior rules do
not. No frontend needs to infer category meaning or start computation.

## Dependencies

- [FEAT-0097](feat-0097-replayable-session-simulation.md): implemented producer;
  its outstanding live replay evidence must be completed, not assumed.
- Existing local source admission and verified embedding assets only.
- No dependency on FEAT-0098/0100 extractor admission or FEAT-0103's trial.

## Likely Affected Surfaces

`session_simulation.py`, `session_simulation_graph.py`, a bounded consumer module,
simulation command/tests, and their architecture/privacy owner docs if contracts
change. No route, template, JavaScript or stylesheet changes in this foundation.

## Pass Or Fail Checks

- Reconcile all Session/exclusion, occurrence and unique-vector totals, including
  duplicates, multi-goal Sessions, singletons and a valid empty corpus.
- Verify stable unchanged replay and zero-encoding grouping-only replay on the
  actual admitted snapshot; synthetic checks alone do not close the live gap.
- Test source append/change/removal, stale selection, configuration differences,
  unavailable source, corruption, expiry and concurrent preparation/read states.
- Ensure deterministic bounded reads can enumerate the complete admitted set;
  missing or unexamined data cannot disappear behind a display limit.
- Verify no source/organization writes, remote calls, hidden generation or new
  permanent private artifact. Contract and Functional evaluators must both pass.

## Regression Surfaces

FEAT-0097 recomputation/recovery, the labeled FEAT-0096 sampled comparator,
Session source reading, current Workstreams/Threads and all frozen model trials.

## Harness Trace

- Spec: [SPEC-0101](../spec/spec-0101-full-history-affinity-inspection-contract.md).
- Run: [RUN-114](../run/run-20260923-114-full-history-affinity-inspection.md).
- Downstream product: [FEAT-0102](feat-0102-full-history-affinity-map.md).

## Continuity Notes

- `2026-09-23`: RUN-114 passed the passive read contract after RUN-113's real
  replay closure. Thirteen synthetic tests and a content-free actual readiness/
  exact-evidence probe pass. No private inventory or quotes enter tracked evidence.
  Required [Contract](../evaluation/eval-0101-contract-full-history-affinity-inspection.md)
  and [Functional](../evaluation/eval-0101-functional-full-history-affinity-inspection.md)
  coverage is complete for this consumer boundary, not semantic quality.

- `2026-09-23`: drafted from the relation-first review. Recommended first target;
  no private-source check, model call, source delta refresh or code change ran
  during planning. Earlier report readiness must be measured at execution time.
