# Terminal

## Delivery And Ownership

Terminal shares its HTML/CSS/xterm workspace between the macOS app and development
web above Sessions. The new self-contained payload targets Apple Silicon/macOS14;
Intel/Windows delivery and external iTerm2 attachment are not established by this
port. Other optional feature admission is unchanged. Terminal output never enters
Session, Usage, search or source ingestion. The conditional bilingual
[Terminal guide](../../../apps/web/content/docs/terminal.md) owns user procedures.

`crates/core` owns Terminal validation, immutable payload
verification/preparation/retirement, manager IPC/stream state, process inspection,
service control and native settings/TOML transactions. `crates/runtime`
provides fixed host protocol1 and app-less management independent of Tauri.
`apps/api` owns Rust CLI/HTTP/WebSocket transports and calls the core directly.
No Python runtime/process helper or interpreter callback is used by the product.

The independent Node24.15.0 arm64 manager uses protocol2, node-pty1.1, xterm
headless6, serialize0.14 and Unicode11 addon0.9. Browser xterm6/fit and D2Coding
load only on this route. The builder verifies the official Node archive SHA256,
installs the pinned public runtime lock without install scripts and signs native
bytes before creating a closed, content-addressed manifest. Full file hashes are
checked before preparation/execution and retirement; ordinary polls inspect the
manifest and exact tree/size/mode shape without repeatedly hashing the Node image.
Bundled components are copied only on explicit New/Start/install to private
`<terminal-cache>/payloads/<payloadId>`. Paths and helper execution then survive
app/checkout removal. No runtime download, user-cache copy, Herdr core, CDN,
login agent or separate terminal window is used. Native recipients need no Node/npm.
Legacy protocol1 managers retain inspection and validated stop, while new work
requires a compatible protocol2 payload. Manager/helper/stream use leases and the
same control lock protect execution from cache retirement. Unknown/lost owners
and loss-marked payloads remain protected; generic cleanup may clear other caches.

Both new manager screens and browser views select the pinned Unicode11 addon0.9
so mixed Hangul/modern emoji use matching cell widths. Each terminal advertises
its width version; an older incompatible manager remains inspectable/stoppable,
but viewing/input requires explicit service update to the matching protocol. This does not establish
complete grapheme/ZWJ or arbitrary application compatibility. The terminal-only
font alias loads unmodified public D2Coding1.4.0 Regular/Bold WOFF2 from the local
web package, with its OFL, pinned upstream revision and SHA256 manifest. The two
faces total3,075,824 bytes; the default remains13px, coding ligatures are disabled,
and opening/measuring panes waits for both faces. URL-only sources avoid a hidden
dependence on installed D2Coding. Font failure blocks new rendering with a concise
reload action; it does not terminate work. No OS font install, runtime font
download or iTerm2 preference import occurs. Coverage includes modern precomposed
Hangul, Latin and basic Powerline; arbitrary Nerd Font/private-use icons and emoji
are not promised by that font. Font coverage, Unicode width and shell/input
encoding remain distinct responsibilities.

For WebKit's macOS Korean input path that lacks composition events, a local
capture adapter holds only the unsent Hangul range. Replacement/deletion events
update its visible preview; the next syllable, ordinary key, control chord,
accepted paste or visible focus-out commits it through xterm's input API. A
rejected multiline paste, including Cmd+V, leaves the pending range intact.
Ctrl+V retains macOS shell literal-next-character behavior. Bare modifiers keep
composing. ASCII stays on xterm's normal key path; textarea prefixes and WebKit
NBSPs are never forwarded as shell input. Native composition events and Chromium
retain xterm's original path, and screen-reader mode remains enabled. Connection
loss, ownership loss, hiding and disposal cancel pending input, including native
composition and deferred xterm sends; it is never replayed on reconnection.
The native helper is retired and replaced at this boundary because the pinned
engine has no public cancellation API. This preserves the supporting accessibility DOM but
does not establish VoiceOver announcement correctness.

New managers require matching width and checkpoint versions before granting input;
an old page receives a refresh request instead of silently using incompatible
cell widths. A new page facing an older checkpoint service directs the user to
finish work and explicitly restart the service through Management. The browser renderer import includes its generated bundle hash,
and the asset check verifies that URL, preventing a cached older module from
missing newly required exports. Runtime lock tarballs use the public registry.

## Lifecycle

- One manager per configured data/cache scope owns its PTYs. A transient macOS
  launchd bootstrap job in the logged-in user's GUI domain outlives the invoking backend and browser. An empty manager can
  idle-exit after 60s without terminals or IPC connections. KeepAlive is disabled;
  a private launch configuration exists only during bootstrap and is removed in
  its finally path. No login agent or permanent launch/environment file remains.
- Closing a view/navigation, hiding the app window or ordinary app Quit preserves execution. Sleep does not request termination, but the OS can suspend computation; wake/reopen revalidates actual liveness and reconnects. System shutdown ends ordinary continuity with no replay. App Quit stops only its own backend/schedules, not the independent terminal manager.
- Closing a view/navigation preserves execution. Pane/tab × ends its scope;
  tab background hides but retains its layout. Management can reopen or end
  tabs and individual terminals, or end all. Tabs have up to 4 panes; the scope
  retains at most 32 terminal records, including exited screens.
  Two panes can be side-by-side or stacked; three/four use a 2×2 grid. Below
  the shared 700px breakpoint, a selector shows one pane while keeping the others.
- The GUI retires a confirmed shell exit, regardless of exit code, through the existing generation-bound
  single-ID stop after the manager has confirmed process cleanup. Normal command
  completion at a still-live prompt never closes the shell. Input faults and unconfirmed descendant cleanup remain inspectable. Individual
  pane/tab/task End acts directly without a confirmation dialog; service/bulk
  stop, restart and update retain their explicit scope confirmation. The runtime
  still retains exited records for non-GUI consumers until explicitly removed.
- Service stop blocks new creation, terminates its owned live descendants with
  TERM/HUP, waits3s, then uses KILL if needed with2s confirmation. POSIX session
  membership also catches ordinary background jobs after their shell exits;
  a short-lived Rust inspection helper reads session IDs and process birth/group
  identity only during control/exit cleanup, with no idle polling process. One
  asynchronous reader is shared by concurrent checks so input remains responsive. Intentionally
  detached work remains stoppable while live ancestry proves ownership;
  after both that link and original session membership are lost, cleanup is not
  guaranteed and may require the program's own controls. There
  is no broad killall. Unknown identity/liveness or unconfirmed exit is failure;
  force skips grace while preserving ownership. Create/start/stop/restart/setup
  share a local control lock; generation and exact target snapshots bind destructive
  requests. Changed scope or generation is rejected for renewed confirmation.
- Restart stops all managed work and starts an empty manager. Commands are never
  replayed. Web backend restart preserves work; updates must explicitly stop the
  old manager, update/install components if needed, restart the web server and
  refresh the browser, then start the service or open a new terminal. Build/version
  mismatches disable new work and allow explicit management of the old service.
- A dead manager with a leftover identity is reported as an unclean loss; an
  empty fresh list does not prove the previous programs ended. Stop/restart
  refuse to claim cleanup. Manager identity includes process birth time; positive
  birth mismatch or a dead process permits classifying a reused PID as unclean
  loss without signaling it. Birth reads use UTC and the C locale; the identity
  tags this format, so caller/system timezone changes cannot imply replacement.
  A live matching PID, legacy/unknown time format or failed inspection
  remains unknown and protected. An explicit New/Start can create a fresh manager
  without replaying or adopting previous work; unconfirmed programs require
  their own controls. Failed per-terminal termination retains its record and
  error for inspection and retry instead of reporting successful removal.

## State And Resource Bounds

Layouts and logical VT screens exist only in manager memory. No terminal input,
output, transcripts, serialized screens or credential/environment dump are
written to disk or indexed. Only owner-private setup files, engine dependencies,
control lock/socket and manager identity persist under the scoped cache.
Service stop or reboot drops screen/layout state; ordinary reconnect restores
the same supported VT buffer, modes, cursor and dimensions from the live manager.
The user's shell and programs retain their own history/logging behavior;
LocalBrain does not disable or replace those settings.

Each screen has1000 scrollback rows and a128 KiB delta tail. PTY parsing pauses
above1 MiB pending and resumes below64 KiB. A lagging observer receives a serialized
state; oversized history falls back to the current screen with a truncation cue.
Manager-to-PTY input has a256KiB per-terminal budget shared by user input and
automatic query replies. Nonblocking writes retain byte order and yield between
bounded pages; full input pipes retry after10ms. Writes run on the same event
loop as descriptor close, avoiding off-thread writes to a reused descriptor.
PTY close cancels the writer immediately, independently of later process exit.
Input backlog does not pause output, which would deadlock cooperative duplex
programs. A new user event that does not fit is
rejected completely. If replies from already parsed output exceed the budget,
the affected terminal pauses output and exposes an input error with management
termination available; other terminals and service controls remain usable.
The web bridge closes a rejected input stream before processing later paste
fragments, and the browser discards the unsent suffix with persistent partial-input
feedback. Already accepted bytes may have reached the program; check/cancel with
Ctrl+C after reconnect. Background faults are visible in Management and CLI list.
Frames are capped at2 MiB, input events at64 KiB, and dimensions at240×80. Hidden pages
detach. Visible streams require render acknowledgements and bounded timeouts.
The view queues at most512KiB of serialized outgoing messages while its socket
drains, retrying only while that same connection remains live. Text is divided
at8192 UTF-16 units without splitting surrogate pairs, keeping escaped JSON below
the web frame bound. Overflow rejects the complete new event with visible feedback;
disconnect or ownership loss cancels unsent input with feedback, never replays it
after reconnect. No timer runs once that queue is empty or the view is disposed.
If a chunked bracketed paste is interrupted, feedback explains that part may
already have reached the application; the user checks/cancels the current input
before retrying. Cancelling the queue does not roll back data already delivered.
These bounds do not establish every-device performance; measured evidence belongs
in the owning Run/Evaluation.

The pinned `xterm6-v3` adapter transfers packed cell runs and nonvisual engine
state, without repainting via synthetic control sequences. It preserves normal/
alternate buffers and wrapping, regions, tabs, saved cursors/attributes/charsets,
current attributes, parser parameters and fragmented OSC/DCS payloads, decoder/
Unicode join state, input/mouse/cursor/newline modes, title stacks, links and
output-mutated colors. Wider hidden alternate-buffer cells survive narrowing.
Link IDs and their original marker rows/lifetimes, including unprinted links and
native dangling/retired markers, are reconstructed in the receiver. Registered
handlers remain local; functions, UI font/base-theme preferences and input authority are
never imported. Browser cursor initialization remains local across import, and
restored cursor coordinates notify the browser's IME textarea anchor before input.
The adapter uses documented-in-source private fields of pinned
xterm6 and is included in the manager fingerprint and browser build. Engine
changes require adapter validation, not a silent field-name fallback.

Capture occurs after parsed writes. The view serializes imports/writes and
acknowledges only after applying them, explicitly resets parser/decoders on a
reused renderer, and enables input only after the initial screen is ready.
Application query suppressors remain receiver-owned. This closes the earlier
SerializeAddon-only continuation defect; tests/evidence do not establish every
TUI, complex grapheme, assistive tool or OS/browser combination. Old live managers
retain their legacy restore path until explicitly stopped and updated; new
managers reject old clients before leasing input. SerializeAddon remains for
legacy read-only protocol consumers, not the current web checkpoint path.

Checkpoint payloads fit within a1,900KiB state budget and2MiB response bound.
Oversized history retries200 then0 history rows. Omitted text is represented by
blank bounded history rows so logical positions/marker expiry remain consistent;
no omitted output is retained by those placeholders. A concise history-omission
cue survives later deltas/control updates until a complete snapshot replaces it.
It also survives exit, socket closure and retained termination-error refreshes.
Resize goes through the manager and invalidates deltas; the view imports a new
authoritative checkpoint instead of independently reflowing omitted history.
An oversized active semantic state reports `checkpoint_limit`
instead of discarding a partial control or silently changing cell contents. The
service/work remains alive and management remains available; a new view can
retry after the state fits. Row counts alone are not an absolute engine-memory
bound: xterm retains OSC/DCS data up to10M UTF16 units and can accumulate longer
combining-cell strings. No custom truncating parser, async parser addon or disk
transcript is introduced to disguise this engine limitation.

## Input And Request Authority

Settings → Terminal owns default cwd/shell in the `[terminal]` section of the
private settings.toml. It uses the common settings revision, lock and atomic
writer, preserving unrelated/unknown fields in both hosts. Native HTTP and WebSocket require the same per-launch credential; WebSocket also requires an exact loopback origin before any helper starts.
Reads/saves do not install dependencies or start a manager/shell. Save validates
an accessible absolute/tilde directory and executable shell, with an empty shell
meaning the backend's default. Deleted/invalid defaults remain readable for
repair and fail a new launch without silently substituting a folder or booting
a manager. Defaults apply to new instances only. New Terminal captures the
configured shell and, without a selected group, the default cwd through
`GET /api/terminal/settings?launch=true`. Within a workspace it uses its optional
default cwd, otherwise the global default; choose-folder actions supply the
explicitly entered folder. The launch read
accepts an optional `cwd` query override without saving it, validating that actual
folder with the configured shell. A deleted unrelated saved cwd cannot block a
valid group/folder override; malformed preferences and invalid shells still fail.
It submits explicit paths with one creation identity.
An uncertain response retains those
paths/identity across retries even if defaults change or disappear. An unresolved
creation exposes explicit Retry and gates other creations, so discovering its
first group cannot replace the pending request key. Splits supply
the clicked pane's cwd/shell; a choose-folder split overrides only cwd. Explicit
API callers supply their own launch values. Omitted/empty HTTP shell resolves
the host's `SHELL` or `/bin/zsh` before the integration step below.
Existing work and service identity are unaffected. Settings saves return common
preference values together with their matching revision, and Terminal controls
wait for an in-flight common-settings read/write before accepting another save.

Management exposes separate View/Open, Background and End Terminals actions, with
visible/background state text. Background only hides the tab; the same manager
continues owning its PTYs. Opening it never creates a replacement shell. Ending
it uses the existing destructive scope/identity contract. All-background empty
state opens the hidden-tab list; the primary New action creates another instance.

## Folder Workspace And Status

Terminal fills the space directly beside the shared app navigation, retaining the
shared header and accessible main/heading. Its upper rail contains named
workspaces; the lower rail lists terminals across workspaces and focuses the
exact pane. Hidden/background tabs are excluded from this foreground list and
the tab strip while their execution continues. The footer separates Background,
Settings and Management; its dedicated list restores the same executions or ends
their tab. Explicit reported hidden errors/completions mark that footer action.
The top tab strip belongs to the selected group;
the toolbar + creates a visible tab grouping terminals. Split controls belong
to each pane header and target that exact terminal's cwd/shell.
The bottom bar shows cwd, connection/input readiness and live shell count.

Workspace identity is independent of cwd and process lifetime. Each workspace
holds tabs, and each tab holds up to four terminals with independent folders.
The rail + creates an empty named workspace with an optional default folder;
its ⋯ edits these values or removes an empty workspace from the list. Neither
operation creates a shell or deletes a directory. Hidden/retained tabs still
prevent removal. The tab menu opens a new tab in another folder or moves an
existing tab to another workspace; a pane menu can split in another folder.
Workspace movement uses a same-panel action list with checked current membership,
back and keyboard navigation, rather than an OS select or nested popup. Terminal
menus share32px desktop/40px narrow rows, viewport-bounded scrolling and below-trigger
placement when space permits; lower triggers may open above without covering
their trigger. Escape backs out of the workspace list before closing the menu;
outside click/focus, peer switching and resize dismiss it. Polling retains its
destination focus; a changed active tab invalidates that menu's action context.
Normal + uses the workspace default or global default plus configured shell;
normal Split inherits the clicked pane's current cwd/shell. `cd`, rename,
membership changes and selection never relaunch work. No Project, Source,
Workstream or imported Session record is created or reused.

The host stores schema1 workspace IDs, names, defaults and generation-bound tab
membership in owner-private `<data>/terminal-workspaces.json` (maximum128 groups,
32 tab references,2MiB input). Empty groups survive exit, app/service restart and
reboot. Screens/layouts/processes remain memory-only with the existing loss and
reboot limits; stored metadata never replays work. GET only projects current
membership. Explicit reconciliation POST adopts unassigned legacy/CLI tabs into
stable initial folder-named groups and drops stale generation references while
retaining group identities. Existing jobs continue. Writes use the shared local
writer lock, a fresh manager snapshot and atomic private publication; corrupt or
unsafe files are preserved with an error. This metadata joins same-installation
backup/restore, with schema validation before restoration.

Creation and metadata publication are separate operations. A post-creation
storage or manager-read failure returns the known terminal identity plus a
recoverable workspace warning. An uncertain creation retains its key and paths;
retry cannot silently reassign confirmed membership. Moving an existing tab is
an explicit generation-checked metadata operation, preserving its IDs and PIDs.

An active tab title edits in place by clicking its text, F2 or the tab/task menu.
Inactive clicks select; dragging does not open the editor. Enter/focus-out saves,
Escape cancels, composition Enter does not submit, and a failed save preserves
the draft. Task ⋯ actions focus the exact pane, background its whole tab (naming
the number of panes when relevant), rename the tab or end just that terminal.
Menus remain reachable beyond rail scroll bounds and support keyboard dismissal.

Mouse dragging reorders visible tabs inside their current workspace. Alt+Shift+Left/
Right and tab-menu move actions provide alternatives. The host stores only
schema/generation/ordered IDs in owner-private `view-order.json` beside the runtime
scope, separate from payloads and TOML. Writes validate the observed manager generation,
exact IDs, matching workspace slots and unchanged background IDs/slots. Last committed
write wins; manager metadata and this UI cache are not one transaction. A later
manager change is reconciled by generation/membership on read. Reads append new tabs, drop missing IDs and ignore stale generations;
unreadable presentation preferences never disable terminal controls. This cache
shares ordering across web/app origins without restoring jobs or screens.
No runtime upgrade or shell stop is required to change these view preferences.

The Terminal rail can collapse independently of global navigation preferences.
At 1100px and below it starts collapsed and opens as an overlay with its own
close control. Exactly one panel toggle is visible: rail collapse when expanded,
toolbar reopen when collapsed. Every route shares the48px desktop header and
32px search control. Terminal group/task controls remain32px, with one-line
context without duplicate names and the existing40px touch targets at700px and
below. Other routes retain their content density and ordinary page scroll. At700px and below the existing pane selector shows one pane
while all processes remain managed. Lists, tabs and terminal scrollback own
their bounded scroll regions; the Terminal route alone contains document scroll.

`activity: {state, exitCode, completion}` is reported shell metadata, separate
from PTY `state`/`exitCode`, view visibility, connection and input lease. The
initial command state is `unknown`. Supported OSC133 A/B mark prompt/input,
C marks command execution, and D after C marks completion with a 0–255 result
or null when omitted. D after B is an aborted input line and adds no completion;
duplicates/out-of-order D and malformed results are ignored. The in-memory
completion counter persists across the following prompt. The official
[FinalTerm/iTerm2 protocol](https://iterm2.com/documentation-escape-codes.html#shell-integrationfinalterm)
defines these signals; any program can emit them, so they are reports, not
trusted proof of task/agent success. No command text is captured for this feature.

The primary indicator gives hidden ◇ and current selection ✓ precedence.
For other foreground items, a small filled ● requires a live terminal reporting
command/program running; a same-outer-diameter hollow ◦ requires every represented
terminal to be live and report prompt. A grouped tab shows ● when any pane meets
the running condition, ◦ only when all meet the prompt condition, otherwise an
empty reserved slot. Unknown, finished-without-prompt and exited metadata do not
fabricate prompt/running. Exact command/process descriptions and result badges
remain available. A running agent CLI can be waiting internally; ● does not mean
the agent is thinking. Program title activity is a separate report below.

All indicators occupy the shared20px navigation slot. The small ring and dot
share their painted outer diameter; fill distinguishes prompt from execution.
These report-based criteria apply to old and new terminals, with no first-tab
rule or question-mark default. Selected tab underlines and pane frames reinforce
selection; inactive windows retain selected IDs with neutral borders. Tab title
controls retain their12rem width and truncate names. Live indicator/title/result
updates preserve buttons and cannot shift the separate close target.

Programs can report a leading braille glyph in their OSC0/2 title. Render that
exact title prefix separately beside the name, update it from stream metadata,
and remove it when the reported title removes it. Preserve manually named tabs.
For a group, represent the focused pane's glyph when present, otherwise the first
reporting pane in that tab. This is program-supplied title presentation, not a
LocalBrain agent-thinking/needs-input protocol. A live agent CLI or shell command
is not proof that the agent is working. Do not synthesize program activity from
shell execution, output text or silence. Non-prefix braille remains ordinary
title text. No native Dock integration, OS badge or multiwindow model is added.
Displayed panes receive stream metadata; inactive/hidden panes also refresh
through the existing three-second model poll while the document is visible.
A brief command can finish between polls. Hiding or a background browser page
does not imply that its last displayed glyph is a fresh liveness guarantee.

Shell command status remains separate in the status bar and descriptions:
reported running, prompt waiting, completion/result and unknown retain their
exact metadata meanings. Unseen completion, failure, faults and termination may
add a separate result/status badge without replacing the view or program mark.
Unknown state is a description, never a default question-mark icon. Before a
confirmed shell exit is retired, stop means its result is unknown and error means
a nonzero exit; this transient result does not prevent retirement. Termination,
input faults and closing retain precedence. Output silence/text and shell
liveness never imply prompt, busy, success or a request for user input.

The rail footer's Background disclosure expands an inline list, rather than a
modal. Hidden tabs stay outside the foreground strip/task list. Its rows retain
◇, program title glyphs, completion/error badges, useful workspace/count context,
name-to-restore and a direct whole-tab × with explicit accessible scope. The
header retains aggregate hidden count/error/new-completion attention. The list
scrolls within a bounded footer while the disclosure and utilities remain
reachable. On initial load, retained hidden work is expanded. Explicit Hide or
the all-background empty-state action reveals/expands the rail; ordinary polling
preserves manual collapse. This is view-local state, with no new stored setting.
Restoring returns to the exact tab/input and closes the narrow rail overlay.
Surviving row focus remains through refresh; final focused-row removal returns
to the disclosure, and Management retains its modal focus rules.

Actual painted input focus in an active window is still the acknowledgement
condition; inline navigation, selection, hiding or window activation alone does
not imply command completion or mark every pane seen. Hidden work can still run.

New zsh terminals created through the web/app host automatically report OSC133
prompt/running/completion/result and OSC7 cwd. A versioned launcher and startup
shims live under owner-private `<data>/terminal-shell/zsh-<identity>/`, independent
of app and runtime payload paths. The selected zsh remains the shell; the launcher
restores its `SHELL`, chains user `.zshenv/.zprofile/.zshrc/.zlogin` at startup scope,
tracks effective ZDOTDIR (unset/empty/export), and appends deduplicated precmd/
preexec hooks without capturing command text. The completion hook captures `$?`
before other work and emits UTF-8 URL-encoded cwd. User startup files are not
edited. Generated files are private and hash-verified, never silently overwritten
when corrupt; an interrupted preparation resumes only matching owned files.
Preparation occurs on explicit creation, not list/page reads. Existing launchers
remain usable across app Quit/replacement and are excluded from backup as
reconstructible files. Existing terminals receive no injected commands or new
hooks; raw CLI launches and other/unreported shells retain unknown command metadata
without changing their view marks.
Real zsh5.9 login, changing ZDOTDIR across startup stages, custom hooks and command
results have dedicated PTY coverage; unusual global startup configurations are
not universally certified. Existing compatible OSC133 integration can also report
status; these signals remain reports rather than trusted proof.

Unseen completion is local to a browser view and manager generation, keyed by
terminal and completion counter. It clears only after that completion's frame
is rendered while the document/window are visible/focused and the xterm input
textarea actually has keyboard focus. The witness follows a full xterm render
and subsequent animation frame, not just parser/import completion; synchronized
output withholds it. Pane menu focus, selection, minimization, hidden tabs and reconnect alone
cannot mark it seen. Seen command failure remains in metadata until superseded;
the ordinary prompt symbol is restored after attention is seen. No additional
process polling, transcript, index or persistent read history is used. Within one
manager generation, older HTTP list metadata cannot replace newer stream sequence
metadata; a new generation clears prior view attention and group selection state.

The default shell is the existing login/interactive shell and startup files;
explicit executable and accessible cwd are validated. No shell rc modification.
One current, expiring per-view lease owns input/resize. Other views observe and
explicitly take over; stale owners cannot type or resize. Browser shell shortcuts
stay terminal-owned, with Shift+Escape returning focus to the pane menu.

Private Unix IPC uses owner-only directories, files and socket. HTTP mutations
require bounded JSON, loopback Host and exact same Origin; WebSocket is checked
before any runtime command. Terminal output cannot request clipboard reads or
writes, automatic URL/file execution, images or external network fetches.
The headless engine alone answers CSI/DCS and OSC4/10/11/12 color queries,
including while detached. The shared default code theme and ordered output color
changes determine replies; browser query suppression preserves color mutations
in mixed commands. The v3 handshake rejects older renderers which could otherwise
duplicate color replies. Paste keeps bracketed modes and asks before unbracketed multiline input.
Mouse binary reports use byte-preserving transport under the same input lease.

## CLI

Both `lb` and legacy `localbrain` use the existing command entrypoint.
`terminal list` inspects runtime IDs; `terminal stop ID|--all` ends that scope;
`terminal service install|status|start|stop|restart` manages optional setup and the
manager. Help/list/status never start, install or create shells. ID and --all are
exclusive. All/service termination confirms once on a TTY; scripts with live
work require --yes. --force preserves identity checks. --json writes only results
to stdout and errors to stderr with a nonzero status. Service restart creates no
shells. Runtime IDs, tab IDs and imported Session IDs are distinct domains.
