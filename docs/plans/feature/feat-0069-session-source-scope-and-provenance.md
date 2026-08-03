# FEAT-0069: Session Source Scope And Provenance

## Metadata

- ID: `feat-0069`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Created: `2026-08-02`
- Updated: `2026-08-03`

## Goal

- Let the owner browse all retained primary work Sessions together or select
  Claude, personal Codex, or Codex Company independently while keeping source
  provenance clear in inventory and detail views.

## Acceptance Contract

- Sessions presents peer primary scopes `전체`, `Claude`, `Codex`, and
  `Codex Company`; there is no combined-Codex primary tab.
- `전체` includes every retained eligible primary work Session from accepted local
  AI sources with no undocumented age cutoff. `Codex` selects only the personal
  source and `Codex Company` only the company source.
- Source controls derive from stable accepted source identities and labels rather
  than a hard-coded provider vocabulary. `전체` remains first and the registered
  source order is deterministic.
- Source scope uses the stable source key in reproducible GET state. Unknown keys
  fall back to `전체`; changing source resets Session-owned pagination to page 1
  while preserving a valid Project/workspace filter.
- The selected source constrains the headline eligible Session count, timeline
  rows, pagination total, and source-scoped Project result consistently. Aggregate
  counts equal the sum of the source counts under the same inclusion contract.
- Ordinary primary Session inventory cards omit the repeated visible source label
  and instead use the compact source cues `CL` for Claude, `CX` for personal
  Codex, and `CC` for Codex Company. The configured source label remains in
  accessible text, and Codex Company uses the approved blue provenance tokens.
  Pinned Session cards, detail headings, and detail Subsession rows follow the
  same compact-cue rule without a repeated visible source name. Configured
  labels remain in accessible text, and every Session/Subsession icon uses the
  same source-key cue mapping rather than collapsing provider-sharing Sources.
  Detail Subsession rows align their question, event, and date metadata with the
  ordinary Sessions inventory reading order.
- Primary work, Maintenance, and Subsession inclusion rules remain unchanged:
  only primary work Sessions appear in headline/list/pagination denominators,
  Subsessions remain parent-owned disclosures, and Maintenance stays excluded.
- Existing 15-item pagination, Projects mode, pin behavior, Session detail routes,
  conversation reading, direct links, and back/forward navigation remain intact.

## Scope Boundary

- In:
  - registry-driven Sessions source controls and stable-key route normalization
  - all-source and per-source inventory queries, counts, and pagination
  - source-aware Project/workspace filtering where Sessions already supports it
  - compact, accessible source provenance without repeated visible source names
    on ordinary cards, Pinned cards, detail headings, and detail Subsession rows,
    plus consistent source-key icon cues across every Session projection
  - selected-scope URL, navigation, focus, and responsive behavior
  - shared eligible-primary-work denominator verification across affected Session
    inventory and Project-derived counts
- Out:
  - synchronization implementation or health cards owned by FEAT-0068
  - Sessions Dashboard Usage controls and composition owned by FEAT-0070
  - combined-Codex tab, nested account selector, or Gemini ingestion
  - source registration editing, disablement, removal, purge, retention, or restore
  - changes to parser, Usage normalization, Maintenance, Subsession, or pin policy

## Surface Lanes

- Query and route lane:
  - path roots: Session inventory/detail/pin queries and routes, source scope
    normalization, pagination, Project/workspace filtering, and tests
  - dependencies: passed FEAT-0068 source registry and ingestion
  - expected evidence: stable-key filtering, exact denominator parity, valid return
    URLs, unknown fallback, and no age cutoff
  - evaluator ownership: `contract`, `functional`
- Inventory presentation lane:
  - path roots: Sessions template, source controls, Session/Subsession rows, pinned
    panel, shared provenance styles, and client behavior
  - dependencies: query and route lane
  - expected evidence: peer scopes, `CL`/`CX`/`CC` distinction, no repeated visible
    source label in ordinary and Pinned cards, stable row geometry, responsive
    containment, and source-transition continuity
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Detail presentation lane:
  - path roots: Session detail and parent/Subsession provenance and navigation
  - dependencies: query and route lane
  - expected evidence: `CL`/`CX`/`CC` icon parity, accessible configured labels,
    no repeated visible source label, question/event/date row alignment,
    direct-entry context, parent/child integrity, and conversation orientation
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, architecture, Session activity, design, interaction, and
    value-dictionary owner docs
  - dependencies: all implementation lanes
  - expected evidence: one denominator/source-scope owner and no stale two-source
    UI classification
  - evaluator ownership: `contract`

## Contract Surfaces

- Sessions `source` GET parameter and normalized stable-key vocabulary
- eligible-primary-work Session denominator
- Session inventory, pagination, detail, parent/Subsession, and pinned projections
- Project/workspace filter combination and return URL behavior
- source provenance label, source-specific cue, accessible name, and CSS semantics

## Required Evaluators

- `contract`: source-key route/query ownership, denominator parity, provenance
  shape, and current Session/Subsession/pin contracts.
- `design`: peer-control hierarchy, compact ordinary-card provenance, stable
  row/detail geometry, Codex Company token use, and `1440`, `920`, `700`, and
  `320` containment.
- `functional`: all/source scopes, pagination, Project/workspace combinations,
  direct links, back/forward, pins, Subsessions, and no-age-cutoff counts.
- `ux-heuristic`: distinction between the two Codex scopes, transition clarity,
  orientation, and filter recovery.

## User-Visible Outcome

- The owner can see combined Session history or isolate company Codex activity
  without personal Codex data leaking into that selection. Session inventory,
  Pinned, and detail projections remain compact through `CL`/`CX`/`CC` without
  repeating configured source names, while accessible labels preserve identity.

## Entry And Exit

- Entry point: open Sessions or select a peer source control.
- Exit or transition behavior: the new source begins at page 1, preserves a valid
  Project/workspace scope, updates URL and counts coherently, and retains normal
  navigation to and from Session detail.

## State Expectations

- Default: `전체` is selected and combines every eligible retained source.
- Selected: one stable source key controls rows, total, pagination, and provenance.
- Empty: identifies the selected source and does not imply the source is disabled
  or that `전체` is empty.
- Unavailable source: previously retained Sessions remain browsable while FEAT-0068
  health communicates synchronization attention separately.
- Invalid URL source: normalize to `전체` without a broken or empty phantom tab.
- Responsive: controls remain reachable and `CX` versus `CC`, backed by accessible
  configured labels, distinguishes both Codex sources without relying on color.

## Dependencies

- [FEAT-0068](feat-0068-multi-source-session-synchronization-and-health.md) must be
  `passed` before build.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/queries.py`
- `src/localbrain/session_pins.py`
- source-aware activity/search/retrieval projections where Session provenance is
  rendered
- `src/localbrain/templates/sessions.html`
- `src/localbrain/templates/session.html`
- shared provenance styles and Session client behavior
- Session inventory, detail, pagination, filter, pin, browser, and count tests
- product, architecture, Session, design, interaction, and value owner docs

## Pass Or Fail Checks

- Pass if `전체`, Claude, personal Codex, and Codex Company select exactly their
  approved Session sets and `Codex` never includes company data.
- Pass if aggregate eligible counts equal per-source sums with no hidden date
  cutoff and all affected consumers use the same primary-work denominator.
- Pass if source transitions reset page 1, preserve a valid workspace filter, and
  keep URL, selected state, focus, and scroll behavior intentional.
- Pass if ordinary, Pinned, detail-heading, and detail Subsession projections show
  `CL`/`CX`/`CC` without repeated visible source names, keep accessible configured
  labels, and detail Subsession rows present question, event, and date metadata in
  the Sessions inventory order at all target widths.
- Pass if existing pagination, Projects mode, pin mutation, Subsession disclosure,
  detail reading, and direct navigation regressions pass.
- Fail on combined-Codex scope, provider-kind filtering, Maintenance/Subsession
  leakage into primary counts, hard-coded two-source controls, visible source-name
  repetition in ordinary or Pinned cards, or color-only provenance.

## Regression Surfaces

- FEAT-0015 Session/Subsession source and parent contract
- FEAT-0017 15-item pagination and source/workspace URL state
- FEAT-0059 pin controls, pinned recall, row geometry, focus, and scroll continuity
- Session conversation reading and direct detail navigation
- Projects view and path-derived inventory behavior
- sync scope and source-health behavior from FEAT-0068
- responsive shell, provenance design semantics, and repository privacy

## Harness Trace

- Active spec doc: [spec-0069-r5-session-detail-metadata-and-subsession-stats](../spec/spec-0069-r5-session-detail-metadata-and-subsession-stats.md)
- Active run: [run-20260803-81-session-detail-metadata-and-subsession-stats](../run/run-20260803-81-session-detail-metadata-and-subsession-stats.md)
- Execution profile: `frontend-product`
- Latest evaluator reports:
  - [Contract](../evaluation/eval-0069-r5-contract-session-detail-metadata-and-subsession-stats.md): `PASS`
  - [Design](../evaluation/eval-0069-r5-design-session-detail-metadata-and-subsession-stats.md): `PASS` with partial browser evidence
  - [Functional](../evaluation/eval-0069-r5-functional-session-detail-metadata-and-subsession-stats.md): `PASS`
  - [UX heuristic](../evaluation/eval-0069-r5-ux-session-detail-metadata-and-subsession-stats.md): `PASS` with partial browser evidence
- Latest fix note: none

## Continuity Notes

- `2026-08-02`: proposed separately from Usage so the Sessions inventory, detail,
  pagination, pin, and source-transition behavior remain one evaluable Product
  outcome.
- `2026-08-02`: human owner approved this Feature boundary for sequential
  execution after FEAT-0068 passes.
- `2026-08-02`: RUN-20260802-74 entered the Fullstack Product execution loop.
- `2026-08-02`: attempt 1 passed all required source-level evaluators. Browser
  evidence remains an explicit non-blocking follow-up because the required
  in-app control capability was unavailable; 318 tests and privacy checks pass.
- `2026-08-02`: post-run owner review corrected the ordinary Session-card
  presentation contract: remove repeated visible source names, distinguish
  personal and company Codex as `CX` and `CC`, and give `CC` a blue provenance
  treatment. The boundary remains FEAT-0069, but SPEC-0069 is superseded by its
  r2 presentation correction and RUN-20260802-76.
- `2026-08-02`: RUN-20260802-76 passed attempt 1 with all four evaluator results
  passing, 322 repository tests passing, and privacy checks passing. Design and
  UX retain an explicit non-blocking browser-evidence gap because the required
  in-app control capability was unavailable.
- `2026-08-02`: owner review identified that visible source names were also added
  to Pinned Sessions despite the pre-existing compact presentation. This invalidates
  the pinned-projection assumption in SPEC-0069-R2; SPEC-0069-R3 and
  RUN-20260802-77 restore icon-only visible provenance with accessible source text.
- `2026-08-02`: RUN-20260802-77 passed attempt 1 with all four evaluator results,
  322 repository tests, privacy, and diff checks passing. Design and UX retain the
  explicit non-blocking browser-evidence gap.
- `2026-08-02`: owner review found that Session and Subsession detail templates
  still derived icons from shared provider kind, so Codex Company rendered `CX`.
  SPEC-0069-R4 and RUN-20260802-78 extend the source-key cue contract to every
  detail projection.
- `2026-08-02`: RUN-20260802-78 passed attempt 1 with all four evaluator results,
  323 repository tests, privacy, and diff checks passing. Design and UX retain the
  explicit non-blocking browser-evidence gap.
- `2026-08-03`: owner review removed repeated configured source names from detail
  headings and detail Subsession rows, while retaining source-key icons and
  accessible labels. The same correction adds question count before event count
  in detail Subsession rows. SPEC-0069-R5 and RUN-20260803-81 own this bounded
  presentation correction.
- `2026-08-03`: RUN-20260803-81 passed attempt 1 after restoring the source-kind
  fallback exclusively in accessible detail text. All four evaluator results,
  the final 327-test suite, privacy, and diff checks pass. Design and UX retain an
  explicit non-blocking browser-evidence gap because the required in-app control
  capability was unavailable.
