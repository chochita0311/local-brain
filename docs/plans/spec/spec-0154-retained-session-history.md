# SPEC-0154: Retained Session History

## Metadata

- Status: `approved`
- Feature: [FEAT-0154](../feature/feat-0154-retained-session-history.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md#session-history-retention--2026-10-31)
- Run: [RUN-229](../run/run-20261031-229-retained-session-history.md)
- Execution Profile: `fullstack-product`
- Created: `2026-10-31`

## Contract

Add `source_files.presence_state` (non-null, `UNKNOWN` default, bounded to
`PRESENT/MISSING/UNKNOWN`), `presence_checked_at` and `presence_error`. Existing
rows start unverified; do not infer availability or advance parsing versions from
stored paths. Keep file size/mtime, scan result/error and owned result versions
on absence. Compatible startup preserves IDs and legacy numeric-revision
conversion and remains idempotent. Local Context producers keep their lifecycle.

After revision admission and complete discovery, preserve missing/uninspectable
accepted Session paths as retained source evidence instead of pruning owners.
Read failures are independent from presence: a found file may have scan error.
Complete directory enumeration must surface access failures instead of silently
classifying skipped entries as missing. Source unavailability/failure records
unknown presence without replacing previously normalized content. Cancellation
does not complete an absence observation.

Retired plain/Zstd representations are reconciled after validated replacement;
do not keep false duplicate files merely because a representation was missing.
Provider-excluded artifacts and confirmed-empty input retain
their existing eligibility corrections. No missing-file marker is permission to
clear references, activities, pins, skills or organization.

Contract repair evaluates current selected inputs, not missing historical paths.
Usage replacement unions prior records for Sessions with retained missing inputs
with newly parsed observations, including partially available multi-file Sessions.
It cannot stamp missing inputs current. Reappearance follows ordinary native-ID
upserts and frozen-fact rules; errors retain the previous owner. Source transactions
and source-scoped rollback/admission remain enforced. Provider Session revisions
advance for the new lifecycle; a revision is never fabricated for an unavailable
input. Older executables are not retrofitted with the new retention behavior.

Derive per-Session availability from linked file evidence: a confirmed present
representation yields `PRESENT`; without one, any unverified input yields
`UNKNOWN`; only confirmed absent known inputs yield `MISSING`; no evidence yields
`UNKNOWN`. List and pinned recall label missing/unknown; detail labels all states
and exposes last check/reason. These states do not disable detail or pins and do
not replace Project `경로 없음`. Keep normal reads database-only for availability.

## Required Verification

Synthetic cases cover both native adapters/profiles, missing and unknown roots,
partial directory failure, parsing error with present input, unchanged repeats,
pin edits while absent, restored/renamed native identity, plain/Zstd transitions,
multi-file retained references/Usage, force and mixed normalizer revisions,
newer-revision refusal, confirmed-empty/ineligible correction and additive legacy
migration. Verify actual rendered routes/actions at wide/narrow widths, a packaged
wheel, required repository checks and guarded delivery/preservation in the normal
web runtime. Full native distribution remains outside this feature.

## Open Blockers

None. The owner's explicit implementation instruction approves this bounded
contract; no new automatic deletion or raw-backup behavior is introduced.
