# EVAL-0147: Drive Settings Connection

Historical authentication witness: Desktop Client prerequisites in this attempt were superseded by the approved gcloud revision in [Runs215–217](../run/run-20261028-215-drive-oauth-adapter.md). Preserve the original evidence/outcome; current provider, native and recipient acceptance belongs to the later implementation/integration records.

## Metadata

- ID: `eval-0147`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [feat-0147](../feature/feat-0147-drive-settings-connection.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Active Spec: [spec-0147](../spec/spec-0147-drive-settings-connection.md)
- Run: [run-20261028-211](../run/run-20261028-211-drive-settings-connection.md)
- Attempt: 1
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`

## Scope And Evaluator Results

Primary agent performed these logical roles sequentially; this is same-author review, not independent certification. PASS applies to the observed app contract. Evidence limits and live acceptance are separate.

| Evaluator | Result | Evidence Coverage | Witness |
| --- | --- | --- | --- |
| Contract | PASS | complete | Producer/consumer contract and synthetic cases below. |
| Functional | PASS | partial | Actual Google/OS credential claims remain blocked; app-only behavior observed. |
| Design | PASS | complete | Existing Settings/Docs family, actual320px and1440px, wrapping, scroll reachability and shell. |
| UX heuristic | PASS | complete | Repeated selection/run controls, independently saved intervals, inline partial results and guide navigation. No new reusable design-rule candidate. |

## Checks And Evidence

Fresh isolated source server and final restarted synthetic fixture; separate Settings tab, URL/name registration, cached status opening, provider-not-ready state, source/publisher controls and actual manual error paths;320px and1440px rendered checks; guide click lands on heading.

- Final synthetic Drive suite:39tests pass as part of the full suite. No actual user source content or account destination was used.
- Full command: `.venv/bin/python -m unittest discover -s tests -v` —1297tests,1292pass,5fail. Remaining failures are the pre-existing Learning/schema owner-table/audit inventory, presentation count and value-registry count mismatches. The failing schema, registry, builder and related test inputs match their work-start fingerprints. These are separate unresolved regression debt, not a green full-suite claim.
- Relevant peers:6App Docs,45UI contract,8desktop boundary and6desktop build tests pass. JavaScript syntax, `git diff --check`, generated artifact catalog and repository privacy scan pass.
- Package evidence: wheel includes all seven Drive modules, web routes, script/panel and guide; keyring dependency present; runtime DB/log/Session files and personal/provider OAuth data absent. A native backend package includes the macOS Keychain module and starts/serves/shuts down with an isolated data root.
- Browser host: Chrome source runtime, restarted after backend changes, loopback only;1440×1000 and320×800 actual viewports. Both standalone provider-missing state and injected five-publisher fixture observed. No outer horizontal overflow; last publisher/footer reachable. Expected422 diagnostic request is distinct from a JavaScript exception. No native UI-host or live Google certification is inferred.

## Evidence Gaps And Acceptance Impact

Provider-owned OAuth Desktop Client is unavailable. No real Google login, actual OS-token round trip or two-account My Drive/Shared Drive create/update/rename/move/Trash/download has been performed. Existing-parent writing under drive.file remains a provider feasibility gate. This blocks live integration/final release acceptance; it is not evidence of an implementation failure or permission proof.

## Findings And Fixes

Resolved implementation issues within the same attempt: scope Settings field names to avoid another form's URL control; guide fragment must use the shared Markdown heading ID; native tab inventory and timezone explanation kept aligned; do not swallow failed saves before a run; bound resource-key headers to relevant IDs; preserve descendants of failed/symlink scans and inaccessible parents; checkpoint per item; recover atomic replacement before checkpoint; handle file/folder replacements without erasing unmanaged contents. Relevant tests re-run after fixes. OAuth completion reuses the validated account instead of a second network lookup; invalid provider JSON and unsupported upload-selection fields are rejected. Open-tab polling refreshes local cached state and stops on close. No remaining observed blocker in the declared local app contract.

## Route

Hold real integration acceptance for provider Client preparation and authorized live account validation; keep the implemented contract available for dependent app-only verification.
