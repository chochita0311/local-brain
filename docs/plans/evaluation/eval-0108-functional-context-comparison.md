# EVAL-0108 Functional: Context Comparison

## Metadata

- ID: `eval-0108-functional-context-comparison`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `FAIL`
- Evidence Coverage: `partial`
- Highest Evidence Level: comparable fresh-producer surrogate execution with a fresh independent content review
- Run: [RUN-20260929-127](../run/run-20260929-127-personal-insight-context-comparison.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Created: `2026-09-29`

## Comparison

Two fresh producers received the original frozen input and two received the same input with eight complete neighboring messages. Guide, selected categories, schema, and transport were held constant. Two additional fresh producers received synthetic opportunity and benign-clarification cases. No producer received the rubric, previous outputs, or a proposed correction.

All six outputs pass structural validation. Both real-sample arms return two `needs_evidence` results and zero findings. Both expanded-input outputs distinguish an assistant's acknowledged scope substitution from an ordinary additional question, without turning either into a repeated user defect. Their requests still differ. This is a useful distinction in the observed reasoning, not proof that the added evidence establishes current friction or improves the owner's work.

The fresh reviewer inspected every result, all selected excerpts in the two cited real Sessions, all control evidence, bundles, schemas, and preservation metadata. It did not inspect the other real Sessions for missed opportunities or audit the source database. Its conclusions were:

| Output | Content result | Qualification |
| --- | --- | --- |
| A1, A2 | PASS | Bounded requests for absent or truncated material |
| B1 | FAIL | Requests four complete messages already supplied |
| B2 | PASS WITH SUGGESTIONS | Identify the missing original request more precisely |
| C1 | PASS within admitted scope | Invalid as the intended positive control |
| D1 | PASS | Correctly interprets ordinary completed editing |

## Observed Gap

One expanded-input result asks again for the two preceding and two following messages that are already present in full. Its separate request for an initial report may be justified, but the duplicated part fails the predeclared check against requesting supplied evidence. The second result appears to request earlier initial exchanges that are not supplied, but its wording could also refer to an already supplied corrective question; the reviewer recommends identifying the request that elicited the first incorrect result. Both requests remain bounded and structurally valid; schema validation cannot detect this semantic overlap.

The correction owner is the guide's evidence-request decision and any future expansion consumer. Before requesting more, distinguish facts established by supplied context, the particular remaining uncertainty, and the smallest missing event or owner answer. Do not automatically increase all sampling limits. This comparison does not establish that a prompt sentence alone fixes the failure.

## Control Validity And Routing

- The intended opportunity control shows a concrete goal and burden without supplying a solution. However, its router selects information access, verification/rework, and assistant configuration from words that also occur in the task's source material. The selected detailed playbooks do not fit the decision-support problem. The producer explicitly recognizes the goal and friction but returns no finding because the available categories do not support it.
- An input-only reviewer identified that mismatch before inspecting the output. This case is useful evidence of a coverage limitation in the selected categories; it cannot cleanly test whether the guide can discover a small trial under appropriate guidance. Do not grade the unchanged answer as a model failure solely because the original author expected a finding. Broader positive discovery remains unverified.
- The benign control presents a repeated question inside a two-audience writing task. The output checks the surrounding dialogue, recognizes accepted completion, and returns no actionable finding. This is one correct negative case, not a false-positive rate estimate.
- Selecting another category alone has not been tested. Whether the guide's single-observation permission and detailed exclusions support the intended opportunity needs review before claiming a routing-only fix.

## Discovery Selection And Product Implications

The current selector spreads Sessions across sources and months, favors recent Sessions within each bucket, and applies no project quota. Each Session supplies at most three short excerpts. Lexical routing then restricts the finding types; the model chooses candidates within that sample and type set. There is no random project picker, cross-project improvement-priority score, or previously reviewed-candidate rotation.

Working-directory counts for the frozen Session IDs are descriptive current metadata. They neither establish the cause of candidate convergence nor justify equating a directory with a semantic work topic. Frequency, duration, and spend do not determine improvement value. A same-input repeat need not uncover a new project or recommendation.

The next product boundary should make coverage and candidate-selection reasons understandable, prevent repeated requests for supplied context, and evaluate category coverage against the owner's actual task. Project balancing or broader automatic expansion remains a policy choice, not a measured fix from this comparison.

## Limits And Disposition

The bounded comparison is complete; the failed request check remains unresolved. Core v3 and production sampling are unchanged. The experiment does not establish broad useful discovery, a successful intervention, actual owner benefit, or product CLI behavior. An invalid positive expectation is an evidence gap, not a passed scenario. Further production behavior requires the owning spec and a bounded follow-up evaluation.

Verification completed: unchanged result validation for all six outputs, exact preservation and lossless-input checks, 99 local link targets across eight affected owner/report documents, a clean `git diff --check`, and repository privacy validation for 1,105 candidate files. No application behavior changed, so no additional application test suite or browser check was run.

Private evidence and detailed review remain under the [evaluation archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis). The [contract evaluation](eval-0108-contract-context-comparison.md) records preservation and validation separately.
