# EVAL-0051: Atlassian URL-First Connection Onboarding — UX Heuristic

## Metadata

- ID: `eval-0051-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260724-56`
- Attempt: `1`
- Feature: [feat-0051-atlassian-url-first-connection-onboarding](../feature/feat-0051-atlassian-url-first-connection-onboarding.md)
- Spec: [spec-0051-atlassian-url-first-connection-onboarding](../spec/spec-0051-atlassian-url-first-connection-onboarding.md)
- Execution Profile: `fullstack-product`
- Surface Lane: paste URL → understand Site/access path → register locally → bind or edit later
- Evidence Coverage: `partial`
- Created: `2026-07-24`

## Scope

- Evaluated first-use orientation, Source Instance/Site/provider comprehension, progressive disclosure, remote-I/O trust, error recovery, editability, no-script fallback, and control burden.

## Checks And Evidence

- The former prerequisite dead end is replaced by one first-use path: paste a URL, inspect its locally detected service/domain/identifier, choose a local access path, and register.
- Existing Site matches are reused automatically only when unambiguous. Zero matches switch to new setup; multiple matches require an explicit user choice.
- `MCP 연결 (Provider)`, “공식 Atlassian MCP,” and “회사 MCP Gateway” express how LocalBrain will later read the source. Separate Source and Site labels plus the concrete domain keep the concepts distinct.
- Cloud ID or Gateway alias is optional and labeled as later-bindable. Leaving it blank creates a visibly local-only reference rather than blocking knowledge capture or implying refresh readiness.
- Source/Site display names are optional and receive understandable defaults. Stable identity fields are not presented as casually editable.
- URL preview, local registration, connection edit, candidate discovery, and refresh keep distinct action and cost language. The first three do not trigger remote reads.
- Invalid input remains in the form; atomic rollback prevents a confusing partial connection. The server-rendered form remains usable without JavaScript.

## Evidence Gaps

- Direct browser observation of disclosure animation, focus transfer, and compact visual scan order was unavailable because the required in-app browser runtime was not exposed.
- DOM order, labels, live-region semantics, ordinary form fallback, focus targets, and compact CSS are directly inspected; exact rendered confirmation remains a non-blocking first-use check.
- Acceptance impact: non-blocking.

## Findings

- No blocking prerequisite loop, provider ambiguity in visible copy, hidden remote action, or irreversible edit path remains.
- Suggestion: if “Source Instance” still feels too technical after real use, a later copy-only refinement could lead with “연결” and keep the formal term secondary. This does not change the current data model.

## Route

- Next action: `pass`.
