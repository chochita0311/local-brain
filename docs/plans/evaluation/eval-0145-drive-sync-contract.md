# EVAL-0145: Drive Sync Contract

## Metadata

- ID: `eval-0145`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`
- Feature: [feat-0145](../feature/feat-0145-drive-sync-contract.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Active Spec: [spec-0145](../spec/spec-0145-drive-sync-contract.md)
- Run: [run-20261028-209](../run/run-20261028-209-drive-sync-contract.md)
- Attempt: 1
- Execution Profile: `foundation-contract`
- Required Evaluators: contract, functional
- Created: `2026-10-28`

## Scope And Evaluator Results

Primary agent performed these logical roles sequentially; this is same-author review, not independent certification. PASS applies to the observed app contract. Evidence limits and live acceptance are separate.

| Evaluator | Result | Evidence Coverage | Witness |
| --- | --- | --- | --- |
| Contract | PASS | complete | Producer/consumer contract and synthetic cases below. |
| Functional | PASS | complete | Declared local behavior and regression scope observed. |

## Checks And Evidence

URL/resource-key parsing, inclusive100MB cap before reads, hidden/link inventory, private schema1 state, per-item checkpoints, all seven fixed intervals and DST/no-catch-up decisions; contract/policy inspected against both directional consumers.

- Final synthetic Drive suite:39tests pass as part of the full suite. No actual user source content or account destination was used.
- Full command: `.venv/bin/python -m unittest discover -s tests -v` —1297tests,1292pass,5fail. Remaining failures are the pre-existing Learning/schema owner-table/audit inventory, presentation count and value-registry count mismatches. The failing schema, registry, builder and related test inputs match their work-start fingerprints. These are separate unresolved regression debt, not a green full-suite claim.
- Relevant peers:6App Docs,45UI contract,8desktop boundary and6desktop build tests pass. JavaScript syntax, `git diff --check`, generated artifact catalog and repository privacy scan pass.
- Package evidence: wheel includes all seven Drive modules, web routes, script/panel and guide; keyring dependency present; runtime DB/log/Session files and personal/provider OAuth data absent. A native backend package includes the macOS Keychain module and starts/serves/shuts down with an isolated data root.
- Browser host: Chrome source runtime, restarted after backend changes, loopback only;1440×1000 and320×800 actual viewports. Both standalone provider-missing state and injected five-publisher fixture observed. No outer horizontal overflow; last publisher/footer reachable. Expected422 diagnostic request is distinct from a JavaScript exception. No native UI-host or live Google certification is inferred.

## Evidence Gaps And Acceptance Impact

No live Google claim belongs to this shared local contract. Other Features own the provider and release gates.

## Findings And Fixes

Resolved implementation issues within the same attempt: scope Settings field names to avoid another form's URL control; guide fragment must use the shared Markdown heading ID; native tab inventory and timezone explanation kept aligned; do not swallow failed saves before a run; bound resource-key headers to relevant IDs; preserve descendants of failed/symlink scans and inaccessible parents; checkpoint per item; recover atomic replacement before checkpoint; handle file/folder replacements without erasing unmanaged contents. Relevant tests re-run after fixes. OAuth completion reuses the validated account instead of a second network lookup; invalid provider JSON and unsupported upload-selection fields are rejected. Open-tab polling refreshes local cached state and stops on close. No remaining observed blocker in the declared local app contract.

## Route

Pass this bounded outcome for owner review; preserve parent integration/release gates.
