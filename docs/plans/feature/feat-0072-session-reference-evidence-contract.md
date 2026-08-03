# FEAT-0072: Session Reference Evidence Contract

## Metadata

- ID: `feat-0072`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`
- Parent PRD: [PRD-0013: Session-Centric Related Context Evidence](../prd/prd-0013-session-centric-related-context-evidence.md)
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Goal

- Establish one source-neutral ownership, identity, value-shape, lifecycle, and
  presentation-authority contract for evidence that a primary work Session
  mentioned, observed, or attempted to read a reference.

## Acceptance Contract

- Session reference evidence is a derived local fact owned separately from the
  authoritative Session event, shared Resource metadata, remote state/content,
  and user-managed Thread/Workstream relationships.
- The contract distinguishes visible user mention, visible assistant mention,
  approved tool-result observation, successful approved resource read, and
  failed approved resource read.
- A successful read requires one allowlisted read operation and its matching
  completed non-error result. When at least one matching read succeeds, the
  target owns successful read evidence; when every matching attempt fails, the
  target owns bounded failure evidence and no remote-read implication.
- Target families cover safe HTTP(S) URLs, exact eligible Markdown references,
  and configured Atlassian Items under deterministic adapter rules.
- Stable Resource identity and destination remain reusable, but
  `external_resources.title` is not the primary Session display authority when
  the Session supplies a deterministic issue key, file identity, or safe
  host/path identity.
- One target may own several evidence kinds and locations without producing more
  than one visible direct-reference row.
- Read counts use distinct completed tool calls. Mention/observation counts use
  distinct normalized source locations. Repeated source text, replay,
  compaction, and rescan do not inflate either count.
- The evidence shape preserves source instance, provider/parser identity,
  Session ID, source event or line location, target identity, evidence kind,
  outcome, observed identity, reconciliation version, and bounded freshness or
  partial state without retaining message excerpts or opaque payloads.
- The persistence contract defines fresh and compatible schema behavior,
  producer and consumer ownership, rebuildability, deletion effects, recovery,
  privacy, indexes, and generated schema documentation before runtime capture
  depends on it.
- Source-derived evidence is deleted or replaced when its owning Session source
  evidence disappears, but shared Resource, remote content, notes,
  classifications, and organization links remain untouched.
- Eligible input is limited to persisted primary work Sessions. Maintenance and
  Subsession evidence does not enter the contract's initial consumer scope.
- Same-workspace or same-directory Documents do not become reference evidence or
  Related Context candidates without a direct Session reference or explicit
  Thread/Workstream relation.

## Scope Boundary

- In:
  - Session reference evidence ownership and terminology
  - supported target and evidence-kind vocabulary
  - success, failure, count, deduplication, stale, and partial semantics
  - deterministic Session-facing display-authority and fallback order
  - bounded source-location and navigation-ready provenance
  - fresh/compatible persistence and data-model ownership
  - source-derived reconciliation and deletion contract
  - privacy and payload-minimization boundary
- Out:
  - parser or scanner extraction behavior
  - Related Context query or UI changes
  - exact conversation navigation
  - Subsession roll-up
  - remote access, metadata refresh, or Resource mutation
  - semantic matching, LLM inference, embeddings, or fuzzy resolution

## Contract Surfaces

- Session evidence identity and uniqueness.
- Evidence kind and read-outcome vocabulary.
- Target identity and Session-facing display fallback.
- Source event/line provenance and count semantics.
- Fresh and compatible SQLite representation, indexes, constraints, and
  migrations.
- Producer, consumer, rebuildability, deletion, recovery, privacy, and generated
  schema-documentation ownership.
- Separation from `activity_events`, `external_resources`, Atlassian remote
  state/content, and user-managed organization links.

## Required Evaluators

- `contract`: ownership, evidence vocabulary, schema/value shape, migration,
  lifecycle, privacy, presentation authority, and downstream readiness.

## State Expectations

- Default: one target owns a deterministic set of bounded Session evidence.
- Success: one or more matching reads completed without error.
- Failure-only: supported reads were attempted but none succeeded.
- Mention-only: the target was observed without a successful or failed approved
  read.
- Ambiguous: no target relation is created.
- Partial/stale: prior valid evidence is retained with an explicit bounded state
  when reconciliation cannot complete.

## Dependencies

- PRD-0013 must remain approved.
- Passed FEAT-0047 and FEAT-0060 are inspected regression contracts, not implicit
  authority for the new Session-facing evidence shape.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/schema-presentation.json`
- `src/localbrain/value-registry.json`
- data-model presentation and value-registry generators
- `docs/policies/project/product.md`
- `docs/policies/project/architecture.md`
- `docs/policies/project/privacy-and-data.md`
- `docs/policies/project/data-model/workspace-and-session-activity.md`
- `docs/policies/project/data-model/atlassian-source-memory.md`
- schema, migration, presentation, registry, and privacy tests

## Pass Or Fail Checks

- Pass if every persisted value has one unambiguous owner and documented
  producer, consumer, lifecycle, deletion, recovery, and privacy rule.
- Pass if success, failure-only, mention, tool-result observation, count,
  deduplication, stale, and partial semantics require no downstream guesswork.
- Pass if Session-observed identity and shared Resource title are distinct
  authorities with deterministic fallback.
- Pass if fresh and compatible databases converge on the same constraints,
  indexes, generated presentation, and value contracts.
- Pass if the contract cannot retain full messages, opaque tool arguments or
  results, or remote content.
- Pass if same-workspace-only Documents, Maintenance Sessions, and Subsessions
  remain ineligible.
- Fail if downstream capture or UI must infer ownership, read success, counting,
  display identity, deletion, or ambiguity behavior.

## Regression Surfaces

- FEAT-0047 Atlassian URL evidence and source fingerprint behavior.
- FEAT-0060 primary Session Related Context projection.
- Activity Event and Session source authority.
- External Resource stable identity and user-managed metadata.
- Atlassian remote state/content and refresh ownership.
- Thread/Workstream links and Local Context document identity.
- Repository privacy and generated schema parity.

## Harness Trace

- Active spec doc: [SPEC-0072](../spec/spec-0072-session-reference-evidence-contract.md)
- Active run: [RUN-20260803-82](../run/run-20260803-82-session-reference-evidence-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [Contract PASS](../evaluation/eval-0072-contract-session-reference-evidence-contract.md)
- Latest fix note: not created.

## Open Review Decisions

- None inside the proposed boundary. Approval authorizes contract/schema work,
  not parser ingestion or product presentation.

## Continuity Notes

- `2026-08-03`: initial draft proposed after PRD-0013 approval; execution remains
  blocked on human Feature-boundary review.
- `2026-08-03`: owner approved FEAT-0072 through FEAT-0074 for dependency-ordered
  execution. FEAT-0072 entered the loop first under `foundation-contract`.
- `2026-08-03`: RUN-20260803-82 passed Contract evaluation with fresh/compatible
  schema, value registry, generated ownership, privacy, and full regressions.
