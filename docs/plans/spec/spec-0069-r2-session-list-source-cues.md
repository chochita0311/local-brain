# SPEC-0069-R2: Session List Source Cues

## Metadata

- ID: `spec-0069-r2`
- Status: `superseded`
- Run ID: `run-20260802-76`
- Attempt: `1`
- Parent Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Supersedes: [spec-0069-session-source-scope-and-provenance](spec-0069-session-source-scope-and-provenance.md) for ordinary inventory-card presentation only
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lanes: inventory card structure → provenance tokens → owner docs
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Source Set

- FEAT-0069's owner-corrected acceptance contract and the still-valid source,
  query, pin, Subsession, and detail behavior from SPEC-0069.
- Sessions template and shared token stylesheet.
- Design Constitution, Design Evaluation, and Interaction Evaluation.

## Implementation Goal

- Reduce repeated source-name text in ordinary Sessions inventory cards while
  preserving compact, source-specific, accessible provenance.

## In-Scope Behavior

- Ordinary primary Session inventory cards omit the visible `source_name` line.
- The compact cue uses stable source identity first: Claude uses `CL`, personal
  Codex uses `CX`, and `codex-company` uses `CC`. Unknown future sources retain
  the current configured-label fallback.
- The compact cue's screen-reader-only text retains the configured source label
  and Session role; the change is not color-only or initials-only for assistive
  technology.
- Personal Codex keeps the existing Codex provenance tokens. Codex Company uses
  new semantic source-provenance aliases backed by the existing blue primitives.
- Pinned Session entries and Subsession disclosures keep their visible configured
  source names. Their compact cues use the same source-specific initials where
  those cues are present.
- Session filters, source-status summary, detail pages, dashboard, query scope,
  pagination, pins, and source data remain unchanged.

## Out-Of-Scope Behavior

- Removing source names from filters, Pinned Sessions, Subsessions, source status,
  details, Sessions Dashboard, Sources, Search, or other screen families.
- New primitive colors, parser or registry changes, source renaming, or source
  settings changes.

## State And Interaction Contract

- Default and filtered lists use the same card cue rules; no selected-source
  special case changes card structure.
- `CL`, `CX`, and `CC` remain fixed-width cues, so removing visible metadata does
  not move the title, utility actions, pin, or Subsession disclosure.
- Accessible source text remains available in the destination link even when the
  visible label is omitted.
- Existing narrow-layout rules continue to own card geometry at 700px and 320px.

## Contract Surfaces

- `source_cue` template macro and source-key class selection
- ordinary `.session-row` visible metadata structure
- source provenance semantic tokens and `.session-source`/pinned cue variants
- README, product, architecture, and Design Constitution wording

## Acceptance Mapping

- No repeated names → rendered ordinary Session rows contain no
  `session-provenance` element.
- Stable cues → rendered Claude/personal/company fixtures contain `CL`, `CX`, and
  `CC` respectively.
- Blue company treatment → component selectors consume only the new semantic
  aliases, which resolve to existing blue primitives.
- Accessibility → rendered cue retains configured `source_name` in `sr-only` text.
- Boundary preservation → pinned and Subsession visible labels and all existing
  Session interactions remain covered by regression tests.

## Evaluation Focus

- Exact cue mapping by stable source key versus shared provider kind.
- Absence of the ordinary-card visible source label with positive source data.
- Token ownership, contrast intent, card containment, and unchanged utility
  alignment at supported widths.
- Pinned/Subsession/detail/source-filter boundary preservation.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-02`: superseded for Pinned Sessions presentation by
  [SPEC-0069-R3](spec-0069-r3-pinned-session-source-cues.md). Owner review showed
  that retaining a visible Pinned source label was a regression from the existing
  compact panel; the ordinary-card and `CL`/`CX`/`CC` token contracts remain valid.
