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
- Updated: `2026-09-28`

## Goal

Define a versioned, occupation-neutral analysis guide and finding value contract so a later model Run can select relevant improvement questions, reason from bounded Session evidence, abstain when support is weak, and return a reviewable practical suggestion without inheriting Workstream or vendor ownership.

## Acceptance Contract

- A short core guide applies to every `ask` or `discover` Run. It interprets the owner's question and goal, checks the selected evidence manifest and coverage, routes to only relevant category playbooks, distinguishes direct observations from hypotheses, tests alternative explanations and counterexamples, and prefers the smallest useful intervention. A no-finding outcome is valid.
- The guide must not treat a current or earlier personal-improvement analysis conversation, generated explanation, suggestion, or its child activity as evidence about the owner's ordinary work, even if the analysis conversation is visible in Sessions.
- Versioned playbooks cover the 11 types in the [research framework](../research/session-improvement-analysis-framework.md): task framing, request and feedback, context recovery, repeated procedure, learning, verification, information access, decision memory, task fit and cost, personal value, and configurable-assistant behavior. The final type is conditional on that environment; the guide does not presume a software-development occupation.
- Each playbook states trigger and exclusion signals, evidence questions, plausible benign alternatives, intervention choice, output sketch, and one owner-checkable follow-up. It identifies when current normalized message-only evidence cannot support its claim. A playbook may be selected without forcing a finding.
- The guide and output shape use stable versions. The future Run records exactly which core and playbook versions it used, and a later guide update never silently rewrites a frozen finding.
- The output is one bounded report with at most three findings, an explicit no-actionable-finding result, or a request for bounded additional evidence. Each finding contains the owner's relevant goal, observation, source-backed evidence references, counterexample or its absence, alternative explanation, scope and missing coverage, proposed action, expected benefit as a hypothesis, effort or tradeoff, and an observable follow-up check. Observation, inference, and owner-confirmed outcome remain distinct. When a concrete change is supported, the report value also supplies a bounded work-session handoff brief: goal, proposed change, scope, constraints, first steps, and a way to judge the result.
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
- Execution profile: `foundation-contract`
- Latest evaluator reports: [contract](../evaluation/eval-0108-contract-personal-improvement-guide-and-finding-contract.md), [functional](../evaluation/eval-0108-functional-personal-improvement-guide-and-finding-contract.md)

## Continuity Notes

- `2026-09-27`: drafted as the next independent foundation boundary while the first evidence producer is in progress. The owner asked for a broadly useful AI-use improvement guide, not a harness-only audit. This proposed guide has no model or persistence side effect and needs its own Feature review before Spec or code.
- `2026-09-27`: clarified that initial sampling is a candidate discovery boundary; conversation-level recurrence needs targeted expansion or explicit abstention.
- `2026-09-28`: the owner confirmed that improvement-analysis conversations must not become source evidence for later improvement analysis. Visibility in Sessions remains a separate product decision.
- `2026-09-28`: the owner chose analysis-only Runs with a Markdown report for use in a separate work Session. The guide's proposed output shape now includes a bounded handoff brief; a later product Feature owns file rendering and explicit local export.
- `2026-09-28`: after the documentation and RUN-120 review, the owner chose to complete this detailed guide before any real personal analysis Run. The existing acceptance contract is approved as the next foundation boundary; provider execution remains separate.
- `2026-09-28`: RUN-121 passed the product-neutral guide and result contract with source inspection and synthetic functional cases. This foundation pass did not start an actual analysis Run or assess model-generated advice.
