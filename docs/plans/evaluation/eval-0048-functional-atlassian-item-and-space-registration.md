# EVAL-0048: Atlassian Item And Space Registration — Functional

## Metadata

- ID: `eval-0048-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260723-53`
- Attempt: `1`
- Feature: [feat-0048-atlassian-item-and-space-registration](../feature/feat-0048-atlassian-item-and-space-registration.md)
- Spec: [spec-0048-atlassian-item-and-space-registration](../spec/spec-0048-atlassian-item-and-space-registration.md)
- Execution Profile: `fullstack-product`
- Surface Lane: registration service → routes/forms → inventory/client → complete regression
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated strict URL input, unambiguous and explicit Site selection, local idempotence, Space defaults, partial discovery, unavailable capability/executor handling, no-script forms, inventory rendering, client polling, compatible migration, generated schema, and complete regressions.

## Checks And Evidence

- Six focused registration tests cover Jira/Confluence recognition, key-only and service-mismatch rejection, Item and Space creation/reuse, default coverage, ambiguous same-domain Source Instances, cross-Site isolation, one-call partial discovery, candidate confirmation, unavailable capability, and no-script error/success behavior.
- The compatible migration test proves existing Spaces receive a service-specific canonical URL and Jira `selected-content` or Confluence `full-content` without changing retained identities.
- Invalid form input returns a bounded server-rendered error while preserving URL, title, Site, service, and runner choices. Successful POST redirects to the exact stable Item or Space fragment.
- The Space discovery route queues nothing unless the selected Source capability is current and the application has an injected approved executor. Ordinary URL registration remains available when discovery is unavailable.
- Client code polls only an already active, explicitly selected catalog Run through its local Run endpoint. It never starts discovery, calls an external service, or continues after a terminal state.
- Local Chrome rendering verified empty and populated states at `1440`, `920`, `700`, and exact emulated `320`, including long content and current/due/stale/unavailable freshness labels.
- Data-model checks, nine Mermaid diagrams, deterministic schema presentation, the 491-object cleanup audit, JavaScript syntax, privacy, compilation, and diff whitespace checks passed.
- The complete Python suite passed 241 tests.

## Evidence Gaps

- No live provider Run was executed and no company data was read. The approved executor boundary, manifest, structured result, and partial candidate projection are exercised with synthetic tests.

## Findings

- None.

## Regression Notes

- One pre-existing Starlette `TemplateResponse` deprecation warning remains unrelated and non-blocking.
- No model process or external request ran during verification.

## Route

- Next action: release Functional evaluation for FEAT-0048.
