# FEAT-0054: Atlassian Add And Registered Scope Flow

## Metadata

- ID: `feat-0054`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Let the owner understand what Atlassian knowledge is already registered and add more through URL registration or connected candidate search without learning the internal Source Instance model or choosing from competing side-by-side workflows.

## Acceptance Contract

- Atlassian navigation exposes only the local browse intent and `Add`; `Add / discover` is removed as a top-level label.
- URL registration and connected Space or project search are two methods inside one Add flow and are not presented as equal competing cards.
- The Add orientation leads with Sites and Spaces or projects already persisted in LocalBrain, grouped under one recognizable Site/domain.
- The registered overview includes durable database records regardless of whether a supported UI, confirmed connected candidate, or approved AI-assisted producer created them.
- Unregistered candidates, raw URL occurrences, Session evidence, and Local Context evidence do not appear as registered Sites or Spaces merely for orientation.
- Connection counts and internal `Source Instance / Site` explanations are not the primary summary.
- Connected candidate search selects, in order, the target Site/domain and then one eligible MCP connection. Claude or Codex runner selection remains a third, separately labeled execution choice.
- A Site reachable through official Atlassian MCP and company MCP Gateway appears once as the target while each eligible connection remains a distinct access method and provenance value.
- `Source Instance` remains an internal identity, isolation, and policy concept. Ordinary Add copy uses `MCP 연결`; diagnostics expose the internal term only when recovery requires it.
- Connection binding, availability, and capability details remain reachable through secondary `연결 관리` treatment rather than dominating Add orientation.
- Page load, method switching, URL preview, registered overview, and local validation perform no remote read.
- Ordinary Atlassian bounded-value copy consumes FEAT-0057's approved whole-family presentation policy without mixed raw and logical labels.

## Scope Boundary

- In:
  - browse and Add top-level intent labels
  - one Add flow with URL and connected-search methods
  - persisted Site and Space or project orientation
  - target Site, MCP connection, and runner distinction
  - connection-management secondary treatment
  - empty, populated, unbound, unavailable, ambiguous, validation, failure, and success states
  - responsive and accessible interaction
  - no-script form or link fallbacks where existing routes support them
- Out:
  - changing Source Instance, Site, Space, or Item physical identity
  - new automatic merge or cross-Instance deduplication
  - remote reads on page load or method selection
  - background discovery or refresh
  - credential, OAuth, MCP installation, or Gateway configuration changes
  - connected defects outside the confirmed Add boundary
  - authoring cross-subject value dictionaries

## Surface Lanes

- Registered-scope read-model lane:
  - path roots: Atlassian browse/registration query modules and focused tests
  - dependencies: current persisted Source Instance, Site, Space, and Item contracts
  - expected evidence: one producer-neutral projection of registered Sites and their registered Spaces or projects, with unregistered evidence excluded
  - evaluator ownership: `contract`, `functional`
- Add route and form lane:
  - path roots: `src/localbrain/main.py`, registration/discovery modules, and route tests
  - dependencies: registered-scope read model and passed FEAT-0044 through FEAT-0051
  - expected evidence: target/MCP/runner parameter ownership, local-only transitions, validation, provenance, and no-script execution
  - evaluator ownership: `contract`, `functional`
- Add presentation lane:
  - path roots: Atlassian templates, shared styles, client interactions, and UI contract tests
  - dependencies: route and form lane plus the Design Constitution
  - expected evidence: single-flow hierarchy, registered overview, secondary connection management, responsive containment, focus, and error placement
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Vocabulary-consumer lane:
  - path roots: Atlassian read models and templates
  - dependencies: FEAT-0057 for any covered bounded-value family
  - expected evidence: complete-family labels with no unapproved raw-token fallback
  - evaluator ownership: `contract`, `design`

## Contract Surfaces

- `/atlassian`, `/atlassian/register`, and `/atlassian/spaces/discover`.
- Registration preview and candidate-registration routes.
- Source Instance, Site, Space, Item, and MCP connection identity.
- Registered-scope overview inclusion and exclusion rules.
- Target Site, MCP connection, and runner form values.
- Explicit remote-read consequence and provenance.
- FEAT-0057 presentation mapping for covered value families.

## User-Visible Outcome

- The owner sees what Atlassian Sites and Spaces or projects LocalBrain already knows, chooses one Add method, and understands separately what will be queried, which MCP path will be used, and which runner will execute the bounded operation.

## Entry And Exit

- Entry point: open `/atlassian` and select `Add`.
- Exit or transition behavior: complete a local URL registration, start an explicitly confirmed connected discovery Run, return to local browse, or open secondary connection management without losing orientation.

## State Expectations

- Default: registered Sites and Spaces or projects orient the screen; no remote action has started.
- Empty: explain that no Atlassian scope is registered and offer URL or connected-search entry without leading with `0 connections`.
- Unbound: local registration remains available while remote methods explain the missing binding.
- Unavailable: the Site remains visible and only the affected MCP choice or remote action is unavailable.
- Error: validation remains attached to the selected Add method and preserves entered values and choices.
- Success: the resulting durable record appears in the registered overview independent of producer route.

## Dependencies

- PRD-0008 is `approved`.
- FEAT-0044 through FEAT-0051 remain `passed`.
- FEAT-0053 should pass before final Spec approval so connected first-use findings can be classified rather than rediscovered during implementation.
- FEAT-0057 must be `approved` before Spec handoff and `passed` before building covered Atlassian vocabulary consumers.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/atlassian_browse.py`
- `src/localbrain/atlassian_registration.py`
- `src/localbrain/external_access.py`
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/static/app.js`
- `src/localbrain/static/styles.css`
- focused Atlassian route, registration, UI, and privacy tests
- relevant product, architecture, and data-model owner docs

## Pass Or Fail Checks

- Pass if the screen exposes only browse and Add top-level intents and both Add methods read as one workflow.
- Pass if the overview is generated only from persisted registered records and is independent of supported producer provenance.
- Pass if unregistered candidates and raw evidence cannot appear as registered scope.
- Pass if candidate discovery asks for target Site, MCP connection, and runner as three distinct choices in that order of meaning.
- Pass if one Site is not duplicated merely because more than one MCP connection can reach it.
- Pass if connection management is available but subordinate and ordinary copy does not require `Source Instance`.
- Pass if local states cause zero remote reads and only explicit confirmed discovery starts a bounded Run.
- Pass if supported widths `1440`, `920`, `700`, and `320`, keyboard focus, validation, and no-script paths remain usable.
- Fail on hidden reads, compound `Source Instance / Site` interaction, producer-filtered overview, mixed raw/logical family labels, or identity changes.

## Regression Surfaces

- FEAT-0044 through FEAT-0051.
- Atlassian browse, search, local classification, registration, preview, refresh, and evidence.
- Source Instance isolation and existing unbound connection behavior.
- Persistent shell, responsive navigation, and route fallback.

## Harness Trace

- Active spec doc: [spec-0054-atlassian-add-and-registered-scope-flow](../spec/spec-0054-atlassian-add-and-registered-scope-flow.md)
- Active run: [run-20260724-62-atlassian-add-and-registered-scope-flow](../run/run-20260724-62-atlassian-add-and-registered-scope-flow.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [contract](../evaluation/eval-0054-contract-atlassian-add-and-registered-scope-flow.md), [design](../evaluation/eval-0054-design-atlassian-add-and-registered-scope-flow.md), [functional](../evaluation/eval-0054-functional-atlassian-add-and-registered-scope-flow.md), and [UX heuristic](../evaluation/eval-0054-ux-atlassian-add-and-registered-scope-flow.md)
- Latest fix note: not created

## Open Review Decisions

- None.
- Closed with owner direction and implementation:
  - the browse-side label is `Browser`;
  - URL and connected search use a query-backed segmented control inside `Add`;
  - MCP connection management is an in-page disclosure below the Add flow.

## Continuity Notes

- `2026-07-24`: initial draft separated the confirmed Add information architecture from connected validation and retained Source Instance only as an internal persistence and policy boundary.
- `2026-07-24`: human owner authorized automatic sequential approval and execution for both approved PRDs' Features.
- `2026-07-24`: run `run-20260724-62` passed the persisted-scope, target/MCP separation, whole-family vocabulary, local-only, responsive, and fallback contracts.
