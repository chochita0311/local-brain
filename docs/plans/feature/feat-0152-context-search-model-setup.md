# FEAT-0152: Selectable Generation Model Setup

## Metadata

- ID: `feat-0152`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Parent PRD: [PRD026](../prd/prd-0026-context-search-grounded-local-answers.md)
- Created: `2026-10-29`
- Authorization: Owner explicitly requested end-to-end implementation within Approved First Delivery, including Feature/spec creation; no additional persistence or external operation authority.

## Outcome And Acceptance

Settings installation/verification for embedding plus4B/8B, common-cache reuse and local model availability; preserve embedding setup consumers.

## Scope And Dependencies

Dependencies: FEAT-0151. Sequential producer-first execution. Preserve existing sources, Drive/schedules, public Hub assets, app metadata/private cache separation, native boundaries and all unrelated working changes. No new conversation database, browser persistence, model training, embedding-first prerequisite or external AI.

## Lanes And Evaluation

Primary owns contract/backend, then Settings/chat consumers and docs; logical roles sequential, no delegated agents. Synthetic source/protocol/storage/lifecycle tests before consumers; real cached model inference and rendered1440/320 states provide separately bounded evidence. Public fixtures only. Exact source/current/cache ownership and UI ephemeral reset are acceptance conditions.

## Harness Trace

- Active spec: [spec-0152-context-search-model-setup](../spec/spec-0152-context-search-model-setup.md)
- Active run: [run-20261029-224-context-search-model-setup](../run/run-20261029-224-context-search-model-setup.md)
- Parent acceptance remains human-owned after bounded evaluation.
