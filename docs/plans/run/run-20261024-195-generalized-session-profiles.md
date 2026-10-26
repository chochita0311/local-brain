# run-20261024-195-generalized-session-profiles

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Active Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md#generalized-session-profiles--2026-10-24)
- Execution Profile: `fullstack-product`
- Surface Lanes: numeric identity/config migration; profile presentation/read models; settings palette/reorder; browser/frozen delivery
- Required evaluations: Contract, Functional, Design, Interaction

## Approved Boundary

The owner approves numeric existing DB identity, configurable profile colors,
TOML-array display ordering and shared metadata across settings, Sessions and
Session Dashboard. Preserve imported history, source/session IDs, attribution,
pins, custom paths and local storage. No extra UUID or user-facing string key.
Apply screen-alignment extend. Prior tests and local app replacement authorization
remain; no external publication, model download or unrelated feature activation.

## Contract Decisions

The compatibility namespace decision below records this historical delivery.
[Run 196](run-20261024-196-source-primary-key-identity.md) supersedes it by removing
the redundant column and migrating its live dependents to the existing source PK.

- Version-2 Session TOML uses source_id (the existing positive integer sources.id),
  provider_kind, display_label, root, optional agent_home/enabled and palette color.
  Array order is the display authority, without an independent order setting.
- Preserve existing sources.kind only as an internal compatibility namespace for
  already imported event/usage identities and old links. New profiles derive that
  internal namespace from their numeric ID, never a separate random key. Public
  profile configuration/API and new filter links use numeric IDs.
- Migrate valid version-1 files with existing numeric IDs and current visible
  order/colors retained. Invalid files remain intact. DB projection columns cache
  color/order from TOML; retained omitted profiles follow configured ones.
- Initial palette: green, blue, orange, yellow, red, gray using existing tokens.
  Provider controls CX/CL; user choice controls profile color across source cues.
- Reorder via a drag handle and keyboard movement; update on drop, revision-check
  and validate the exact configured ID set. Color changes use the same save/readback
  boundary. Preserve active source selection and return focus after rerendering.
- Home derives the normal collection folder. Reconnection is required when an
  existing profile's actual collection root changes; custom-root Home-only edits
  do not relocate records. Existing duplicate/overlap and evidence checks remain.
- New ID allocation, rename, color/order updates and removals cannot modify native
  transcripts or recreate imported records. Failed persistence restores the prior
  config/DB state; ambiguous responses are read back before any retry.

## Verification

Meaningful synthetic migration and reingestion tests must establish preserved IDs,
record counts, frozen usage and pins. Check duplicate/invalid IDs/colors/orders,
restored IDs, manual-file reload, stale revisions and failed writes. Verify shared
labels/colors/order and current selection in browser and frozen WebView at wide,
narrow and short sizes. Rebuild backend offline, verify package paths/signatures,
replace/relaunch actual app with before/after metadata invariants, and clean owned
scratch. Existing broader native/recipient acceptance limits remain explicit.

## Results

- Numeric DB PKs now identify profiles in v2 TOML, settings APIs and new source
  filters. Migration preserves the legacy ingestion namespace internally and
  retains existing visible order/colors. Same-provider profiles remain distinct.
  Missing v2 color uses the provider default; DB metadata is only a projection.
- Shared names, six palette colors and TOML-array order update settings, Sessions
  and Session Dashboard without losing the selected profile. Drag/keyboard moves,
  accessible color names/focus, stale revisions, failed writes and lost-response
  readback were exercised. Home-only edits preserve unchanged custom roots.
- All nine profile behavior tests pass, including migration/reingestion identity,
  frozen usage/pins, duplicate/invalid inputs, restored IDs, manual-file projection,
  provider scans and post-replacement rollback. The full suite ran 1,230 tests with
  four pre-existing failures reproduced from the pre-change snapshot: learning
  table inventory in data-model docs/schema audit and the value-family count.
  Relevant desktop/source/UI tests, JS syntax, generated metadata and privacy
  checks pass. These four historical failures are not reported as a clean suite.
- Source Chromium and final frozen WKWebView pass profile interactions and
  wide/narrow/short geometry. The final frozen run has 24 interaction and 33
  geometry assertions; dashboard/chart/detail checks also verify numeric scope,
  label/color propagation and retained selection. Six startup checks pass for
  both the frozen fixture and replaced actual app.
- Actual local migration compares every application table's row digest before and
  after (excluding FTS shadow tables and newly projected source presentation).
  Existing source identities, record rows and provenance are identical; integrity
  and foreign keys pass. General/search configuration bytes remain unchanged.
- Rebuilt the bundled backend offline, checked raw/compressed private paths,
  renewed and verified ad-hoc signatures, and verified ZIP CRC, internal symlinks
  and extracted inventory parity. Replaced and relaunched the local app; health,
  numeric settings, served assets and one native/backend instance pass. Version
  remains 0.0.1. No model download, external publication or Git commit.
- Task-owned synthetic servers, probes, scratch and intermediate artifacts were
  cleaned after verification. The final app/ZIP/checksum are the durable outputs.
- [Contract receipt](../evaluation/eval-0139-contract-standalone-test-app.md#generalized-session-profile-contract--2026-10-24),
  [functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#generalized-session-profiles-delivery--2026-10-24-superseded),
  and [design/interaction receipt](../evaluation/eval-0139-design-standalone-test-app.md#generalized-session-profiles--2026-10-24)
  own detailed evidence and final artifact identity. Physical native input,
  VoiceOver, picker/Notes permissions and recipient-Mac acceptance remain outside
  this scoped pass; the broader Feature acceptance status is unchanged.
