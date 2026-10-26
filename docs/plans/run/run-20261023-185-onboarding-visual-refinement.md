# run-20261023-185-onboarding-visual-refinement

## Metadata

- Status: `passed`
- Feature: [FEAT-0137](../feature/feat-0137-first-run-local-setup.md)
- Active Spec: [SPEC-0137](../spec/spec-0137-first-run-local-setup.md#onboarding-visual-refinement--2026-10-23)
- Execution Profile: `frontend-product`
- Surface Lanes: onboarding layout, transition/focus, packaged assets
- Required evaluations: Functional, Design, Interaction

## Approved Boundary And Reference

The owner rejected the first wizard's visual quality and asked for the feel of
polished native setup, specifically bottom page dots and the transitions on
[Tesla's homepage](https://www.tesla.com/), while retaining LocalBrain's design
constitution. This is `screen-alignment` **adapt**. Primary owns implementation
and evaluation; prior related tests/browser/app verification authorization applies.

Rendered Tesla inspection found a centered hero, restrained controls and small
bottom dots. Its hero crossfades opacity over one second; a lower product carousel
uses smooth horizontal scrolling with mandatory snap. Borrow quiet hierarchy,
stable framing, bottom progress and coherent motion. Keep LocalBrain's neutral
surfaces, warm action color, SF-oriented type, compact geometry and motion tokens.
No external imagery, marketing copy, auto-advance or foreign theme is imported.

## Mismatches And Planned Changes

- Structure/border: the heavy title separator and numbered top row split the
  compact setup into stacked boxes. Use a quieter header and bottom progress.
- Type/spacing: multiple bold titles and redundant hierarchy make the form feel
  administrative. Use existing medium/semibold roles and intentional spacing;
  retain labels, help, errors, real source entries and explicit model controls.
- Interaction: the current instant swap has no visual continuity. Crossfade with
  a small directional offset using shared motion tokens; keep the footer fixed.
  Reduced motion swaps immediately. During transition, prevent duplicate moves
  and isolate the outgoing/incoming inputs before handing focus to the new title.
- Scope: keep four actual steps, their existing Back/Next/Skip/Later semantics,
  source consent, completion persistence and normal settings behavior. The bottom
  dots indicate progress; they do not introduce a shortcut that bypasses saves.

## Verification Plan

Compare rendered reference/current/family states. Exercise all steps at wide and
320px widths; inspect early/middle/late transitions, rapid clicks, reduced motion,
keyboard focus, long forms and errors. Re-run focused tests and synthetic browser
save/skip/completion checks. Update/re-sign app assets and ZIP, confirm source
parity and runtime behavior without changing the owner's settings or downloading
models, and clean task-owned captures/staging after verification.

## Results

- Quiet header and centered welcome replace the heavy separators and numbered
  top strip. Four accessible bottom dots track the four actual steps. Desktop
  source fields use two columns; narrow screens retain a single column. Content,
  registration consent, explicit model actions and normal settings stay intact.
- The shared 240ms/16px motion tokens provide a short crossfade and directional
  offset. Both panels are inert during handoff, duplicate moves are disabled,
  the outgoing scroll position is preserved and incoming heading receives focus.
  Reduced motion swaps immediately. A narrow final-label footer wrap and a
  hidden reconnect-label CSS conflict were found and corrected.
- 119 existing focused tests and JavaScript syntax passed. Six source/frozen
  WKWebView cases at 1100×800, 320×720 and 700×480 passed 258 checks. Chromium
  passed 43 normal-motion and 33 reduced-motion checks. Additional browser
  actions verified source/document saves, validation/error retention, failed and
  ambiguous completion, general autosave, dropdown placement and native-dialog
  keyboard behavior. No model download was performed.
- The packaged backend and actual running app each passed six startup checks.
  Reused the native/frozen runtime, updated the three UI assets, re-signed and
  replaced the app/ZIP/checksum. Raw/compressed private-path checks, ZIP integrity
  and extraction parity, deep strict signature and served-source parity passed.
  Exactly one actual app is running; three real saved configuration files retain
  identical hashes, including the existing completed-onboarding flag.
- Scoped [functional delivery](../evaluation/eval-0139-functional-standalone-test-app.md#onboarding-visual-refinement-delivery--2026-10-23-superseded-artifact)
  and [design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#onboarding-visual-refinement--2026-10-23)
  evaluations passed. Full-suite, physical native input/VoiceOver, native pickers
  and recipient-Mac acceptance retain their existing evidence limits. No external
  publication or Git commit; no broader feature acceptance is implied.

## Completion Checks

- Repository privacy check passed for 1423 candidate files; `git diff --check`
  passed. Verified 117 local links/anchors across ten affected owner/evidence
  documents. The generated plan catalog is current.
- Final installed inventory, checksum, source/template/guide parity and deep
  strict signature passed. Existing saved configuration remains unchanged.
- Closed the task browser page and synthetic servers; confirmed no open files
  before removing all task-owned reference captures, previews, synthetic data,
  probes, build/cache/staging and previous-delivery recovery copies. App, ZIP
  and checksum remain in `dist/`; no temporary dependency remains.
