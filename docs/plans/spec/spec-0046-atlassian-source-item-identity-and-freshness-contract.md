# SPEC-0046: Atlassian Source Item Identity And Freshness Contract

## Metadata

- ID: `spec-0046`
- Status: `approved`
- Run ID: `run-20260723-51`
- Attempt: `1`
- Parent Feature: [feat-0046-atlassian-source-item-identity-and-freshness-contract](../feature/feat-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lanes: identity and compatible upgrade → remote ownership and freshness → content normalization and FTS → durable docs and generated schema
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Source Set

- Human request and approval: retain stable local Resource relations, split Site domains below a Source Instance, remove global URL uniqueness compatibly, treat due as advisory, retain last-known content, and execute the exact strict one-to-one table contract now.
- Parent Feature and PRD: approved FEAT-0046 and PRD-0007.
- Dependency truth: passed FEAT-0044 Source Instance/read policy and passed FEAT-0045 validated external-sync result contract.
- Implementation truth: current `external_resources`, polymorphic Workstream/Thread/checkpoint links, SQLite FTS, compatible migration, schema presentation, and query/retrieval consumers.
- Governing contracts: Architecture, Privacy And Data Handling, Work Organization And Resources, Derived Retrieval Index, Source Registry And Scans, and schema recovery/presentation policies.

## Implementation Goal

- Add a source-specific Atlassian extension whose stable local identity is exactly the existing External Resource ID, whose Site/remote/URL/content concerns cannot overwrite local facts, and whose deterministic freshness and FTS projection can consume validated FEAT-0045 results without making any remote or model call.

## In-Scope Behavior

1. Remove only the global `external_resources.url UNIQUE` constraint through a guarded, backup-producing compatible migration that preserves every row, ID, and polymorphic relation.
2. Add the exact source-specific split:
   - `atlassian_sites`: stable domain/tenant identity below one Source Instance
   - `atlassian_spaces`: optional Jira or Confluence containment under one Site
   - `atlassian_items`: strict one-to-one extension keyed by `external_resources.id`
   - `atlassian_item_urls`: exact observed URL plus normalized canonical/alias identity
   - `atlassian_item_remote_state`: bounded metadata and check/version/failure evidence
   - `atlassian_item_content`: source body, deterministic normalized document/text, hashes, version, and FTS projection state
3. Enforce one Source Instance service per Item, Site-contained uniqueness, one canonical URL per Item, no automatic collision merge, and in-place manual-stub resolution.
   - a single matching unbound manual External Resource is reused automatically
   - multiple matching unbound Resources are ambiguous and fail before mutation
4. Keep External Resource title, summary, source role, links, and future local organization user-owned. Remote metadata and content never overwrite them.
5. Derive `unknown`, `current`, `due`, `stale`, and `unavailable` at read time:
   - Jira due after seven days and Confluence due after 30 days from last successful check
   - due performs no I/O and does not imply remote change
   - stale requires confirmed change or projection mismatch
   - unavailable reflects the latest explicit unsuccessful check while retaining last-known data
6. Apply validated source outcomes idempotently:
   - unchanged updates check/version evidence only
   - changed metadata remains separate from content
   - changed content writes only when the canonical source hash changes
   - unavailable/not-found/error retain prior content and FTS
   - partial metadata responses merge observed fields without erasing unrequested last-known fields
7. Normalize Jira ADF and supported Confluence ADF, HTML, Markdown, and plain text with deterministic local code, source preservation, safe HTML treatment, versioned normalized blocks, and bounded warnings.
8. Project only `indexed` content to one FTS row keyed as `atlassian_item` plus stable External Resource ID. Reference/metadata coverage removes or omits that projection. Rebuild is deterministic from relational state.
   - reference rejects remote metadata/body persistence; metadata rejects bodies
   - an explicit indexed-to-metadata/reference downgrade removes stored content and FTS, while refresh failure never does
9. Update all owner documents, schema subjects/counts/ERDs, cleanup decisions, and synthetic tests.

## Out-Of-Scope Behavior

- Live company Atlassian reads, credentials, Gateway dispatch, runner execution, or model invocation.
- Session/Local Context URL extraction and evidence rows owned by FEAT-0047.
- Space registration UI and inventory owned by FEAT-0048.
- Refresh preview, progress, or result orchestration owned by FEAT-0049.
- Browse/detail/search presentation, notes, Topics, and Tags owned by FEAT-0050.
- Comments, attachments, remote history, automatic polling, background refresh, retries, migration inference, cross-domain merge, or destructive remote actions.

## Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/workstreams.py`
- a new `src/localbrain/atlassian.py`
- `src/localbrain/queries.py` and retrieval consumer guards as required
- focused Atlassian, migration, search, schema, and data-model tests
- Atlassian and existing Resource/retrieval owner documents
- generated schema presentation and cleanup audit artifacts

## Surface Lanes

- Identity and compatible upgrade:
  - path roots: schema, database startup/migration, Workstream Resource creation
  - dependency order: first
  - implementation responsibility: exact cardinality, scoped uniqueness, lifecycle, backup, preservation, fail-closed repair
  - validation evidence: fresh and upgraded SQLite, repeated startup, duplicate URL compatibility, exact row/link snapshots, FK/integrity checks
- Remote ownership and freshness:
  - path roots: Atlassian domain APIs and focused tests
  - dependency order: after identity
  - implementation responsibility: Site/Space/Item registration, stub binding, collisions, metadata allowlist, retained state, derived freshness
  - validation evidence: cross-instance/site duplicates, alias transitions, outcome matrix, deterministic clocks
- Content normalization and FTS:
  - path roots: Atlassian normalization/projection, FTS/query consumers
  - dependency order: after identity and remote ownership
  - implementation responsibility: safe deterministic normalization, source/content hashes, coverage gating, no-change suppression, rebuild
  - validation evidence: ADF/HTML/Markdown/plain fixtures, unsafe HTML, hash idempotency, changed replacement, retention, FTS queries/rebuild
- Durable docs and generated schema:
  - path roots: data-model owners, architecture/privacy references, schema presentation and audit
  - dependency order: after behavior stabilizes
  - implementation responsibility: one canonical contract and deterministic generated consumers
  - validation evidence: doc map/counts, generated parity, privacy, Mermaid, links, diff checks

## State And Interaction Contract

- Stub: External Resource and Atlassian Item exist from a valid HTTP(S) URL; remote ID may be absent.
- Confirmed: one remote ID has been bound inside the Item's Source Instance/Site/service boundary without changing the local ID.
- Reference or metadata: no FTS body is retained.
- Indexed: current stored body has one matching FTS projection.
- Unknown/current/due/stale/unavailable: derived independently of coverage and attention.
- Collision: any normalized URL or confirmed remote-identity conflict aborts before mutation; no merge winner is inferred.
- Purge: the explicit source-specific purge API removes its FTS row and polymorphic Workstream, Thread, and checkpoint references before deleting the stable Resource and cascading extensions; Source Instance or Site deletion is restricted while descendants exist.

## Data And Contract Assumptions

- `atlassian_items.external_resource_id` is both primary key and `ON DELETE CASCADE` foreign key to `external_resources.id`; there is no second Item ID.
- Site uniqueness is `(source_instance_id, normalized_domain)` and optional remote Site identity is unique within its Source Instance.
- Confirmed Item uniqueness is `(site_id, service, remote_id)`. URL identity is `(site_id, normalized_url)` before confirmation and remains an alias guard afterward.
- Space is optional for an Item. Space identity is remote-ID or stable key scoped to Site and service.
- External Resource `url` remains a useful local/display URL but is not a global identity constraint. Atlassian canonical and observed URLs are owned by `atlassian_item_urls`.
- Remote metadata is bounded JSON without Jira description or Confluence body. Content has its own table and source format.
- Freshness is a pure projection from timestamps, outcomes, known-change, and projection-mismatch facts; no stored freshness label can drift.
- Normalization uses no network, model, active HTML, or external assets. Unknown ADF nodes recurse into known descendants and record bounded warnings.
- FTS source kinds are `atlassian:jira` and `atlassian:confluence`; current work suggestion retrieval continues to exclude Atlassian rows until a downstream product Feature owns that behavior.

## Contract Surfaces

- Producer expectations:
  - callers supply stable Source Instance/Site identity, an actual HTTP(S) URL, bounded remote identifiers, and validated FEAT-0045 target outcomes
  - content source format matches the Item service and contains no unvalidated provider envelope
- Consumer expectations:
  - all existing Resource relations continue using `entity_type = external` and the unchanged numeric ID
  - current Session/Document search presentation keeps filtering to its supported entity types; FEAT-0050 can expose the stable `atlassian_item` FTS row without changing its identity
  - FEAT-0047 through FEAT-0050 consume public domain APIs rather than writing split tables independently
- Generated artifacts:
  - schema presentation and cleanup audit are regenerated from canonical DDL and owner docs
- Source-of-truth owner:
  - DDL in `schema.sql`; migration in `db.py`; Item behavior in `atlassian.py`; semantics in the Atlassian source-memory data-model owner
- Stale-assumption check:
  - scan current External Resource upsert, Workstream/Thread/checkpoint links, retrieval filters, FTS rebuild, schema counts/ERDs, backup contracts, and current tests

## Required Evaluators

- Contract:
  - identity/cardinality, source/site containment, uniqueness, migration preservation, ownership/lifecycle, freshness vocabulary, normalization/source preservation, FTS identity, and downstream readiness
- Design:
  - not applicable
- Functional:
  - fresh/upgrade databases, stubs, remote binding, aliases, collisions, cross-boundary duplicates, all outcomes, due clocks, normalization formats, coverage changes, no-change writes, FTS rebuild, deletion, and idempotency
- UX heuristic:
  - not applicable

## Acceptance Mapping

- Stable Resource identity → strict one-to-one Item PK/FK and unchanged polymorphic relation IDs.
- Multi-domain Source Instances → Site table and Source Instance-scoped domain/remote Site constraints.
- Manual stub resolution and aliases → atomic registration/binding APIs and site-scoped normalized URL rows.
- Remote/local separation → remote-state/content tables and no writes to local External Resource fields during result application.
- Due versus stale → pure freshness derivation with approved service intervals and explicit change/projection evidence.
- Retained last-known data → failure paths update only bounded remote-state evidence.
- Safe content and FTS → versioned normalizer, hashes, indexed-only projection, no-change suppression, deterministic rebuild.
- Compatible schema → guarded rebuild, non-overwriting valid backup, exact rows/relations, integrity checks, and repeated-startup tests.

## Evaluation Focus

- Prove that a URL collision or remote-ID collision cannot partially update either Item.
- Prove existing External Resources with the same URL become legal after upgrade without changing IDs or relationships.
- Prove unavailable and not-found results cannot erase a last-known body or search row.
- Prove due is local clock math only and stale requires explicit evidence.
- Prove source bodies are preserved while normalized output is deterministic and unsafe HTML cannot become active content.
- Prove FTS rows have stable identity, correct coverage gating, exact no-change behavior, and deterministic recovery.

## Open Blockers

- None. The owner approved the exact split and execution boundary.

## Continuity Notes

- `2026-07-23`: Spec approved for RUN-20260723-51 after the owner approved strict one-to-one External Resource extension, Site separation, compatible URL migration, and derived freshness.
