# SPEC-0064: Shared Native Select Disclosure Geometry

## Metadata

- ID: `spec-0064`
- Status: `approved`
- Run ID: `run-20260727-69`
- Attempt: `1`
- Parent Feature: [feat-0064-shared-native-select-disclosure-geometry](../feature/feat-0064-shared-native-select-disclosure-geometry.md)
- Parent PRD: [prd-0011-shared-native-select-control-geometry](../prd/prd-0011-shared-native-select-control-geometry.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: shared native-select primitive and current consumers
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-27`
- Updated: `2026-08-02`

## Source Set

- Human request: use one intentional arrow clearance for every dropdown of the
  same native-select type, including Atlassian and Workstream.
- Parent Feature and PRD.
- Golden sources: current LocalBrain form controls and the Design Constitution.
- Relevant contracts: Design Constitution, Design Evaluation, and Interaction
  Evaluation.

## Implementation Goal

- Establish one select-specific disclosure inset, indicator size, and
  trailing-text reserve without replacing native select behavior.

## In-Scope Behavior

- Define shared semantic geometry in `styles.css`.
- Apply one `select:not([multiple])` rule to every current native select.
- Verify Atlassian, Workstream, and Search consumers at desktop and narrow
  touch widths, including disabled and focused controls.

## Out-Of-Scope Behavior

- Custom menus, comboboxes, option changes, form-flow changes, and a broad
  control-system redesign.

## Affected Surfaces

- `src/localbrain/static/styles.css`
- Atlassian, Workstream, and Search templates containing native selects.
- `tests/test_ui_contract.py`

## State And Interaction Contract

- Native semantics, keyboard focus, disabled state, validation, submission, and
  no-script behavior remain intact.
- The indicator stays vertically centered at one right inset and selected text
  owns a separate trailing reserve at every supported width.

## Data And Contract Assumptions

- No schema, route payload, option value, or persisted state changes.
- The shared stylesheet is the sole geometry owner.

## Required Evaluators

- Contract: not required because no data or integration contract changes.
- Design: compare rendered geometry and containment across named consumers.
- Functional: confirm shared consumer coverage and native behavior regression.
- UX heuristic: confirm arrow discoverability and text clearance.

## Acceptance Mapping

- Shared geometry: three semantic variables and one global native-select rule.
- Consumer coverage: Atlassian, Workstream, and Search rendered and static
  inventory checks.
- Responsive and state coverage: desktop, `320px` touch, focused, and disabled
  controls.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-27`: approved and executed after FEAT-0063 cleared the sequential dependency; RUN-20260727-69 passed.
- `2026-08-02`: normalized the Spec status to `approved`; RUN-20260727-69 and FEAT-0064 retain the successful execution outcome.
