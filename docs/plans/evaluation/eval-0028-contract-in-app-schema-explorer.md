# EVAL-0028: In-App Schema Explorer — Contract

## Metadata

- ID: `eval-0028-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-33`
- Attempt: `1`
- Feature: [feat-0028-in-app-schema-explorer](../feature/feat-0028-in-app-schema-explorer.md)
- Spec: [spec-0028-in-app-schema-explorer](../spec/spec-0028-in-app-schema-explorer.md)
- Execution Profile: `fullstack-product`
- Surface Lane: data/contract, backend route, frontend integration, docs/design parity
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: manifest-only Schema Explorer.
- Active spec: SPEC-0028 attempt 1.
- Evaluated build or commit: current unstaged FEAT-0028 implementation, policies, tests, browser QA, and final wheel.

## Checks

- Verified the read model calls the passed bounded loader and imports no DB or documentation consumer.
- Verified global order/count/diagram parity, all eight area states, all 21 owned table states, canonical href construction, and selected-table relation filtering.
- Verified an invalid area, unknown or cross-area table, and table-without-area normalize to fixed bounded states without reflecting query input.
- Re-ran FEAT-0027 presentation freshness.
- Verified `GET /schema` uses the read model without `connect()`, marks `active_page="schema"`, and serves global, every area/table, invalid, missing, and malformed-package state as bounded HTML.
- Verified `Sources` remains destination 07 and `Schema` is destination 08 immediately after it, with matching visible and programmatic current state.
- Verified templates consume only packaged v1 fields, pass the exact app-owned Mermaid definition through JSON-safe text, and expose no row, mutation, SQL, cleanup, external asset, or reflected invalid-query surface.
- Verified the strict local adapter and route module are versioned static assets; ordinary subject/table anchors remain executable without JavaScript.
- Verified Design Constitution, design governance v6, Architecture, Schema Presentation, README, and Developer Guide own the durable route, eight-destination shell, Explorer family, and QA boundary.
- Inspected the final wheel and loaded the installed route from `/tmp` with repository docs, runtime DB, Node, and network unavailable.

## Evidence

- Three contract-view-model tests passed across every packaged subject and table.
- The current v1 manifest remained byte-current.
- Six Schema contract/route tests and the UI contract suite passed; the full suite passed 102 of 102 tests.
- The final wheel contains the v1 JSON, loader/read model, route composition, Schema/base templates, route module, CSS, strict Mermaid adapter, bundle, manifest, and licenses.
- Final wheel SHA-256: `be2bc8ca0c193060dc51d1a7b8a58a33f169700fa72ab1b96e7dc130df4c19fa`.

## Evidence Gaps

- None within the Feature contract.

## Contract Evidence

- Producer surfaces: passed v1 loader and package manifest.
- Consumer surfaces checked: Schema read model, HTML route, shell/template, route module, strict adapter, installed package.
- Schemas and routes checked: v1 subjects/tables/relations, canonical query value shape, `/schema`, all links/states, local assets, policies, and package inventory.
- Stale-assumption check: presentation, data-model, nine Mermaid, asset freshness, route tests, browser states, package load, privacy, and full regression passed.

## Findings

- No producer/consumer mismatch, runtime-data fallback, duplicate ERD, raw query reflection, external asset, policy drift, or package omission remains.

## Regression Notes

- All existing routes and UI tests passed; shell geometry and stable destinations 01 through 07 remain unchanged.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: data/contract gate passed with partial evidence; full Feature acceptance remains blocked on dependent lane evaluation.
- `2026-07-18`: final coverage completed after route, shell, local assets, policies, browser behavior, wheel, regressions, and privacy all passed.
