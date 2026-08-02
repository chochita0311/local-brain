# SPEC-0063: Atlassian Local-Only Add And Access Setup

## Metadata

- ID: `spec-0063`
- Status: `approved`
- Run ID: `run-20260727-68`
- Attempt: `1`
- Parent Feature: [feat-0063-atlassian-local-only-add-and-access-setup](../feature/feat-0063-atlassian-local-only-add-and-access-setup.md)
- Parent PRD: [prd-0010-atlassian-ui-and-interaction-reconciliation](../prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: local registration route → separate access route → Add composition → interaction evidence
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-27`
- Updated: `2026-08-02`

## Source Set

- Approved PRD-0010 and passed FEAT-0062.
- Design Constitution, Design Evaluation, Interaction Evaluation, and Screen
  Alignment `extend` mode.
- Existing LocalBrain card, form, badge, spacing, and responsive primitives.

## Local-Only Registration Contract

- The URL form submits only `service` and `url`; Jira/Confluence, Site,
  Item/Space identity, coverage default, and compact bootstrap title are
  derived locally.
- No source/site/local display name, Provider, configuration reference,
  capability, or remote read belongs to this submission.
- Preview returns only URL-derived local identity facts and never connection
  candidates or generated aliases.

## Optional Access Contract

- A separate POST accepts one persisted Site, Provider, and required actual
  configuration reference.
- It stores or reuses a Source Instance and explicit Site binding without
  capability inspection or remote read.
- Connection management exposes enabled state and one-time legacy reference
  binding, but no editable connection or Site display aliases.

## Presentation And Interaction Contract

- URL registration is the left task and optional access is the right task at
  wide and compact widths.
- At the narrow breakpoint, optional access follows URL registration in DOM
  and visual order with a top divider.
- Validation retains the active URL method and access form values.
- URL preview, no-script POST, redirects, notice focus, and connected discovery
  remain functional.

## Verification

```bash
uv run python -m unittest tests.test_atlassian_registration tests.test_ui_contract -v
uv run python -m unittest discover -s tests
```

- Render the URL method with a synthetic local-only Site at supported wide,
  compact, narrow, and minimum widths.
- Confirm control containment, reading order, focus, long reference/domain
  handling, and no document overflow.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-27`: the initial Spec recorded the in-app Browser adapter as unavailable for required rendered evidence.
- `2026-07-27`: Chrome DevTools later supplied complete Design evidence at `1440`, `920`, `700`, and `320` widths; RUN-20260727-68 passed with no open blocker.
