# EVAL-0108 Contract: Explanation Question

## Metadata

- ID: `eval-0108-contract-explanation-question`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-132](../run/run-20261001-132-personal-insight-explanation-question.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Evidence Owner: [FEAT-0107](../feature/feat-0107-personal-insight-evidence-manifest.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `data`
- Created: `2026-10-01`

## Frozen Baseline

The owner requested question-mode analysis of clarification followed by assistant self-correction. A faithful concise restatement of the question, the unchanged production ask selector, core v6/request-feedback v4, all eleven playbooks and report v3 were frozen before execution. The indexed database was opened read-only with query-only enabled; the production selector ran without writes. The frozen manifest owns the cutoff and revision metadata. No source retrieval occurred after that initial selection.

Three fresh producers received the same real manifest and exact prompt. Four more fresh producers each received a separate synthetic control, the same question, byte-identical guide bundle and response schema. The controls cover a substantive unsupported conclusion, accepted learning, a missing original explanation, and an unsupported apology after a correct explanation. Each received only its assigned packet, with no expected answer or preceding producer output. Every producer used `fork_turns: none`, with no model override.

## Checks Performed

- All seven preserved first JSON answers pass the production `validate_guided_result` function against their respective manifests and bundles. Raw hashes remain unchanged; derived identified values are saved separately.
- All 37 frozen-value checks pass: relevant implementation hashes, five manifests/bundles/schemas/prompts, complete prompt-part reconstruction, current guide identity, and identical control guides/schemas.
- The missing-original control requests only the omitted, in-range message. It does not request any supplied complete message or expose numeric message positions in prose. Semantic necessity is covered by the functional evaluation.
- Reading receipts cover every complete prompt part. One producer recovered a truncated combined tool display by rereading complete parts. Three control producers report save-transport encoding failures before writing and successful identical-content retries. No saved first answer was repaired to pass validation.

No application code, guide text, schema or selection policy changed. This audit ran output validation and frozen-value checks; it did not rerun the unit suite, exercise a browser or invoke the product's model CLI. Those unperformed checks are not counted as passing.

## Coverage And Route

Coverage is complete for the declared seven-output and frozen-value checks. Structural validity does not establish diagnosis, usefulness, retrieval quality, generalization or owner benefit. The [functional evaluation](eval-0108-functional-explanation-question.md) owns those judgments and their limits. Exact resolved model, reasoning effort and seed are unavailable; an inherited company home is not a captured product invocation or billing receipt.

Private `eval-20261001-132` owns exact inputs, raw first answers, independent review and checks under the existing [evaluation archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis). Route: `pass` for this bounded contract audit.
