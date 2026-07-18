# SPEC-0020: Usage And Cost Fact Contract

## Metadata

- ID: `spec-0020`
- Status: `approved`
- Run ID: `run-20260718-27`
- Attempt: `4`
- Parent Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: source normalization → immutable pricing → persistence
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Source Set

- Human request: include every observed Claude and Codex usage record, including maintenance and subsessions, and use the source-provided model with one trend-oriented estimate rather than parallel cost methods.
- Parent Feature and approved PRD-0004.
- Local Claude and Codex JSONL field inspection, installed `ccusage` 20.0.17 Codex adapter behavior, fallback snapshot, service-tier behavior, and embedded price data as validation references.
- Project Architecture, Product Model, Privacy And Data Handling, and foundation-contract execution profile.

## Approved Correction

- Attempt 2's cumulative-only Codex assumption is superseded. Each token-count event uses `last_token_usage` as its direct delta when present and subtracts `total_token_usage` only when that direct delta is absent.
- Preserve source model text in `raw_model`. Resolve `codex-auto-review` to the dated fallback model for pricing and breakdowns without rewriting the raw value.
- The current local Codex configuration is `fast`. Codex facts produced by this corrective contract use a new immutable ccusage 20.0.17-referenced fast-price snapshot. Existing Claude facts retain their prior snapshot.
- Attempt 4 supersedes the flat-rate limitation of Attempt 3. The new Codex snapshot stores both fast base and fast long-context rates plus the inspected model threshold. GPT-5.5, GPT-5.6 Sol, and GPT-5.6 Terra use `272000`; GPT-5.6 Luna uses `200000`.
- Determine the price tier independently for each Usage Fact. In normalized LocalBrain components, input context is non-cached `input_tokens + cache_read_tokens`; the exact threshold stays on the base tier and only a strictly greater value uses the long-context tier.
- This is an explicitly approved versioned corrective repair. It is not an ordinary price-catalog update and does not introduce a user-facing reset control.

## Implementation Goal

- Persist one idempotent, source-neutral usage fact for each directly observed Claude usage record and each positive Codex event delta, attach at most one reproducible estimated USD cost using an immutable local price snapshot, and repair derived facts safely when the normalizer contract changes.

## In-Scope Behavior

- Extend both Session parsers with normalized usage facts without changing message or tool-event behavior.
- Store facts for primary, maintenance, and subsession Sessions independently of their search or Dashboard-statistics eligibility.
- Normalize `input_tokens` as non-cached input: Claude input is already exclusive of cache components; Codex cached input is subtracted from its source input total.
- Preserve output, cache write, cache read, and reasoning components separately. Reasoning remains a declared subset of Codex output and is never added to output again.
- Store both the source-reported total when present and a normalized total equal to non-cached input + output + cache write + cache read. Store an explicit total-semantics value.
- Treat repeated Claude records with the same stable message or record identity as one fact.
- For Codex, read `last_token_usage` from each `token_count` event when present and treat it as the direct event delta. Only when it is absent, subtract the prior `total_token_usage` observation in the same Session file. Discard an unchanged all-zero delta and persist every positive event with stable event identity.
- Detect Codex spawned or forked subsession replay prefixes using bounded source markers and the same-second token-event pattern, seed the cumulative fallback baseline from those replayed records, and exclude the replay copies from persisted facts without excluding the subsession's later original activity.
- Normalize each Codex event as non-cached input + cached input + output. Reasoning output remains a subset of output. A cumulative decrease on the fallback path is an explicit partial/reset boundary rather than an implicit negative fact.
- Preserve the current turn-context model as the raw model. Resolve `codex-auto-review` by event date using the frozen fallback sequence through GPT-5.5; record the resolution basis in capability metadata.
- For Claude cache creation, retain the top-level aggregate when it is consistent. When it is zero but the nonnegative nested ephemeral breakdown is positive, use the nested sum and declare the fallback in capability metadata.
- Mark current Claude and Codex observations as `direct`; the schema reserves `includes_children` for a future source record that explicitly reports a parent aggregate, so a downstream rollup can exclude the covered child facts rather than adding both.
- Seed immutable local model-price rows for the inspected snapshot and calculate cost with decimal arithmetic from the normalized components.
- Store optional context-threshold and above-threshold input, output, cache-write, and cache-read rates with each model-price row. A missing threshold means the base tier only; a declared tier must contain every rate needed by the fact or produce an explicit partial state.
- Preserve an existing fact's price snapshot on rescan. A changed in-progress source record may update token values and cost only against that original snapshot.
- Store a normalizer-contract version on Session source files and Usage Facts. File freshness requires both unchanged file metadata and the current source-adapter contract version.
- On any source-file version mismatch, reparse every current file for that source and transactionally reconcile the complete union of Usage Facts: update matching identities, insert new identities, and delete prior source identities absent from the successfully parsed union. This source-level boundary preserves facts when one Session identity spans several files.
- When identities change during contract repair, inherit the Session's frozen Project-attribution snapshot. Preserve the nearest prior price snapshot unless the producer explicitly assigns a corrective snapshot as part of an approved normalizer-version repair.
- Assign the new tiered Codex fast-price snapshot explicitly to Attempt 4 Codex facts and record calculator v2. This bounded exception repairs Attempt 3's flat tier while preserving token identities and Project snapshots; ordinary synchronization and future catalog additions remain non-repricing.
- A parse or persistence failure in any affected source file must roll back the complete source replacement and leave its prior facts and prior source-file contract versions intact.
- Source-file freshness records the size and modification time observed before parsing. If an active JSONL changes during or immediately after the read, the next synchronization must see the mismatch and ingest the append rather than treating unread bytes as current.
- Do not expose a user-facing aggregate-reset control. Ordinary synchronization owns automatic version detection and repair; a bounded internal maintenance entry point may remain available for diagnostics.
- Persist unknown-model, partial-capability, and malformed-token states without substituting numeric cost zero.
- Keep source JSONL, Git state, and external services read-only.

## Out-Of-Scope Behavior

- Usage aggregation queries, date ranges, Project attribution snapshots, active-time segments, cards, charts, breakdowns, projections, budgets, or caps.
- Page-time invocation of `ccusage`, remote pricing, or network access.
- Exact invoice reconciliation or subscription accounting.

## Affected Surfaces

- `src/localbrain/ingest/common.py`
- `src/localbrain/ingest/claude.py`
- `src/localbrain/ingest/codex.py`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/usage.py`
- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- parser, pricing, persistence, migration, and repeat-scan tests
- `docs/policies/project/product.md`
- `docs/policies/project/architecture.md`

## Surface Lanes

- Source normalization:
  - path roots: `src/localbrain/ingest/`
  - dependency order: first
  - implementation responsibility: source identity, component capability, raw model, and total semantics
  - validation evidence: synthetic Claude and Codex parser fixtures
- Persistence and pricing:
  - path roots: `src/localbrain/usage.py`, `src/localbrain/schema.sql`, `src/localbrain/db.py`
  - dependency order: after source normalization
  - implementation responsibility: immutable snapshot lookup, cost calculation, idempotent upsert, and explicit unavailable states
  - validation evidence: fresh and compatible databases, changed-record rescan, unknown-model, and snapshot stability fixtures
- Contract ownership:
  - path roots: `docs/policies/project/`
  - dependency order: after implementation names settle
  - implementation responsibility: durable producer, storage, calculation, and rebuild rules
  - validation evidence: policy-to-code parity review

## State And Interaction Contract

- `complete` capability means every component supported by that adapter was read successfully.
- `partial` means a usable fact exists but at least one expected source value is absent or invalid.
- `malformed` means usage evidence exists but no trustworthy numeric fact can be calculated.
- Cost state is `priced`, `unpriced`, or `failed`; only `priced` has a numeric estimated cost.
- Synchronization under one contract version converges on the same exact fact set and never changes assigned snapshots.
- Synchronization under a newer normalizer version replaces the obsolete source-wide fact set once and becomes idempotent after every current source file records the new version.
- Parent and child facts are direct-only facts. No derived parent rollup is persisted, so both direct records are included once without a second parent aggregate.

## Data And Contract Assumptions

- `usage_facts.id` is deterministic from source kind, Session identity, and source record identity.
- `usage_facts.normalizer_version` identifies the derived-data semantics independently of the price calculator version.
- `source_files.usage_contract_version` records which adapter contract successfully processed that file; `NULL` or an older value is stale for usage repair even when size, mtime, and health are current.
- `raw_model` preserves the source value; an optional producer-resolved model carries bounded dated fallback semantics; `model_name` is the supported catalog key after normalization.
- `reasoning_tokens` is informational when it is a subset of output and does not add to normalized totals or cost.
- Every snapshot identifier is immutable and records its ccusage/model-price reference provenance. The Attempt 4 Codex snapshot freezes base rates, optional above-threshold rates, and threshold tokens. GPT-5.5, Sol, and Terra branch above 272K input-context tokens; Luna branches above 200K.
- The tier boundary is per source usage record, not per Session, turn, day, or aggregate. A later call after compaction is evaluated from its own input context and may return to the base tier.
- Cost uses per-million-token decimal rates and is stored as a decimal string so repeated calculations are deterministic.
- Existing databases receive the new tables through idempotent schema initialization; no existing user-curated table is rebuilt.

## Contract Surfaces

- Producer expectations: both adapters return `ParsedUsageFact` values with stable identity and explicit capability.
- Consumer expectations: later Features read `usage_facts` and never reconstruct price from current catalog rows at query time.
- Generated artifacts: derived usage facts and immutable model-price snapshot rows in local SQLite.
- Source-of-truth owner: source JSONL for usage evidence, `usage.py` and stored snapshot rows for calculation semantics, Project Architecture for durable ownership.
- Stale-assumption check: existing primary-only Session statistics remain unchanged; their narrower scope must not be copied into usage-cost totals.

## Required Evaluators

- Contract: inspect field ownership, component math, identity, immutable pricing, source inclusion, and policy parity.
- Functional: exercise both parsers, malformed and unknown models, maintenance and child persistence, repeat scans, and historical snapshot stability.

## Acceptance Mapping

- Source-neutral shape maps to `ParsedUsageFact` and `usage_facts`.
- Model-price provenance maps to `usage_price_snapshots`, `usage_model_prices`, and calculator metadata on each fact.
- All-session inclusion maps to `_store_session` storing usage independently from `index_policy` and `session_role`.
- Component and total deduplication maps to adapter normalization and calculator tests.
- Historical immutability maps to conflict updates that retain the original `price_snapshot_id`; the approved Attempt 4 corrective producer is the explicit exception that assigns the tiered Codex snapshot while replacing the flat prior contract.
- Unavailable states map to nullable cost plus explicit capability and calculation states.

## Evaluation Focus

- Verify Codex cached input is not charged again as ordinary input and reasoning is not counted twice.
- Verify Claude cache creation and read tokens remain additive to its non-cached input.
- Verify multiple positive Codex `last_token_usage` events remain direct facts, cumulative fallback occurs only when direct usage is absent, initial subagent replay copies are excluded, zero-delta repeats disappear, and the aggregate matches the installed ccusage token dimensions for the same source boundary.
- Verify dated `codex-auto-review` resolution preserves its raw value, current explicit models remain unchanged, every supported Codex model receives the fast snapshot, and Claude facts keep their earlier snapshot.
- Verify context equal to the model threshold uses base rates, threshold plus one uses above-threshold rates, non-cached input plus cache read owns the comparison, output and reasoning do not affect the boundary, and later below-threshold facts in the same Session return to base rates.
- Verify the frozen per-call arithmetic reproduces the installed ccusage premium for the same source and date boundary without invoking ccusage from LocalBrain runtime code.
- Verify a normalizer-version mismatch reparses every current source file, retains the union from files sharing one Session identity, replaces obsolete fact identities without double counting, applies the explicitly assigned corrective Codex price snapshot, preserves Project snapshots, and skips every unchanged file on the next synchronization.
- Verify malformed new source evidence does not delete a previously valid fact.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-18`: approved from the human's sequential execution request after inspecting local source capability and the installed ccusage reference snapshot.
- `2026-07-18`: Attempt 2 replaces the invalid latest-per-turn Codex assumption with cumulative-delta facts, adds the Claude zero-aggregate cache fallback, and defines versioned transactional repair after human post-run review.
- `2026-07-18`: human owner approved Attempt 3 after ccusage comparison: `last_token_usage` first, cumulative fallback only, dated auto-review normalization, and one immutable fast-price trend snapshot without budget/cap or reset UI.
- `2026-07-18`: human owner approved Attempt 4 after isolating the remaining variance: freeze request-level long-context thresholds and rates, keep trend and non-invoice semantics, and repair Codex facts automatically under a new snapshot and calculator version.
