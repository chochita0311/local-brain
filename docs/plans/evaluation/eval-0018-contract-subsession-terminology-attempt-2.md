# EVAL-0018: Subsession Terminology Contract Attempt 2

## Metadata

- ID: `eval-0018-contract-subsession-terminology-attempt-2`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260717-18`
- Attempt: `2`
- Feature: [feat-0018-conversation-focused-session-details](../feature/feat-0018-conversation-focused-session-details.md)
- Spec: [spec-0018-conversation-focused-session-details](../spec/spec-0018-conversation-focused-session-details.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Session hierarchy terminology and compatibility route
- Created: `2026-07-19`

## Contract Evidence

- `sessions.session_role = 'subsession'`, `parent_external_id`, and `parent_session_id` remain the unchanged normalized hierarchy contract.
- Product UI, canonical route, template context, Product Model, Architecture, and Design Constitution now use `Subsession` consistently.
- Claude `subagents/` and Codex `source.subagent` remain upstream evidence names only.
- Existing `/subagents/` links redirect permanently to `/subsessions/`; normalized children continue to resolve through `/sessions/{child_id}`.

## Verification

- Relevant template and query tests plus the complete 142-test suite passed.
- Synthetic local HTTP verification confirmed `200` detail responses and the `308` compatibility redirect.

## Findings And Regression

- No blocking contract finding. Source parsing, stored identity, child eligibility, raw events, and primary-only consumers are unchanged.

## Route

- Next action: `pass`
