# FEAT-0169: Folder Terminal Workspace

## Metadata

- ID: `feat-0169`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0030](../prd/prd-0030-macos-terminal-work-area.md)
- Created: `2026-11-12`
- Updated: `2026-11-12`
- Approval: the human's continuation explicitly requests the discussed Herdr-like rail, upper/lower sections and tabs. This approves this bounded implementation; prior contract-only Runs remain unchanged.

## Goal And Acceptance Contract

Provide a working Terminal area directly beside the existing navigation: upper folder groups, lower cross-group task status, compact tabs and add/split actions, large terminal panes, hidden-tab recovery and settings/management in the rail footer. Preserve the app shell and all existing PTY/input/lifetime contracts.

- Groups derive from each tab's fixed, canonical creation folder, independent of later `cd`, Workstream, Project and imported Session. Opening a folder explicitly creates its first terminal; selecting a group never starts work. New tabs use that group's folder and the configured shell; Split retains the clicked pane's current folder/shell. No empty group or new persistent store is introduced; the group disappears after its last retained tab is removed.
- Existing groups/tabs/PTYs remain manager-memory state, surviving web/backend disconnection, not manager loss or reboot. Hide only changes visibility; status rows reopen the same hidden tab and focus the exact pane. Close retains the current explicit termination scope and confirmation.
- Status symbols distinguish live shell with unknown command state, reported prompt/running/completion and process exit/error. Only explicit OSC 133 shell signals supply command states; no silence/output-text inference or startup-file modification. Unsupported shells show unknown command state. Seen/unseen completion is local view state and clears only after the matching completion is painted in a focused visible pane.
- At most four panes per tab and 32 retained records, both D2Coding faces/13px, Unicode/checkpoint/input lease/IME/backpressure/no replay remain intact. Narrow viewports show a pane selector and collapsible Terminal rail without terminating other panes.
- Setup/font/network/service failure recovery and accessible names remain reachable. Other routes retain their layout.

## Scope And Lanes

| Lane / owner | Paths | Evidence |
| --- | --- | --- |
| contract/backend / primary | terminal manager + status module; runtime fingerprint | real isolated manager, shell-signal tests, stable group root |
| frontend / primary | terminal template/CSS/JS, scoped base main class | rendered geometry, keyboard, groups/tabs/panes/hidden/status and failure cases |
| integration / primary | synthetic browser fixture/QA | actual xterm + isolated PTY route, manager continuity |
| docs / primary | terminal policy/guide, design constitution/plan, PRD and trace | current owners and link/catalog checks |

Native authentication, bundled runtime, Rust port and actual packaged-app validation remain downstream PRD-0029/0030 work, not claims made by this web/UI increment. No machine-specific settings, live-user process changes, app replacement or publication is authorized by this Run.

## State And Regression Expectations

Initial readiness remains unknown until checked; empty/setup/font/service faults retain distinct recovery. Group selection preserves hidden tasks and scoped tab selection. Cross-group status focuses existing work. New creation keeps its idempotency key and launch values across uncertain retries. Preserve other app routes and the independent manager lifecycle.

## Harness Trace

- Active spec: [SPEC-0169](../spec/spec-0169-terminal-workspace.md)
- Active Run: [Run249](../run/run-20261112-249-terminal-workspace.md)
- Evaluation: [EVAL-0165](../evaluation/eval-0165-terminal-workspace.md), PASS with explicit platform limits; implementation/evaluation complete, human visual acceptance remains separate.

## Delivery

Run249 delivers the shared web workspace, folder roots and reported status. Explicit
retry preserves uncertain creation identities, launch validation uses the actual
group/folder, and completion acknowledgement requires actual rendered xterm input
focus. Independent read-only challenge findings were repaired and exercised with
real synthetic PTYs. Native access/bundling and Rust port remain outside this
Feature and are not marked complete by it.
