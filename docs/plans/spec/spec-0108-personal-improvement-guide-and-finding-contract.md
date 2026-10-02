# SPEC-0108: Personal Improvement Guide And Finding Contract

## Metadata

- ID: `spec-0108`
- Status: `approved`
- Parent Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-28`

## Owner And Value Contract

- `src/localbrain/personal_insight_guidance.py` owns deterministic guide selection and strict validation. Versioned Markdown under `src/localbrain/personal_insight_guides/` owns the core instructions and eleven category playbooks. The prior `personal_insight_guide.md` remains the historical v1 resource.
- The core guide and each playbook have independent stable versions. New Runs freeze core v8, all eleven detailed playbooks (request-feedback v4, the others v1), report v3, exact trusted text, and a route reason. This bounded catalogue avoids excluding an appropriate type because of incidental words in quoted source material. The caller supplies a FEAT-0107 manifest; this module reads no database, source file, runtime Run, or network service.
- Core v2/v3 and report v2 remain supported for their frozen Runs; historical core v4/v5/v6/v7 retain report v3. Guide/report mismatches are rejected. The JSON schema specifies structure; the trusted guide also discloses local acceptance limits. Historical resources and reports are not rewritten.
- For `ask`, address the owner's actual question first. For `discover`, identify a visible owner goal and friction before choosing a type. Source subject matter alone cannot select a type or establish a problem. Each finding explains its type choice; a clear request ignored by an assistant is not a user-framing defect. One directly observed goal/output mismatch with visible burden may support a small response-review trial under request-feedback v4's explicit evidence routes, never a persistent instruction or recurrence claim by itself.
- The output contract allows up to three findings, a no-actionable-finding outcome, or a bounded additional-evidence request. Findings identify their selected type, owner goal, observation, scope, admitted evidence and counterevidence IDs, an explicit disconfirming check and its status, benign alternative, coverage limit, proposed action, benefit hypothesis, effort, follow-up, and a structured work-session handoff. A stable finding ID is assigned locally after validation.
- Validation rejects unknown fields and IDs, unselected types, missing required text, more than three findings, a recurrence with fewer than two distinct Sessions, an unsupported owner-confirmed outcome, and an unbounded evidence request. The guide must abstain when a sampled excerpt cannot support a claim.

## Approved Selection And Evidence-Request Correction

The owner's 2026-09-29 continuation approves [RUN-128](../run/run-20260929-128-personal-insight-selection-contract.md), following the failed duplicate-request check in RUN-127.

- Report v3 adds `selection_reason` and up to five admitted `selection_evidence_ids` for every outcome, and a required `type_reason` for each finding. Explain the candidate's relevance and competing interpretation without claiming exhaustive ranking or guaranteed novelty.
- Core v5 adds a presentation-ownership correction observed during real-sample review: numeric message positions appear only in structured request targets. Model prose uses contents, dates, or relations to quoted anchors; the product alone assigns human-readable positions. Core v4 remains preserved with its exact evaluation evidence.
- A `needs_evidence` result also states a nonempty `no_finding_reason`. Before requesting anything, inventory supplied facts, distinguish unknown outcomes from missing conversation, and choose the smallest genuinely absent item.
- `additional_evidence.message_requests` contains at most five unique `{anchor_evidence_id, message_index}` targets for `conversation_neighbors`. The anchor must be in the request's admitted evidence IDs; the zero-based index must fall within that anchor Session's frozen eligible message count. A fully supplied message cannot be requested again. A truncated message may be requested in full. Other request kinds have an empty target list. Reject unknown, duplicate, out-of-range, unpositioned, or fully supplied targets; do not silently retry a paid Run.
- Position metadata identifies eligible user/assistant messages within the frozen scope, not raw provider event sequence. Older manifests without it cannot support new indexed requests. Version-two reports retain their original acceptance rules.
- The consumer renders conversation requests from validated targets with source links and nearby quoted anchors; it must not display unconstrained model prose as an extra conversation request. Semantic redundancy in other request kinds remains subject to guide checks and behavior evaluation; structural validation alone cannot prove it absent.
- This foundation owns only guide/value validation. FEAT-0110 separately integrates additive evidence metadata, renderer, and visible scope after the foundation checks pass. Sampling limits, evidence expansion, model options, and feedback persistence are outside this correction.

## Boundaries And Checks

- The guide distinguishes observed words from hypotheses and owner-confirmed outcomes. It excludes improvement-analysis and maintenance material from ordinary-work evidence. A single observation can justify a narrow question or reversible trial only when the relevant goal and friction are directly visible; it cannot justify a persistent rule from one ambiguous phrase.
- Each playbook includes a trigger, exclusions, evidence questions, benign alternatives, a choice among small interventions, an output sketch, a follow-up, and an explicit current-source limit. The configurable-assistant category is conditional on environment evidence.
- Synthetic tests cover all eleven resources and versions, goal-led category availability, quoted vocabulary, no-finding and additional-evidence outcomes, recurring and single-observation thresholds, citation validity, stable IDs, and strict shape limits. No model invocation or private Session data is needed.
- This foundation Feature does not change the current provider runner, UI, database, or report renderer. The original integration passed in [RUN-122](../run/run-20260928-122-guided-personal-insight-result-integration.md); the v5/v3 consumer correction belongs to [RUN-129](../run/run-20260929-129-personal-insight-scope-and-requests.md).

## Single-Observation Decision Clarification

The owner's 2026-10-01 continuation starts [RUN-131](../run/run-20261001-131-personal-insight-decision-threshold.md) after RUN-130 identified an unresolved initial-goal threshold. The core owns the choice of findings, action-dependent evidence requests, or no actionable finding. Request-feedback v3 introduced the narrower type-specific evidence routes; v4 clarifies the same output-review scope after an observed execution-gating proposal. Other playbooks retain their own thresholds.

- A future reversible trial needs a directly evidenced goal, mismatch, and burden, plus a specific action with value beyond the supplied correction or adopted method. Unknown future benefit or unknown acceptance of the past correction alone does not block such a trial. A fix to a currently unresolved task still needs the current fact on which it depends.
- For request-feedback, the initial goal/response/reaction route remains valid. A later explicit owner correction may establish the concrete goal when the prior response and the assistant's corresponding mismatch admission are supplied. This additional route supports only a bounded output-review trial. It does not establish clarity of an absent original request, earlier timing of the goal, recurrence, a user deficit, or a persistent setting cause.
- In that retrospective route, review the draft result response after the underlying work, against work performed and evidence returned. Its action, benefit, follow-up, and handoff share that timing; selecting tools or gating planned execution is outside the admitted remedy. This clarifies the existing scope rather than broadening it.
- Vague dissatisfaction plus an apology remains insufficient. Explicit changed requirements, accepted normal clarification, and accepted corrections with no further friction remain exclusions. Requests for more evidence must name the action whose admission or value depends on the missing fact.
- These are semantic guide checks using existing fields, not a new schema or an automatic semantic validator. Preserve the old guide and its evaluation rather than retroactively claiming that v2 met the new route.

## Concrete Application Handoff

The owner's 2026-10-01 follow-up asks the feature to explain how to adopt a suggestion, after RUN-132/133 left the distinction between a temporary instruction, a persistent policy and repeated prompting unclear. [RUN-134](../run/run-20261001-134-personal-insight-application-handoff.md) owns the core-v7 correction and comparison.

- Every supported finding identifies a change mechanism and target, concrete proposed content, setup and execution actors, activation and scope, initial setup, repeated manual burden, and an observable activation/outcome check. Core v7's application section owns the exact mapping into the existing `action`, `effort_or_tradeoff` and six `handoff` fields; report v3 and its renderer remain compatible.
- Exact paths and automatic loading require supplied evidence. An unresolved location or loading route is named as such, with a concrete first step to resolve it before editing. It does not alone block an otherwise supported bounded trial. Existing appropriate artifacts are preferred when supported; a policy file, skill or automation is not the default.
- Trial and adoption remain distinct. A single observation cannot justify a persistent policy, even when its proposed wording is concrete. A later adoption route is conditional on its stated evidence and owner decision. A clear request missed by the assistant must not become a requirement for the user to repeat it every prompt. Legitimate manual work is allowed when its frequency and burden are explicit, including repeated setup across Sessions.
- These are semantic generation requirements checked through behavior evaluation. Nonempty-field validation alone does not guarantee specificity or actual benefit. The analysis Run proposes a reviewable handoff; it does not install the change or grant approval for ordinary work.

## Existing Proposal Follow-through

The owner's 2026-10-02 continuation approves [RUN-136](../run/run-20261002-136-personal-insight-proposal-follow-through.md) after a real core-v7 result stopped at proposal duplication while application remained unknown.

- Assess what the supplied evidence establishes about a previous proposal: mention, intended use, actual application, observed outcome or explicit deferral. Missing later evidence stays unknown; it is not proof of non-adoption, adoption or success. These distinctions use existing prose fields and do not create persisted review state.
- Reusing a method can add value by resolving a supported application gap: delivery, setup, activation, bounded trial or outcome check. Novel wording or a different idea is not required. A supported finding follows the existing concrete handoff contract; a no-finding answer may carry forward a usable existing next step without manufacturing a new finding.
- Earlier analysis and its recommendations may identify what was proposed. They remain excluded from ordinary-work evidence, recurrence, efficacy claims and authorization. A proposal alone cannot justify an intervention; preserve the goal/friction and playbook evidence thresholds.
- Respect supplied effective application, owner acceptance without further friction and explicit deferral. Do not reinstall a working method, invent extra checks, or pressure the owner to adopt a declined method. Ask for application state only when it would change the justified next action and the fact is genuinely absent.
- Keep the new decision rule in core v8's decision section and link it to the existing application section. Report v3, playbooks, sampling, historical results, UI and persistence remain unchanged.

## Open Blockers

- None for the product-neutral guide and value contract. RUN-122 completed the consumer's package freeze and version reporting with synthetic checks. RUN-126 adds a bounded subagent behavior comparison with private frozen evidence; it does not establish actual CLI behavior or owner-confirmed benefit.

## Behavior Follow-up

[RUN-130](../run/run-20260929-130-personal-insight-requested-context.md) owns the unchanged-guide requested-context comparison and its historical threshold ambiguity. RUN-131 records the explicit clarification above, the first attempt's scope failure, and a targeted v4 correction checked by three new producers and fresh review. Its [functional evaluation](../evaluation/eval-0108-functional-decision-threshold.md) accepts the bounded correction with a source-attribution suggestion and partial coverage. Neither Run changes production sampling or the provider contract. Those comparisons do not establish example independence, final-version control regression, product CLI execution, or owner benefit.

[RUN-134](../run/run-20261001-134-personal-insight-application-handoff.md) compares core v6/v7 on identical focused real evidence and checks two v7 controls. It supports the application-handoff correction with a partial functional pass and unchanged structural contract. The observed improvement is explicit delivery, setup and application checking; the underlying intervention's benefit and actual adoption remain unproven.

[RUN-136](../run/run-20261002-136-personal-insight-proposal-follow-through.md) compares two v7 and three v8 first answers on one focused real input and three separate v8 controls. Its [functional evaluation](../evaluation/eval-0108-functional-proposal-follow-through.md) accepts the application-decision correction with suggestions for observed language and initial-goal wording defects, with partial coverage. The [contract evaluation](../evaluation/eval-0108-contract-proposal-follow-through.md) preserves historical resources and report compatibility. That closed comparison did not start a new production analysis or establish owner-confirmed benefit.

A [subsequent owner-started product observation](../evaluation/eval-0108-functional-proposal-follow-through.md#subsequent-owner-started-product-observation) records one successful core-v8 execution and report download with the targeted application detail. It is separate from the frozen eight-producer comparison. Stable generation, actual adoption and user benefit remain unverified.
