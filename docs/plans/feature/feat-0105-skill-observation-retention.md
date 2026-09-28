# FEAT-0105: Skill Observation And Retention

## Metadata

- ID: `feat-0105`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Created: `2026-09-27`
- Updated: `2026-09-28`

## Goal

Define and persist one bounded, source-backed skill-use observation per admitted native event, independently of the lifetime of the normalized Session row.

## Acceptance Contract

- Claude `Skill` calls with native IDs and Codex-generated `<skill>` messages with native IDs are the admitted first-release signals. Direct `SKILL.md` reads and mere skill-name mentions do not count. Admitted observations retain native event identity, Session identity, source key, skill identity, time, and signal kind.
- A versioned first sync backfills available source files. Later changed or resumed files insert only previously unseen observations; retries, replay, moves, and repeated scans do not raise counts.
- Ordinary source-file or Session disappearance leaves previously admitted observations intact. Source and native Session identity stay in the ledger for later provenance work; the first ranking does not require a live Session lookup.
- Maintenance activity is excluded. Direct work subsessions are eligible when their event is independently observed.
- The ledger stores bounded identity metadata rather than a transcript, full tool input, or an aggregate-only total. A parser correction can invalidate an erroneous observation without ordinary disappearance doing so.
- Current source coverage and extraction version remain distinguishable from an observed zero.

## Scope Boundary

- In: source adapters, versioned incremental ingestion, durable observation identity and schema, compatible migration, retention and correction semantics, source coverage query contract, and owning data-model documentation.
- Out: Insight navigation, ranked presentation, inferred skill candidates, work-pattern analysis, skill-file creation, and external analysis.
- The owner excluded direct Codex `SKILL.md` reads from the first-release count. Precise source identity remains separate in storage while the approved UI sums the same normalized name across sources.

## Contract Surfaces

- Producers: `ingest/claude.py`, `ingest/codex.py`, `ingest/scanner.py`.
- Persistence: `schema.sql`, `db.py`, and source-file extraction freshness.
- Consumer: source-neutral observation query for the first Insights view.
- Semantic owner: [Workspace And Session Activity](../../policies/project/data-model/workspace-and-session-activity.md) and [Project Architecture](../../policies/project/architecture.md).

## Pass Or Fail Checks

- Reimport and source-path movement preserve the count of a native event.
- A resumed Session with one new admitted event increases only that skill's count by one.
- Removing a Session source does not decrement the count, and its prior link is shown as unavailable to consumers.
- Claude and Codex supported signals, malformed/missing native IDs, replay, maintenance, subsessions, and coverage gaps have bounded synthetic examples.
- Fresh and compatible databases expose the same schema contract and no private source payload enters tracked artifacts.

## Dependencies

- Approved PRD-0005 boundary; explicit source-signal admission decision.

## Regression Surfaces

- Session and Usage Record ingestion, source-file skip/repair behavior, source removal, startup migration, and Schema presentation.

## Harness Trace

- Spec: [SPEC-0105](../spec/spec-0105-skill-observation-retention.md)
- Run: [RUN-20260928-123](../run/run-20260928-123-skill-observation-retention.md)
- Execution profile: `foundation-contract`
- Latest evaluator reports: [contract](../evaluation/eval-0105-contract-skill-observation-retention.md) and [functional](../evaluation/eval-0105-functional-skill-observation-retention.md)

## Continuity Notes

- `2026-09-27`: proposed as the first foundation increment after the owner directed skill ranking work to proceed. The owner resolved signal admission and same-name presentation in subsequent answers, allowing this contract boundary to proceed to Spec.
- `2026-09-28`: implementation predated its formal Run record. Synthetic admission, incremental-retention, correction, coverage, and compatible-migration checks passed after fixing the zero-current coverage state. No personal-improvement analysis model Run was invoked.
