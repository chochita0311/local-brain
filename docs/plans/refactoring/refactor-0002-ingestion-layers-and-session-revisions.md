# REFACTOR-0002: Ingestion Layers And Session Revisions

## Purpose

Make ingestion responsibilities and Session-result freshness easier to understand:
replace descriptive Session-version tokens with numeric revisions, define how
older runtimes may write a shared store, and separate native decoding, evidence
extraction, synchronization and projection persistence. The owner approved end-to-end implementation on 2026-10-30, including a rebuilt
app. Previously built clients are handled by rebuilding/replacing them; no
retroactive enforcement framework for unmodified legacy executables is required.

## Refactor Type

- Status: `complete`; owner-approved implementation and verification completed on
  `2026-10-30`. The implementation log and merge check own evidence and limits.
- Primary type: `Semantic` for revision storage and write admission.
- Supporting types: `Structural` for module/package boundaries; `Interface` for
  affected imports, schema consumers and package wiring.
- Parity target: `Intentional delta` for steps 1–2; `Behavior-preserving` for
  steps 3–4 as one structural batch against the fixed post-semantic snapshot.
- Compare baseline: current `master`, before this planning track.
- Baseline pin: `81590bdc3d9857eca71d5d982dbb1354a3a49215`.
- Structural baseline: `5e23084a2be9c8e2869fef9b011f3d55583e3e7b`, retained
  by `refactor-0002-semantic-baseline`. The fixed post-semantic snapshot was
  committed in a separate worktree and reran all 1,433 tests. The main branch's
  history is retained; this comparison commit is not its parent.
- Parity status: intentional deltas versus the original baseline; structural
  units pass normalized-AST comparison against the post-semantic baseline.
  [Implementation evidence](logs/2026-10-30_refactor-0002_implementation.md) and
  the [merge check](logs/2026-10-30_refactor-0002_final-merge-check.md) distinguish
  source, package and live verification.
- Execution profiles: foundation-contract for revision/storage admission;
  backend-product for extraction and integration. Any newly required screen or
  interaction change must declare its affected lane and evaluators before execution.
- Continuity: [REFACTOR-0001](refactor-0001-session-sync-repair-performance.md)
  completed performance/repair-lane work. Its baseline and evidence are historical;
  this new schema, compatibility and layering boundary requires a separate track.

## Scope

1. Keep `source_files.session_contract_version`, using nullable positive
   `INTEGER` storage and short numeric constants, initially
   `CODEX_SESSION_REVISION = 12` and `CLAUDE_SESSION_REVISION = 7`. Numbers describe
   processing-result generations within one provider; they do not select old
   parser implementations and are not compared across providers.
2. Retain independent Session, Usage and reference freshness. Only Session
   revisions become numeric in this track; Usage/reference token redesign is out
   of scope. Migration-only legacy tag mapping is separate from runtime constants.
3. Implement forward-only Session projection updates in updated runtimes before
   source projection/lifecycle writes. Rebuild the stale packaged app. The owner
   explicitly accepts build replacement rather than retroactive legacy-client
   enforcement as this track's delivery boundary.
4. Separate ingestion modules by responsibility using the approved map below.
   Preserve provider algorithms and existing skill responsibilities while moving
   their code. Do not replace concrete adapters with a generic parser framework.
5. Update dependent imports, tests, owner docs, schema/value presentation and
   package/startup wiring with each approved step.

The baseline review found the following concrete seams. Old paths and line
locations in this table describe the original baseline:

| Baseline evidence | Implemented responsibility |
| --- | --- |
| `ingest/scanner.py:913` combines repair planning, parsing, persistence, source tracking, finalization and lifecycle reconciliation; the file also owns Local Context/Notes ingestion at 1378–1876. | Separate one-source Session scanning, Session persistence/lifecycle, Context scanning and public coordination. |
| `ingest/common.py` combines DTOs, generic readers, reference/tool-result admission and maintenance classification. | Make parsed contracts a leaf; separate evidence candidate extraction from normalization helpers. |
| `skill_observations.py:6–8` imports provider parsers for revision metadata and types. | Import lightweight shared contracts/revisions without importing native parser algorithms. |
| Codex config reads/replay pre-read and both providers' dated pricing selection occur during parsing. | Keep native adapters intact initially; do not claim they are pure or change fallback/config behavior while moving them. |
| `scanner.py:939–950` treats any unequal Session token as repair; stale cleanup at 1009 precedes file-level decisions. | Version admission must occur before cleanup and projection writes, not only inside a skip helper or at the final marker write. |

An explicitly requested read-only subagent reviewed complete ingestion paths,
relevant consumers and tests using refactor-plan, then critiqued the proposed
grouping. Its evidence is incorporated here; the primary retains architecture,
migration and acceptance decisions. The initial review established no runtime
recovery; the implementation log records subsequent direct verification. [RUN-227](../run/run-20261029-227-codex-empty-page-control.md#attempt-5-recurrent-projection-with-an-older-app)
owns the earlier mixed-build reproduction and its evidence limits.

## Non-Goals

- New message/tag heuristics, broader XML filtering, CRLF cleanup, title layout
  fixes or changes to authored-input preservation.
- A directory or implementation for every historical parser revision, dynamic
  parser selection from DB values, Git restoration, or a new plugin framework.
- Repricing Usage because a Session revision or its representation changes.
- Parallel SQLite writers, a new background daemon, extra cloud services,
  dependency upgrades or a repository-wide persistence rewrite.
- Automatic downgrade, a force flag that bypasses newer-data protection, or a
  new production UI for replaying old parser results.
- Editing native JSONL, new private-corpus extraction, or adding a DB-trigger/
  write-owner protocol solely to control unmodified legacy executables. Previously
  built app copies must be replaced before using the upgraded store.
- General formatting, unrelated naming changes, or changing failure/transaction
  semantics while extracting modules.

## Invariants

- Native inputs stay read-only. Preserve accepted source candidates, per-profile
  `source_id`, source-scoped Session identity, event/provenance IDs, parent rules,
  curated pins/links, Usage snapshots and retained skill observations.
- Preserve normalized message order, native counterpart precedence, explicit and
  ambiguous phase handling, per-block context filtering, literal boundaries,
  reference admission and tool/skill evidence meaning. Reading old native formats
  with the newest parser remains supported.
- Session-only repair must not reprice unchanged Usage. Keep source-level Usage
  union reconciliation across contributing files and existing reference bounds.
- Keep one outer transaction per registered Session source. Normal Context
  collection groups enabled roots within its existing collection transaction;
  direct `scan_context_root` uses its caller's transaction. Preserve repair
  savepoints, ordinary per-file exception behavior and Session source failure
  isolation; do not add commits, connections, locks or per-file savepoints by accident.
- Preserve the order of stale cleanup, file processing, reference finalization,
  repair reconciliation/rollback, error marking, parsed-empty cleanup, parent
  reconciliation and maintenance skill correction after successful admission.
- For full-index Sessions, parsed-empty cleanup requires the current owner
  **and every tracked sibling** to be in the empty set. A meaningful shared owner,
  including a skill-only owner, prevents that cleanup. After eligible stale
  conversation/search is cleared, retained historical Usage prevents Session retirement.
- Preserve optional/null Context ownership and revision fields, source/file PKs,
  foreign keys, uniqueness, indexes, timestamps and error evidence through schema
  conversion except the explicitly mapped Session revision values.
- Keep public `scan_*` signatures and report/progress contracts. In particular,
  `scan_context_root(connection, ...)` uses the caller's transaction. New admission
  errors must be bounded, preserve prior results and identify update-required
  state without exposing private input paths/content.

## Planned Work

### Step 1 - Enforce Forward-Only Revision Admission

Goal:
- Implement provider-scoped numeric revision admission in updated runtimes before
  source upsert, cleanup or normalized projection writes.

Why this grouping:
- Revision comparisons are a semantic change and must be verified independently
  of moving code. The owner's implementation approval resolves deployment scope:
  rebuild the old app rather than introduce retroactive legacy-client control.

Guardrails:
- A null marker means unknown freshness and triggers real Session/skill backfill;
  Context rows may remain null. Lower revisions upgrade; equal revisions still
  use normal file/eligibility/independent freshness checks. Higher revisions reject
  that source before mutation, including forced scans; safe peer sources continue.
- Invalid revisions fail with a bounded diagnostic. Do not infer Session freshness
  from a current Usage marker or silently stamp unknown results current.
- Preserve input-format backward compatibility. Historical comparisons use isolated
  data; an intentional rule reversion is released as a new higher result revision.
- These guards apply to the new code. Integer storage checks are validation, not
  proof that an already-running old executable has been made compatible. Stop old
  local writers before live rollout and verify the rebuilt app's embedded code.

Targets:
- `src/localbrain/ingest/scanner.py`, shared Session revision metadata
- Source health/error handling, updated scanner consumers and tests

Validation:
- Lower/equal/higher/null/invalid revisions, both providers and arbitrary labels.
- Mixed revisions in one source, independent safe peers, force, growing files,
  disappearing files and empty-owner cleanup. Assert rejection occurs before
  any normalized/source projection mutation and retains existing curated data.

Exit gate:
- Updated runtimes reject backwards writes with a clear update-required result;
  existing forward repair, Usage separation and source isolation remain verified.

### Step 2 - Migrate Session Freshness To Nullable Integer Revisions

Goal:
- Replace Session TEXT tags with validated numeric revisions and short constants
  without changing parser outputs or unrelated freshness lanes.

Why this grouping:
- Column representation, migration mapping, revision comparisons and coverage
  consumers form one schema/interface change; separating them would create a
  partially converted store.

Guardrails:
- Retain the column name and nullable behavior. Use explicit integer validation;
  SQLite affinity alone permits nonnumeric text. Do not make the whole database
  STRICT merely to change this field.
- Preserve current numbering, Codex `12` and Claude `7`, and map only reviewed
  historical tags within the matching provider. Known source history includes
  Codex `3, 4, 8, 11, 12` and Claude `1, 2, 6, 7`; enumerate verified full-token
  mappings at the migration boundary, not multiple runtime parsers.
- Do not use `CAST(... AS INTEGER)`, extract any unvalidated `vN`, reset everything
  to `1`, or stamp the current revision on results that were not reparsed.
  Unknown/future/mismatched-provider tags stop migration before mutation; null
  remains null and is subsequently handled by the accepted admission policy.
- Use the existing backup/transaction/shape-validation pattern for a table
  rebuild. Preserve every other column, identity, FK and index; restore only
  through the approved storage recovery contract.
- Reconcile the source-registry owner's historical Usage-proven null-backfill
  description with current behavior: the current missing-marker test requires
  Session/skill backfill without Usage repair, not a marker-only current stamp.
- Move the small numeric Session constants to a parser-independent contract
  owner. Keep the migration's old strings isolated from daily runtime metadata.

Targets:
- `schema.sql`, `db.py`, existing provider Session constants and scanner types
- `skill_observations.py` coverage comparisons and `source_settings.py` null reset
- Data-model source-registry owner, relevant value dictionaries, schema
  presentation generator/data and cleanup audit inputs/ledger

Validation:
- Fresh and legacy synthetic schemas; all known tags; already-integer rows;
  Context nulls; invalid/text/real/zero/negative values; future revisions;
  mixed-provider profiles; interrupted and repeated migration.
- Verify declared type and stored `typeof`, row-by-row preservation, valid backup,
  `integrity_check`, `foreign_key_check`, unique/index/FK shape and idempotence.
- Assert Session-only freshness repair leaves exact Usage values unchanged;
  skill coverage and source reconnection continue to observe the correct revision.
- Rerun numeric forward/backward-admission and source-isolation tests against the
  migrated schema. Do not claim retroactive compatibility of old executable copies.

Exit gate:
- Numeric schema, constants, readers, docs and generated consumers agree. Known
  migrations are lossless apart from the declared tag-to-integer mapping, unknown
  cases fail without changing data, and updated-runtime admission remains proven.

### Step 3 - Separate Shared Contracts, Provider Adapters And Evidence

Goal:
- Establish readable downward dependencies without changing native reconstruction.

Why this grouping:
- Leaf contracts remove imports of provider algorithms merely to read DTOs or
  Session revision metadata; provider/evidence moves can then share that boundary.

Guardrails:
- Approved layout and old-to-new mapping:

  | Baseline owner | Current owner |
  | --- | --- |
  | Parsed DTOs, numeric Session revisions and unchanged Usage tokens | `ingest/contracts.py` |
  | Identity, JSONL/text/title helpers and maintenance classifier | Reduced `ingest/common.py` |
  | Native Codex/Claude reconstruction | `ingest/providers/codex.py`, `claude.py` |
  | URL/Markdown and approved tool-result candidates | `ingest/evidence/reference_candidates.py` |
  | Existing skill collection and matching modules | `ingest/evidence/skill_loads.py`, `skill_usage.py` |

- Keep provider algorithms, config/pricing/replay behavior, evidence limits and
  skill-module internals intact. No generic cross-provider event pipeline.
- Package initializers stay empty. Contracts import neither providers nor sync;
  candidate extraction imports no persisted reference/evidence service.
- Keep only demonstrated public compatibility wrappers; update private import
  and patch targets instead of building module-proxy indirection.

Targets:
- Existing `ingest/common.py`, `codex.py`, `claude.py`, skill modules
- `usage.py`, `skill_observations.py`, `session_references.py`,
  `atlassian_evidence.py`, `source_settings.py`, `subagents.py`, direct parser tests

Validation:
- Use the fixed post-step-2 commit above as the comparison target for the combined steps 3–4 batch.
- Compare complete ParsedSession/Usage/skill/reference fields on identical
  synthetic native bytes, including both Codex formats, turns, phases, generated
  contexts, literal examples, Claude split messages and hierarchy.
- Fresh-process imports of parser consumers and application entrypoints; verify
  imports do not start collection and coverage no longer imports provider code.

Exit gate:
- Imports point downward, public/direct consumers remain wired, and strict
  structural comparison covers outputs, side effects and failure behavior against
  the step baseline before any parity claim.

### Step 4 - Separate Domain Scans And Projection Persistence

Goal:
- Reduce scanner to public composition while separating Session and Local Context
  work and their concrete persistence responsibilities.

Why this grouping:
- Session and Context paths have distinct inputs/lifecycles, but share locks,
  source metadata, cancellation and some local projection operations.

Guardrails:
- Approved old-to-new ownership:

  | Baseline scanner responsibility | Current owner |
  | --- | --- |
  | Public entrypoints, registry/adapter selection, reports, locks/init and Session-source/Context collection transaction boundaries | `ingest/scanner.py` facade |
  | `_scan_session_source`, discovery, freshness/repair planning and selective updates | `ingest/sync/sessions.py` |
  | Session/Usage projection, stale/empty lifecycle and parent reconciliation | `ingest/sync/session_store.py` |
  | Context folder/file/PDF/Notes extraction and document persistence | `ingest/sync/contexts.py` |
  | Shared source/file tracking, revision admission, workspace upsert, FTS replacement and structure-owner reprojection | `ingest/sync/storage.py` |
  | Shared cancellation context and callback-safe progress | `ingest/sync/control.py` |

- Services use the supplied connection and do not commit or obtain another writer
  lock. Preserve caller-owned Context transactions and one cancellation context
  with its existing `finally` reset.
- Storage/control do not import the facade. Explicitly pass facade-owned settings,
  adapter selection and invocation dependencies where needed; do not add global
  service lookup to keep monkeypatches working.
- Keep named lifecycle operations and their SQL/side effects together. Do not
  silently consolidate differing folder/direct-file document upserts or add
  per-file savepoints while moving code.

Targets:
- `ingest/scanner.py` and `ingest/sync/` modules
- `main.py`, `cli.py`, `runner.py`, source services/settings and affected tests

Validation:
- Use the same combined-batch baseline and map every old entrypoint/query/write to its new
  owner, including predicates, nulls, timestamps, call ordering and failure paths.
- Compare full synthetic DB projections for ordinary, forced, Session-only,
  Usage-only, reference-only, mixed/failed repairs, shared-file Usage union,
  disappearing/empty/skill-only owners and maintenance propagation.
- Exercise folder/direct-file/Notes identities, PDF/unreadable-file behavior,
  timeout/cancellation, partial reference repair and structure-search reprojection.
- Update tests to patch the actual lookup owner. Verify progress/report ordering,
  same settings isolation, existing-connection calls and public scanner signatures.

Exit gate:
- Domain services, persistence and coordination have distinct responsibilities;
  transaction/failure/side-effect parity is demonstrated against the step baseline.

### Step 5 - Verify Source And Packaged Runtime Wiring

Goal:
- Confirm the approved implementation is used by both source and rebuilt runtime
  entrypoints, with updated-runtime backward-write refusal verified.

Why this grouping:
- Source imports and tests do not prove that a previously built executable has
  changed or that packaged dependency discovery includes moved modules.

Guardrails:
- Freeze the final candidate/legacy baselines. Use synthetic data and owned temp
  roots; never overwrite or delete an active app bundle during verification.
- Package success does not imply recipient/native browser acceptance. Record
  actual build, startup, parser revision, import and operational evidence separately.
- No automatic production rollback/rebuild command is introduced by this step.

Targets:
- `pyproject.toml`, `desktop/backend.spec`, `scripts/build-desktop.py`
- CLI/web startup, scheduled/manual sync and existing error/result presentation
- Relevant owner/generated docs and future execution/refactor evidence

Validation:
- Source and isolated installed-wheel imports/CLI startup, synthetic scan/API
  round trips and configured automated checks.
- Rebuilt frozen backend starts against synthetic data, reports/uses numeric
  revisions, imports moved modules and passes backward-write rejection cases.
- Inspect existing Sync success/error/retry behavior and confirm original sources,
  Usage and curated relationships remain intact. Run the full suite on the exact
  final candidate and privacy/generated checks; retain necessary aggregate evidence
  before stopping owned processes and removing temp state.

Exit gate:
- Required source/package/compatibility evidence passes for the declared scope;
  unresolved recipient/deployment conditions remain explicit. A merge decision
  uses the separate merge-check artifact linked above.

## Validation Gates

- The initial planning pass was static only. The implementation and merge-check
  logs record new direct execution; historical parser-fix results remain separate.
- Required focused coverage: `test_parsers`, `test_session_sync`, `test_session_contract`,
  `test_schema_migrations`, `test_source_profiles` / `test_session_source_settings`, `test_skill_observations`,
  `test_automatic_skill_loads`, `test_usage_contract`, `test_session_references`,
  `test_atlassian_structure_references`, `test_context_sync`, `test_context_roots`,
  existing source-service and desktop/build tests. Resolve actual suite names from
  the implementation baseline before invoking them.
- Static/build: configured Python compilation and fresh-process imports; declared
  Python 3.9 syntax compatibility and recommended uv-managed Python 3.11 runtime;
  wheel and frozen-module discovery after package moves. No dependency upgrade.
- Required final repository checks include `scripts/check-repo-privacy.sh`,
  `python -m unittest discover -s tests -v`, `scripts/check-data-model-docs.py`,
  `scripts/build-schema-presentation.py check`,
  `scripts/check-schema-cleanup-audit.py --check`,
  `scripts/build-plan-artifact-catalog.py check`, the configured value-dictionary
  check and `node scripts/check-data-model-mermaid.mjs` when owner ERDs change,
  plus whitespace/link checks. Use the configured environment and task-owned
  temporary roots for synthetic evidence.
- Strict structural parity requires the committed batch baseline, complete source
  mapping, row/DTO field comparisons, query/write predicates, output/fallback
  equivalence, transactions, exceptions, retries, callbacks and side effects.
  Any uncovered path keeps parity `Provisional`.

## Intentional Deltas

- Session freshness changes from nullable descriptive TEXT to nullable validated
  INTEGER with provider-scoped ordering; short numeric metadata replaces verbose
  runtime Session strings. Legacy labels remain only where needed to migrate data.
- Ordinary Sync and same-source reconnection refuse a newer stored Session revision instead of reparsing it
  with older rules; force does not mean downgrade permission. Compatible input
  formats and parser outputs otherwise retain their existing semantics.
- Old unmodified binaries are handled by rebuild/replacement. The owner declined
  a retroactive DB-trigger or write-owner protocol; integer storage alone does not
  make those binaries safe or compatible.
- Review found two additional intentional safety deltas: reconnection checks before
  null invalidation, and refusal of unrecognized same-column migration shapes,
  including incoming/outgoing FK, unique, affinity, check and timing differences. They are tested separately.
- Steps 3–4 intentionally move imports/module owners only; do not hide normalization,
  SQL, error/transaction, timing, pricing or source lifecycle changes inside them.

## Risks / Open Questions

- The owner resolved the former legacy-enforcement gate by approving a rebuilt
  app. New checks do not change an old executable; unupdated external copies are
  unsupported on the migrated store. This track verifies replacement delivery,
  not a DB-level legacy-client enforcement protocol.
- Resolved before rollout: exact provider-specific historical-token mapping,
  unknown/future/null policy, verified backup, savepoint rollback and supported
  table-shape checks. Unknown legacy strings fail before startup mutations;
  unsupported rebuild shapes fail while preserving the original table.
- An INTEGER affinity alone accepts legacy TEXT in ordinary SQLite. A CHECK or
  suitable equivalent can validate storage, but does not by itself establish
  atomic old-client refusal. See [SQLite datatypes](https://www.sqlite.org/datatype3.html)
  and [STRICT semantics](https://www.sqlite.org/stricttables.html); no whole-DB
  STRICT conversion is proposed. The [ALTER TABLE procedure](https://sqlite.org/lang_altertable.html#making_other_kinds_of_table_schema_changes)
  was retrieved after an initial timeout and documents a table-rebuild route for
  datatype changes; verify it against actual source and packaged runtime versions.
- A provider's numeric revision must identify one result contract across branches
  and builds. Reusing the same number for different rules would defeat freshness
  checks; release review must allocate a new revision for an intentional change.
- Resolved documentation drift: the source-registry owner now records actual
  Session/skill backfill for null markers without Usage repair. The previous
  Usage-proven marker-only description did not match the implementation.
- Module moves can alter monkeypatch/global lookup, relative import cycles,
  cancellation context, packaging discovery and source-adjacent configuration.
  Empty package initializers and explicit composition help, but require validation.
- A release/process can run code different from the checkout. Source, installed
  wheel and frozen code were checked separately; local rollout
  evidence lives in the implementation log. These checks establish neither
  universal parsing correctness, a measured speedup, old-build safety nor
  recipient/WKWebView acceptance.

## Exit Goal

An approved implementation has a small, understandable ingestion dependency
structure, numeric Session revisions with reviewed legacy conversion, independent
Usage freshness, and a demonstrated policy preventing ordinary backward writes by updated runtimes.
The combined structural batch has its fixed comparison baseline and proof. The
required implementation, review and verification gates passed; the final merge
check records the intentional deltas and remaining acceptance limits.

Execution record: [implementation log](logs/2026-10-30_refactor-0002_implementation.md).
