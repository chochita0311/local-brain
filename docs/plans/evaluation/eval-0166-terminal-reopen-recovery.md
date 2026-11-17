# EVAL-0166: Terminal Reopen And Version Recovery

- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete` for the selected web recovery boundary.
- Feature: [FEAT-0169](../feature/feat-0169-terminal-workspace.md)
- Spec: [SPEC-0169](../spec/spec-0169-terminal-workspace.md)
- Run: [Run250](../run/run-20261113-250-terminal-reopen-recovery.md)
- Profile: `fullstack-product`; contract, functional, design and interaction evaluation.

The reported disabled New is explained by an observed incompatible manager built
from the committed source while the page used changed source. It had zero
retained terminals. The evidence does not establish that closing a tab itself
caused the mismatch. The manager later stopped through its own idle lifecycle;
this work did not terminate a user terminal or replace a live manager.

The page now explains the old-service state and offers an explicit update.
Update uses the existing exact generation/terminal-ID confirmation, including an
empty ID set; a concurrently created terminal invalidates that confirmation.
Ordinary last-tab or last-pane termination leaves New available. In a bundled
host, the first New may prepare the offline payload without a separate Node/npm
installation step. Font/API readiness and uncertain-create retry gates remain.

The final real Rust/PTY browser run passes 54 checks. It includes three repeated
last-tab/pane close→toolbar New cycles; an incompatible empty-service explanation
and explicit update; network-lost and503 creation responses followed by retry
with identical keys, terminal IDs/PIDs and exactly one retained shell. Existing
folder groups, scoped tabs, four panes, hide/reopen, attention, keyboard focus,
responsive geometry, font recovery and late-list ordering remain exercised.
Rust integration separately verifies stale confirmation and contradictory stop
targets cannot broaden termination, including against a live old manager.

The original development HTTP host was gracefully restarted with its exact
existing launcher arguments, environment and working directory preserved in
memory. No terminal stop was sent. Afterward the actual endpoint reports stopped,
zero terminals and an available public offline bundle. Merely observing that
state creates no private terminal payload. An already open page needs reloading
to receive the new script. A separate owned Chromium session then opened the
actual development `/terminal` route read-only: fonts loaded, New enabled, zero
panes/terminals and service stopped. No create/install/start/stop was sent.
These live observations do not claim a synthetic
shell was created in the user's own runtime.

Native window/input acceptance belongs to [Eval0168](eval-0168-native-terminal-integration.md).
Run249/Eval0165 retain their historical web-only evidence. The broader PRDs are
not declared complete by this recovery result.
