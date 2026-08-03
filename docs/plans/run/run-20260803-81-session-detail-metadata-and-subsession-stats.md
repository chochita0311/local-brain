# RUN-20260803-81: Session Detail Metadata And Subsession Stats

## Metadata

- ID: `run-20260803-81`
- Status: `passed`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Active Spec: [spec-0069-r5-session-detail-metadata-and-subsession-stats](../spec/spec-0069-r5-session-detail-metadata-and-subsession-stats.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Alignment Mode: `extend`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Goal

- Remove repeated visible source names from Session detail headings and detail
  Subsession rows, and add question count before event count with family-aligned
  row geometry.

## Selected Loop

- Feature type: `product`
- Profile: `frontend-product`
- Lanes: Session detail heading → Subsession list stats → lazy Subsession detail → owner docs
- Affected routes: `/sessions/{id}` and lazy Subsession detail
- Components: detail heading source cue and detail Subsession rows
- Required evaluators: Contract, Design, Functional, UX Heuristic
- Current phase: complete

## Contract Surfaces

- existing child `user_message_count` route projection
- visible versus accessible source provenance in detail templates
- desktop and responsive Subsession metadata order
- primary, normalized child, and lazy child route presentation

## Current Artifacts

- Spec: [spec-0069-r5-session-detail-metadata-and-subsession-stats](../spec/spec-0069-r5-session-detail-metadata-and-subsession-stats.md)
- Evaluations:
  - [Contract](../evaluation/eval-0069-r5-contract-session-detail-metadata-and-subsession-stats.md)
  - [Design](../evaluation/eval-0069-r5-design-session-detail-metadata-and-subsession-stats.md)
  - [Functional](../evaluation/eval-0069-r5-functional-session-detail-metadata-and-subsession-stats.md)
  - [UX heuristic](../evaluation/eval-0069-r5-ux-session-detail-metadata-and-subsession-stats.md)
- Fix log: none

## Evidence Plan

- Render synthetic company primary and normalized child detail routes.
- Assert no visible configured source eyebrow or child metadata prefix while `CC`
  and `sr-only` source identity remain.
- Assert detail child question, event, and date order and responsive CSS ownership.
- Run focused UI/detail tests, full repository tests, privacy, and diff checks.
- Attempt Browser-skill evidence; record partial design/UX coverage if its required
  in-app control capability remains unavailable.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: all four evaluators passed; Design and UX retain explicit partial
    browser-evidence coverage
  - notes: Browser skill was read and tool discovery was attempted, but its
    required in-app control capability is not exposed in this session. The first
    full suite found two equivalent value-registry failures caused by removing the
    accessible source-kind fallback; the bounded fix restored it only in
    `sr-only` detail text. Final source review also added question counting for
    non-normalized lazy Claude children. The final 327-test suite passed.

## Post-Contract Regression Check

- Needed: yes
- Result: passed; rendered company primary/child fixtures, focused Session/UI
  tests, the final 327-test repository suite, privacy check over 722 candidate
  files, and `git diff --check` all pass

## Human Review Outcome

- Decision: owner requires source-neutral visible detail metadata and Sessions-
  aligned Subsession question/event/date presentation.
- Follow-up run: none unless post-run owner review finds another bounded mismatch

## Continuity Notes

- `2026-08-03`: Orchestrator selected Frontend Product and `extend` alignment.
  The correction reuses current source cues, Session count fields, semantic roles,
  and responsive breakpoints; no backend or persistence contract is introduced.
- `2026-08-03`: attempt 1 passed after one implementation-bug correction. Detail
  headings and child metadata no longer repeat configured source names; child
  rows now show question before event and date, including lazy Claude child
  summaries. All required evaluator results, final tests, privacy, and diff checks
  pass.
