# SPEC-0161: App Navigation History

## Metadata

- ID: `spec-0161`
- Status: `approved`
- Run: [Run237](../run/run-20261106-237-app-navigation-history.md)
- Attempt: `1`
- Parent Feature: [FEAT-0161](../feature/feat-0161-app-navigation-history.md)
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`

## Implementation Contract

One shared JS owner manages an opaque entry marker merged into existing native
history state, bounded 50 session metadata and native Back traversal. Only marked
app pages and their explicit partial-page pushes join the chain. Shared control
initially disabled; reload and replace retain identity, Back/Forward adopt saved
identity, branch navigation truncates future, oldest retained point disables.
First startup/deep link cannot exit to a handshake or external page. Private
storage denial must not break existing navigation; unknown predecessor disables
Back. No new backend routes/schema or complete page snapshots are needed.

Per-feature producers retain their URL/selection responsibilities and report
pending/settled partial renders. Capture outgoing scroll before replacement and
restore incoming state after its DOM is ready; abort abandoned GET work on
pagehide. Keep Chart's global visibility preferences separate from entry camera.
Use existing tokens and 320px floor, retain search and body h1, rename Docs rail
label only. Preserve distinct parent/list/search-return destinations.

## Acceptance

Actual multi-document and AJAX routes in order, including reverse traversal,
forward/branch, reload, 50-point boundary, direct entry, storage denial, async
interruption, source/filters/selected document/window+pane scroll, Chart selection,
keyboard disabled/available control and 320/700/920/1440 layout. Full relevant
suite/privacy, independent challenge, source identity and final frozen/native
checks. Temporary build staging is private; final output is normal canonical dist.
