# EVAL-0110 Contract: Insight Usage Accounting

## Metadata

- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-125](../run/run-20260928-125-personal-insight-usage-accounting.md)
- Attempt: `1`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md), usage accounting correction
- Execution Profile: `backend-product`
- Lanes: `data`, `backend`
- Created: `2026-09-28`

## Evidence

- Source binding resolves the exact registered `CODEX_HOME/sessions` root, including symlinks, and freezes its key. Unmatched or ambiguous profiles fail before model launch. New Runs explicitly select Standard tier; historical unmarked summaries retain a labeled default-tier assumption.
- The independent Run retains its identity and artifacts. One deterministic metadata-only Maintenance Session supports the existing non-null Usage parent contract without events, search, native source-file registration, or a work Project. Work inventory, details, activity, and future insight evidence exclude it through their existing filters.
- Inclusive input and cached input are separated before the existing calculator runs. Reasoning is not added twice. Missing fields, malformed values, unsupported models, and ambiguous aggregate long-context pricing retain explicit states instead of fabricated zero costs.
- Replayed Run summaries reuse one Usage ID, occurrence time, snapshot, and attribution. Native source cleanup and repair preserve insight accounting. Startup recovery is local and idempotent. Schema structure is unchanged; owner docs and generated presentation match it.
- Relevant bounded regression failures were compared with unchanged HEAD and found pre-existing; see the Run for the eight exact test categories and impact.
