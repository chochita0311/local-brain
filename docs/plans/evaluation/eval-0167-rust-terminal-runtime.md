# EVAL-0167: Shared Rust Terminal Runtime

- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`; the selected executable/control paths pass, with limits below.
- Feature: [FEAT-0170](../feature/feat-0170-rust-terminal-runtime.md)
- Spec: [SPEC-0170](../spec/spec-0170-rust-terminal-runtime.md)
- Run: [Run251](../run/run-20261113-251-rust-terminal-runtime.md)
- Profile: `fullstack-product`; contract/backend, integration, design and interaction evaluation.

The first Terminal Rust slice is implemented and used by product web/CLI/native
adapters. Core has no Tauri, HTTP, database or TOML-writer dependency. Python
continues to own HTTP/WS/CLI transport and the common settings commit. Node owns
PTY/VT/input/checkpoints. The common HTML/CSS/xterm workspace is preserved.
This passes the bounded Feature; whole-repository migration parity is provisional.

## Source To Target And Preserved Consumers

| Previous owner / consumer | Implemented target and distinguishing evidence |
| --- | --- |
| Python runtime scope, setup, dependencies, service start/stop/restart and RPC | Rust `files`, `payload`, `service`; strict Python control adapter. No-start observations, offline cold create, malformed/cold-invalid requests, live→stopped validation, idempotency/conflict and selected legacy management are exercised. |
| Python process helper / Node termination inspection | Fixed Rust `process-snapshot`, bounded C/UTC `/bin/ps` and birth/session fields. No arbitrary process command or shell is exposed. Short rows are skipped; malformed numeric fields fail. |
| Terminal settings / shared preferences consumers | Rust typed snapshots, paths and patches under the existing Python operations lock/revision transaction. Python alone parses/commits TOML, preserves unknown values and retains409 preference errors. Repair works independently of broken runtime/cache. |
| HTTP/WS, Python CLI and app-less management | Existing public routes and CLI shapes use the same core. One control request or streaming view per helper, bounded JSON, exact acknowledgements, serialized lease publication, partial-input warning and detach/reaping. Cached management clears obsolete app overrides and survives app removal. |
| Manager1 and current UI | Known protocol1 inspection/validated stop retained; new work requires manager2/helper1/checkpoint xterm6-v3/Unicode11. Additive creation-cwd/activity fields, tab IDs, max4 panes/max32 records, group derivation, terminal IDs and unknown fallback remain. No live upgrade/replay occurs. |
| Generic cache recovery | Rust exact preview receipt, control/use leases, immutable payload identity and parent-link rejection. Active, unknown and loss-marked owners stay protected; other eligible caches may still clear. |

The source baseline and candidate files were frozen before challenges. Product
imports no longer select the old Python runtime/process helper. They remain
explicit legacy parity fixtures and are excluded from native packaging. The
representative create path is host envelope→Rust authoritative stopped-state
validation/lock→verified payload→Node idempotent create→unchanged public result.
Settings has one commit owner, and stream has one lease/ack owner; no second
business implementation was added to Tauri.

## Verification

- Rust formatter and 11 unit/contract tests pass on Rust 1.99.1. The workspace
  declares 1.90 / edition 2021; that minimum compiler was not installed or tested.
  Cargo-clippy is unavailable, so no Clippy success is claimed.
- Final real Rust/payload/PTY suite: 14 tests pass. Cases include offline launch
  without PATH Node/npm/Python; cold/live lexical cwd parity; invalid requests
  before bootstrap even across a deterministic live→stopped transition; exact
  creation retry; hide/split/last-close recreation; stream acknowledgement,
  takeover/detach/reconnect; exact termination; build mismatch management;
  cross-scope symlink refusal; exact retirement receipt and foreign use lease;
  app-less stale-environment management; incompatible width rejection; and an
  actual saturated stdout pipe retaining mandatory input-failure warning while
  releasing ownership before the reader resumes. The14 names map to compound
  cases rather than 14 exhaustive feature assertions.
- Final common browser: 54 checks pass on real Rust/PTY. Node renderer/state/input:
  73 tests pass. Terminal asset check passes. Settings, native authority, builder
  and host error tests are included in the full Python regression.
- Full Python discovery: 1678 tests, PASS with 47 optional process tests skipped.
  The 14 real Rust cases are separately enabled as above. The frozen legacy
  reference previously passed 55 tests including 33 actual PTY cases; its Node
  source was unchanged afterward. These are separate scopes, not a combined
  exhaustive parity count. All 4 builder regressions and host-environment cases
  are included in this full run. The later public-cache refusal branches also
  pass the focused7 host/auth suite against actual Rust helpers.

Initial non-elevated full-suite attempts were blocked by local listener/process
permissions; the correctly permitted full run passes. Wrong generic npm/asset
CLI invocations were corrected to configured commands and are not test failures.
Native package/build evidence is owned by [Eval0168](eval-0168-native-terminal-integration.md).

## Review Findings And Limits

A fresh read-only core challenge found parent-link retirement, stale writable
publication, mismatched-build selected stop, contradictory target and process-row
issues. Primary repaired them. Informed followups found retained raw-RPC target
bypass, mandatory warning queue loss, lexical cwd mismatch and a cold-validation
race. Shared validators, serialized publication, a separate failure slot/exit75,
lexical normalization and locked stopped-branch revalidation address those cases.
The final 13-file informed recheck found no material residual in those repairs;
it executed no code and is not independent acceptance. A separate native review's
first packaging findings were independent; later core discussion was exposed to
other review findings. Primary owns all adjudication and final semantic review.

Final primary inspection additionally found that the Python control/stream child
inherited the full host environment. It now receives only launch keys and trusted
terminal/HF/XDG paths, retaining protected-cache checks without app credentials.
An actual child and an async stream-spawn regression verify credential exclusion,
path retention and unchanged parent authentication; the 7 focused host/auth cases
pass. The informed four-file recheck found no residual in this change, without
execution or rebuilt-app approval. Primary then added actual Rust refusal cases
for private destinations under each of the four configured public-cache roots.
This repair is distinct from the earlier challenger's findings.

Native physical input/focus, real Mac sleep, minimum-OS hardware, recipient,
long-duration/resource budgets and a performance advantage over Python are not
established. No schema/data/model/source migration occurred. Session ingestion,
retrieval/models, Usage, database/repositories and other Python families remain
outside this implemented slice, as tracked by
[Refactor0006](../refactoring/refactor-0006-rust-core-transition.md).
