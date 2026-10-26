# SPEC-0128: 공통 로컬 설정 계약

## Metadata
- Status: `approved`
- Parent Feature: [FEAT-0128](../feature/feat-0128-local-settings-contract.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-166-local-settings-contract](../run/run-20261018-166-local-settings-contract.md)
- Execution Profile: `foundation-contract`
- Created: `2026-10-18`

## Implementation And Contract
The corresponding section of [Desktop App And Common Local Settings](../../policies/project/desktop-app-and-settings.md) fixes the field ownership, predicates and failure semantics for this Feature. Its parent acceptance clauses map directly to that section. Implement common helpers without introducing UI work into this foundation boundary.

## Scope And Regression
Preserve legacy stores, source IDs, frozen Usage attribution and originals. No downloads, relocation, external writes or unrelated learning changes. Unknown/newer config must never be replaced as though it were empty.

## Evaluation Focus
Contract review of all field values, file values and missing-field defaults, explicit lifecycle branches and downstream ownership. Runtime checks are reported separately from contract acceptance.

## First-Startup Persistence — 2026-10-19

The owner confirmed that a new installation must run with defaults and create its
local settings file automatically. The existing shared application lifecycle owns
creation before serving app/web requests; the read helper itself stays read-only.
Verify fresh creation, private permissions, restart preservation, saved-value
precedence and preservation of partial/malformed/future files. No UI or runtime
behavior change is required when those existing paths satisfy the contract.

## Open Blockers
No unresolved product choice for this foundation contract. Its acceptance did
not include product runtime execution. Later scoped runtime results and remaining
native/recipient checks are owned by [EVAL-0139](../evaluation/eval-0139-functional-standalone-test-app.md);
a foundation pass does not close those checks.
