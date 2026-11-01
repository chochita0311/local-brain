# RUN-228: Session Dashboard Cost And History

## Metadata

- ID: `run-20261031-228`
- Status: `passed`
- Feature: [FEAT-0020](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Parent PRD: [PRD-0004](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Active Spec: [SPEC-0020](../spec/spec-0020-usage-and-cost-fact-contract.md), bounded correction below
- Attempt: `1` cost correction; `2` compressed native history recovery; `3` container coexistence preservation
- Execution Profile: `fullstack-product`
- Surface Lanes: pricing/data → existing dashboard verification → docs
- Required Evaluators: contract, functional, scoped design/interaction
- Created: `2026-10-31`

## Attempt 1 Authorized Correction

The owner requests correction of incomplete cost and missing personal Codex
history, plus a durable guide preventing unrelated feature work from changing
existing behavior. Reuse the direct Usage and immutable-pricing contract; no new
product workflow, provider storage rewrite or shared-harness export is authorized.

Add cited Standard/Fast GPT-6.1 Terra snapshots effective October 26, 2026.
Use the existing startup correction to fill only previously unpriced exact-model
Codex observations with sufficient frozen evidence and the unavailable snapshot.
Preserve already priced rows, Usage IDs, tokens, source identity and Project
attribution. Keep unknown prices unavailable and the existing `Partial` indicator
for genuinely incomplete cost. Do not bump Session/Usage versions or reparse every
file for a catalog-only addition. Dashboard GET stays read-only and offline.

Trace missing history through current source files, source registry and provider
metadata read-only. Restore from original evidence only when it is located and
its authority is established; aggregate provider token counters do not supply
dated model/cache/output components. Missing evidence is an explicit unresolved
recovery dependency, not permission to fabricate usage or invent a second source.

Install a project-owned change-scope/regression guide and its AGENTS entrance
link. Preserve existing planning approvals, source reconciliation contracts,
design vocabulary and evaluation evidence limits. No visual redesign is needed.

## Evidence Plan

- Synthetic rate/date/tier/context boundaries and startup correction, including
  identity/attribution preservation, non-target rows and a second unchanged start.
- Existing Usage/parser/Sync/dashboard checks and repository-required checks.
- Synthetic browser inspection of complete, partial and unavailable cost plus
  source/range/metric continuity, including a narrow viewport.
- Read-only local history diagnosis; keep private paths, IDs and counts at the
  private evidence owner rather than copying them into shareable records.
- Final diff scope, owner-document links and generated artifact freshness.

## Attempt 1 Results (History Diagnosis Superseded)

- Pricing correction and project guide are implemented. The existing local web
  runtime has been updated and its saved settings verified unchanged.
- [Evaluation](../evaluation/eval-0020-session-dashboard-cost-and-history.md)
  records contract/functional/scoped browser PASS for delivered work, 1,492 passing
  tests and partial request coverage. Existing `Partial` semantics remain intact.
- The project guide is linked from AGENTS and the docs map. It requires declared
  scope, preserved contracts, shared-consumer checks and a final diff/runtime
  comparison; it does not claim automatic prevention of all future regressions.
- Attempt 1 incorrectly treated absent plain JSONL paths as unavailable originals
  and requested a backup. Attempt 2 found native compressed originals and withdrew
  that diagnosis and recovery block. Metadata/counters alone remain insufficient
  to reconstruct direct usage; the recovered archives supply the actual events.
- No commit, push, shared-harness export or native app rebuild was performed.
  Task-owned temporary artifacts are removed after verification; the normal web
  runtime remains running independently of task scratch.

The earlier backup-location request is withdrawn. Current recovery evidence and
human-review needs follow attempt 2 below.

## Attempt 2: Compressed Native History

The owner identified a missed source form: historical Codex originals can remain
as `.jsonl.zst` in the registered source directory. The earlier absence/recovery
block was based on a plain-JSONL-only search and is withdrawn. Preserve that
attempt as evidence of the incomplete diagnosis, not current source availability.

Resume the original history correction within native capture and direct Usage
contracts. Stream Codex `.jsonl.zst` using the Python Zstandard file API (its
declared backport on supported older Python); do not extract, rewrite or remove
provider originals. Prefer a live plain file over its same-path compressed copy.
Keep native identity/line ordering and replay filtering independent of compression.
On plain-to-compressed replacement preserve Session IDs, pins, direct Usage IDs,
frozen pricing/Project evidence and references; bad/truncated archives must not
retire their last valid normalized owner. Keep source failures isolated.

Advance the Codex Session revision so an older scanner cannot treat imported
archives as missing files and delete their normalized history. Usage normalization
and Claude capture remain unchanged. This source revision is a compatibility
guard, not permission to reprice existing history. Verify old-runtime refusal,
incremental repeat Sync, both Codex source identities and unchanged non-target
data. Apply ordinary source-level synchronization to the affected local source
and verify recovered monthly Usage in the current web runtime.

## Attempt 2 Outcome And Review

- The earlier missing-originals diagnosis is corrected: compressed native files
  were present under the registered source. Discovery and binary replay peeking
  both needed codec support. No separate backup is needed for those originals.
- Codex plain/compressed discovery and streaming reads are implemented. Native
  identity, replay exclusion, source separation, curated IDs/pins and frozen Usage
  remain intact. Codex revision 13 connects archive admission to existing
  older-runtime refusal; the Usage normalizer and Claude candidates are unchanged.
- Eight new archive tests and the final full **1,500-test** suite pass. An isolated
  installed wheel passes import, full startup, compressed Sync and dashboard
  rendering. A minimal PyInstaller executable reads the same compressed fixture;
  desktop build metadata explicitly collects the codec. The full native app was
  not rebuilt/replaced by this correction.
- The normal web runtime was gracefully restarted with unchanged settings. Normal
  Sessions Sync completed every configured source with zero failed files. The
  personal Monthly dashboard now shows June–October; Cost and Tokens retain that
  source/month scope at wide and narrow widths, with complete eligible price coverage.
- Snapshot-backed comparison preserves every prior Usage fact except its permitted
  import observation time, prior Session identities, pins and immutable price
  snapshots. Repeated collection preserves the recovered cold archive Usage and
  freshness fingerprints exactly. Original compressed-file sizes, mtimes and
  content hashes are unchanged. Private quantities and locators remain at the
  configured private evidence owner.
- The project guide now explicitly requires checking compressed containers before
  declaring history absent. No automatic guide-effect claim, new shared-harness
  promotion, commit or publication is inferred.

Both reported dashboard issues are repaired in the current web runtime. Human
review is the visible recovered history and project guardrails; the earlier
backup-location request is withdrawn. Task-owned recovery/test/build artifacts
are removed after verification; no normal runtime depends on them.

## Attempt 3: Container Coexistence Preservation

The owner's follow-up asks whether reads use normalized DB state and whether
plain/compressed coexistence causes duplicates. Dashboard Usage and ordinary
Codex detail read their stored projections; decompression occurs during Sync.
Discovery selects only the plain member of a same-directory, same-basename pair.
This priority compares neither content nor mtime and is not global content deduplication.

A synthetic reverse-transition check exposed a preservation gap in attempt 2:
when plain JSONL reappeared after archive ingestion, pre-parse stale reconciliation
deleted the archived projection before reimport. Totals were not doubled, but pins
and frozen Project evidence were lost. Attempt 2's verified plain-to-archive
preservation did not establish archive-to-plain preservation.

Keep the existing selection priority and source-scoped native identity. Retain
the prior owner transactionally for either container transition, reject changed
native identity, and preserve prior facts on read failure. Advance only the Codex
Session revision to 14 so older admitted collectors refuse before lifecycle writes;
Usage normalization, Claude capture, pricing and UI selection remain unchanged.
Verify both coexistence/removal, failures, empty evidence and repeated collection,
then deliver to the normal web runtime and check retained data. At entry,
evaluation was pending; no actual user pin/frozen-data loss is inferred from the
synthetic finding.

## Attempt 3 Outcome And Review

- Bidirectional container retention is implemented for Codex only. Five new
  reverse-transition checks cover coexistence, removed archives, read failure
  and recovery, changed native identity and confirmed-empty projections. All
  13 archive checks and the required full **1,505-test** suite pass. Existing
  plain priority, pricing, Usage normalizer and Claude capture are preserved.
- The current process was reidentified as the same checkout's ordinary web
  server before any restart. A guarded graceful restart preserves settings and
  source registration. Normal Sessions Sync completes every configured source
  with zero failed files; admitted Codex files carry revision 14. A packaged
  native app was not rebuilt or replaced.
- Read-only comparison against a consistent pre-restart snapshot finds no
  changed/missing prior Usage facts except permitted import time, no lost or
  reidentified prior Sessions/pins, and no changed immutable price snapshots.
  Source-scoped native-identity groups and tracked plain/archive pairs contain
  no duplicates. Original compressed files retain size, mtime and content hash.
- Browser checks return successful personal Monthly Cost and Tokens pages for
  June–October, no `Partial` label, and a successful archive-backed Session detail.
  The in-app guide now explains DB reads and same-path pairing. No template,
  style or interaction implementation changed; prior viewport observations are
  historical evidence rather than a new physical-input claim.
- Evaluation is same-author PASS for this bounded web/source correction. No
  further product decision is introduced. Review the plain-priority rule:
  content differences do not trigger freshness comparison or merging, and
  personal/company source identities remain separate. Task-owned scratch and
  the temporary recovery snapshot are removed after final checks.

## Follow-up Causal Verification

The owner asks why Usage could disappear despite already being stored. A
temporary synthetic old-discovery reproduction verifies that plain-to-Zstd
replacement can make stale-path cleanup delete the Session and cascade-delete
its Usage while the archive remains and the scan reports no file failure.
[Evaluation](../evaluation/eval-0020-session-dashboard-cost-and-history.md#follow-up-why-stored-usage-could-disappear)
records the bounded evidence. Exact historical execution time/binary and an
introducing feature commit remain unestablished. The delivered compression fix
does not change general missing-file reconciliation into independent permanent
Usage retention. No new product policy or code change is implied by this diagnosis.

That describes RUN-228's boundary. The owner subsequently approved broader
[retained Session history](../feature/feat-0154-retained-session-history.md),
implemented and evaluated in [RUN-229](run-20261031-229-retained-session-history.md).
Missing accepted originals now preserve collected Sessions and their descendants;
the earlier causal reproduction remains evidence of the previous lifecycle.

## Change-Impact Guide And Generalized Source Scope

The owner clarified that prevention must support complete product development:
necessary dependent edits belong in the same work, and already agreed changes
across features proceed without reopening approval. The
[project guide](../../policies/project/change-scope-and-regression.md) now
classifies required coordinated edits, approved behavior changes, unexpected
differences and uncertain causes. It requires causal diagnosis, preserves
unrelated work, permits supported targeted reverts and reserves human decisions
for consequential new unresolved choices under the existing workflow. Development
commands, approval routing and detailed Session/Usage contracts remain with their
existing owners; AGENTS, the docs map and Developer Guide route to this guide.

Codex compressed capture applies recursively within every registered Codex Session
root, including separate personal/company or custom roots. It is not tied to one
home, date range or recovered file. The same-directory, same-basename plain/Zstd
selection and source-scoped native identity rules remain explicit; no global
content deduplication or discovery outside registered roots is implied. The
[installation owner](../../policies/project/installation-and-storage.md#native-session-compression-and-recovery)
retains version-scoped upstream compression findings separately from the
unestablished actor and time of a past local compression pass. An earlier reply's
unqualified statement that compression timing had not been checked was too broad;
the unresolved point is the actual local execution history, not the existence of
the documented upstream mechanism. Neither dashboard symptom alone establishes
that another feature change caused it.

The combined source tree's final review, verification and publication boundary
are recorded in [RUN-229's source closeout](run-20261031-229-retained-session-history.md#final-source-closeout).
