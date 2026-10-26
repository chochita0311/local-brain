# SPEC-0129: 사용자 세션 소스와 수집 소유 계약

## Metadata
- Status: `approved`
- Parent Feature: [FEAT-0129](../feature/feat-0129-session-source-lifecycle-contract.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-167-session-source-lifecycle-contract](../run/run-20261018-167-session-source-lifecycle-contract.md)
- Execution Profile: `foundation-contract`
- Created: `2026-10-18`

## Implementation And Contract
The corresponding section of [Desktop App And Common Local Settings](../../policies/project/desktop-app-and-settings.md) fixes the field ownership, predicates and failure semantics for this Feature. Its parent acceptance clauses map directly to that section. Implement common helpers without introducing UI work into this foundation boundary.

The initial generalized-profile follow-up retained an internal string namespace.
The owner's later [PK-only correction](spec-0133-user-managed-source-settings.md#source-primary-key-only--2026-10-24)
supersedes that choice: version-2 configuration and runtime use the existing
numeric `sources.id` alone. One-time migration may read old keys, while retained
Source/Session/Event/Usage PKs, frozen attribution and provenance survive. No
replacement string identifier or alias store is introduced.

## Scope And Regression
Preserve legacy stores, source IDs, frozen Usage attribution and originals. No downloads, relocation, external writes or unrelated learning changes. Unknown/newer config must never be replaced as though it were empty.

## Evaluation Focus
Contract review of all field values, saved/effective precedence, explicit lifecycle branches and downstream ownership. Runtime checks are reported separately from contract acceptance.

## Open Blockers
No unresolved product choice for this foundation contract. Its acceptance did
not include product runtime execution. Later scoped runtime results and remaining
native/recipient checks are owned by [EVAL-0139](../evaluation/eval-0139-functional-standalone-test-app.md);
a foundation pass does not close those checks.
