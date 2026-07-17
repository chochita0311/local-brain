# SPEC-0002: Semantic UI Token Foundation

## Metadata

- ID: `spec-0002`
- Status: `approved`
- Run ID: `run-20260716-02`
- Attempt: `1`
- Parent Feature: [feat-0002-semantic-ui-token-foundation](../feature/feat-0002-semantic-ui-token-foundation.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `foundation-contract`
- Surface Lane: shared CSS and interaction foundation
- Required Evaluators: `contract`, `design`, `functional`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Approved Feature and PRD, Design Constitution, provenance contract from `feat-0001`, and the current shared stylesheet.

## Implementation Goal

- Replace the legacy flat aliases with a closed primitive-to-semantic token layer and migrate shared component consumers without changing product behavior.

## In-Scope Behavior

- Implement color, type, spacing, shape, elevation, motion, shell, feedback, and provenance tokens.
- Use semantic roles for all component colors; add focus, disabled, reduced-motion, and bounded feedback foundations.
- Preserve current routes, fields, API payloads, reloads, and destructive confirmations.

## Out-Of-Scope Behavior

- Backend or schema changes, new components, route-specific product capabilities, and new breakpoints.

## Affected Surfaces

- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- `tests/test_ui_contract.py`

## State And Interaction Contract

- Brand, selection, provenance, info, success, warning, and danger remain separate.
- Disabled controls are explicit; focus is keyboard-visible; reduced motion resolves transitions to zero duration.

## Contract Surfaces

- Producer: the Design Constitution and `:root` token layer.
- Consumers: all shared and route-family CSS selectors.
- Source-of-truth owner: Design Constitution for values; stylesheet for implementation.
- Stale-assumption check: the implementation keeps the documented `220/188`, `920/700`, and `320` geometry.

## Acceptance Mapping

- Token closure and raw-color containment map to the stylesheet root and UI contract test.
- Shared focus, disabled, status, provenance, and reduced-motion behavior map to foundational selectors.
- Route renderability maps to unit and local HTTP smoke verification.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved for the second sequential PRD run.
