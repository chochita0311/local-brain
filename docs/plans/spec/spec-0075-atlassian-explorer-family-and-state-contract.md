# SPEC-0075: Atlassian Explorer Family And State Contract

## Metadata

- ID: `spec-0075`
- Status: `approved`
- Run ID: `run-20260829-85`
- Attempt: `1`
- Parent Feature: [FEAT-0075](../feature/feat-0075-atlassian-explorer-family-and-state-contract.md)
- Parent PRD: [PRD-0014](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Surface Lane: `durable-design -> product-interaction -> consumer-audit`
- Required Evaluators: `contract`, `design`
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Source Set

- Human request: approve each proposed Feature sequentially and continue
  through the full approved increment.
- Parent Feature: FEAT-0075.
- Parent PRD: PRD-0014 and its owner-approved defaults.
- Golden sources: current Atlassian surface, Local Context Explorer family,
  and the active Atlassian Explorer reframe design plan.
- Relevant contracts: Design Constitution, Design Document Governance,
  Product Model, Design Evaluation, Interaction Evaluation, PRD-0007,
  PRD-0008, and PRD-0010.

## Implementation Goal

- Establish the Atlassian Explorer family and complete state/action ownership
  as durable policy before any dependent query or product implementation.

## In-Scope Behavior

- Move Atlassian from `Browse and inventory` to `Explorer` in the durable
  screen-family table.
- Define an Atlassian Explorer variant with Site/Space/Unclassified hierarchy,
  list, and detail without claiming a Page or issue tree.
- Define one visible surface-local Atlassian query and the shared-shell handoff.
- Define `All` default and reversible Jira/Wiki presentation, with Wiki mapping
  to the stored `confluence` value.
- Define preserve/reset ownership for service, hierarchy, query, filters,
  selection, disclosures, pane state, history, focus, and scroll.
- Define wide, compact, and narrow transformations.
- Keep local Sync, manual Add, Connections/discovery, and remote Refresh as
  distinct actions with distinct consequences.
- Record the design-governance version entry and audit current consumers that
  downstream Features must change.

## Out-Of-Scope Behavior

- Runtime routes, queries, templates, CSS, JavaScript, schema, or test changes.
- Exact-match algorithm, product UI, detail fragment, Add, Connections, Sync,
  Refresh, or AI implementation.
- Nested Confluence Page or Jira issue hierarchy.

## Affected Surfaces

- `docs/policies/design/design-constitution.md`
- `docs/policies/design/design-document-governance.md`
- `docs/policies/project/product.md`
- FEAT-0075 and RUN-85 trace fields
- current Atlassian route/template/query consumers as read-only audit evidence

## Surface Lanes

- Durable design:
  - path roots: `docs/policies/design/`
  - dependency order: first
  - implementation responsibility: screen-family, responsive, shell, and
    Explorer-variant law plus governance version
  - validation evidence: policy diff and family-table cross-check
- Product interaction:
  - path roots: `docs/policies/project/product.md`
  - dependency order: after durable design
  - implementation responsibility: action and state ownership table
  - validation evidence: state/event matrix and consequence definitions
- Consumer audit:
  - path roots: current Atlassian routes, templates, query helpers, JavaScript,
    styles, and tests as read-only evidence
  - dependency order: after both contract lanes
  - implementation responsibility: identify downstream adoption points without
    modifying runtime code
  - validation evidence: cited stale-assumption inventory in RUN-85

## State And Interaction Contract

- Default: `All`, root hierarchy, empty query, no advanced filters, no Item
  selection, and a quiet unselected detail region.
- Service changes preserve query and compatible advanced filters, reset
  structure/selection/result-local scroll, and normalize hierarchy disclosure.
- Structure changes preserve service/query/filters, reset selection and
  result-local scroll, and keep the destination hierarchy visible.
- Query or advanced-filter changes preserve service/structure, reset selection
  and result-local scroll, and retain editable URL-backed input state.
- Item selection preserves all browse state and list position while updating
  URL/history, visible/programmatic selection, and detail state together.
- Direct entry and refresh reconstruct URL-backed state; omitted values use the
  default state and invalid values normalize visibly rather than remaining
  hidden.
- Back/forward restores the same URL-backed state and practical scroll/focus
  orientation as click-driven transitions.
- Breakpoint changes preserve eligible browse and selection state while
  normalizing unsupported pane/disclosure state into the destination layout.
- Wide uses persistent hierarchy/list/detail; compact keeps the list primary
  and moves hierarchy/detail to bounded disclosures; narrow is list-first with
  explicit sheets or sequential destinations.

## Data And Contract Assumptions

- Stored services remain `jira` and `confluence`; `Wiki` is presentation only.
- Space/project containment is optional; null containment remains visible as
  `Unclassified`.
- Current Site, Space, Item, evidence, classification, relationship, access,
  and Refresh data remains unchanged.
- Local Browse remains available without access capability.

## Contract Surfaces

- Producer expectations: durable design and product policies define the target
  family, state, terminology, and action consequences.
- Consumer expectations: FEAT-0076 through FEAT-0080 must adopt the contract in
  dependency order and may not infer hidden modes or external work.
- Generated artifacts: the plan artifact catalog is regenerated after status
  changes.
- Source-of-truth owner: Design Constitution for family/presentation law and
  Product Model for product/action/state behavior.
- Stale-assumption check: current `/atlassian` defaults to Jira, exposes two
  query inputs and the selector matrix, routes rows to full detail, couples Add
  with optional setup, and has no explicit local evidence Sync action; these
  are expected downstream adoption points, not FEAT-0075 defects.

## Required Evaluators

- Contract: ownership, completeness, downstream readiness, and stale consumer
  inventory.
- Design: durable family classification, shell continuity, Explorer variant,
  and responsive law.
- Functional: not required because this Feature changes no runtime behavior.
- UX heuristic: not required because this Feature changes no rendered surface.

## Acceptance Mapping

- Design Constitution and governance log changes satisfy family/version checks.
- Product Model terminology and state table satisfy one-search, All/Jira/Wiki,
  hierarchy, preservation/reset, and action-consequence checks.
- Consumer audit satisfies downstream-readiness and regression checks.
- No runtime diff satisfies the foundation-only boundary.

## Evaluation Focus

- Confirm no sequencing, unresolved experiments, or page-local implementation
  values entered durable policy.
- Confirm Local Context tree behavior was not generalized into unsupported
  Atlassian containment.
- Confirm one search owner and each action consequence remain unambiguous.
- Confirm state transitions cannot retain an inaccessible hidden mode.

## Open Blockers

- None. The owner's sequential approval accepts the proposed FEAT-0075
  boundary; exact search and later UI decisions remain in their own Features.

## Continuity Notes

- `2026-08-29`: approved for RUN-85 after the owner authorized sequential
  Feature approval and complete execution of PRD-0014.
