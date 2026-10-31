# Workstream Candidates

This contract owns the pure supplied-fact candidate boundary, eligibility, identity, coverage and serialization. It admits no discovery, review, promotion or organization consumer.

## Candidate Meaning And Authority

- A provisional Workstream candidate is a versioned, in-memory descriptor of
  one proposed pair of canonical artifacts supported by at least two distinct
  eligible primary work Sessions. The pure contract validates supplied facts
  and pairs; it has no database-discovery or candidate-review consumer. The
  contract is not admitted as a replacement Workstream experience.
- Every member independently references both artifacts. A Session may support
  several candidates through different evidence, and shared Sessions/artifacts
  do not transitively merge their boundaries. Existing organization is not a
  prerequisite and cannot stand in for direct reference evidence.
- Artifact aliases count once. Disabled, unresolved, ambiguous, or container
  anchors cannot qualify; failed-read-only evidence cannot create membership.
  Retained stale/missing evidence keeps its source-state labels.
- The seed key is independent of labels, local row IDs, and later members.
  Membership revision records evidence changes separately from source freshness
  and presentation. Provisional labels are attributed source metadata or an
  explicit unnamed fallback, never an inferred goal or confirmed Workstream.
- Candidate observation spans and latest known references use supporting
  reference times only. Missing time stays unknown; Session end and import time
  do not prove progress, a single causal tip, or completion.
- Source observations and inferred membership retain separate authority.
  Coverage refers to the supplied facts and defaults to partial. Hard bounds
  fail explicitly; bounded reference/overlap samples retain full counts.
- The contract changes no current screen, source, global Focus assertion,
  Workstream, Thread, link, or Suggestion. It grants no durable review or
  promotion authority and has no model, remote, or persistence operation.

## Workstream Candidate Contract

- `workflow/candidates.py` owns `localbrain.workstream-candidate.v1`.
  Producers supply canonical artifact/Session/reference facts and proposed
  pairs. The module validates their evidence; it neither enumerates a corpus
  nor resolves a URL, path, Site, or alias through I/O.
- Artifact keys hash kind, source scope, and canonical identity with length
  delimiters. Producers map Context Documents to stable source plus relative
  path, Jira/Wiki Items to normalized Site plus canonical issue key/Page ID,
  and other existing Resources to their canonical path/URL namespace. Known
  Resource aliases use the resolved Document/Item owner. SQLite IDs and raw
  Session-reference target keys containing row IDs are not stable identities.
- Session keys reuse `workflow_episode_key`; the factory validates primary
  work/full-index and supplied meaningful Event/Usage evidence. Reference keys
  hash the Episode, artifact, and source-native occurrence identity. Each member
  independently supports both anchors through mentions or successful reads.
- Identical facts/pairs collapse; conflicting facts with one stable identity
  are excluded with fixed diagnostics. Weak, missing, disabled, container, or
  insufficient evidence cannot be repaired through title, workspace, existing
  organization, a mixed Session, or transitive graph membership.
- Candidate identity hashes contract version and sorted anchors. Membership
  revision observes all admitted supporting references, including those beyond
  the response sample. A separate result revision includes presentation,
  coverage, source state, and diagnostics. Source change may invalidate an
  inferred candidate but never transfers future user assertions to another key.
- Hard input/output bounds raise `CandidateLimitError` instead of returning an
  order-dependent prefix. Evidence and overlap samples retain complete totals
  for the supplied scope. Coverage defaults to partial and cannot claim global
  discovery. The current shapes, bounds and producer duties below complete
  this pure contract.
- Import, normalization, and serialization perform no application I/O and own
  no table, cache, route, scheduled work, model, or current product consumer.

### Candidate Inputs And Producer Duties

The current factories accept normalized mappings and produce frozen descriptors;
`normalize_workstream_candidates(artifacts, sessions, references, pairs, *,
coverage=None)` validates the supplied scope. Factories reject malformed values
with fixed `ValueError` text. Batch normalization counts invalid, excluded and
conflicting individual facts/pairs with sorted fixed diagnostic codes rather
than choosing values by input order. Invalid top-level iterables, coverage or
hard overflow fail; strings, bytes and mappings are not fact iterables.

| Factory input | Mapping fields |
| --- | --- |
| `candidate_artifact_from_record` | Required `kind`, `source_scope`, `source_identity`; optional `title`, `identity_state`, `enabled`, `is_container`, `availability`, `freshness` |
| `candidate_session_from_record` | Required `id`, `source_id`, `external_id`, `session_class`, `session_role`, `index_policy`; meaningful-evidence inputs `event_count`, `has_activity_events`, `has_usage_records`; optional `title` |
| `candidate_reference_from_record` | Required `episode_key`, `artifact_key`, `reference_identity`, `evidence_kind`; optional `read_outcome`, `observed_at` |
| Proposed pair | A tuple/list of exactly two valid distinct Artifact keys |

- Artifact kinds are `context-document`, `wiki-item`, `jira-item`,
  `local-resource` and `external-resource`. Producers resolve aliases first:
  Context uses stable source plus relative path, Jira/Wiki uses normalized Site
  plus canonical Issue/Page identity, and other Resources use their canonical
  path/URL namespace. Known Document/Item aliases use that resolved owner's
  identity. The normalizer performs no fuzzy match, URL/Site inference or I/O.
- Identity strings are nonempty trimmed UTF-8 text, at most 4,096 code points;
  after trimming, reject characters where `ord(char) < 32 or ord(char) == 127`.
  Source scopes are at most 300. Attributed titles
  collapse whitespace and retain at most 500 code points; absent/invalid titles
  remain absent. Raw identities never serialize. Opaque Artifact, Episode and
  Reference keys use their validated namespace and 64-hex digest.
- Artifact identity is `resolved`, `unresolved` or `ambiguous`; enablement and
  container flags are actual booleans. Only resolved, enabled, non-container
  facts qualify. Availability (`available`, `unavailable`, `missing`, `unknown`)
  and freshness (`current`, `stale`, `unknown`) stay separate; retained stale or
  missing facts do not acquire false freshness.
- Artifact factory defaults are identity `unresolved`, `enabled=False`,
  `is_container=False`, and availability/freshness `unknown`. A Session's
  `event_count` defaults to zero and both meaningful-evidence flags to false.
  These conservative defaults do not admit an otherwise unknown fact.
- A Session fact requires work/primary/full, a positive non-boolean local ID,
  a positive integer numeric `source_id`, source-native identity and meaningful
  supplied evidence: `event_count > 0 OR has_activity_events OR has_usage_records`.
  `event_count` is a nonnegative non-boolean integer and both flags are strict
  booleans. Unknown eligibility never defaults true. Episode identity uses the
  [pure workflow identity contract](workflow.md#workflow-projection-contract), not local ID.
- Reference kinds are `user_mention`, `assistant_mention`, `resource_read` and
  `tool_result`. A mention qualifies only with `read_outcome is None`; a read
  qualifies only with `read_outcome == 'success'`. Failed/missing read outcomes,
  absent endpoints and excluded anchors cannot support membership. The producer
  supplies source-native occurrence identity and observed time; local reference
  row IDs and import time are not source occurrence identity.
- Proposed pairs contain two distinct resolved Artifact keys; reversed/duplicate
  pairs collapse. Each admitted member independently supports both anchors,
  with at least two distinct stable Episode keys. Shared Sessions/anchors do
  not merge seeds transitively. Organization, workspace, Git, wording and recency
  cannot repair missing direct evidence.

### Candidate Result, Bounds And Coverage

| Descriptor | Returned contract |
| --- | --- |
| Artifact | `artifact_key`, `kind`, hashed `source_scope_key`, optional `display_title`, `identity_state`, `enabled`, `is_container`, `availability`, `freshness` |
| Session | Stable `episode_key`, current local `session_id`, numeric `source_id`, optional `display_title`, `destination` |
| Reference | `reference_key`, `episode_key`, `artifact_key`, `evidence_kind`, `read_outcome`, UTC-or-unknown `observed_at`, `authority='observed'` |
| Anchor support | `artifact_key`, sampled `references`, full `reference_count`, `observed_start_at`, `last_observed_at`, `unknown_time_count` |
| Membership | `session`, both anchor `supports`, `authority='deterministic-candidate'` |
| Overlap | Other `candidate_key`, `shared_artifact_count`, `shared_session_count` |
| Candidate identity/presentation | `candidate_key`, `anchors`, `label`, `label_authority`, `label_artifact_key`, `members`, `membership_revision` |
| Candidate evidence | `observed_start_at`, `last_observed_at`, `latest_observations`, `latest_observation_count`, `unknown_time_count`, sampled `overlaps`, full `overlap_count` |
| Candidate status | `authority='deterministic-candidate'`, `outcome=None`, `next_action=None`, `activity_state='unknown'`, `lifecycle_state='unknown'`, `closure_reason=None`, `contract_version` |
| Whole result | `candidates`, sorted `diagnostics` (`code`, `count`), `coverage` (`complete`, `unexamined_session_count`), separate `revision`, `scope='supplied-facts'`, `contract_version` |

Seed identity hashes the version and sorted anchor keys. Membership revision
observes every admitted supporting reference, including evidence beyond samples;
it excludes title, local navigation ID and source freshness. Result revision
also observes presentation, source state, coverage and diagnostics. Added members
or changed labels do not rename a seed or retarget future assertions.

Label precedence is Context Document, Wiki, Jira, local Resource, external
Resource, then Artifact key. The first available attributed title wins with
`source-metadata` authority; otherwise `Unnamed work candidate` uses `fallback`.
No goal or confirmed Workstream name is inferred. Only admitted source-observed
reference times determine bounds/latest observations; missing or invalid time
stays unknown. Session end/start, import and wall-clock time do not prove progress.
Outcome/next action and closure reason remain absent; activity/lifecycle stay
`unknown`. Overlap reports shared anchors/Sessions without redefining membership.

| Hard input/output bound | Maximum |
| --- | ---: |
| Artifact facts / Session facts | 2,000 each |
| Reference facts | 20,000 |
| Proposed pairs | 200 |
| Memberships across the whole result | 2,000 |

The normalizer reads at most each input bound plus one and raises fixed
`CandidateLimitError` on overflow, returning no order-dependent partial prefix.
Each member samples at most five references per anchor, by known observed time
descending then opaque key, while retaining full counts, bounds and unknown-time
counts. Latest-reference ties sample at most five with their full total; overlaps
sample at most 20 with full counts. All admitted references still affect revisions
and time bounds. Coverage defaults to partial with unknown unexamined count;
`complete=True` requires an explicit zero unexamined Session count. An empty
partial result never means that the corpus has no candidate.

`coverage` must be a `CandidateCoverage` value, with an actual boolean `complete`
and an unknown or nonnegative non-boolean integer `unexamined_session_count`.
Fixed diagnostics distinguish `invalid-artifact`, `invalid-session`,
`invalid-reference`, `conflicting-artifact`, `conflicting-session`,
`conflicting-reference`, `ineligible-session`,
`disabled-artifact`, `unresolved-artifact`, `ambiguous-artifact`,
`container-artifact`, `missing-session`, `missing-artifact`, `excluded-reference`,
`weak-reference`, `invalid-pair`, `missing-pair-anchor`, `excluded-pair` and
`insufficient-sessions`; codes and counts never copy rejected input text.

This remains a pure supplied-fact contract, with no admitted discovery/review/
promotion consumer, table, route, cache, schedule, model or organization mutation.

## Implementation Ownership

- `src/localbrain/workflow/candidates.py`: pure candidate identity, supplied
  pair/member validation, revisions, evidence/time/coverage descriptors, and
  bounded serialization; no database discovery or organization mutation
