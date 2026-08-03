# FEAT-0068: Multi-Source Session Synchronization And Health

## Metadata

- ID: `feat-0068`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Goal

- Let the owner invoke `동기화` once to scan Claude, personal Codex, and Codex
  Company independently and understand each source's result without a failed or
  misconfigured source erasing another source's retained data.

## Acceptance Contract

- One Sessions `동기화` invocation scans every validated registered local AI
  Session source regardless of the selected Sessions tab. The wider Sources scan
  still includes those Session sources and enabled Local Context roots.
- Personal Codex and Codex Company dispatch to the same Codex parser and Usage
  normalizer but use different Source IDs, source-file sets, Session identities,
  Usage attribution, parent reconciliation, and stale-input boundaries.
- One source failure cannot roll back another source's successful scan. The
  structured result has one aggregate outcome and one bounded result per source,
  including imported, unchanged, failed-file, eligible-Session, and tracked-file
  counts when applicable.
- Source outcomes distinguish at least completed, empty, unavailable,
  configuration error, and scan failure. Aggregate outcome distinguishes complete,
  partial, and failed execution.
- A missing or unreadable registered root and a configuration conflict skip stale
  reconciliation for that source and preserve its existing Sessions, Usage
  Records, pins, search projection, and user-curated relations.
- When an accepted root is unchanged, present, and readable, disappearance of one
  previously imported native JSONL remains deletion authority only for that
  source's normalized Session and physically owned descendants.
- The Sessions action keeps `동기화` and `동기화 중...`. Complete success may use
  the current refresh behavior. Partial or failed results remain visible long
  enough to inspect, restore the action, and do not collapse into a raw HTTP code.
- The result names each source and consequence. Representative failure copy states
  that the source was not synchronized and that existing data was retained.
- Sources inventory presents Claude, Codex, and Codex Company as independent cards
  with readable label, root, availability, last attempt, last success, eligible
  Session count, tracked-file count, and bounded error state. Provenance and health
  remain separate visual semantics.

## Scope Boundary

- In:
  - configuration-driven adapter dispatch for registered Session sources
  - independent transaction and reconciliation boundaries per source
  - Codex Company ingestion through the current Codex parser and Usage normalizer
  - structured sync API and no-script route result behavior
  - aggregate and per-source complete, partial, empty, unavailable,
    configuration-error, and failure states
  - Sessions synchronization feedback and local Session-source inventory cards
  - source-owned stale deletion and cross-source collision/failure isolation
  - state, API, browser, responsive, and privacy-safe synthetic evidence
- Out:
  - source-scoped Sessions tabs, filters, or provenance changes owned by FEAT-0069
  - source-scoped Usage controls or composition owned by FEAT-0070
  - in-app settings editing, source disablement, source removal, purge, archive,
    restore, or root-relocation confirmation
  - parser or Usage-normalization semantic changes
  - ingesting native authentication, configuration, history, memory, log, cache,
    shell-snapshot, generated-image, plugin, or OAuth files

## Surface Lanes

- Scanner and data lane:
  - path roots: Session-source registry, scanner, parsers, Usage ingestion,
    transaction handling, source status persistence, and focused tests
  - dependencies: FEAT-0066 and FEAT-0067
  - expected evidence: per-source commit isolation, same-native-ID coexistence,
    source-scoped stale deletion, unavailable preservation, and parser reuse
  - evaluator ownership: `contract`, `functional`
- API and route lane:
  - path roots: Session-only and Sources-wide scan routes and response adapters
  - dependencies: scanner and data lane
  - expected evidence: bounded aggregate/per-source payloads, actionable errors,
    current selected-view return behavior, and no raw exception leakage
  - evaluator ownership: `contract`, `functional`
- Presentation and interaction lane:
  - path roots: Sessions synchronization result, Sources inventory cards, shared
    status styles, client action binding, and no-script fallback
  - dependencies: API and route lane
  - expected evidence: progress, complete, partial, empty, unavailable, and failed
    states at `1440`, `920`, `700`, and `320` widths
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, architecture, source registry, Session activity, Usage,
    operations, and privacy owner docs
  - dependencies: all implementation lanes
  - expected evidence: one non-duplicated current behavior contract and no stale
    hard-coded two-source assumptions
  - evaluator ownership: `contract`

## Contract Surfaces

- registered-source scanner dispatch and transaction boundary
- Session-only sync and wider Sources scan report shapes
- Source availability, last-attempt, last-success, and bounded-error state
- source-file freshness and stale-input deletion authority
- Sessions synchronization result and Sources inventory read models
- Codex parser and Usage-normalizer reuse under two source identities

## Required Evaluators

- `contract`: response shape, state vocabulary, source ownership, transaction and
  deletion boundaries, and producer/consumer alignment.
- `design`: readable per-source result and health states, provenance/status
  separation, containment, and responsive behavior.
- `functional`: successful, unchanged, empty, missing, unreadable, partial-file,
  configuration-error, same-ID collision, and source-disappearance workflows.
- `ux-heuristic`: action/result clarity, recovery guidance, repeated sync, and
  absence of misleading complete-success feedback.

## User-Visible Outcome

- The owner can synchronize all three local AI sources once and immediately tell
  which sources updated, which need attention, and whether retained data was
  preserved.

## Entry And Exit

- Entry point: `동기화` on Sessions or the wider scan on Sources.
- Exit or transition behavior: the current page and valid scope remain oriented;
  refreshed counts and persistent per-source status reflect every committed
  source, while partial/error feedback remains inspectable.

## State Expectations

- Default: action is ready and existing source health remains visible.
- Loading: one action is disabled, exposes `동기화 중...`, `aria-busy`, and a
  bounded live status.
- Success: per-source counts and aggregate completion are truthful and the view
  refreshes without losing valid scope.
- Empty: a readable root with no eligible JSONL is distinct from unavailable.
- Partial: successful sources commit and appear beside each failed or unavailable
  source; the result never says complete success.
- Error: configuration and route failures show actionable bounded text rather than
  only `HTTP 4xx/5xx`; existing retained data remains visible.
- Repeated action: bindings, selected view, and result region remain functional
  after refresh or partial completion.

## Dependencies

- [FEAT-0066](feat-0066-local-ai-source-identity-contract.md) must be `passed`.
- [FEAT-0067](feat-0067-local-session-source-settings-and-safe-registration.md)
  must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/ingest/scanner.py`
- `src/localbrain/main.py`
- `src/localbrain/queries.py`
- `src/localbrain/static/app.js`
- `src/localbrain/static/styles.css`
- `src/localbrain/templates/sessions.html`
- `src/localbrain/templates/sources.html`
- source status, ingestion, route, browser, and privacy tests
- current product, architecture, source registry, Session, Usage, and interaction
  owner docs

## Pass Or Fail Checks

- Pass if one action scans all three sources independently and both Codex sources
  use the same parser/normalizer with distinct ownership.
- Pass if one unavailable, invalid, or failed source leaves successful source
  commits intact and retains the affected source's existing imported data.
- Pass if the same native Codex Session ID in both homes produces two Sessions and
  neither source's stale reconciliation touches the other.
- Pass if actual JSONL disappearance under one unchanged present root still removes
  only its owning Session descendants.
- Pass if Sessions and Sources show bounded per-source complete, empty, partial,
  unavailable, and failed states with no raw HTTP-only failure.
- Pass if button, focus, selected view, repeated action, no-script path, and
  responsive states remain usable.
- Fail on cross-source rollback/deletion, false complete-success messaging, source
  selection narrowing sync, or native non-Session-file reads.

## Regression Surfaces

- existing Claude and personal Codex incremental scan and parser freshness
- Session/Usage identity, parent reconciliation, Maintenance classification, pins,
  search, Workstream links, and price snapshots
- Sessions/Projects mode, workspace/source/page return state, and current sync copy
- wider Sources scan and enabled Local Context behavior
- design provenance/status semantics and repository privacy

## Harness Trace

- Active spec doc: [spec-0068-multi-source-session-synchronization-and-health](../spec/spec-0068-multi-source-session-synchronization-and-health.md)
- Active run: [run-20260802-79-claude-session-candidate-discovery-fix](../run/run-20260802-79-claude-session-candidate-discovery-fix.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [Contract fix evaluation](../evaluation/eval-0068-fix-contract-claude-session-candidate-discovery.md): `PASS`
  - [Functional fix evaluation](../evaluation/eval-0068-fix-functional-claude-session-candidate-discovery.md): `PASS`
- Previous passed evaluator reports:
  - [Contract](../evaluation/eval-0068-contract-multi-source-session-synchronization-and-health.md)
  - [Design](../evaluation/eval-0068-design-multi-source-session-synchronization-and-health.md)
  - [Functional](../evaluation/eval-0068-functional-multi-source-session-synchronization-and-health.md)
  - [UX heuristic](../evaluation/eval-0068-ux-multi-source-session-synchronization-and-health.md)
- Latest fix note: [fix-0068-claude-session-candidate-discovery](../fix/fix-0068-claude-session-candidate-discovery.md)

## Continuity Notes

- `2026-08-02`: proposed as the first Product Feature after both Foundation
  contracts. It owns scanning and health only; source browsing and Usage controls
  remain separate loops.
- `2026-08-02`: human owner approved this Feature boundary for sequential
  execution after both Foundation dependencies pass.
- `2026-08-02`: RUN-20260802-73 entered the Fullstack Product execution loop.
- `2026-08-02`: attempt 1 passed all required source-level evaluators. Browser
  evidence remains an explicit non-blocking follow-up because the required
  in-app control capability was unavailable; 315 tests and the privacy check pass.
- `2026-08-02`: post-run runtime inspection found Claude workflow journals were
  accepted by generic recursive discovery and defaulted to primary work Sessions.
  The owner classified this as a bug and started RUN-20260802-79 against the
  existing non-Session-file exclusion contract.
- `2026-08-02`: RUN-20260802-79 passed attempt 1. Claude discovery now excludes
  deeper native `subagents` artifacts before reconciliation while preserving
  primary and direct-child files; 324 tests and all owner/privacy checks pass.
