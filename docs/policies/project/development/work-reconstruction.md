# Work Reconstruction Operations

Use the [shared model-tool prerequisites and private storage rules](model-tools.md) before these operations.

## Operations

An isolated non-model tool compares reference-pair grouping with explicit
Korean/English goal extraction. It does not replace the current Workstream UI
or change its data. Inspect its options without opening runtime storage:

```bash
uv run --no-sync python scripts/experiment-work-reconstruction.py --help
```

Execution accepts an explicit supplied fixture or an existing database plus a
frozen selection manifest. After selecting an existing database and through-time,
`--prepare-through <UTC> --unassessed` can prepare a deterministic bounded sample
and check execution without an answer key. It covers the selected population's
whole existing time range, not every record, and reports omissions explicitly.
Scored quality still requires separate source-bound expectations. Results need
a new private output directory outside the repository and an owner/expiry;
default output contains status codes only. No private database is opened by
default, and predictions never become the answer key. The current
[Work Reconstruction contract](../work-reconstruction.md#isolated-work-reconstruction-experiment)
owns the wire shapes, caps, source permissions and assessment boundaries; the
invocation and file shapes below describe this command.
Synthetic correctness is not evidence that real work is reconstructed usefully.

### Model-Free Invocation And Files

Choose exactly one input mode. All paths below are explicit local paths; use a
new absolute output directory with an existing canonical nonsymlink parent
outside the repository. Set `RECONSTRUCTION_EXPIRES_AT` to an explicit future
aware ISO timestamp before a supplied-fixture or preparation invocation.

```bash
uv run --no-sync python scripts/experiment-work-reconstruction.py \
  --fixture /absolute/private/fixture.json \
  --expectations /absolute/private/expectations.json \
  --output-dir /absolute/private/new-fixture-result \
  --owner reconstruction-review --expires-at "$RECONSTRUCTION_EXPIRES_AT"

uv run --no-sync python scripts/experiment-work-reconstruction.py \
  --database /absolute/private/localbrain.db \
  --manifest /absolute/private/selection.json \
  --expectations /absolute/private/expectations.json \
  --output-dir /absolute/private/new-scored-result

uv run --no-sync python scripts/experiment-work-reconstruction.py \
  --database /absolute/private/localbrain.db \
  --prepare-through '2026-09-15T00:00:00+00:00' --unassessed \
  --output-dir /absolute/private/new-unassessed-result \
  --owner reconstruction-review --expires-at "$RECONSTRUCTION_EXPIRES_AT"
```

The preparation cutoff is an explicit scope choice, not a default or permission
to open another database. Preparation requires database mode, `--unassessed`,
and no manifest or expectations. Other database runs require a manifest;
supplied-fixture and scored database runs require an independent expectations
file. The selected manifest supplies database-mode owner/expiry. Fixture and
preparation modes require explicit owner/expiry arguments. Expiry must be later
than the current time, and preparation also requires expiry after its cutoff.
No invocation creates missing database/schema/source state.

| File | Current shape and validation |
| --- | --- |
| Supplied fixture | Exactly `{"version":1,"snapshots":[...]}`; 1–12 distinct named snapshots obey the [current snapshot contract](../work-reconstruction.md#reconstruction-input-and-bounds) |
| Private selection | Exactly `version`, `source_ids`, `start`, `end`, `snapshots`, `owner`, `expires_at`; version 1, ordered snapshot cutoffs, one bounded hash-verified selection per record and the source/permission predicates in [Reconstruction Input And Bounds](../work-reconstruction.md#reconstruction-input-and-bounds) |
| Expectations | Exactly `{"version":1,"snapshots":{"snapshot-name":...}}`; names exactly match all supplied snapshots. Each version-1 answer key binds `snapshot_digest` and independently supplies `groups`, `negative`, `unresolved`; group/member/label bounds and contradictory-span refusal are in [assessment](../work-reconstruction.md#reconstruction-output-and-assessment) |
| Result | One new `comparison.json`, encoded at most 10 MiB, wrapped as `owner`, `expires_at`, `report`; directory mode 0700/file mode 0600. Existing output is never replaced; a failed write removes only paths created by that invocation |

JSON inputs must be existing nonsymlink files no larger than 10 MiB; duplicate
keys, non-finite constants, malformed data and hard-bound overflow refuse.
Answer keys are validated against every frozen snapshot before either arm runs.
The command compares text and metadata with/without organization, checks
unchanged replay, and records scores, source/expectation digests, resource
measurements and chronological stability. Results include `technical`,
`input_kind`, `private_quality`, `viability`, `snapshots`, `history`, `sample`,
`required_review`, `admission_resources` and `assessment`; preparation adds its
frozen `input_manifest` and omission/sample metadata. `assessment: unassessed`
retains unknown expectations and cannot pass quality; fixture execution cannot
establish private quality. `viability` remains `unverified` even after technical
success. The [finite human-review allowance](../privacy-and-data.md#local-persistence)
is separate and is never renewed by these commands.

Each admission, extraction, comparator or scoring worker has a 120-second wall
limit and 512-MiB peak-RSS bound, with monitor availability checked fail-closed;
cancellation/failure terminates and reaps only its task-owned worker. The command
opens no native file, source parser, connector or model. It adds no background
retention scheduler or full database copy. Owner-managed expiry cleanup remains
required for retained results. Standard output is only `EXPERIMENT_RECORDED`
(exit 0), `EXPERIMENT_FAILED` (exit 2), or `EXPERIMENT_CANCELLED` (exit 130).
Only explicit `--share-summary` replaces the success code with the non-identifying
`technical`/`private_quality`/`viability` summary; private payloads never print.
