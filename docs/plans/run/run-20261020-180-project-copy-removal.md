# run-20261020-180-project-copy-removal

## Metadata

- Status: `passed`
- Feature: [FEAT-0134](../feature/feat-0134-general-and-project-settings.md)
- Active Spec: [SPEC-0134](../spec/spec-0134-general-and-project-settings.md)
- Execution Profile: `frontend-product`
- Required evaluations: Functional, Design, Interaction

## Approved Boundary

Remove the added Project scope/total paragraph and its unused CSS. Frontend profile,
Project composition copy lane, screen-alignment `extend`. Restore the existing heading
and controls immediately followed by the table. Preserve usage membership, denominator,
rows, By Project / Project labels, work-specific empty state, stored data and settings.
Primary owns implementation and review; no delegation. Related test/browser/app
verification authorization remains active. Prior copy evidence belongs to Run 179.

## Verification Plan

Check the UI contract and usage tests, synthetic wide/narrow original and updated
web/frozen screens, source/model/project switching, unchanged values and contained
layout. Refresh the bundled assets, signature, ZIP and checksum; confirm actual native
startup/current HTML and unchanged saved settings. Remove task-owned temporary files.

## Results

Scoped Functional/Design/Interaction PASS. [Functional receipt and artifact identity](../evaluation/eval-0139-functional-standalone-test-app.md#project-notice-removal-delivery--2026-10-20-superseded-artifact)
and [design/interaction receipt](../evaluation/eval-0139-design-standalone-test-app.md#project-notice-removal--2026-10-20)
record the detailed evidence. 44 UI contract plus 17 usage tests passed. Original
frozen baseline and updated web/frozen at 1100/320 each passed eight checks. Captures
were inspected. The template/CSS removal introduces no data or query change.

The actual app was gracefully replaced and reopened. Authenticated dashboard HTML
has no notice, served CSS matches source, and settings/source-registry hashes are
unchanged. App deep strict signature, ZIP CRC, app bytes/modes/links, separately
extracted signature and installed ZIP checksum passed. The backend executable hash
is identical to Run 179; no Python/Rust rebuild or model download was performed.
Broader native controls, physical input, VoiceOver, minimum-OS and teammate checks
retain their recorded limits. No full-suite rerun, upload, commit or publication.

## Completion Checks

Privacy check passed for 1,416 candidate files; diff whitespace, schema presentation,
plan catalog freshness and changed planning link targets passed. All task-owned
processes exited. Tools, fixtures, screenshots, staging/extracted builds and recovery
copies were removed after checking active use. Updated app/ZIP remain in dist;
the app was reopened successfully with saved settings intact.
