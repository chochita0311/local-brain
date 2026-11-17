# SPEC-0170: Shared Rust Terminal Runtime

- Status: `approved`
- Feature: [FEAT-0170](../feature/feat-0170-rust-terminal-runtime.md)
- Run: [Run251](../run/run-20261113-251-rust-terminal-runtime.md)
- Profile: `fullstack-product`; contract/backend→host integration→evaluation/docs.

Implement the accepted [core/host contract](../project/rust-core-and-host-contract.md)
and [runtime contract](../project/app-independent-terminal-runtime-contract.md).
Rust1.90/edition2021, built with available1.99.1, uses exact locally locked
serde1.0.229/serde_json1.0.154/sha2.10.9/libc0.2.191, without upgrading Tauri.

Core owns scope/private locations, manager socket/deadlines/generation, status,
prepare/start/create/stop/restart, settings typed value/path validation, leases,
stream backpressure and process identity snapshot. Executable owns only mode and
JSON stdin/stdout. Host paths are trusted config, never browser-supplied scope.
No logs on control stdout or credentials in manager/helper environment.

The Python common writer still owns TOML/revision/operations.lock and merges a
validated Rust patch while preserving unknown fields. Settings remain repairable
without a healthy terminal cache or payload. Retained low-level manager consumers
may use a strict internal manager.rpc envelope (closed manager method set) through
the same Rust client; no arbitrary RPC HTTP route or process command is added.

Node retains PTY/headless/checkpoint/input/ownership semantics, advertises protocol2,
and calls only the fixed Rust process-snapshot command. Dev source manager
fingerprint and packaged manifest identity remain distinct. Legacy protocol1 may
be listed/stopped with verified scope; new work cannot silently upgrade it.

Preserve409 preferences, terminal error mapping, exact confirmed terminal-ID set,
Unicode11/xterm6-v3 and bounded stream/ack/lease/queue behavior. Old and new source
flows and failure/side-effect cases must be mapped; shared test success alone is
not whole-backend parity. Native payload and access are the following consumer.
