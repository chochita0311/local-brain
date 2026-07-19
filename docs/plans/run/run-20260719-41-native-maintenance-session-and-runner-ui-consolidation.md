# RUN-20260719-41: Native Maintenance Session And Runner UI Consolidation

## Metadata

- ID: `run-20260719-41`
- Status: `passed`
- Feature: [feat-0036-native-maintenance-session-and-runner-ui-consolidation](../feature/feat-0036-native-maintenance-session-and-runner-ui-consolidation.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Active Spec: [spec-0036-native-maintenance-session-and-runner-ui-consolidation](../spec/spec-0036-native-maintenance-session-and-runner-ui-consolidation.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal And Selected Loop

- Correct the Session source contract, simplify the Runner UI, expose its exact execution command, and return evidence to the human owner.
- Route: `Orchestrator → Spec Agent → Builder → Contract → Design → Functional → UX Heuristic → Fix if required`.

## Surface Lanes

- Runner and ingestion: native persistence, scan/link/inheritance, stream producer removal.
- Dashboard and Workstream UI: marker removal, exact command display, responsive containment.
- Documentation/generated: current owner contracts, Data Model/schema parity, correction history.

## Contract Surfaces

- Claude CLI argument list and stdin prompt boundary.
- Native Claude JSONL Session/Usage ownership and Run marker linkage.
- Workstream Run endpoint and removed marker endpoint/controls.
- Session schema constraints and generated presentation.

## Invocation Context

- Golden sources: FEAT-0036, SPEC-0036, code/schema implementation truth, local `claude --help`.
- Relevant policies: Task Runner, Data Model, Usage/cost, privacy, design constitution, design/interaction evaluation.
- Optional skills or tools expected: `screen-alignment` in `extend` mode; in-app browser control.

## Current Artifacts

- Spec: [spec-0036-native-maintenance-session-and-runner-ui-consolidation](../spec/spec-0036-native-maintenance-session-and-runner-ui-consolidation.md)
- Contract: [eval-0036-contract](../evaluation/eval-0036-contract-native-maintenance-session-and-runner-ui-consolidation.md)
- Design: [eval-0036-design](../evaluation/eval-0036-design-native-maintenance-session-and-runner-ui-consolidation.md)
- Functional: [eval-0036-functional](../evaluation/eval-0036-functional-native-maintenance-session-and-runner-ui-consolidation.md)
- UX heuristic: [eval-0036-ux](../evaluation/eval-0036-ux-native-maintenance-session-and-runner-ui-consolidation.md)

## Current Route

- Next role: Human owner.
- Current blocker classification: none.
- In-run route: Attempt 1 passed all required evaluators.
- Post-run recommendation for human review: accept.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: native Claude Session ownership, simplified UI, and exact command confirmation satisfy the corrected contract.
  - notes: 138 tests, privacy, generated-schema, Mermaid, desktop/320 browser, and guarded actual-data cleanup evidence passed.

## Post-Contract Regression Check

- Needed: yes.
- Result: passed.
- Notes: targeted and 138-test full suites, Data Model/Schema/audit/Mermaid checks, privacy, browser, and actual-data integrity passed.

## Human Review Outcome

- Decision: implementation boundary approved; final result pending review.
- Returned layer if any: FEAT-0035 producer contract returned to planning.
- Follow-up run: this Run.

## Continuity Notes

- `2026-07-19`: initialized from the corrected planning layer after the owner rejected `--no-session-persistence`, requested native Session ownership, removed marker surfaces, and required exact command confirmation.
- `2026-07-19`: Attempt 1 passed Contract, Design, Functional, and UX evaluation. The two empty historical synthetic Sessions were removed; their Run ledger rows and the valid schema constraints remain.
