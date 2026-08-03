# SPEC-0068: Multi-Source Session Synchronization And Health

## Metadata

- ID: `spec-0068`
- Status: `approved`
- Run ID: `run-20260802-73`
- Attempt: `1`
- Parent Feature: [feat-0068-multi-source-session-synchronization-and-health](../feature/feat-0068-multi-source-session-synchronization-and-health.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: data/backend → API/integration → frontend → docs
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Source Set

- FEAT-0068, PRD-0012, passed FEAT-0066/0067 contracts.
- Current scanner transactions, sync routes, source inventory, Sessions and
  Sources templates/client behavior.
- Design Constitution, Design Evaluation, Interaction Evaluation, privacy and
  Source/Session/Usage owner docs.

## Implementation Goal

- Dispatch every validated Session source through its provider adapter with one
  independent commit boundary per source, then expose a bounded aggregate and
  source-by-source health result to both sync surfaces.

## Lane Order And Handoffs

1. Data/backend owns persistent latest attempt/success/status/error evidence and
   per-source scanner isolation.
2. API/integration serializes one stable report shape for Session-only and wider
   scans without leaking exceptions or private content.
3. Frontend renders the report and source inventory from that contract while
   preserving no-script execution and current view orientation.
4. Docs reconcile current source, deletion, health, and privacy ownership.

## In-Scope Behavior

- `sources.last_scanned_at` remains latest attempt. Add nullable
  `last_scan_success_at`, `last_scan_status`, and bounded `last_scan_error`.
  Status values are `completed`, `empty`, `unavailable`,
  `configuration_error`, and `scan_failed`.
- Load and reconcile FEAT-0067 settings before dispatch. Each `ready` entry scans
  in its own transaction; unavailable/config-conflict/omitted entries skip scan
  and stale deletion, record truthful health, and retain data.
- Provider map supports Claude and Codex. Both `codex` keys receive the exact
  Codex parser and Usage contract with their own Source ID and root.
- Unexpected source exceptions roll back only that source. A follow-up health
  update records a bounded application-generated failure message.
- File-local failures may commit healthy files but yield `scan_failed`. Empty
  means a readable accepted root finishes with no tracked Session JSONL.
- A successful accepted-root scan keeps current source-scoped disappeared-file
  reconciliation unchanged.
- Report v1 contains `outcome`, aggregate `summary`, and ordered `sources`. Each
  source exposes stable key, label, provider, status, imported, unchanged,
  failed-file, eligible-Session, tracked-file, attempt/success timestamps,
  bounded error code/message, and `retained_data` when synchronization was
  skipped or failed.
- Aggregate is `complete` when every source is completed/empty, `partial` when
  success and attention coexist, and `failed` when no source completes.
- Wider scan appends the current aggregate Context result without weakening the
  independent Session-source transactions.
- Enhanced sync renders a compact aggregate heading and per-source rows. Complete
  success reloads after a short status interval; partial/failed results remain
  inspectable and immediately restore the action.
- The POST fallback redirects with bounded aggregate state and the destination
  scope. The refreshed page shows current persisted per-source health.
- Sources cards show local AI sources independently with provenance label, root,
  health, attempt, success, eligible Session and tracked-file counts, and error
  consequence. Context cards retain their current compatible inventory.

## Out-Of-Scope Behavior

- Sessions source tabs/filter generalization and Session-row provenance
  (FEAT-0069).
- Usage source scope/composition (FEAT-0070).
- Settings editing, source disable/remove/purge/archive/restore or occupied-root
  relocation.
- Parser, token, pricing, Maintenance, or native retention changes.

## State And Interaction Contract

- Loading: one disabled action, `aria-busy`, existing working label, live status.
- Complete: success tone, all source rows truthful, then reload preserving route
  and valid query scope.
- Partial/failed: warning/danger tone, per-source consequence remains, action and
  focus return without reload.
- Repeated action: replaces only its result region, leaves one listener, and
  remains executable.
- No-script: ordinary POST executes the same scan and redirects to the original
  Sessions/Projects scope with aggregate notice.
- Narrow widths: result rows and health metadata stack; path/error wrap inside
  cards; action remains reachable at 320px.

## Contract Surfaces

- scanner provider dispatch and source transaction helper
- persistent Source health fields and compatible additive migration
- sync report serializer consumed by API/CLI/client
- Sessions result DOM and Sources inventory read model/cards
- current-view redirect query and health notice

## Acceptance Mapping

- One action/all sources → settings-ordered dispatch independent of filter.
- Failure isolation → per-source transactions plus caught health update.
- Retained mistakes → no scanner call for unavailable/config states.
- Same parser/distinct ownership → provider map plus two Codex synthetic homes.
- Inspectable outcome → API report, persistent cards, enhanced and fallback copy.
- Source-owned deletion → missing-file test under one unchanged valid root.

## Evaluation Focus

- Cross-source commit/rollback, same external ID, and stale deletion isolation.
- Exact report keys/state derivation and bounded error data.
- Current route/query, button/focus/repeat behavior, no-script result.
- Provenance versus status semantics, long paths/errors, and widths 1440/920/700/320.
- No reads outside provider Session patterns and no private tracked artifacts.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-02`: Orchestrator declared the Fullstack Product profile and four
  ordered lanes. Sessions browsing scope remains intentionally deferred.
