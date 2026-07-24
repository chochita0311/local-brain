# SPEC-0048: Atlassian Item And Space Registration

## Metadata

- ID: `spec-0048`
- Status: `approved`
- Run ID: `run-20260723-53`
- Attempt: `1`
- Parent Feature: [feat-0048-atlassian-item-and-space-registration](../feature/feat-0048-atlassian-item-and-space-registration.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: registration contract → bounded Space discovery → inventory UI → durable docs and generated schema
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Source Set

- Human approval: run PRD-0007 Features sequentially and use the recommended Source Instance selection rule.
- Parent Feature and PRD: approved FEAT-0048 boundary and PRD-0007.
- Passed dependencies: FEAT-0044 through FEAT-0047.
- Current capability evidence: Gateway Jira exposes bounded field-selective issue search and project detail; Gateway Wiki exposes bounded Page search/read/hierarchy, but neither exposes a dedicated complete project/Space-list operation.
- Existing product truth: `/atlassian` browse shell, FEAT-0046 stable Item/Site/Space services, FEAT-0045 external-sync Run, shared Run console, and current Design Constitution.
- Design mode: `screen-alignment: extend`; preserve the existing browse-and-inventory family, shell, tab geometry, tokens, and breakpoint contract.

## Implementation Goal

- Deliver a local-first Jira/Confluence registration screen that creates or reuses Items and Spaces from actual URLs without hidden I/O, and exposes an explicit bounded maintenance action for partial accessible-Space discovery when current read capability permits it.

## In-Scope Behavior

1. Add a strict registration URL recognizer:
   - Jira issue URLs and Confluence Page URLs create `reference` Items.
   - Jira project URLs and Confluence Space URLs create Spaces.
   - key-only text, REST URLs, unsupported paths, and service mismatches fail before mutation.
2. Resolve Source Instance and Site from the selected service plus normalized domain:
   - exactly one enabled match may auto-select
   - multiple matches require one explicit Site option that visibly includes Source Instance and domain
   - no match is rejected and never auto-creates a Site
3. Reuse FEAT-0046 stable Item identity for duplicate canonical URLs and preserve all local fields and relations.
4. Persist Space canonical URL and coverage:
   - Jira defaults to `selected-content`
   - Confluence defaults to regular-Page `full-content`
   - direct and discovered registration share one idempotent service function
5. Render enabled and unavailable Source Instances, registered Items, registered Spaces, coverage, remote-validation state, and duplicate/success/error feedback without remote access.
6. Add one explicit Space discovery action:
   - one Source Instance/Site at a time
   - one bounded FEAT-0045 maintenance Run
   - Jira uses field-selective issue search with `project` only
   - Confluence uses regular-Page search with `space` only
   - the result is always labeled partial because empty or unobserved Spaces may be absent
   - candidates are not registered until the user selects one and submits its actual or locally constructed Site URL
7. Preserve server-rendered forms as the no-script path. A small route-scoped client may poll an explicitly started Run, restore focus after success, and update local time labels; failure falls back to ordinary navigation/reload.
8. Keep the shared shell, Jira/Confluence view URL, entered URL on errors, and responsive layouts stable at `1440`, `920`, `700`, and `320`.

## Out-Of-Scope Behavior

- Complete company-wide project or Space enumeration.
- Hidden remote access, startup inspection, page-load refresh, or scheduled polling.
- Item/Space content refresh, classification, detail reading, or Workstream linking.
- Automatic registration of every discovered candidate.
- Provider writes, credentials, authentication repair, or capability installation.
- Treating a bounded search sample as a complete accessible catalog.

## Affected Surfaces

- `src/localbrain/atlassian.py`
- new `src/localbrain/atlassian_registration.py`
- `src/localbrain/schema.sql` and compatible additive migration
- `src/localbrain/main.py`
- `src/localbrain/templates/atlassian.html`
- new route-scoped `src/localbrain/static/atlassian.js`
- `src/localbrain/static/styles.css`
- focused registration, schema, route-contract, and UI-contract tests
- Atlassian, architecture, privacy, product, and maintenance owner docs
- schema presentation and cleanup-audit artifacts

## Surface Lanes

- Registration contract:
  - path roots: Atlassian domain/registration services, DDL, migration, focused tests
  - dependency order: first
  - implementation responsibility: URL classification, exact Site selection, duplicate reuse, Space URL/coverage ownership
  - validation evidence: valid/invalid/ambiguous/cross-instance/idempotent synthetic cases
- Bounded Space discovery:
  - path roots: registration orchestration, FEAT-0045 manifest composition, Run projection
  - dependency order: after registration identity
  - implementation responsibility: explicit one-call partial catalog, current capability guard, candidate projection, no auto-registration
  - validation evidence: manifest inspection, unavailable state, partial result, candidate confirmation
- Inventory UI:
  - path roots: `/atlassian` routes, template, route-scoped client, shared CSS
  - dependency order: after read models
  - implementation responsibility: form state, Source Instance/domain orientation, local inventory, feedback, focus/history, responsive containment
  - validation evidence: static/route tests and rendered browser checks at all four widths
- Durable docs and generated schema:
  - path roots: owner docs, schema presentation, cleanup audit
  - dependency order: after stable data behavior
  - implementation responsibility: update ownership and generated consumers
  - validation evidence: documentation, Mermaid, generated parity, privacy, and regression checks

## State And Interaction Contract

- Default: view switching and all local inventory reads perform zero remote calls.
- No configured Site: forms remain visible but registration explains that a matching Source Instance/Site is required.
- Ambiguous: the URL remains entered and matching Source Instance/Site options remain selectable.
- Duplicate: the existing stable Item or Space is focused and identified as reused.
- Discovery ready: the control identifies Source Instance, Site, one remote read, maintenance classification, and partial-result semantics.
- Discovery unavailable: disabled/stale/unavailable capability remains visible; no Run is queued.
- Discovery running: current inventory remains usable; only the discovery panel polls or offers manual reload.
- Discovery result: candidates remain unregistered until one explicit confirmation.
- Error: bounded application copy appears beside the owning form; raw provider payload and local runtime paths are not exposed.

## Data And Contract Assumptions

- `atlassian_spaces.canonical_url` is the stable local navigation URL for the registered Space.
- `atlassian_spaces.coverage` is independent of Item coverage and accepts exactly `selected-content` or `full-content`.
- A direct URL can reuse only an already configured enabled Site. FEAT-0046's lower-level automatic Site creation remains available to evidence ingestion but is not exposed by this registration UI.
- The Space discovery target uses `scope.kind = space`, one `source_root` locator, metadata-only coverage, one request, and a call budget of one.
- Jira normalized discovery metadata uses the allowlisted `project` field; Confluence uses `space`. Each may be a single object or bounded list of objects.
- The host-side external executor remains injected operational state. An absent executor is a visible unavailable condition, not permission to let the model call external tools.

## Contract Surfaces

- Producer expectations:
  - configured Site rows and current capability observations precede registration/discovery
  - direct forms submit actual HTTP(S) URLs
  - validated provider adapters return only bounded `project` or `space` candidate facts
- Consumer expectations:
  - FEAT-0049 consumes registered Item/Space IDs and stored Space coverage
  - FEAT-0050 consumes the same inventory without changing registration identity
- Generated artifacts:
  - schema presentation and cleanup audit are regenerated from canonical DDL and owner docs
- Source-of-truth owner:
  - DDL in `schema.sql`; identity behavior in `atlassian.py`; product registration behavior in `atlassian_registration.py`; visible contract in the Atlassian template
- Stale-assumption check:
  - inspect FEAT-0046 Space constructors/tests, schema counts/owners, Run console, Source Instance capability state, existing Atlassian navigation, and all External Resource consumers

## Required Evaluators

- Contract: exact URL/service/Site identity, Space URL/coverage, duplicate reuse, discovery manifest, capability guard, and no-auto-registration.
- Design: browse-family alignment, hierarchy, long labels/URLs, feedback, unavailable/partial states, focus, and four required widths.
- Functional: direct Item/Space registration, ambiguity, invalid/key-only, duplicate, discovery start/result/unavailable, no implicit calls, no-script forms, history, and regression.
- UX heuristic: consequence clarity, Source Instance distinction, partial-catalog wording, duplicate completion, and avoidance of an action wall.

## Acceptance Mapping

- Direct Item and Space URL paths → strict recognizer plus local POST routes.
- Source Instance safety → exact enabled Site matching and explicit ambiguity selection.
- Local-only ordinary interaction → pure read models and direct registration with no external executor call.
- Default Space coverage → persisted service-specific values.
- Accessible-Space selection → explicit one-call maintenance Run plus unregistered candidate confirmation.
- Bounded states → inline form feedback and Source Instance capability labels.
- UI continuity → existing shell/tabs, server-rendered forms, route-scoped enhancement, and responsive rules.

## Evaluation Focus

- Prove a key-only value, unknown domain, or service-mismatched URL creates no row.
- Prove ambiguous same-domain Source Instances cannot be silently selected.
- Prove duplicate registration retains one stable Resource and all local relations.
- Prove page load, tab switch, form typing, and inventory rendering never start discovery.
- Prove discovery is one read-only selected Run, labels partial coverage, and never registers candidates automatically.
- Render long synthetic domains and URLs plus empty, error, unavailable, and populated states at all four widths.

## Open Blockers

- None. The owner approved the selection rule and sequential run. Dedicated complete Space enumeration is not claimed because current capability evidence does not support it.

## Continuity Notes

- `2026-07-23`: Spec approved for RUN-20260723-53 using the `fullstack-product` profile and `screen-alignment: extend` mode.
