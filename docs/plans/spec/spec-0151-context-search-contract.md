# SPEC-0151: Context Search Source And Storage Contract

## Metadata

- ID: `spec-0151`
- Status: `approved`
- Feature: [FEAT-0151](../feature/feat-0151-context-search-contract.md)
- Parent PRD: [PRD026](../prd/prd-0026-context-search-grounded-local-answers.md)
- Run: [run-20261029-223-context-search-contract](../run/run-20261029-223-context-search-contract.md)
- Attempt: 1
- Execution Profile: `foundation-contract`
- Required Evaluators: contract, functional

## Contract

Source/model-storage ownership and bounded read-only tool contracts; no dialogue persistence or model execution.

Use the current [Context Search owner](../../policies/project/context-search.md) and [storage contract](../../policies/project/installation-and-storage.md). Scope is Approved First Delivery. Source tools only use server-enumerated source IDs; bound traversal/read/results and return coverage/evidence. Read regular files only, reject path escape/symlink changes, preserve partial/currentness observations. Private dialogue/tool data stays request/page-memory only. Public assets remain Hub-owned and app caches/metadata stay separate.

For product surfaces use screen-alignment extend: existing shell/tokens/Settings cards, central input and transcript, model selector and small evidence disclosure. Preserve global search and responsive320px access. Clear on settings/navigation/hidden/pagehide/pageshow; abort pending generation and discard late responses. Only current page messages may supply user/assistant history; no client system/tool authority. Local model worker uses pinned offline assets; no global networking monkeypatch in web app.

## Verification

Focused source/model/protocol/route tests and owner docs; for visible behavior run isolated source host and actual browser at desktop/320. Exercise installed/missing/busy/error/cancel, model selection, repeated turns and leave/back restoration. Real4B/8B use synthetic files only and no downloads, with time/memory/host limits reported. Full regressions, privacy, catalog/link/diff and wheel before completion; native binary/recipient acceptance remains separate.
