# SPEC-0095: Bounded Work Reconstruction Experiment

## Metadata

- ID: `spec-0095`
- Status: `approved`
- Feature: [FEAT-0095](../feature/feat-0095-bounded-work-reconstruction-experiment.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Run ID: [RUN-20260915-101](../run/run-20260915-101-bounded-work-reconstruction-experiment.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: extraction/scoring → local experiment
- Required Evaluators: `contract`, `functional`
- Attempt: 2
- Created: `2026-09-15`
- Updated: `2026-09-16`

## Source Set And Scope

FEAT-0095 owns bounds and quality targets. PRD-0017 owns outcome/contribution
semantics, minimal intervention, and the legacy transition exclusion. Product,
Architecture, Privacy, `schema.sql`, the current Session reference eligibility,
and FEAT-0090's pure pair module remain current implementation contracts.

Implement an isolated experimental package, explicit script, and synthetic
tests. Do not import application startup/configuration or change any existing
route, table, scheduler, assertion ledger, or normalizer semantics.

## Inputs And Ownership

- Versioned supplied snapshots contain Session metadata, canonical artifact and
  reference facts, and bounded text records. Each record has a stable key,
  source kind, role, optional Session ID, selected-text offset, UTC observation
  time, and text. Keys and span offsets identify evidence, not expected groups.
- Only Session work/primary/full and explicitly admitted Document/Item/owner
  records are eligible. User requests and attributed assistant message text are
  allowed; raw tool records are not. Direct functions reject malformed values,
  duplicates, unknown record fields, and hard-limit overflow.
- Expectations are separate versioned input, bound to the exact snapshot digest,
  with independently named goals, subject/change/completion, allowed labels,
  positive member spans, negative spans, and unresolved counts. They never enter
  extraction. Absent label assessment remains unknown, not correction-free.
- Each expected member is a record key and half-open character interval. A
  predicted statement must be contained in that interval; sharing a Session
  alone does not earn a match. Duplicate annotations or overlapping contradictory
  answers fail validation; scoped multi-goal evidence is explicit.
- Snapshot, expectation, report, and synthetic correction versions are
  experimental and independent of production flow or Episode identifiers.

## Extraction And Grouping

1. Split bounded text into sentence/line statements while preserving offsets.
   Recognize explicit English/Korean goal/change clauses and subordinate phase
   wording. Support a small versioned action vocabulary (reduce, increase,
   improve, fix, add, remove, replace, enable, disable) with explicit linguistic
   variants. A bare topic, URL, imperative to continue, or generic noun is not a
   goal. Unrecognized language is reported unassigned, not guessed.
2. Extract subject and desired change from the goal clause; completion criteria
   and outcome claims are optional source spans, not invented progress. Mark
   normalized action/subject and membership as inferred, original wording and
   locators as observed. Assistant wording stays assistant-attributed.
3. Group only equal normalized subject/change with compatible completion
   criteria. Conflicting explicit criteria split; an unspecified criterion may
   attach only when exactly one explicit outcome is supported. Shared artifacts
   never override conflicting goals. Investigation/implementation/verification
   is a member phase, not a peer flow. Changing resource identities does not
   change a semantic goal key.
4. Experimental IDs hash semantic goal identity, not labels or shared-reference
   pairs. Revisions hash sorted evidence and values. Unrelated append cannot
   alter other flow IDs; source removal cannot invent closure. Surface label
   churn and membership changes separately. These rules are a measured
   prototype, not production identity approval.
5. Optional synthetic corrections specify exact statement keys, a stable target
   correction group, and optional user label. Statement keys bind source record,
   offsets, and exact wording, so even equal-length edits cannot retarget an old
   correction. Unavailable statements remain
   inactive; corrections remain replayable without acquiring future members.
   Never write or reuse the production correction ledger.

## Reference Comparator

Derive qualifying canonical pairs from admitted existing reference facts:
both anchors must occur in at least two eligible Sessions. Feed bounded batches
to the unchanged FEAT-0090 normalizer and combine exact pair identities.
Enforce global 4,096 pairs, 12,000 references, and existing per-call limits.
Do not silently select favorable pairs. Compare all resulting pair memberships,
including their fragmentation; a pair is not automatically a recognized goal.

## Scoring And Replay

- Compute exact integer numerators/denominators for goal recovery, wrong scoped
  assignments, excess matched groups, unsupported groups, assessed correction
  freedom, identity and assignment retention. Never round into a pass; zero or
  unknown denominators yield insufficient evidence.
- Match an expected outcome using its independently declared subject/change/
  completion and supporting spans, not a predicted label. Every emitted
  assignment is correct, wrong, or unassessed. Missing goals remain missing.
- Correction-free requires a unique correctly supported group with an assessed
  acceptable label and no required split/join/reassignment. Unknown label
  acceptability is not success. Unassessed scope blocks complete quality claims.
- PRD targets apply absolutely to the text arm. Report metadata quality without
  requiring that rejected baseline to meet text goals.
- The comparison runs both arms with/without owner organization, unchanged
  replay, and chronological snapshots. Report additions/removals and stability;
  unrelated append, source rename/loss, and corrections have synthetic witnesses.
- `technical`, `quality`, `coverage`, and `viability` are separate. A synthetic
  report is never private viability evidence. Local viability additionally
  requires 40–60 eligible Sessions, ten expected efforts, an effort over 24
  Sessions, weak/no-reference cases, three chronological snapshots, all safety
  witnesses, complete matching/assessment, and every numerical gate.

## Read-Only Local Adapter

- Explicit manifest only: source IDs, UTC start/end, ordered snapshot cutoffs,
  Session IDs, exact event/document/item/organization selections with offsets
  and hashes, and an explicit private output owner/expiry. No default DB path.
- Open an existing SQLite file using a read-only connection, query-only
  enforcement, a read transaction, bounded SQL selections, and an authorizer
  that forbids mutation, attachment, or extension operations. Never use
  `db.connect`, `init_db`, the CLI server bootstrap, or source sync helpers.
- Validate eligibility/permission metadata before selecting text. Use bounded
  SQL substrings for selected spans, compare expected hashes, and retain exact
  source/offset/time attribution. Validate time bounds rather than silently
  adding adjacent records. A source disappearing or permissions changing yields
  incomplete/invalid evidence, never automatic recovery or source expansion.
- Session records come only from selected primary work/full Sessions and
  message events. Context Documents require enabled/readable/ready roots;
  Jira/Wiki content requires indexed coverage and a permitted enabled binding
  when one exists. Read only normalized text, never source-body payloads.
- Optional owner goals use selected Workstream summaries, Thread goals, or
  checkpoint text with selected existing owner relationships. No inferred
  organization becomes source evidence. All selections count against Feature
  caps, and the no-organization variant removes both text and relationships.
- Canonical references use selected Sessions' persisted reference evidence;
  excluded/out-of-scope targets cannot trigger resolution, file reads, or
  connector access. Missing/partial scan coverage stays visible.

## Command And Resource Contract

- `scripts/experiment-work-reconstruction.py` requires either an explicit
  synthetic/supplied fixture or explicit database + manifest inputs, independent
  expectations (or explicit unknown assessment after preparation), and an
  explicit output directory and future expiry for retained
  results. `--help` performs no runtime access. Default stdout/stderr contains
  fixed status codes only; sharing non-identifying aggregate summaries is opt-in.
- A supervised worker performs admission/analysis. Enforce the Feature's wall
  and process-tree memory caps; fail closed on unsupported monitoring. The
  worker starts no child processes. Cancellation kills/reaps its process group.
- Private input, errors, report bodies, paths and IDs never reach default tool
  output. Bound JSON input and output bytes, reject duplicate keys/nonfinite
  values, and publish a result only after complete serialization. Output is a
  newly created owner-only task directory outside the repository in either
  mode, never an overwrite or a symlink. No whole DB backup is created.
- Use no external runtime dependency. Snapshot resource measurements and fixed
  limit/error statuses are distinct from algorithm metrics.
- Retained local result includes its owner/expiry and selected evidence needed
  for review. Temporary files are removed on success/failure/cancel. An existing
  result is not deleted or overwritten by a rerun. No scheduler is added.

## Explicit Current-Data Preparation

The owner selected the currently configured LocalBrain database and its entire
existing history through the invocation time. The operator resolves that named
database from the existing configuration; the command still has no default
database discovery, source crawl, synchronization, or automatic startup hook.

- `--prepare-through <UTC>` with explicit `--database`, `--owner`, expiry, and
  output enables deterministic preparation. It is incompatible with a supplied
  manifest. All source selection happens before either arm's predictions.
- Chronological ordinal sampling includes the earliest/latest eligible Sessions
  and at most 60 total across the existing history, using all eligible source
  instances only when their count is within eight. Sample at most 32 evenly
  spaced message events per selected Session, at most 1,000 leading code points
  each (32,000 per Session); retain hashes and exact offsets. No goal keywords,
  generated labels, expected groups, or favorable-score resampling choose input.
- Related admitted Documents/Items come only from persisted references of those
  Sessions, at most 20 each. Optional owner goal/checkpoint records come from
  existing user-owned Session links, at most 20 total and 200 links. All original
  eligibility, time, text, reference, process, and output caps still apply.
- Freeze up to three chronological observation cutoffs using the selected
  Session start observations and final through-time. This reconstructs only
  retained observed records, not unavailable historical versions of edited text.
- Report population versus selected counts separately. Omitted/truncated text
  and unsupported source timestamps remain incomplete evidence. An optional
  per-snapshot `coverage` field carries preparation omissions through admission
  and replay; it cannot turn downstream partial reference coverage complete.
- Explicit `--unassessed` may supply only a digest-bound unknown-assessment
  placeholder: no groups, no negative labels, and a nonzero unresolved count.
  It enables a local execution check without an answer key; it cannot establish
  extraction accuracy, correction freedom, or viability. The report identifies
  this assessment state and retains the frozen private manifest for audit.
- Preparation runs under the same supervised resource and private-output
  boundaries. Missing independent expectations are not a request for the owner
  to classify the whole sample, and are not replaced by model or hosted analysis.

## Local Invocation And File Shapes

The command can prepare a bounded manifest after explicit scope selection; it
does not author an independent answer key. Freeze inputs independently of either
arm's output under that local scope.
No whole-sample naming/assignment task is delegated to the owner. Missing input
or unassessed cases remain a validation gap; do not synthesize an answer key
from the extractor or repeatedly expand the approved review batch.

After that preparation, the local invocation is:

```text
python scripts/experiment-work-reconstruction.py --database <absolute-existing-db> --manifest <private-manifest.json> --expectations <private-expectations.json> --output-dir <absolute-new-private-directory>
```

- Manifest root: `version: 1`, `source_ids`, timezone-qualified `start`/`end`,
  `owner`, future `expires_at`, and `snapshots` (at most 12).
- Each snapshot: unique `name`, ordered `as_of`, `session_ids`, `events`,
  `documents`, `items`, `organization`, and `organization_links` arrays; optional
  `coverage` carries preparation's `complete`/`unexamined` values.
- Each text selection: `id`, half-open Unicode-code-point `start`/`end`, and
  `sha256` of the exact selected UTF-8 text. Organization selections also carry
  `table` (`workstreams`, `threads`, or `checkpoints`). Event IDs are persisted
  event identities; Item IDs are existing External Resource IDs. There is one
  selection per source record. Links are existing user-owned link IDs only.
- Supplied fixture alternative: `--fixture <snapshot-bundle.json>` replaces
  database/manifest and requires `--owner`/`--expires-at`. Its root is
  `{version: 1, snapshots: [...]}` using the supplied snapshot shape implemented
  in `validate_snapshot`. No database is opened in this mode.
- Expectations root: `{version: 1, snapshots: {<name>: <answer-key>}}`. Each
  answer key contains `version: 1`, `snapshot_digest`, `groups`, `negative`, and
  `unresolved`. Groups contain independently authored `key`, `subject`, `change`,
  optional `completion`, `members`, and `acceptable_labels` (null if unassessed).
  Each positive/negative span has `record_key`, `start`, and `end`.
- Digests use SHA-256 over UTF-8 JSON with sorted keys, compact separators,
  unescaped Unicode, and no nonfinite numbers. The independent preparation must
  bind the exact admitted snapshot, including coverage; hashes are transport
  integrity, not permission or evidence of independent labeling.
- Output: private `comparison.json` with owner/expiry, per-arm groups and
  evidence, scores, resources, chronological stability, and required review.
  `assessment` distinguishes supplied expectations from unassessed execution;
  prepared runs also retain `input_manifest` and preparation counts locally.
  Fixed default statuses are `EXPERIMENT_RECORDED`, `EXPERIMENT_FAILED`, and
  `EXPERIMENT_CANCELLED`. Exit 0 means a report was recorded, not useful flows.
  `--share-summary` explicitly opts into non-identifying aggregate output.
- The report always leaves `viability` unverified: an evaluator must still
  reconcile private expectation independence, mandatory synthetic evidence,
  weak-reference cases, and unrelated-append stability. Numeric `private_quality`
  is only one input to that verdict; a recorded report is not an evaluator receipt.

Executable synthetic shape examples and full database-mode invocation tests
live in `tests/work_reconstruction_cases.py` and
`tests/test_work_reconstruction_input.py`; they contain no private corpus.

## Acceptance Mapping And Verification

| Feature guarantees | Evidence |
| --- | --- |
| 1–3: actual scoped extraction and comparison | independently authored natural-language fixtures; English/Korean, mixed goals, changed references, >24 Sessions, incompatible outcomes, held-out paraphrases |
| 4: honest scores/coverage | zero/unknown denominators, false/duplicate/fragmented assignments, no-org comparisons, unassessed corrections, invalid expectation digests |
| 5: stable experimental state | unchanged rebuild/order shuffle, unrelated append, renamed/late/removed evidence, exact-scope correction replay |
| 6: bounded read-only operation | real-schema synthetic SQLite, excluded content, write/DDL/bootstrap/network guards, manifests/hashes/time/bounds/errors/output/cancellation |
| 7: no inflated viability | synthetic-only/unrun private/insufficient/limited cases never yield full private viability |

Use focused unittests first, the existing full regression after integration,
plan catalog/link checks, privacy scanner, and whitespace checks. Track actual
results in separate Contract/Functional reports; do not substitute this Spec
for executed evidence. No browser evidence is required because no UI changes.

## Open Blockers

- The named current database and through-now scope are resolved by the owner.
  Independent expectations remain absent; this blocks a full quality/viability
  verdict, but not bounded preparation or an explicitly unassessed execution check.

## Continuity Notes

- `2026-09-15`: implementation contract accepted under owner-approved FEAT-0095.
  Prototype language coverage is deliberately measured and limited; no general
  semantic or whole-corpus quality is assumed.
- `2026-09-16`: owner resolved the database/time scope by naming current
  LocalBrain data through now. Defined deterministic preparation and explicit
  unknown assessment within the existing caps; no quality gate was relaxed.
