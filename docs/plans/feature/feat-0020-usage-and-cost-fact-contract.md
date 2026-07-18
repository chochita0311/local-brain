# FEAT-0020: Usage And Cost Fact Contract

## Metadata

- ID: `feat-0020`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Establish one source-neutral, locally reproducible usage and estimated-cost fact contract so every downstream summary, history, breakdown, and projection consumes the same token, model, inclusion, deduplication, price, freshness, and unavailable-value semantics.

## Acceptance Contract

- Original Claude and Codex records remain authority; normalized usage and cost facts are derived local data with stable source identity and rebuild rules.
- Every directly observed real-model usage record is eligible regardless of `session_class` or `session_role`, including primary work, maintenance, and subsession activity. Source-generated pseudo assistant or API-error records may remain persisted for provenance but are not downstream usage.
- Parent and child records contribute usage exactly once when a source-level parent total already includes child usage.
- A normalized usage fact records source kind and record identity, Session and optional parent identity, observation time or period, raw and normalized model identity, supported token components, total-token semantics, capability state, freshness, and calculation state.
- Codex usage uses each event's direct `last_token_usage` when present and monotonic `total_token_usage` subtraction only as a fallback, so every positive model-call increment contributes once even when one turn contains multiple model calls. Repeated zero-delta observations contribute nothing.
- Claude cache creation uses the nested ephemeral breakdown when a zero aggregate contradicts a positive internally consistent breakdown, and records that bounded fallback in capability metadata.
- Input, output, cache creation or write, cache read, and reasoning tokens remain distinct when supplied. A derived total never double counts a component already represented by a source total.
- Each fact has at most one canonical estimated USD cost, calculated from its supported model and token fields with the matching locally available model-price snapshot.
- A snapshot may define a model-specific input-context threshold and above-threshold rates. The calculator evaluates each fact independently using non-cached input plus cache read, uses the base tier at the exact threshold, and uses the long-context tier only when that sum is greater than the threshold.
- Price snapshot identity, calculator version, and calculation time make the estimate reproducible. A later ordinary pricing update applies only to source usage first observed after that update and never automatically reprices historical facts. An explicitly approved normalizer repair may assign a corrective snapshot when the prior facts were derived with the wrong token or service-tier contract.
- Missing model identity, unsupported token components, unknown prices, malformed records, and partial source capability produce explicit unavailable or partial states rather than zero values.
- The estimate is labeled and contracted as trend cost, not an invoice, subscription charge, company spend, credit balance, or actual payment.
- Dashboard requests never invoke `ccusage`, a remote pricing service, or another external executable synchronously. `ccusage` remains a report-dimension and validation reference only.
- Fresh and upgraded databases converge on the same contract without changing source files, Git state, credentials, or external services.
- Each Session source file and Usage Fact records the normalizer-contract version that produced it. A version mismatch makes an otherwise unchanged healthy file eligible for repair synchronization.
- Repair synchronization reparses every file for the affected source and replaces that source's prior derived Usage Facts with the complete successfully parsed union. It deletes facts no longer produced, preserves retained historical price and Project-attribution snapshots, and leaves the previous set intact if any source file fails parsing or storage.
- Contract repair is an internal synchronization/migration responsibility; it does not require or expose a user-facing aggregate-reset button.

## Scope Boundary

- In:
  - Claude and Codex usage-field capability inventory
  - normalized usage-record identity and value shape
  - model-name preservation and supported normalization
  - token-component ownership and total-token deduplication
  - primary, maintenance, and subsession inclusion
  - source-aware parent-child usage deduplication
  - local model-price snapshots and calculator versioning
  - one canonical estimated USD cost and explicit unpriced state
  - freshness, partial, malformed, and calculation-failure states
  - fresh-schema and compatible-migration behavior
  - synthetic parser, normalization, pricing, deduplication, and rebuild evidence
- Out:
  - Project attribution and activity-time contracts owned by FEAT-0021
  - dashboard cards, charts, filters, breakdowns, or projection UI
  - personal budgets, caps, warnings, quota governance, currency conversion, tax, or actual billing reconciliation
  - runtime dependency on `ccusage`
  - remote price lookup at page-render time
  - Workflow and Skill Intelligence from PRD-0005

## Surface Lanes

- Contract and ownership lane:
  - path roots: `docs/policies/project/`, `docs/plans/feature/`
  - dependencies: approved PRD-0004
  - expected evidence: explicit producer, storage, rebuild, pricing, and consumer invariants
  - evaluator ownership: `contract`
- Source normalization lane:
  - path roots: `src/localbrain/ingest/`
  - dependencies: contract lane
  - expected evidence: synthetic Claude and Codex records covering supported, partial, malformed, maintenance, primary, and subsession usage
  - evaluator ownership: `contract`, `functional`
- Persistence and pricing lane:
  - path roots: `src/localbrain/schema.sql`, `src/localbrain/db.py`, usage and pricing modules introduced by the approved Spec
  - dependencies: source normalization lane
  - expected evidence: fresh and upgraded database parity, deterministic calculation, stable snapshots, and idempotent rebuilds
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- Claude and Codex source-adapter usage producer rules
- normalized usage-fact identity and token-component shape
- parent and subsession deduplication keys and precedence
- model normalization with raw-source value preservation
- local price catalog or snapshot shape and ownership
- canonical estimated-cost calculator input, output, version, and unavailable state
- freshness and source-capability state model
- SQLite schema, indexes, compatible migration, and repeat-scan behavior
- derived-fact rebuild rules and historical price immutability

## Required Evaluators

- `contract`: source authority, value shape, component ownership, deduplication, pricing provenance, migration, rebuild, and producer/consumer parity.
- `functional`: supported and unsupported source records, repeated synchronization, parent-child overlap, unknown pricing, malformed input, and historical-price stability.

## User-Visible Outcome

- This foundation Feature does not introduce a new screen. It ensures later dashboard numbers share one inspectable meaning and never present missing usage or pricing as zero.

## Entry And Exit

- Entry point: local Claude or Codex Session synchronization and derived usage normalization.
- Exit or transition behavior: valid facts become available to downstream read models; partial or unavailable facts retain their explicit limitation without blocking unrelated valid facts.

## State Expectations

- Supported: model and token components normalize and produce one snapshot-priced estimate.
- Partial capability: supported components persist while missing components remain declared.
- Unpriced: usage persists with an unavailable-cost state and no numeric zero substitute.
- Malformed: the offending record is bounded and diagnosable without clearing previously valid facts.
- Parent-child overlap: the same source usage contributes once.
- Re-scan: unchanged source identity does not duplicate usage or change its historical price snapshot.
- Price update: new source usage can use the new snapshot while prior facts retain the original snapshot.
- Source pseudo-message: the record and Session evidence remain persisted, while downstream usage consumers exclude it from dates, totals, coverage, and breakdowns.

## Dependencies

- PRD-0004 was `approved` during execution and is now `passed`.
- FEAT-0021, FEAT-0022, FEAT-0023, and FEAT-0024 must not enter Spec work against unresolved usage or cost semantics from this Feature.

## Likely Affected Surfaces

- `src/localbrain/ingest/common.py`
- `src/localbrain/ingest/claude.py`
- `src/localbrain/ingest/codex.py`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- new bounded usage and pricing modules selected by the Spec
- source, schema, migration, normalization, pricing, and deduplication tests
- `docs/policies/project/product.md`
- `docs/policies/project/architecture.md`

## Pass Or Fail Checks

- Pass if synthetic Claude and Codex inputs produce one documented source-neutral fact shape without erasing source-specific capability differences.
- Pass if primary work, maintenance, and subsession usage are included while source-level parent-child overlap contributes exactly once.
- Pass if every supported token component has an explicit owner and total tokens cannot double count cache or reasoning values.
- Pass if raw and normalized model identity are both inspectable when normalization occurs.
- Pass if each priced fact has exactly one estimated USD cost with snapshot and calculator provenance.
- Pass if a later price change and a full derived-data rebuild leave historical estimated costs unchanged.
- Pass if unknown models, missing components, malformed records, and calculation failures never appear as zero usage or zero cost.
- Pass if repeated synchronization is idempotent and a failed record does not erase previously valid facts.
- Pass if fresh and upgraded databases satisfy the same schema and query contract.
- Pass if no dashboard-time path requires `ccusage`, remote pricing, or network access.
- Fail if actual billing, budget, cap, quota, or currency-conversion semantics enter the contract.

## Regression Surfaces

- Claude and Codex Session identity, classification, parentage, and repeated synchronization
- maintenance and subsession browse behavior from PRD-0002
- existing Session, Project, source-health, Search, Workstream, and retrieval consumers
- runtime database migration and local-only operation
- source JSONL and Git non-mutation
- privacy boundary for model, path, pricing, and Session data

## Feature Review Questions

- None at the product boundary. The Spec must document the exact source-field capability matrix and physical table or module names without changing these semantics.

## Harness Trace

- Active spec doc: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Active run: [run-20260718-27-long-context-cost-contract-attempt-4](../run/run-20260718-27-long-context-cost-contract-attempt-4.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [eval-0020-functional-attempt-4](../evaluation/eval-0020-functional-usage-and-cost-fact-contract-attempt-4.md)
- Latest fix note: [fix-0025-long-context-cost-contract-attempt-4](../fix/fix-0025-long-context-cost-contract-attempt-4.md)

## Continuity Notes

- `2026-07-18`: initial draft split usage, token, price, and deduplication ownership from activity-time, Project-attribution, and visible dashboard work.
- `2026-07-18`: human owner requested sequential execution of PRD-0004 Features; this Feature entered `in-loop` as the first run with no unresolved product-boundary choice.
- `2026-07-18`: Contract and Functional evaluation passed with 53 tests, fresh and upgraded database evidence, immutable snapshot checks, and no remaining gap; FEAT-0021 may proceed.
- `2026-07-18`: private live validation invalidated the synthetic Codex assumption from Attempt 1 because same-turn token observations overwrote one another. Human review returned the passed Feature to Spec with an approved versioned-repair direction and no user-facing reset control.
- `2026-07-18`: repair validation also found that a Session identity can span several source files. Attempt 2 therefore owns exact-set deletion at the complete source-file-union boundary rather than at one Session or file boundary.
- `2026-07-18`: Attempt 2 passed Contract and Functional evaluation with 76 tests, private all-source repair, active-file append detection, repeat synchronization, database integrity, and rendered route evidence. FEAT-0020 is again safe for downstream consumers.
- `2026-07-18`: a later direct ccusage comparison invalidated Attempt 2's cumulative-only Codex basis. Official adapter evidence uses `last_token_usage` first and cumulative subtraction only as fallback; the installed report also applies the local fast service tier and model fallback/pricing coverage that LocalBrain does not yet reproduce. The Feature is blocked pending human approval to return SPEC-0020 for a second versioned repair.
- `2026-07-18`: human owner approved Attempt 3 with direct-event-first parsing, cumulative fallback, dated auto-review normalization, and one current fast-tier trend snapshot.
- `2026-07-18`: Attempt 3 passed Contract and Functional evaluation with 80 tests, exact same-boundary token-dimension parity against the installed ccusage report, intentional bounded trend-cost variance from omitted long-context tiering, private source-wide repair, repeat synchronization, SQLite integrity, and rendered route evidence.
- `2026-07-18`: human owner approved Attempt 4 after request-level analysis reproduced the entire remaining variance from long-context calls. FEAT-0020 returned to `approved` for a tiered immutable snapshot, calculator v2, automatic Codex repair, and same-boundary ccusage cost comparison.
- `2026-07-18`: Attempt 4 passed Contract and Functional evaluation with 82 tests, immutable request-tier coverage, private source-wide repair, repeat synchronization, SQLite integrity, dashboard rendering, and exact fixed-boundary token and cost parity against the installed offline ccusage report. FEAT-0020 is restored to `passed`.
- `2026-07-18`: RUN-20260718-29 clarified consumer eligibility without changing storage: Claude `<synthetic>` pseudo-messages remain persisted, while real-model maintenance and subsession usage stays eligible and downstream dashboards exclude only the pseudo-model records.
