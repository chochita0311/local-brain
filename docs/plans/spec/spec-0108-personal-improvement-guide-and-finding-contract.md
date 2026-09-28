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
- The core guide and each playbook have independent stable versions. Selection returns a frozen package value containing core version, at most four selected playbook IDs and versions, exact trusted text, and a route reason. The caller supplies a FEAT-0107 manifest; this module reads no database, source file, runtime Run, or network service.
- For `ask`, the owner's question has priority in routing, then eligible user excerpts. For `discover`, eligible user excerpts are the routing signal. Deterministic lexical cues select relevant detailed playbooks; a small general fallback covers weak cues. The core includes a short eleven-type index so a selected subset is not mistaken for exhaustive coverage. Selection alone never establishes a finding.
- The output schema allows up to three findings, a no-actionable-finding outcome, or a bounded additional-evidence request. Findings identify their selected type, owner goal, observation, scope, admitted evidence and counterevidence IDs, an explicit disconfirming check and its status, benign alternative, coverage limit, proposed action, benefit hypothesis, effort, follow-up, and a structured work-session handoff. A stable finding ID is assigned locally after validation.
- Validation rejects unknown fields and IDs, unselected types, missing required text, more than three findings, a recurrence with fewer than two distinct Sessions, an unsupported owner-confirmed outcome, and an unbounded evidence request. The guide must abstain when a sampled excerpt cannot support a claim.

## Boundaries And Checks

- The guide distinguishes observed words from hypotheses and owner-confirmed outcomes. It excludes improvement-analysis and maintenance material from ordinary-work evidence. A single observation can justify a narrow question or reversible trial only when the relevant goal and friction are directly visible; it cannot justify a persistent rule from one ambiguous phrase.
- Each playbook includes a trigger, exclusions, evidence questions, benign alternatives, a choice among small interventions, an output sketch, a follow-up, and an explicit current-source limit. The configurable-assistant category is conditional on environment evidence.
- Synthetic tests cover all eleven resources and versions, general and harness routing, question priority, no-finding and additional-evidence outcomes, recurring and single-observation thresholds, citation validity, stable IDs, and strict shape limits. No model invocation or private Session data is needed.
- This foundation Feature does not change the current provider runner, UI, database, or report renderer. Integration into executable analysis Runs belongs to the separate [RUN-122 product-consumer correction](../run/run-20260928-122-guided-personal-insight-result-integration.md), which passed after this foundation.

## Open Blockers

- None for the product-neutral guide and value contract. RUN-122 completed the consumer's package freeze and version reporting with synthetic checks; real model behavior and advice quality remain unobserved.
