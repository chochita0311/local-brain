# EVAL-0147: Drive Settings Connection Repair

## Metadata

- ID: `eval-0147-repair`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0147](../feature/feat-0147-drive-settings-connection.md)
- Active Spec: [SPEC-0147](../spec/spec-0147-drive-settings-connection.md)
- Run: [Run218](../run/run-20261028-218-drive-settings-connection.md)
- Attempt: 3
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`

## Problem And Correction

Metadata save previously left account/root verification as two separate actions while exposing full auth, diagnostics, unselected schedules and empty timestamps. This made an incomplete connection look like an unexplained configuration task. A sanitized read of the active source runtime showed cached auth/network failure without a bound account; no real destination or account identifier was retained. A credential-free public API probe reproduced default Python certificate verification failure; a system-trust context reached an expected unauthenticated401 response. This establishes a transport problem and correction, not account/permission success.

The explicit save-and-check action now saves metadata, connects existing SDK credentials and browses the root in order. A saved destination has one check/retry action. No file upload or browser login is implicit in this check. Advanced account/login and separate observations remain in disclosures; initial sync controls follow successful root verification, while configured controls remain available after later errors. Unselected receive rows show selection first, and selected rows reveal independent schedules/manual actions. Empty result timestamps are omitted.

The scoped Drive HTTPS context uses the existing truststore version as a base macOS dependency, retains certificate/hostname verification and NoRedirect, and avoids global SSL injection or organizational certificate bundles. TLS errors have their own sanitized code/message and no automatic login/retry. A certificate failure is not inferred to be a missing invitation or expired authentication.

## Evaluation Results

Primary agent performed sequential logical roles without delegated agents or independent certification.

| Evaluator | Result | Coverage | Witness |
| --- | --- | --- | --- |
| Contract | PASS | complete for local repair | Producer TLS/dependency checks pass before consumer acceptance; existing SDK, scope, root/selection, scheduler/deletion/copy contracts retained. |
| Functional | PASS | partial |55Drive tests; synthetic browser setup, transfer, failures/retry and selection; actual credential-free HTTPS; no user-account/provider operation. |
| Design | PASS | complete for browser Settings | Existing Settings family in screen-alignment extend mode;1440×1000 and actual320×800, scoped hidden semantics, visible options, footer reachability and no root overflow. |
| UX heuristic | PASS | complete for observed flow | Save/check order, distinct explicit login, concise errors/diagnostics, selected-only controls and empty-root message. No reusable promotion candidate established. |

## Evidence

- `.venv/bin/python -m unittest discover -s tests -p 'test_google_drive*.py' -v`:55PASS. Three new transport tests check native SSL context/NoRedirect, default certificate+hostname verification, and non-retryable sanitized TLS classification.
- Full suite1313:1308pass,5fail. Same existing Learning/schema owner-table/audit inventory, presentation count and value-registry count failures; all corresponding inputs match work-start fingerprints. Six guide route/link tests pass after guide edits. No whole-suite success claim.
- Synthetic source server with production gcloud subprocess adapter, synthetic executable and injected Drive API. Opening/status polling issued no SDK or Google calls. Save used SDK account listing and a pinned token command, then account lookup, root metadata and child listing; no login command or transfer occurred. Two roots, four local sources and five publishers exercised. Initial unselected controls hidden; selecting revealed upload360m and receive1440m/OFF defaults, with receive180m saved independently. Synthetic manual upload2files including hidden; receive1file. Deselect preserved the received copy.
- First-setup TLS failure preserved the saved destination and hid initial sync configuration; account options remained closed because it was a TLS error. Explicit login completed through the fake SDK, then check/retry completed root setup. A later TLS failure preserved configured controls, choices, intervals and copies. An empty verified root displayed an accurate empty message. Expected422 diagnostics are not JS exceptions.
- Browser inputs: DevTools fill/click for initial save, script-dispatched control actions for repeated state/selection paths. Actual1440/320 viewports inspected visually and geometrically; options/login remain discoverable at320; footer bottom stays inside dialog; unselected actions/schedules respect hidden even with shared button CSS. Reload used fresh source assets; no native input/host proof inferred.
- Corrected production `google_opener()` reached Google public API with verified TLS and received401 without credentials. This probe supplied no token, account, folder URL/ID or user content. Actual gcloud login, authenticated folder access and user transfers were not run.
- Final wheel assets/code/guide match source; truststore is a conditional base dependency, no changed existing dependency versions. No runtime/credential data bundled. JavaScript syntax, relative artifact links, catalog, diff and privacy are final closing checks recorded in Run218.

## Limits And Route

The user's active server/process was inspected read-only and left running; restart is required to load the new backend transport. Stored destination/selection data is retained. Existing native binaries were not rebuilt; this browser/wheel repair is not a native-recipient or signed release acceptance. Real Google consent, account/root permissions and two-account My Drive/Shared Drive operations remain unverified. Final human/parent integration acceptance is separate from this bounded local PASS. No temporary evidence path is required by this record.
