# Run236: Shared Docs Language Option

## Metadata

- ID: `run-20261106-236`
- Status: `passed`
- Feature: [FEAT-0157](../feature/feat-0157-bilingual-app-docs.md)
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Active Spec: [SPEC-0157 shared-language amendment](../spec/spec-0157-bilingual-app-docs.md#shared-language-option--2026-11-06)
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Attempt: `1`
- Created: `2026-11-06`

## Boundary And Visual Contract

Screen-alignment `extend`: existing Docs shell/tokens, fixed registry, all twelve
bodies, locale queries and surrounding app language stay intact. The old pair of
links under the article heading reads as an article-specific setting. Move it to
a single current-language dropdown in the common Docs contents header, with a
below-trigger menu. Narrow mode keeps the control with the common contents.
Initial dirty prior implementation/installation changes are preserved. Before
source/body hashes and the previously delivered screenshot were inspected.

## Verification And Risk

Docs8 route/link/error tests; browser closed/open, current option, same-topic
language switch, guide/history retention, keyboard/Escape focus, outside dismissal,
no-script native disclosure, and 1440/920/700/320px geometry. Rebuild and inspect the
actual local artifact before replacing canonical output. This is a low-risk
single-surface refinement with no auth/data/schema/backend contract change;
primary semantic review is proportionate, no delegated challenge required.

## State

Implementation and local verification passed. Human review will assess the shared-option presentation after launching the updated app at its normal canonical path. All twelve guide bodies retain their before-content hashes; the surrounding app language retains its observed labels.

## Delivery History

Initially, a canonical-dist native app, backend and worker were running. The
verified refinement was offered in a separate folder to preserve those processes.
The owner questioned the alternate path. On follow-up, no LocalBrain process was
running, so the same verified app/ZIP/checksum were promoted to the original
`dist/` paths with backup/rollback publication. Signature, source fingerprint and
ZIP checksum matched; four isolated frozen checks passed at the canonical path.
The empty `dist/docs-language-option/` folder was removed. No user process was
stopped and no source rebuild or application-data change was needed for promotion.

## Evaluation

| Evaluator | Result | Evidence Coverage | Observed scope |
| --- | --- | --- | --- |
| Design | PASS | complete | Actual screenshots inspected at1440/920/320px; closed/current-language disclosure and below-trigger menu use existing tokens. Menu hit targets remain reachable at1440/920/700/320. |
| Functional | PASS | complete | Docs8 and full Python1,534; desktop browser94, including all12 guides, common-control placement, same-topic selection/history, keyboard/Tab/Enter/Escape/focus, outside dismissal, controller failure fallback and unchanged app labels. |
| UX heuristic | PASS | complete | Language option belongs to shared contents, article reading starts without per-article controls, selected language is visible and follows guide navigation. |
| Packaging | PASS | complete | Rebuilt app, strict deep codesign/private-path checks; actual frozen backend12 guides plus2 exact CSS/JS hashes and an isolated native WebKit interaction (15 checks). Relocated frozen14 checks PASS in the final separate delivery path. |

The first CDP keyboard attempt sent keydown/up without a keypress. Recorded focus
and events isolated this test-input issue; adding Enter text produced the native
keypress/default action. Product code uses native disclosure/link activation.

## Artifact And Remaining Review

- App: `dist/LocalBrain-apple-silicon/LocalBrain.app`.
- ZIP/checksum: under `dist/`; BUILD-INFO: under `dist/LocalBrain-apple-silicon/`.
- Built UTC `2026-11-06T01:38:04.097828+00:00`, v0.0.1, dirty HEAD52a99d8.
- Input SHA256 `3103eac8b21022daaa619738577e8b160adb1a77ee329699d0cd8299b00cf3da`.
- ZIP SHA256 `e0b25767892ed27787f0f717cf2abe6f810ce3650d9aa9f10016f79e6c38fff5`.
- The original artifact was preserved during the initial running session. After
  the app was closed, the verified update replaced the canonical output. Launch
  the normal app path to use the shared language menu.
- No source commit/push, global preference change, Windows change or model work.

- Closing gates: privacy1,777 candidates PASS; guide body hashes12 unchanged; current build fingerprint matches delivered BUILD-INFO; diff whitespace and artifact catalog checked.
