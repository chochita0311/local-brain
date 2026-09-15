# EVAL-0087 Design: Session Workflow Focus Map

## Metadata

- ID: `eval-0087-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run: [RUN-20260914-97](../run/run-20260914-97-session-workflow-focus-map.md)
- Attempt: `1`
- Feature: [FEAT-0087](../feature/feat-0087-session-workflow-focus-map.md)
- Spec: [SPEC-0087](../spec/spec-0087-session-workflow-focus-map.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Session Workflow Focus map and Trace presentation`
- Evidence Coverage: `complete`
- Created: `2026-09-14`

## Alignment Declaration

- Mode: `extend` through `screen-alignment`.
- Authority: Design Constitution → current Session and Schema Explorer families
  → Workflow Map Design Plan. Quartz and Obsidian contributed local-focus and
  navigation ideas, not their force layout or flat peer-node model.
- Affected surface: one additive Session action and one separate Workflow Focus
  route. Existing Session detail, Related Materials, source details, shell, and
  Workstream screens remain visually and structurally unchanged.

## Consistency And Rendered Evidence

- The screen reuses the shared shell, Session identity cue, panel hierarchy,
  semantic buttons, status text, source cues, spacing, borders, radii, and focus
  treatment. Workflow geometry is expressed through semantic tokens; no raw
  component color or competing design system was introduced.
- Wide presentation uses a left-to-right time spine with fixed branch lanes and
  an adjacent Trace. The `920px` state preserves the same topology vertically;
  `700px` and `320px` deliberately make the complete textual lineage primary
  before the Trace instead of squeezing an unreadable graph.
- Synthetic Chrome evidence used exact effective widths `1440`, `920`, `700`,
  and `320`. All four retained four Episodes, three relations, selected-state
  text, the shared shell, and document width no larger than client width. Wide
  and compact states retained the graph; narrow states opened the fallback and
  disabled hidden graph controls.
- Episode selection changes emphasis and Trace content without moving cards.
  Relation kind and authority are written on edges and in Trace, while
  selection, partial state, availability, and source family never rely on color,
  hover, glow, or motion alone.
- No-script rendering exposes the full lineage, relation reasons, evidence, and
  Session destination without a blank canvas. A deliberately malformed cloned
  payload changes the enhanced panel to `unavailable`, opens the same fallback,
  and disables its controls.

## Mismatch List

- None after implementation.

## Findings

- None.

## Current Route

- Current route: `PASS`.
