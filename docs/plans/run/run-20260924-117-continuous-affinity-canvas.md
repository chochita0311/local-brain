# RUN-20260924-117: Continuous Affinity Canvas

- ID: `run-20260924-117`
- Status: `passed`
- Feature: [FEAT-0104](../feature/feat-0104-temporal-affinity-flow.md)
- Spec: [SPEC-0104](../spec/spec-0104-temporal-affinity-flow.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `backend`, `frontend`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Attempt: `1`
- Created: `2026-09-24`

Owner review returns the same temporal-flow Feature to its corrected Spec:
arbitrary list-page slices hid off-page affinity and broke continuous observation.
Prior through-UI authorization covers this bounded correction without another
classification/approval queue. The primary owns sequential orchestration,
implementation and semantic review; no delegated worker is required.

Backend lane: separate whole-scope map data from paged text projection, preserve
exact source/freshness/snapshot rules. Run reader contract tests first.
Frontend lane: native bounded scrolling and visible time controls; preserve
camera/list state across selection, list paging, history, source return and resize.
Run synthetic browser checks at 1440/920/700/320 and private-safe live readiness.

Screen-alignment `extend`: the rendered current Explorer has an arbitrary
24-strand boundary, missing horizontal scroll affordance and page-dependent
camera. Correct these structural/data-density issues only; preserve shell,
Search, palette, evidence lens, point meaning and hierarchy. The existing design
plan owns sequencing; constitution clarification owns continuous-canvas law.
No model, migration, organization change, new persistent cache or source write.

Required gates: three-plus text pages, off-page edge witnesses, page-independent
membership/geometry/camera, actual horizontal and vertical scroll, all hierarchy
levels, unknown times, search, exact period evidence, repeat/history/resize,
keyboard/reduced motion, no-script/render failure, privacy and task cleanup.

## Evaluation

- [Contract](../evaluation/eval-0104-contract-temporal-affinity-flow.md),
  [Design](../evaluation/eval-0104-design-temporal-affinity-flow.md),
  [Functional](../evaluation/eval-0104-functional-temporal-affinity-flow.md) and
  [UX](../evaluation/eval-0104-ux-temporal-affinity-flow.md) pass with complete
  evidence for the continuous observation boundary. Human visual preference
  and semantic work continuity are not asserted accepted. No new reusable
  design/interaction rule candidate or user classification task.
- 970 application tests: 967 passed, three unchanged optional semantic skips.
  25 reader tests include three-page scope/edge/evidence conservation and safe
  old-reader/new-template fallback. No model/producer changes require the extras.
- Real Chrome QA passes 1440/920/700/320 with all 65 synthetic groups available,
  horizontal/vertical wheel input, fixed viewport axis, visible time controls,
  page-two/page-three and history camera/geometry/edge stability, period evidence,
  source return, three levels, zoom/pan/fit/reset, keyboard, resize with list
  disclosure retention, rapid selection, search and both executable fallbacks.
  Zero mutation requests or runtime exceptions. A 1,200-Session/257-group probe
  reaches the last row/latest time; unknown-date evidence remains unplaced and
  reachable without false dates or enabled time controls.
- The actual app returns booleans only for current full history, graph equality
  on page three, cross-page affinity, native movement, containment and exact
  period evidence. Python/static asset restart is the supported runtime boundary;
  lifespan startup is disabled so no migration/ingestion is triggered.
- Corrections within this Run: indexed neighbor ordering and incident-edge
  lookup, content-bounded pan, row-aware whole-time fit, native-scrollbar pointer
  ownership and retained list disclosure on resize. QA uses a viewport-aware
  synthetic SVG click helper with waits outside page scripting for no-script
  evidence. Existing grouping, point-size semantics, DB/report files and manual
  organization remain unchanged.
- Owner docs and prior projection assumptions were reconciled. Schema audit
  remains 649 objects (543 keep, 106 defer), without schema or removal changes.
  Repository privacy passes for 1,027 candidate files; diff checks pass.

## Handoff

The running loopback app is the deliverable. Open Auto Work, scroll left/right
through time and up/down through strands. Text list pages do not alter the map.
Only synthetic task-owned servers, fixtures and captures are cleanup targets;
the user-facing app remains running. No source material is a cleanup target.

Cleanup is complete: task-owned synthetic servers and browser tabs are stopped,
and their fixture databases/reports, browser captures/profile and staging script
are removed. The final live app reload confirms current `v2` projection, enhanced
scrollable map and fresh assets. No durable reference depends on a temporary path.
