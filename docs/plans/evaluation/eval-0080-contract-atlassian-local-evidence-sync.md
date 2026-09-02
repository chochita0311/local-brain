# EVAL-0080 Contract: Atlassian Local Evidence Sync

## Metadata

- ID: `eval-0080-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260829-90`
- Attempt: `1`
- Feature: [FEAT-0080](../feature/feat-0080-atlassian-local-evidence-sync.md)
- Spec: [SPEC-0080](../spec/spec-0080-atlassian-local-evidence-sync.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `persisted-source projection; reconciliation; action/report; documentation`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Evaluated persisted Session and Local Context input authority, bounded URL
  recognition and reconciliation, source isolation and idempotency, report and
  receipt contracts, Explorer return continuity, zero-hidden-I/O, and durable
  owner-document parity.

## Checks And Evidence

- Session Sync consumes only the retained FEAT-0073 URL projection for eligible
  primary work Sessions. Missing, stale, error, and partial projection states
  retain honest source outcomes; merge-only reconciliation neither reads raw
  source files nor advances, replaces, or cleans Session-owned scan state.
- Enabled, readable, ready Local Context Documents are read only from persisted
  SQLite bodies in 64-KiB UTF-8 chunks. The complete pass preserves continuous
  source locations, the deterministic first-500 evidence set, exact generic URL
  overflow, changed-source replacement, and read-only repeat behavior while a
  failed or unavailable pass retains prior valid state.
- The configured Site/service and optional unique binding choice are frozen for
  the action. Jira keys and Confluence page IDs are bounded to 300 code points,
  observed and normalized evidence URLs are bounded to 8,000 code points, and
  unsafe, unsupported, unconfigured, ambiguous, and invalid-location candidates
  become fixed skip outcomes instead of database failures.
- Session and Document ID populations are frozen together before processing and
  fetched and processed in batches of 100. A start-existing source deleted
  before its later turn remains an unavailable outcome, while a source inserted
  after the snapshot does not enter the action.
- Each source owns an isolated transaction. Successful peers survive later
  source or action failure, repeated evidence keys and Item IDs retain disjoint
  new/reused accounting, and changed Document observations preserve Item,
  remote, local, classification, organization, and Refresh owners.
- The exact aggregate and fixed per-source report keeps source, Item, evidence,
  candidate-skip, and scope-limit units separate. Process-local single-flight,
  strict zero-input form parsing, canonical pre/post `return_to` validation,
  bounded immutable five-minute receipts, ordinary PRG, and enhanced JSON use
  the same report authority.
- Sync opens only LocalBrain SQLite state and performs no source import, raw
  source or filesystem read, Provider, capability, executor, runner, model,
  connected-discovery, Refresh, or maintenance Run work. Product, Architecture,
  Privacy, Design Constitution, and Atlassian Source Memory own the same action
  separation, persistence, observation, and cleanup boundaries.
- Independent post-build audit passed the 123-test Atlassian evidence, route,
  browse, preview, registration, Refresh, and UI-contract set, JavaScript syntax
  and diff checks, repository privacy scan, and data-model owner and Mermaid
  parity checks.

## Findings

- None.

## Route

- Next action: `pass`
