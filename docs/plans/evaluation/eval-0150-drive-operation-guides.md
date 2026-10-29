# EVAL-0150: Drive Operation Guides

Historical authentication witness: Desktop Client prerequisites in this attempt were superseded by the approved gcloud revision in [Runs215–217](../run/run-20261028-215-drive-oauth-adapter.md). Preserve the original evidence/outcome; current provider, native and recipient acceptance belongs to the later implementation/integration records.

## Metadata

- ID: `eval-0150`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [feat-0150](../feature/feat-0150-drive-operation-guides.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Active Spec: [spec-0150](../spec/spec-0150-drive-operation-guides.md)
- Run: [run-20261028-214](../run/run-20261028-214-drive-operation-guides.md)
- Attempt: 1
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`

## Scope And Evaluator Results

Primary agent performed these logical roles sequentially; this is same-author review, not independent certification. PASS applies to the observed app contract. Evidence limits and live acceptance are separate.

| Evaluator | Result | Evidence Coverage | Witness |
| --- | --- | --- | --- |
| Contract | PASS | complete | Producer/consumer contract and synthetic cases below. |
| Functional | PASS | partial | Declared local behavior and regression scope observed. |
| Design | PASS | complete | Existing Settings/Docs family, actual320px and1440px, wrapping, scroll reachability and shell. |
| UX heuristic | PASS | complete | Repeated selection/run controls, independently saved intervals, inline partial results and guide navigation. No new reusable design-rule candidate. |

## Checks And Evidence

Six canonical English guide routes retained; app user guide and provider Desktop Client/Google Cloud/Testing/production instructions; privacy/storage/architecture/model owners aligned. Wheel assets/metadata verified; macOS frozen backend built and authenticated Settings/status/guide, anonymous rejection and shutdown observed without Google or OS-token calls.

- Final synthetic Drive suite:39tests pass as part of the full suite. No actual user source content or account destination was used.
- Full command: `.venv/bin/python -m unittest discover -s tests -v` —1297tests,1292pass,5fail. Remaining failures are the pre-existing Learning/schema owner-table/audit inventory, presentation count and value-registry count mismatches. The failing schema, registry, builder and related test inputs match their work-start fingerprints. These are separate unresolved regression debt, not a green full-suite claim.
- Relevant peers:6App Docs,45UI contract,8desktop boundary and6desktop build tests pass. JavaScript syntax, `git diff --check`, generated artifact catalog and repository privacy scan pass.
- Package evidence: wheel includes all seven Drive modules, web routes, script/panel and guide; keyring dependency present; runtime DB/log/Session files and personal/provider OAuth data absent. A native backend package includes the macOS Keychain module and starts/serves/shuts down with an isolated data root.
- Browser host: Chrome source runtime, restarted after backend changes, loopback only;1440×1000 and320×800 actual viewports. Both standalone provider-missing state and injected five-publisher fixture observed. No outer horizontal overflow; last publisher/footer reachable. Expected422 diagnostic request is distinct from a JavaScript exception. No native UI-host or live Google certification is inferred.

## Evidence Gaps And Acceptance Impact

The full native Tauri window, installed-recipient behavior, real Google authorization and public OAuth verification were not tested. Frozen backend and wheel evidence do not establish these. This does not block the bounded guide/local contract; parent integration/release acceptance remains open.

## Findings And Fixes

Resolved implementation issues within the same attempt: scope Settings field names to avoid another form's URL control; guide fragment must use the shared Markdown heading ID; native tab inventory and timezone explanation kept aligned; do not swallow failed saves before a run; bound resource-key headers to relevant IDs; preserve descendants of failed/symlink scans and inaccessible parents; checkpoint per item; recover atomic replacement before checkpoint; handle file/folder replacements without erasing unmanaged contents. Relevant tests re-run after fixes. OAuth completion reuses the validated account instead of a second network lookup; invalid provider JSON and unsupported upload-selection fields are rejected. Open-tab polling refreshes local cached state and stops on close. No remaining observed blocker in the declared local app contract.

## Route

Pass this bounded outcome for owner review; preserve parent integration/release gates.

## Reproducing Package Evidence

Python3.11.15, PyInstaller6.22.3 and keyring25.7.0 were used. Wheel construction used `uv --system-certs build --wheel`; frozen backend construction used `.venv/bin/python -m PyInstaller desktop/backend.spec --noconfirm`, with separate task-owned output/work/cache directories. The frozen executable was launched with synthetic data/source roots and a generated per-launch token; its random loopback port served authenticated `/settings`, `/api/settings/google-drive`, `/help/settings` and the exact current `google-drive.js` bytes. The unauthenticated Drive request returned401, shutdown returned200 and the process exited0. No Google authorization, real OS token operation or native Tauri window was inferred from these checks. Build/runtime outputs were temporary verification artifacts and removed after their results were recorded here.
