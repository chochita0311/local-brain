# FEAT-0002: Semantic UI Token Foundation

## Metadata

- ID: `feat-0002`
- Status: `passed`
- Type: `foundation`
- Surface: `frontend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `design`, `functional`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Establish one implementation token invariant for LocalBrain so every downstream screen Feature consumes the same primitive, semantic, type, spacing, shape, elevation, motion, shell, status, and provenance roles.

## Acceptance Contract

- The shared stylesheet implements the Design Constitution's primitive and semantic token layers without changing their ownership.
- Foundational canvas, typography, focus, action, control, surface, status, disabled, and reduced-motion selectors consume semantic roles only.
- Provenance roles from `feat-0001` are available to downstream source components.
- Existing pages remain renderable while screen-family Features migrate their local selectors.
- A downstream spec can name a semantic role without choosing a raw design value or private breakpoint.

## Scope Boundary

- In:
  - shared primitive and semantic token definitions
  - base document typography and canvas roles
  - shared focus, action, control, surface, status, disabled, and reduced-motion foundations
  - removal or containment of legacy aliases inside this foundation boundary
- Out:
  - screen-family template redesign
  - route-specific layout migration
  - new product states or components
  - backend, schema, route, or API changes

## Contract Surfaces

- `src/localbrain/static/styles.css` token and foundational selector boundary
- Design Constitution Sections 5, 6, 8, 9, 11, 12, and 13
- CSS custom-property producer and consumer naming

## Required Evaluators

- `contract`: verify primitive-to-semantic ownership and downstream readiness.
- `design`: verify the foundation expresses the approved design language without foreign values.
- `functional`: smoke-check that current routes and controls remain usable after the shared CSS change.

## User-Visible Outcome

- Current pages retain their usable structure while shared base text, focus, control, disabled, status, and motion behavior begin from one consistent system.

## Entry And Exit

- Entry point: the shared stylesheet loaded by every current route.
- Exit behavior: `feat-0003` and all screen-family Features can migrate selectors against a stable semantic layer.

## State Expectations

- Default: canvas, typography, surfaces, and controls resolve through semantic roles.
- Loading: shared working treatment is available but remains bounded to the owning region.
- Empty: shared neutral empty-state roles are available.
- Error: shared danger, validation, and focus treatment remain distinct.
- Success: shared success treatment remains distinct from brand and provenance.

## Dependencies

- `feat-0001` must be `passed` before provenance roles are implemented.

## Likely Affected Surfaces

- `src/localbrain/static/styles.css`
- `docs/policies/design/design-constitution.md` only if implementation reveals an approved contract correction
- focused stylesheet or rendering tests if the active Spec requires them

## Pass Or Fail Checks

- Pass if every token in the implemented foundation has one documented owner and valid reference closure.
- Pass if foundational component selectors use semantic roles rather than primitive or raw values.
- Pass if focus, disabled, feedback, and reduced-motion foundations are independently visible and labeled where required.
- Pass if all current GET routes still render and essential controls remain operable.
- Fail if screen-local exceptions or private breakpoints enter the foundation.
- Fail if semantic roles silently change product-state meaning.

## Regression Surfaces

- every route that loads `styles.css`
- current form controls, buttons, links, status labels, and technical text
- existing `920px`, `700px`, and `320px` responsive boundaries

## Harness Trace

- Active spec doc: [spec-0002-semantic-ui-token-foundation](../spec/spec-0002-semantic-ui-token-foundation.md)
- Active run: [run-20260716-02-semantic-ui-token-foundation](../run/run-20260716-02-semantic-ui-token-foundation.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [eval-0002-functional-token-foundation](../evaluation/eval-0002-functional-token-foundation.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft separated the token invariant from screen-family renewal so downstream features do not redefine shared roles.
- `2026-07-16`: human-approved boundary executed and passed in `run-20260716-02`.
