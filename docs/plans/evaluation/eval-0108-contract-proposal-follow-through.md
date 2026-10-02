# EVAL-0108 Contract: Proposal Follow-through

## Metadata

- ID: `eval-0108-contract-proposal-follow-through`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-136](../run/run-20261002-136-personal-insight-proposal-follow-through.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `data`
- Created: `2026-10-02`

## Contract And Preservation

Core v8 changes only the existing decision section and version heading. It distinguishes proposal, application, outcome and deferral; useful application help does not require conceptual novelty. The existing playbook thresholds, ordinary-work evidence boundary, concrete handoff requirements and output schema remain authoritative. Proposal state is expressed in existing prose fields, not a new database or JSON field.

The loader selects v8 for new Runs and explicitly retains the v7-to-report-v3 mapping. Every preexisting core/playbook resource matches its pre-edit digest. Tests also compare the unchanged sections and preserve the historical v7 application-section comparison against v6. The historical real v7 response still validates to the same value and renders to byte-identical Markdown under the revised module; its production artifacts were not modified.

## Verification

- 28 focused tests pass: guidance 18, Run guidance 2, usage 7, UI contract 1.
- Eight first producer answers validate against their assigned frozen bundle and schema and render successfully. This establishes structure, allowed citations and output construction, not semantic correctness or Korean-language compliance.
- All 22 frozen packet input files match their initial hashes. Baseline packets are identical to each other, as are the three revised real-case packets. Producer receipts report the corresponding input digests and bounded file access; these are producer-reported transport records, not independent provider traces.
- Existing report v2/v3 compatibility, evidence-request limits, no automatic retry, usage projection and run freezing remain covered by the focused checks.

Private `eval-20261002-136` under the [archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis) retains exact inputs, outputs, snapshots and checks. The [functional evaluation](eval-0108-functional-proposal-follow-through.md) owns behavior, source fidelity, output-quality limitations and the production-execution gap.
