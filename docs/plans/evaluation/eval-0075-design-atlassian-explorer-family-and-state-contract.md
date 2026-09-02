# EVAL-0075 Design: Atlassian Explorer Family And State Contract

## Metadata

- ID: `eval-0075-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260829-85`
- Attempt: `1`
- Feature: [FEAT-0075](../feature/feat-0075-atlassian-explorer-family-and-state-contract.md)
- Spec: [SPEC-0075](../spec/spec-0075-atlassian-explorer-family-and-state-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `durable-design`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Active feature: durable design-family and responsive-state contract only.
- Active spec: SPEC-0075.
- Evaluated build: Design Constitution and Design Governance changes.

## Checks

- Applied `screen-alignment` in `reframe` mode: implementation stayed stopped
  until the requested Explorer family was explicitly made constitutional.
- Checked the new family law against existing Explorer, browse, shell, token,
  component, responsive, accessibility, and AI guardrails.
- Confirmed no new visual token, component family, raw value, private
  breakpoint, nested Page tree, or shell redesign was introduced.
- Confirmed wide, compact, and narrow compositions preserve list primacy,
  selection reachability, containment, and full-detail fallback.
- Confirmed one-query handoff preserves shell geometry and does not remove
  global Search from other routes.
- Confirmed Sync/Add/Connections/Refresh remain presentation-distinct and local
  work cannot appear dependent on remote access.

## Evidence

- Environments checked: Design Constitution, Design Governance, Product Model,
  active design plan, current Atlassian structure, and Local Context Explorer
  source patterns.
- Shared owner: the Explorer screen-family law; representative peers checked
  were Local Contexts and Schema.
- Rendered comparison is intentionally deferred to FEAT-0077 through FEAT-0080,
  whose approved contracts require browser evidence. RUN-85 makes no rendered
  geometry or interaction claim.

## Evidence Gaps

- None for the documentation-only acceptance contract.

## Findings

- None.

## Regression Notes

- Persistent shell geometry, semantic token vocabulary, accessibility floor,
  Local Context tree semantics, and Schema Explorer behavior remain unchanged.

## Route

- Next action: `pass`

## Continuity Notes

- `2026-08-29`: design contract passed; later implementation work switches
  from `reframe` to constitution-preserving `extend` mode.
