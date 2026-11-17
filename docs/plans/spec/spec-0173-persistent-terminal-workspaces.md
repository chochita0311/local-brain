# SPEC-0173: Persistent Terminal Workspaces

- Status: `approved`
- Feature: [FEAT0173](../feature/feat-0173-persistent-terminal-workspaces.md)
- Run: [Run254](../run/run-20261113-254-persistent-terminal-workspaces.md)
- Profile: `fullstack-product`; contract/backend/frontend/integration/docs.

The host owns `terminal-workspaces.json` in the private data directory, containing
versioned workspace IDs/names/optional default cwd and current-generation tab
membership. Use the existing private JSON/atomic writer and local writer lock.
Bound and validate data; reject unsafe/corrupt files without overwriting them.
GET only projects state. Explicit reconciliation POST adopts live legacy/CLI
tabs into stable initial folder-named groups. Later workspace membership is
independent of tab/pane cwd. Empty groups persist; remove only an empty workspace.
Rename/move/remove use workspace identity and fresh manager membership.
Include this metadata in the existing same-installation backup/restore allowlist;
validate its schema before restore. Generated launch shims are reconstructible
and excluded from backups. Restoring metadata never starts a shell.

Manager creation and preference publication are separate. Creation returns the
actual terminal identity even when subsequent membership persistence fails,
with an explicit recoverable warning, never a false no-process outcome. Preserve
creation keys across retries; confirmed tab membership is never silently reassigned by a
retry with another workspace. Do not persist transcripts, commands or new Sources.

Retain the existing manager tab/split operations and immutable payload. Host-only
annotations connect tabs to workspaces; order validation uses workspace slots
while keeping hidden positions. Add explicit choose-folder actions for a new tab
and a split. Normal + uses workspace default or global defaults; normal split
inherits its clicked pane. Existing tab movement between workspaces changes only
membership. No process relaunch is implied by metadata changes.

New zsh launches use a verified, versioned private launcher/startup shim outside
the app and immutable payload. Existing generic executable spawning is sufficient;
do not alter manager/Rust protocol or inject live input. Startup/hook details must
be established against installed zsh and official source plus real synthetic PTY
tests before acceptance. Reads do not prepare integration files. Preserve user
rc content/order, effective ZDOTDIR, hook coexistence and last-command result.
HTTP creates with an omitted/empty shell explicitly resolve the host's `SHELL`
or `/bin/zsh` before integration; the GUI continues capturing configured defaults.
The low-level standalone CLI and already-running terminals remain unchanged.

The rail header owns collapse while visible; the tab toolbar shows only reopen
when collapsed. Narrow overlay dismissal returns focus to reopen. Terminal-only
density uses existing tokens; task secondary context is omitted when redundant.
Reported prompt/running/result have hollow-circle/spinner/check/error semantics;
unreported live shells have a neutral dot, never a fabricated prompt/result.

Verify persistent empty workspaces, different-root tabs/panes, generation reset,
restart/reload, current jobs and failure races. Exercise actual zsh startup/status
with a synthetic HOME/ZDOTDIR, nonzero commands, other hooks and preserved startup
files. Repeat browser/native-frame controls, density and input regression checks.
Build/app/physical evidence and prior native IME failures remain separately scoped.
