# EVAL-0046: Atlassian Source Item Identity And Freshness Contract — Contract

## Metadata

- ID: `eval-0046-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260723-51`
- Attempt: `1`
- Feature: [feat-0046-atlassian-source-item-identity-and-freshness-contract](../feature/feat-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Spec: [spec-0046-atlassian-source-item-identity-and-freshness-contract](../spec/spec-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: identity and compatible upgrade → remote ownership and freshness → content normalization and FTS → durable docs and generated schema
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated stable identity/cardinality, Source Instance/Site/Space containment, URL and remote uniqueness, manual-stub reuse, migration preservation, remote/local/content ownership, coverage and attention, derived freshness, retained failure state, deterministic normalization, FTS lifecycle, purge, schema ownership, and downstream readiness.

## Checks And Evidence

- `atlassian_items.external_resource_id` is both primary key and cascading FK to `external_resources.id`. No second local Item ID exists, and every Workstream, Thread, and checkpoint relation continues addressing the unchanged External Resource ID.
- The exact source-specific split is present: Sites own Source Instance/domain identity, Spaces own optional containment, Items own strict binding and local axes, URL rows own canonical/alias identity, remote-state owns metadata/check evidence, and content owns source body/normalization/hash/projection state.
- One Source Instance can own several domain-scoped Sites. Confirmed remote IDs and keys are unique per Site/service; the same values on different Sites or Source Instances remain distinct. Source Instance and Site deletion are restricted while descendants exist.
- URL normalization requires HTTP(S), rejects embedded credentials, removes fragments/default ports/trailing non-root slash, normalizes IDNA host/query ordering, and keeps the exact observed spelling separately. One normalized URL is unique inside its Site and one partial unique index permits only one canonical URL per Item.
- A single matching unbound manual External Resource is reused automatically. Ambiguous manual matches, canonical URL conflicts, remote ID/key conflicts, wrong-Site Spaces, and Source/Site mismatches abort their savepoint before identity or URL mutation.
- The global `external_resources.url UNIQUE` constraint is removed only through a preflighted backup-backed rebuild. The repair refuses unexpected columns, explicit indexes, triggers, uniqueness, or a coexisting target; it exact-compares rows and every External Resource Workstream/Thread/checkpoint relation, restores FK enforcement, and is idempotent.
- External Resource title, summary, source role, locator, and relations remain local-owned. Remote metadata is canonical bounded JSON, incrementally merges partial observations, rejects Jira description/Confluence body recursively, and cannot overwrite content or local fields.
- Coverage and attention are independent. Reference rejects metadata/body persistence; metadata rejects bodies; indexed admits eligible bodies and FTS. Explicit downgrade is the destructive content action and removes stored body/FTS, while failed refresh never downgrades or purges.
- Freshness is derived, not stored: latest failure is unavailable; explicit change/projection mismatch is stale; no success is unknown; Jira becomes due at seven days and Confluence at 30 days; otherwise current. Due performs no I/O and does not assert change.
- Failure/not-found/unavailable application updates only bounded check evidence, requires a non-empty error code of at most 80 characters, and retains last-known metadata, content, URLs, FTS, and local organization.
- Jira ADF and Confluence ADF/HTML/Markdown/plain bodies are source-preserving and normalize through versioned deterministic local code. Active HTML is omitted from normalized text, unknown ADF nodes retain known descendants with bounded warnings, and no normalizer path uses a network or model.
- FTS admits exactly indexed Items with stored normalized content under `entity_type = atlassian_item` and the stable External Resource ID. Source/projection hashes suppress unchanged content and FTS writes; rebuild is deterministic. Existing Session/Document search and work-retrieval consumers explicitly filter their supported types until FEAT-0050.
- Explicit Item purge removes its FTS row and polymorphic Workstream/Thread/checkpoint relations before deleting the External Resource and cascading source-specific rows. Ordinary synchronization has no deletion path.
- Durable owners and generated schema agree on 29 ordinary tables, one FTS5 object, 31 physical relations, 29 explicit indexes, 334 columns, 24 application relations, and nine subjects.

## Evidence

- Source inspection covered `schema.sql`, `db.py`, `atlassian.py`, External Resource registration, search/retrieval filters, owner policies, generated presentation, cleanup audit, and synthetic tests.
- Environments checked: fresh in-memory SQLite, compatible in-memory repair, compatible file-backed startup with non-overwriting validated backup, deterministic clock inputs, synthetic Jira/Confluence bodies, and generated schema consumers.

## Evidence Gaps

- None for the approved local foundation boundary.
- No company content, live Gateway read, paid model invocation, registration UI, refresh UI, URL evidence extraction, or Atlassian browse/search presentation was exercised. Those are explicitly owned by FEAT-0047 through FEAT-0050.

## Findings

- None remaining.

## Regression Notes

- Generic External Resource registration retains exact-URL reuse by application policy after removal of the database-global uniqueness constraint.
- Existing Workstream suggestion retrieval and visible global search remain Session/Document-only; the new Atlassian FTS row is ready for its downstream product consumer without becoming an accidental current result.

## Route

- Next action: `pass` and run Functional evaluation.
