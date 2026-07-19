# EVAL-0027: Schema Presentation Contract — Functional

## Metadata

- ID: `eval-0027-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-32`
- Attempt: `1`
- Feature: [feat-0027-schema-presentation-contract](../feature/feat-0027-schema-presentation-contract.md)
- Spec: [spec-0027-schema-presentation-contract](../spec/spec-0027-schema-presentation-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: deterministic generation, failure handling, regressions, packaging, and privacy
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: generated v1 presentation data and bounded installed-package loader, with no product route.
- Active spec: SPEC-0027 attempt 1.
- Evaluated build or commit: current unstaged FEAT-0027 implementation and final wheel.

## Checks

- Ran the Data Model parity checker and parsed all nine Mermaid definitions through the pinned local Mermaid bundle.
- Ran build then check mode and confirmed regenerated output is byte-current.
- Exercised missing output, stale bytes, missing semantic fields, malformed JSON, wrong schema version, missing required shape, and invalid one-owner mapping.
- Built the manifest twice and compared exact bytes.
- Patched SQLite connection observation during generation and verified the sole target is `:memory:`; patched Context-root migration to fail if reached and confirmed it is skipped.
- Built the final source distribution and wheel, inspected its file inventory, expanded it outside the repository, removed Node from `PATH`, and loaded the v1 manifest successfully without repository docs, runtime DB, or network.
- Ran Mermaid asset freshness/stale tests, all Python tests, privacy scanning, and whitespace checks.

## Evidence

- Schema-presentation contract tests: 10 of 10 passed.
- Complete Python suite: 95 of 95 passed.
- Data-model checker: 20 ordinary tables, one FTS5 object, 19 physical FKs, 20 explicit indexes, and eight owners passed.
- Mermaid parser: nine of nine diagrams passed; Mermaid asset check and deliberate stale-output test passed.
- Final wheel SHA-256: `c1e636f441fb421b9f8351025a32bfa03a9ca65dfd4043e6bbffd6f0f7c64847`.
- Final wheel contains `localbrain/schema-presentation.json`, `localbrain/schema_presentation.py`, the strict Mermaid adapter, the local bundle, asset manifest, and licenses.
- Isolated installed load returned the exact v1 schema with eight subjects and 21 tables while executed from `/tmp` with Node absent from `PATH`.

## Evidence Gaps

- None within the Feature contract. Browser evaluation is not required because no visible route or interaction was added.

## Findings

- No stale generation, malformed-input escape, package omission, runtime-row access, network dependency, Mermaid drift, or application regression remains.

## Regression Notes

- The full suite covers existing compatible migration behavior, including legacy row migration. Generated schema construction uses the new opt-out and never invokes it.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: passed attempt 1 with deterministic generation, bounded failures, complete regressions, final wheel inspection, and isolated installed loading.
