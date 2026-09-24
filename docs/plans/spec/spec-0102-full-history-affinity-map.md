# SPEC-0102: Full-History Affinity Map

## Metadata

- ID: `spec-0102`
- Status: `superseded`
- Feature: [FEAT-0102](../feature/feat-0102-full-history-affinity-map.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Run: [RUN-115](../run/run-20260923-115-full-history-affinity-map.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `backend`, `frontend`
- Attempt: `1`
- Created: `2026-09-23`

## Route And Contract

`2026-09-24`: [SPEC-0104](spec-0104-temporal-affinity-flow.md) supersedes the
freeform geometry after owner review requested temporal flow. The following is
the historical RUN-115 contract, not current presentation law.

FEAT-0101 passed before this build. `/auto-work` now defaults to its full-history
consumer, while `mode=sample` explicitly retains the earlier comparator and its
own preparation action. Sample links/redirects preserve that mode. No map GET or
interaction calls the model, ingests, changes organization or starts preparation.
Loopback/same-origin protections and private/no-store responses remain unchanged.

## Design Consistency List — Extend Mode

Current sampled Auto Work and rendered Session Workflow Focus were inspected.
Preserve sidebar position, shell/header geometry and global Search literally.
Use the neutral native Explorer canvas, existing red selection and type/spacing/
control tokens; do not introduce a dark space theme, gradients or a new library.
Make group-first observation the primary region and exact evidence its adjacent
Trace. Counts/coverage belong in a compact disclosure, not a wall of warnings.
Long Korean/English labels wrap in the complete list and inspector. Narrow views
stack regions with normal page scroll; the graph never becomes the only path.

## Interaction And Rendering

- Native paginated lists and source links are server-rendered. The map is an
  optional SVG enhancement with deterministic settled positions; selection does
  not relayout nodes. A separate expand action moves down one scope. Breadcrumbs
  and snapshot URLs retain orientation. Source labels are representative, not
  invented category names. Observed first/last dates do not imply lifecycle.
- Undirected similarity lines only; circle size encodes occurrence count. A
  bounded default edge display discloses shown/available counts and offers all
  visible-scope edges. No arrow, branch/merge, completion or confidence claim.
- Visible zoom, fit/reset, keyboard pan and pointer drag controls. Ctrl/Meta-wheel
  zoom is anchored under the pointer; ordinary wheel scrolls the document. Touch
  page scrolling remains possible. No perpetual physics or required editing.
- Native navigation is the fallback. Optional same-route partial navigation uses
  cancellation/generation ownership, atomic root replacement and one delegated
  handler set. Keep graph transform for same-scope selection and evidence pages;
  history state stores only viewport/Trace coordinates and edge visibility,
  never private evidence. Back/
  forward and source-return restore valid selection/transform. Network or render
  failure leaves an operable textual path. No persistent browser storage.
- No-script has complete paginated lists, hierarchy expansion, evidence and
  source return. Reduced motion has no layout animation. Missing/busy/stale/
  expired/invalid/empty states use the mapped native semantic families.

## Verification And Open Blockers

No open boundary blockers. Contract, Design, Functional and UX must pass using
the running app and loaded assets at 1440/920/700/320. Exercise long labels,
selection/expansion/source-return, history, fast/repeated clicks, fit/reset,
keyboard/pointer ownership, reduced motion, no script and rendering failure.
Use synthetic screenshots; actual local handoff checks return only booleans.
This increment does not pass semantic grouping or replace Workstream identity.
