# FEAT-0108: Personal Improvement Guide And Finding Contract

## Metadata

- ID: `feat-0108`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Created: `2026-09-27`
- Updated: `2026-10-02`

## Goal

Define a versioned, occupation-neutral analysis guide and finding value contract so a later model Run can select relevant improvement questions, reason from bounded Session evidence, abstain when support is weak, and return a reviewable practical suggestion without inheriting Workstream or vendor ownership.

## Acceptance Contract

- A short core guide applies to every `ask` or `discover` Run. It interprets the owner's question and goal, checks the selected evidence manifest and coverage, makes all eleven bounded playbooks available and selects a finding type from the owner goal and observed friction, distinguishes direct observations from hypotheses, tests alternative explanations and counterexamples, and prefers the smallest useful intervention. A no-finding outcome is valid.
- The guide must not treat a current or earlier personal-improvement analysis conversation, generated explanation, suggestion, or its child activity as evidence about the owner's ordinary work, even if the analysis conversation is visible in Sessions.
- Versioned playbooks cover the 11 types in the [research framework](../research/session-improvement-analysis-framework.md): task framing, request and feedback, context recovery, repeated procedure, learning, verification, information access, decision memory, task fit and cost, personal value, and configurable-assistant behavior. The final type is conditional on that environment; the guide does not presume a software-development occupation.
- Each playbook states trigger and exclusion signals, evidence questions, plausible benign alternatives, intervention choice, output sketch, and one owner-checkable follow-up. It identifies when current normalized message-only evidence cannot support its claim. A playbook may be selected without forcing a finding.
- The guide and output shape use stable versions. The future Run records exactly which core and playbook versions it used, and a later guide update never silently rewrites a frozen finding.
- Every new report explains its candidate selection with admitted anchors, and each finding explains its type choice. Already supplied complete conversation messages cannot be requested again; truncated or omitted messages need exact bounded targets under the frozen scope.
- The output is one bounded report with at most three findings, an explicit no-actionable-finding result, or a request for bounded additional evidence. Each finding contains the owner's relevant goal, observation, source-backed evidence references, counterexample or its absence, alternative explanation, scope and missing coverage, proposed action, expected benefit as a hypothesis, effort or tradeoff, and an observable follow-up check. Observation, inference, and owner-confirmed outcome remain distinct. When a concrete change is supported, the report value also supplies a bounded work-session handoff brief: goal, proposed change, scope, constraints, first steps, and a way to judge the result.
- A handoff explains where and how to apply its proposed change: mechanism and target, concrete content, actors, activation, initial setup and recurring work. It distinguishes a bounded trial from conditional adoption, marks unresolved placement/loading facts, and does not make repeated user prompting the default remedy for an assistant error. The [Spec](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md#concrete-application-handoff) owns the detailed contract.
- Existing advice is assessed for evidenced application and outcome, including explicit deferral. A useful missing application step may carry that advice forward without requiring a new idea. The [existing-proposal contract](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md#existing-proposal-follow-through) owns the decision rules; no persisted adoption state is introduced.
- A recurrence claim needs distinct supporting Session contexts and a disconfirming check; repeated excerpts from one Session are not independent recurrence. The initial FEAT-0107 sample can route candidate questions but cannot by itself certify a pattern that depends on omitted conversation turns. The guide must request targeted expansion or abstain rather than fill the gap by inference.
- The intervention vocabulary includes a better request or review method, worked example, learning resource, template, checklist, decision note, document, script, focused skill, assistant setting, scoped tool, or no persistent change. Neither a skill nor `AGENTS.md` is the default remedy.
- No universal productivity score, causal improvement claim from Session counts, automatic local edit, external write, or model invocation belongs to this Feature. A candidate supported only by token volume, spend, Session duration, skill invocation count, or a single ambiguous phrase must abstain or seek owner clarification.
- The first finding contract describes owner review and follow-up as future state transitions, but this Feature does not persist review decisions. Its value shape must leave a stable finding ID and versioned provenance for later independent Run and review owners.

## Scope Boundary

- In: versioned core/playbook resource shape, routing rules, evidence sufficiency and abstention rubric, bounded report/finding schema, an additional-evidence request shape, intervention vocabulary, source and inference labels, and synthetic examples for useful, ambiguous, and no-finding outcomes.
- Out: model selection or prompting for one provider, Run scheduling, model call, private Session read, Markdown file writing or export, finding persistence, review-state mutation, proactive candidate storage, UI, automatic edits, and judging actual productivity.

## Contract Surfaces

- Input: one FEAT-0107 evidence manifest or a synthetic value with the same versioned shape, plus `ask` question or `discover` intent and optional user-stated goal.
- Output: validated, versioned report and finding values with evidence references into the manifest, explicit uncertainty, and enough structure for a later private Markdown report and optional work-location copy. This Feature defines the value shape, not the file writer.
- Owner: a future product-neutral guide package under `src/localbrain/` with a documented version and provenance; it is not a repository-wide assistant instruction or Workstream Run template.
- Consumer: later independent analysis-Run and Insights Features.
- Source rationale: [research framework](../research/session-improvement-analysis-framework.md) and [proposed type-specific playbooks](../research/session-improvement-playbook-drafts.md); durable product terms remain under [Product Model](../../policies/project/product.md) and privacy boundaries under [Privacy And Data Handling](../../policies/project/privacy-and-data.md).

## Pass Or Fail Checks

- A broad nontechnical question routes to relevant general playbooks and yields no harness recommendation without environment evidence.
- A repeated clarification pattern can produce a source-linked, bounded suggestion only after checking whether it was healthy exploration, changed requirements, or an AI error.
- A lone repeated term, high spend, long Session, or skill count cannot itself produce a finding or a productivity score.
- A report with missing counterevidence, stale references, or inadequate message coverage labels the gap and either narrows the claim or abstains.
- A candidate that needs omitted conversation neighbors or another independent example requests bounded additional evidence instead of turning a sampled excerpt into a recurrence claim.
- A no-finding report is structurally valid and tells the owner what was reviewed and why it could not support a useful change.
- Versioned guide and finding values reject unknown fields, unsupported evidence IDs, unbounded prose or finding counts, and claims of owner-confirmed outcomes that the owner has not supplied.
- Synthetic cases cover general work, learning, developer harness configuration, false positives, and useful no-change results without private Session content.

## Dependencies

- Approved PRD-0018 upper boundary.
- FEAT-0107 evidence manifest value shape. This Feature may be planned while FEAT-0107 is in its execution loop; a later model consumer must wait for the evidence contract to pass.
- The analysis engine choice is not needed to define the guide and finding value contract.

## Regression Surfaces

- Existing Session Insights skill ranking, Workstream Task Runner result schema, Session retrieval evidence, privacy handling, and any future analysis Run that consumes the guide version.

## Harness Trace

- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Run: [RUN-20260928-121](../run/run-20260928-121-personal-improvement-guide-and-finding-contract.md)
- Guide behavior comparison: [RUN-20260928-126](../run/run-20260928-126-personal-insight-guide-behavior.md)
- Evidence-context comparison: [RUN-20260929-127](../run/run-20260929-127-personal-insight-context-comparison.md), [contract](../evaluation/eval-0108-contract-context-comparison.md), [functional](../evaluation/eval-0108-functional-context-comparison.md)
- Requested-context follow-up: [RUN-20260929-130](../run/run-20260929-130-personal-insight-requested-context.md), [contract](../evaluation/eval-0108-contract-requested-context.md), [functional](../evaluation/eval-0108-functional-requested-context.md)
- Decision threshold and scope correction: [RUN-20261001-131](../run/run-20261001-131-personal-insight-decision-threshold.md), [contract](../evaluation/eval-0108-contract-decision-threshold.md), [functional](../evaluation/eval-0108-functional-decision-threshold.md), [fix](../fix/fix-0108-output-review-scope.md)
- Explanation-question audit: [RUN-20261001-132](../run/run-20261001-132-personal-insight-explanation-question.md), [contract](../evaluation/eval-0108-contract-explanation-question.md), [functional](../evaluation/eval-0108-functional-explanation-question.md)
- Proposed response-review trial: [RUN-20261001-133](../run/run-20261001-133-personal-insight-explanation-trial.md), [contract](../evaluation/eval-0108-contract-explanation-trial.md), [functional](../evaluation/eval-0108-functional-explanation-trial.md)
- Concrete application handoff: [RUN-20261001-134](../run/run-20261001-134-personal-insight-application-handoff.md), [contract](../evaluation/eval-0108-contract-application-handoff.md), [functional](../evaluation/eval-0108-functional-application-handoff.md)
- Existing-proposal follow-through: [RUN-20261002-136](../run/run-20261002-136-personal-insight-proposal-follow-through.md), [contract](../evaluation/eval-0108-contract-proposal-follow-through.md), [functional](../evaluation/eval-0108-functional-proposal-follow-through.md)
- Execution profile: `foundation-contract`
- Foundation evaluator reports: [contract](../evaluation/eval-0108-contract-personal-improvement-guide-and-finding-contract.md), [functional](../evaluation/eval-0108-functional-personal-improvement-guide-and-finding-contract.md)
- Initial guide behavior reports: [contract](../evaluation/eval-0108-contract-guide-behavior.md), [functional](../evaluation/eval-0108-functional-guide-behavior.md)

## Continuity Notes

- `2026-09-27`: drafted as the next independent foundation boundary while the first evidence producer is in progress. The owner asked for a broadly useful AI-use improvement guide, not a harness-only audit. This proposed guide has no model or persistence side effect and needs its own Feature review before Spec or code.
- `2026-09-27`: clarified that initial sampling is a candidate discovery boundary; conversation-level recurrence needs targeted expansion or explicit abstention.
- `2026-09-28`: the owner confirmed that improvement-analysis conversations must not become source evidence for later improvement analysis. Visibility in Sessions remains a separate product decision.
- `2026-09-28`: the owner chose analysis-only Runs with a Markdown report for use in a separate work Session. The guide's proposed output shape now includes a bounded handoff brief; a later product Feature owns file rendering and explicit local export.
- `2026-09-28`: after the documentation and RUN-120 review, the owner chose to complete this detailed guide before any real personal analysis Run. The existing acceptance contract is approved as the next foundation boundary; provider execution remains separate.
- `2026-09-28`: RUN-121 passed the product-neutral guide and result contract with source inspection and synthetic functional cases. This foundation pass did not start an actual analysis Run or assess model-generated advice.
- `2026-09-28`: the owner requested independent subagent analysis and review before and after justified guide edits. RUN-126 compared three core v2 and three core v3 outputs on the same frozen evidence, plus synthetic proposal/abstention controls. Core v3 exposes existing output limits after a hidden citation cap rejected one baseline answer. This is a bounded surrogate comparison; actual product CLI behavior and owner benefit remain unverified.
- `2026-09-29`: the owner continued with a frozen-input versus neighboring-context comparison and asked how discovery chooses work to inspect. RUN-127 completed four real-sample and two synthetic analyses with core v3 unchanged. All outputs validate, but one requests already supplied context; the intended positive control has unsuitable selected categories. The functional evaluation records the failed check and remaining discovery coverage without changing the earlier foundation acceptance or authorizing a production sampling policy.

- `2026-09-29`: the owner approved the three follow-ups from RUN-127. [RUN-128](../run/run-20260929-128-personal-insight-selection-contract.md) adds core v5/report v3, goal-led selection over the full bounded catalogue, request-feedback v2, and exact missing-message validation. Historical packages remain intact; [RUN-129](../run/run-20260929-129-personal-insight-scope-and-requests.md) owns the separate consumer/UI change.

- `2026-09-29`: RUN-128 passed its bounded contract with a partial functional pass and recorded suggestions. Core v5 adds the observed prose-numbering correction after v4 testing; all intermediate outputs and guide hashes are retained. Two same-input real analyses chose different episodes, while a third after the narrow correction remained a request for context. This does not establish useful real-world findings or owner benefit.

- `2026-09-29`: the owner continued with an exact requested-context supplement and fresh producers/reviewer. RUN-130 completes three original-input and three supplemented-input analyses with the guide unchanged. All validate and avoid supplied-message repetition; supplemented outcomes span a trial, further context, and no new finding. The functional report retains an initial-goal admission ambiguity and local precision suggestions. The proposed trial is a reviewable hypothesis, not verified usefulness or an accepted relaxation of the playbook threshold.

- `2026-10-01`: RUN-131 clarifies future-trial versus current-problem evidence in core v6 and adds the explicit retrospective request-feedback route. The first three real answers and four controls expose one output-review scope failure. Request-feedback v4 clarifies that existing boundary; three new first answers and another fresh review support the correction. Contract passes; functional passes with a source-attribution suggestion and partial coverage. All raw failures remain preserved. Final-version control regression, example independence, actual product execution, and owner benefit are not established.

- `2026-10-01`: RUN-132 audits the unchanged current guide in ask mode with three identical-input analyses, four separate controls and a fresh reviewer. The real answers converge on a narrow response-review trial; the controls distinguish substantive correction, accepted learning, missing context and unsupported self-blame. Contract passes and functional passes with precision suggestions and partial coverage. No supplement or guide correction is required for this trial; actual owner benefit, retrieval quality and product execution remain unverified. These new ask controls do not retroactively rerun RUN-131's discovery controls.

- `2026-10-01`: RUN-133 applies the proposed review instruction in one same-source comparison using an owner-selected historical question and current code. Fresh usual and additional-instruction answers both resolve the question; a condition-hidden reviewer finds no overall winner and one precision suggestion in the latter. The bounded content check passes with suggestions, while incremental benefit and owner comprehension remain unproven. No permanent guide change follows from this trial.

- `2026-10-01`: the owner asks the feature to include concrete adoption detail rather than leave the choice between a temporary prompt, policy edit or skill unclear. RUN-134 adds core v7 within report v3's existing handoff fields. One baseline, two revised same-input analyses and two separate controls pass structural checks; fresh independent review passes the four revised outputs for application specificity and all five for evidence fidelity. The narrowed behavior comparison passes with partial coverage. Actual adoption and benefit remain unverified; user instruction files and installed skills are unchanged.

- `2026-10-02`: a real v7 result stopped at prior-proposal duplication while application remained unknown. RUN-136 adds core v8 decision rules for useful application help, state uncertainty, effective adoption and deferral. Two baseline answers stop at a status request or duplication; all three same-input revised answers supply a concrete one-response application route. Three separate controls preserve restraint. Contract passes 28 focused tests; functional passes with suggestions and partial coverage. A Japanese sentence and localized source-chronology wording/typo remain recorded first-answer defects. The server now loads v8 for new Runs; existing reports are preserved. No new paid analysis or actual intervention benefit was measured.
