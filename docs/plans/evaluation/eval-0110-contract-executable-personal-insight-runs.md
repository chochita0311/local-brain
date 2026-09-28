# EVAL-0110 Contract: Executable Personal Insight Runs

## Metadata

- ID: `eval-0110-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `partial`
- Run: [RUN-20260928-120](../run/run-20260928-120-executable-personal-insight-runs.md)
- Attempt: `2`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `fullstack-product`
- Lane: `data`, `backend`
- Created: `2026-09-28`

## Evidence And Finding

- `personal_insight_runs` has its own ID, checked lifecycle/mode/runner, frozen settings and artifact references, and no Session or maintenance foreign key. The owner-only artifact directory is outside Git; reports are served only from the expected Run path.
- The evidence producer admits normalized primary work Sessions only and bounds the selected excerpts. The runner accepts only cited frozen IDs, requires independent Sessions for a recurring pattern, and locally renders the Markdown rather than trusting model-authored links.
- Codex CLI uses the selected `CODEX_HOME`, ignores user configuration and rules for the Run, disables model tools, and uses `--ephemeral` to keep the analysis conversation outside ordinary Session evidence. The selected profile and model are frozen before execution.
- The contract was inspected in source and generated schema documentation. No provider response, completed report, or cancellation transition was observed at runtime. This limits evidence coverage, not the source-level conclusion.
