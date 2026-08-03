# SPEC-0069-R3: Pinned Session Source Cues

## Metadata

- ID: `spec-0069-r3`
- Status: `superseded`
- Run ID: `run-20260802-77`
- Attempt: `1`
- Parent Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Supersedes: [spec-0069-r2-session-list-source-cues](spec-0069-r2-session-list-source-cues.md) for Pinned Sessions presentation only
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Pinned Sessions presentation → owner docs
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Source Set

- FEAT-0069's owner-corrected acceptance contract and the still-valid ordinary
  card, source-key cue, and provenance-token behavior from SPEC-0069-R2.
- Sessions template, Pinned Sessions styles, positive rendered fixtures, and pin
  continuity contracts.

## Implementation Goal

- Restore the compact Pinned Sessions presentation by removing the newly added
  visible source name while retaining `CL`/`CX`/`CC` and accessible source identity.

## In-Scope Behavior

- Pinned Session cards do not render a visible configured source-name line.
- Their compact cue remains source-key-specific: Claude `CL`, personal Codex `CX`,
  and Codex Company `CC` with the approved provenance tokens.
- The cue exposes the configured source name through `sr-only` text instead of
  hiding the entire cue from assistive technology.
- The displayed activity date remains in the same metadata region.
- Pinned ordering, global filter independence, links, mutation behavior, panel
  scrolling, source data, ordinary cards, Subsessions, and detail remain unchanged.

## Out-Of-Scope Behavior

- Removing source names from filters, Subsessions, detail, source status, Sessions
  Dashboard, Sources, Search, or other screen families.
- Changing cue tokens, pin persistence, ordering, eligibility, or interaction.

## State And Interaction Contract

- Pinned entries with positive Claude, personal Codex, or Codex Company data omit
  the visible source-name element and keep the activity date.
- Removing the text must not change link, focus, scroll, unpin, empty, or narrow
  panel behavior.
- Accessible source text remains part of the Pinned destination link.

## Contract Surfaces

- Pinned Session markup and accessible cue structure
- obsolete `.pinned-session-provenance` style removal
- README, product, architecture, PRD, Feature, and Design Constitution wording

## Acceptance Mapping

- No repeated Pinned name → positive rendered panel contains no
  `pinned-session-provenance` element.
- Source recognition → rendered cue contains `CX`/`CC`/`CL` as applicable and the
  configured source name in `sr-only` text.
- Continuity → activity date, link, global pin projection, scroll preservation,
  pin mutation, and existing regression suites continue to pass.

## Evaluation Focus

- Positive-state suppression rather than empty-panel-only evidence.
- Visual metadata reduction without dead space or cue/date loss.
- Accessible source identity and unchanged Pinned interaction ownership.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-02`: fully implemented and passed by RUN-20260802-77, then superseded
  as the active FEAT-0069 Spec by [SPEC-0069-R4](spec-0069-r4-session-detail-source-cues.md).
  Its Pinned Sessions contract remains valid without change.
