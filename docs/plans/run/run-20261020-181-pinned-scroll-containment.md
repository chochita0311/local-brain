# run-20261020-181-pinned-scroll-containment

## Metadata

- Status: `passed`
- Feature: [FEAT-0084](../feature/feat-0084-project-grouped-pinned-sessions.md)
- Active Spec: [SPEC-0084](../spec/spec-0084-project-grouped-pinned-sessions.md#pinned-scroll-containment-correction--2026-10-20)
- Execution Profile: `frontend-product`
- Surface Lane: Pinned Sessions scroll containment
- Required evaluations: Functional, Design, Interaction

## Approved Boundary

Repair the owner-reported blank space below the Sessions list. Primary owns
implementation and evaluation; screen-alignment `extend`, no delegation. The
existing authorization includes related tests and browser/app execution. Preserve
pin membership, accessibility, query/state ownership, tokens, layout and controls.

## Reproduction And Cause

The running app's Sessions document exceeded its visible layout by 749px at
1280×800. A synthetic 47-pin frozen fixture reproduced a document height of
4,148px against a 2,226px shell. The scroller's absolutely positioned `.sr-only`
source labels had no positioned ancestor inside its clipping boundary. Adding
`position: relative` to `.pinned-session-list` reduced the document to 2,226px;
removing it restored 4,148px. Repeated end-scroll measurements remained stable:
this is overflow from hidden labels, not incremental Session loading.

## Verification Plan

Check focused pin, inventory and UI tests; render empty, short and overflowing
panels with short/long main content, including 1280/920/700/320 widths. Verify
document bounds, last-row access, pagination, pin/unpin refresh, narrow reflow,
settings and Session/Project switching. Compare synthetic captures. Refresh the
app assets, signature, ZIP and checksum; restart the actual app and check its
served CSS, scroll bounds and unchanged saved settings. Clean task-owned artifacts.

## Results

Scoped Functional/Design/Interaction PASS. The [functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#pinned-scroll-containment-delivery--2026-10-20-superseded-artifact)
and [design/interaction receipt](../evaluation/eval-0139-design-standalone-test-app.md#pinned-scroll-containment--2026-10-20)
own the complete matrix, exploratory limitations and that Run's artifact identity.
The [portable metadata repair](run-20261020-182-portable-python-build-metadata.md)
supersedes its delivered app/ZIP while retaining this scroll-correction evidence.

69 focused tests and 138 targeted checks across nine web/frozen WebKit cases
passed. Seven first-page cases verify pin refresh/scroll/focus; fourth-page cases
verify layout and non-mutation controls only after exploratory pin/navigation
probes timed out. No broader paginated-pin continuity claim is made.

The actual app was replaced and reopened. Its backend's document height now
equals the 2,226px shell rather than 2,975px; repeated end scrolling is bounded.
Served CSS matches source, saved settings/source-registry hashes are unchanged,
and app/ZIP/extracted signature and archive checks passed. Only the CSS asset
changed; the backend executable is unchanged. No model download or publication.

## Completion Checks

Privacy passed for 1,417 candidate files. Diff whitespace, catalog freshness and
90 planning links/anchors passed. Final installed signature, ZIP checksum and
source/bundled CSS equality passed. All task-owned probes and synthetic backends
exited. Temporary tools, data, screenshots, staging/extracted builds and recovery
copies were removed after checking active use. The delivered app remains running.
