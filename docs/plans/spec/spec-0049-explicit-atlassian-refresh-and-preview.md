# SPEC-0049: Explicit Atlassian Refresh And Preview

## Metadata

- ID: `spec-0049`
- Status: `approved`
- Run ID: `run-20260723-54`
- Attempt: `1`
- Parent Feature: [feat-0049-explicit-atlassian-refresh-and-preview](../feature/feat-0049-explicit-atlassian-refresh-and-preview.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: local scope preview → multi-instance Run composition → validated application → progress and recovery UI
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Source Set

- Human approval: run the remaining PRD-0007 Features sequentially using the recommended decisions.
- Parent Feature and PRD: approved FEAT-0049 boundary and PRD-0007.
- Passed dependencies: FEAT-0044 through FEAT-0048.
- Existing product truth: stable Site/Space/Item identity and freshness, source-neutral external-sync maintenance Runs, local-only registration inventory, Workstream/Thread polymorphic links, shared Run console, and the current Design Constitution.
- Current provider evidence: Jira supports bounded issue metadata/description reads; Confluence supports bounded regular-Page search/read/hierarchy. Gateway Confluence pagination is offset-based with at most 200 results per search; official Cloud Confluence remains unavailable until its capability becomes current.
- Design mode: `screen-alignment: extend`; preserve the browse-and-inventory and Workstream workspace families, shell, action hierarchy, semantic states, and `1440`/`920`/`700`/`320` contract.

## Implementation Goal

- Resolve every approved local refresh scope without external access, let the user see and adjust the exact bounded target set, start one read-only maintenance Run, and apply only host-validated target outcomes while preserving last-known and user-owned state.

## In-Scope Behavior

1. Add a pure local refresh scope resolver for:
   - one Item
   - one registered Space
   - one Thread's directly linked Atlassian Items
   - one Workstream's direct plus Thread-linked Atlassian Items, deduplicated
   - every Atlassian Item already known locally
2. Give Thread, Workstream, Space, and all-known scopes the same lightweight preview surface. Item scope uses the same read model as a compact confirmation rather than a dense multi-select table.
3. Preview includes source/service/Site/Space identity, canonical URL, Item coverage, freshness, last successful check, last body application, calculated request count, and one inclusion checkbox per Item.
4. Default selection is true for `unknown`, `due`, `stale`, and `unavailable`; `current` is visible and false. The user can override either direction.
5. Preview performs no capability inspection, external dispatch, model execution, or database mutation.
6. Preserve one user action as one FEAT-0045 maintenance Run even when the selected Workstream or all-known scope crosses Source Instances:
   - the additive manifest contract may assign a registered Source Instance to each target
   - every target is authorized against its own current FEAT-0044 capability before the Run row is created
   - the query projection stores a concrete Source Instance/service for a homogeneous Run and `NULL`/`mixed` for a heterogeneous Run
   - existing single-source manifests remain byte-compatible and loadable
7. Build Item requests from persisted coverage:
   - `reference`: identity check only; any provider metadata/body remains Run evidence and is not applied to Item persistence
   - `metadata`: bounded metadata/identity read
   - `indexed`: bounded metadata plus body for Jira, or one regular-Page read carrying eligible metadata/body/hierarchy for Confluence
   - known remote version/update/content hash are supplied as change hints but never skip the explicit check by themselves
8. Enforce the normal hard Run budget before preparation:
   - at most 500 manifest targets remain a foundation validation ceiling
   - the initial product preview permits at most 20 calculated provider requests in one Run
   - Jira indexed Items normally consume two requests; other Items normally consume one
   - overflow rows remain visible but unselected and explain that another explicit Run is required
9. Registered Space behavior is bounded and coverage-specific:
   - Jira `selected-content` resolves only locally known Items assigned to that project; it never enumerates every remote issue description
   - Confluence `full-content` includes locally known regular Pages and one explicit catalog page of at most 200 regular-Page candidates
   - page 1 is the default; a numeric Gateway continuation page is another explicit preview/Run
   - newly identified regular Pages become indexed local stubs with `stale` projection state and enter a later explicit content batch; comments, attachments, blogs, and other excluded types never enter the catalog
10. Apply terminal result targets through FEAT-0046 using the stable target-to-Item mapping:
    - success/no-change updates only eligible remote state and hash-gated content
    - failure records bounded availability evidence and retains last-known content
    - reference targets strip ineligible metadata/body before Item application
    - one malformed or mismatched target aborts result application before partial database mutation
    - application is idempotent and records no Topic, Tag, note, Workstream relation, or provider write
11. Project progress and terminal outcomes from the common Run ledger and validated structured result. Failed/unavailable/not-found Items can open a new local preview with only those stable IDs selected; no automatic retry occurs.
12. Add contextual entry links from the Atlassian inventory, registered Spaces/Items, Workstream heading, and Thread body. Return destinations are local allowlisted paths and never provider-controlled redirects.

## Out-Of-Scope Behavior

- Scheduler, background polling, startup refresh, browse-time refresh, or automatic retry.
- Company-wide enumeration or any meaning of all-known beyond current local Items.
- One Run per Item or hidden fan-out into several user-invisible maintenance Runs.
- Dynamic provider calls not present in the validated manifest.
- Automatically fetching bodies for newly cataloged Confluence Pages in the same Run.
- Comments, attachments, blogs, whiteboards, databases, historical revision bodies, or arbitrary Jira custom fields.
- Summary/classifier execution, Topic/Tag generation, Suggestions, Workstream mutation, purge, or provider writes.
- General Item detail reading and local classification owned by FEAT-0050.

## Affected Surfaces

- `src/localbrain/external_sync.py`
- `src/localbrain/atlassian.py`
- new `src/localbrain/atlassian_refresh.py`
- `src/localbrain/runner.py`
- `src/localbrain/main.py`
- `src/localbrain/workstreams.py`
- `src/localbrain/templates/atlassian.html`
- new refresh preview template and route-scoped client behavior
- `src/localbrain/templates/workstream.html`
- `src/localbrain/static/styles.css`
- focused scope, manifest, application, route, interaction, and UI-contract tests
- Architecture, Product, Privacy, Maintenance Runner, and Atlassian/Maintenance data-model owner docs

## Surface Lanes

- Local scope and preview:
  - path roots: refresh query service, Workstream/Thread link resolver, preview routes and tests
  - dependency order: first
  - implementation responsibility: exact membership, deduplication, default selection, request-cost projection, no-I/O guarantee
- Run composition:
  - path roots: additive external-sync manifest and envelope projection, Item request plans, Runner preparation
  - dependency order: after preview
  - implementation responsibility: multi-instance authorization, one Run, 20-request hard product limit, single-source compatibility
- Result application:
  - path roots: FEAT-0046 application and refresh coordinator
  - dependency order: after Run composition
  - implementation responsibility: stable target mapping, eligibility stripping, atomic/idempotent application, failure retention, catalog continuation
- Interaction and recovery:
  - path roots: Atlassian/Workstream contextual entries, preview, Run status/result, route-scoped client, CSS
  - dependency order: after read models and application
  - implementation responsibility: consequence clarity, selection, disabled/overflow states, return orientation, retry, focus/history, responsive containment

## State And Interaction Contract

- Default preview: local target count and calculated calls appear before any executable control.
- Empty: the owning scope remains identified and explains that no known Atlassian Item is mapped.
- Capability unavailable: affected rows remain visible but disabled; no Run can be queued until every selected target has current capability.
- Over budget: extra rows remain visible and unchecked; the selected call total explains the 20-call boundary.
- Ready: the action states selected Item and call counts, selected runner, maintenance classification, and remote-read consequence.
- Running: current local content remains readable; the common Run detail owns polling and cancellation.
- Partial: every target outcome is visible with stable Item identity; failed targets offer an explicit retry preview.
- No change: check time advances while content-applied time and FTS fingerprint remain unchanged.
- Error: selection and local source orientation remain recoverable; raw provider content and private artifact paths are not exposed in feedback.

## Data And Contract Assumptions

- `target_id` uses `atlassian-item-<external_resource_id>` for Item application and a separate bounded `atlassian-space-catalog-<space_id>-<page>` form for Confluence catalog work.
- An Item's canonical URL is the preferred locator. Confirmed remote ID is a known fact, not a caller-selected source boundary.
- All selected targets must belong to enabled configured Sites and Source Instances at preparation time.
- Mixed Source Instance execution is an additive FEAT-0045 manifest capability, not a new maintenance task type or separate provider-specific Run table.
- The host executor remains the only provider caller. Claude or Codex sees validated evidence and returns only the existing bounded presentation summary.
- Preview request counts are calculated from the same deterministic request-plan builder used during preparation.

## Contract Surfaces

- Producer expectations:
  - Workstream/Thread links use `entity_type = external` and an `external_resources.id` that has a strict Atlassian extension
  - registered Items retain canonical URLs and coverage
  - every selected Source Instance has a current capability observation and the host executor is injected
- Consumer expectations:
  - FEAT-0050 reads freshness, content-applied time, Run history, and local classification without causing refresh
  - existing single-source Space discovery and external-sync Runs remain compatible
- Source-of-truth owner:
  - scope and request planning in `atlassian_refresh.py`; authorization/envelope in `external_sync.py`; Item mutation in `atlassian.py`; execution in `runner.py`
- Stale-assumption check:
  - inspect every Workstream/Thread external-link query, current capability state, registered Space defaults, provider policy arguments, Run cancellation/detail projection, and FEAT-0046 application constraints

## Required Evaluators

- Contract: exact scope membership, multi-instance authorization, one-Run projection, calculated budget, coverage request plans, atomic application, and retained source/local ownership.
- Design: preview hierarchy, checkboxes, density, capability/freshness/overflow states, progress/outcomes, long identity, contextual entry, and four supported widths.
- Functional: every scope, default and overridden selection, mixed instances, budget rejection, no-change/changed/failure/invalid/cancel/retry, Space page boundary, no implicit calls, and complete regression.
- UX heuristic: scope confidence before calls, clear all-known meaning, action-wall avoidance, partial recovery, and Workstream/Thread return orientation.

## Acceptance Mapping

- Exact approved scopes → pure local resolver and stable ID deduplication.
- Required preview → server-rendered GET state with no executor or Runner call.
- Freshness defaults → FEAT-0046 derived freshness mapped to checked state.
- One selected Run → additive per-target Source Instance manifest authorization.
- Bounded Space coverage → Jira known selected Items; Confluence 200-result explicit catalog page plus later body batch.
- Efficient persistence → known hints, content hashes, and FEAT-0046 idempotent application.
- Partial recovery → validated per-target result projection and explicit failed-ID retry preview.
- No implicit access → contextual links are GET-only local previews; POST is the only preparation/start boundary.
- Responsive acceptance → server and browser evidence at `1440`, `920`, `700`, and exact emulated `320`.

## Verification Plan

- Focused unit tests for Item/Space/Thread/Workstream/all-known membership and request counts.
- External-sync compatibility tests for old single-source and new mixed-source manifests/envelopes.
- Result-application tests for atomic mapping, reference stripping, no-change hash gating, failure retention, invalid rollback, and retry selection.
- Route/UI tests for no-script preview/start, unavailable executor/capability, over-budget state, contextual links, and local return validation.
- Render synthetic empty, long, mixed-source, current/due/stale/unavailable, over-budget, running, partial, and retry states at all supported widths.
- Run data-model docs, Mermaid, generated schema, cleanup audit, complete Python suite, JavaScript syntax, privacy, and diff whitespace checks.

## Explicit Non-Goals

- No background sync, provider write, general federated search, classifier, Topic, Tag, note, or destructive deletion.
- No claim that a bounded Confluence catalog page is a complete Space mirror.
- No remote call merely to decide what the preview should contain.

## Decision Log

- `2026-07-23`: owner-approved recommended decision gives Thread the same lightweight local preview as Workstream/all-known.
- `2026-07-23`: initial execution uses the existing 500-target validation ceiling but a stricter 20-calculated-request product batch; overflow requires another explicit Run.
- `2026-07-23`: one user action remains one maintenance Run across Source Instances through additive per-target authorization; this preserves the approved all-known meaning without weakening Source Instance isolation.
- `2026-07-23`: Jira Space refresh is known-selected-content only. Confluence catalog discovery is one explicit page of at most 200 regular Pages, followed by explicit content batches for newly known Items.
