# FEAT-0046: Atlassian Source Item Identity And Freshness Contract

## Metadata

- ID: `feat-0046`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal

- Establish a stable, source-specific Atlassian identity, ownership, freshness, retention, and search-projection contract that enriches existing External Resources without duplicating or severing user-managed relationships.

## Acceptance Contract

- An existing or newly created `external_resources.id` remains the stable linkable local Resource identity for Workstream, Thread, checkpoint, note, attention, Topic, and Tag relations.
- Atlassian Source Instance, service, Site, remote ID, Jira key or Page ID, Canonical URL, URL aliases, remote metadata, remote content, and evidence have explicit ownership and lifecycle boundaries.
- `atlassian_items.external_resource_id` is both the Atlassian Item primary key and a cascading foreign key to `external_resources.id`. No second local Item identifier exists, and one External Resource can have at most one Atlassian Item extension.
- `atlassian_sites`, `atlassian_spaces`, `atlassian_items`, `atlassian_item_urls`, `atlassian_item_remote_state`, and `atlassian_item_content` own separate identity, containment, URL, remote-fact, and body-projection concerns.
- `atlassian_sites` is a distinct domain or tenant identity layer below Source Instance. One Source Instance may expose multiple Sites; each Site has a normalized domain and may later bind a provider remote Site ID without changing its stable local ID.
- Jira and Confluence Spaces and Items reference one Site. Confirmed remote uniqueness uses Source Instance plus Site plus service plus remote ID. Before resolution, local reuse uses Source Instance plus normalized Site domain plus Canonical URL.
- The current global `external_resources.url UNIQUE` constraint is removed through a guarded compatible migration. Existing Resource IDs and relations remain unchanged; non-Atlassian URL reuse remains application-owned, while Atlassian URL uniqueness is enforced only within one Source Instance.
- The same key on different Source Instances or Sites remains distinct. Separately connected old and new domains are never merged or treated as migration stages.
- A manual URL stub can bind to a confirmed remote Item without changing its stable External Resource ID or losing existing links and local fields.
- Remote metadata excludes Jira description and Confluence body. Remote content is separately versioned, hashed, timestamped, and eligible for FTS only under `indexed` coverage.
- Coverage (`reference`, `metadata`, `indexed`), attention (`normal`, `pinned`, `ignored`, `archived`), and organization remain independent axes.
- Freshness uses `unknown`, `current`, `due`, `stale`, and `unavailable` independently from coverage and attention. `due` is only an age-based advisory recheck state and never proves remote change; `stale` requires evidence that the remote state changed or the applied local projection no longer matches confirmed remote state.
- The initial due policy is seven days after the last successful Jira check and 30 days after the last successful Confluence check. Reaching due performs no remote or model call and only affects local preview defaults.
- Last attempted check, last successful check, last confirmed remote version or timestamp, and last content-applied time remain distinguishable.
- Successful no-change checks do not rewrite unchanged content or FTS rows.
- Changed content is applied only after identity, coverage, version or timestamp, and content-hash validation.
- Unavailable, permission, authentication, deletion, not-found, and partial failure retain last-known remote state and every user-managed relation until an explicit destructive local action.
- Session and Local Context evidence is source-separated from remote content and can be rebuilt without rewriting user-managed fields.
- Jira ADF and supported Confluence body formats normalize into safe source-preserving local content and deterministic FTS text without making rendered output source authority.
- Fresh and upgraded databases preserve all existing External Resource IDs, Workstream/Thread/checkpoint relations, notes, and accepted organization.

## Scope Boundary

- In:
  - stable External Resource binding
  - compatible removal of global External Resource URL uniqueness
  - Source Instance, service, Site, Space, and remote Item identity
  - Canonical URL and alias ownership
  - remote metadata versus remote content
  - independent coverage, attention, organization, and freshness axes
  - check, version, content-applied, and hash timestamps
  - last-known retention and explicit purge boundary
  - Jira and Confluence content normalization contract
  - FTS eligibility and idempotent projection
  - compatible schema evolution and exact relationship preservation
- Out:
  - external provider capability and allowlist owned by FEAT-0044
  - maintenance Run execution owned by FEAT-0045
  - Session and Document URL extraction owned by FEAT-0047
  - Space registration UI owned by FEAT-0048
  - refresh preview and result application workflow owned by FEAT-0049
  - Topic and Tag user experience owned by FEAT-0050
  - old/new migration inference or cross-domain merge
  - comments, attachments, blogs, whiteboards, databases, and remote revision-history bodies

## Surface Lanes

- Identity and ownership lane:
  - path roots: `src/localbrain/schema.sql`, `src/localbrain/db.py`, resource and Atlassian domain modules, and data-model owner docs
  - dependencies: PRD-0007 and FEAT-0044 Source Instance contract
  - expected evidence: uniqueness, cardinality, lifecycle, source-of-truth ownership, and no cross-instance merge
  - evaluator ownership: `contract`
- Upgrade and preservation lane:
  - path roots: compatible schema upgrade, backups when structural repair requires them, and synthetic legacy fixtures
  - dependencies: identity and ownership lane
  - expected evidence: exact External Resource IDs and relationship preservation, fail-closed collisions, foreign-key and integrity checks, and idempotent startup
  - evaluator ownership: `contract`, `functional`
- Content and projection lane:
  - path roots: body normalization, content hashes, freshness derivation, FTS projection, and query tests
  - dependencies: identity and ownership lane plus FEAT-0045 result contract
  - expected evidence: metadata/content separation, safe normalization, no-change writes suppressed, stale retention, and deterministic rebuild
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- Stable External Resource to Atlassian Source Item binding.
- Source Instance and confirmed remote uniqueness.
- Canonical URL and alias rules.
- Remote metadata, content, local organization, and evidence ownership.
- Coverage, attention, and freshness vocabularies.
- Check, content-applied, remote version/timestamp, and hash fields.
- Jira ADF and Confluence body normalization.
- FTS row identity, eligibility, replacement, and rebuild.
- Compatible upgrade, collision, backup, and recovery behavior.

## Required Evaluators

- `contract`: identity, ownership, lifecycle, uniqueness, value vocabularies, upgrade preservation, FTS projection, and consumer readiness.
- `functional`: manual-stub resolution, aliases, cross-instance duplicate keys, no-change and changed content, stale/unavailable retention, collision refusal, normalization, FTS rebuild, and idempotency.

## Entry And Exit

- Entry point: a manual or discovered URL creates or resolves a stable local Resource, or a validated FEAT-0045 result targets an existing binding.
- Exit or transition behavior: the contract returns one stable local Item state and updates only eligible remote projections without changing user-managed identity or organization.

## State Expectations

- Reference: local URL identity exists without implying remote validation.
- Metadata: confirmed remote fields exist without a stored body.
- Indexed: eligible remote body and matching FTS projection exist.
- Unknown or due: local state remains usable while a check is absent or its advisory interval has elapsed; due alone never marks the content outdated.
- Stale: a known remote change or local projection mismatch exists; last-known state remains readable until validated replacement succeeds.
- Unavailable: the latest explicit check could not establish remote state; last-known state remains readable with the bounded failure reason.
- Collision: ambiguous duplicate resolution stops before merge and requires later review.
- Success: all consumers resolve the same stable Resource and source-specific binding.

## Dependencies

- FEAT-0044 must be `passed`.
- FEAT-0045 must define the structured result consumed by this contract before its content-application lane enters build.
- Existing Workstream, Thread, checkpoint, External Resource, FTS, and data-recovery policies remain regression contracts.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/workstreams.py`
- `src/localbrain/retrieval.py`
- `src/localbrain/queries.py`
- a source-specific Atlassian domain or normalization module under `src/localbrain/`
- schema-upgrade, Workstream, retrieval, search, and normalization tests
- `docs/policies/project/data-model.md`
- `docs/policies/project/data-model/work-organization-and-resources.md`
- a new Atlassian source data-model owner document when required
- `docs/policies/project/architecture.md`
- generated Schema presentation inputs and outputs when the schema changes

## Pass Or Fail Checks

- Pass if one manual Resource resolves to one confirmed binding without changing its ID or any relation.
- Pass if the compatible migration removes only global URL uniqueness, preserves every existing External Resource ID and relation, and replaces Atlassian deduplication with Source Instance-scoped normalized URL identity.
- Pass if one Source Instance can retain multiple domain-scoped Sites, identical keys or remote IDs on different Sites remain distinct, and Site binding never merges domains.
- Pass if identical keys across Source Instances remain distinct and no migration relation is inferred.
- Pass if Canonical URLs and aliases deduplicate only inside the confirmed Source Instance boundary.
- Pass if remote metadata, remote content, local organization, and evidence cannot overwrite one another.
- Pass if no-change checks suppress content and FTS writes and changed hashes replace exactly one eligible projection.
- Pass if unavailable and not-found outcomes retain last-known state and local organization.
- Pass if safe Jira and Confluence normalization is deterministic and source-preserving.
- Pass if fresh and upgraded schema paths preserve every existing Resource and relation and reject ambiguous collisions before mutation.
- Fail on Resource duplication, cross-instance merge, local-field overwrite, stale-state erasure, unsafe body handling, FTS/source divergence, or relationship loss.

## Regression Surfaces

- Existing manual Jira, Wiki, Slack, Git, document, and URL External Resources.
- Workstream and Thread polymorphic links.
- Checkpoint resource snapshots and retrieval manifests.
- Search rebuild and source-backed result resolution.
- Database backup, schema presentation, and privacy contracts.

## Harness Trace

- Active spec doc: [SPEC-0046](../spec/spec-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Active run: [RUN-20260723-51](../run/run-20260723-51-atlassian-source-item-identity-and-freshness-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [Contract — PASS](../evaluation/eval-0046-contract-atlassian-source-item-identity-and-freshness-contract.md), [Functional — PASS](../evaluation/eval-0046-functional-atlassian-source-item-identity-and-freshness-contract.md)
- Latest fix note: not created

## Open Review Decisions

- None. The owner approved the exact table split, strict one-to-one External Resource extension, Site layer, scoped URL identity, and freshness defaults before SPEC-0046 entered execution.

## Continuity Notes

- `2026-07-23`: initial draft fixed stable External Resource ownership, separate Source Instances, remote/local/evidence boundaries, last-known retention, and hash-gated search projection before any visible Atlassian workflow.
- `2026-07-23`: the owner approved removing global `external_resources.url` uniqueness through a relationship-preserving compatible migration and moving Atlassian URL deduplication into the Source Instance boundary.
- `2026-07-23`: the owner fixed `due` as an advisory age state distinct from evidence-backed `stale`, with Jira at seven days and Confluence at 30 days, and approved a distinct Site domain layer so one Source Instance can represent multiple global-company Sites.
- `2026-07-23`: the owner approved a strict one-to-one `external_resources.id` to `atlassian_items.external_resource_id` extension and requested execution. The Orchestrator routed the approved Feature to SPEC-0046 and RUN-20260723-51.
- `2026-07-23`: Attempt 1 passed Contract and Functional evaluation with 21 focused Atlassian tests, the complete 225-test suite, relationship-preserving file upgrade evidence, deterministic generated schema, and no live company or model call.
