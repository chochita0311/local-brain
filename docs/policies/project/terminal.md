# Web Terminal

## Delivery And Ownership

Terminal is a macOS web feature above Sessions. It is excluded from native app
assembly, routes, CLI registration, startup and packaged terminal assets. Windows
and external iTerm2 windows/attachment are outside this delivery.
`terminal/` owns setup, control, IPC and PTYs; the existing Session, Usage, search
and source pipelines do not consume terminal output or infer provider identity.
The canonical user instructions are the conditional bilingual
[Terminal guide](../../../src/localbrain/content/docs/terminal.md).

Browser xterm6 and fit render only this route. The independent Node20+ manager
uses node-pty1.1, xterm headless6 and serialize0.14. Python provides CLI/setup,
launchd control and the FastAPI HTTP/WebSocket bridge. A pinned optional npm lock
is installed into a private cache only by explicit setup; it is separate from
web asset build dependencies. Other app features do not require Node/npm at run
time. No Herdr core, custom emulator, CDN, login agent or terminal window is used.

Readiness requires a matching lock marker, present main entry files for every
required runtime package, and both Darwin spawn helpers. Setup and explicit
Start prepare both helpers as owner-only executables, permitting later native/
Rosetta Node selection without another download. Partial module/cache loss returns the setup action;
this existence check is not a full integrity audit of every dependency file.

Both new manager screens and browser views select the pinned Unicode11 addon0.9
so mixed Hangul/modern emoji use matching cell widths. Each terminal advertises
its width version; a new browser viewing an older live manager keeps its Unicode6
rules until the user explicitly updates that service. This does not establish
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
- Closing a view/navigation preserves execution. Pane/tab × ends its scope;
  tab background hides but retains its layout. Management can reopen or end
  tabs and individual terminals, or end all. Tabs have up to 4 panes; the scope
  retains at most 32 terminal records, including exited screens.
  Two panes can be side-by-side or stacked; three/four use a 2×2 grid. Below
  the shared 700px breakpoint, a selector shows one pane while keeping the others.
- Service stop blocks new creation, terminates its owned live descendants with
  TERM/HUP, waits3s, then uses KILL if needed with2s confirmation. POSIX session
  membership also catches ordinary background jobs after their shell exits;
  a short-lived Python inspection helper reads session IDs and process birth/group
  identity only during control/exit cleanup, with no idle polling process. One
  asynchronous reader is shared by concurrent checks so input remains responsive. Intentionally
  detached work remains stoppable while live ancestry proves ownership;
  after both that link and original session membership are lost, cleanup is not
  guaranteed and may require the program's own controls. There
  is no broad killall. Unknown identity/liveness or unconfirmed exit is failure;
  force skips grace while preserving ownership. Create/start/stop/restart/setup
  share a local control lock; generation and exact target snapshots bind destructive
  confirmations. Changed scope or generation is rejected for renewed confirmation.
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
writer, preserving unrelated/unknown fields; the pane and endpoints are web-only.
Reads/saves do not install dependencies or start a manager/shell. Save validates
an accessible absolute/tilde directory and executable shell, with an empty shell
meaning the backend's default. Deleted/invalid defaults remain readable for
repair and fail a new launch without silently substituting a folder or booting
a manager. Defaults apply to new instances only. New Terminal captures validated
cwd/shell once through `GET /api/terminal/settings?launch=true`, then submits
explicit paths with one creation identity. An uncertain response retains those
paths/identity across retries even if defaults change or disappear. Splits supply
the clicked pane's cwd/shell; explicit API callers supply their own launch values.
Existing work and service identity are unaffected. Settings saves return common
preference values together with their matching revision, and Terminal controls
wait for an in-flight common-settings read/write before accepting another save.

Running exposes separate View/Open, Background and End Terminals actions, with
visible/background state text. Background only hides the tab; the same manager
continues owning its PTYs. Opening it never creates a replacement shell. Ending
it uses the existing destructive scope/identity contract. All-background empty
state opens the management list; the primary New action creates another instance.

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
