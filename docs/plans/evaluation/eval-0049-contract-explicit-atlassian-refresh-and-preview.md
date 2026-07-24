# EVAL-0049: Explicit Atlassian Refresh And Preview — Contract

## Metadata

- ID: `eval-0049-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260723-54`
- Attempt: `1`
- Feature: [feat-0049-explicit-atlassian-refresh-and-preview](../feature/feat-0049-explicit-atlassian-refresh-and-preview.md)
- Spec: [spec-0049-explicit-atlassian-refresh-and-preview](../spec/spec-0049-explicit-atlassian-refresh-and-preview.md)
- Execution Profile: `fullstack-product`
- Surface Lane: local scope → authorized mixed-source manifest → atomic Item application
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated exact scope membership, freshness defaults, calculated reads, mixed Source Instance authorization, single-source compatibility, provider/result authority, atomic application, catalog bounds, owner documentation, and external-call boundaries.

## Checks And Evidence

- Item, Space, Thread, Workstream, and all-known previews resolve from SQLite only. Workstream combines direct and Thread links by stable Resource ID; Thread remains direct-only; all-known never enumerates the remote estate.
- Unknown, due, stale, and unavailable targets default selected. Current targets remain visible and opt-in. Preparation recomputes selection and rejects an empty, outside-scope, unavailable, or greater-than-20-read batch.
- One mixed-instance user action produces one maintenance Run. Every mixed target carries its own authorized Source Instance; the aggregate projection is nullable and uses `mixed` only when services differ. Existing single-source manifests retain the original source shape.
- Every request is authorized against the target's current FEAT-0044 capability before queuing. A target cannot change Source Instance, locator, request, field allowlist, or identity during execution.
- Jira reference/metadata/indexed coverage yields the approved metadata/description plans. Reference application strips remote metadata/body persistence. Confluence indexed Page reads combine metadata, content, and hierarchy under one approved operation.
- Jira Space scope checks known selected Items only. One explicitly selected Confluence catalog page uses a 200-result bound; new Page identities become indexed-intent stale stubs and no body is fetched by catalog expansion.
- Runner completion validates the assembled result and applies all target changes inside the same transaction as terminal Run state. Invalid target/locator/source mapping rolls back before Item mutation.
- Product, architecture, privacy, Task Runner, Maintenance Execution, and Atlassian Source Memory owners match implementation. Schema presentation and the 491-object cleanup audit are current.

## Evidence Gaps

- No company Atlassian content was retrieved. Provider and Runner paths were exercised with synthetic dispatch and result evidence only.

## Findings

- None.

## Route

- Next action: `pass` and release Design, Functional, and UX Heuristic evaluation.
