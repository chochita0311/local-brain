# FEAT-0153: Transient Context Search Conversation

## Metadata

- ID: `feat-0153`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Parent PRD: [PRD026](../prd/prd-0026-context-search-grounded-local-answers.md)
- Created: `2026-10-29`
- Authorization: Owner explicitly requested end-to-end implementation within Approved First Delivery, including Feature/spec creation; no additional persistence or external operation authority.

## Outcome And Acceptance

Read-only model-guided retrieval,4B/8B selector, same-page Q/A with source evidence, cancellation and clear-on-leave; isolated local inference.

## Scope And Dependencies

Dependencies: FEAT-0151 and FEAT-0152. Sequential producer-first execution. Preserve existing sources, Drive/schedules, public Hub assets, app metadata/private cache separation, native boundaries and all unrelated working changes. No new conversation database, browser persistence, model training, embedding-first prerequisite or external AI.

## Lanes And Evaluation

Primary owns contract/backend, then Settings/chat consumers and docs; logical roles sequential, no delegated agents. Synthetic source/protocol/storage/lifecycle tests before consumers; real cached model inference and rendered1440/320 states provide separately bounded evidence. Public fixtures only. Exact source/current/cache ownership and UI ephemeral reset are acceptance conditions.

## Harness Trace

- Active spec: [spec-0153-context-search-conversation](../spec/spec-0153-context-search-conversation.md)
- Active run: [run-20261029-225-context-search-conversation](../run/run-20261029-225-context-search-conversation.md)
- Parent acceptance remains human-owned after bounded evaluation.
