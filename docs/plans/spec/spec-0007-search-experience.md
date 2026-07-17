# SPEC-0007: Search Experience

## Metadata

- ID: `spec-0007`
- Status: `approved`
- Run ID: `run-20260716-07`
- Attempt: `1`
- Parent Feature: [feat-0007-search-experience](../feature/feat-0007-search-experience.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: shared search entry and Search results
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, `/search?q=` contract, base global search, and current result schema.

## Implementation Goal

- Keep one query-preserving search path with readable result type, provenance, excerpts, destinations, and distinct empty conditions.

## In-Scope Behavior

- Align search controls, results, type/provenance badges, excerpts, counts, empty states, and narrow composition.
- Preserve exact query values and current Session or Document destinations.
- Label Claude and Codex with provenance roles rather than feedback colors.

## Out-Of-Scope Behavior

- Ranking, indexing, parsing, autocomplete, new filters, pagination, or destination changes.

## Affected Surfaces

- `base.html`, `search.html`, and search selectors in `styles.css`.

## State And Interaction Contract

- Blank query invites input; nonblank zero-result state reports no matches.
- Full-row hover is used only where the full row is the existing anchor.

## Acceptance Mapping

- Query retention maps to both search inputs' `q` value.
- Provenance and type separation maps to result badge selectors.
- Long-content containment maps to excerpt clamping, path wrapping, and `320px` responsive rules.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved after provenance and shell contracts passed.
