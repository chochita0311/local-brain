# RUN-20260927-118: Personal Insight Evidence Manifest

## Metadata

- ID: `run-20260927-118`
- Status: `passed`
- Feature: [FEAT-0107](../feature/feat-0107-personal-insight-evidence-manifest.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0107](../spec/spec-0107-personal-insight-evidence-manifest.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-27`
- Updated: `2026-09-28`

## Goal And Boundary

Implement the read-only bounded Session message manifest and current-reference review for future personal insight Runs. The selected loop is one foundation data contract. It does not call a model, add a user-facing route, persist Run evidence, or choose an analysis engine.

## Execution Record

- Orchestrator: the approved FEAT-0107 is independent of the later model path. `foundation-contract` with contract and functional evaluators is the smallest matching profile; no surface lanes are needed.
- Spec Agent: [SPEC-0107](../spec/spec-0107-personal-insight-evidence-manifest.md) fixes input validation, scope, selection, value shape, staleness, privacy, and caps.
- Builder: `src/localbrain/personal_insight_evidence.py` and its owner-document updates provide the producer and reference reviewer. Existing tables and Session FTS are read only; no migration or UI hook is introduced.
- Attempt 1: the static [contract evaluation](../evaluation/eval-0107-contract-personal-insight-evidence-manifest.md) passed its inspected value shape with partial coverage. It did not establish behavioral acceptance.
- Attempt 2: eight synthetic, in-memory SQLite tests passed under [functional evaluation](../evaluation/eval-0107-functional-personal-insight-evidence-manifest.md). A Unicode casefold offset error found in the first functional pass was corrected before the passing rerun.

## Contract Surfaces

- `build_insight_evidence_manifest` input and versioned private value shape.
- `resolve_insight_evidence_reference` status and Session destination.
- Existing `sources`, `sessions`, `activity_events`, and `search_index` authority; no new storage owner.
- Project Architecture, Workspace And Session Activity, and Privacy And Data Handling documentation.

## Evaluation Coverage

- Contract result: `PASS`, partial source-inspection coverage.
- Functional result: `PASS`, complete synthetic evidence-only coverage. SQL eligibility and local-date behavior, FTS fallback, deterministic source/month spread, hard caps, and stale/unavailable references passed focused tests.
- UI, private Session content, and provider execution remain outside this foundation Run's acceptance surface.

## Current Route

- The foundation contract has passed its required evaluation. The later analysis guide and provider execution are separate Features.
- Post-run human review may inspect this bounded result without treating it as proof of a real-model analysis.

## Attempts

- Attempt 1: implementation and owner-document update complete; required evaluator evidence remained pending.
- Attempt 2: functional evaluation found and fixed the casefold offset error, then passed eight synthetic tests.

## Continuity Notes

- `2026-09-27`: started after the owner directed work to continue on the first evidence-only analyzer target. The selected model path remains open for later work.
- `2026-09-28`: the required foundation evaluation closed without a provider call or private Session read.
