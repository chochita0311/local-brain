# FEAT-0177: Terminal Activity And Background Rail

- ID: `feat-0177`
- Status: `in-loop`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Parent PRD: [PRD0030](../prd/prd-0030-macos-terminal-work-area.md)
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Authority: the user approves the proposed small hollow prompt mark, filled program-running mark and expandable inline Background list with an explicit continuation.

Replace the earlier all-open ● rule with reported command information for
nonselected foreground items: same-outer-diameter ◦ for confirmed prompt, ● for
reported command/program running, and an empty reserved slot when neither is
established. Current selection ✓ and hidden ◇ take precedence. A grouped tab
shows running if any live pane reports it, prompt only if every pane is live and
reports prompt, otherwise neutral. Agent activity remains separately reported
title braille; an agent CLI waiting for input can still be a running program.

Replace the Background modal with a compact expandable list in the rail footer.
Keep hidden tabs out of the strip and foreground tasks, but expose their names,
workspace, program/result indications, restore and whole-tab end actions inline.
Initially show retained hidden work; explicit Hide reveals the list and rail.
Manual collapse survives polling. Bound its scroll area so the workspace/task
lists and utilities remain reachable. Keep exact process identities, scope,
painted-input completion acknowledgement and stable tab-close geometry.

- Spec: [SPEC0177](../spec/spec-0177-terminal-activity-and-background-rail.md)
- Run: [Run258](../run/run-20261114-258-terminal-activity-and-background-rail.md)
- Evaluation: [Eval0174](../evaluation/eval-0174-terminal-activity-and-background-rail.md)

- Current boundary: code/web and packaged-backend delivery verified; actual
  native-window validation waits for Mac unlock. No waiver or native UI pass is
  inferred. [Eval0174](../evaluation/eval-0174-terminal-activity-and-background-rail.md)
  keeps the observed coverage separate from the remaining gate.
