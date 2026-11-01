# FEAT-0154: Retained Session History

## Metadata

- ID: `feat-0154`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md#session-history-retention--2026-10-31)
- Created: `2026-10-31`
- Authorization: the owner approved the discussed retention/state contract and explicitly requested implementation in this session.

## Goal And Acceptance Contract

1. Missing native files do not delete previously collected Sessions, Activity
   Events, Usage, pins, search evidence or user relationships. Stored detail and
   pin/unpin remain usable without originals. Preserve existing source separation.
2. Existing `source_files` owns independent `PRESENT`, `MISSING`, `UNKNOWN`
   presence observations, their check time and bounded failure reason. Keep
   existing scan `status`/`error` separate. Presence requires one admitted plain
   or compressed representation; absence requires a successful readable-root
   check. Failed/incomplete inspection cannot establish absence.
3. Available evidence is still processed. Missing inputs keep their prior
   parser/normalizer/reference versions and historical facts; forced collection
   and contract repair cannot erase their retained history or claim reprocessing.
   Original-independent reads/calculations continue normally.
4. Reappearing originals update the same source/native Session identity and
   preserve IDs, pins (including edits during absence), frozen prices and Project
   attribution. Plain/Zstd precedence and unchanged repeat skipping remain intact.
5. List/detail show original availability separately from Project path state.
   Use existing design/value-label facilities. Normal read routes do not inspect
   provider files to determine presence.

## Scope Boundary

Session capture, storage compatibility, availability read models, bounded visible
state and owner documentation are in scope. Provider originals remain read-only.
No new deletion UI, automatic expiry, raw-transcript backup, Local Context
lifecycle change, external call, native distribution or unrelated feature change.
Existing confirmed-empty/provider-internal eligibility corrections remain
separate from missing-file preservation.

## Surface Lanes And Verification

- Contract/data: additive compatible fields, enum registry, revision admission
  and Session lifecycle; primary contract evaluator.
- Backend: capture, Usage repair, references, source failure handling and reads;
  synthetic missing/unknown/return/multifile/force/version/rollback regression.
- Frontend: existing Sessions list, pinned recall and detail availability labels;
  actual browser missing/unknown/present, pin actions and wide/narrow inspection.
- Docs: canonical ingestion, Sessions, Usage, schema and in-app owners; generated
  artifacts, privacy/link checks. Required full repository suite follows focused
  checks. Evaluations are primary-agent observations, not independent review.

## Trace

- Spec: [SPEC-0154](../spec/spec-0154-retained-session-history.md)
- Run: [RUN-229](../run/run-20261031-229-retained-session-history.md)
- Prior correction: [RUN-228](../run/run-20261031-228-session-dashboard-cost-and-history.md)
- Evaluation: [EVAL-0154](../evaluation/eval-0154-retained-session-history.md); same-author bounded PASS, separate from human acceptance.
