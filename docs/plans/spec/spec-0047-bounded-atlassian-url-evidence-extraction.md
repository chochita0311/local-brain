# SPEC-0047: Bounded Atlassian URL Evidence Extraction

## Metadata

- ID: `spec-0047`
- Status: `approved`
- Run ID: `run-20260723-52`
- Attempt: `1`
- Parent Feature: [feat-0047-bounded-atlassian-url-evidence-extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lanes: bounded parsing → source-backed reconciliation → durable ownership
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Source Set

- Human approval: run the remaining Features sequentially using the recommended open-point decisions.
- Parent Feature and PRD: approved FEAT-0047 boundary and approved PRD-0007.
- Dependency truth: FEAT-0046 passed with stable Item identity, configured Site boundaries, and source-specific URL ownership.
- Implementation truth: Claude and Codex parsers, Session classification, incremental source files, enabled Local Context documents, Atlassian stub registration, and current scanner transactions.
- Governing contracts: Privacy And Data Handling, Workspace And Session Activity, Local Context Corpus, Source Registry And Scans, Atlassian Source Memory, and execution-loop governance.

## Implementation Goal

- Extract only configured Atlassian Item URLs from eligible primary work Session text, bounded approved-tool result fields, and changed enabled Local Context documents; reconcile source-backed evidence idempotently without storing excerpts, opaque payloads, or triggering any external/model action.

## In-Scope Behavior

1. Add versioned URL-evidence scan state keyed to exactly one Session or Document and the source fingerprint, extractor version, and configured-Site fingerprint.
2. Add Item evidence rows keyed to one stable Atlassian Item plus exactly one Session or Document source, with:
   - observed and normalized URL
   - `visible_text` or `approved_tool_result` channel
   - Session event ID/source line or Document source line
   - URL occurrence ordinal
   - optional bounded observed remote ID/title from approved result fields
   - observation and reconciliation timestamps
3. Recognize only HTTP(S) Jira issue and Confluence Page URL forms whose domain/service maps unambiguously to an enabled configured Source Instance and Site.
4. Ignore key-only strings, Space-only URLs, unknown domains, ambiguous Source Instance mappings, malformed URLs, repository files, disabled Context roots, maintenance Sessions, and subsessions.
5. Extract visible user/assistant text without changing current Activity Event storage.
6. Inspect only results associated with allowlisted FEAT-0044 Atlassian read tools. Traverse only allowlisted URL, remote-ID, and title field names with bounded depth, node count, text length, and candidate count; do not retain result envelopes or unrelated values.
7. Reconcile a changed eligible source atomically:
   - create or reuse a FEAT-0046 reference stub for each recognized URL
   - upsert current sightings
   - remove prior derived sightings no longer present
   - never delete the Item or any user/remote state when evidence disappears
8. Skip parsing when source, extractor, and configured-Site fingerprints are unchanged; re-evaluate deterministically when any of them changes.
9. Record bounded extraction failures without deleting prior valid evidence.
10. Update canonical data-model owners, generated schema artifacts, privacy notes, and synthetic tests.

## Out-Of-Scope Behavior

- Remote identity validation, metadata/content fetch, freshness update, Gateway dispatch, or model invocation.
- Key-only detection, unresolved placeholders, repository/Git/arbitrary-filesystem scanning, comments, attachments, and full tool-result retention.
- Visible evidence browsing, classification, Workstream Suggestions, or user-facing registration/refresh behavior.
- Binding observed result remote IDs as confirmed remote identity.

## Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/atlassian_evidence.py`
- `src/localbrain/ingest/common.py`
- `src/localbrain/ingest/claude.py`
- `src/localbrain/ingest/codex.py`
- `src/localbrain/ingest/scanner.py`
- parser, evidence, Session-policy, Local Context, schema, and regression tests
- Atlassian, Session, Local Context, source-registry, architecture, privacy, and generated schema owners

## Surface Lanes

- Bounded parsing:
  - path roots: common parser dataclasses and Claude/Codex adapters
  - dependency order: first
  - implementation responsibility: visible text URLs plus approved-tool bounded projection, no opaque persistence
  - validation evidence: synthetic parser/result fixtures, malformed/deep/oversized payloads, unapproved tools
- Source-backed reconciliation:
  - path roots: evidence domain module and scanner hooks
  - dependency order: after parsing
  - implementation responsibility: configured mapping, stable stub reuse, fingerprints, replace-derived lifecycle, failure retention
  - validation evidence: changed/unchanged/removed sources, ambiguous domains, maintenance/subsession exclusion, zero-call guards
- Durable ownership:
  - path roots: DDL, data-model owners, generated presentation/audit
  - dependency order: after behavior stabilizes
  - implementation responsibility: exact cardinality, cascade behavior, canonical counts and diagrams
  - validation evidence: schema constraints, generated parity, privacy, complete regression

## State And Interaction Contract

- Eligible: primary `work` Session or enabled readable Context Document.
- Current scan: source, extractor, and configured-Site fingerprints match; parsing is skipped.
- Changed scan: candidates reconcile atomically and obsolete evidence rows are removed.
- No match: scan state advances with zero evidence and no placeholder.
- Unsupported or ambiguous: candidate is ignored; no Item/evidence/lookup is created.
- Error: bounded failure state advances only when safe and prior valid evidence remains.
- Removed evidence: only the derived sighting disappears; stable Item, remote state, content, and local organization remain.

## Data And Contract Assumptions

- Evidence references `atlassian_items.external_resource_id`; the stable Item ID remains the External Resource ID.
- Scan and evidence rows use explicit nullable Session/Document foreign keys with an exactly-one-source check rather than a polymorphic unvalidated identifier.
- Session source fingerprints derive from the imported source-file size/mtime plus parser contract; Document fingerprints derive from `content_hash`.
- The configured-Site fingerprint derives only from enabled Source Instance/Site/service identity and causes local re-evaluation without remote access.
- Source locations contain identifiers and numeric line/occurrence values only; no excerpt column exists.
- Observed remote ID/title are evidence facts only and never confirm Item identity or overwrite local Resource fields.

## Contract Surfaces

- Producer expectations: parsers emit bounded ephemeral candidates; scanner supplies eligible source identity/fingerprint.
- Consumer expectations: FEAT-0050 may navigate evidence to its Session event or Document line, while FEAT-0049 must not treat evidence as freshness or refresh success.
- Generated artifacts: schema presentation and cleanup audit follow canonical DDL.
- Source-of-truth owner: DDL in `schema.sql`, extraction/reconciliation in `atlassian_evidence.py`, parser shape in `ingest/common.py`, orchestration in `ingest/scanner.py`.
- Stale-assumption check: ingestion skip rules, maintenance/subsession classification, Context removal/cascade behavior, schema consumers, and privacy docs.

## Required Evaluators

- Contract: bounded fields, source eligibility, cardinality, fingerprints, Site mapping, ownership separation, no external/model side effects.
- Design: not applicable.
- Functional: visible/tool-result URLs, key-only, unknown/ambiguous domains, duplicate/alias, changed/removed/error sources, maintenance/subsession, extractor/Site-version re-evaluation, idempotency.
- UX heuristic: not applicable.

## Acceptance Mapping

- URL-only configured discovery → strict recognizer plus enabled Site mapping.
- Bounded source fields → ephemeral candidate model and allowlisted result walker.
- Incremental behavior → versioned source and configured-Site scan fingerprints.
- Stable reuse → FEAT-0046 stub API and Item-keyed evidence.
- Provenance without excerpts → explicit source FKs and location/occurrence fields only.
- No feedback loop → eligibility guard excludes maintenance and subsession records before reconciliation.
- Derived lifecycle → atomic replace-per-source evidence with Item retention.

## Evaluation Focus

- Prove unapproved or opaque tool result fields cannot become evidence.
- Prove a key-like string and Space URL produce no row.
- Prove maintenance output and subsession text cannot rediscover an Item.
- Prove an unchanged source performs no reparse while an extractor/Site fingerprint change does.
- Prove removed evidence does not delete or modify stable Item/local/remote state.
- Prove all extraction paths perform zero external and zero model calls.

## Open Blockers

- None. The owner approved identifier/line/occurrence-only source locations and sequential execution.

## Continuity Notes

- `2026-07-23`: Spec approved for RUN-20260723-52 with the recommended bounded-location decision.
