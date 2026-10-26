# FIX-0131: macOS First-Page Authentication

## Metadata

- ID: `fix-0131`
- Status: `complete`
- Run: [RUN-169](../run/run-20261018-169-standalone-macos-runtime.md)
- Attempt: 2 — user-reported startup correction
- Feature: [FEAT-0131](../feature/feat-0131-standalone-macos-runtime.md)
- Spec: [SPEC-0131](../spec/spec-0131-standalone-macos-runtime.md)
- Execution Profile: `fullstack-product`
- Surface Lane: native WebView → loopback authentication, error encoding, packaged runtime
- Created: `2026-10-19`
- Updated: `2026-10-19`

## Input Reports

The owner opened the delivered app and saw an authentication JSON error with
unreadable Korean. The previous [integration evaluation](../evaluation/eval-0139-functional-standalone-test-app.md)
verified native window/process lifecycle but did not establish authenticated
first-page rendering. That evidence was insufficient for startup acceptance.

## Fix Scope And Cause

The native shell first loads `tauri://localhost`, then navigates to the loopback
`/desktop/start` handshake. Its `SameSite=Strict` cookie was stored but omitted
on the following top-level redirect. WKWebView received HTTP 401 on `/onboarding`.
The JSON response had no explicit charset; WebKit guessed EUC-KR and misdecoded
the UTF-8 Korean message. Both observations were reproduced with synthetic data
against the original frozen backend, including the exact unreadable text.

## Changes Applied

- Use an HttpOnly `SameSite=Lax` launch cookie for this top-level GET transition.
  Per-launch token validation, loopback host restriction, product admission and
  cross-origin mutation rejection remain required.
- Explicit UTF-8 on boundary JSON errors; private/no-store error and handshake
  responses, and no-referrer on the token-bearing handshake.
- Add six middleware regression tests for the handshake, stale cookie, saved
  start page, wrong/missing token, mutation origin and edition/host boundaries.
- Add [the macOS WKWebView startup check](../../../scripts/qa-desktop-startup-webkit.swift).
  It begins at the custom scheme with a fresh nonpersistent cookie store, then
  checks the rendered shell, UTF-8, protected health/settings requests, settings
  dialog opening/closing and removal of the token from the landing URL. It can
  seed a previous-launch cookie. It emits booleans, not private page contents.

## Verification

- Original frozen backend: new check exits 1 with `landing HTTP 401` (negative control).
- Fixed frozen backend: fresh and previous-cookie runs both exit 0; all six
  rendered/API checks pass. A synthetic WKWebView snapshot was inspected through
  its own snapshot API, without changing Screen Recording or Accessibility settings.
- Missing authentication still returns 401, with `application/json; charset=utf-8`
  and correctly decoded Korean; cross-origin writes remain 403.
- Six new unit checks pass. Full suite: **1,178 tests, 1,174 passed, four existing
  learning schema/value-inventory failures, no errors**.
- Rebuilt the Python backend with the same PyInstaller 6.22.3 toolchain, reused
  the unchanged native-shell implementation, and re-signed the app ad hoc.
  Deep strict codesign verification passed. No model download or user-data
  migration was performed for this repair.

## Contract Or Lane Impact

The owner document now records cross-scheme cookie behavior and UTF-8 errors.
The initial native lifecycle result remains limited to window/process behavior;
this repair adds direct WKWebView startup evidence against the frozen backend.
It does not certify native file choosers, menu shortcuts, Notes permissions,
recipient Gatekeeper behavior or another Mac.

## Remaining Issues And Return Decision

The startup defect is repaired. Return: `re-evaluate`, with the above regression
results. The broader PRD retains its required direct native/teammate checks and
four unrelated suite failures; those are not cleared by this fix.

## Continuity Notes

- `2026-10-19`: The user report invalidated first-page readiness of the initial
  ZIP. The initial artifact must be replaced by the repaired app/ZIP; current
  artifact identity is recorded in the integration evaluation and BUILD-INFO.

- `2026-10-19` owner confirmation: after replacement and relaunch at the same path,
  the owner confirmed “정상 화면이 보여요”. This confirms the actual Tauri app
  landing on this Mac. It does not close the other native-control or teammate
  acceptance gaps.
