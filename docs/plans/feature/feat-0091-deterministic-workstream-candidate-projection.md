# FEAT-0091: Deterministic Workstream Candidate Projection

## Metadata

- ID: `feat-0091`
- Status: `superseded`
- Type: `foundation`
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-15`
- Updated: `2026-09-15`

## Supersession Boundary

The owner requested automatic outcome-level reconstruction with minimum
confirmation. Pair enumeration is not a sufficient top-level flow rule, and
metadata-only discovery may miss the required goal evidence. This unexecuted
proposal is superseded by [PRD-0017 replanning](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#reconciliation-and-approval-state).
The remaining sections preserve the old proposal for audit; they do not
authorize Spec work or select the next Run. A new experiment boundary must
follow review of the revised PRD.

## Goal

Produce the FEAT-0090 candidates from persisted local evidence across Sessions
and source families, independently of any selected Session or Focus viewport.

## Acceptance Contract

- One read owner assembles eligible source facts and invokes the passed
  [FEAT-0090](feat-0090-workstream-candidate-discovery-contract.md) contract.
  Registered primary-work Session sources share the same eligibility rule;
  maintenance, provider-internal, and Subsession content cannot seed candidates.
- Admission uses current normalized Session reference evidence and resolved
  enabled Local Context, Jira/Wiki Item, and existing Resource identities.
  Metadata-only or reference-mode sources never gain body access. Unregistered
  sources and unstored ticket/Page ancestry are not invented.
- Each distinct qualified anchor pair produces one provisional candidate and
  each member independently supports both anchors. No connected-component
  algorithm, shared workspace, existing organization, or Session-wide evidence
  union expands that membership.
- The discovery scope covers eligible persisted history across sources and
  workspaces, with no default selected-Session or recency cutoff. Work and
  response sizes remain bounded: the Spec fixes deterministic input batches,
  pair/response limits, and continuation behavior before build. Every reached
  processing limit reports examined and unexamined scope explicitly.
- Bounded display pages use a stable result revision and deterministic order.
  Pagination cannot change candidate identity, member totals, or source scope.
  A changed corpus requires an explicit fresh result; it never silently joins
  pages from incompatible revisions.
- The result exposes attributable labels, exact per-member reasons, source
  families, observation span, latest supporting observations, overlapping
  candidates, and missing/limited evidence. Full Session contents and unrelated
  references do not become candidate evidence.
- Existing Workstream/Thread associations appear as explicit organization and
  possible review destinations. Discovery writes none of those records and
  does not count its own future promotion output as new independent evidence.
- Repeat reads against unchanged local facts produce the same candidates,
  identities, memberships, reason order, and diagnostics. Source removal and
  re-resolution change inferred availability according to the contract without
  claiming deletion authority over user records.
- The producer performs local SQLite reads only. It writes no candidate cache,
  scans/parses no source file or content body, schedules no work, and initiates
  no model, network, connector, capability, Sync, or Refresh operation.

## Scope Boundary

- In: normalized evidence reads, alias/eligibility reconciliation, candidate
  assembly, result revisions, deterministic bounds, coverage, and continuation.
- Out: source ingestion changes, body extraction, semantic models, derived
  persistence, routes/templates, durable review, promotion, Lens, and Atlas.

## Contract Surfaces

- Database evidence to FEAT-0090 producer contract.
- Bounded read result, pagination/revision, partial and empty semantics.
- Read ownership, query budget, privacy, and source-operation exclusion.

## Required Evaluators

- `contract`: admission parity, identity, query/response bounds, source-state
  ownership, privacy, and independence from Focus display truncation.
- `functional`: synthetic corpus cases, repeatability, paging, source change,
  read-only enforcement, and representative local performance.

## Entry And Exit

- Entry: a local candidate read with explicit scope/continuation state.
- Exit: deterministic candidates and coverage or a bounded recoverable error;
  no durable write and no automatic fallback source operation.

## State Expectations

- Ready: supported candidates for the examined scope.
- Empty: examined scope contains no supported candidate.
- Partial: processing or source coverage is incomplete, even if zero candidates
  were found; no claim that the remaining history has no useful work.
- Changed revision: restart result inspection without mixing old and new pages.
- Error: preserve source and organization state; report local recovery.

## Dependencies

- FEAT-0090 must be approved before Spec work and passed before build.
- Passed source reference/Atlassian/Local Context contracts remain authoritative.
- [FEAT-0092](feat-0092-workstream-candidate-evidence-review.md) consumes this
  producer; this Feature does not claim its UI or product-review outcome.

## Likely Affected Surfaces

- A dedicated candidate read module under `src/localbrain/`.
- Existing source-reference and organization reads as bounded dependencies.
- Synthetic projection/performance tests and product/architecture/privacy docs.
- No schema, source adapter, or existing Focus behavior change is assumed.

## Pass Or Fail Checks

- Pass the PRD's synthetic candidate matrix, including multiple source families
  and an effort extending beyond 24 Sessions and across workspace boundaries.
- Demonstrate candidates when Workstream and Thread tables contain no records.
- Check every retained member's anchor reasons and verify that unrelated
  references in a mixed Session do not transfer to both candidate groups.
- Verify stable results and revision-safe paging, with independently checked
  coverage totals for complete, partial, unavailable, and empty inputs.
- Freeze a representative synthetic corpus and a local latency/memory budget
  in the Spec before implementation; report cold/repeat reads and limit cases.
  A missed budget returns the boundary for review before adding persistence.
- Fail on a write, body read, excluded source, hidden I/O, or an unreported cap.

## Regression Surfaces

- Focus/Trace and reversible workflow corrections.
- Session reading and the authoritative Related Materials rail.
- Workstream/Thread links and Suggestions; source Sync/Refresh separation.

## Harness Trace

- Spec doc: not created; prerequisite and Feature approval pending.
- Run: not started.
- Execution profile: `foundation-contract`.
- Latest evaluator reports: none.
- Latest fix note: none.

## Open Review Decisions

- Dependency-gated on FEAT-0090 baseline acceptance. A change to seed admission
  requires updating this proposal before approval.
- Processing limits and the measured performance corpus must be fixed in the
  Spec; they cannot silently reduce the product's reported discovery scope.

## Continuity Notes

- `2026-09-15`: proposed as a separate corpus read boundary after the candidate
  contract; no source/model operation or implementation is authorized yet.
- `2026-09-15`: superseded during the automatic-reconstruction replan. No Spec,
  Run, or implementation was started; no current producer depends on this plan.
