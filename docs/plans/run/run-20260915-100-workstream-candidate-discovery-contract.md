# RUN-20260915-100: Workstream Candidate Discovery Contract

## Metadata

- ID: `run-20260915-100`
- Status: `returned-to-planning`
- Feature: [FEAT-0090](../feature/feat-0090-workstream-candidate-discovery-contract.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Active Spec: [SPEC-0090](../spec/spec-0090-workstream-candidate-discovery-contract.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-15`
- Updated: `2026-09-15`

## Goal

Establish the approved pure candidate identity, evidence admission, many-to-many
membership, observation, coverage, and deterministic rebuild contract.

## Selected Loop

- Feature type: `foundation`
- Surface: pure contract and durable owner docs
- Surface lanes: none
- Required evaluators: Contract, Functional
- Current phase: post-run planning return; technical evaluation complete

## Contract Surfaces

Canonical artifact/Session/reference identity, pair/member validation, revisions,
source/time axes, bounds, overlap, omission, serialization, and no-I/O ownership.

## Original Invocation Context

- Golden sources: owner-approved FEAT-0090 and PRD-0017.
- Relevant policies: Product, Architecture, Privacy, Workspace/Session Activity,
  execution governance, and Foundation Contract profile.
- Optional skills/tools: none required; no visible surface changes.
- Initial authority covered FEAT-0090 only. The later post-run planning return
  below governs current routing; this historical invocation cannot restart it.

## Current Artifacts

- Spec: [SPEC-0090](../spec/spec-0090-workstream-candidate-discovery-contract.md).
- Contract evaluation: [PASS, complete coverage](../evaluation/eval-0090-contract-workstream-candidate-discovery-contract.md).
- Functional evaluation: [PASS, complete coverage](../evaluation/eval-0090-functional-workstream-candidate-discovery-contract.md).
- Design/UX evaluation: not applicable.
- Fix log: none.

## Evaluation Coverage

- Contract and Functional evidence: complete for SPEC-0090; both PASS.
- Evidence: pure-module/consumer inspection, 33 synthetic candidate tests,
  complete 584-test regression, data-model parity, generated schema/audit
  checks, privacy scan, and whitespace validation.
- No database-discovery, browser, private-corpus usefulness, or promotion
  evidence is claimed; those belong to later Features.

## Current Route

- Follow-up: approved [FEAT-0095](../feature/feat-0095-bounded-work-reconstruction-experiment.md)
  is implemented in [RUN-20260915-101](run-20260915-101-bounded-work-reconstruction-experiment.md),
  blocked on independent quality assessment after synthetic verification and an
  unassessed current-data execution check. Its DB/time scope is resolved.
- Original return classification: `planning gap`; pair-as-flow granularity and
  routine review/promotion do not meet the owner's replacement intent.
- In-run route: complete; no remaining fix or implementation work.
- Post-run review: owner requested replanning; FEAT-0091–0094 are superseded.
  This Run's technical PASS applies only to the unchanged isolated pair
  contract, not product sufficiency or follow-up authority. It stays
  returned-to-planning; the approved experiment has its own Run and evidence.

## Attempts

- Attempt 1: implemented the approved pure contract and passed both required
  evaluations. The first full regression found a stale derived semantic-owner
  digest; rebuilt Schema Presentation and refreshed its audit digest/ledger.
  Schema objects and existing audit decisions are unchanged. The repeated
  full suite passed `584/584`.

## Post-Contract Regression Check

- Needed: yes; identity/descriptor ownership changes.
- Result: PASS. Existing Focus/Trace, workflow assertions, Related Materials,
  organization, and source-operation consumers are unchanged and their
  regression tests pass. Generated artifacts match their owners.

## Human Review Outcome

- Decision: owner approved FEAT-0090 execution on `2026-09-15`.
- Post-run acceptance: product-level continuation not accepted; the owner
  requested automatic reconstruction and minimum confirmation instead of
  the proposed candidate review/promotion chain.
- Returned layer/follow-up Run: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#reconciliation-and-approval-state)
  was reopened as draft and its revised analysis boundary has since been
  approved. FEAT-0095 subsequently entered RUN-20260915-101; its partial
  evidence and current missing-input block do not reopen this Run.

## Continuity Notes

- `2026-09-15`: the Orchestrator selected one Foundation Contract Run and
  accepted SPEC-0090 as ready for build. Later candidate Features remain drafts.
- `2026-09-15`: the pure contract passed with no remaining findings. The next
  approval target is the local-only producer in FEAT-0091; this result does not
  approve that Feature or establish candidate usefulness.
- `2026-09-15`: post-run owner review rejected treating the pair contract as
  sufficient for the replacement product and requested a planning return.
  Status changed to `returned-to-planning`; prior Contract/Functional results
  remain valid for their bounded checks. No code fix is inferred, and no
  superseded candidate Feature may start from this Run's earlier pass.
- `2026-09-15`: owner accepted the revised PRD's analysis/validation direction.
  Updated current routing to draft FEAT-0095 review without reopening this Run,
  rerunning its tests, or changing historical evaluation results.
- `2026-09-15`: linked the now-approved experiment's RUN-20260915-101 and
  missing-private-evidence block. The original return classification and
  historical evaluator results remain unchanged.
