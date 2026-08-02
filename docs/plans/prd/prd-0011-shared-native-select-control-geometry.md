# PRD-0011: Shared Native Select Control Geometry

## Metadata

- ID: `prd-0011`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-27`
- Updated: `2026-08-02`
- User review status: `implemented and verified`
- Approval mode: `completed`

## Request Summary

- Normalize the right-side disclosure-arrow clearance and selected-text
  protection of every current native dropdown control.
- Own the correction at the shared form-control layer so Atlassian,
  Workstream, Search, and future consumers do not carry page-local
  near-equivalent spacing.
- Keep native select semantics and current product tasks intact while making
  the visible control geometry deliberate and consistent.

## Source Set

- Human request:
  - the dropdown-arrow issue is not Atlassian-specific;
  - Workstream and every control of the same type show the same lack of
    intentional spacing;
  - one shared rule should apply to all of them.
- Golden source:
  - the owner's direct review of current LocalBrain screens.
- Supporting docs:
  - [Design Constitution](../../policies/design/design-constitution.md)
  - [Design Evaluation](../../policies/design/design-evaluation.md)
  - [Interaction Evaluation](../../policies/experience/interaction-evaluation.md)
  - [PRD-0010: Atlassian UI And Interaction Reconciliation](prd-0010-atlassian-ui-and-interaction-reconciliation.md)
- Current implementation references:
  - `src/localbrain/static/styles.css`
  - `src/localbrain/templates/atlassian.html`
  - `src/localbrain/templates/atlassian-item.html`
  - `src/localbrain/templates/atlassian-refresh.html`
  - `src/localbrain/templates/workstream.html`
  - `src/localbrain/templates/search.html`

## Product Intent

- Make every native select look like one LocalBrain form primitive regardless
  of the screen family that consumes it.
- Give the disclosure indicator an intentional right-edge inset and reserve
  enough trailing room that selected text never competes with it.
- Correct one shared primitive without expanding into a broad form redesign.

## Plan Type

- Cross-surface visual consistency and interaction preservation.
- Completed reconciliation plan. The implementation proved the final rule, and
  durable product-wide visual law remains owned by the Design Constitution.

## Pre-implementation State Reconciliation

| Surface family | Consumers at intake | Style owner at intake | Observed drift at intake |
| --- | --- | --- | --- |
| Atlassian | Add, discovery, filters, Item organization, refresh runner | several Atlassian form selectors | ordinary horizontal padding is reused; no select-specific indicator inset or text reserve |
| Workstream | maintenance task, Thread and Workstream status, resource linking | `.stack-form` and `.task-run-form` | horizontal padding differs from Atlassian and still has no disclosure contract |
| Search | source and Atlassian filtering | shared search/Atlassian filter selector | visually inherits the same unresolved native-arrow geometry |

- At intake, all in-scope consumers used native `<select>` elements.
- At intake, no shared `appearance`, disclosure asset, `background-position`,
  arrow inset, or select trailing-content token owned the indicator geometry.
- The browser therefore controlled the indicator position while LocalBrain
  controlled only general box padding, producing an incidental rather than
  intentional relationship between text, indicator, and right border.

## Confirmed Scope

- Every current native `<select>` consumer in tracked product templates,
  including Atlassian, Workstream, and Search surfaces.
- One shared select-specific geometry contract covering:
  - indicator distance from the right control boundary;
  - protected trailing space between selected text and the indicator;
  - vertical centering and box alignment;
  - long labels, translated labels, and selected values;
  - idle, hover, focus, disabled, required, invalid, compact, narrow, and touch
    states.
- Adoption through shared semantic ownership rather than copied page-local
  numeric values.
- Preservation of current labels, option values, submission behavior,
  keyboard behavior, focus behavior, validation, and no-script operation.
- Responsive validation at `1440`, `920`, `700`, and `320` widths using
  synthetic content.

## Excluded Scope

- Custom menus, `details` disclosures, disclosure buttons, comboboxes, or
  other arrow-bearing controls that are not native `<select>` elements.
- Rewriting a native select as a custom JavaScript component.
- Changing the option vocabulary, form workflow, information hierarchy,
  control height system, or screen layout.
- A broad LocalBrain input, textarea, button, or form-system redesign.
- Page-local tuning that bypasses the shared select owner.
- Spec, implementation, or evaluator work before this PRD and its child
  Feature are approved.

## Constraints

- Execution profile: `Frontend Product`.
- Affected surface lanes:
  - shared native-select component styling and semantic tokens;
  - Atlassian Add, discovery, filter, Item-detail, and refresh consumers;
  - Workstream task, status, and resource-linking consumers;
  - Search source and Atlassian-filter consumers;
  - responsive, focus, disabled, validation, long-label, and touch evidence.
- The implementation may retain the platform-native indicator or introduce a
  shared decorative indicator, but it must preserve native select semantics
  and must not expose two arrows.
- Exact inset and trailing-reserve values must come from the existing spacing
  system and rendered comparison, not an isolated raw page value.
- Any shared CSS owner change must be checked against every current consumer
  before acceptance.
- Tracked screenshots and fixtures use synthetic data.

## Acceptance Envelope

- Every current native select presents the same intentional disclosure
  clearance from the right control edge.
- Selected text has a separate protected trailing reserve and does not collide
  with or render beneath the indicator, including with long labels.
- Atlassian, Workstream, and Search no longer define incompatible select-arrow
  geometry through page-local spacing.
- Focus, disabled, required, invalid, narrow, and touch states keep the same
  indicator alignment and usable control box.
- Mouse, keyboard, focus, validation, native form submission, and no-script
  behavior remain unchanged.
- Design, Functional, and UX Heuristic evaluation evidence covers all named
  surface lanes and supported widths.
- The approved child Feature executed after FEAT-0062 and FEAT-0063.

## Approved Feature

- [FEAT-0064: Shared Native Select Disclosure Geometry](../feature/feat-0064-shared-native-select-disclosure-geometry.md)
  (`product`, `frontend-product`): establish one select-specific disclosure inset
  and trailing-text reserve, adopt it across all current native select
  consumers, and verify unchanged native interaction behavior.

## Continuity Notes

- `2026-07-27`: split the initial Atlassian select-arrow observation from
  PRD-0010 after the owner confirmed the same issue on Workstream and every
  dropdown of the same native-select type.
- `2026-07-27`: implementation inventory confirmed current consumers in
  Atlassian, Workstream, and Search and found no shared select-specific
  disclosure or trailing-text geometry.
- `2026-07-27`: the owner approved implementation through the current boundary;
  FEAT-0064 will execute after the Atlassian foundation and product Features.
- `2026-07-27`: FEAT-0064 passed automated and Chrome DevTools rendered
  evaluation across Atlassian, Workstream, and Search, completing this PRD.
- `2026-08-02`: marked the intake reconciliation as pre-implementation and the
  plan as completed without changing the passed contract or evidence.
