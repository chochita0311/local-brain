# EVAL-0108 Contract: Context Comparison

## Metadata

- ID: `eval-0108-contract-context-comparison`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete` for the frozen comparison and six result values; `partial` for production execution
- Highest Evidence Level: comparable surrogate execution with unchanged result validation
- Run: [RUN-20260929-127](../run/run-20260929-127-personal-insight-context-comparison.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Created: `2026-09-29`

## Verified Boundary

- Arm A's prompt is byte-identical to the preceding core-v3 comparison. Arm B preserves every original event and the Session order, adding eight complete neighboring messages selected by sequence around two previously fixed anchors.
- Both original anchors resolve as current against the read-only database: source, eligibility, role, and complete-text revision agree. This is a current reference check; historical classification lineage was not archived.
- Core v3, selected playbooks, and result schema are identical in both arms. Natural routing after the addition also selects the same types, although the experiment explicitly holds the original bundle fixed.
- The original sample contains 100 Sessions and 297 excerpts; the expanded sample has the same Sessions and 305 excerpts. Added text is 2,068 characters; total excerpt text is 97,025 characters. All eight additional messages are complete, with no clipping.
- Arm B is a manual experimental extension. It exceeds the production excerpt-count cap, and one added message exceeds the production per-excerpt cap. It is not a conforming output of the unchanged production evidence producer. No production cap or schema was changed.
- All four real-sample outputs and both synthetic outputs pass the unchanged `validate_guided_result` function. No output was repaired after generation. This establishes structural validity, not appropriate or useful advice.
- Lossless prompt chunks, preserved original evidence, identical schema and guide, and raw-output hashes are recorded in the private archive.

## Limits

Six fresh producer contexts used inherited agent bindings; the interface does not expose resolved model identity, sampling parameters, or seed. Subagent execution does not validate product CLI isolation, billing, history, or provider behavior. The read-only reconstruction of the old sample from the current database differs after additional pre-cutoff messages were imported; the original archive remains the comparison source of truth. Project distribution diagnostics join frozen Session IDs to current working-directory metadata and must not be represented as a frozen historical project classification.

See the [functional evaluation](eval-0108-functional-context-comparison.md) for the failed redundant-request check and the limitation in the intended positive control. Contract success does not override those findings.

## Retention

Inputs, raw outputs, provenance checks, distribution diagnostics, and independent reviews are private under the [evaluation archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis). Only sanitized conclusions are tracked here.
