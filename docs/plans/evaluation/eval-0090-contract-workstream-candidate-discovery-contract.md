# EVAL-0090 Contract: Workstream Candidate Discovery Contract

## Metadata

- ID: `eval-0090-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-20260915-100](../run/run-20260915-100-workstream-candidate-discovery-contract.md)
- Attempt: `1`
- Feature: [FEAT-0090](../feature/feat-0090-workstream-candidate-discovery-contract.md)
- Spec: [SPEC-0090](../spec/spec-0090-workstream-candidate-discovery-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: none; pure descriptors and durable owners
- Evidence Coverage: `complete`
- Created: `2026-09-15`

## Scope

The uncommitted FEAT-0090 implementation in `workstream_candidates.py`, its
synthetic tests, and the changed Product, Architecture, Privacy, and
Workspace/Session Activity owner sections. This is not a database-discovery or
candidate-usefulness evaluation.

## Checks And Evidence

- Source inspection and 33 synthetic tests establish source-scoped artifact,
  Episode, and reference identity. Unordered two-artifact seeds require at
  least two eligible primary Sessions, each with its own support for both
  anchors. Aliases already reconciled by the producer and repeated occurrences
  collapse; conflicting normalized facts are omitted independent of order.
- Candidate identity is separate from membership and full-result revisions.
  Titles, local row IDs, and source state do not retarget the seed. Added
  members or changed supporting evidence update membership revision, including
  evidence beyond the serialized samples.
- Many-to-many memberships retain candidate-specific references. Overlap is a
  bounded descriptor, not a transitive merge or a new causal direction.
  Mentions and successful reads retain observed authority; candidate membership
  is inferred and never becomes user-confirmed organization.
- Source reference times alone determine observed bounds and latest known
  observations. Unknown times, unavailable/stale anchors, coverage, lifecycle,
  and activity remain independent. Outcome, next action, and closure are not
  fabricated.
- Hard input/output bounds fail explicitly without accepting a prefix.
  Reference and overlap samples retain full totals. Default partial coverage
  describes only supplied facts, never a whole-corpus negative result.
- Serialization uses whitelisted fields and opaque identities, excluding raw
  native IDs, reference occurrences, paths, bodies, and payloads. A subprocess
  test with existing utility dependencies preloaded guards new-module import,
  empty/populated normalization, and serialization against application file
  reads, SQLite connections, sockets, and process launches.

## Contract Evidence

- Producer: canonical identity/alias resolution, meaningful primary-Session
  facts, source references, proposed pairs, and honest scope belong to the
  later FEAT-0091 producer. The pure contract performs no corpus enumeration.
- Consumer: only the new synthetic tests currently import this module.
  Inspection found no new route, query, persistence, Focus, assertion,
  Workstream, Thread, or Suggestion consumer.
- Owners: Product, Architecture, Privacy, and Workspace/Session Activity match
  SPEC-0090. Data-model parity passed for 42 ordinary tables, one FTS5 object,
  57 foreign keys, 46 explicit indexes, and ten subject owners.
- Generated artifacts: Schema Presentation was rebuilt and checked. Its only
  JSON change is the semantic owner's source digest. The audit manifest hash
  and generated runtime-reference inventory were refreshed without changing
  decisions: 649 objects, `keep=543`, `defer=106`, no change/remove candidates.
- Stale-assumption check: existing Focus limits, organization, global
  assertions, and Related Materials are unchanged. No schema/value-registry
  family or source-operation dependency was introduced.
- The complete repository suite passed `584/584`; the repository privacy scan
  and `git diff --check` also passed.

## Evidence Gaps

- None for the approved pure-contract boundary.
- Database discovery, real private-corpus usefulness, and visible interaction
  were not evaluated. They belong to later draft Features and are not implied
  by this PASS; browser evidence is not applicable to FEAT-0090.

## Findings

- No remaining findings. The initial full-suite failure was a stale derived
  audit digest after the owner-document update; regeneration and the repeated
  full suite verified its correction without a schema or decision change.

## Route

- Technical result: `pass` for this unchanged isolated contract.
- Subsequent product review returned RUN-20260915-100 to planning and
  superseded FEAT-0091–0094. This report does not establish a sufficient
  workstream unit or authorize those consumers. Current direction belongs to
  the revised PRD-0017, not this historical evaluation.
