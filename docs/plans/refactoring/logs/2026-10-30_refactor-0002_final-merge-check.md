# REFACTOR-0002 Final Merge Check

## Scope

- Related track: [REFACTOR-0002](../refactor-0002-ingestion-layers-and-session-revisions.md)
- Scope: Session result storage/admission and the combined ingestion structural
  batch, including package and local runtime wiring.
- Initial baseline: `81590bdc3d9857eca71d5d982dbb1354a3a49215`.
- Structural baseline: `5e23084a2be9c8e2869fef9b011f3d55583e3e7b`, retained as
  `refactor-0002-semantic-baseline`; confirmed, rerun in the separate comparison worktree with 1,433
  passing tests. It captures numeric semantics before module extraction.
- Evidence owner: [implementation log](2026-10-30_refactor-0002_implementation.md).

## Changed Surface

- Added: leaf contracts, exact legacy conversion, supported-shape validation,
  new-runtime revision admission, provider/evidence/sync packages and focused tests.
- Updated: schema/storage ownership, source reconnection, actual import/mock
  owners, current policy and generated consumers.
- Moved: provider/skill modules, common DTO/evidence units and scanner services.
- Removed: old flat provider/skill paths and provider imports needed only for
  metadata. No historical parser implementation registry or proxy layer remains.

## Validation Run

- Working tree at assessment: **No**, the reviewed task-owned candidate awaited
  commit. It was committed as `f8fb80d80cb2b0d9323f2679525e59caeb39fff3` and
  pushed with the comparison tag; both remote SHAs were verified. Unrelated
  changes were not included.
- Build/compile: source imports and compilation pass; installed wheel and the
  rebuilt signed Apple Silicon backend pass. Fifteen frozen modules match source.
- Targeted tests: migration **9**, Session Sync **27**, source profiles **18** pass;
  normal/forced future refusal is exercised for both providers, as are reconnect
  preservation and interruption after table drop.
- Full suite: original **1,426**, semantic snapshot **1,433**, committed semantic
  snapshot **1,433**, post-extraction **1,435**, expanded **1,436**, and final
  **1,437** pass. The final run took 28.724s with no failures/errors/skips.
- Runtime: synthetic frozen old-DB conversion/Sync/refusal/preservation and clean
  shutdown pass; live web migration preserves non-revision data and passes DB
  integrity/FK checks. Chrome verifies the reported Session route with no standalone
  page-control row, script error or horizontal overflow.
- Owner/generated checks and 12 Mermaid diagrams pass. Final privacy, catalog,
  relative links and both independent documentation reviews pass after the
  primary applied their required corrections. Python 3.9 syntax passes for all
  changed Python files. Final packaged schema/value data matches source; ZIP
  SHA-256 verification passes.

## Strict Parity Audit Coverage

- Immutable baseline: **Yes**, the separate comparison commit/tag above.
- Source mapping: **Yes**, the complete implementation-log map and all 136 mapped
  scanner/common/provider/skill units. Another 98 non-ingest modules compare
  unchanged except imports; reconnect/migration safety deltas are explicit.
- Query/write semantics: **Yes** for structural units. Normalized AST comparison
  retains SQL, bindings, predicates, identity selection, nulls and return branches.
- Payload/output mapping: **Yes** for the seven DTOs and the complete provider
  algorithms, preserving field defaults, native precedence, provenance and phases.
- Side effects: **Yes** for structural units, including source-adjacent reads,
  pricing selection, grouped/caller Context transactions, per-source Session
  transactions, repair savepoints, shared cancellation and safe callbacks.
- Failure modes: **Yes** for structural units, including ordinary per-file catches,
  repair rollback, reference finalization/error marking, empty-owner lifecycle,
  Notes timeout/cancellation and source isolation. Existing integration tests
  exercise these paths; no new commit/lock/per-file savepoint was introduced.
- Unaudited relevant structural path: **None**. Runtime acceptance limits below
  are separate from the completed source comparison.

## Merge Assessment

- Safe to merge: **Yes** for the scoped P2-1 correction assessed below. The
  independent audit correctly retracted the earlier no-required-fix statement;
  the correction now closes that finding with fresh proof.
- Behavioral parity versus initial baseline: **Intentional deltas present**.
- Structural parity versus the semantic snapshot: **Preserved** for moved units;
  confidence basis is complete source comparison plus tests/runtime evidence.
- External contract parity: **Intentional deltas present** — numeric DB values and
  newer-source refusal, including reconnect. Existing scan signatures and report
  structure remain; the bounded error code is additive.
- Client-visible change: **Yes**, higher-result sources now request an update
  instead of allowing a backward reparse. Legacy app copies need replacement.
- Required fixes before declaring scoped readiness: **None**; P2-1 is resolved
  by the correction and fresh verification below.

## Parity Proof

- Inputs: identical provider/source candidate rules and native formats; exact
  code-unit comparison preserves turn/message/Usage/evidence reconstruction.
- Outputs: DTO fields, identities, order, Session/activity/search/skill/reference
  operations and public scan reports are unchanged by the structural move.
- Side effects: shared connection/transaction ownership and statement/call order
  remain; Context uses explicit facade configuration instead of a copied global.
- Failure behavior: original catches/savepoint branches remain. The numeric
  migration and future-revision errors are intentionally new and independently
  tested, rather than counted as structural parity.

## Intentional / Reviewed Deltas

- Nullable positive integer Session revisions; known provider-specific strings
  convert without parser execution or result replacement. Unknown tokens stop.
- Before any scan lifecycle write, a higher revision refuses the source, including
  force; safe peers continue. Reconnect refuses before parser/path/null invalidation.
- A table rebuild refuses unsupported affinity/FK/implicit uniqueness/check/timing
  shapes and unknown incoming FKs, including mixed-case target names. A failure
  after dropping the old table restores the full original schema.
- The owner resolved old-binary deployment by rebuild/replacement. No retroactive
  old-client write protocol is claimed or required by this approved delivery.

## Residual Risks

The existing exact-text ambiguity concerns the earlier Codex null-page filter:
an authored standalone block indistinguishable from its generated envelope is
also filtered. The [normalization owner](../../../policies/project/data-model/workspace-and-session-activity.md#conversation-normalization-and-empty-sources)
defines that boundary; it is unchanged by P2-1's DDL recognition correction.
Broader provenance safeguards and the earlier deferred parser/UI cases remain
in the [Sessions backlog](../../project/backlog.md#p1---sessions-and-retrieval). No
universal correctness, measured speedup, recipient/WKWebView acceptance, live
external-provider success or notarization is implied. Original sources stay
outside Git; private runtime/screenshot/raw logs remain private. Migration backup
retention follows the storage owner. A changed parser result contract must get a
new higher provider revision across branches.

## Independent Parity Audit

- Request/date: user-requested subagent review under refactor-plan Parity-Strict,
  `2026-10-30`, after the completed implementation/publication above.
- Frozen target: `c7eadd3a2ade77f93cb7a5704e91f2e0b20ef35b`; application-code
  identity `f8fb80d80cb2b0d9323f2679525e59caeb39fff3`. The target differs from the
  implementation only in documentation. Compare target remains
  `5e23084a2be9c8e2869fef9b011f3d55583e3e7b`; original baseline `81590bd` remains
  the reference for intentional semantic deltas. Worktree was clean at review start.
- Authority: fresh independent read-only subagent plus primary verification.
  No application code, user DB, native input, running app or external service was
  changed. Earlier runtime/package receipts were read as historical evidence and
  were not rerun or relabeled as fresh deployment proof.

### Structural Coverage And New Verification

The independent source audit maps all **107** old top-level ingestion functions/
classes with none missing: common DTOs/helpers/candidates **27**, contracts error
class **1**, Codex **14**, Claude **3**, skill collection/matching **9**, scanner
composition **20**, Session orchestration **2**, Session persistence **8**, Context
**10**, shared storage **11**, progress/cancellation **2**. Of these, **104** have
identical normalized ASTs; **3** differ solely in explicit settings/configuration
injection, whose call sites and values were manually reconciled. All **32** moved
module assignments match. This function/class counting differs from the earlier
136-unit inventory that included other definition forms.

All **98** moved SQL execute/executemany call sites and bind arguments match:
facade **5**, Session orchestration **23**, Session store **38**, Context **19**,
shared storage **13**. Nine import-only consumers add **152** unchanged top-level
units and **162** unchanged SQL calls: `atlassian_evidence`,
`atlassian_evidence_sync`, `atlassian_structure_references`,
`personal_insight_usage`, `session_context`, `session_references`,
`skill_observations`, `subagents`, and `usage`. Source settings has eight identical
functions; its reconnect function has only the approved guard and import move.
Main/CLI/runner, source schedulers/registry/configuration/locks/pricing and build
configuration are unchanged against the structural baseline.

The audit checked joins, predicates, null/default/order/limit behavior, write
keys/fields/timestamps, DTO fields, native counterpart/phase/provenance, replay/
config/pricing, skill/reference bounds, search reprojection and source health.
It also checked source-owned versus grouped/caller Context transactions,
ordinary per-file partial failures versus repair savepoints, shared-file Usage
union, reference finalization/rollback, empty/skill-only/Usage retention, parent
maintenance propagation, one cancellation ContextVar with finally reset, safe
callbacks and public scan signatures. No relevant frozen-source path is unmapped.

The primary separately reran **1,437 tests in 29.264s**, with no failures/errors/
skips, on the frozen source. A synthetic differential replay ran identical native
bytes, source paths, file stats and controlled clock inputs on both baselines:

- **13 ParsedSession DTOs**, including all nested Usage/skill/reference fields;
- **15 phases**: initial Context, initial Session, unchanged, null Session repair,
  Usage-only repair, reference-only repair, force, appended input, per-file
  failure, source rollback, stale/empty ownership, Context edit, direct caller
  rollback, cancellation, and resumed scan;
- **49 application/FTS data tables per phase**, plus public reports/progress.

Both complete replay JSON outputs were byte-identical; no output fields, IDs or
timestamps were scrubbed. Table enumeration and JSON keys were sorted. SQLite/
FTS shadow bookkeeping tables were excluded; DDL safety was assessed separately.
This is evidence for the declared source behavior, not latency, every possible
native input, native-browser or recipient acceptance.

### P2-1 Counterexamples Before Correction

In frozen target `c7eadd3`, shape validation at original lines 79–87 removed
whitespace and searched SQL substrings; current-contract detection at original
lines 99–100 also treated required CHECK text anywhere in SQL as enforcement.
Neither interpreted comments. The [current module](../../../../src/localbrain/source_revision_migration.py)
contains their correction described below. The subagent reproduced the following in-memory on
SQLite **3.51.0**; the primary independently confirmed all four on configured
SQLite **3.53.1**:

| Legal synthetic schema | Before / expected | Observed before correction |
| --- | --- | --- |
| `CHECK /* rule */ (status <> 'archived')` | Reject `archived`; refuse unsupported shape | Migration succeeds, drops CHECK, then accepts `archived`. |
| `UNIQUE(source_id,path) ON /* policy */ CONFLICT IGNORE` | Duplicate is ignored; refuse unsupported policy | Migration drops IGNORE and duplicate insert raises `IntegrityError`. |
| `) STRICT /* mode */;` | Reject TEXT in INTEGER `size_bytes`; refuse unsupported storage | Migration drops STRICT and accepts TEXT. |
| INTEGER revision column with required CHECK text only in a comment | No enforced revision CHECK; do not mark current | Contract is reported current, migration skips and arbitrary revision TEXT is accepted. |

This was one migration-validation defect family and an unmet approved safety
contract in the frozen target. It is not an intended delta or an ordinary conversation-parser change.
No impact to the user's actual database was inspected or established by that
review. The then-passing suite did not cover the counterexamples. The initial
review applied no product fix; the owner-approved correction and regressions below
close the issue without erasing that counterevidence.

### Independent Review Decision Before Correction

- Structural parity against the pinned semantic baseline: **Preserved** in the
  completely audited source scope, supported by source comparison, fresh tests
  and differential replay.
- Whole-track behavior versus the original baseline: **Intentional deltas present**,
  with **P2-1 open** in their migration enforcement. Overall safety/readiness is
  **Not yet**; the previous blanket no-required-fix assessment is retracted.
- Fresh wheel/frozen/backend/browser/live-DB/recipient proof: **Not run in this
  review**. Earlier receipts retain their original scope and timing.

## P2-1 Correction

The owner approved implementation after the review. The correction is semantic
only in DDL admission/current-contract detection; native parser algorithms,
Session revisions **12/7**, Usage rules, scan services, reconnect and `schema.sql`
remain unchanged. No dependency was added.

`_ddl_tokens` distinguishes SQLite whitespace/comments from single-quoted
literals and double-quoted/backtick/bracketed identifiers. It preserves literal
case and doubled quote escapes. U+FEFF is whitespace at a token boundary but is
retained inside identifiers/literals. `_revision_checks` inspects actual top-level
CHECK spans and accepts only the known predicate, with proper identifier quoting.
Unsupported active CHECK/modifier/conflict semantics refuse before table replacement.
Keyword text in comments/quoted values cannot establish a numeric constraint.
This is a bounded contract recognizer; arbitrary equivalent predicates and legacy
double-quoted string-literal forms are deliberately refused instead of assumed equivalent.
The lexical rules were checked against [SQLite comments](https://www.sqlite.org/lang_comment.html)
and [quoting rules](https://www.sqlite.org/lang_keywords.html).

### Correction Verification

- **16 migration tests** pass on configured SQLite **3.53.1**, including the four
  original failures, block/line comments, BOM-hidden CHECK/conflict/STRICT,
  fake CHECK text in comments/quotes, real quoted/commented predicates, literal
  case, quoted modifier names and existing mappings/index/FK/backup/rollback.
- A separate read-only subagent reviewed source blob
  `811421664a5d5d9da6c6c33945c26d8ba8a1c0e2` and test blob
  `abb0754fa2173b2909ad6fcc46983c267829984d`. It independently ran **14 in-memory
  probes on SQLite 3.51.0**, including a newly discovered BOM bypass, which was
  corrected and retested. No further concrete false-current or constraint-loss
  finding remained. Four migration execution functions, the canonical predicate,
  backup suffix and legacy mappings remain AST-identical to `c7eadd3`.
- **1,444 full tests pass in 28.282s**, with no failures/errors/skips. The exact
  differential replay against `5e23084` again matches **13 DTOs**, **15 phases**,
  **49 data tables per phase**, reports and progress byte-for-byte. No outputs
  were scrubbed; input clocks, paths and file stats were controlled.
- Compilation and Python 3.9 syntax checks pass. An isolated installed wheel
  passes all **16 migration tests** plus app/scanner imports and CLI help. The
  first wheel test placement put runtime scratch under its package-root boundary;
  separating those directories resolved the fixture failure without changing
  application storage rules.
- The rebuilt Apple Silicon app passes signing/private-path inspection and ZIP
  checksum verification. **15 embedded code modules** and schema/value JSON match
  source. Synthetic frozen startup repairs a comment-only fake CHECK, converts
  the known token to integer 12 and enforces rejection of invalid values. A real
  Sync imports **one** native file, filters the control, stores Usage, then refuses
  future revision 13 without changing Sessions/events/Usage/pins/source-file rows.
  A separate frozen launch refuses a BOM/comment-hidden extra CHECK; its original
  table SQL, rows and rule remain. The successful backend exits **0**.
- Final web restart was preceded by data-target, operation-lock and active-run
  checks. Existing `source_files` SQL was not rebuilt; source-file, Session,
  activity, Usage, pin, organization-link, skill and reference signatures remain
  identical through initialization. Integrity/FK checks pass, health is `web/ok`
  and the reported Session route returns **200**. The final server inherits no
  task temporary path and writes no task log.
- Owner/dictionary/schema/audit/catalog and privacy checks pass. All **896**
  relative links/anchors in the six changed Markdown documents resolve. Both
  independent documentation reviews completed; their current-versus-historical
  link/cleanup and readiness wording findings were reconciled with actual results.
  No ownership or navigation redesign was needed. Native-window/recipient
  acceptance, live external providers, notarization and universal input correctness
  remain outside this correction's evidence.

### Correction Decision

P2-1 is **resolved** in the reviewed source and packaged/runtime checks. Structural
source parity remains **Preserved**; the correction intentionally restores the
approved DDL refusal/real-check contract. The earlier independent review's
Not-yet decision is superseded for this corrected candidate; its failure evidence
and the previous publication history remain preserved above.

### Final Session Reconciliation

- The product correction was committed as
  `61a491c188a1788944b0f3f5fcd8914787852a06` and pushed to `origin/master`;
  a fresh remote readback matched that SHA on `2026-10-30`. Its source/test blobs
  match the identities in Correction Verification. Subsequent closeout edits
  change documentation only; application, tests, build configuration and locked
  dependencies remain identical to that commit.
- The final closeout reran the full suite: **1,444 tests in 27.960s**, with no
  failures/errors/skips. Data-model, value-dictionary, schema-presentation,
  cleanup-audit, catalog, privacy and whitespace checks pass. Earlier code review,
  exact replay, wheel, rebuilt backend, web and browser evidence retain their
  recorded source identities, timing and limits; these were not rerun as part of
  the documentation-only reconciliation.
- The two independent documentation reviews cover the initial filter and
  recovery chain, revision/layer refactor, P2 correction and connected owners.
  They confirm the historical no-gate/no-native-delivery states now point to
  the subsequent completed refactor, and the known literal-input ambiguity is
  attributed to the initial filter. No additional ownership or composition fix
  or broad restructuring was required. Publication identity for this final
  documentation reconciliation is its resulting Git commit and remote ref.

## Next Action

No required implementation or verification item remains for this correction.
Confirmed inactive task scratch was removed after evidence consolidation; the
existing private experiment owner retains bounded receipts and synthetic replay
evidence. Application recovery backup retention follows the storage owner.
The resulting Git commit and verified remote ref own publication identity.
Existing heuristic/recipient limits remain separate follow-ups.
