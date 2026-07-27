# EVAL-0058: Session Pin Persistence Contract — Functional

## Metadata

- ID: `eval-0058-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260724-61`
- Attempt: `1`
- Feature: [feat-0058-session-pin-persistence-contract](../feature/feat-0058-session-pin-persistence-contract.md)
- Spec: [spec-0058-session-pin-persistence-contract](../spec/spec-0058-session-pin-persistence-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: pin operations, deterministic query, rescan-safe identity, and regressions
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Checks And Evidence

- Pin, repeat pin, membership, unpin, repeated unpin, and re-pin transitions returned the expected row-presence state.
- The deterministic list sorts newest pin first with Session ID as the tie-break and includes source plus workspace/path orientation without copying conversation content.
- The list limit rejects booleans, non-integers, zero, and values over 100.
- Session metadata update preserved the pin; Session deletion cascaded it.
- The operation module has no source writer, filesystem, network, model, MCP, or external-service dependency.
- Sixty-one focused tests and all generated-data/documentation checks passed.

## Evidence Gaps

- A native-file scanner integration test was not needed because the contract depends on the existing stable Session upsert, which is covered by current Session identity tests; the pin test verifies the equivalent retained-row update and the FK deletion boundary.
- Acceptance impact: none.

## Findings

- None.

## Regression Notes

- Existing Session hierarchy, migration, ingestion policy, Schema Presentation, and cleanup audit suites passed.

## Route

- Next action: `pass`.
