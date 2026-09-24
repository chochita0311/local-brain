# SPEC-0097: Replayable Full-Session Simulation

## Metadata

- ID: `spec-0097`
- Status: `approved`
- Run: [RUN-20260923-113](../run/run-20260923-113-full-history-simulation-replay.md)
- Attempt: `1`
- Parent Feature: [FEAT-0097](../feature/feat-0097-replayable-session-simulation.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, then `infra`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-22`

## Source Set And Boundary

The owner's full-data/recalculation request and FEAT-0097 govern this increment.
Session body eligibility and local privacy remain owned by project policies.
No browser, source ingest, source schema, existing preview or organization
behavior changes. Run only from an explicit database/output/model selection.

## Implementation Contract

- Stream a read-only transaction into private current-inventory tables. Cover
  every eligible nonempty user/assistant message in non-overlapping character
  chunks, not a chronological sample. Keep stable Session/source and event/span
  keys, content hashes, role and observed date; do not persist full source text.
- Missing/invalid dates remain unknown and do not remove a Session or close work.
  Source identity incorporates provider/native identity, not reusable row ID alone.
- Separate current inventory, content-addressed vectors, grouping report and
  run-progress metadata. Bind output to the selected database. Unknown output
  ownership and symlinks fail closed. Hold a nonblocking output lock for writes.
- Cache namespace includes verified asset fingerprint, library/device versions,
  dimensions, token windows and character extraction version. Verify model files
  before reading private content; local-files-only and telemetry/offline settings
  precede library import. Read existing assets; never invoke installation.
- Encode missing vectors in bounded batches, validate dimensions/finiteness,
  and commit each batch. Resume does not trust a mere done flag: compare current
  input hashes with cache keys. Force recomputation is an explicit command mode.
- Content changes replace current inventory atomically, clear unused vectors,
  and invalidate the current-report relationship. Revalidate the complete source
  fingerprint before publishing; concurrent change fails with a fixed code.
  Frozen manifests verify original indexed data; they are not historical body
  backups and cannot replay overwritten source bytes without that source.
- Group compatible vectors through a bounded-neighbor cosine graph and seeded
  community detection at two resolutions. Query neighbors in bounded batches,
  not a materialized all-pairs matrix. Parameters are explicit and versioned;
  similarity is never a causal edge. No fixed global group count or top-N loss.
  Record all singletons, multiple memberships, source-attributed representative
  labels and unknown lifecycle. Larger communities are experimental work-area
  candidates; inner communities are work candidates, not confirmed categories.
  Session titles supply explicitly source-attributed representative labels;
  these are not generated or confirmed names for the entire community.
- `report.json` is atomic, private and complete, with source/configuration
  digests, model identity, coverage, groups, unassigned counts, cache statistics,
  prior-run comparison and `quality: unassessed`. Keep at most one previous
  report for comparison/recovery. Normal stdout contains fixed status codes only.
- Derived state has a 30-day inactivity expiry. An explicit purge removes only
  known owned state under lock; stale results are never published as current.
  Access/replay enforces expiry; no background scheduler is implied. Interruption
  retains checkpoints for resumption. Command-created transient files are always
  removed; original sources and external model caches are never purge targets.

## Acceptance Mapping And Evaluation

Synthetic tests cover over 60 Sessions, over 32 messages, long tails and missing
timestamps; full character coverage; unchanged replay, interrupted batch resume,
changed/deleted/reclassified sources, grouping-only changes, model namespace
changes, source changes during inference, deterministic grouping, exclusive
locks, unknown ownership, symlinks and source byte preservation. A real private
run establishes processing coverage only, not semantic usefulness. Tests use an
injected deterministic encoder; a separate installed-model smoke check proves
the actual local runtime boundary.

## Open Blockers

None for the simulation contract. Grouping parameters and labels are experiment
variables; production semantics, identity continuity, UI and quality remain
downstream work, not silently assumed resolved.

## Continuity Notes

- `2026-09-23`: unchanged contract resumed under RUN-113 to close real replay
  evidence before the owner-authorized whole-history UI. RUN-103 remains the
  historical implementation/backfill record. No new model or source boundary.

## Implementation References

- [Sentence Transformers local model and encoding API](https://sbert.net/docs/package_reference/sentence_transformer/model.html)
- [scikit-learn nearest-neighbor API](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html)
- [NetworkX seeded Louvain communities](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html)
