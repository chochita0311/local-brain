# Run256: Terminal Action Hierarchy

- Status: `passed`
- Feature: [FEAT0175](../feature/feat-0175-terminal-action-hierarchy.md)
- Spec: [SPEC0175](../spec/spec-0175-terminal-action-hierarchy.md)
- Profile: `frontend-product`; frontend/integration/docs.

The user's correction authorizes moving pane actions out of the tab toolbar,
compacting menu rows and fixing the workspace move chooser. Primary owns this
bounded correction and evaluation. No delegation, Git write, installed-app
replacement or user manager stop/upgrade. Baseline123 dirty/new files are
preserved in task-owned private scratch; unrelated work remains intact.

Rendered baseline uses a separate synthetic HOME/server/real PTYs. The tab menu
has37.6875px rows from8px vertical padding and body14px type; the native workspace
select has a separate OS popup. The Settings family uses compact controls and
shared tokens. These are implementation mismatches, not a demand for wider menu
spacing in the constitution. The tab toolbar mixes group creation with globally
focused-pane split actions; move those actions to their actual source pane.

Preserve backend/runtime/schema/input contracts, existing named empty workspaces,
mixed roots, direct close, hide/reopen, process IDs, tab editing/reorder, shared
header and app-independent lifetime. UI/template/QA/app-guide changes require
new asset/browser and final package checks. Earlier backend/native-input evidence
is reused only within its unchanged scope.

## Implementation And Browser Evaluation

Split controls now belong to each pane and inherit that pane's cwd/shell. The tab
menu changes to a checked workspace list in the same panel. One menu position and
keyboard/dismissal owner covers tab, pane and task menus; shared label/padding
roles produce32px rows (40px narrow). Long lists scroll, active-tab changes close
the stale chooser, and polling retains the selected/focused destination. Failed
movement retains membership/execution and permits retry. Header controls can
wrap when connection/lease controls consume a narrow pane's remaining width.

The strengthened browser packet exposed a focus ownership gap: the stop caller
cannot assume its refresh is the read that actually removes the view. Focus
recovery now belongs to confirmed model-driven pane removal in reconcile, while
layout/workspace-only unmounts do not steal focus. A peer's confirmed removal is
also exercised. No manager or input-adapter code changes.

Final Chromium118 and Node75 pass, with11 desktop-build checks. Earlier browser
attempts retain their actual failures: short narrow viewport/click scrolling,
missing Enter character events in the driver (a blank-page probe distinguished
keydown/keyup from keypress/click), deferred close focus, and a peer-switch test
clicking a trigger behind a popup. The final pointer helper checks actual hit
testing, keyboard Enter generates its normal character event, and peer switching
uses an exposed trigger. Viewport evidence is1440/920×400 and700/320×800, in
addition to the existing everyday Terminal packet; no universal tiny-height pass.

The existing development host already serves matching new template/JS/CSS, so no
HTTP restart or user-terminal stop is needed. The final app rebuild and actual
native menu/split/lifecycle gates were subsequently completed after owner unlock.

## Delivered Evidence And Initial Technical Access Block

[Eval0172](../evaluation/eval-0172-terminal-action-hierarchy.md) records browser118,
Node75, desktop-build11, final319-file package integrity and actual packaged-host10
PASS. Build input67d304d404b0865b1f510d38e8e87ad493f14cc51114a71a32e43c32f04bcad1,
431 input files; app988233819 regular bytes; ZIP
fad443a9af9e7cab78f02d73e590794fb3858b8eb5227025867328746b4ecc43.
The runtime payload remains66b53da245e4cb9be9deba12d1079217efce0a62977c053514cc71f81352e9e8.
The app/ZIP at the existing dist owner were rebuilt and ad-hoc signed; no installed
application was replaced and no Git write occurred. The running web host already
serves matching new assets/template without a restart; all3 freshly observed
user execution IDs/PIDs and generation remain identical.

The new actual native-window packet stopped at its screen-lock preflight before
any UI claim. Independent `--backend-only` checks then passed offline cold
creation/four-pane API, per-launch HTTP/WS authentication, zsh state, presentation
order, Quit/source-app removal/app-less management, process suspend/resume,
relaunch and exact test-service stop with retained empty workspaces. This is not
actual WebView/physical-input evidence. Prior native12 belongs to the previous
build and is not relabeled as this candidate's menu acceptance.

Screen lock initially blocked the remaining window gate, and the owner was told
and asked to unlock. This was an access block rather than a code/planning defect.
The subsequent unblock and13-check actual-window result below close that gate.
The existing separate IME/AX/VoiceOver/physical sleep/platform/resource/human-review
limits remain. Final private evidence/source hashes retain the initial block,
failed driver attempts and successful outcome; owned scratch/QA roots/build cache
are cleaned after verification, leaving the rebuilt candidate ready for review.


## Technical Unblock / Native Attempt2

The owner explicitly reports the screen is unlocked. Resume the prepared actual
window packet within this technical-block Run, retaining the preflight/host
results and frozen pre-native snapshot. No boundary, runtime or source change was
needed for access. Subsequent driver attempts and the final result follow.

## Actual Window Result

Final native attempt5 passes13 checks with IME explicitly skipped. The actual
Tauri window exercises pane-header splits/max-four, last close/recreate, named
groups, checked same-panel workspace moves in both directions with exact PIDs,
zsh state, minimize/red close/Dock, Quit/app-path removal/relaunch and exact stop.
Primary inspected its actual chooser and four-pane screenshots. The chooser is
entered through OS keyboard events: Shift+Escape, reverse Tab, Space and arrows/
Enter. Browser118 supplies pointer/geometry evidence; physical mouse/VoiceOver is
not inferred from this native keyboard observation.

The first resumed AXPress-only disclosure probe failed. A process-targeted mouse
probe did not activate the menu; a guarded WindowServer-pointer probe refused a
point attributed to another top window. Those test-driver paths were removed,
their failures retained, and the complete OS-keyboard packet passes. No product
code or delivered app bytes were changed to manufacture that native result.
Feature175's selected technical target passes; the wider acceptance limits stay
with Eval0172/Eval0170. No further scope or approval decision is introduced.
