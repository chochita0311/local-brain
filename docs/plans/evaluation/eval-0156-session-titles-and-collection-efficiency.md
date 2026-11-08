# Session Titles And Collection Efficiency Evaluation

- Status: `complete`
- Result: `PASS`
- Evidence Coverage: complete for the approved source, synthetic browser and
  Python-wheel boundary; installed-native and physical IME acceptance excluded.
- Feature: [FEAT-0163](../feature/feat-0163-session-display-titles.md), [FEAT-0164](../feature/feat-0164-sync-and-index-efficiency.md)
- Specs: [SPEC-0163](../spec/spec-0163-session-display-titles.md),
  [SPEC-0164](../spec/spec-0164-sync-and-index-efficiency.md)
- Runs: [RUN-239](../run/run-20261107-239-sync-and-index-efficiency.md),
  [RUN-240](../run/run-20261107-240-session-display-titles.md), attempt 1
- Evaluators: primary contract, functional, design and interaction; same author,
  no independent implementation review or human acceptance claim.
- Date: `2026-11-07`

## Contract And Functional Evidence

Fresh and upgraded Session tables place nullable `display_title` immediately
after source-owned `title`. Upgrades preserve IDs, child links, events, pins,
Usage snapshots and explicit indexes. Missing and previously appended columns
converge; existing overrides survive. A verified backup precedes the rebuild.
Unknown columns, triggers or constraints are refused; a copy failure restores
the table, indexes, rows and FK setting. Repeated startup does not rebuild it.
The schema at the running installation was inspected read-only: its 21-column
shape is admitted, with zero foreign-key errors. No runtime DB was migrated.

Local title writes validate primary-work eligibility, length, single-line input,
same-origin and bounded form payloads. They update only `display_title`; blank
stores SQL NULL. Source reprocessing and forced synchronization preserve it.
Pins and Chart use the override, while source-backed search text stays owned by
the source. Subsessions have read-only titles and retain parent orientation.

Focused regression coverage is in `test_session_titles.py`,
`test_collection_efficiency.py` and `test_session_sync.py`, alongside the existing
migration, retention, source-revision, attribution, Context cancellation and
natural-search resume/validation suites. The required full suite passed
**1,550 tests**. JavaScript syntax and required privacy/schema/catalog checks
also pass. The wheel includes the new mutation module, script, template, nullable
schema column and schema presentation.

## Efficiency Comparison

All comparisons below use synthetic sources and the same retained inputs; they
do not predict model inference time or real-corpus wall-clock speedups.

| Operation | Before | After | Preserved evidence |
|---|---|---|---|
| Changed-parent preparation with 177 existing fragments, encoder batch 16 | 354 vector SELECTs | 15 vector SELECTs | identical parent, fragment, vector-blob and term rows; 177 reused, 0 encoded |
| Tree with 100 excluded dependency subdirectories and 10 retained Markdown files | 204 directory reads | 1 directory read | exactly the same sorted 10 retained paths |
| File-change metadata check for 32 unchanged native files | one lookup per path plus the existing snapshot | one snapshot | no reparse; Session/Event/Usage rows unchanged; forced sync keeps the override |
| New Usage attribution for 30 records in one store call | one workspace lookup per new record | 1 lookup | distinct per-record times; later call observes changed Git metadata; prior facts and prices remain frozen |

Per-Session reference/evidence freshness checks retain their existing queries;
this is not a claim that all synchronization SQL is constant. Backfills now
match only NULL `updated_at` fields, preserving their required repair values.
They may still scan a table; populated rows are no longer UPDATE targets.

## Design And Interaction Evidence

screen-alignment mode `extend` uses the existing constitution and rendered
Session inventory, not a foreign visual target. A captured 500px pre-change row
had height 169.24px; its normal and editing states retain that height. Long-title
checks at 320px emulation and 700/920/1440px retain normal/editing row geometry,
containment and pin hit targets without document overflow. Existing 34px narrow
and 38px wide provider cues remain. Title controls are outside destination links.

Observed browser transitions cover pointer and keyboard activation, actual Enter
key saving, Escape cancellation, blur saving, clearing to source, reload
persistence, pending edit exclusion, injected 503 failure and successful retry.
Composition events verify the IME guard; physical OS composition is unverified.
Page 2 with source/workspace filters keeps URL, scroll and row order while
updating matching pinned labels. Pin hit targets and child disclosure remain
independent. Detail updates its document title; child detail keeps its parent
alias and has no editor. A script-disabled same-origin frame opens and submits
the native title form, returns with the same scope and confirms persistence.

Narrow rendering initially exposed a shifted pin containing block; retaining the
existing row containing block fixed it, and hit tests then passed at 320/700px.
Initial full-suite failures for a raw radius and the asset-version expectation
were fixed before the final full pass. No unresolved failure remains in scope.

The first isolated server omitted application lifespan, so shared Sync-status
polls returned fixture-only initialization errors. A final normal-startup run
with automatic collection disabled returned HTTP 200 for that status endpoint
and confirmed title save/clear with the same page/source/workspace scope.

## Delivery And Remaining Candidates

Source and Python package are verified; the installed native app was not rebuilt
or replaced. Parent PRD release/recipient gates and human acceptance remain at
their existing owners. Learning, Workstreams, Auto Work and Workflow optimizations
remain parked. Keyword source batching, lazy document-body loading, Chart's
undated-time fallback batching, Usage aggregation and Atlassian detail narrowing
remain proposals, not changes delivered by these Runs.

## Later Session Closeout

The original Run results above retain their November7 scope. The November8
[closeout evaluation](eval-0157-reading-query-efficiency-and-title-caret.md#session-closeout-review--2026-11-08)
records later independent documentation/code reviews, bounded traversal/workspace/
popup repairs, the final1,556-test pass and32-file wheel verification. Native
replacement, physical input and human acceptance remain separate.
