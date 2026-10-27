# SPEC-0116: Query And Results

## Metadata

- ID: `spec-0116`
- Status: `approved`
- Run: [run-20261012-153](../run/run-20261012-153-natural-search-query-contract.md)
- Attempt: 1
- Parent Feature: [FEAT-0116](../feature/feat-0116-natural-search-query-contract.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Execution Profile: `foundation-contract`
- Surface: contract
- Required Evaluators: contract
- Created: `2026-10-12`

## Implementation Goal And Acceptance Mapping

Fix the query and results contract in [Natural Language Search](../../policies/project/natural-language-search.md#query-and-results). Its **Query And Results** section maps each feature guarantee to explicit actors, inputs, boundaries, failure states and downstream responsibilities. Other sections remain separately owned foundations.

## Contract Surfaces

- Producer: source normalization/model/index or evaluation preparation as named in the owner section.
- Consumer: FEAT-0119–0121 implementations.
- Owner: the named section; neither derived vectors nor reports replace original source authority.
- Out: executable model trials, runtime changes, UI implementation and external publication.

## Evaluation Focus

Check every feature guarantee against its owner paragraph, fixed predicates and failure semantics. Explicitly distinguish proposed empirical settings from product invariants. Check linked parent/dependent boundaries for stale assumptions.

## Open Blockers

None for this contract. Empirical results remain the responsibility of FEAT-0121; they are not claimed here.
