# run-20261020-182-portable-python-build-metadata

## Metadata

- Status: `passed`
- Feature: [FEAT-0139](../feature/feat-0139-standalone-test-app-delivery.md)
- Active Spec: [SPEC-0139](../spec/spec-0139-standalone-test-app-delivery.md#portable-python-metadata-correction--2026-10-20)
- Execution Profile: `infra-devtool`
- Surface Lane: Python metadata, build privacy guard and delivered app/ZIP
- Required evaluations: Contract, Functional

## Approved Boundary

The owner requested removal of the private interpreter build paths found by the
preceding audit. Primary owns the bounded repair and evaluation. Existing test
and app execution authorization applies. Preserve user data, settings, source
registration, desktop edition, native UI and unrelated development work.

## Reproduction

The delivered backend's compressed `_sysconfigdata__darwin_darwin` contains the
builder's interpreter prefix in 20 `build_time_vars` fields (26 expanded
occurrences; 13 constants containing 19 occurrences before dictionary expansion).
The ZIP carries the identical backend. Raw-file repository checks missed this
compressed metadata; the audit did not establish a dependency on these paths
for ordinary application execution.

## Implementation And Verification Plan

Generate runtime-relative sysconfig paths through a PyInstaller pre-find hook;
retain all other build/ABI values. Add a packaging check that inspects raw and
compressed code. Test synthetic users and app locations, unchanged flags,
unknown private-path rejection, and detection without code execution. Rebuild
offline into owned staging, inspect all Python code, exercise isolated frozen
startup after relocation, and verify app/ZIP/signatures. Replace/reopen the
actual app and check unchanged settings/source registry. Retire owned scratch
and superseded distribution copies after successful replacement.

## Results

Scoped Contract/Functional PASS. The [contract evaluation](../evaluation/eval-0139-contract-standalone-test-app.md#portable-python-metadata-contract--2026-10-20)
and [functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#portable-python-metadata-delivery--2026-10-20-superseded-artifact)
own the inspected rules, checks, build attempts and exact artifact identity.

42 related tests passed. The offline rebuilt archive preserves all 100 LocalBrain
code modules and 937 non-path sysconfig values; its 20 private installation-path
fields now follow the runtime prefix. The former distribution fails the new
privacy guard and the replacement passes raw/compressed inspection, including
the temporary-build root. Two relocated frozen executions passed 14 checks;
isolated startup passed six routes, authentication rejection and six WebKit checks.
The native shell was reused because the local Tauri CLI was unavailable; the
Python backend was rebuilt and the app re-signed.

App/ZIP/checksum replacement and actual native restart passed. Health/settings
and six WebKit startup checks succeeded, and three saved settings/source/search
files retained their hashes. ZIP CRC, full distribution file parity, extracted
app inventory/signature and installed signature/checksum passed. No model
download or external publication. Other-Mac execution and broader standalone
acceptance remain separate.

## Completion Checks

The final focused rerun passed all 42 tests. Repository privacy passed for 1,420
candidate files; diff whitespace, artifact-catalog freshness and 112 local
planning links/anchors passed. Installed app inventory, signature, ZIP/checksum,
bundled-guide parity, one running native app and three unchanged saved files
were rechecked after replacement.

No process retained open files in the owned temporary directory. Temporary
build/probe tools, generated sysconfig modules, isolated data, build caches,
extracted app and superseded recovery copies were removed, along with the two
task-created bytecode cache files. The durable app/ZIP/checksum remain in `dist/`
and the updated app remains running. No private path or temporary artifact is
required to interpret this record or run the delivered app.
