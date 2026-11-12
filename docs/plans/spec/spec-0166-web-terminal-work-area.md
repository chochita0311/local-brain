# SPEC-0166: Web Terminal Work Area

## Metadata

- ID: `spec-0166`
- Status: `approved`
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Parent PRD: [PRD-0028](../prd/prd-0028-web-terminal-work-area.md)
- Run: [RUN-246](../run/run-20261112-246-terminal-final-audit.md)
- Profile: `fullstack-product`
- Lanes: contract/backend/infra → frontend/integration → docs/evaluation
- Created: `2026-11-10`

## Fixed Technical Decisions

1. TF-01: xterm.js6.0 browser + headless6.0 + serialize0.14 and fit0.11.
   Independent Node manager owns node-pty1.1 processes and logical screens.
   Python owns CLI, optional setup/launch/client and the FastAPI bridge. Use
   Node20+ from PATH, require macOS for production; no custom emulator/core reuse.
   A private cache installs the pinned npm lock only on explicit setup; status,
   page visits and service start never silently download packages. An unavailable
   dependency has one setup action; other app routes still work. Setup does not
   create a service/shell. `service install` is the corresponding explicit CLI
   setup action required by the already-planned optional-install boundary.
   Select the native spawn helper using the installed Node process architecture,
   including a Node running under Rosetta. Prepare both bundled Darwin helpers
   during setup and explicit Start, including caches installed before switching
   Node architecture. Missing helpers invalidate setup readiness. Build the browser ESM from xterm's
   published CommonJS entry; check the resulting DECRQM response as well as
   asset hashes to catch bundler regressions without patching the dependency.
2. TF-02: defaults use the existing system shell with login/interactive startup
   and existing user files. Explicit cwd must exist and be accessible; new panes
   inherit a known current/start cwd. No user rc modification. The manager's
   launch environment carries ordinary shell/path/locale context, no persisted
   credential/environment dump. Shell override is an executable, not arbitrary
   command text. Tests isolate HOME and use synthetic commands.
3. TF-03: one manager per local cache/config scope; owner-only local IPC and
   identity/version handshake. A macOS transient launchd job separates its
   lifetime from the invoking backend/terminal. Bootstrap in the logged-in
   macOS GUI domain with RunAtLoad and KeepAlive=false; delete the owner-private
   temporary launch configuration immediately after submission, including failure.
   No login LaunchAgent install or persisted environment dump. Plain launchctl
   submit is excluded because its OnDemand=false setting restarts clean idle exits.
   State/list/help cannot boot it. Normal backend restart keeps the manager.
   Control requests have bounded frames/timeouts and explicit runtime IDs.
   Stop blocks creation, terminates only owned process groups/descendants,
   confirms exit and then exits the manager; never broad killall. TERM/HUP has
   a3s grace, then owned-process KILL with a2s confirmation window. Unknown
   ownership/liveness is failure; force never bypasses identity. Start/restart
   must not race a stopped/old generation. Bind destructive confirmations to
   generation and exact runtime-ID scope; changed targets require renewed review.
   Capture original root identity and preserve proven session membership across
   normal shell exit. Identity readers are asynchronous and shared in flight;
   lost inspection never authorizes a replacement PID. All signals use the
   identity gate, including HUP. An empty manager may idle-exit after
   60s with no views/terminals. Plain PID kill is not the supported stop path.
   A dead manager with a remaining identity file is an unclean loss, not proof
   that its children ended. Stop/restart must report that uncertainty. Explicit
   new/start may create a fresh manager without replay or adoption; it does not
   clean up the old unconfirmed work. A failed terminal stop remains visible
   and retryable, with its record retained.
4. TF-04: all terminal output and tab/layout metadata are bounded manager memory.
   Reconnect while it lives restores layout and exact supported VT state; manager
   stop/reboot starts empty and never replays commands. No transcript/DB/browser
   content storage. Only private IPC/setup/identity files persist; diagnostics
   contain no input/output. Per terminal1000 scrollback rows,128KiB raw tail;
   parse backlog pauses PTY at1MiB and resumes below64KiB. Behind viewers get a
   new serialized state, with explicit history truncation if needed. Maximum
   32 retained terminals,4panes/tab,240columns/80rows;2MiB response cap.
5. TF-05: verify one/eight idle instances, TUI/full-screen/Unicode and flood while
   another control/view remains usable. Initial target: manager RSS below96MiB
   for one idle shell and160MiB for eight, manager idle CPU below1% of one core,
   p95 local input-to-render below150ms and control during flood below250ms.
   Report actual browser/backend/manager/child costs separately and scope timing
   evidence; these targets do not establish every-device or long-term stability.
6. TF-06: input/resize require a single current per-view lease. Other windows
   observe and explicitly take over; stale/disconnected owners cannot type.
   Hidden pages detach; visible return reconnects from runtime state. Visible
   streams wait for rendering acknowledgements; bounded tails avoid slow-client
   memory growth. UTF-8, IME, bracketed paste, Ctrl keys, TUI and resize preserve
   terminal behavior. Terminal focus owns shell keys; ordinary shell shortcuts
   still work outside it. Block clipboard reads/writes from output, automatic
   URL/file execution and unrequested network effects. Validate local Host and
   exact same Origin for HTTP mutations and WebSocket, including desktop denial.

## Surface And Interaction Contract

The2026-11-11 follow-up removes dependence on installed D2Coding or per-install
font instructions. Deliver a reviewed, locally served terminal font covering
Hangul/Latin and the reproduced Powerline symbols, keep13px, and measure only
after its load succeeds. A missing asset must be recoverable and visible rather
than silently treated as correct rendering. Keep this dependency route-local and
excluded from native packaging. Glyph coverage is distinct from UTF-8 and
Unicode cell-width rules; arbitrary private-use glyphs are not universal coverage.

Complete the live-manager checkpoint contract without an unbounded raw replay or
disk transcript. Preserve supported parser fragmentation and nonvisual VT state
as well as serialized screen contents. Version any pinned-engine state adapter,
validate its shape, include it in the build identity, and negotiate incompatible
renderers before input. Differential future-output and actual new-renderer checks
must establish continuity; text-only screenshots do not prove state restoration.
The selected adapter is `xterm6-v3`: packed cell runs plus typed parser/service
data, with receiver-owned handlers/prototypes/link markers. It replaces synthetic
VT repaint in the current web path; legacy read-only consumers keep the old data
shape. A1,900KiB checkpoint budget leaves metadata room within2MiB. Drop only
history to fit; if active semantic state still exceeds it, report a recoverable
limit and preserve execution/management rather than silently changing state.
This is the existing frame-budget failure boundary, not command replay or a
new persistent recovery service. Track the underlying engine's large-control/
combining-string memory limitation separately from ordinary measured workloads.
Rows carry their stored width independently of the viewport, retaining hidden
alternate-screen cells after narrowing. Link records retain actual marker rows,
including unprinted/dangling/retired states. Omitted history text uses bounded
blank placeholders to preserve logical coordinates; its cue remains visible
through subsequent output and lease updates until full restoration.

The2026-11-11 human revision replaces per-creation folder/shell dialogs with
Settings → Terminal defaults. Store feature-owned cwd/shell under `[terminal]`
in the existing private settings.toml, preserving unknown/common values and the
shared revision/atomic-write lock. Reading/saving settings requires no Node,
install, manager start or shell launch; desktop/unsupported editions admit no
Terminal pane or endpoints. Validate directory/executable on save and before
using stored defaults. Invalid/stale settings retain correctable input and do
not silently fall back. Explicit defaults affect future terminals only.

New Terminal creates immediately from the latest saved defaults. Splits create
immediately with the clicked pane's known cwd/shell. No dialog or command replay;
creation request identities prevent duplicate instances during a pending/retried
request. The web action captures validated cwd/shell once through the settings
launch query and retains that explicit request and identity after an uncertain
response; later defaults must not change a retry's parameters. Keep exact path
characters, including leading/trailing spaces. Terminal saving waits for common
settings reads/writes and receives their complete matching values/revision.
Management exposes separate View/Open, Background and End actions;
all-background empty state opens that list rather than implicitly making another
shell. Keep concise labels and existing Settings form/control geometry. Shared
settings changes must not lose the revision of another preference section.

`/terminal` is web/macOS only, above Sessions. Keep the existing shell and locally
load xterm assets only here. Empty page has a New Terminal action. Tabs have a
selection and distinct ×; each pane has focus/state/split/×. The first split
chooses two side-by-side or stacked panes; three and four use a balanced2×2
grid, with a vacant cell when there are three. Narrow screens show one selected pane with a
switcher. Tab menu has background action. Management dialog lists visible and
background tabs and service status; Open/End and Start/Stop/Restart are distinct.
Use existing semantic tokens, readable labels, short tooltips, native focus/dialog
semantics and contextual errors. No long instructional banners or diagnostic rail.

## CLI And IPC Contract

`lb terminal list`, `stop ID|--all`; `service install|status|start|stop|restart`.
Keep `localbrain` compatibility and all existing commands. ID/all are exclusive;
no target is a usage error. Help/status/list never start/install. JSON has only
results on stdout; errors on stderr and nonzero exit. Destructive all/service
actions confirm once on a TTY and require --yes otherwise. --force keeps the
same ownership bounds. Install/start require explicit commands; restart creates
no shells. Web exposes the same command outcomes via bounded JSON, plus a
WebSocket that bridges data/ack/input/resize/claim/release to private IPC.
Creation uses an idempotency key; lost replies must not create duplicate PTYs.

## Ownership And Preservation

`terminal/` owns optional setup, launch/control and manager assets; no generic
service framework. App composition only admits it for web and supported OS.
Desktop packaging excludes its Python/runtime/browser assets, not just menus.
Sessions and workspaces stay unchanged; no unsupported provider link inference.
Feature data/cache files follow existing private storage and owner rules.

## Acceptance And Evaluation

Map PRD A-01–16 to synthetic real-PTY/control/process tests, CLI/boundary tests,
headless mode/snapshot tests, actual wide/narrow browser interactions and a
read-only package/wheel admission check. Exercise ordinary exit, ×/background,
service-stop/start/restart, view/backend disconnect, stale lease, setup failure,
invalid selectors/origin/IDs, absent runtime and control during flood. Complete
the existing full Python suite/privacy, focused JS checks and asset checks.
Required reviewers: contract, design, functional and interaction. Process control,
auth/concurrency and multiple consumers require the governed fresh code challenge
before completion; record source/physical IME/native-host evidence separately.

## Open Blockers

None requiring a new product decision. Verify dependency/runtime/OS behavior;
return through Spec/planning if it contradicts the locked contracts. Runtime
retention is deliberately memory-only for this first stop/restart delivery.
The implementation/evaluation is now recorded in Run242/Eval0158; required
physical IME and full resource/regression evidence remain acceptance gaps there,
not unresolved engine or product choices.

Run244 identified a confirmed technical acceptance blocker: fresh-view restoration
loses an incomplete CSI/OSC and separately fails scroll-region, saved-cursor and
custom-tab-stop differential checks. A complete supported VT checkpoint and
renewed before/after witnesses are required before broad TUI/reconnect parity.
This was an implementation gap, not an accepted semantic change or a new demand
for IDE convenience features. Run245/Eval0161 now close it with typed checkpoint
continuation, direct macOS input-method/browser/PTY checks, actual hidden streams
and representative corpus/flood measurements. No technical blocker remains for
that bounded Run. Hardware-keyboard/Safari-app repetition, VoiceOver, complex
graphemes, long soaks and other versions retain the evaluation's explicit limits.

## Continuity Notes

2026-11-11: Run243/Eval0159 pass the approved saved-default/quick-launch revision,
including exact paths, shared settings read/write ordering and stable explicit
New/Split retries. This does not close the original Run242 whole-feature gaps.

2026-11-12: Run245 passes the supported-checkpoint, bundled-font and observed
WebKit Korean-input corrections plus renewed evidence. Current input/font/state
contracts remain owned by the terminal policy; Eval0161 separates actual native
OS input from synthetic composition and preserves earlier failed evidence.

2026-11-12 final audit: Run246/Eval0162 own the latest reviewed implementation.
The v3 checkpoint retains browser-local cursor initialization and updates the
IME anchor; headless owns ordered color queries even while detached. A bounded
PTY writer and explicit interrupted-input fault preserve management/peer work,
without pausing cooperative duplex output. Native composition cancellation,
keyboard-tab focus, helper preparation and UTC-tagged birth-identity recovery
(with legacy/unknown formats protected) are verified
within the unchanged product boundary. Earlier results remain historical; no
supported technical blocker remains in the final evaluated scope.
