# EVAL-0108 Functional: Guide Behavior

## Metadata

- ID: `eval-0108-functional-guide-behavior`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS WITH SUGGESTIONS`
- Evidence Coverage: `partial` for broader advice usefulness and product execution; all planned surrogate cases completed
- Highest Evidence Level: comparable rerun with fresh producers and independent content review
- Run: [RUN-20260928-126](../run/run-20260928-126-personal-insight-guide-behavior.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`, `docs-content`
- Created: `2026-09-28`

## Method And Results

Three fresh subagents analyzed one frozen product `discover` input with core v2. Three new subagents analyzed the same evidence with core v3. The schema, selected playbooks, inherited agent binding, evidence, and analysis task were held constant; the guide version and its existing output bounds changed. Producers received no earlier answer, evaluation key, or correction feedback. Each reported complete input reads. Separate fresh evaluation subagents reviewed each phase; the second reviewer did not read the first phase's outputs or verdicts. The primary agent compared phases and reviewed the synthetic controls.

| Check | Core v2 | Core v3 |
| --- | --- | --- |
| Unchanged product validator | 2 of 3 accepted | 3 of 3 accepted |
| Main analysis outcome | 3 bounded evidence requests, no findings | 3 bounded evidence requests, no findings |
| Independent content judgment | 3 PASS for the admitted sample | 2 PASS, 1 PASS WITH SUGGESTIONS |
| Supported synthetic opportunity | One reversible trial | One reversible trial |
| Normal-work synthetic control | No actionable finding | No actionable finding |

The baseline rejection is the hidden request-reference limit described in the [contract evaluation](eval-0108-contract-guide-behavior.md). No produced answer was repaired to improve these counts. The synthetic controls cover a visible request/correction pair with an ordinary successful case, and intentional exploration/restatement with repeated instructions. One fresh control producer per phase handled both cases, so these controls are not four independently isolated contexts.

All six main outputs differed in wording. Their candidate issue and cautious conclusion were substantially shared; follow-up evidence requests differed. All three revised outputs chose the same reference set. This is observed convergence on one fixed sample, not three new improvement ideas, proof of general stability, or a statistically established gain from the guide edit.

## Quality Findings

- Both independent reviewers found the main abstentions justified. Missing neighboring dialogue and owner outcome evidence prevented a sound new prescription; existing completion reports were treated as reports, not confirmed effects. No clear immediately actionable opportunity was demonstrated to have been missed within the admitted sample and selected categories.
- One revised output asked for conversation evidence plus related documents. The reviewer recommended requesting the documents only if the initial conversation leaves the relevant uncertainty unresolved. This is a non-blocking output-level scope suggestion; it does not justify another general guide rule or rewriting the frozen result.
- The two synthetic controls preserved useful proposal and no-finding behavior. Actual-work results contain no proposed intervention, so the practicality of a real intervention and its owner benefit remain untested.
- The frozen input includes analysis or guide-maintenance material alongside ordinary work. The six outputs did not use that material as evidence of an ordinary-work problem. Evidence admission and bounded neighboring-turn expansion are follow-up investigation candidates; this experiment does not establish a specific filter or routing fix.

## Checks, Gaps, And Acceptance

- `.venv/bin/python -m unittest discover -s tests -p 'test_personal_insight*.py' -v`: 25 tests pass after correction; 24 passed before the added regression case.
- The plan artifact catalog is current, all 68 local link targets in the affected owner/trace documents exist, `git diff --check` is clean, and the repository privacy check passes for 1,102 candidate files.
- Product validation was applied to all six original main outputs and four synthetic control outputs. The original over-limit case remains rejected by design; the other nine pass.
- Exact prompt transport, unchanged evidence/schema/playbooks, preserved core v2 text, and preserved earlier core rules were checked. Full output and input hashes remain in the private archive.
- Read truncation was repaired by complete rereads. A control producer initially could not invoke a bare `python` executable; it resumed with an available local reader before producing either analysis. These were transport interventions, not answer coaching or model retries after grading.
- The subagent interface does not expose a reproducible sampling seed or resolved model identity. This is a surrogate behavior comparison, not the configured product CLI, its pricing, tool isolation, or actual history flow. One sample and three repetitions per revision cannot establish broad reliability, category coverage, or personal productivity.
- The gaps do not block the bounded disclosure correction or completion of the requested experiment. They do block a claim that the real product has demonstrated useful personal improvements. More repeat runs on unchanged shallow evidence are not a substitute for the particular missing context.

## Retention

Private source excerpts, actual topic details, raw answers, and reviewer citations remain in the evaluation archive defined by the [Developer Guide](../../policies/project/developer-guide.md#personal-improvement-analysis). This tracked report contains only method, aggregate results, and sanitized findings. No product Run records or personal work changes were created by the experiment.
