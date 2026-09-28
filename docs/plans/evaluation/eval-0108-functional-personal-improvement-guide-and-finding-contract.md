# EVAL-0108 Functional: Personal Improvement Guide And Finding Contract

## Metadata

- ID: `eval-0108-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `complete` for the synthetic foundation contract
- Run: [RUN-20260928-121](../run/run-20260928-121-personal-improvement-guide-and-finding-contract.md)
- Attempt: `1`
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Lane: `data`
- Created: `2026-09-28`

## Evidence And Finding

- Eight guidance tests passed with `.venv/bin/python -m unittest discover -s tests -p test_personal_insight_guidance.py -v`. The larger focused command, `.venv/bin/python -m unittest discover -s tests -p 'test_personal_insight*.py' -v`, passed all 17 evidence, guide, and synthetic consumer checks.
- Resource checks cover the eleven versioned playbooks and their trigger, exclusion, evidence-question, benign-alternative, intervention, output, follow-up, and current-source sections. Routing cases cover a broad nontechnical question, conditional harness selection, strict question priority over stronger excerpt cues, and fallback when no cue matches.
- Synthetic values cover a source-linked learning suggestion, one-observation scope, no actionable finding from ambiguous token/time volume, and a request for a second Session. Invalid cases reject unknown fields, unselected types, unsupported or overlapping citations, one-Session recurrence, owner-confirmed outcome, excess findings or text, and a request with no bounded question.
- The synthetic consumer check freezes the selected versions and digests, builds the selected output schema, validates a result, and renders a report without starting Codex CLI. All source paths and values in these checks are synthetic or temporary.

## Limits And Route

- This PASS covers deterministic resource loading, routing, value validation, and synthetic integration. A model's ability to follow the guide, usefulness of its findings, provider entitlement, and a real Session-based report remain unobserved. No private Session was transmitted or analyzed by a model.
