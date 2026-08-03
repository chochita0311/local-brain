# EVAL-0069: Session Source Scope And Provenance — Design

## Metadata

- ID: `eval-0069-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS WITH SUGGESTIONS`
- Run ID: `run-20260802-74`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-session-source-scope-and-provenance](../spec/spec-0069-session-source-scope-and-provenance.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Sessions controls, rows, pins, Subsessions, and detail orientation
- Evidence Coverage: `partial`
- Created: `2026-08-02`

## Scope

- Evaluated peer-control hierarchy, readable provenance, provider-cue reuse,
  stable row/detail geometry, and responsive containment contracts.

## Checks And Evidence

- Source choices reuse the existing segmented-control family and are populated in
  one deterministic registry loop rather than hard-coded Claude/Codex markup.
- Personal and company Codex intentionally share `CX`; adjacent readable source
  labels distinguish them without color or initials alone.
- Provenance is subordinate to the Session title and activity facts in ordinary,
  pinned, Subsession, and detail presentation.
- The control retains each peer at intrinsic width and scrolls horizontally when
  labels exceed the available width; the narrow breakpoint does not stretch
  peers into misleading full-width rows.
- Existing Session row, pin utility, child disclosure, conversation, and related
  context component geometry remains in place.
- Rendered Jinja fixtures confirm option order, selected state, provenance labels,
  scoped detail links, and empty-state ownership.

## Evidence Gaps

- The Browser skill's required in-app control capability was unavailable, so
  screenshots and pixel measurements at 1440, 920, 700, and 320px were not
  collected. The report does not claim those rendered pixels as observed.
- Acceptance impact: non-blocking because existing component tokens, breakpoints,
  DOM order, overflow behavior, and synthetic rendering are directly covered.

## Findings

- No hierarchy, color-only distinction, or fixed-width containment failure found.
- Suggestion: collect the four-width visual sample in the next browser-enabled UI
  run, especially with longer owner-customized source labels.

## Route

- Next action: `pass` with rendered-evidence follow-up retained.
