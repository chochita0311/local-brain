# FEAT-0074: Session-Centric Related Materials Rail

## Metadata

- ID: `feat-0074`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0013: Session-Centric Related Context Evidence](../prd/prd-0013-session-centric-related-context-evidence.md)
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Goal

- Replace the flat primary Session Related Context rail with a calm `관련 자료`
  index that presents direct Session evidence first, explicit organization
  context second, and no path-only ambient documents.

## Acceptance Contract

- Persisted primary Session detail labels the rail `관련 자료` and uses exactly
  two eligible groups: `이 세션의 참조` and `연결된 작업`.
- `이 세션의 참조` contains targets mentioned by the viewed primary Session,
  observed through an approved result, or read/attempted through an approved
  resource tool.
- `연결된 작업` contains only eligible Documents or Resources sharing an
  explicit user-managed Thread or Workstream with the Session.
- Same-workspace, same-directory, same-repository, and global recent Documents
  never enter candidates, counts, limits, empty states, or fallback content.
- One target appears once under its strongest group. A direct-reference row may
  expose several bounded evidence labels and counts while retaining secondary
  explicit organization reasons without duplicating the target.
- Evidence labels use `MCP 조회`, `MCP 조회 실패`, `사용자 메시지에서 언급`,
  `Agent 응답에서 언급`, and `도구 결과에서 확인`.
- Any successful matching read presents successful read evidence. Failure-only
  attempts present `MCP 조회 실패` and never imply remote content or freshness.
- Jira identity prefers the Session-observed issue key; Markdown prefers the
  observed file name or relative path; generic URLs prefer a safe bounded
  host/path. Confirmed remote and shared Resource titles remain secondary or
  deterministic fallback, not evidence strength.
- Each group initially displays at most `10` unique targets and always shows its
  total. Additional retained items appear through an explicit keyboard-operable
  `N개 더 보기` disclosure that can be collapsed without losing page
  orientation.
- Direct and organization groups own independent counts and display limits.
  Explicit organization items cannot displace direct Session references.
- A 100-target safety boundary exposes observed total and visible partial copy;
  retained subsets never masquerade as complete.
- Initial ordering is successful reads, failure-only reads, approved tool-result
  observations, then visible mentions; ties follow first normalized source
  occurrence and stable target identity. Explicit organization uses Thread
  before Workstream and stable target ordering.
- Normal rows show concise identity and destination context. Repeated type,
  provenance, and relationship pills disappear when the group or evidence label
  already communicates the same fact. Missing, archived, unsafe, ambiguous,
  stale, and partial states retain explicit text.
- Opening Session detail performs only bounded local reads and no source parse,
  relationship write, external/MCP/model/embedding call, capability inspection,
  scan, or maintenance Run.
- Exact `대화에서 보기` scrolling, highlighting, and occurrence selection is not
  exposed in this Feature.
- Subsession detail has no rail, and primary Session detail does not aggregate
  child evidence.
- The conversation retains established reading width. The rail remains secondary
  at wide widths and enters document flow before the conversation at compact
  widths without forcing a long initial list, horizontal overflow, or focus
  trap.

## Scope Boundary

- In:
  - grouped Related Materials read model and strongest-group deduplication
  - Session-observed identity and evidence summaries
  - successful/failed read and mention presentation
  - explicit Thread/Workstream organization group
  - independent total, initial 10-item display, disclosure, and partial states
  - primary Session route failure isolation
  - responsive, accessible detail rail presentation
  - empty, unavailable, stale, partial, and error states
- Out:
  - same-workspace/path/repository documents
  - recent or inferred context
  - exact conversation navigation
  - Subsession rail or parent roll-up
  - manual ordering or Session-to-context curation
  - remote refresh, Resource title mutation, or external/model work
  - parser, evidence-persistence, or reconciliation scope owned by FEAT-0073

## Surface Lanes

- Read-model lane:
  - path roots: Session reference query, explicit Thread/Workstream projection,
    target loading, deduplication, ordering, limits, and tests
  - dependencies: passed FEAT-0072 and FEAT-0073
  - expected evidence: group eligibility, source-facing identity, evidence labels,
    count/disclosure shape, 100-target partial state, and same-workspace absence
  - evaluator ownership: `contract`, `functional`
- Route lane:
  - path roots: primary Session detail route, failure isolation, and route tests
  - dependencies: read-model lane
  - expected evidence: bounded local read, primary-only scope, no hidden work,
    empty/partial/error behavior
  - evaluator ownership: `contract`, `functional`
- Presentation lane:
  - path roots: Session detail/rail templates, semantic-token styles, optional
    local disclosure enhancement, and UI tests
  - dependencies: route lane and Design Constitution
  - expected evidence: calm hierarchy, reduced repetition, 10-item initial
    display, accessible disclosure, responsive order, containment, and focus
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, architecture, design, interaction, and data-model owner
    docs
  - dependencies: completed read and presentation lanes
  - expected evidence: passed FEAT-0060 behavior revised without erasing its
    historical contract
  - evaluator ownership: `contract`

## Contract Surfaces

- Session reference read projection from FEAT-0073.
- Explicit Thread/Workstream relationship projection.
- Group vocabulary, evidence labels, ordering, deduplication, totals, 10-item
  disclosure, and 100-target partial state.
- Session detail route failure isolation and zero-hidden-I/O boundary.
- Existing target destinations and safe external-link behavior.
- Responsive detail grid, DOM order, disclosure state, and accessibility.

## User-Visible Outcome

- Opening a primary Session shows a concise index of resources that the Session
  actually mentioned, observed, or attempted to read, followed only by explicit
  user-managed organization context, with truthful evidence and no path-only
  document flood.

## Entry And Exit

- Entry point: open a persisted primary Session detail route.
- Exit or transition behavior: open a related target at its existing owned
  destination, expand or collapse additional items, or continue reading the
  Session without losing page orientation.

## State Expectations

- Default: up to 10 direct targets and up to 10 explicit organization targets
  appear in separate groups with totals.
- Expanded: retained additional targets appear in the owning group and can be
  collapsed.
- Empty: no direct or explicit organization evidence is reported; no path/recent
  fallback appears.
- Failure-only: target remains visible with `MCP 조회 실패`.
- Partial/stale: retained evidence remains visible with bounded explanatory copy.
- Error: rail failure remains local and conversation reading continues.
- Narrow: rail follows Session identity/orientation and precedes conversation
  with compact initial groups and matching keyboard/visual order.

## Dependencies

- FEAT-0072 and FEAT-0073 must be `passed` before this Feature enters build.
- FEAT-0060 remains the passed responsive/detail regression baseline.

## Likely Affected Surfaces

- `src/localbrain/session_context.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/session.html`
- `src/localbrain/templates/_session_related_context.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js` only if native disclosure is insufficient
- Session context, detail, route, UI contract, and source-evidence tests
- product, architecture, design, interaction, and data-model owner docs

## Pass Or Fail Checks

- Pass if direct Session evidence and explicit organization are the only groups
  and same-workspace-only Documents never affect any state or count.
- Pass if equivalent Jira references display the same issue-key identity despite
  different shared Resource bootstrap titles.
- Pass if successful reads, failure-only reads, user/assistant mentions, and
  approved tool-result observations present truthfully on one deduplicated row.
- Pass if each group shows at most 10 items initially, exposes total count, and
  reveals retained remainder through an accessible reversible disclosure.
- Pass if a target beyond the 100-target safety boundary yields explicit partial
  copy rather than silent omission.
- Pass if primary/Subsession boundaries, existing destinations, route failure
  isolation, and zero-hidden-I/O behavior remain intact.
- Pass if `1440`, `920`, `700`, and `320` rendered checks preserve readable
  conversation width, calm hierarchy, containment, disclosure operation,
  keyboard order, and focus.
- Fail on ambient path documents, global recency, inferred relevance, repeated
  redundant badges, false remote-read claims, Resource-title mutation, hidden
  I/O, or exact conversation-navigation scope.

## Regression Surfaces

- FEAT-0060 Session Related Context rail responsive and failure behavior.
- FEAT-0043 Session Markdown conversation reading and long-content containment.
- Primary/Subsession detail orientation and source cues.
- Workstream/Thread explicit resource links.
- Local Context and Atlassian target destinations.
- External-link safety, keyboard focus, and repository privacy.

## Harness Trace

- Active spec doc: [SPEC-0074](../spec/spec-0074-session-centric-related-materials-rail.md)
- Active run: [RUN-20260803-84](../run/run-20260803-84-session-centric-related-materials-rail.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [Contract PASS](../evaluation/eval-0074-contract-session-centric-related-materials-rail.md), [Design PASS](../evaluation/eval-0074-design-session-centric-related-materials-rail.md), [Functional PASS](../evaluation/eval-0074-functional-session-centric-related-materials-rail.md), and [UX Heuristic PASS](../evaluation/eval-0074-ux-session-centric-related-materials-rail.md).
- Latest fix note: [FIX-0074](../fix/fix-0074-related-material-evidence-density.md).

## Open Review Decisions

- None inside the proposed boundary. Exact conversation navigation and
  Subsession roll-up remain later planning work.

## Continuity Notes

- `2026-08-03`: initial draft proposed after PRD-0013 approval; execution remains
  blocked on human Feature-boundary review and passed FEAT-0072/0073 dependencies.
- `2026-08-03`: owner approved the Feature boundary. Execution remains queued
  behind passed FEAT-0072 and FEAT-0073 dependencies.
- `2026-08-03`: FEAT-0072 and FEAT-0073 passed. This Feature entered the
  Fullstack Product loop with Contract, Design, Functional, and UX Heuristic
  evaluation.
- `2026-08-03`: Attempt 1 passed all required evaluators after a bounded evidence-
  density fix. The complete PRD-0013 Feature sequence is implemented.
