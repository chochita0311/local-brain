# FEAT-0173: Persistent Terminal Workspaces And Shell Status

- ID: `feat-0173`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `functional`, `design`, `ux-heuristic`
- Parent PRD: [PRD0030](../prd/prd-0030-macos-terminal-work-area.md)
- Authority: explicit user correction of duplicate collapse controls, workspace lifetime/folder restriction, dense header/rows, and explicit approval of automatic zsh status integration.

## Outcome And Acceptance

Workspaces are named, durable groups independent of folders and terminal process
lifetime. Each holds tabs; each tab holds up to four terminals with independent
working folders. A workspace may have an optional default folder. Empty groups
survive shell exit, service/app restart and reboot without restoring processes or
replaying commands. The user can rename a workspace or remove an empty group
from the list. Existing folder-based groups are adopted without ending jobs.

New tabs and splits can explicitly choose another folder while remaining in the
selected workspace/tab. Existing defaults, direct create, scoped individual End,
background/reopen, tab order/edit/recovery and input contracts remain preserved.
Workspace metadata is local app data, separate from cached process payloads and
generic settings. Membership is generation-bound and never reconnects an old ID
to a new process. CLI-created/unassigned tabs remain visible and recoverable.

Keep one visible Terminal rail collapse/open control in each state. Compact the
Terminal header/search and group/task rows under the existing design language,
without changing density on other routes or hiding accessible actions/status.

New zsh terminals automatically report prompt/running/completion/result through
the existing OSC133 parser. Do not edit user startup files or inject commands
into existing terminals. Preserve startup files, chosen working folder/shell,
command exit status, input and app-less lifetime. Other shells and unreported
states retain truthful fallback markers. Status uses actual signals rather than
silence or shell liveness guesses. No active manager upgrade/stop is authorized.

- Spec: [SPEC0173](../spec/spec-0173-persistent-terminal-workspaces.md)
- Run: [Run254](../run/run-20261113-254-persistent-terminal-workspaces.md)
- Evaluation: [Eval0170](../evaluation/eval-0170-persistent-terminal-workspaces.md)

Shared browser95, Node75, Python1700 (49 opt-in skips), separate shim/zsh PTY5,
final319-file app integrity and actual native12 checks pass. New integrated zsh
survives normal app Quit, source-app removal and relaunch with the same generation/
PID. Empty workspace metadata survives explicit service stop. Native modal
external-AX exposure, earlier failed/intermittent Korean-input probe, physical
input/VoiceOver/sleep/resource and human visual acceptance remain scoped limits
in Eval0170; whole-backend Rust parity is not this Feature's completion claim.
