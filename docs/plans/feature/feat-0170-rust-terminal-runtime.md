# FEAT-0170: Shared Rust Terminal Runtime

- ID: `feat-0170`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `functional`, `design`, `ux-heuristic`
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Created: `2026-11-13`
- Updated: `2026-11-13`
- Authority: explicit human direction to proceed with migration and app integration, using the accepted core/runtime contracts.

## Goal And Acceptance

Development web and existing terminal CLI use an executable Rust core for terminal
scope/value validation, setup/service lifecycle, Unix manager IPC/stream and fixed
process inspection. Keep the same HTML/CSS/xterm, shared settings commit owner,
public HTTP/CLI semantics, IDs, limits, errors and independent PTY lifetime.

- Independent `rust/` workspace contains localbrain-core and localbrain-runtime;
  no Tauri/HTTP/SQLite dependency in business code.
- Bounded protocol1 control/stream/process-snapshot with strict envelopes and
  typed terminal/preferences errors; Node manager protocol2 uses Rust helper,
  retaining known protocol1 management without automatic live replacement.
- Python remains the thin HTTP/auth/CLI/common-TOML writer adapter. Rust validates
  terminal settings under the existing host-owned writer lock without reopening it.
- Reconnection/lease/ack/order/partial-input failure, exact-generation termination,
  path/ownership/no-start observations and four-pane/32-record/no-replay contracts
  remain valid, including current folder/status fields.
- Actual Rust build/unit/integration and old-to-new call-path checks precede native
  consumer acceptance. Unproved parity remains provisional; later Python product
  families stay explicitly inventoried rather than falsely declared migrated.

## Lanes And Trace

Contract/backend: rust workspace, terminal adapter and Node helper protocol.
Integration: existing web/CLI/settings and synthetic PTY/stream tests.
Docs: core/host contract, refactor phase/source map and current owners.
No native delivery claim until [FEAT-0171](feat-0171-native-terminal-integration.md).

- Spec: [SPEC-0170](../spec/spec-0170-rust-terminal-runtime.md)
- Run: [Run251](../run/run-20261113-251-rust-terminal-runtime.md)
- Evaluation: [Eval0167](../evaluation/eval-0167-rust-terminal-runtime.md); selected Terminal slice passes, full-backend parity remains provisional.
