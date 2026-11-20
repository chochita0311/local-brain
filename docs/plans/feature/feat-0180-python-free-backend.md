# FEAT-0180: Python-Free Backend And Application Layout

## Metadata

- ID: `feat-0180`
- Status: `passed`
- Type: `product`
- Surface: `mixed`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, design, functional, ux-heuristic
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Created: `2026-11-18`
- Updated: `2026-11-19`
- Authorization: user explicitly selected the proposed apps layout and requested completing backend Python removal, cleanup, feature/port/deletion verification with subagents in the current continuation. This is implementation authorization within that stated result; no new feature admission, user-app replacement or publication.

## Goal And Acceptance Contract

Run the existing admitted LocalBrain functionality through native Rust backend
and CLI, with shared web assets and a distinct Tauri application. Backend
runtime and delivered artifacts require no Python. The
[selected final target](../project/python-free-backend-target.md) owns the exact
zero-Python, data/feature preservation, performance and delivered-runtime exit.

1. Move server, shared screens and native shell to `apps/api`, `apps/web`,
   `apps/desktop`; shared Rust crates live under `crates/`. Complete all actual
   build/resource/discovery/test/doc consumers of these paths.
2. Preserve every currently admitted route/CLI/job/service and its edition,
   feature, auth/origin, error, empty/loading/recovery and data contracts. The
   inventory is a checklist, not permission to omit large feature families.
3. Port settings/TOML/zone, SQLite schema/compatible migrations/recovery,
   registration, ingestion, Usage, readers/resources, search/models and admitted
   development-web features. Model-free use and explicit-only model work remain.
4. Remove Python runtime/adapters, PyInstaller and obsolete bridging/packaging
   after verified replacement. Retain an immutable private old reference for
   comparison and explicit test/build tooling when useful. Deletion requires
   consumer/dependency audit, not merely an unused-name search.
5. Ordinary Rust HTTP requests call Rust services directly. Preserve concurrency,
   private atomic publication and readback semantics while eliminating per-call
   Python/Rust codec/process overhead. Measure old/new calls and user surfaces.
6. Native model execution preserves pinned assets/tokenizer and explicitly
   reconciles numerical runtime/index compatibility. No Python-worker exception,
   silent weight/model replacement, unrequested download or suspended trial.
7. Actual source/CLI/package/web/native delivery, declared Rust minimum, behavior,
   migration/failure/concurrency, source-to-target coverage and independent
   cleanup/deletion review pass before whole-backend completion.

## Scope, Lanes And Dependencies

Prerequisite179 supplies bounded settings evidence; it does not fulfill this
Feature. Primary owns architecture, contracts, integration and final decision.
Independent evidence workers first establish current host, storage and model
contracts. Bounded implementation workers own disjoint native codec, persistence/
source and model modules; primary owns host/web/CLI integration and remaining
families. Later worker packets follow the fixed exports and ownership map.

Core/transaction → native services → HTTP/CLI/rendering/desktop → packaging and
retirement are explicit checkpoints within this authorized result. No checkpoint
is whole completion. Each includes old/new values/errors/effects and named tests.
After source freeze, independent review and bounded verification inspect the
actual candidate, deleted-code map, delivered processes/assets and residuals.

Out: current user data/source mutation, collection/model downloads or jobs on
user content, live app/service replacement, Windows support claim, frontend/VT/
database/model-weight redesign, suspended feature activation, commit/push.

## Harness Trace

- Active spec doc: [SPEC-0180](../spec/spec-0180-python-free-backend.md)
- Active run: [RUN-261](../run/run-20261118-261-python-free-backend.md)
- Execution profile: fullstack-product; existing screen contracts preserved
- Latest evaluator report: [EVAL-0177](../evaluation/eval-0177-python-free-backend.md), PASS with explicitly scoped evidence gaps; all prior results retain their original scope
- Latest fix note: none

## Completion Boundary

Run261/Eval0177 accepts the complete native implementation, Python runtime
retirement, approved layout and delivered regression/performance result on the
tested Mac. Actual Rust 1.90,412 tests, packaged app/API/CLI, Python-denial controls,
native-window16, browser26 and publication-fault6 checks pass. No Python model
worker exception or per-call bridge remains. Strict exhaustive behavioral parity,
physical minimum-OS/other-platform/input/soak, real large-model quality and separate
Feature177 acceptance retain Eval0177's explicit limits. This result performs no
installed-app replacement, user-source operation, activation or publication.
