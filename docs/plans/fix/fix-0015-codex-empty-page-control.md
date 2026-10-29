# FIX-0015: Codex Empty Page Control

## Metadata

- ID: `fix-0015-codex-empty-page-control`
- Status: `complete`
- Run: [RUN-227](../run/run-20261029-227-codex-empty-page-control.md)
- Attempt: `1`
- Feature: [FEAT-0015](../feature/feat-0015-session-subsession-source-contract.md)
- Spec: [SPEC-0015 R2](../spec/spec-0015-r2-codex-empty-page-control.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: data normalization, existing Session presentation verification, docs
- Created: `2026-10-29`

## Findings Addressed

The observed empty-page envelope was retained as a user message, became the
Session title and inflated question/event counts. The owner confirmed the same
input in a native desktop Session. Reproduction covered legacy, response-only
and counterpart logs before the correction.

## Changes Applied

- Admit only the complete standalone envelope with exactly one `page_id: null`
  JSON field. Reject duplicates and preserve unknown, malformed and literal forms.
- Reuse the existing per-block generated-context path so actual questions,
  adjacent blocks and assistant quotations keep their source order.
- Advance the Codex Session contract to v12; ordinary Sync repairs unchanged
  files while preserving Session IDs, pins, Workstream links and Usage snapshots.
- Keep native JSONL and existing control-only/parsed-empty lifecycle rules.
- Update the canonical Session owner and its generated source/audit digests.

## Evaluation And Remaining Boundary

[Evaluation](../evaluation/eval-0015-r2-codex-empty-page-control.md) passed contract
and functional checks, with a non-blocking narrow-screen literal-title finding.
Non-null page states, unrelated context/CRLF formats and native distribution
remain separate. The subsequently authorized live web application is complete
in RUN-227 attempt 2: normal Sync repairs the persisted projection and the
actual HTTP detail, preserving the selected native source and existing Usage.

The owner-requested compatibility audit adds current-schema arbitrary/renamed
profile coverage and a read-only old/new parser comparison. All 1,426 tests pass;
no unexpected output differences were found within the inspected corpus. Exact
standalone authored copies of the recognized envelope share its content-based
classification; literal framing remains the supported way to preserve examples.

## Recommended Route

- Automated correction complete; human review of RUN-227 and its evidence limits.
