# run-20261018-170-settings-and-product-navigation

## Metadata

- Status: `blocked`
- Feature: [FEAT-0132](../feature/feat-0132-settings-and-product-navigation.md)
- Active Spec: [SPEC-0132](../spec/spec-0132-settings-and-product-navigation.md)
- Execution Profile: `frontend-product`
- Required evaluations: Contract, Functional

## Selected Loop

The primary agent owns implementation and review. No delegation. User approval covers
implementation and related tests, browser verification and packaged-app execution.

## Current Route

Implementation and available local verification completed on 2026-10-19.
The [functional report](../evaluation/eval-0139-functional-standalone-test-app.md), [contract report](../evaluation/eval-0139-contract-standalone-test-app.md) and
[design/interaction report](../evaluation/eval-0139-design-standalone-test-app.md) record the integration checks for this
Feature and the complete Feature/Spec/Run trace. They distinguish browser evidence,
the actual frozen/native app and real model execution from unobserved native
interactions and the required teammate Mac receipt.

Route: `blocked` for full product acceptance pending those external/manual
observations. The local test artifact is available for owner use. The full suite
has 1,168 passes and four pre-existing learning inventory failures (1,172 total);
no failure is concealed by this route. No upload, teammate message or Git
publication was performed. The 21-commit figure remains an estimate.

## Compact Settings Dialog — 2026-10-19

Owner correction: Settings occupies too much space. Frontend profile, settings-shell
geometry and interaction lanes, screen-alignment `extend`; the primary agent owns
implementation and review. The constitution now caps this dialog at 720×560 CSS
pixels with a 160px desktop category rail, existing spacing roles and the shared
700px horizontal-navigation breakpoint. Text/control sizes and dropdown choices
remain. A flex shell and bounded grid keep the header/close action fixed while
the body scrolls. Tab changes reset scroll without clearing pending values;
nonempty save/error feedback scrolls into view.

- Two focused UI contract tests and JavaScript syntax passed. The first `uv`
  invocation could not access its shared cache under the sandbox; the same checks
  passed using the existing `.venv` interpreter, without installing dependencies.
- One original frozen-backend WKWebView baseline confirmed 992×800 at 1440×900.
  Four final frozen-backend runs at 1440×900, 900×450, 700×650 and 320×650, plus
  ordinary source web at 1100×800, each passed 23 checks. All six categories,
  header/body bounds, scroll reset, fixed header, end reachability, containment,
  matching-width below-trigger menus and scripted Escape passed. Pending values
  survive tab changes; save, close/focus return, reopen, conflict error visibility,
  input retention, retry and restoration of synthetic preferences passed.
- Initial verification found feedback hidden above the scrolled form; the shared
  message helper now brings it into view. Two probe issues were also corrected:
  WebKit's deferred focus scrolling required a settled selection before the next
  simulated action, and narrow layouts hide the footer gear, so those probes open
  Settings with the existing Cmd+, handler from a visible search field. No
  assertion was removed. Scripted input is not physical-keyboard/VoiceOver evidence.
- Wide before/after, short, breakpoint, narrow and ordinary-web screenshots were
  inspected. The compact surface preserves hierarchy and readable controls; long
  panels stay reachable within the fixed shell.
- The frozen backend uses task-owned synthetic storage and offline model settings.
  No model download or real preference mutation. Packaging reuses the existing
  Python/Tauri executables, replaces shared CSS/JavaScript, updates the guide and
  re-signs ad hoc. No Python/Rust rebuild or full-suite rerun.

The [functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#compact-settings-delivery--2026-10-19-previous)
owns artifact identity and actual-app replacement evidence. This correction does
not close the broader recipient/native/minimum-OS acceptance gaps above.

Delivery completed locally: the actual app was reopened, served source-identical
assets and retained saved preferences/settings-source file hashes. ZIP integrity,
installed/extracted signature, catalog, diff whitespace and owner-document links
passed. Synthetic processes exited and all task-owned temporary artifacts were
removed after checking active use. The updated app remains running.
