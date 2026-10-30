# REFACTOR-0002 Implementation And Runtime Verification

## Log Type

- Type: `Wrap-Up`
- Date: `2026-10-30`
- Related track: [REFACTOR-0002](../refactor-0002-ingestion-layers-and-session-revisions.md)
- Scope: numeric Session revisions, forward-only admission, ingestion layers,
  installed package, rebuilt native backend and local web rollout.
- Status: `complete`; implementation and required verification passed.
  Implementation commit `f8fb80d80cb2b0d9323f2679525e59caeb39fff3` and comparison
  tag `refactor-0002-semantic-baseline` were pushed; remote refs matched on
  `2026-10-30`. Subsequent documentation receipts do not change that code identity.

## Summary

The owner approved completing the refactor and rebuilding the app. Current
executables have one current parser per provider; the database stores the
revision of the results, not executable parsers or instructions to restore Git.
An already-built app retains its own frozen code until it is rebuilt/replaced.

The earlier incident and parser fix remain owned by
[RUN-227](../../run/run-20261029-227-codex-empty-page-control.md).
The separate Session freshness field originated in
`83e28166466101c93fa1f9bd8c877177ab2b0080` on `2026-08-24`, when Session
repair was separated from Usage repair to avoid replacing unrelated derived
lanes. Its former inequality check treated older and newer tokens alike; this
track adds ordered admission instead of retaining historical parser code.

RUN-227 recognized the exact standalone empty-page control and demonstrated
mixed-build replacement of newer normalized results. It did not identify the
historical writer with a write audit. This refactor does not reinterpret that
limit or change the existing text-based filter's authored-input ambiguity.

## What Changed

- `source_files.session_contract_version` is nullable positive `INTEGER`, checked
  by SQLite storage type as well as value. Codex starts at `12`, Claude at `7`;
  the numbers are provider-specific and are not compared across providers.
- `ingest/contracts.py` owns DTOs, short numeric Session revisions and unchanged
  Usage freshness tokens. There are no v1/v2/... parser implementations kept for
  runtime selection. Runtime code retains old descriptive Session strings only
  in the explicit legacy conversion boundary; synthetic compatibility fixtures
  and historical documentation retain their evidence.
- Updated runtimes reject any higher stored Session revision before source
  upsert, discovery, stale cleanup or result replacement. Force cannot bypass
  rejection; independently registered safe peers still complete. Same-source
  reconnect checks before reading with an older parser or nulling revision markers.
- Null or lower Session revisions require real Session/skill repair. A current
  Usage contract does not prove the Session result current and Session-only
  repair does not replace or reprice Usage.
- Startup validates exact known legacy tokens before schema writes, makes a
  verified private migration backup, then rebuilds source-file storage inside a
  savepoint. IDs, mappings, other fields, FKs, uniqueness and explicit indexes
  survive. Unknown strings stop; unsupported column/FK/implicit-unique/check/
  timing shapes and unknown incoming file FKs refuse replacement, including
  case-insensitive FK target spellings that could otherwise cascade child data. An interruption after dropping the old table
  rolls back to the complete original table.
- Provider reconstruction, candidate/skill extraction, synchronization and
  projection persistence now have separate owners. Package initializers are
  empty; contracts and coverage consumers do not import provider algorithms.
- Current owner docs, value-dictionary path references, packaged schema
  presentation and schema audit evidence were reconciled. Existing useful
  historical records and the earlier refactor's completed scope are preserved.

The owner explicitly chose rebuilding/replacing old app copies. No trigger/UDF,
exclusive writer-owner protocol or retroactive compatibility framework for
unmodified old executables was added. An integer CHECK is not a claim that all
writes from old binaries are safely rejected.

## Source Mapping

| Baseline owner | Current owner and responsibility |
| --- | --- |
| `ingest/common.py` parsed classes | `ingest/contracts.py`: seven parsed/call DTOs |
| `ingest/common.py` evidence helpers/constants | `ingest/evidence/reference_candidates.py`: URL/Markdown and approved tool/result candidates |
| Remaining generic common helpers | `ingest/common.py`: identity, JSONL, text/title and existing maintenance classification |
| `ingest/codex.py`, `ingest/claude.py` | `ingest/providers/`: native algorithms, replay/config and pricing calls |
| Flat `skill_loads.py`, `skill_usage.py` | `ingest/evidence/`: unchanged collection and matching algorithms |
| Scanner file discovery/repair orchestration | `ingest/sync/sessions.py` |
| Scanner Session/Usage persistence, stale/empty cleanup, parent propagation | `ingest/sync/session_store.py` |
| Scanner folder/file/PDF/Notes collection | `ingest/sync/contexts.py`, with facade settings passed explicitly |
| Scanner source/file/workspace/search/structure operations and revision admission | `ingest/sync/storage.py` |
| Scanner cancellation ContextVar and safe progress callback | `ingest/sync/control.py` |
| Registry/adapter composition, public scans, reporting, outer transactions | Reduced `ingest/scanner.py` |

Public `scan_*` signatures remain. Internal consumers and tests import/patch the
actual new owner, with no module-proxy compatibility framework. Per-provider
Session and Usage metadata imports are lightweight; Usage token values did not
change when their owner moved.

## Behavior / Parity Notes

- Overall parity versus the initial baseline: `Intentional deltas present`.
  Numeric storage and forward-only refusal intentionally change behavior.
- Structural comparison target:
  `5e23084a2be9c8e2869fef9b011f3d55583e3e7b`, tagged
  `refactor-0002-semantic-baseline`. This is the tested post-semantic,
  pre-extraction snapshot, committed separately; main history was retained.
- The original pre-work baseline is
  `81590bdc3d9857eca71d5d982dbb1354a3a49215`.
- Steps 3–4 form one compared structural batch. All 136 mapped units match after
  only declared module qualification and Context configuration injection;
  another 98 shared non-ingest modules match after import changes are removed.
  The mapped units include all 61 scanner and 43 common units plus provider/skill
  algorithms and relocated metadata. DTO fields, SQL predicates and values,
  return/report shapes, call order, savepoints, callbacks and failure branches
  remain unchanged in those units.
- Two safety deltas discovered after that snapshot are reviewed separately:
  reconnection admission before marker invalidation, and refusal of unrecognized
  migration shapes. They are not counted as behavior-preserving extraction.
- Existing Session-source outer transactions, grouped Context collection, caller
  transactions for direct Context scans, ordinary file-error handling and the
  single cancellation context remain. No per-file savepoint, commit or new lock
  was introduced by extraction.
- Empty-session cleanup still requires the current owner and all tracked siblings
  to be empty. Meaningful/skill-only siblings prevent cleanup. Historical Usage
  prevents retirement after eligible stale conversation/search clearing.
- No tag heuristic, native counterpart precedence, phase/turn logic, reference
  admission, skill meaning, pricing, source-candidate or maintenance rule changed.

## Validation

- Original baseline: **1,426 tests passed**.
- Numeric-revision snapshot: **1,433 tests passed**, then **1,433 passed again**
  from its separately committed comparison worktree.
- Post-extraction full suite: **1,435 passed**; expanded candidate **1,436 passed**.
  Final candidate: **1,437 passed in 28.724s**, with no failures/errors/skips,
  including interruption after table drop and case-insensitive incoming-FK refusal.
- Final focused checks: nine migration tests and 27 Session-sync tests
  passed. Higher revision refusal covers Codex and Claude, normal and forced
  scans, missing native files, pins, events, Usage and safe peer completion.
  The source-profile suite passed 18 tests including rejected reconnect and
  preservation of config, journal cleanup, paths and the higher marker.
- Compilation/imports: source application and new layers import successfully;
  structural normalized-AST comparison passes. Python 3.9 syntax parsing passes
  for all 52 changed Python files; execution uses Python 3.11.15. Tests were updated to patch the
  actual owner; initial import/mock wiring failures were fixed before the passing
  suite. Intermediate schema-doc digest failures were resolved by regenerating
  owners and consumers; no unrun check is counted as a pass.
- Installed wheel: built offline and installed into an isolated task-owned
  directory; app/CLI and provider/evidence/sync imports use that installation.
- Rebuilt native app: PyInstaller/Tauri Apple Silicon build completed after
  loading the documented Rust environment. The first attempt stopped at missing
  `cargo` PATH before replacing the distributed app. Signing verification and
  private build-path inspection passed; ZIP and matching SHA-256 were produced.
- Frozen backend: 15 embedded modules match current source code objects, including
  the migration and reconnect guards. Old flat provider/skill modules are absent.
  Against synthetic native input and a genuine pre-migration DB, startup converts
  known strings to integer revisions. An explicit null-marker repair reports one
  imported file, retains only the authored question and preserves exact Usage,
  proving fresh packaged parsing excludes the control. Ordinary Sync completes;
  a higher revision then refuses missing-file cleanup while preserving Sessions, events, Usage, pins and source-file rows.
  Authenticated loopback health passes; owned backend exits `0` after shutdown.
- Local web rollout: no active Sync/maintenance work or old native process was
  present before restart. Migration backup exists; row-by-row comparison shows
  only Session revision values changed in source-file rows. Session, activity,
  Usage, pin, organization-link, skill and reference signatures remain identical.
  `integrity_check`, `foreign_key_check` and migration contracts pass. The restarted
  final server is healthy, inherits no task temporary directory, and writes no
  logs into task scratch.
- Chrome: the reported Session route returns `200`; the first conversation is
  authored input, no standalone generated control row remains, no JavaScript
  errors or horizontal overflow were observed. Browser context was closed.
- Owner/generated checks: data-model ownership, schema presentation, value
  dictionaries, cleanup audit, compilation, whitespace and all 12 local Mermaid
  diagrams pass, as do catalog, relative-link and privacy checks. The final bundle
  schema/value JSON matches source and its ZIP passes SHA-256 verification.
- Independent documentation reviews: docs-structuring identified a missing local
  admission predicate and misowned migration refusal/rollback details; both were
  fixed in their existing policies. Docs-shaping identified that the first frozen
  smoke could skip parsing; the new null-marker/import assertion closes that gap.
  Its separate-worktree wording clarification was also applied. The primary
  reconciled every finding against source and retained stable content. No broad
  documentation restructuring was needed.

## Risks / Limitations

- These checks do not establish universal parsing correctness. Existing exact
  text heuristics can also recognize an identical standalone user-authored block;
  authored framed/fenced/adjacent content retains its existing behavior.
- Existing non-null page, CRLF, title-layout and unrelated navigation follow-ups
  from the earlier parser work remain outside this refactor. Input format
  compatibility remains supported by the current parser; old output writers
  must be replaced.
- A revision number must identify one provider result contract across branches.
  Reverting a rule requires a new higher revision, not reusing an older number.
- No measured performance improvement, recipient installation, WKWebView visual
  acceptance, live external-provider test, Developer ID signing or notarization
  is claimed. Native backend smoke and local Chrome evidence have their stated
  scopes. No private content was uploaded or sent to teammates.
- Publication identity is the final implementation commit and the separate
  semantic-baseline tag; Git refs and the final response record push verification.

## Next Action

No required implementation, verification or publication item remains in this
track. Existing parsing/recipient limits above remain separate follow-ups.
All task-owned comparison worktrees, baseline copies, synthetic databases,
installed test wheels, browser tooling/profiles, screenshot and raw logs were
removed after their evidence was consolidated and no open files remained.
Runtime backups and the rebuilt distribution retain their existing storage/build
owners; they are not disposable test scratch.
