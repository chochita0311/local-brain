# EVAL-0020: Usage And Cost Fact Contract Functional

## Metadata

- ID: `eval-0020-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `FAIL`
- Run ID: `run-20260718-20`
- Attempt: `1`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: source normalization and persistence runtime
- Evidence Coverage: `partial`
- Created: `2026-07-18`

## Scope

- Active feature: runtime parsing, normalization, pricing, persistence, and repeat-start behavior required by FEAT-0020.
- Active spec: SPEC-0020.
- Evaluated build: current working tree for RUN-20260718-20 Attempt 1.

## Checks

- Parsed complete Claude and Codex usage records.
- Repeated a Codex turn observation and a stored Session synchronization.
- Stored a maintenance subsession with no indexed Activity Events.
- Stored unknown-model and malformed-token facts.
- Introduced a second price snapshot and updated an in-progress historical fact.
- Upgraded and restarted a temporary legacy database.
- Re-ran the complete regression suite.

## Evidence

- Claude components totaled 200 normalized tokens and produced `$0.001134000000` with the retained snapshot.
- Codex source input 1,000 with 400 cached input normalized to 600 non-cached input; 200 output including 80 reasoning tokens produced 1,200 total tokens and `$0.009200000000` without double counting.
- Two observations for one Codex `turn_id` produced one fact using the latest values.
- Re-storing one maintenance subsession produced one usage row even though it produced no Activity Events or Search row.
- Unknown price produced `unpriced` and malformed tokens produced `failed`; both retained `NULL` estimated cost rather than zero.
- A growing historical fact retained `ccusage-20.0.14-litellm-20260718` after a future snapshot appeared and recalculated only from the retained rates.
- All 53 tests passed.

## Evidence Gaps

- Attempt 1 lacked same-turn multi-delta, multi-file shared-Session, and automatic normalizer-version repair coverage.
- Acceptance impact: `blocking`.

## Findings

- Severity: blocking.
- Classification: `spec gap`.
- Description: synthetic latest-per-turn behavior passed but did not represent the private Codex source's cumulative observation semantics; replacement behavior also lacked a safe source-wide boundary.
- Evidence: private post-run validation performed after the initial report.
- Fix hint: apply the corrected Attempt 2 contract and re-evaluate.

## Regression Notes

- Existing Session, Project, Workstream, retrieval, runner, UI-contract, and synchronization tests passed.

## Route

- Next action: `spec-review`

## Continuity Notes

- `2026-07-18`: functional evaluation passed; FEAT-0021 may consume the stable usage fact contract.
- `2026-07-18`: superseded after private post-run validation; the Attempt 2 functional evaluation is the current acceptance evidence.
