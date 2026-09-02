# FEAT-0083: Atlassian Structure Reference Sync And Explorer

## Metadata

- ID: `feat-0083`
- Status: `passed`
- Boundary State: passed under [SPEC-0083 Attempt 1](../spec/spec-0083-atlassian-structure-reference-sync-and-explorer.md)
  and [RUN-93](../run/run-20260901-93-atlassian-structure-reference-sync-and-explorer.md)
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0016](../prd/prd-0016-atlassian-standard-url-recognition.md)
- Created: `2026-09-01`
- Updated: `2026-09-01`

## Goal

- Reconcile locally observed FEAT-0082 structure descriptors into durable,
  honest structure references and make them selectable in the Site-first
  Atlassian Explorer without claiming Item or persisted Space authority.

## Acceptance Contract

- Explicit zero-input Sync consumes only already persisted eligible Session and
  Local Context evidence through the passed FEAT-0080 source/cap/transaction
  boundary and the passed FEAT-0082 descriptor.
- A `structure` candidate creates or reuses one normalized-domain Site and one
  durable Site/service/`reference_kind`/`reference_identity` reference. Locator
  aliases and source evidence remain separate from stable reference identity.
- A `site` candidate has no structure identity. It is reported truthfully as
  recognized family/domain only and creates no reference row or zero-count
  Explorer branch.
- Structure references are separate from `atlassian_items`,
  `atlassian_spaces`, `space_id`, remote facts/content, access bindings,
  capability state, and Refresh eligibility. A container hint groups read-only
  presentation but never confirms or creates Project/Space containment.
- Each source is atomic. Session evidence remains merge-only under its
  authoritative scanner; a completely read Document owns bounded replacement.
  Failed/unavailable sources retain last-known stable reference identity and
  honest availability while changing no unrelated Item, Space, or local state.
- Repeat Sync reuses exact semantic identity and evidence; changed locator
  spelling or grouping hint cannot create a duplicate. Conflicting hints remove
  derived grouping rather than changing identity or silently choosing one.
- Sync reports structure-reference new/reused/evidence outcomes separately from
  link/document outcomes and separately counts recognized Site-only family
  candidates. Existing receipt, source-detail, single-flight, safe return, and
  no-script/enhanced ownership remain.
- Explorer groups eligible references under normalized-domain Site and a
  deterministic URL-derived container or `소속 미확인`, includes one center-list
  structure-reference row per eligible identity, and shows a read-first preview
  plus ordinary direct/no-script detail.
- Structure-reference and link/document counts remain separate and each
  hierarchy count equals adjacent list membership. Site-only candidates never
  appear as selectable zero-count nodes.
- Jira Project, Board, Filter, Dashboard, JSM portal/project, and Confluence
  Space copy remains explicit and includes `URL 기준`/local-evidence provenance.
  It never borrows Item freshness, coverage, remote content, or confirmation.
- Add remains explicit Issue/Page/Project/Space registration; equal persisted
  Space and structure-reference labels stay distinguishable and never silently
  convert or merge. Connections and Refresh exclude structure references unless
  a later separately approved authority changes that boundary.
- All work is local-only and performs no Provider, capability, runner, model,
  connected-discovery, Refresh, or external I/O.

## Scope Boundary

- In:
  - durable structure-reference identity, URL aliases, evidence, lifecycle,
    fresh/compatible schema, and owner docs
  - explicit Sync admission, atomic reconciliation, report/receipt outcomes
  - Site-first hierarchy/list/count/filter/search/selection read model
  - read-first preview, direct/no-script detail, provenance and terminology
  - responsive focus/history/scroll/patch continuity at four widths
- Out:
  - Item or persisted Space inference, `space_id` writes, or remote confirmation
  - Provider/access/capability/discovery/Refresh/model work
  - silent Add conversion or persisted-Space merge
  - another hierarchy depth, another primary action, or a new search mode

## Surface Lanes

- Persistence/Sync lane:
  - path roots: schema/compatibility, structure-reference domain module,
    `atlassian_evidence_sync.py`, source evidence, tests
  - dependencies: passed FEAT-0082 descriptor
  - expected evidence: identity, atomicity, cleanup/availability, repeat, report,
    caps, receipt, and zero external I/O
  - evaluator ownership: `contract`, `functional`
- Explorer/read-model lane:
  - path roots: browse/search/routes/templates/controller/styles as approved
  - dependencies: durable reference/evidence contract
  - expected evidence: hierarchy/list/count/detail/provenance/state at four widths
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable-owner lane:
  - path roots: Product, Architecture, Privacy, data-model owners, Design
    Constitution if visible law proves stable, plans and generated artifacts
  - dependencies: implemented contract
  - expected evidence: no Item/Space/access authority drift
  - evaluator ownership: `contract`

## Contract Surfaces

- Stable structure-reference, URL-alias, and source-evidence persistence.
- Site/service/reference-kind/reference-identity uniqueness and hint conflict.
- Sync candidate/outcome/reason taxonomy, caps, transactions, receipt/patch.
- Explorer route/read-model/list/detail/search/filter/count state.
- Add/Connections/Refresh/Item/Space authority separation.

## Required Evaluators

- `contract`: identity, schema/lifecycle, source authority, caps, report,
  zero-I/O, privacy, and owner parity.
- `design`: Site-first composition, row/detail provenance, terminology, and
  four-width containment.
- `functional`: fresh/repeat/change/failure/cleanup, filters/counts, direct and
  enhanced state, action regressions.
- `ux-heuristic`: distinction from Items/Spaces, orientation, recovery,
  responsive focus/history/scroll, and no-script clarity.

## User-Visible Outcome

- After Sync, a standard Jira Project/Board/Filter/Dashboard/JSM or Confluence
  Space URL appears as one durable `구조 참조` row beneath its domain, with an
  honest URL/evidence preview and no implication that remote data was read.

## Entry And Exit

- Entry point: explicit local Sync followed by ordinary Explorer/Search
  navigation.
- Exit: inspect the durable structure reference, return through preserved
  service/structure/query/filter/history context, or use Add/Connections/Refresh
  separately for their existing meanings.

## State Expectations

- New/reused: exact semantic reference and evidence counts are separate.
- Site-only: truthful bounded report only, no selectable row.
- Hint conflict: stable reference remains under `소속 미확인`.
- Source unavailable: last-known reference remains visibly unavailable; no
  fabricated freshness or destructive identity cleanup.
- Missing/archived/filtered: deterministic route and count behavior without
  widening Item-only filter semantics accidentally.
- Narrow: list-first structure row and explicit detail sheet/full-detail
  fallback with no horizontal overflow.

## Dependencies

- FEAT-0082 passed Contract and Functional evaluation under RUN-92 Attempt 1;
  the dependency gate is satisfied.
- SPEC-0083 and RUN-93 were created only after that lifecycle close.
- PRD-0015/FEAT-0081 Site-first Item behavior remains a regression baseline.

## Likely Affected Surfaces

- schema/db compatibility and data-model presentation/value registry
- structure-reference domain/evidence modules
- `src/localbrain/atlassian_evidence_sync.py`
- browse/search/main routes, Atlassian templates/controller/styles
- focused/full tests, durable Product/Architecture/Privacy/Source Memory,
  Design Constitution and generated planning/schema artifacts as required

## Pass Or Fail Checks

- PASS when fresh and compatible databases converge on one stable reference
  identity and evidence lifecycle with no Item/Space/access ownership drift.
- PASS when RapidBoard variants for one `rapidView` reuse one reference, distinct
  IDs stay distinct, and changing/conflicting `projectKey` never changes identity.
- PASS when one source failure publishes no partial Site/reference/evidence or
  cached identity to later sources and unchanged repeat is read-only reuse.
- PASS when Site-only family roots report honestly but create no row/branch.
- PASS when hierarchy/list/search/detail counts and filters agree for reference-
  only and mixed populations and equal Space/reference labels remain distinct.
- PASS when Add, Connections, Refresh, Item search/detail, and FEAT-0080 receipt/
  return/single-flight behavior regress cleanly.
- PASS when Chrome at `1440`, `920`, `700`, and `320` preserves focus, history,
  scroll, responsive containment, accessibility, and no-script execution.

## Regression Surfaces

- FEAT-0080 source population, per-source atomicity, report, receipt, and return.
- FEAT-0081 Site-first hierarchy, canonical Item URL grouping, and count parity.
- FEAT-0082 descriptor/target-key/privacy contract.
- FEAT-0079 Add/Connections and FEAT-0049 Refresh authority.

## Harness Trace

- Approved spec doc: [SPEC-0083 Attempt 1](../spec/spec-0083-atlassian-structure-reference-sync-and-explorer.md)
- Completed run: [RUN-93](../run/run-20260901-93-atlassian-structure-reference-sync-and-explorer.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  [contract](../evaluation/eval-0083-contract-atlassian-structure-reference-sync-and-explorer.md),
  [design](../evaluation/eval-0083-design-atlassian-structure-reference-sync-and-explorer.md),
  [functional](../evaluation/eval-0083-functional-atlassian-structure-reference-sync-and-explorer.md),
  and [UX](../evaluation/eval-0083-ux-atlassian-structure-reference-sync-and-explorer.md),
  all `PASS`
- Latest fix note: none

## Continuity Notes

- `2026-09-01`: owner approved the durable visible structure-reference product
  outcome and queued this Feature behind FEAT-0082. It is approved but must not
  enter Spec or Run before the foundation passes.
- `2026-09-01`: FEAT-0082 passed RUN-92 Attempt 1 with both required evaluators
  at `PASS`. The dependency gate closed before SPEC-0083 and RUN-93 were
  approved, so FEAT-0083 became the sole in-loop Atlassian Feature.
- `2026-09-01`: RUN-93 Attempt 1 passed Contract, Design, Functional, and UX
  evaluation. Full `480/480` regression, privacy, owner/generated checks, and
  Chrome/no-script evidence passed; FEAT-0083 is passed.
