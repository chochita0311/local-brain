# FEAT-0111: Automatic Skill Load Observation

## Metadata

- ID: `feat-0111`
- Status: `passed`
- Type: `product`
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `data`, `backend`, `frontend`, `docs`
- Required Evaluators: `contract`, `functional`, `design`, `ux-heuristic`
- Created: `2026-10-02`
- Updated: `2026-10-03`

## Historical Projection

Continuity, 2026-10-03: the owner returned the displayed load count because inspection reads inflated it. [FEAT-0112](feat-0112-session-skill-use-estimate.md) owns the subsequent estimated-use projection; this completed load-evidence extension remains historical.

The current use/reference Session projection is owned by [FEAT-0113](../feature/feat-0113-skill-reference-session-count.md).

## Goal And Approved Boundary

The owner approved counting automatically read skill instructions after reviewing the difference between a recorded load and actual application. Extend the existing skill ranking with source-backed successful `SKILL.md` reads and describe the result as observed loads. Reading a skill for inspection also qualifies; application, success and benefit are not inferred.

## Acceptance Contract

- Admit existing Claude `Skill` calls and Codex `<skill>` contexts, plus successful literal skill-file reads with native tool-call identity and a returned skill name.
- Recognize Claude `Read` and supported shell read commands, including literal commands nested inside Codex `exec`. Never execute source commands or consult current skill installations to reconstruct history.
- Count a normalized skill once within one identifiable request, including a generated context followed by file reads or repeated partial reads. A later request may count again. With no identifiable request, retain distinct native events rather than guessing a Session-wide application count.
- Preserve individual evidence and old observations. Backfill request identity and new read observations from available files once; missing historical files retain their previous evidence. Repeated scans, append, movement, correction and maintenance exclusion remain safe.
- Keep source arguments, results and skill bodies out of the observation ledger. Unsupported, failed, pending and unidentifiable reads do not become confirmed loads.
- Update Insights terminology, empty states and a short count explanation within its existing layout. The ranking remains independent of Usage & Cost controls.

## Dependencies And Regression Surfaces

- Extends [FEAT-0105](feat-0105-skill-observation-retention.md) and [FEAT-0106](feat-0106-first-session-insights-view.md); their first-release records remain historical.
- Check compatible schema upgrades, native-source sync, Session/Usage preservation, request grouping, maintenance classification and retained counts without source files.
- Check the Insights route in a browser at narrow and desktop widths, with reciprocal navigation and truthful count wording.

## Harness Trace

- Spec: [SPEC-0111](../spec/spec-0111-automatic-skill-load-observation.md)
- Run: [RUN-138](../run/run-20261002-138-automatic-skill-load-observation.md)
- Owner approval: `2026-10-02`, the owner directed implementation after the load-count and deduplication explanation.
- Evaluations: [contract](../evaluation/eval-0111-contract-automatic-skill-load-observation.md), [functional](../evaluation/eval-0111-functional-automatic-skill-load-observation.md), [design](../evaluation/eval-0111-design-automatic-skill-load-observation.md), [UX](../evaluation/eval-0111-ux-automatic-skill-load-observation.md).
