# RUN-20260923-113: Full-History Simulation Replay

## Metadata

- Run ID: `run-20260923-113`
- Status: `passed`
- Attempt: `2`
- Feature: [FEAT-0097](../feature/feat-0097-replayable-session-simulation.md)
- Spec: [SPEC-0097](../spec/spec-0097-replayable-session-simulation.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-23`

## Scope And Approval

The owner authorized continuing through the full-history inspection UI, including
bounded replanning/review without further approval stops. This first Run closes
the earlier simulation's live evidence gap before a new consumer is built.
Earlier RUN-103's returned outcome remains historical. No new source admission,
model download, training, source mutation, UI or legacy deletion is in this Run.

## Execution Contract

Use the existing verified embedding runtime and source-bound simulation owner.
Refresh only missing/changed input, then run unchanged and grouping-only replays.
Verify zero new encoding for the latter two, exact unchanged grouping/configuration,
source immutability and full-population accounting. Restore the default grouping
configuration after the controlled grouping variant. Do not publish private
titles, excerpts, paths or inventory in tracked evidence.

## Current Route

- Primary agent owns orchestration and semantic review.
- Current role: verify existing runtime and perform explicit local replay.
- Next: Contract/Functional evidence, then FEAT-0101 read contract.
- No active model-relation trial or mandatory user classification.

## Attempts

- Attempt 1: source-delta refresh reused existing vectors and encoded only new
  inputs. Unchanged replay reproduced all edges and weights but not all inner
  communities. Fixed-seed Louvain consumed a subgraph view with hash-dependent
  iteration order. This is an implementation defect, not permission to weaken
  replay acceptance. No data was removed or model retrained.
- Attempt 2: canonicalize graph node/neighbor insertion before each Louvain
  pass; version the grouping engine independently of vector identity. Add
  cross-process hash-seed regression and fail closed on nonfinite distances.
  Local BLAS emitted numerical flags despite finite normalized vectors and
  finite sample distances agreeing with float64; actual result validation now
  guards every neighbor batch. Skip excluded event bodies in inventory length
  reads without changing the admitted fingerprint. Revalidate live replay.

## Focused Verification

- Semantic runtime: all 23 simulation tests pass, including cross-process hash
  seeds, nonfinite-neighbor rejection and character-window boundaries.
- Full app regression: 945 tests pass, with three optional semantic checks
  skipped in the lightweight application runtime. Privacy scan passes.
- A bounded 65,536-character source read-ahead preserves the actual full-source
  manifest exactly and reduces its observed verification time from 53.536 to
  2.362 seconds. It stores no extra source body and changes no cache identity.

## Outcome

Actual unchanged replay reproduced input, configuration and full grouping with
zero encoder calls. The grouping-only variant also encoded zero inputs; restoring
the original parameters reproduced the canonical baseline exactly. Source DB
and WAL byte hashes were unchanged across the entire verification. Existing
vectors were retained; only the earlier source-delta preparation encoded missing
inputs. Both required evaluations now have complete technical evidence.
Semantic grouping quality remains unassessed. Next: FEAT-0101, then FEAT-0102;
the owner's continuous-through-UI approval requires no intervening review stop.
