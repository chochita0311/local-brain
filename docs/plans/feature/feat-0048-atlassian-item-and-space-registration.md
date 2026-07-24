# FEAT-0048: Atlassian Item And Space Registration

## Metadata

- ID: `feat-0048`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal

- Let the user register an individual Jira ticket, Confluence Page, Jira Space, or Confluence Space through a URL or an explicit accessible-Space selection while keeping Source Instance, coverage, duplication, and remote-call consequences clear.

## Acceptance Contract

- The Atlassian destination exposes separate Jira and Confluence registration paths inside the existing browse-and-inventory screen family.
- An individual Item can be registered from an HTTP or HTTPS URL without first registering its Space.
- A Space can be registered by direct URL or by explicitly requesting an accessible-Space list and selecting a result.
- Opening the page, switching Jira or Confluence views, typing a URL, and browsing existing registrations perform no remote call.
- Accessible-Space retrieval is a visible FEAT-0045 maintenance action governed by FEAT-0044 and cannot invoke write tools.
- Every registration names or visibly identifies its Source Instance so separately connected domains cannot be confused or deduplicated by key alone.
- Key-only input is invalid and creates no Item, stub, unresolved evidence, or lookup request.
- Direct valid URL registration creates or reuses a `reference` Item immediately without implying successful remote metadata or content retrieval.
- Duplicate Canonical URLs inside one Source Instance reuse the FEAT-0046 stable Resource and preserve existing local fields and relations.
- Jira Spaces default to `selected-content`; Confluence Spaces default to regular-Page `full-content`.
- Registration does not pin an Item, assign a Topic or Tag, create a Workstream or Thread relation, or fetch remote content implicitly.
- Unavailable Source Instances, unavailable Cloud Confluence, invalid URLs, unsupported domains, duplicate registrations, remote-list failure, empty Space lists, and partial Space-list results have bounded visible states.
- Existing Atlassian navigation, shared shell, no-script form behavior where applicable, and supported `1440`, `920`, `700`, and `320` layouts remain intact.

## Scope Boundary

- In:
  - Atlassian Item URL registration
  - Jira and Confluence Space URL registration
  - explicit accessible-Space retrieval and selection
  - Source Instance selection or derivation
  - reference-only Item creation and duplicate reuse
  - default Jira and Confluence coverage labels
  - registration inventory and unavailable/error feedback
  - stable URL state, focus restoration, and responsive behavior
- Out:
  - Item or Space content refresh owned by FEAT-0049
  - detail reading, local search, Topic, Tag, and attention owned by FEAT-0050
  - key-only discovery
  - Workstream or Thread mapping during registration
  - automatic registration of every accessible Space
  - old/new migration inference or cross-domain merge
  - changing company authentication or installing unavailable provider apps
  - external writes

## Surface Lanes

- Registration contract lane:
  - path roots: Atlassian route/request models, FEAT-0046 Item and Space registration services, and route tests
  - dependencies: FEAT-0044 and FEAT-0046 passed
  - expected evidence: URL validation, Source Instance identity, default coverage, duplicate reuse, and local-only direct registration
  - evaluator ownership: `contract`, `functional`
- Accessible-Space integration lane:
  - path roots: FEAT-0045 Run composition and validated result consumption for Space-list retrieval
  - dependencies: FEAT-0044 and FEAT-0045 passed
  - expected evidence: explicit remote action, read-only policy, partial/unavailable handling, and no automatic registration
  - evaluator ownership: `contract`, `functional`
- Atlassian inventory lane:
  - path roots: `src/localbrain/templates/atlassian.html`, route-scoped client behavior, `src/localbrain/static/styles.css`, and browser tests
  - dependencies: registration and accessible-Space lanes
  - expected evidence: clear Jira/Confluence and Source Instance orientation, forms, selection, feedback, containment, focus, history, and responsive states
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- `/atlassian` Jira and Confluence browse state.
- Item and Space registration request and result shapes.
- Source Instance and URL validation.
- Canonical duplicate reuse.
- Jira `selected-content` and Confluence regular-Page `full-content` defaults.
- Accessible-Space maintenance action and result projection.
- Progressive-enhancement, history, focus, and visible feedback behavior.

## Required Evaluators

- `contract`: registration ownership, Source Instance boundary, URL-only requirement, default coverage, duplicate reuse, and maintenance handoff.
- `design`: registration hierarchy, long URLs and labels, Source Instance distinction, status treatment, empty/error states, and responsive containment.
- `functional`: direct registration, Space-list retrieval, selection, invalid and duplicate input, unavailable provider, partial result, no-remote ordinary interactions, history, focus, and no-script fallback where supported.
- `ux-heuristic`: clarity of URL versus remote-list paths, remote-call consequence, Source Instance choice, duplicate feedback, and registration completion.

## User-Visible Outcome

- The user can intentionally add one Atlassian Item or register one Space through the appropriate connected domain without triggering hidden synchronization or losing track of which source owns it.

## Entry And Exit

- Entry point: persistent Atlassian navigation, direct `/atlassian` entry, or a registration action from an empty state.
- Exit or transition behavior: successful registration returns to the owning Jira or Confluence inventory with the stable Item or Space visible; remote Space-list selection returns to the same scope without retaining an open disclosure.

## State Expectations

- Default: registered Items and Spaces are grouped or filterable by service and Source Instance.
- Empty: no registration explains the URL and accessible-Space paths with one clear next action per group.
- Loading: only explicit Space-list retrieval displays bounded maintenance progress.
- Duplicate: the existing Resource is revealed with non-destructive feedback.
- Unavailable: the Source Instance remains visible and explains why remote listing cannot proceed.
- Error: entered URL and selected Source Instance remain available for correction or retry.
- Success: the stable reference appears with coverage and remote-validation state.

## Dependencies

- FEAT-0044, FEAT-0045, and FEAT-0046 must be `passed` before this Feature enters build.
- FEAT-0047 may add automatically discovered Items later but is not required for manual registration correctness.
- The existing Atlassian shell and Design Constitution browse-family contract remain authoritative.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- FEAT-0046 Atlassian domain/query modules
- FEAT-0045 Run composition for accessible-Space retrieval
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/static/styles.css`
- route-scoped client behavior under `src/localbrain/static/`
- Atlassian route, registration, duplicate, provider, interaction, and responsive tests
- user-visible Product and external-source owner documentation

## Pass Or Fail Checks

- Pass if valid Item and Space URLs create or reuse one reference without a remote call.
- Pass if key-only, unsupported, and ambiguous cross-instance inputs create nothing and preserve entered values for correction.
- Pass if accessible-Space retrieval is explicit, read-only, Source Instance-scoped, selectable, and non-registering until confirmation.
- Pass if Jira and Confluence defaults are visible and correct.
- Pass if duplicate registration reveals the existing stable Resource without changing local organization.
- Pass if unavailable Cloud Confluence and other provider failures remain bounded and do not affect working Instances.
- Pass if navigation, focus, history, long content, empty/error states, and `1440`/`920`/`700`/`320` layouts remain usable.
- Fail on implicit remote access, automatic bulk registration, cross-instance merge, hidden write capability, lost form state, or unsupported backend implication.

## Regression Surfaces

- Existing Atlassian navigation and Jira/Confluence local view switch.
- Shared shell, active navigation, and no-script route behavior.
- Existing External Resources and Workstream links.
- Maintenance Run console and Source Instance isolation.
- Privacy-safe tracked tests and examples.

## Harness Trace

- Active spec doc: [spec-0048-atlassian-item-and-space-registration](../spec/spec-0048-atlassian-item-and-space-registration.md)
- Active run: [run-20260723-53-atlassian-item-and-space-registration](../run/run-20260723-53-atlassian-item-and-space-registration.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [contract](../evaluation/eval-0048-contract-atlassian-item-and-space-registration.md)
  - [design](../evaluation/eval-0048-design-atlassian-item-and-space-registration.md)
  - [functional](../evaluation/eval-0048-functional-atlassian-item-and-space-registration.md)
  - [UX heuristic](../evaluation/eval-0048-ux-atlassian-item-and-space-registration.md)
- Latest fix note: not created

## Open Review Decisions

- None. A direct URL auto-selects only when its service and normalized domain map to exactly one enabled configured Site. Multiple matches require explicit Site/Source Instance selection; zero matches are rejected without creating a Site or Item.

## Continuity Notes

- `2026-07-23`: initial draft combined direct Item/Space URL registration and explicit accessible-Space selection because both produce the same user-visible registered inventory while preserving distinct local-only and remote-action paths.
- `2026-07-23`: the owner approved sequential execution and the recommended unambiguous auto-selection rule. The Feature advanced through approval to `in-loop` for RUN-20260723-53.
- `2026-07-23`: current Gateway capability inspection confirmed bounded Jira issue search and Confluence Page search but no dedicated project/Space-list tool. Accessible-Space discovery therefore uses one explicit bounded search Run, labels its deduplicated result as partial, and never implies a complete company catalog.
- `2026-07-23`: Attempt 1 passed Contract, Design, Functional, and UX Heuristic evaluation. Direct registration, one-call partial discovery, generated schema ownership, exact `1440`/`920`/`700`/`320` rendering, privacy, and the complete 241-test suite passed without a live provider or model call.
