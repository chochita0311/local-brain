# FEAT-0075: Atlassian Explorer Family And State Contract

## Metadata

- ID: `feat-0075`
- Status: `passed`
- Type: `foundation`
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `design`
- Parent PRD: [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Goal

- Make the approved Atlassian Explorer family and its state ownership durable
  so later product Features do not guess about hierarchy, search placement,
  URL/history, action meaning, or responsive behavior.

## Acceptance Contract

- The Design Constitution classifies Atlassian under the durable `Explorer`
  family and records the required governance version entry.
- Explorer law distinguishes the Atlassian Site/Space/link/detail variant from
  Local Context's source/directory/document preview without inventing a nested
  Confluence Page hierarchy.
- The Product Model owns one surface-local Atlassian query input. The shared
  topbar query is not simultaneously visible on the Atlassian route, and the
  shell retains stable geometry and navigation continuity during entry/exit.
- `All` is the default service scope; Jira and user-facing Wiki are explicit
  reversible scopes. `Wiki` maps to persisted `confluence` without changing
  stored service vocabulary.
- Hierarchy state is Service when needed, then Site, then Space/project, with
  `Unclassified` for valid Items whose Space is null.
- Query, service scope, structural scope, Item selection, advanced-filter
  state, hierarchy disclosure, pane state, outer scroll, and inner scroll have
  explicit preserve/reset owners for click, direct entry, refresh, back,
  forward, and breakpoint transitions.
- Wide state supports persistent hierarchy/list/detail; compact state keeps
  the list primary and moves hierarchy/detail to bounded disclosures; narrow
  state is list-first with hierarchy and detail sheets or equivalent
  sequential destinations.
- Local Sync, manual Add, connected discovery, and remote Refresh have distinct
  definitions, prerequisites, I/O, progress, completion, and recovery owners.
- Full-detail links remain the direct-entry and no-script fallback for Item
  inspection.
- PRD-0007, PRD-0008, and passed PRD-0010 behavior that remains a regression
  surface is cross-linked without rewriting historical contracts.

## Scope Boundary

- In:
  - durable Atlassian Explorer family classification
  - shell-to-surface search ownership and handoff contract
  - service, hierarchy, query, filter, selection, pane, history, scroll, and
    breakpoint state ownership
  - action-semantics contract for Sync, Add, discovery, and Refresh
  - current-owner and stale-assumption inventory for downstream Features
- Out:
  - route, query, template, CSS, JavaScript, schema, or runtime changes
  - exact-match algorithm or read-model implementation
  - Explorer presentation, detail fragments, Add, Sync, or Connections UI
  - AI retrieval contract or control
  - nested Confluence Page or Jira issue hierarchy

## Surface Lanes

- Durable design lane:
  - path roots: `docs/policies/design/`
  - dependencies: approved PRD-0014 and current Design Constitution
  - expected evidence: Explorer classification, Atlassian variant constraints,
    shell continuity, responsive-family rules, and governance version entry
  - evaluator ownership: `contract`, `design`
- Product interaction lane:
  - path roots: `docs/policies/project/product.md`,
    `docs/policies/experience/interaction-evaluation.md` only when a reusable
    rule is genuinely missing
  - dependencies: durable design lane
  - expected evidence: one-search ownership, scope/selection/history rules,
    action consequences, and responsive state table
  - evaluator ownership: `contract`
- Consumer audit lane:
  - path roots: current Atlassian templates, routes, queries, JavaScript,
    styles, tests, and passed owner docs as read-only evidence
  - dependencies: product interaction lane
  - expected evidence: explicit downstream adoption and regression inventory;
    no implementation in this Feature
  - evaluator ownership: `contract`

## Contract Surfaces

- Design Constitution screen-family table and governance version.
- Product Model Atlassian Browse/Add/access contract.
- Search ownership and shared-shell handoff.
- Service/hierarchy/query/selection/history/pane/scroll state model.
- Sync/Add/discovery/Refresh consequence vocabulary.
- Downstream Feature dependency and regression map.

## Entry And Exit

- Entry point: approved PRD-0014 and its design plan.
- Exit or transition behavior: hand the locked contract to FEAT-0076 through
  FEAT-0080; this Feature itself changes no user-visible runtime state.

## State Expectations

- Default: the contract defines `All`, no structural selection beyond the
  root, no Item selection, exact/local retrieval, and list-first narrow state.
- Direct entry: explicit service, structure, query, or Item identity restores
  the corresponding reachable orientation.
- Unsupported breakpoint state: normalizes to the nearest supported
  hierarchy/detail disclosure without retaining a hidden mode.
- Error/unavailable: local Browse remains available; optional access or remote
  readiness cannot become a prerequisite.

## Dependencies

- PRD-0014 is `approved`.
- FEAT-0076 through FEAT-0080 must not enter Spec until this foundation is
  approved and must not enter build until it is `passed` where their state or
  design-family behavior depends on it.

## Likely Affected Surfaces

- `docs/policies/design/design-constitution.md`
- `docs/policies/project/product.md`
- `docs/policies/experience/interaction-evaluation.md` only if promotion of a
  reusable missing rule is justified
- `docs/plans/design/atlassian-explorer-reframe-plan.md`
- active Atlassian planning cross-links and consumer inventory

## Pass Or Fail Checks

- Pass if Atlassian is unambiguously classified as Explorer with a governance
  version entry and Local Context-specific tree semantics are not copied as
  unsupported Atlassian hierarchy.
- Pass if exactly one visible query owner, `All` default, Jira/Wiki mapping,
  Site/Space/Unclassified hierarchy, selection/history, and responsive state
  behavior are durable and internally consistent.
- Pass if Sync, Add, discovery, and Refresh have distinct consequence
  contracts and optional remote setup cannot block local work.
- Pass if downstream specs can identify every state owner and regression
  surface without consulting conversational assumptions.
- Fail on runtime implementation, unresolved family/search ownership, hidden
  state at breakpoints, an invented nested Page tree, or accidental AI scope.

## Regression Surfaces

- Existing shared shell and global Search behavior outside Atlassian.
- Local Context and Schema Explorer family rules.
- PRD-0007 read-only Browse/evidence/Refresh contracts.
- PRD-0008 access binding and connected discovery.
- PRD-0010 passed URL-only Add and optional access separation.

## Harness Trace

- Approved spec: [SPEC-0075](../spec/spec-0075-atlassian-explorer-family-and-state-contract.md)
- Completed run: [RUN-20260829-85](../run/run-20260829-85-atlassian-explorer-family-and-state-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract PASS](../evaluation/eval-0075-contract-atlassian-explorer-family-and-state-contract.md) and [design PASS](../evaluation/eval-0075-design-atlassian-explorer-family-and-state-contract.md)
- Latest fix note: none

## Resolved Review Decisions

- No additional decision remained inside this completed boundary. Exact
  retrieval details, advanced-filter retention, Connections placement, and
  detail-pane content were owned by their downstream Features.

## Continuity Notes

- `2026-08-29`: proposed after PRD-0014 approval to establish the durable
  Explorer and state contract before any visible implementation.
- `2026-08-29`: the owner approved sequential execution of FEAT-0075 through
  FEAT-0080. FEAT-0075 was boundary-locked first and entered RUN-85; later
  Features remain draft until their dependency turn.
- `2026-08-29`: RUN-85 passed contract and design evaluation with complete
  evidence. The durable family/state prerequisite is ready for FEAT-0076.
