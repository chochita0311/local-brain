# FEAT-0079: Atlassian Manual Add And Connections Separation

## Metadata

- ID: `feat-0079`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Goal

- Make manual Atlassian registration a focused one-URL action and move
  optional access binding and connected discovery to a truthful secondary
  destination.

## Acceptance Contract

- The Explorer `Add` action opens a modal, drawer, or equivalent bounded first
  state whose only required user input is one Atlassian URL.
- URL preview and submission infer Jira/Confluence service, normalized Site,
  and Issue/Page/Project/Space identity locally. Registration no longer relies
  on the currently selected service tab or a hidden user-chosen service value.
- Existing supported Jira issue/project and Confluence Page/Space URLs remain
  valid, idempotent, and local-only; invalid, REST, unsupported, or conflicting
  URLs preserve the input and create no partial rows.
- Provider, Source Instance, connection reference, capability, runner, and
  remote readiness do not appear as required or adjacent primary Add fields.
- Successful Item Add closes or completes the first state and makes the new or
  reused Item reachable in the appropriate Explorer scope. Successful
  Project/Space Add makes the structural group reachable without claiming
  that remote Items were discovered.
- A secondary `Connections` destination is reachable from an Atlassian
  overflow/secondary action, not from the primary Add form. It owns existing
  access bindings, Provider/configuration references, enabled/capability
  state, and connection management.
- Connected discovery remains inside `Connections`, preserves Site → binding
  → runner selection, starts at most the currently approved remote read, and
  registers nothing without the existing explicit candidate confirmation.
- Missing or invalid remote access cannot block Add, Browse, exact search,
  local detail, local classification, or later local Sync.
- Wide, compact, and narrow composition keeps Add first in reading/focus order.
  Cancel or dismissal after an error returns focus to the initiating Explorer
  action; success transfers focus to the selected Item preview or structural
  Explorer destination created by the handoff.
- A server-executable Add route remains available without JavaScript.

## Scope Boundary

- In:
  - one-URL Add first state and service-independent submission
  - local preview, validation, idempotent Item/Space registration, and success
    handoff to Explorer
  - secondary Connections destination and relocation of access management and
    connected discovery
  - focus, responsive, error, and no-script behavior
- Out:
  - new access providers, credentials, capability operations, or remote writes
  - automatic connected discovery or candidate registration
  - local evidence Sync
  - remote Refresh behavior
  - Item detail lifecycle, exact search, or hierarchy changes outside action
    integration
  - AI retrieval

## Surface Lanes

- Registration contract lane:
  - path roots: URL recognition/preview/registration service and focused tests
  - dependencies: passed PRD-0010 registration contract and FEAT-0075
  - expected evidence: service inference, idempotency, zero-access success,
    rollback, and Item/Space handoff identity
  - evaluator ownership: `contract`, `functional`
- Explorer Add lane:
  - path roots: Atlassian routes, Add first-state template/controller/styles,
    focus return, and UI tests
  - dependencies: passed FEAT-0077 and registration contract lane
  - expected evidence: one required URL, no optional-access competition,
    validation retention, success orientation, responsive and no-script paths
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Connections lane:
  - path roots: access management and connected-discovery routes/templates,
    current binding/discovery services, and tests
  - dependencies: Explorer Add lane for destination separation
  - expected evidence: secondary discoverability, current Site/binding/runner
    semantics, readiness/error states, and explicit candidate confirmation
  - evaluator ownership: `contract`, `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, architecture, design, and interaction owner docs
  - dependencies: completed runtime behavior
  - expected evidence: Add/Connections/discovery ownership parity
  - evaluator ownership: `contract`

## Contract Surfaces

- Service-independent URL preview and registration request/response.
- Jira/Confluence Item/Space inference and validation.
- Explorer success destination and selected/structural identity.
- Connections route/destination and access-binding management.
- Connected discovery Site/binding/runner and confirmation contract.
- Modal/drawer focus, dismissal, error retention, and no-script form.

## User-Visible Outcome

- The user can add a known Jira or Wiki URL immediately with one field, while
  optional remote access and discovery remain available in a separate place
  that does not make Add feel incomplete.

## Entry And Exit

- Entry point: activate `Add` from the Explorer or open the server-executable
  Add destination directly.
- Exit or transition behavior: cancel and restore Explorer focus; complete an
  Item/Space registration and reach its Explorer context; or deliberately
  navigate to secondary Connections for access/discovery work.

## State Expectations

- Default: one empty required URL and bounded local-only orientation.
- Preview: locally inferred service/Site/type/identity with no remote work.
- Reused: existing identity is reported and becomes reachable without a
  duplicate.
- Invalid: input is retained, no partial rows exist, and recovery is local.
- Success: new/reused Item or Space identity and Explorer destination are
  explicit.
- Connections empty/unavailable: Add remains complete; remote recovery is
  scoped to Connections.
- Connected discovery: readiness, running, partial candidate, confirmation,
  failure, and no-results states retain existing remote boundaries.
- Narrow: Add remains first and isolated; Connections is not stacked as a
  prerequisite card beneath it.

## Dependencies

- FEAT-0075, FEAT-0077, and FEAT-0078 must be `passed` before this Feature
  enters build.
- Passed FEAT-0062 and FEAT-0063 remain foundation and behavior baselines.
- FEAT-0080 may proceed independently after FEAT-0077, but the recommended
  execution order places this Add/Connections separation first.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/atlassian_registration.py`
- `src/localbrain/templates/atlassian.html`
- a bounded Add/Connections template or partial if introduced
- `src/localbrain/static/atlassian.js`
- `src/localbrain/static/styles.css`
- registration/access/discovery/route/UI tests
- product, architecture, design, and interaction owner docs

## Pass Or Fail Checks

- Pass if Jira issue/project and Confluence Page/Space URLs register or reuse
  correctly from any service scope with one required field and zero access.
- Pass if invalid and conflicting URLs retain input, perform no remote read,
  and leave no partial identity.
- Pass if Item/Space success reaches the correct Explorer context and focus/
  history behavior remains understandable.
- Pass if Connections is secondary yet discoverable and preserves access,
  discovery, readiness, runner, partial-candidate, and confirmation contracts.
- Pass if synthetic `1440`, `920`, `700`, and `320` checks keep Add first,
  optional access separate, focus bounded, and no-script submission usable.
- Fail on a service selector, optional-access fields inside Add, hidden remote
  work, automatic candidate registration, dead-end missing access, or a
  stacked mobile setup flow before the URL task.

## Regression Surfaces

- FEAT-0062 Site/access-binding identity and compatible persistence.
- FEAT-0063 local-only URL Add and separate optional access behavior.
- PRD-0008 connected discovery, partial results, and explicit confirmation.
- FEAT-0077 service/hierarchy/query state and Explorer action region.
- Existing full-detail and Refresh destinations.

## Harness Trace

- Approved spec: [SPEC-0079](../spec/spec-0079-atlassian-manual-add-and-connections-separation.md), Attempt 1
- Completed run: [RUN-20260829-89](../run/run-20260829-89-atlassian-manual-add-and-connections-separation.md), passed Attempt 1
- Execution profile: `fullstack-product`
- Latest evaluator reports: [contract](../evaluation/eval-0079-contract-atlassian-manual-add-and-connections-separation.md), [design](../evaluation/eval-0079-design-atlassian-manual-add-and-connections-separation.md), [functional](../evaluation/eval-0079-functional-atlassian-manual-add-and-connections-separation.md), and [UX](../evaluation/eval-0079-ux-atlassian-manual-add-and-connections-separation.md), all PASS
- Latest fix note: none

## Resolved Review Decisions

- `Connections` is a secondary Atlassian overflow destination and does not
  appear inside the primary Add first state.
- FEAT-0078 passed, so successful Item Add returns to and selects the Item in
  the appropriate Explorer scope; successful Project/Space Add returns to its
  structural scope without claiming Item discovery.

## Continuity Notes

- `2026-08-29`: proposed after PRD-0014 approval to preserve current local
  registration/access/discovery contracts while removing setup competition
  from the primary Add task.
- `2026-08-29`: FEAT-0078 passed. The owner's sequential approval activated
  this Feature, resolved both review decisions, and authorized SPEC-0079 as
  the only current planning target.
- `2026-08-29`: SPEC-0079 Attempt 1 approved and RUN-89 activated after
  preflight resolved exact-URL reuse, helper atomicity, archived Item
  reachability, and selected empty-Space count parity without a schema change.
- `2026-08-29`: RUN-89 Attempt 1 and all four evaluators passed. One-URL Add,
  structural handoff, separate Connections, responsive modal ownership, and
  bounded authority were verified by 403 tests and synthetic four-width Chrome
  evidence; FEAT-0080 became the sole active Feature.
