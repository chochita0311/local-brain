## Open a terminal

Open **Terminal** above Sessions in the macOS app or development web. Choose
**+** or **New terminal** to prepare the bundled runtime offline and open a shell.
The Apple Silicon app includes execution components; users need no separate
Node/npm installation. Page visits and list reads neither copy components nor
start shells. Checkout developers first build the terminal runtime.

Open the rail's gear for **Settings → Terminal** to save the default working
folder and shell. The first **+** opens a tab with those defaults. Inside a
workspace, **+** uses its optional default folder (otherwise the global default)
and the latest configured shell.
Leave Shell empty to use the default shell, or enter an executable such as
`/bin/zsh`. Existing login/interactive configuration, including Oh My Zsh, applies.
Default changes apply to new instances; existing terminals retain their folders
and shells.
LocalBrain does not edit shell startup files or embed iTerm2.

The terminal includes D2Coding for Hangul, Latin and basic Powerline symbols at
the default13px. No system font installation or iTerm2 settings import is needed.
If the bundled file cannot load, use **Reload font**; execution remains running.
Extra Nerd Font icons and emoji can require system fallback. Shell encoding,
font glyph coverage and terminal character widths are separate responsibilities.

## Tabs and panes

The upper left **Workspaces** (`작업 공간`) section contains named working groups.
Its **+** creates an empty workspace with an optional default folder; its **⋯**
edits the name/default or removes an empty workspace from the list. Removing the
group does not delete a folder. Hidden tabs still belong to their workspace.
Existing folder groups are adopted without stopping work. Workspaces are separate
from Projects, Workstreams and imported Sessions. Empty groups survive closing all
terminals, app/service restarts and reboot, and join local backup/restore; their
saved structure never relaunches a program or replays a command.

Use the top **+** to add a tab grouping terminals in the current workspace.
Each pane header's **Split right/down** icons split that terminal;
**Add split** adds a third or fourth in a 2×2 grid.
Splits open immediately in the clicked pane's known folder and shell. A workspace
can contain tabs from different folders, and one tab can contain different-folder
panes. Choose **New tab in another folder** (`다른 폴더에서 새 탭…`) in the tab
menu or **Split in another folder** (`다른 폴더에서 분할…`) in the pane menu.
A later `cd` changes that pane's folder without moving its workspace.
On narrow screens, the pane selector changes the
visible pane while the others keep running. **Shift+Escape** moves keyboard
focus from the terminal to its menu; ordinary Escape still reaches the shell.

Closing a pane with **×** ends that terminal and its managed child processes.
Closing a tab with **×** ends all its panes directly, without a confirmation.
Individual task End is also direct; service/bulk stop, restart and update still
confirm their affected scope. When the shell exits through `exit` or Ctrl+D and cleanup is confirmed, its GUI view is removed regardless of exit code,
and empty tab; the workspace remains. A command returning to a live prompt does not close it.
Input errors and unconfirmed child cleanup remain inspectable. Ending work cannot be undone.

Click an active tab title, press **F2** or choose **Rename** to edit in place.
Enter/focus-out saves, Escape cancels, and failure preserves the draft for retry.
Drag tabs with the mouse, use **Alt+Shift+Left/Right**, or use the tab-menu move
actions. Ordering stays inside the workspace and preserves processes/splits.
The tab menu's **Move to workspace** shows destinations in the same panel.
Choose one to change the tab's group while retaining the same terminals and
processes. A check marks current membership; **Tab menu** or Escape returns.
Arrow keys and Home/End navigate menu items; Enter runs the action. The
same live service's presentation order is shared across web/app reconnections;
it does not restore work after a service restart.

## Keep work in the background

Choose **Send to background** (`백그라운드로 보내기`) in the tab menu, or
**Background** (`백그라운드`) in **Management**, to hide a tab while its
work continues. It leaves the foreground tab strip and task list. **Background**
(`백그라운드`) in the rail footer expands an inline list. Choose a tab name to
return to the same work; its × ends that whole tab. Hide reveals this list, and
retained hidden work starts expanded when you return. You can collapse it;
periodic refresh preserves your choice. Long lists scroll within the rail while
its utilities remain reachable. In Management, **Open** (`열기`) also returns to that background work;
**End terminals** (`터미널 종료`) ends the tab's work. Individual termination is
available in each terminal's details. If every tab in a group is hidden, the
empty view opens the hidden list. **+** always creates another instance.
Reported hidden errors/new completions mark the footer's Background action.
Closing the browser, leaving Terminal, closing the app window or quitting with
**⌘Q** retains terminal work. Mac sleep can suspend computation/network activity;
wake/reopen checks actual liveness and reconnects surviving work. System shutdown
or reboot ends ordinary process continuity, and no commands are replayed.

The lower **Task status** (`작업 현황`) list covers foreground terminals across all
groups. Choose a row to focus that exact pane. Each row's **⋯** offers focus,
background tab, tab rename and ending that terminal; multi-pane background actions
explicitly name their whole-tab scope. Collapse
this rail with its panel control; on narrow screens, reopen it from the toolbar.
The bottom bar shows the focused folder, input/connection readiness and number
of live shells.

If a creation response is lost, use **Retry terminal creation** (`터미널 생성 재시도`).
It retains the original request and launch values even if a refreshed list already
shows the new group. Resolve that request before starting another creation.

## Read status symbols

Hidden and current selection take precedence. Other foreground items use
reported shell command state:

| Mark | Meaning |
| --- | --- |
| ✓ | Currently selected tab or focused terminal |
| ◦ | Confirmed shell prompt waiting |
| ● | Reported command/program running; an agent CLI can still be waiting internally |
| ◇ | Hidden/background tab in the inline list; its processes remain managed |

The small ring and filled dot have the same painted diameter and20px slot.
A grouped tab shows running when any pane reports it and prompt only when all
panes are live and report prompt. Unavailable or otherwise unclassified state
keeps an empty slot with its exact description; it is not inferred to be idle.
The same criteria apply to old and new terminals. An underline/frame also marks
selection; its inactive-window border becomes neutral and returns on focus.

A separate braille indicator beside the name comes from the program's reported
title. It follows that program's frames and disappears when removed from its
title, while your tab name stays intact. In a grouped tab, the focused reporting
pane takes precedence, otherwise the first reporting pane is represented.
A running agent CLI is not necessarily an agent doing work. LocalBrain does not
fabricate this indicator from a running shell command, quiet output or a timer.
Programs without a reported title indicator have no separate activity glyph.
Inactive/hidden terminal metadata also uses a three-second refresh, so a short
command may finish between observations.

The bottom bar and tooltips separately describe **shell command** running,
prompt waiting or unavailable status. New zsh terminals automatically report
these signals. Result/error badges appear separately; a new completion stays
marked until its screen is actually painted with keyboard focus in an active
window. Hiding, selecting, minimizing or opening a menu alone does not mark it
seen. Hidden rows retain ◇, any reported program indicator and result badges.
A confirmed shell exit is removed after cleanup regardless of its exit code;
cleanup/input faults remain available for inspection.

LocalBrain uses private startup shims for new zsh terminals and preserves your
startup files, aliases and hooks. Existing terminals receive no injected changes;
create a new terminal for automatic shell integration. Reconnecting does not
retrofit an old running shell. Other shells can use compatible OSC133 signals;
unreported command state remains explicitly unknown with a neutral empty slot
unless selected/hidden, never a question-mark default. Reported command success is separate from
an agent or workflow finishing. Input requests and unread output are not inferred.

A separate local service owns the shells. Restarting the web server preserves
them. If two browser windows show one terminal, the second observes until you
choose **Take control** (`제어권 가져오기`). Only the current controller can type
or resize. Hidden browser pages disconnect and reconnect when visible.

Input waits briefly when the connection is congested. Unsendable input or lost
control produces feedback; unsent input is cancelled and never automatically
executed after reconnect.
If a program does not read terminal replies and exceeds the input limit, its
pane shows an input error and pauses output. End that terminal through Management;
other terminals remain available.
An interrupted paste may already have partially reached the application. After
reconnect, cancel/check the current input with Ctrl+C before retrying. An old
view asks for a refresh. If a current view and an older service use different
restore versions, finish work and restart the service in Management. Service restart
ends its terminals.

The service keeps screens and layouts in bounded memory. Reconnect restores
supported terminal modes and recent output; older output can be truncated.
The current engine restores fragmented control sequences, both buffers, modes,
saved cursors, tab stops, character attributes and links into a fresh view.
If current state exceeds the frame limit even after omitting history, reconnect
reports a limit instead of silently importing an incomplete screen; management
remains available. An older running engine needs an explicit service update.
It retains at most 32 terminal records, including exited screens, with 1000
scrollback rows per screen. End/remove old terminals to free a record.
Service stop, service restart, or a computer reboot discards this state. No
commands are replayed. Terminal output is not added to Sessions, search, or Usage.
Your shell and programs can still write their own normal history and logs.

## Manage the service

The rail footer's **Management** control has separate **Start**, **Stop**, and **Restart** controls
under Background service. Stop ends all managed terminals and then the service.
Restart does the same and starts an empty service. Ending all terminals leaves
the service available; an empty service can stop itself after one minute idle.

Before replacing the app or runtime, explicitly stop affected terminal work
through Management and confirm its termination. Ordinary app Quit leaves that work
alive. Replace, reopen and start a fresh service. When an older service disables
New, use **Update terminal service**; existing work requires exact-scope confirmation.
An empty old service also needs an explicit update. Known older services keep
individual/tab stop available. A failed stop is an error, not permission to start
a second owner. Updating never replays commands.

After an unexpected service loss, a warning says that previous work may remain.
Stop/restart cannot confirm that work ended. Use the affected program's own
controls to inspect and end it. An explicit New/Start creates a fresh service
without recovering or replaying the old work; its empty list is not proof that
the previous programs ended. A failed individual stop keeps that terminal's
record and error so you can inspect and retry it.

The same controls work in the command line:

```sh
lb terminal service install
lb terminal list
lb terminal stop t-example
lb terminal stop --all
lb terminal service status
lb terminal service start
lb terminal service stop
lb terminal service restart
```

`list` shows terminals and IDs. `service status` describes the background
manager. Reading either never starts it. `stop ID` ends one terminal; `stop --all`
ends all terminals; `service stop` also stops the manager. Add `--json` for
machine-readable output. All/service termination confirms once; scripts must
pass `--yes` when work is running. `--force` skips the normal grace period while
keeping the same ownership checks. `localbrain` remains an alias for `lb`.

If setup or connection fails, the screen shows the relevant error without
affecting Sessions or other pages. Check the app's bundled components and service
status; packaged-app users do not need to install Node/npm. An unidentifiable
service is not killed automatically. As with other
terminals, detached programs remain stoppable while their ancestry proves ownership. After
both that link and the original POSIX session are lost, cleanup is not guaranteed;
use the program's own controls.

After first preparation, `<terminal-cache>/localbrain-terminal` supports the same
`list`, `stop` and `service` commands without Python, the app or its source checkout.
Find the terminal scope under the cache location in Settings. Cache cleanup
preserves live/in-use, unknown and loss-marked terminal components.
