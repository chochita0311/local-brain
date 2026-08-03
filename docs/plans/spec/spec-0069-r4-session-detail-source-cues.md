# SPEC-0069-R4: Session Detail Source Cues

## Metadata

- ID: `spec-0069-r4`
- Status: `superseded`
- Run ID: `run-20260802-78`
- Attempt: `1`
- Parent Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Extends: [spec-0069-r3-pinned-session-source-cues](spec-0069-r3-pinned-session-source-cues.md) without changing its passed Pinned contract
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lanes: Session detail → Subsession detail/list → owner docs
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

Superseded by
[SPEC-0069-R5](spec-0069-r5-session-detail-metadata-and-subsession-stats.md).
The stable source-key cue contract remains valid; R5 owns the corrected visible
metadata hierarchy.

## Source Set

- FEAT-0069 and the passed `CL`/`CX`/`CC` source-key cue contract from R2/R3.
- Session detail, normalized Subsession detail, detail child-list, and lazy Claude
  Subsession templates and route projections.

## Implementation Goal

- Make every Session and Subsession detail icon use stable source identity so a
  Codex Company record never renders the personal Codex `CX` cue.

## In-Scope Behavior

- The primary Session detail heading uses `session.source_kind` for its class and
  cue mapping: Claude `CL`, personal Codex `CX`, Codex Company `CC`.
- A normalized Subsession detail, rendered through the same Session template,
  follows the identical rule.
- Each Subsession item inside a parent detail uses `subsession.source_kind`, so a
  company child renders `CC` even though its provider kind is `codex`.
- The lazy Subsession template consumes the same macro signature and source-key
  class contract; its current runtime remains Claude-only.
- Visible configured source labels and accessible names remain unchanged.
- Routes, query projections, source scope, conversation, parent/child links, pin,
  and Session data remain unchanged.

## Out-Of-Scope Behavior

- Source indicator changes outside Session inventory/detail surfaces.
- Detail layout, visible label, navigation, conversation, or data-contract changes.

## Contract Surfaces

- `source_cue(source_kind, provider_kind, display_label)` in all Session templates
- `.session-source` source-key class selection for detail headings and child rows
- positive company primary/child rendered detail fixtures
- Design Constitution and Session owner-doc cue wording

## Acceptance Mapping

- Company primary detail → `session-source large codex-company` plus visible `CC`.
- Company normalized child detail → the same company class and `CC`.
- Company child in parent detail → `session-source codex-company` plus `CC`.
- Accessibility and visible provenance → configured `Codex Company` remains in
  `sr-only` and visible heading/child metadata.
- Regression preservation → Session detail, conversation, parent/child, source
  scope, pin, full suite, privacy, and diff checks pass.

## Evaluation Focus

- Stable source key must win over shared provider kind in every affected template.
- No remaining detail macro call or source class may derive company identity only
  from `provider_kind`.
- Existing geometry and visible provenance must remain unchanged.

## Open Blockers

- None.
