# SPEC-0090: Workstream Candidate Discovery Contract

## Metadata

- ID: `spec-0090`
- Status: `approved`
- Run: [RUN-20260915-100](../run/run-20260915-100-workstream-candidate-discovery-contract.md)
- Attempt: `1`
- Parent Feature: [FEAT-0090](../feature/feat-0090-workstream-candidate-discovery-contract.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: none
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-15`
- Updated: `2026-09-15`

## Current Applicability

This remains the approved historical contract of the unchanged pure pair
module. It does not specify automatic outcome-level reconstruction. Subsequent
owner review returned the product boundary to
[PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#reconciliation-and-approval-state)
and superseded FEAT-0091–0094. References below to the former next producer
describe the original split, not current execution authorization.

## Source Set

- Owner approval of FEAT-0090's proposed baseline on `2026-09-15`.
- Approved Feature/PRD boundary, passed Episode identity and reference contracts.
- Product, Architecture, Privacy, and Workspace/Session Activity owner docs.
- Existing immutable descriptor, length-delimited identity, UTC normalization,
  and deterministic abstention patterns in `workflow_projection.py`.

## Implementation Goal

Add `workstream_candidates.py`, a pure validation/normalization contract for
supplied candidate pairs and their evidence. Finding pairs in the database,
choosing a corpus scope, and collecting source facts belong to FEAT-0091.

## In-Scope Behavior

### Input And Identity

- `WORKSTREAM_CANDIDATE_VERSION` is `localbrain.workstream-candidate.v1`.
- Factories produce frozen artifact, Session, and reference descriptors from
  normalized mappings; batch normalization accepts mappings and proposed
  artifact-key pairs. Factories raise fixed `ValueError` messages on malformed
  inputs; batch normalization counts invalid facts and abstains.
- `candidate_artifact_key(kind, source_scope, source_identity)` uses a
  length-delimited SHA-256 digest and an `artifact:` prefix. Kinds are
  `context-document`, `jira-item`, `wiki-item`, `local-resource`, and
  `external-resource`. Source scope and identity are supplied canonical facts,
  never resolved by filesystem or URL access in this module.
- Producer identity recipes are:
  - Context Document: stable Local Context source key plus normalized,
    source-relative document path;
  - Jira Item: normalized Site domain plus the persisted canonical issue key;
  - Wiki Item: normalized Site domain plus canonical Page ID;
  - local/external Resource: its existing canonical local path or safe URL in
    the corresponding resource namespace. Known Document/Atlassian aliases use
    that resolved owner's kind and identity instead of a second Resource key.
- Producers must reconcile aliases through existing owners before constructing
  a fact. Current SQLite IDs, alternate URLs, labels, and imported timestamps
  cannot be stable artifact identity. The contract performs no fuzzy matching,
  Site discovery, URL inference, or cross-source basename matching.
- Session identity reuses `workflow_episode_key(source_key, external_id)`.
  The Session factory requires `work`, `primary`, `full` index policy, positive
  local ID, and meaningful activity (`event_count > 0`, supplied
  `has_activity_events`, or supplied `has_usage_records`). Boolean flags are
  strict; unknown eligibility does not default to true.
- A reference supplies opaque Episode/artifact keys, a source-native occurrence
  identity, evidence kind, read outcome, and source-observed time. Its opaque
  `reference:` key hashes the Episode, artifact, and occurrence identity. Local
  reference-row IDs and import times are not occurrence identities.
- Identity strings are nonempty, contain no control characters, and are bounded
  to 4,096 code points; source keys/scopes are bounded to 300. Titles are
  optional attributed metadata, bounded to 500. Raw identities never serialize.

### Admission And Normalization

- `normalize_workstream_candidates(artifacts, sessions, references, pairs,
  coverage=...)` validates the supplied pairs; it does not enumerate missing
  pairs or discover a corpus. Reversed/duplicate pairs collapse to one seed.
- A seed requires two distinct resolved, enabled, non-container artifact keys.
  Unresolved/ambiguous artifacts remain excluded; current, stale, missing, and
  unavailable retained artifacts keep separate freshness/availability cues.
- Reference kinds are `user_mention`, `assistant_mention`, `resource_read`, and
  `tool_result`. Mentions require no read outcome; read evidence requires
  `success`. Failed/missing read outcomes cannot qualify membership. Explicit
  organization, workspace, Git, wording, and recency are not reference kinds.
- Every member independently has admitted references to both anchors. At least
  two distinct stable Episode keys are required; duplicate rows, aliases, or
  repeated references in one Session cannot meet the threshold.
- Only those two anchors' supporting references enter each membership. Other
  Session evidence is excluded. Distinct seeds retain independent membership;
  shared Sessions/anchors never cause a transitive merge.
- Identical facts collapse by stable identity. Conflicting normalized facts
  with one identity are omitted with a conflict diagnostic, rather than choosing
  a title, destination, or timestamp by input order.
- Diagnostics are sorted fixed codes with counts, never raw input/exception
  text. Missing endpoints, invalid/weak references, insufficient support,
  invalid pairs, and source exclusions remain distinguishable.

### Output, Rebuild, And Time

- Frozen candidate descriptors carry two anchors, a provisional label and its
  source anchor, members/reasons, observed bounds, latest supporting references,
  overlap, and `membership_revision`. Normalized results carry coverage,
  diagnostic counts, and a separate full-result `revision`.
- A `candidate:` key hashes the contract version and sorted anchor keys. Added
  members, local row IDs, title changes, ordering, and source freshness cannot
  change that seed key. A version change creates a new namespace.
- Membership revision hashes the candidate key and all admitted member Episode
  keys and supporting reference keys/kinds/times. It excludes title, local row
  ID, and source freshness. The result revision also observes presentation,
  source state, coverage, and diagnostics so consumers can reject stale reads.
- Label precedence is Context Document, Wiki Item, Jira Item, local Resource,
  external Resource, then artifact key. The first available title wins with
  `source-metadata` attribution. With no title, use `Unnamed work candidate`
  with `fallback` attribution; never synthesize intent or outcome.
- Observation bounds and latest references use only admitted references'
  source-observed times, normalized to UTC. Invalid/missing timestamps remain
  unknown and are counted; Session start/end, source import, and wall-clock time
  do not stand in for candidate progress.
- All admitted known timestamps contribute to bounds, including evidence beyond
  the serialized samples. Latest reference ties retain a total and a bounded
  sample. Unknown-time counts prevent a latest known observation from implying
  that all activity is ordered.
- Candidate authority is always `deterministic-candidate`. Outcome and next
  action are absent; lifecycle/activity are `unknown` and closure reason absent.
  No main path, causal edge, assertion, or universal single tip is inferred.
- Overlap descriptors identify another candidate and counts of shared anchor
  and Session keys; they do not redefine either membership.

### Bounds And Coverage

- Hard limits are 2,000 artifact facts, 2,000 Session facts, 20,000 reference
  facts, 200 proposed pairs, and 2,000 output memberships across the result.
  The normalizer reads at most each input limit plus one. Exceeding a hard bound
  raises `CandidateLimitError` with a fixed message and returns no partial
  success; it does not accept an order-dependent prefix.
- A member retains up to five reference samples per anchor, sorted by known
  source time descending then opaque key, plus full reference totals,
  known bounds, and unknown-time counts. Candidate latest-reference samples
  retain at most five ties; overlap samples retain at most 20 with full totals.
- Coverage describes only the supplied producer scope. Its default is partial
  with unknown unexamined Session count. `complete=True` requires an explicit
  zero unexamined count. A nonempty result may be partial, and an empty partial
  result does not mean the whole corpus has no candidate.
- No wall-clock value, source scan, persistence, query, model, or background
  operation occurs on import, normalization, or serialization.

## Out-Of-Scope Behavior

Database discovery, pair enumeration across the corpus, source/URL resolution,
body parsing, persistence, schema/value-registry changes, routes, UI, correction,
promotion, Lens, Atlas, new adapters, and models remain outside this Feature.

## Affected Surfaces

- `src/localbrain/workstream_candidates.py`
- `tests/test_workstream_candidate_contract.py`
- Product, Architecture, Privacy, and Workspace/Session Activity owner sections.
- FEAT-0090, this Spec, RUN-20260915-100, evaluations, and planning navigation.

## State And Interaction Contract

No user interaction changes. Invalid facts produce bounded omission diagnostics;
hard processing bounds fail explicitly. User-owned state is neither accepted as
inference authority nor changed by normalization.

## Data And Contract Assumptions

The producer owns canonical source/alias resolution, actual eligibility facts,
and corpus coverage. This contract verifies supplied membership evidence; it
cannot prove remote truth or whole-corpus discovery from those inputs. Changing
a canonical source identity may invalidate a future review, never retarget it.

## Contract Surfaces

- Producer: canonical facts, explicit pairs, eligibility, and honest coverage.
- Consumer: opaque seed identity, separate revisions, evidence counts/samples,
  source state, unknown time, abstention, and inferred authority.
- Generated artifacts: planning catalog and schema-presentation/audit source
  digests after the semantic owner update; no schema objects or audit decisions
  change.
- Source-of-truth owner: pure module and the four named project owner docs.
- Stale-assumption check: existing Focus and organization must not consume the
  new contract, and no new persistence or source-operation dependency may appear.

## Acceptance Mapping

- Two artifacts/two Sessions → exact seed/member checks and negative controls.
- Many-to-many and no transitive union → mixed-Session/overlap cases.
- Rebuild/alias stability → scoped key, duplicate, rename, row-ID, added-member,
  source removal/restoration, and permutation tests.
- Honest observation/source coverage → invalid time, late import, stale/missing,
  partial/empty, sample totals, and hard-limit checks.
- Pure, private, source-safe contract → serialization, no-I/O/import evidence,
  unchanged-input checks, owner audit, relevant regression and privacy checks.

## Required Evaluators

- Contract: identity, admission, authority, bounded output, producer/consumer
  ownership, source safety, and owner/generated-artifact parity.
- Functional: deterministic synthetic normalization and all named edge cases;
  complete Python regression suite for the additive module.
- Design and UX heuristic: not applicable; no visible interaction changed.

## Evaluation Focus

Keep correctness of the pure contract separate from FEAT-0091 database discovery
and FEAT-0092 usefulness. No browser or real private corpus result is claimed.

## Open Blockers

- None within the approved Feature boundary.

## Continuity Notes

- `2026-09-15`: the Orchestrator accepted this implementation contract for
  RUN-20260915-100 after the owner approved FEAT-0090.
