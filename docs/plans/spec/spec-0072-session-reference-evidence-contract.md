# SPEC-0072: Session Reference Evidence Contract

## Metadata

- ID: `spec-0072`
- Status: `approved`
- Run ID: `run-20260803-82`
- Attempt: `1`
- Parent Feature: [feat-0072-session-reference-evidence-contract](../feature/feat-0072-session-reference-evidence-contract.md)
- Parent PRD: [prd-0013-session-centric-related-context-evidence](../prd/prd-0013-session-centric-related-context-evidence.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: Session reference ownership, persistence, and value contract
- Required Evaluators: `contract`
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Source Set

- Human request: make Related Context describe what the viewed Session mentioned,
  observed, or attempted to read, while excluding ambient same-workspace files.
- Parent PRD and Feature: PRD-0013 and FEAT-0072.
- Golden sources: current Session/Event ownership, Context Document identity,
  External Resource and configured Atlassian Item identity, FEAT-0047 evidence,
  FEAT-0060 Related Context projection, and the effective SQLite model.
- Relevant policies: Agent Workflow, Foundation Contract profile, Architecture,
  Privacy And Data Handling, and Data Model ownership/governance.

## Implementation Goal

- Add one source-neutral, fully derived Session reference contract before parser
  capture or product presentation depends on it.

## In-Scope Behavior

- `session_reference_scans` owns one primary work Session's aggregate reference
  extraction fingerprint, extractor version, bounded counts, current/partial/error
  state, and bounded failure diagnostics.
- `session_reference_evidence` owns one normalized evidence location for a URL,
  exact Context Document, or configured Atlassian Item. It retains no message
  excerpt, opaque tool argument/result, remote content, credential, fragment, or
  unapproved query material.
- Evidence kinds are `user_mention`, `assistant_mention`, `tool_result`, and
  `resource_read`. Only `resource_read` owns `success` or `failure` outcome and a
  completed tool-call identity.
- Target kinds are `url`, `context_document`, and `atlassian_item`. Document and
  Atlassian targets use cascading target FKs; deleting derived evidence never
  deletes those shared targets.
- Stable grouping uses a bounded target key, while Session-facing identity uses
  the bounded observed identity and normalized safe destination. Shared Resource
  titles remain fallback metadata outside this evidence authority.
- One 64-character evidence fingerprint is unique across normalized source
  location, target, evidence kind/outcome, and extractor identity. The scan row
  enforces retained count no larger than observed count or the 100-target cap.
- Session deletion cascades both scan and evidence rows. Compatible startup adds
  both tables and indexes idempotently without rewriting existing user data.
- The Workspace And Session Activity subject owns both new tables; Atlassian
  Source Memory retains its current Session/Document URL-sighting responsibility
  until FEAT-0073 produces the generalized contract.

## Out-Of-Scope Behavior

- Provider parsing, evidence extraction, reconciliation producer code, read
  projection, Related Context query/markup, conversation navigation, Subsession
  roll-up, remote access, or ambient workspace discovery.

## Affected Surfaces

- `src/localbrain/schema.sql`
- Workspace/Session Data Model and global Data Model entry
- value registry and generated dictionaries
- generated Schema presentation and cleanup audit
- schema, migration, documentation, value, and privacy tests

## State And Interaction Contract

- `ok`: reconciliation completed and retained count equals observed count.
- `partial`: reconciliation completed at the 100-target cap and observed count is
  greater than retained count.
- `error`: prior valid evidence may remain stale; bounded code/message explains
  the failed attempt and no completion is implied.
- Mention or observation: no read outcome or completed-read implication.
- Resource read: exactly one completed call identity and either success or failure.
- Unsupported, missing, ambiguous, Maintenance, or Subsession input: no row.

## Data And Contract Assumptions

- A Session's existing `source_id` is the authoritative source-instance identity;
  `source_path`, source event/line, and extractor version preserve producer
  provenance without duplicating mutable provider labels.
- `target_key` is an opaque bounded grouping identity, not presentation copy.
- Generic URL rows store only a normalized safe HTTP(S) destination. Context
  Documents and Atlassian Items remain their own identity/content authorities.
- Error state preserves last-known evidence; successful reconciliation is the
  only authority to replace or delete a source-derived set.

## Contract Surfaces

- Fresh and compatible SQLite tables, checks, foreign keys, indexes, and counts.
- Bounded evidence/target/outcome/status value families and generated registry.
- Producer, consumer, lifecycle, deletion, recovery, privacy, and presentation
  authority in the durable Data Model owner.
- Explicit separation from Activity Events, shared Resources, remote Item memory,
  and user-managed organization links.

## Required Evaluators

- Contract: schema parity, ownership, vocabulary, constraints, lifecycle,
  privacy, generated artifacts, and downstream readiness.
- Design: not required; no visible surface changes.
- Functional: not required for this Foundation contract; FEAT-0073 owns runtime
  behavior.
- UX heuristic: not required.

## Acceptance Mapping

- Source-neutral evidence → two Session-owned derived tables and bounded values.
- Truthful reads → resource-read-only outcome/tool-call parity checks.
- One target row readiness → stable target key plus distinct evidence locations.
- Safe display authority → observed identity and safe destination separated from
  shared Resource title.
- Rebuild/deletion → Session cascade, target-directional FKs, scan state, recovery.
- Downstream determinism → generated schema/value contracts and focused tests.

## Evaluation Focus

- Fresh and compatible databases converge without altering retained rows.
- Invalid target/evidence/outcome/status combinations fail at the schema boundary.
- No field can retain full messages, opaque payloads, or remote content.
- Every new object has exactly one documented owner and generated representation.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-03`: Orchestrator selected one Foundation Contract lane. The owner
  pre-approved dependency-ordered execution through FEAT-0074.
