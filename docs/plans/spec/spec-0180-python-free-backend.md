# SPEC-0180: Python-Free Backend And Application Layout

## Metadata

- ID: `spec-0180`
- Status: `approved`
- Run: [RUN-261](../run/run-20261118-261-python-free-backend.md)
- Attempt: `1`
- Parent Feature: [FEAT-0180](../feature/feat-0180-python-free-backend.md)
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Surface: backend, CLI, shared SSR/web assets, Tauri and delivery
- Execution Profile: fullstack-product
- Surface Lane: core/services → host/screens → delivery/retirement
- Required Evaluators: contract, design, functional, ux-heuristic
- Created: `2026-11-18`
- Updated: `2026-11-19`

## Fixed Implementation Contract

User approved end-to-end implementation of the final Python-free target and
apps layout, including delegated implementation/audit/verification. Preserve
existing owner contracts and actual source; no new user-facing scope is inferred.

- Root Cargo workspace contains `crates/core`, independent Terminal
  `crates/runtime`, native inference `crates/models` and
  `apps/api`. The Tauri crate remains independently built under `apps/desktop`.
  Native models are a separate dependency/lifetime boundary; no Python binding.
  The user's2026-11-19 naming refinement shortens directories only; Cargo
  package/import names and runtime/binary identities keep their `localbrain` prefix.
- The API is a persistent Tokio/Axum Rust host; HTTP/WS/CLI adapters call shared
  core directly. Blocking SQLite/file/inference work leaves the async reactor.
  Keep exact loopback/token/origin/path/feature boundaries, ready/shutdown/parent
  lifetime and optional service startup/stop ordering.
  Web `serve` prints a ready/listening banner including request-log state on stderr
  and logs requests by default. Each access line includes the client socket
  address, method, actual encoded path, HTTP version, status and time to response
  headers. Paths include parameter values and are shown for unmatched requests.
  `--no-access-log` disables request logs, including when an older alias also
  supplies compatible `--access-log`. Desktop stdout JSON/lifetime and
  query/header/body privacy remain required; console I/O errors must not alter
  HTTP responses.
- Existing HTML/CSS/JS/content moves to `apps/web`. Native MiniJinja renders the
  same templates/context and native Markdown preserves safe link/math/diagram/
  evidence semantics. Rust compatibility methods are allowed; no interpreter,
  new frontend framework or duplicated app screen implementation.
- `backend::Config` owns explicit paths/edition/features; `BackendError` owns
  code/status/detail. Services take explicit config/connection, not global mutable
  per-request environment. `db::connect/initialize/row/rows` supply the shared
  connection boundary and preserve WAL/FK/busy timeout and ordered migrations.
- Native preferences reuse the same semantic/commit implementation with native
  TOML1.0/zone syntax adapters in-process. The lossless ordered representation
  retains arbitrary integers/nonfinite/date precision and existing refusals.
  Source registry uses the same codec but its own restricted schema/IDs.
- Shared operation guard remains reentrant on the same thread, nonblocking
  between writers and inherited-description-safe where a purposeful child is
  required. DB/registry/recovery retain explicit old transaction boundaries.
- Native model crate uses original pinned safetensors and Rust tokenizer/Candle
  inference, lazy offline loading and explicit known-file installation. A changed
  numerical runtime has a distinct identity and cannot reuse an incompatible
  index silently. Preserve every independent pinned asset/fingerprint; no model
  quality claim from a deterministic fake or a same-dimension vector.

The workspace remains edition2021/Rust 1.90. Dependencies are pinned and locked;
actual compatibility must be tested with that compiler. Primary selects and
verifies APIs against official/versioned source. No package/version upgrade is
justified solely by newer documentation.

## Comparison, Verification And Retirement

Freeze actual1973-file dirty source over HEAD e6958df before moves. Private old
source/fixtures remain immutable; new runtime never falls back to it. Reconcile
all static/dynamic route registrations, CLI entrypoints, feature/edition matrix,
startup jobs, templates and package assets to concrete Rust functions/tests.
Port before deleting corresponding producers/consumers; audit every deletion.
The user's follow-up explicitly retires obsolete standalone Python research,
comparison, compatibility launchers and dependent tests. These unadmitted tools
are removed rather than reimplemented; their former procedures/evidence are
historical records. Current native product behavior and build/check tools remain.

Use old-shape migration/idempotence/fault cases, exact value/error/byte tests,
synthetic ingestion/Usage/reference/retrieval witnesses and browser/native flows.
Renew actual app/source/asset/target identity after material changes. Separately
verify no shipped Python/interpreter/process or unsupported fake healthy path.
Independent review of frozen whole scope plus repair deltas is required for the
data/concurrency/retirement risk; worker returns do not accept completion.

Fullstack surface lanes are every existing admitted page/control and shared
loading/error/recovery state. Design constitution/functional/interaction checks
preserve DOM/layout/assets, focus/history/readiness and local authority; no new
visual design is selected. Native/physical/minimum-OS results remain distinct.

## Open Points And Failure Policy

No new user decision is needed for the selected result. Evidence gaps (including
real numerical model and minimum-OS checks) are unresolved checks, not passes.
Unknown legacy shapes refuse without destructive repair. Missing native coverage
or delivery blocks whole completion; no placeholder route/disabled old feature,
exhausted allowance or partial Rust slice may substitute for that outcome.

## Continuity Notes

- `2026-11-19`: Run261 passes [Eval0177](../evaluation/eval-0177-python-free-backend.md)
  for native implementation, Python-free delivery, regression/performance and
  retirement on the tested host. Spec remains approved. Original POSIX file and
  directory fsync boundaries are preserved after correcting Apple's unintended
  stronger sync_all cost; no cache, durability or readback shortcut is accepted.
  Declared platform, real large-model and exhaustive-parity evidence limits are
  explicit in the evaluation rather than converted into passes.
