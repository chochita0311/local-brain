# SPEC-0001: Source Provenance Design Contract

## Metadata

- ID: `spec-0001`
- Status: `approved`
- Run ID: `run-20260716-01`
- Attempt: `1`
- Parent Feature: [feat-0001-source-provenance-design-contract](../feature/feat-0001-source-provenance-design-contract.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Surface Lane: none
- Required Evaluators: `contract`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Parent Feature and PRD
- Design Constitution and Design Document Governance
- Current Claude and Codex source treatments in `src/localbrain/static/styles.css`

## Implementation Goal

- Define accessible Claude and Codex semantic provenance roles without reusing status meaning.

## In-Scope Behavior

- Add provenance primitives, semantic surface, text, and border roles.
- Define an explicit neutral fallback for other or unknown sources.
- State that provenance cannot communicate status, selection, confidence, or priority.
- Record the durable constitution change in governance.

## Out-Of-Scope Behavior

- Runtime CSS and template migration.
- New source types or state changes.

## Affected Surfaces

- `docs/policies/design/design-constitution.md`
- `docs/policies/design/design-document-governance.md`

## State And Interaction Contract

- Source identity always retains readable text.
- Product state remains independently labeled when shown with provenance.

## Data And Contract Assumptions

- Claude and Codex remain current implementation source kinds.
- Other source kinds use the neutral fallback until durable roles are approved.

## Contract Surfaces

- Producer expectations: the Constitution owns provenance roles.
- Consumer expectations: components consume provenance semantics without inferring status.
- Generated artifacts: none.
- Source-of-truth owner: Design Constitution.
- Stale-assumption check: current source selectors are migrated by `feat-0002` and later product Features.

## Required Evaluators

- Contract: required.
- Design: not required for this contract-only run.
- Functional: not required.
- UX heuristic: not required.

## Acceptance Mapping

- Dedicated roles and neutral fallback satisfy the Feature contract.
- Text labels and semantic separation satisfy non-color and status-collision requirements.
- Governance v4 entry satisfies durable-change traceability.

## Evaluation Focus

- Ownership, reference closure, contrast, fallback, and status separation.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved for run `run-20260716-01`.
