# EVAL-0066: Local AI Source Identity Contract — Functional

## Metadata

- ID: `eval-0066-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260802-71`
- Attempt: `1`
- Feature: [feat-0066-local-ai-source-identity-contract](../feature/feat-0066-local-ai-source-identity-contract.md)
- Spec: [spec-0066-local-ai-source-identity-contract](../spec/spec-0066-local-ai-source-identity-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Source registry identity and provider semantics
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Verified fresh and compatible startup, current scanner/query behavior,
  same-native-ID isolation, and full adjacent regressions.

## Checks

- Fresh startup accepts explicit Claude, Codex, Context, and additional Codex
  source identities.
- Legacy startup preserves normalized Session, source-file, Usage, pin, search,
  and user-link descendants and a second startup makes no structural change.
- `codex` and `codex-company` can store an identical external Session ID without
  collision while sharing Codex normalization behavior.
- Current Claude and personal Codex scans, Maintenance classification, Usage,
  Session inventory/detail, pins, retrieval, Workstreams, and Runner regressions
  remain compatible.
- Source-scoped activity filtering accepts arbitrary stable source keys rather
  than a hard-coded provider list.

## Evidence

- Targeted identity and migration tests: 6 passed.
- Full suite: 297 passed in 2.042 seconds.
- Existing Starlette `TemplateResponse` deprecation warning remains unrelated and
  non-blocking.

## Evidence Gaps

- No browser evaluation was required because this Foundation Feature makes no
  visible template or interaction change.

## Findings

- None.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-08-02`: functional evaluation passed attempt 1; FEAT-0067 may now enter
  the loop.
