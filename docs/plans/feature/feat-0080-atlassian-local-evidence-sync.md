# FEAT-0080: Atlassian Local Evidence Sync

## Metadata

- ID: `feat-0080`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Goal

- Give deterministic Atlassian URL evidence already present in LocalBrain
  Sessions and Local Context Documents one explicit local Sync action with
  understandable reconciliation outcomes.

## Acceptance Contract

- The Explorer `Sync` action has no URL, Provider, binding, runner, or remote
  target input. It scans the currently persisted eligible primary work
  Sessions and enabled Local Context Documents.
- Sync does not import or rescan authoritative Claude/Codex JSONL or filesystem
  documents. Existing Session and Local Context source synchronization remains
  the owner of bringing new source content into LocalBrain.
- Eligible recognized Atlassian URLs are reconciled automatically using the
  current configured Site/service and deterministic evidence rules; no
  per-link confirmation is required.
- The action reports effective source scope and distinct `new`, `reused`,
  `skipped`, `unavailable`, and `failed` outcomes with honest totals. A zero
  result is successful completion, not an error.
- Unsupported URLs, key-only text, unknown/unconfigured domains, and unsafe
  locators are candidate skips. Ineligible maintenance/subsession Sessions and
  disabled Documents are source-level excluded outcomes. Both remain bounded
  and visible rather than being silently registered.
- Repeated Sync is idempotent. Existing Item identity, evidence uniqueness,
  local/remote state, classification, organization, and Refresh history are
  preserved.
- Sync retains only exact/normalized URL, eligible source identity/location,
  and bounded title/remote-ID observations already allowed by policy. It never
  copies Session/Document excerpts, prompts, comments, opaque tool payloads,
  credentials, or remote bodies.
- Sync performs no Atlassian/provider, capability, model, embedding, network,
  connected discovery, or Refresh call.
- During Sync the prior Explorer remains readable. Completion refreshes the
  affected hierarchy/list counts without losing approved service, structural,
  query, filter, selection, or scroll state; newly eligible Items are reachable
  through their owned scope.
- Failure is bounded to the local action, retains prior valid evidence and
  inventory, and offers a clear retry. One source failure does not erase
  successful peer outcomes.
- Remote `Refresh` remains separately labeled and retains its current preview,
  access readiness, selection, read budget, and maintenance history.

## Scope Boundary

- In:
  - explicit zero-input local evidence Sync action
  - bounded persisted Session/Document scan orchestration
  - automatic deterministic reconciliation and idempotency
  - source scope, progress, outcome categories, partial failure, and retry
  - Explorer count/list update with state preservation
  - responsive and accessible status/feedback
- Out:
  - Session source or Local Context filesystem synchronization
  - manual URL Add
  - remote Refresh, connected discovery, capability inspection, or new MCP
    operations
  - source-body, prompt, comment, attachment, or opaque payload storage
  - AI/semantic classification or key-only inference
  - Workstream/Thread relationship changes or Suggestions

## Surface Lanes

- Reconciliation service lane:
  - path roots: Atlassian evidence scan/reconciliation services and focused
    source-eligibility/idempotency tests
  - dependencies: current bounded evidence contract and passed FEAT-0075
  - expected evidence: eligible persisted scope, automatic deterministic
    outcomes, bounded storage, idempotency, and zero-hidden-I/O
  - evaluator ownership: `contract`, `functional`
- Action and route lane:
  - path roots: local Sync endpoint/controller, progress/outcome response,
    failure isolation, and route tests
  - dependencies: reconciliation service lane and passed FEAT-0077
  - expected evidence: zero-input start, effective scope, outcome categories,
    partial failure, retry, and Refresh non-execution
  - evaluator ownership: `contract`, `functional`
- Presentation lane:
  - path roots: Explorer Sync action/status region, local JavaScript only when
    needed, semantic-token styles, and browser/UI tests
  - dependencies: action and route lane
  - expected evidence: truthful local label, bounded progress/summary, state
    preservation, focus, responsive feedback, and no-script fallback
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, architecture, privacy, and Atlassian data-model owners
  - dependencies: completed behavior
  - expected evidence: scan/import/Refresh ownership and retained-field parity
  - evaluator ownership: `contract`

## Contract Surfaces

- Persisted Session/Local Context eligibility and scan fingerprint ownership.
- Local Sync request, progress, outcome, partial-failure, and retry shape.
- Evidence and Item reconciliation/idempotency.
- Skipped/unavailable/failure reason categories.
- Explorer list/count refresh and preserved state.
- Zero external/model work and Refresh separation.

## User-Visible Outcome

- The user can press Sync and collect recognized Atlassian links already
  mentioned in synchronized local Sessions and Local Context Documents, see
  what changed or was skipped, and continue browsing without triggering a
  remote read.

## Entry And Exit

- Entry point: activate `Sync` from the Atlassian Explorer or submit its
  server-executable local action.
- Exit or transition behavior: remain in the same Explorer scope with updated
  counts/list and a bounded outcome summary; inspect a reconciled Item, retry a
  whole-scope local Sync, or separately choose Refresh.

## State Expectations

- Default: Sync is available without access configuration and states its local
  persisted-source scope.
- Running: one bounded local progress owner; repeated initiation is prevented
  or receives a bounded busy outcome.
- Success with changes: new/reused/skipped totals and updated inventory are
  visible.
- Success with zero: clear zero-result completion and guidance to use existing
  Session/Context synchronization or manual Add when appropriate.
- Partial: successful source outcomes remain visible beside unavailable or
  failed source outcomes.
- Error: prior inventory/evidence remains, retry is bounded, and raw paths,
  source text, or traces do not leak.
- Narrow: progress and summary remain near the initiating action and do not
  replace the primary link list with a long diagnostic report.

## Dependencies

- FEAT-0075 and FEAT-0077 must be `passed` before this Feature enters build.
- Current bounded Atlassian evidence extraction/reconciliation remains the
  foundation baseline.
- FEAT-0079 passed as the preceding product Feature and remains a regression
  baseline rather than a data dependency.

## Likely Affected Surfaces

- `src/localbrain/atlassian_evidence.py`
- `src/localbrain/main.py`
- current persisted Session/Document evidence readers
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/static/atlassian.js`
- `src/localbrain/static/styles.css`
- evidence/reconciliation/route/UI/browser tests
- product, architecture, privacy, and Atlassian data-model owner docs

## Pass Or Fail Checks

- Pass if eligible synthetic primary Sessions and enabled Local Context
  Documents produce the intended new/reused evidence and Items automatically.
- Pass if key-only, unknown-domain, unsafe, and unsupported candidates are
  skipped, while disabled, maintenance, and subsession sources are excluded,
  with bounded reasons for each observable outcome.
- Pass if a repeated Sync is idempotent and preserves Item identity, evidence,
  local/remote state, organization, and Refresh history.
- Pass if zero, partial, source-failure, and retry states retain valid peer
  outcomes and prior inventory.
- Pass if Explorer scope/query/filter/selection/scroll remain stable and
  synthetic `1440`, `920`, `700`, and `320` feedback is contained, accessible,
  and near the initiating action.
- Fail on source import, external/model/capability/Refresh work, source-text or
  opaque-payload storage, per-link confirmation, silent skips, or inventory
  loss.

## Regression Surfaces

- Existing Session and Local Context source synchronization ownership.
- FEAT-0047 bounded Atlassian evidence extraction and source fingerprints.
- Item/evidence identity, local/remote ownership, and reconciliation cleanup.
- FEAT-0077 hierarchy/list/count/query state.
- FEAT-0079 manual Add and Connections separation when already passed.
- Explicit Refresh preview, execution, and maintenance history.
- Privacy scanner and synthetic tracked evidence.

## Harness Trace

- Approved spec: [SPEC-0080](../spec/spec-0080-atlassian-local-evidence-sync.md), Attempt 1
- Completed run: [RUN-90](../run/run-20260829-90-atlassian-local-evidence-sync.md), Attempt 1
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  [contract](../evaluation/eval-0080-contract-atlassian-local-evidence-sync.md),
  [design](../evaluation/eval-0080-design-atlassian-local-evidence-sync.md),
  [functional](../evaluation/eval-0080-functional-atlassian-local-evidence-sync.md),
  and [UX](../evaluation/eval-0080-ux-atlassian-local-evidence-sync.md), all `PASS`
- Latest fix note: none

## Resolved Review Decisions

- Sync scans only already persisted eligible primary Sessions and enabled Local
  Context Documents; their authoritative source synchronization remains a
  separate action.
- Reconciliation is automatic and deterministic without per-link review, and
  reports bounded outcome categories rather than a candidate approval list.

## Continuity Notes

- `2026-08-29`: proposed after PRD-0014 approval with automatic local
  reconciliation and outcome summary, explicitly separate from source import,
  connected discovery, remote Refresh, and deferred AI retrieval.
- `2026-08-29`: the owner's approved sequential execution advanced here after
  FEAT-0079 passed. Both review decisions inherit the approved PRD defaults;
  FEAT-0080 entered the loop and proceeded to SPEC-0080.
- `2026-08-29`: SPEC-0080 and RUN-90 approved bounded persisted-reference
  input, merge-only Session evidence, separate report units, verified ephemeral
  receipts, process-local single-flight, and named in-place Explorer refresh.
- `2026-08-29`: RUN-90 Attempt 1 passed all four required evaluators, focused
  and full regressions, privacy and owner-document checks, and Chrome evidence
  across `1440`, `920`, `700`, and `320`; FEAT-0080 is passed.
