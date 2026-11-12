## Open a terminal

On macOS, open **Terminal** above Sessions in the web sidebar. Choose
**Install components** (`구성요소 설치`) once, then **New terminal** (`새 터미널`).
Setup requires Node.js 20 or later and npm, and downloads the pinned terminal
components. Visiting the page does not install anything or start a shell.
This feature is available in the web edition; the desktop app does not include it.

Open **Settings → Terminal** to save the default working folder and shell.
**New terminal** immediately opens a new tab with the latest saved defaults.
Leave Shell empty to use the default shell, or enter an executable such as
`/bin/zsh`. Existing login/interactive configuration, including Oh My Zsh, applies.
Saving defaults affects future terminals; it preserves work already running.
LocalBrain does not edit shell startup files or embed iTerm2.

The terminal includes D2Coding for Hangul, Latin and basic Powerline symbols at
the default13px. No system font installation or iTerm2 settings import is needed.
If the bundled file cannot load, use **Reload font**; execution remains running.
Extra Nerd Font icons and emoji can require system fallback. Shell encoding,
font glyph coverage and terminal character widths are separate responsibilities.

## Tabs and panes

Use **New terminal** for another tab. The pane's **⋯** menu splits right or down
for two panes; **Add split** adds a third or fourth in a 2×2 grid.
Splits open immediately in the selected pane's known folder and shell.
On narrow screens, the pane selector changes the
visible pane while the others keep running. **Shift+Escape** moves keyboard
focus from the terminal to its menu; ordinary Escape still reaches the shell.

Closing a pane with **×** ends that terminal and its managed child processes.
Closing a tab with **×** ends all its panes. A confirmation identifies running
terminals before ending them. Ending work cannot be undone.

## Keep work in the background

Choose **Send to background** (`백그라운드로 보내기`) in the tab menu, or
**Background** (`백그라운드`) in **Running** (`실행 중`), to hide a tab while its
work continues. In Running, **Open** (`열기`) returns to the same background work;
**End terminals** (`터미널 종료`) ends the tab's work. Individual termination is
available in each terminal's details. If every tab is in the background, the
empty view opens this list. New Terminal always creates another instance.
Closing the browser or leaving Terminal also keeps work running.

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
restore versions, finish work and restart the service in Running. Service restart
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

The Running dialog has separate **Start**, **Stop**, and **Restart** controls
under Background service. Stop ends all managed terminals and then the service.
Restart does the same and starts an empty service. Ending all terminals leaves
the service available; an empty service can stop itself after one minute idle.

Before updating the web installation, stop the service, update the source or
package, and install components again if the dependency lock changed. Restart
the web server to load the updated server code and refresh the browser. Then
start the service, or open a new terminal. An ordinary web-server restart does not apply
a new manager version to an already running service. Version conflicts require
an explicit service stop/restart; a failed stop is an error, not permission to
start a second owner.

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
affecting Sessions or other pages. Check Node/npm availability and service
status. An unidentifiable service is not killed automatically. As with other
terminals, detached programs remain stoppable while their ancestry proves ownership. After
both that link and the original POSIX session are lost, cleanup is not guaranteed;
use the program's own controls.
