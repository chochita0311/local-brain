# EVAL-0079 Design: Atlassian Manual Add And Connections Separation

## Metadata

- ID: `eval-0079-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260829-89`
- Attempt: `1`
- Feature: [FEAT-0079](../feature/feat-0079-atlassian-manual-add-and-connections-separation.md)
- Spec: [SPEC-0079](../spec/spec-0079-atlassian-manual-add-and-connections-separation.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Explorer Add; Connections presentation`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- `screen-alignment` was applied in `extend` mode. Add reuses the existing
  action, dialog/sheet, button, form, status, focus, scrim, radius, elevation,
  and breakpoint families; Connections reuses the settings/editor and
  registered-scope families without introducing a private shell or token set.
- The Explorer action region keeps Add and Refresh visible and places
  Connections in one secondary disclosure. Add contains exactly one visible
  required URL field and no service, Provider, Source Instance, capability,
  runner, or discovery controls.
- At `1440x1000`, Add is a centered 620-pixel bounded dialog. At `920x900`, it
  is a 400-pixel right drawer. At `700x900` and `320x800`, it is a full-width
  sheet beginning at the current workspace-header bottom: 160 pixels at page
  start and 54 pixels after the header becomes sticky.
- The narrow sheet recomputes its offset through open resize, ends at the
  viewport bottom, keeps heading and Close visible, and assigns vertical
  scrolling to Add content. All four widths had zero horizontal overflow.
- Connections has one document `main`. Its DOM and visual order is registered
  scope, connection inventory, access/discovery tools, then catalog results.
  Wide layouts place tools in the right rail; `920`, `700`, and `320` preserve
  the same reading and keyboard order while moving the tools into flow.
- Long Site domains, Space identities, and URL content wrap within their
  owners. Error fields use the danger border, pending status returns to a
  neutral surface, and programmatic feedback destinations use the shared
  visible focus token.
- Independent design re-audit found no constitution or family drift.
  Lighthouse reported Accessibility `100` and Best Practices `100` for the
  desktop Explorer, mobile Connections, and open Add snapshot.

## Findings

- None.

## Route

- Next action: `pass`
