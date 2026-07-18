# SPEC-0023: Usage Breakdown And Trust

## Metadata

- ID: `spec-0023`
- Status: `approved`
- Run ID: `run-20260718-23`
- Attempt: `1`
- Parent Feature: [feat-0023-usage-breakdown-and-trust](../feature/feat-0023-usage-breakdown-and-trust.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Implementation Goal

- Extend FEAT-0022 with one compact Source, Model, or Project explanation surface and one bounded trust surface using the exact same selected usage facts and estimated-cost contract.

## In-Scope Behavior

- Add `breakdown=source|model|project` to normalized GET state; default and invalid values resolve to `source`.
- Preserve breakdown state across source, range, metric, and valid custom-date controls.
- Group the selected direct facts by source kind, normalized model identity, or immutable Project snapshot key.
- For each group return supported token total, priced estimated cost, usage-linked primary-work Session count, metric-compatible share, last usable activity, fact and price coverage, and evidence navigation when truthful.
- Model rows expose distinct raw source model identities; missing identity is `Unknown model`.
- Project rows use `usage_facts.project_key` and snapshot labels only; missing attribution is `Unassigned`. Current workspace joins are used only to decide whether an existing browse destination is available, never to regroup history.
- Source rows link to the current primary-work Session inventory filtered by source. Project rows link to the current workspace inventory when the snapshot workspace still resolves. A group backed by exactly one primary-work Session may link to that detail; otherwise the row states that it is aggregated.
- Sort by the selected compatible metric descending, then label. Show eight rows initially and place additional rows in a native, keyboard-accessible disclosure.
- Build a separate trust region after composition with selected-fact token coverage, price coverage, calculation states, last calculation, active price snapshots, per-source last attempt, inferred last successful synchronization, stale/error state, and retained-data wording.
- Infer a source's last successful synchronization from its latest healthy source file when the current attempt has errors; otherwise use the successful source scan time. Do not expose source paths or raw parser errors.
- Keep prior usage visible when source-file errors or stale markers exist and label the trust state accordingly.

## Out-Of-Scope Behavior

- A new usage-detail route, model-filtered Session inventory, automatic Project reconciliation, exact failed-run history, refresh action, budgets, caps, quotas, projections, tool or workflow analysis, or shell changes.

## Affected Surfaces

- `src/localbrain/usage_queries.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/sessions_dashboard.html`
- `src/localbrain/static/styles.css`
- deterministic query, template, UI-contract, and local HTTP evidence
- Product Model, Project Architecture, roadmap, and backlog status

## State And Interaction Contract

- Composition defaults to Source and changes through ordinary GET links with `aria-current="page"`.
- The selected breakdown is one list family, not three simultaneous panels.
- Unsupported group values display `Unavailable`; shares use only the compatible token or priced-cost denominator.
- A zero eligible Session count is allowed for maintenance-only or subsession-only usage and is explicitly labeled.
- Native disclosure keeps the first eight ranked rows stable with no script dependency.
- Empty and no-match composition reuse the selected dashboard state and do not imply synchronization failure.
- Trust states use `current`, `stale`, `error`, or `not synchronized` independently from source provenance and selected control state.

## Surface Lanes

- Read model: compatible grouping, shares, identity, evidence, cardinality, source synchronization inference, and retained-data states.
- Route: normalized breakdown query and producer/consumer parity.
- Frontend: one composition list, one trust list/disclosure, frozen shell, responsive list containment.

## Evaluation Focus

- Reconcile every group to its compatible selected total and exact unsupported remainder.
- Prove current workspace changes do not affect historical Project groups.
- Prove error and stale source state retains prior usage.
- Prove high-cardinality and long-label fixtures remain one compact list with eight-row initial disclosure.
- Verify source provenance, selected state, price state, and source health use distinct semantics.

## Open Blockers

- None for implementation. Direct `1440`, `920`, `700`, and `320` browser evidence remains unavailable and must be recorded without claiming observation.

## Continuity Notes

- `2026-07-18`: approved with an eight-row native disclosure, compatible metric denominators, immutable Project grouping, and bounded source-success inference from current persistence.
