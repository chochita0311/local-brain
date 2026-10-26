# run-20261024-196-source-primary-key-identity

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Active Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md#source-primary-key-only--2026-10-24)
- Execution Profile: `backend-product`
- Surface Lanes: schema/config migration; ingestion and references; consumers; local delivery
- Required evaluations: Contract, Functional; existing screen interaction regression

## Approved Correction

The owner rejects retaining a second profile identifier for compatibility.
`sources.id` is the sole profile identity, `provider_kind` identifies the tool,
and `name`/display label is editable presentation. Home/root, color/order and scan
health retain their separate responsibilities. Remove the redundant `sources.kind`
column and active alias resolution rather than replacing it with another alias.
This supersedes Run 195's internal legacy namespace decision.

## Implementation And Invariants

1. Convert dependent structured references once, then rebuild the registry without
   its string identity. Preserve source/session PKs, originals, recorded evidence,
   usage attribution, pins and presentation. No permanent alias table/column.
2. Ingestion matches existing events/usage through their existing natural unique
   keys and retains their opaque record PKs. New identities use the source PK.
   Skills use a source FK; chart scopes, current settings and filters use that PK.
3. Remove old-key API/filter fallbacks and duplicate fields from current profile
   configuration and read models. Update shared consumers, including disabled
   development surfaces, without activating them or changing their scope.
4. Validate migration/repeated scan, same-provider profiles, invalid files,
   rollback, stored references and UI continuity on synthetic data and a private
   copy of the actual database before actual migration and app replacement.
5. Rebuild offline, verify the packaged runtime and actual startup, update owner
   docs/evidence, and remove task-owned temporary artifacts. No publication,
   model download, dependency upgrade or unrelated cleanup.

## Baseline And Evidence

The pre-change dirty workspace is snapshotted privately for comparison; Run 195
owns the previous delivered artifact. Full-suite baseline has four known
documentation/inventory failures. Record actual outcomes and limits below;
successful construction alone does not establish migration or runtime correctness.

## Results

- Removed `sources.kind`, current profile `source_key` DTO/config fields and live
  alias lookups. Skills now reference the source PK through a physical FK. Chart
  scopes, workflow boundaries, analysis usage settings and cached sync reports
  migrate once. Provider/domain classifications and opaque record PKs retain
  their distinct meanings; frozen report artifacts remain historical evidence.
- Re-ingestion matches native unique keys and preserves imported event/usage IDs.
  Name, color and TOML-array ordering continue to propagate to Settings, Sessions
  and Session Dashboard. Home/root, provenance, pins, attribution and scan health
  retain their existing contracts; no replacement identity or alias table exists.
- All 17 profile behavior tests pass, including invalid/ambiguous input, failed
  migration rollback, reconnect recovery, repeated startup and cached sync clocks.
  The final focused profile/scheduler/desktop group passes 61 tests. The full suite
  runs 1,238 tests with the same four pre-existing learning-table/documentation
  inventory failures established by the Run 195 baseline; no clean-suite claim.
- Source WebKit passes 25 profile/route checks; the final packaged backend passes
  26, adding cached-report PK migration. Existing Run 195 geometry/physical-input
  evidence limits remain. No visible layout redesign was introduced.
- A private actual-data copy and then the stopped actual database pass all-table
  row-count and unaffected-row digest comparisons, retained source field/ID
  comparisons, repeated-startup idempotency, integrity and foreign-key checks.
  General, Session and search configuration files remain byte-identical; cached
  sync report references change while their clocks, outcomes and counts remain.
- The first actual migration attempt stopped at the exclusive backend lock before
  any data write because a separate local web server was running. Both existing
  runtimes were stopped before backup/migration. The app and original web address
  were restored afterward and both expose numeric-only current profile metadata.
- Offline frozen build retains the dependency lock and native source; all 104
  bundled local modules match current source code. Private-path checks, strict
  ad-hoc signatures, ZIP CRC, internal symlinks and extracted inventory parity pass.
  Actual app startup passes six WebKit checks, health, numeric settings, parity
  for 18 served assets, unchanged configuration and one native/backend instance.
  The model worker remains idle; no model download, publication or commit.
- [Contract receipt](../evaluation/eval-0139-contract-standalone-test-app.md#source-primary-key-only-contract--2026-10-24)
  and [functional delivery receipt](../evaluation/eval-0139-functional-standalone-test-app.md#source-primary-key-only-delivery--2026-10-24-superseded)
  own the final contract, artifact identity and broader acceptance limits.
- Generated schema/value dictionaries, JavaScript syntax, plan catalog, whitespace
  and repository privacy checks pass. Task-owned verification processes and
  temporary copies/builds/probes are removed at closure; durable outputs are the
  final app/ZIP/checksum, owner documents and the policy-managed recovery backup.
