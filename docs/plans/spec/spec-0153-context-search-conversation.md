# SPEC-0153: Transient Context Search Conversation

## Metadata

- ID: `spec-0153`
- Status: `approved`
- Feature: [FEAT-0153](../feature/feat-0153-context-search-conversation.md)
- Parent PRD: [PRD026](../prd/prd-0026-context-search-grounded-local-answers.md)
- Run: [run-20261029-225-context-search-conversation](../run/run-20261029-225-context-search-conversation.md)
- Attempt: 1
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic

## Contract

Read-only model-guided retrieval,4B/8B selector, same-page Q/A with source evidence, cancellation and clear-on-leave; isolated local inference.

Use the current [Context Search owner](../../policies/project/context-search.md) and [storage contract](../../policies/project/installation-and-storage.md). Scope is Approved First Delivery. Source tools only use server-enumerated source IDs; bound traversal/read/results and return coverage/evidence. Read regular files only, reject path escape/symlink changes, preserve partial/currentness observations. Private dialogue/tool data stays request/page-memory only. Public assets remain Hub-owned and app caches/metadata stay separate.

For product surfaces use screen-alignment extend: existing shell/tokens/Settings cards, central input and transcript, model selector and small evidence disclosure. Preserve global search and responsive320px access. Clear on settings/navigation/hidden/pagehide/pageshow; abort pending generation and discard late responses. Only current page messages may supply user/assistant history; no client system/tool authority. Local model worker uses pinned offline assets; no global networking monkeypatch in web app.

## Verification

Focused source/model/protocol/route tests and owner docs; for visible behavior run isolated source host and actual browser at desktop/320. Exercise installed/missing/busy/error/cancel, model selection, repeated turns and leave/back restoration. Real4B/8B use synthetic files only and no downloads, with time/memory/host limits reported. Full regressions, privacy, catalog/link/diff and wheel before completion; native binary/recipient acceptance remains separate.

## Native And Publication Closeout

Owner explicitly authorizes native build/integration and all-session publication review in Run226. Preserve the approved source/model/ephemeral contract while validating the frozen worker entry, native route/auth boundary and packaged assets. Current Learning/schema owner/checker debt must be reconciled rather than silently publishing known stale validation. Use synthetic corpus and isolated application roots; no user-server restart or live Drive replay. Review public candidate and docs with requested read-only subagents, then commit/push only verified nonprivate material. This extends deployment evidence and authorizes publication; it does not authorize private data disclosure, saved answers, live credentials, history rewriting or notarization claims.
