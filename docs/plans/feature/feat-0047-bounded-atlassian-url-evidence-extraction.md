# FEAT-0047: Bounded Atlassian URL Evidence Extraction

## Metadata

- ID: `feat-0047`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal

- Establish one incremental, URL-only evidence extraction contract for eligible work Sessions and Local Context documents without retaining opaque tool payloads, contacting Atlassian, or allowing maintenance output to rediscover itself.

## Acceptance Contract

- Only actual HTTP or HTTPS URLs recognized as belonging to a configured Atlassian Source Instance can create or attach evidence.
- A key-shaped string without a URL creates no Item, stub, unresolved evidence, or lookup request.
- Eligible Session evidence comes from visible user and assistant text plus an explicit allowlist of bounded fields such as URL, remote ID, and title from approved MCP results.
- Opaque tool arguments, tool-result bodies, comments, attachments, command output, and unrelated structured fields are not copied or indexed.
- Only eligible primary work Sessions participate. Maintenance Sessions, subsessions, maintenance artifacts, and maintenance structured results remain excluded.
- Local Context extraction scans changed enabled readable documents and retains the owning Document relation without copying its text into remote Item content.
- Repository code and unregistered filesystem paths are not scanned.
- Extraction uses source-file or document fingerprints so unchanged inputs are not reparsed.
- A repeated URL attaches an idempotent evidence sighting to the existing FEAT-0046 stable Resource rather than creating a duplicate.
- Observed URL, owning source identity, bounded location or event identity, and observed time are retained separately from Canonical URL and remote content.
- Discovery performs no external call, LLM call, content coverage upgrade, classification, Workstream mutation, or freshness update.
- Removal or change of source evidence does not delete user-managed Item state or remote content; evidence reconciliation follows an explicit derived-data lifecycle.

## Scope Boundary

- In:
  - URL recognition for configured Atlassian Source Instances
  - primary work Session user and assistant text
  - allowlisted bounded MCP-result fields
  - enabled readable Local Context documents
  - changed-input fingerprints and incremental reconciliation
  - observed URL and source provenance
  - idempotent FEAT-0046 Resource reuse
  - maintenance and subsession exclusion
- Out:
  - key-only detection or unresolved evidence
  - repository scanner, Git history scanner, or arbitrary filesystem search
  - opaque tool payload persistence
  - remote identity resolution, metadata, content, or refresh
  - Topic, Tag, summary, classification, or Workstream Suggestions
  - deleting user-managed Resources when evidence disappears
  - visible evidence browsing owned by FEAT-0050

## Surface Lanes

- Session extraction lane:
  - path roots: `src/localbrain/ingest/common.py`, Claude and Codex adapters, scanner reconciliation, and parser tests
  - dependencies: FEAT-0046 stable identity and evidence shape
  - expected evidence: eligible text and allowlisted projection extraction, maintenance/subsession exclusion, and no opaque payload retention
  - evaluator ownership: `contract`, `functional`
- Local Context extraction lane:
  - path roots: Local Context scan and document ingestion modules plus context tests
  - dependencies: FEAT-0046 stable identity and evidence shape
  - expected evidence: changed readable Document extraction, owning-source provenance, and no repository expansion
  - evaluator ownership: `contract`, `functional`
- Reconciliation lane:
  - path roots: evidence storage, fingerprints, idempotent Resource lookup, stale evidence handling, and synthetic tests
  - dependencies: Session and Local Context lanes
  - expected evidence: repeated sightings deduplicate, changed sources reconcile, and local or remote authority remains untouched
  - evaluator ownership: `functional`

## Contract Surfaces

- Eligible source and Session-class policy.
- URL recognizer and Source Instance mapping.
- Allowlisted MCP-result projection.
- Evidence identity, provenance, and derived lifecycle.
- Source fingerprint and incremental-scan version.
- Stable Resource lookup and duplicate behavior.
- Exclusion from remote content, freshness, classification, and organization.

## Required Evaluators

- `contract`: source eligibility, bounded extraction, evidence ownership, fingerprint versioning, exclusion rules, and FEAT-0046 consumer boundary.
- `functional`: valid URL, key-only, duplicate, alias, changed Session, changed Document, opaque payload, maintenance, subsession, malformed input, disabled source, and removed evidence fixtures.

## Entry And Exit

- Entry point: an eligible Session source file or enabled Local Context document has a changed fingerprint under the active extraction contract.
- Exit or transition behavior: zero or more derived evidence sightings attach idempotently to stable Resources without external access or user-organization changes.

## State Expectations

- Default: changed eligible content is scanned once under the current extractor version.
- No match: no evidence or unresolved placeholder is created.
- Duplicate: the existing Item receives or retains one source-specific sighting.
- Unsupported: unknown domains and non-URL identifiers remain untouched.
- Error: one malformed source records bounded scan failure without deleting prior valid evidence.
- Success: evidence can lead back to the owning Session or Document and remains separate from remote content.

## Dependencies

- FEAT-0046 must be `passed`.
- Existing Session class, role, index policy, source-file fingerprint, and Local Context source eligibility contracts remain authoritative.

## Likely Affected Surfaces

- `src/localbrain/ingest/common.py`
- `src/localbrain/ingest/claude.py`
- `src/localbrain/ingest/codex.py`
- `src/localbrain/ingest/scanner.py`
- Local Context scanning modules under `src/localbrain/`
- FEAT-0046 Atlassian evidence storage
- parser, ingestion policy, Session contract, Local Context, privacy, and idempotency tests
- `docs/policies/project/architecture.md`
- `docs/policies/project/data-model/workspace-and-session-activity.md`
- `docs/policies/project/data-model/local-context-corpus.md`
- Atlassian data-model owner documentation

## Pass Or Fail Checks

- Pass if valid configured Atlassian URLs from eligible Session text and Local Context documents attach evidence once.
- Pass if key-only strings, unknown domains, opaque payload fields, maintenance, subsession, and repository files produce no Item or evidence.
- Pass if the bounded MCP projection cannot retain an entire tool result or unrelated sensitive fields.
- Pass if unchanged inputs are skipped and extractor-version changes re-evaluate deterministically.
- Pass if repeated, changed, removed, malformed, and partial source states preserve stable Resource and user-managed fields.
- Pass if extraction performs zero external and zero model calls.
- Fail on feedback loops, remote-content contamination, duplicate Resources, key-only stubs, broad payload retention, or silent organization mutation.

## Regression Surfaces

- Claude and Codex primary/subsession/maintenance classification.
- Existing Session Activity Event and FTS eligibility.
- Local Context source health and document indexing.
- Scanner idempotency, source-file fingerprints, and privacy-safe failures.
- Existing External Resource and Workstream relations.

## Harness Trace

- Active spec doc: [SPEC-0047](../spec/spec-0047-bounded-atlassian-url-evidence-extraction.md)
- Active run: [RUN-20260723-52](../run/run-20260723-52-bounded-atlassian-url-evidence-extraction.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [Contract — PASS](../evaluation/eval-0047-contract-bounded-atlassian-url-evidence-extraction.md), [Functional — PASS](../evaluation/eval-0047-functional-bounded-atlassian-url-evidence-extraction.md)
- Latest fix note: [Session source-file evidence cardinality](../fix/fix-0047-session-source-file-evidence-cardinality.md)

## Open Review Decisions

- None. The owner approved the recommended source-location contract: retain only the owning Session event or Document line/anchor plus URL occurrence identity, never an excerpt or opaque result body.

## Continuity Notes

- `2026-07-23`: initial draft fixed URL-only, changed-input, source-backed evidence extraction and explicitly excluded key-only placeholders, repository scanning, opaque tool payloads, maintenance feedback loops, and remote access.
- `2026-07-23`: the owner approved the recommended bounded location marker and requested sequential execution of every remaining PRD-0007 Feature. FEAT-0047 entered RUN-20260723-52 first.
- `2026-07-23`: Attempt 1 found one multi-file Session scan-cardinality implementation bug. FIX-0047 made Session evidence source-path-aware; Attempt 2 passed Contract and Functional evaluation with eight focused tests and the complete 233-test suite.
