# SPEC-0054: Atlassian Add And Registered Scope Flow

## Metadata

- ID: `spec-0054`
- Status: `approved`
- Run ID: `run-20260724-62`
- Attempt: `1`
- Parent Feature: [feat-0054-atlassian-add-and-registered-scope-flow](../feature/feat-0054-atlassian-add-and-registered-scope-flow.md)
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: registered-scope read model → Add route/form → Add presentation → vocabulary consumer
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Source Set

- Human approval on `2026-07-24`: execute both approved PRDs' Features automatically and sequentially.
- PRD-0008, FEAT-0053 connected findings, FEAT-0057 value registry, and the owner's confirmed information architecture.
- Existing Atlassian registration, browse, discovery, capability, maintenance Run, and no-hidden-read contracts.
- Design Constitution, Design Evaluation, and Interaction Evaluation using the Fullstack Product profile.
- Screen Alignment mode: `extend`; the existing LocalBrain constitution is the target system and no durable Figma file key is owned by this repository.

## Registered-Scope Contract

- Build the Add orientation only from persisted `atlassian_sites`, `atlassian_spaces`, `atlassian_items`, and their owning Source Instance rows.
- Group target Sites by selected service plus `normalized_domain`.
- Keep each Source Instance/Site row as a distinct MCP connection under the group.
- Deduplicate repeated Space and Item remote identities inside the orientation only; do not merge physical rows or provenance.
- Do not query or include evidence scans, URL sightings, Session/Document evidence, maintenance manifests, or unconfirmed candidates.

## Add Interaction Contract

- Top-level Atlassian intents are `Browser` and `Add`.
- `Add` contains one query-backed method selector:
  - `method=url` renders URL registration;
  - `method=connected` renders connected candidate search.
- Method selection is a GET and performs no remote read.
- URL registration derives the target Site from the URL and asks for an MCP connection only when needed.
- Connected candidate search asks in order for:
  1. persisted target Site/domain;
  2. one eligible MCP connection under that domain;
  3. Claude or Codex execution owner.
- The POST carries `target_domain` and `site_id` separately. Preparation rejects a domain mismatch before capability authorization or Run creation.
- Connection administration remains a closed, secondary `MCP 연결 관리` disclosure.
- Validation keeps the active method and entered values. Existing no-script forms and redirect fragments remain functional.

## Vocabulary Contract

- Register `value_label` as the shared server-rendered template helper.
- The Atlassian surface consumes complete registry mappings for provider, service, enabled state, effective capability state, Space coverage, Item type, Item coverage, Item attention, Item freshness, maintenance runner, and maintenance status.
- Effective capability state includes `unavailable`, `unauthorized`, and `error` because `capability_state` legitimately projects those values.
- No covered family mixes raw and logical labels on the Atlassian page.

## Presentation Contract

- Lead with `등록된 Atlassian 범위`, then the single Add flow, then secondary connection management and detailed inventory.
- Use the existing card, segmented-control, status, spacing, and typography system without introducing a foreign visual system.
- At supported widths `1440`, `920`, `700`, and `320`, the registered scope and Add controls remain contained with no horizontal document overflow.
- Labels, select order, disclosure semantics, focus destinations, live URL preview, and local validation remain keyboard and no-script legible.

## Verification

```bash
uv run python -m unittest tests.test_value_registry tests.test_ui_contract tests.test_atlassian_registration -v
uv run python scripts/build-data-model-value-dictionaries.py check
```

- Render the connected method against a synthetic local DB at `1440`, `920`, `700`, and emulated `320` widths.
- Confirm no document overflow, no console errors, and only the local document/static assets on page load.
- Confirm target selection exposes both eligible MCP connections for one domain.

## Open Blockers

- None.
