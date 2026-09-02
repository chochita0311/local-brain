# EVAL-0081 UX: Atlassian Deterministic Site-First Hierarchy

## Metadata

- ID: `eval-0081-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260901-91`
- Attempt: `1`
- Feature: [FEAT-0081](../feature/feat-0081-atlassian-deterministic-site-first-hierarchy.md)
- Spec: [SPEC-0081](../spec/spec-0081-atlassian-deterministic-site-first-hierarchy.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Hierarchy orientation; responsive browse continuity`
- Evidence Coverage: `complete`
- Created: `2026-09-01`

## Checks And Evidence

- The default task now reads as `모든 도메인 → domain → Project/Space | URL
  group | 소속 미확인`. All/Jira/Wiki remain the first peer scope choice rather
  than being repeated inside every domain, so mixed inventory can be scanned
  once without losing service filtering.
- Equal child labels stay separate and understandable without color. All shows
  `Jira · URL 기준` or `Wiki · URL 기준`; a service-specific view keeps the
  provenance cue `URL 기준`. Row, preview, and full-detail copy repeats the
  bounded URL-basis cue where needed, so a user can distinguish local URL
  organization from persisted Project/Space membership.
- Hierarchy nodes remain ordinary server-authored links with visible active
  treatment and `aria-current`. Canonical destinations preserve the applicable
  view, query, and advanced filters, clear selected link/document state under
  the existing structural-transition contract, and remain executable without
  JavaScript.
- At wide width, focus and reading order is hierarchy rail, result list, then
  adjacent preview. At `920` and below, the hidden rail is replaced by the
  in-flow compact hierarchy disclosure before the result heading and list; an
  active child opens the disclosure. Selected preview continues to use the
  established drawer/sheet modal owner after the list.
- The existing selection controller still owns preview identity, selected-row
  semantics, focus destination, list/page scroll, and browser history. The Sync
  fragment contract still names hierarchy rail, compact hierarchy, and results
  separately and restores hierarchy, list, preview, page, focus, and compact
  disclosure state after replacement.
- Supplied Chrome evidence found the All hierarchy's shared domain once in the
  inspected branch with no service parent, verified mixed provenance cues, and
  verified the reduced URL cue in Jira. The `1440` three-region and `920`
  compact/list compositions remained legible and retained the existing action
  order.
- At `700`, the 325/325-pixel Sync/Add row and 657-pixel More row kept 40-pixel
  targets. At emulated `320`, the 142/142-pixel Sync/Add row and 292-pixel More
  row also kept 40-pixel targets; the open hierarchy labels wrapped and the
  320-pixel document did not exceed the 320-pixel viewport.
- Strict Add handoff was exercised for Jira and Wiki. Both finished on a `200`
  Explorer response with the correct service-qualified URL scope; focused
  route tests also retain persisted-Space precedence, reused and archived item
  context, and the unclassified fallback for a valid loose Wiki page.
- The evaluator reran the complete automated suite with `436/436` passing and
  JavaScript syntax passed. Supplied mobile Lighthouse evidence reported
  Accessibility `100`, Best Practices `100`, and Agentic `100`; supplied final
  console inspection reported zero errors and zero warnings.

## Findings

- None.

## Route

- Next action: `pass`
