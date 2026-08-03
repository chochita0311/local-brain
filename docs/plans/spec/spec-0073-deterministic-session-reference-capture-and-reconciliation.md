# SPEC-0073: Deterministic Session Reference Capture And Reconciliation

## Metadata

- ID: `spec-0073`
- Status: `approved`
- Run ID: `run-20260803-83`
- Attempt: `1`
- Parent Feature: [feat-0073-deterministic-session-reference-capture-and-reconciliation](../feature/feat-0073-deterministic-session-reference-capture-and-reconciliation.md)
- Parent PRD: [prd-0013-session-centric-related-context-evidence](../prd/prd-0013-session-centric-related-context-evidence.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Surface Lanes: provider extraction → target resolution → reconciliation → read projection
- Required Evaluators: `contract`, `functional`
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Source Set

- Human-approved PRD-0013 decisions and passed FEAT-0072 persistence contract.
- Current Claude/Codex parsers, multi-source scanner, source-file freshness,
  configured Atlassian recognition, Local Context Document identity, and legacy
  Atlassian URL evidence behavior.
- Relevant policies: Agent Workflow, Foundation Contract, Architecture, Privacy,
  Workspace/Session Activity, Source Registry And Scans, Local Context Corpus,
  and Atlassian Source Memory.

## Implementation Goal

- Normalize direct primary Session references once during synchronization and
  expose a bounded database projection without source-file parsing at detail-read
  time.

## Lane Order And Handoffs

1. Provider extraction produces source-neutral ephemeral candidates with native
   event/call identity and no opaque payload retention.
2. Resolver converts safe URLs, exact Markdown references, and configured
   Atlassian reads into FEAT-0072 targets or rejects ambiguity.
3. Reconciler replaces derived evidence by contributing source path, enforces one
   100-target Session set, and records aggregate complete/partial/error state.
4. Read projection groups one row per target with deterministic evidence counts,
   labels, order inputs, totals, and partial/stale state for FEAT-0074.

## In-Scope Behavior

- Claude and Codex share `ParsedReferenceCandidate`; source key remains separate
  through the Session's existing Source ID while provider-specific shapes retain
  native event and tool-call identity.
- Visible user/assistant text yields safe HTTP(S) and explicit `*.md` candidates.
  Approved result containers yield only allowlisted URL identities.
- Approved Atlassian calls are correlated to matching completed results. Explicit
  non-error completion yields `success`; explicit error completion yields
  `failure`; missing, malformed, or unmatched output yields neither.
- A resource-read target comes only from an approved safe result URL or bounded
  direct call URL/Jira-key/Confluence-page-ID that resolves to a configured local
  Item. Unknown tools, arbitrary JQL/text, and key-only discovery create no target.
- Generic URLs keep only normalized HTTP(S) scheme, host/port, and path; userinfo,
  fragments, and query are removed. Atlassian adapters retain only their approved
  canonical identity query fields.
- Absolute Markdown paths resolve by exact enabled Document path. Relative paths
  resolve exactly against Session cwd. Bare filenames resolve only when exactly
  one enabled Document in the Session workspace has that basename.
- `source_files.session_id` and `reference_contract_version` preserve file-to-
  Session ownership and drive version repair. Initial upgrade reparses current
  Session files once; later syncs parse changed files, plus current siblings only
  when the aggregate state was partial/error and exact reconstruction is needed.
- Reconciliation retains at most 100 unique targets and at most 50 normalized
  evidence locations per retained target. Stronger read/result evidence selects
  the retained subset before visible mentions; deterministic fingerprints prevent
  replay or repeat scans from inflating rows.
- Successful reconciliation removes obsolete evidence for current contributing
  source paths. Missing accepted source deletion cascades through Session cleanup;
  unavailable/configuration/failed source scans retain prior evidence.
- Maintenance Sessions and Subsessions clear or produce no generalized reference
  evidence. Legacy Atlassian Session/Document evidence remains operational and
  is not a read-projection authority for the new rail.
- The read projection returns one target per row, success-over-failure read truth,
  evidence-kind counts, safe destination, bounded observed identity, total,
  retained count, and partial/error state without parsing JSONL or message bodies.
- No parser, resolver, reconciler, or read projection performs network, MCP,
  model, embedding, remote refresh, organization mutation, or source-file writes.

## Out-Of-Scope Behavior

- Related rail markup/copy/CSS/disclosure, conversation anchors, Subsession
  roll-up, fuzzy matching, repository-wide scans, arbitrary tool interpretation,
  remote metadata refresh, or new External Resource creation for generic URLs.

## Affected Surfaces

- `src/localbrain/ingest/common.py`, Claude/Codex parsers, and scanner
- new source-neutral Session reference resolver/reconciler/query owner
- `source_files` compatible freshness columns and index
- Data Model, Architecture, Privacy, and generated schema/audit/value artifacts
- parser, resolver, reconciliation, source sync, projection, schema, and privacy tests

## State And Interaction Contract

- Current: source file fingerprint and reference contract match; no reparse.
- Changed/version-old: reconcile the current authoritative candidate set.
- Partial: 100 retained unique targets and a larger observed total.
- Error: prior valid evidence remains; bounded error state is retryable.
- Deleted/removed: only Session-owned derived evidence disappears.
- Unsupported/ambiguous: no relation and no fallback guess.

## Contract Surfaces

- Ephemeral candidate vocabulary and approved tool adapter allowlist.
- Safe URL/Markdown/configured-Item resolution.
- Source-file Session mapping and reference version freshness.
- FEAT-0072 evidence/summary producer and lifecycle semantics.
- Bounded target projection consumed by FEAT-0074.

## Required Evaluators

- Contract: provider equivalence, adapter allowlist, resolver/privacy boundary,
  source-file mapping, persistence, generated owners, and projection shape.
- Functional: success/failure/missing/malformed/unknown cases, exact/ambiguous
  Markdown, counts/dedup/bounds, changed/repeat/version/deletion/error recovery,
  personal/company source isolation, and zero detail-time source parsing.

## Acceptance Mapping

- Provider parity → shared candidate contract with provider fixture coverage.
- Truthful MCP state → call/result identity correlation and explicit error parity.
- Deterministic targets → safe URL and exact Document/configured Item resolvers.
- Bounded/repeatable storage → 100 targets, 50 locations, stable evidence keys.
- Safe lifecycle → source-file mapping/version, atomic per-source reconciliation,
  error retention, Session cascade, and shared target preservation.
- Product readiness → one bounded grouped read projection with no hidden I/O.

## Evaluation Focus

- No false successful read or cross-source/session target ownership.
- No query/fragment/credential, message excerpt, or opaque payload persistence.
- Multi-file Session changes cannot delete unchanged sibling evidence.
- A repeated unchanged scan writes no new evidence and a detail read opens no file.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-03`: Spec Agent selected explicit `source_files` Session mapping and a
  separate reference contract version after inspecting the existing multi-file
  Usage repair contract.
