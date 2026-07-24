# EVAL-0051: Atlassian URL-First Connection Onboarding — Functional

## Metadata

- ID: `eval-0051-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260724-56`
- Attempt: `1`
- Feature: [feat-0051-atlassian-url-first-connection-onboarding](../feature/feat-0051-atlassian-url-first-connection-onboarding.md)
- Spec: [spec-0051-atlassian-url-first-connection-onboarding](../spec/spec-0051-atlassian-url-first-connection-onboarding.md)
- Execution Profile: `fullstack-product`
- Surface Lane: preview and form routes → atomic persistence → local inventory/edit
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Scope

- Evaluated first-use registration, existing connection reuse, ambiguity, validation rollback, unbound and bound states, editable fields, no-script behavior, local preview enhancement, live isolated HTTP responses, and complete regressions.

## Checks And Evidence

- Focused tests cover unbound URL-first creation and idempotent reuse, late-failure rollback, one-time binding, immutable bound reference, preview/registration/edit routes, strict URL recognition, ambiguous domains, direct registration, and discovery capability gating.
- With no configured Site, the synthetic `https://jira.example.test/browse/EXAMPLE-62` shape produces the local preview `jira`, `item`, `jira.example.test`, and `EXAMPLE-62`, reports no matches, and requires a new connection.
- An isolated `/tmp` runtime returned HTTP 200 for the Jira Add/discover page, registration-preview JSON, and route-scoped JavaScript. The page contained the first-use Source/Site option and explicit provider labels.
- Ordinary form POST remains the executable path. JavaScript only adds a debounced, abortable, same-origin local preview and selection assistance.
- The new registration composition invokes no external executor. Remote discovery and refresh retain the prior capability gate, so an unbound connection cannot imply read readiness.
- Editing updates only bounded display names, enabled state, or an absent configuration reference. A service mismatch or forbidden identity replacement rolls back.
- The complete suite passed 260 tests. Python compilation, JavaScript syntax, generated schema presentation, data-model ownership, cleanup audit, privacy, and diff checks passed.

## Evidence Gaps

- The isolated runtime did not submit a real company URL because that would mutate the user's actual LocalBrain data and was not required to verify the implementation. Synthetic tests cover the identical transaction.
- Direct pointer interaction was unavailable with the in-app browser runtime. No-script POST and JavaScript contracts are covered by route and source tests.
- Acceptance impact: non-blocking.

## Findings

- None.

## Regression Notes

- FEAT-0044, FEAT-0046, FEAT-0048, FEAT-0049, and FEAT-0050 tests remain green. One existing Starlette `TemplateResponse` deprecation warning remains non-blocking.

## Route

- Next action: `pass`.
