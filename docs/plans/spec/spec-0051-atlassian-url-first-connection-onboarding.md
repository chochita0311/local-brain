# SPEC-0051: Atlassian URL-First Connection Onboarding

## Metadata

- ID: `spec-0051`
- Status: `approved`
- Run ID: `run-20260724-56`
- Attempt: `1`
- Parent Feature: [feat-0051-atlassian-url-first-connection-onboarding](../feature/feat-0051-atlassian-url-first-connection-onboarding.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: registration contract → routes and interaction → Atlassian UI → durable contracts
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Source Set

- Human approval on `2026-07-24`: proceed with URL parsing, Source/Site creation, and later editing.
- Passed PRD-0007 and FEAT-0044 through FEAT-0050.
- Current implementation: strict registration URL recognizer, stable Source/Site/Item tables, local-only direct registration, explicit refresh, and Atlassian browse UI.
- Operational evidence: the official Atlassian connector exposed accessible-Site metadata needed to confirm the distinction between provider and Site; no ticket body was read.
- Design mode: `screen-alignment: extend`.

## Implementation Goal

- Replace the no-configured-Site dead end with a server-owned URL-first setup flow that preserves the existing access, identity, and no-hidden-I/O contracts.

## In-Scope Behavior

1. Add a local preview projection over the existing strict URL recognizer.
2. Return service, kind, normalized URL/domain, remote key or ID, and matching configured Sites without returning configuration references.
3. Extend direct registration:
   - existing Site selection or unambiguous derivation keeps current behavior
   - `site_id = new` requires an explicit provider/access path
   - derive a stable local instance key from provider, service, and domain
   - reuse only an exact compatible existing Source/Site
   - create Source Instance, Site, and Item or Space inside one transaction
4. Allow optional configuration reference:
   - official Atlassian accepts a Cloud ID
   - Gateway accepts a bounded local configuration alias
   - omission creates an unbound Source Instance suitable only for local references
5. Add bounded connection editing:
   - source display name
   - Site display name
   - enabled state
   - one-time binding when currently unbound
   - provider, service, bound reference, domain, and IDs remain immutable
6. Enhance the registration form:
   - URL detection summary
   - existing Site versus new connection selection
   - human-readable access-path choices
   - fields shown only for new setup
   - ordinary form submission remains the executable fallback
7. Show existing Source/Site rows with provider, domain, capability/binding state, and an edit disclosure.
8. Preserve no remote calls for every new route and interaction.

## Out-Of-Scope Behavior

- Web-process discovery of currently connected Codex or Claude MCP tools.
- Automatic provider selection when no registered Site exists.
- Capability observation creation, connector authentication, or remote content retrieval.
- Destructive removal or reassignment of Source/Site descendants.
- Editing canonical domains or replacing a bound configuration reference.

## State And Interaction Contract

- Known match: preview identifies the matching connection and ordinary registration reuses it.
- No match: preview requests one explicit access-path choice and opens the new-connection fields.
- Unbound: connection is labeled local-only; discovery and refresh readiness remain false.
- Bound but unchecked: binding is visible while capability remains unknown.
- Invalid URL: entered value remains and no Source, Site, or Item/Space row is created.
- Save failure: all onboarding writes roll back and the owning form retains values.
- Edit: server-rendered disclosure submits an ordinary form and returns to the same Jira or Confluence setup scope.
- Provider terminology: the visible field is `MCP 연결 (Provider)`; internal enum values remain implementation metadata.

## Data And Contract Assumptions

- Existing DDL is sufficient; no schema migration is required.
- A generated `instance_key` is a stable local slug. A collision with incompatible identity receives a deterministic bounded suffix instead of mutating the existing Source Instance.
- `config_ref = NULL` is an approved unbound state already supported by FEAT-0044.
- Site display name defaults to the first domain label; Source display name defaults to access-path label plus normalized domain.
- For an official connection, the Cloud ID is configuration identity and may also later become confirmed remote Site identity, but this feature does not perform that remote confirmation.

## Contract Surfaces

- Producer:
  - registration preview and forms provide strict URL and explicit provider only when creating
  - edit forms provide bounded display values and optional first binding
- Consumer:
  - FEAT-0048 registration consumes the created Site immediately
  - FEAT-0049 continues to require current capability before remote work
  - FEAT-0050 continues to use stable Item IDs and local organization
- Source of truth:
  - identity policy remains in `external_access.py` and `atlassian.py`
  - onboarding composition belongs in `atlassian_registration.py`
  - route and visible behavior belong in `main.py` and `atlassian.html`

## Acceptance Mapping

- URL-first setup → preview projection plus `new` registration mode.
- Provider clarity → access-path labels and no URL inference.
- Atomicity → one transaction and rollback tests.
- Editability → bounded Source/Site edit route and connection inventory.
- No hidden I/O → pure local services and route tests with executor call counters.
- Screen-family consistency → existing action-card, form, badge, disclosure, toolbar, and responsive token families.

## Evaluation Focus

- Exact existing/new/ambiguous/invalid transaction matrix.
- Unbound versus bound and capability state wording.
- Bound identity mutation rejection.
- Preview response privacy and no configuration-reference exposure.
- No-script registration/edit paths and route-scoped enhancement fallback.
- Long domain/name containment and supported-width layout.

## Open Blockers

- None.
