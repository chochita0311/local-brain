# RUN-20260724-62: Atlassian Add And Registered Scope Flow

## Metadata

- ID: `run-20260724-62`
- Status: `passed`
- Feature: [feat-0054-atlassian-add-and-registered-scope-flow](../feature/feat-0054-atlassian-add-and-registered-scope-flow.md)
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Active Spec: [spec-0054-atlassian-add-and-registered-scope-flow](../spec/spec-0054-atlassian-add-and-registered-scope-flow.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal And Selected Loop

- Replace connection-administration-led setup with a persisted-scope-led Add flow while preserving internal Source Instance identity and explicit remote-read boundaries.
- Route: `Orchestrator → Spec Agent → Fullstack Builder → Contract Evaluator → Design Evaluator → Functional Evaluator → UX Heuristic Evaluator`.
- Screen Alignment mode: `extend`.

## Delivered Contract

- Renamed top-level intents to `Browser | Add`.
- Added a producer-neutral persisted-scope projection that groups the same domain once, retains distinct MCP connections, and excludes evidence/candidates.
- Replaced equal left/right cards with one Add method selector.
- Split connected search into target Site, MCP connection, and execution owner.
- Added server-side target/connection domain validation before Run creation.
- Moved connection administration into a secondary disclosure.
- Connected the Atlassian template to the FEAT-0057 value registry for ten complete value families.
- Updated user overview, privacy, Atlassian Data Model ownership, generated dictionaries, focused tests, and UI contracts.

## Current Artifacts

- Spec: [spec-0054-atlassian-add-and-registered-scope-flow](../spec/spec-0054-atlassian-add-and-registered-scope-flow.md)
- Contract evaluation: [eval-0054-contract-atlassian-add-and-registered-scope-flow](../evaluation/eval-0054-contract-atlassian-add-and-registered-scope-flow.md) — `PASS`
- Design evaluation: [eval-0054-design-atlassian-add-and-registered-scope-flow](../evaluation/eval-0054-design-atlassian-add-and-registered-scope-flow.md) — `PASS`
- Functional evaluation: [eval-0054-functional-atlassian-add-and-registered-scope-flow](../evaluation/eval-0054-functional-atlassian-add-and-registered-scope-flow.md) — `PASS`
- UX heuristic evaluation: [eval-0054-ux-atlassian-add-and-registered-scope-flow](../evaluation/eval-0054-ux-atlassian-add-and-registered-scope-flow.md) — `PASS`
- Fix log: not created

## Verification Evidence

- `45` focused value-registry, UI-contract, and Atlassian registration/route tests passed after the final read-model correction.
- A same-domain synthetic case with official Atlassian MCP and company Gateway produced one registered target, two MCP connections, one deduplicated Space, and one Item count.
- Mismatched target domain plus connection failed with `target-connection-mismatch` and created zero maintenance Runs.
- Browser-rendered checks at `1440`, `920`, `700`, and emulated `320` widths showed no horizontal document overflow and contained Add controls.
- Target selection exposed both current MCP paths for the one Site.
- Page load made five localhost requests only: document, shared CSS, shared JS, Atlassian JS, and favicon. No remote Atlassian request or console error occurred.
- No real runtime user database or external Atlassian record was mutated; browser evidence used a temporary synthetic DB.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: registered-scope-led Add flow delivered.
  - notes: one visual QA finding corrected the scope header to count deduplicated logical Spaces rather than physical connection-specific rows.

## Human Review Outcome

- Decision: automatic sequential approval authorized on `2026-07-24`.
- Returned layer if any: none.
- Follow-up run: FEAT-0056.

## Continuity Notes

- `2026-07-24`: detailed physical inventory continues to retain connection-specific rows and provenance; only target orientation is logically deduplicated.
