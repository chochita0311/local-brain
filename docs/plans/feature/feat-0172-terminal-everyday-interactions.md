# FEAT-0172: Terminal Everyday Interactions

- ID: `feat-0172`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `functional`, `design`, `ux-heuristic`
- Parent PRD: [PRD-0030](../prd/prd-0030-macos-terminal-work-area.md)
- Created: `2026-11-13`
- Authority: explicit user correction of the current Terminal interactions and instruction to benchmark basic terminal conventions.

## Outcome And Acceptance

- A confirmed shell exit, regardless of exit code, is removed from the GUI through the existing scoped stop
  operation after the manager confirms exit/cleanup. Input/cleanup errors and uncertain ownership retain inspectable feedback. Command completion while the
  shell remains alive does not close it. No commands are replayed.
- Background keeps execution but removes that tab's panes from the foreground
  task list and tab strip. A separate footer list restores/focuses or ends them.
  Actions explicitly name whole-tab scope when a tab has multiple panes.
- An active tab title edits in place like Sessions: click title/F2/menu, Enter or
  focus-out saves, Escape cancels, IME composition is preserved, failed saves keep
  the draft. Inactive tab selection and dragging do not accidentally rename.
- Mouse drag and keyboard/menu alternatives reorder tabs within their folder.
  Order is a shared presentation preference for the current manager generation,
  stored privately outside the immutable payload and reused across web/app hosts.
  It never changes PTYs, IDs, group roots or split membership.
- Single pane/tab/task End is direct, without a JS confirmation. Existing service
  stop/restart/update and stop-all retain explicit confirmed scope.
- Each foreground task has a reachable ⋯ menu for focus, background tab, title
  edit and terminating that terminal; menu placement/dismissal/focus work in rails.
- Unknown command state uses a recognizable neutral terminal icon. Reported
  running/done/failure/prompt states retain their truthful distinct meanings.
- Shared navigation, existing input/checkpoint/ownership/font/bounds, runtime
  identity, active user work and normal app Quit retention are preserved. No
  manager/payload upgrade is required for these interactions.

Native physical acceptance remains separate from the shared browser/host evidence.
Official benchmarks inform conventions; no installed-app or universal-default
claim is inferred from documentation.

- Spec: [SPEC0172](../spec/spec-0172-terminal-everyday-interactions.md)
- Run: [Run253](../run/run-20261113-253-terminal-everyday-interactions.md)
- Evaluation: [Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md); shared-browser80 and final native-window10 pass within the stated scope. The native OS IME probe did not pass; physical input and human visual acceptance remain separate.
