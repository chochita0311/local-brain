# EVAL-0125: Reviewed Learning Contract

## Metadata
- ID: `eval-0125-contract`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Evaluator: `contract`
- Feature: [FEAT-0125](../feature/feat-0125-reviewed-learning-home.md)
- Spec: [SPEC-0125](../spec/spec-0125-reviewed-learning-home.md)
- Run: [RUN-163](../run/run-20261017-163-reviewed-learning-home.md)
- Created: `2026-10-17`

## Inspected Contract

The primary agent inspected the packet validator, additive schema, importer,
local route handlers, scheduling and rendering against FEAT-0124. All packet
validation precedes the batch write; caller-owned transactions cover the batch.
Stable key and canonical-content digest distinguish identity from revision.
Attempts use a restrictive revision FK, question membership and duplicate-token
payload comparison. Pending self-assessment uses a guarded one-way transition.
Reading, hints and reported confidence retain separate meanings; no score or
mastery value is inferred. Visibility changes do not modify attempt history.

Configured-local completion dates, pre-day selection and latest completion per
day express the bounded schedule. Source snapshots have their own fingerprint;
unknown versions, source age and declared reviewer remain visible. Assistant
review does not imply owner review. Browser reads do not invoke a model or fetch
external sources. Native POSTs require loopback host, same origin, URL-encoded
bounded input and admitted fields. Source text is autoescaped plain text.

## Observed Production Actions

- The existing private database accepted three lessons with nine questions.
  A subsequent import appended three revisions declaring assistant review;
  current library selection still contains three lessons, and prior revisions
  remain. No personal answer/self-assessment was manufactured.
- Schema presentation and value dictionaries were regenerated from their owners.
  Current schema adds three ordinary tables, one restrictive FK and one explicit
  index; the learning subject has complete bounded-value mappings.
- Normal app startup completed against the existing local DB. These successful
  actions support only their observed paths, not all migration/import behavior.

## Limits And Acceptance Impact

No tests were added or run under the active session instruction. Existing fixed
schema-count assertions were updated with the additive baseline, not executed.
Atomic failure/rollback, identical replay, conflicting submission, concurrent
writes, timezone rollover, old-revision attempts, missing sources and mutation
recovery have source inspection only. This is a contract inspection PASS, not a
functional PASS. Required functional evidence remains open and blocks formal
Feature/Run acceptance; it does not block the implemented pilot from local review.
No generator admission, source monitoring or learning benefit is established.
