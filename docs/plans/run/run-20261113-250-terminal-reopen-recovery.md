# Run250: Terminal Reopen And Version Recovery

- Status: `passed`
- Feature: [FEAT-0169](../feature/feat-0169-terminal-workspace.md)
- Spec: [SPEC-0169](../spec/spec-0169-terminal-workspace.md)
- PRD: [PRD-0030](../prd/prd-0030-macos-terminal-work-area.md)
- Profile: `fullstack-product`; frontend/integration/docs.
- Authority: human reports disabled New after closing and explicitly requests full verification, Rust migration and app integration with subagents.

Read-only actual-service inspection found zero retained terminals and a live
incompatible manager whose build matches committed HEAD rather than current
source. The development HTTP endpoint reports the same state. Closing alone is
not established as the cause: the missing version-recovery explanation/action
and missing direct last-close→toolbar-New coverage are the supported gaps.

Preserve compatibility rejection and all running work. Add contextual explanation
and an explicit version-update action using the exact confirmed generation/ID
scope. An empty-scope update must conflict if a terminal appears meanwhile.
Never silently replace a manager with live work. Verify repeated last tab/pane
close then toolbar New, normal restart and stale-service recovery using synthetic
PTYs. Current user empty manager may be retired only with an empty expected set;
app/backend update must preserve data and configured scope.

Initial dirty files from Run249 remain; no commit/push is requested. Three named
read-only support workers inspect reopen call paths, official Herdr evidence,
and native packaging/auth/lifecycle call paths. Primary owns all fixes and choices.

## Checks

[Eval0166](../evaluation/eval-0166-terminal-reopen-recovery.md) records PASS for
the bounded recovery increment. Final actual Rust/PTY browser54 passes repeated
last-tab/pane close→New, stale empty-service explicit update and network/503
uncertain-create identity-preserving retry. Exact expected-scope termination and
adjacent workspace/input/font/state behavior remain covered.

The original development HTTP host was gracefully restarted after rechecking
its process identity, listener and cwd, preserving its actual original launcher
arguments/environment in memory. No terminal stop was sent; the actual endpoint
now reports stopped/zero and bundleReady true. It prepared no private payload.
An owned read-only browser opening the actual `/terminal` then confirms fonts
loaded and New enabled with zero panes, without any create/install/start/stop.
An already open page must reload. User data, jobs and installed apps are intact.
Run249 is historical evidence; the current loaded-host observation is separate.
