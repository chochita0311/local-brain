# run-20261025-199-settings-row-shadow-lines

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md#settings-row-shadow-lines--2026-10-25)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Profile: `frontend-product`; screen-alignment mode: `adapt`
- Lanes: shared settings-row CSS; rendered verification; packaged-asset delivery

## Approved Correction

The owner clarifies that individual rows should be separated by a subtle edge and
shadow, not tinted fills. Remove the Run 198 resting/hover/drag background tints
from Session and Local Context rows. Use the shared white/default surface, subtle
border and resting card elevation, borrowing the quiet boundaries of the
[Notion reference](https://www.notion.com/ko). Preserve geometry, controls, focus
rings, drag insertion cues and all registration/order/storage behavior.

## Comparison And Validation

Compare rendered reference and current synthetic settings before editing. Check
rest/hover/focus/drag states, row separation and clipping at wide/narrow/short
viewports. This is CSS-only: no new tests or backend rebuild are needed. Verify the
source and packaged CSS bytes, refresh the signed local app/ZIP/checksum, and
confirm app startup. Keep all configuration/data untouched. No model download,
publication, unrelated changes or broader Feature acceptance.

## Results

- Removed whole-row resting/hover/focus/drag tints. Both lists use the existing
  white surface, subtle border and 0/1/2px 5% resting shadow. Control focus and drag
  opacity/insertion cues remain; dimensions and data behavior are unchanged.
- Synthetic rendered before/after inspection and eight style/state/geometry checks
  pass. Both lists retain containment at 1100×800, 320×720 and 700×480. No new test
  files, behavior-suite rerun or backend compilation for this CSS-only correction.
- All 69 bundled data assets match source; strict signatures, ZIP CRC, symlinks and
  extracted inventory parity pass. App/web serve the new CSS, six WebKit startup/
  cookie checks pass and saved settings are byte-identical. Both runtimes remain live.
- Catalog, whitespace and repository privacy checks pass. Task-owned preview,
  build and rollback artifacts are removed at closure. No model download,
  publication or commit; broader Feature/PRD acceptance limits remain.
- [Design evidence](../evaluation/eval-0139-design-standalone-test-app.md#white-rows-and-shadow-lines--2026-10-25)
  and [delivery identity](../evaluation/eval-0139-functional-standalone-test-app.md#settings-row-shadow-lines-delivery--2026-10-25-superseded)
  retain the scoped verification record.
