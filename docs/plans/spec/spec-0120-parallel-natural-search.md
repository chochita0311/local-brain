# SPEC-0120: Parallel Natural Search

## Metadata

- ID: `spec-0120`
- Status: `approved`
- Run: [RUN-157](../run/run-20261012-157-parallel-natural-search.md)
- Attempt: 1
- Feature: [FEAT-0120](../feature/feat-0120-parallel-natural-search.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-12`

## Goal And Authority

Expose the approved local search engine beside the existing keyword search.
Use the Design Constitution and existing Search/detail families; screen-alignment
mode is `extend`. The rendered old Search screen is the visual baseline.
The FEAT-0119 engine contract has passed; empirical quality remains FEAT-0121.

## Surface Lanes And Ownership

1. Service → explicit activation/status, conservative query filters, current-source evidence.
2. main.py routes → GET `/natural-search`, local POST preparation/cancellation, bounded status JSON and evidence reader.
3. base/results/read templates → new input on the left of the preserved old input; source-parent results with excerpts and original links, query/page return anchors.
4. styles/script → native semantic tokens, status-only progressive updates, native GET forms and keyboard/IME submission.
5. tests/browser → routes, error/empty/partial states, original/back continuity, 320/700/920/1440px, keyboard, escaping and existing search.

## Behavior Contract

- Separate accessible natural/keyword input labels; same old `/search` behavior and Search link. Preserve the existing Atlassian header exception. Narrow widths keep both inputs in reading order without overflow.
- No setup/model download on GET. First activation requires the local preparation action; installed verified assets only. Missing runtime/assets get installation guidance. A running enabled app resumes automatic Sync refresh.
- Disabled, missing-model, preparing, partial, failed/interrupted, ready, no-data and no-match have distinct text and recovery. Progress updates only the status region, preserving entered text, focus and results. No full-page automatic refresh.
- Search applies explicit conditions and displays applied labels/unapplied ambiguity. Ranking score is not displayed as a probability; no threshold settings UI.
- Group by original parent, with at most three evidence links. Session links use stable event anchors; document evidence validates generation and current body before showing the exact escaped span and normalized-body line range. Changed evidence offers re-search, never stale private text.
- Back links are validated same-app natural-search URLs, preserving query/page and result anchor; no open redirect. Browser history stays native.
- Query bodies are not saved in app logs. Bounded GET inputs (300 characters), existing local request checks and bounded form parsing protect action boundaries. Only synthetic data appears in tracked evidence.

## Acceptance And Failure Checks

Route fixtures cover all states, escaped input, return validation, local-only actions
and original search regression. Real browser checks cover rendered containment,
native family consistency, reachable controls, Enter/IME composition, prepare/status
transition, result→Session/document→results continuity and back/forward. No test
claims model accuracy; actual Qwen/Laya measurements are separate.

## Open Blockers

None within the approved boundary. Existing runtime requires restart after Python
route changes; templates alone must not be treated as a completed deployment.
