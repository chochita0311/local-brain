# SPEC-0115: Molecules

## Metadata

- ID: `spec-0115`
- Status: `approved`
- Run: [run-20261012-152](../run/run-20261012-152-search-molecule-contract.md)
- Attempt: 1
- Parent Feature: [FEAT-0115](../feature/feat-0115-search-molecule-contract.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Execution Profile: `foundation-contract`
- Surface: contract
- Required Evaluators: contract
- Created: `2026-10-12`

## Implementation Goal And Acceptance Mapping

Fix the molecules contract in [Natural Language Search](../../policies/project/natural-language-search.md#searchable-material-and-indexed-fragments). Its **Searchable Material And Indexed Fragments** section maps each feature guarantee to explicit actors, inputs, boundaries, failure states and downstream responsibilities. Other sections remain separately owned foundations.

## Contract Surfaces

- Producer: source normalization/model/index or evaluation preparation as named in the owner section.
- Consumer: FEAT-0119–0121 implementations.
- Owner: the named section; neither derived vectors nor reports replace original source authority.
- Out: executable model trials, runtime changes, UI implementation and external publication.

## Evaluation Focus

Check every feature guarantee against its owner paragraph, fixed predicates and failure semantics. Explicitly distinguish proposed empirical settings from product invariants. Check linked parent/dependent boundaries for stale assumptions.

## Open Blockers

None for this contract. Empirical results remain the responsibility of FEAT-0121; they are not claimed here.
