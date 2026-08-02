# FEAT-0063: Atlassian Local-Only Add And Access Setup

## Metadata

- ID: `feat-0063`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0010-atlassian-ui-and-interaction-reconciliation](../prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md)
- Created: `2026-07-27`
- Updated: `2026-07-27`

## Goal

- Let the owner register an Atlassian URL locally with only the URL, while
  optional remote access is configured in a distinct adjacent task.

## Acceptance Contract

- Local-only Add accepts URL only and derives service, Site domain, Item/Space
  identity, and compact bootstrap title locally.
- It does not request or create Provider, connection name, Site name, local
  display name, reference, capability, or remote access.
- A separate access card selects a registered Site, Provider, and actual
  reference; generated labels are not editable aliases.
- The access card sits to the right at wide/compact widths and follows
  Local-only Add at narrow widths.
- No action performs an implicit remote read.

## Scope Boundary

- In: registration and access routes, read models, templates, route-scoped
  JavaScript, Atlassian layout/copy, validation, focused tests.
- Out: remote writes, automatic capability inspection, shared select geometry,
  connection-alias editing, and multi-binding refresh selection.

## Surface Lanes

- Server lane: registration/access handlers and validation.
- Presentation lane: `/atlassian` Add and connection-management regions.
- Interaction lane: URL preview, form error retention, responsive order, and
  no-script submission.

## Dependencies

- FEAT-0062 must be `passed` before build.

## Pass Or Fail Checks

- Pass if URL-only Jira/Confluence Item and Space registration works with no
  configured access.
- Pass if bootstrap titles are compact and deterministic.
- Pass if optional access creates/reuses a real binding independently.
- Pass if removed name/reference fields do not remain in Local-only Add.
- Pass if wide, compact, narrow, keyboard, error, and no-script states remain
  usable.

## Regression Surfaces

- Atlassian browse, discovery, connection management, Item detail, and refresh.
- Existing registered connections and disabled/bound state presentation.

## Harness Trace

- Active spec doc: [spec-0063-atlassian-local-only-add-and-access-setup](../spec/spec-0063-atlassian-local-only-add-and-access-setup.md)
- Active run: [run-20260727-68-atlassian-local-only-add-and-access-setup](../run/run-20260727-68-atlassian-local-only-add-and-access-setup.md)
- Execution profile: `fullstack-product`
- Latest evaluator report: [contract](../evaluation/eval-0063-contract-atlassian-local-only-add-and-access-setup.md), [design](../evaluation/eval-0063-design-atlassian-local-only-add-and-access-setup.md), [functional](../evaluation/eval-0063-functional-atlassian-local-only-add-and-access-setup.md), [UX heuristic](../evaluation/eval-0063-ux-atlassian-local-only-add-and-access-setup.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-27`: approved for sequential execution after FEAT-0062.
- `2026-07-27`: implementation and automated/no-script verification completed;
  required rendered Browser evidence remains unavailable.
- `2026-07-27`: Chrome DevTools rendered evidence passed at `1440`, `920`,
  `700`, and `320` widths. The owner-requested redundant Local-only
  explanation and coverage help were removed, and the Feature passed.
- `2026-07-27`: owner follow-up removed the remaining HTTP(S) Item/Space field
  helper; the URL preview remains the only contextual explanation.
