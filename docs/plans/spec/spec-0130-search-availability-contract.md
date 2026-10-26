# SPEC-0130: 모델 선택 검색 계약

## Metadata
- Status: `approved`
- Parent Feature: [FEAT-0130](../feature/feat-0130-search-availability-contract.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-168-search-availability-contract](../run/run-20261018-168-search-availability-contract.md)
- Execution Profile: `foundation-contract`
- Created: `2026-10-18`

## Implementation And Contract
The corresponding section of [Desktop App And Common Local Settings](../../policies/project/desktop-app-and-settings.md) fixes the field ownership, predicates and failure semantics for this Feature. Its parent acceptance clauses map directly to that section. Implement common helpers without introducing UI work into this foundation boundary.

## Scope And Regression
Preserve legacy stores, source IDs, frozen Usage attribution and originals. No downloads, relocation, external writes or unrelated learning changes. Unknown/newer config must never be replaced as though it were empty.

## Evaluation Focus
Contract review of all field values, saved/effective precedence, explicit lifecycle branches and downstream ownership. Runtime checks are reported separately from contract acceptance.

## Open Blockers
No unresolved product choice for this foundation contract. Its acceptance did
not include product runtime execution. Later scoped runtime results and remaining
native/recipient checks are owned by [EVAL-0139](../evaluation/eval-0139-functional-standalone-test-app.md);
a foundation pass does not close those checks.
