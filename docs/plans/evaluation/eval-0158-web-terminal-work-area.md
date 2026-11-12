# EVAL-0158: Web Terminal Work Area

- Status: `complete`
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Active Spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Parent PRD: [PRD-0028](../prd/prd-0028-web-terminal-work-area.md)
- Run: [RUN-242](../run/run-20261110-242-web-terminal-work-area.md)
- Profile / attempt: `fullstack-product` /1
- Evaluators: primary contract/design/functional/interaction; named independent code challenger.
- Result: `PASS` for performed checks
- Evidence Coverage: `partial`
- Acceptance impact: implementation is available locally; A-06 physical IME and
  A-08 hidden-view/representative regression evidence remain partial and block the
  whole Feature pass. No product decision is reopened or criterion waived.
- Completed: `2026-11-11`

## Environment And Scope

Actual macOS26.5.1 arm64, Python3.11.15, Node24.15.0 and Chrome156.0.0.0.
Node20.0.0 was additionally downloaded from the official distribution and checked
against its official SHA256 before testing the minimum build version. Public
engine dependencies were installed into isolated owner-private test roots; HOME,
shell startup files, DB and source roots were synthetic. No personal Session,
default terminal service, installed app or external iTerm2 was exercised.

The engine-only entry probe was narrower evidence; the following observations
supersede that entry limitation, without establishing every host or long-run
stability. No native app build, commit, push or publication occurred.

## Evaluator Results

| Evaluator | Result and checked boundary |
| --- | --- |
| Contract | PASS: independent service/PTY ownership, bounded IPC/screens, one input/resize lease, exact Host/Origin, generation/target-bound destructive operations, CLI/web outcome parity and explicit web/desktop admission. Source/package checks establish exclusion, not a rebuilt native binary. |
| Functional | PASS: real PTYs and launchd lifecycle, actual Chrome shells/TUI/reconnect, CLI/boundary fixtures, whole Python suite and compiled asset checks. Failures and their repairs are below. |
| Design | PASS within observed wide/700px/320px layouts: existing shell/tokens, compact header/tabs/pane controls,2×2 grid, selected-pane narrow view, contextual errors and service management. No permanent instructional rail. |
| Interaction / UX heuristic | PASS for observed create/split/select/background/reopen/end, service controls, takeover, keyboard escape/focus, navigation and reconnect. Clipboard-event Unicode paste is not physical OS IME or a complete system-clipboard matrix. |

## Acceptance Map

| PRD | Evidence and observation limit |
| --- | --- |
| A-01 | macOS web menu above Sessions and real route inspected; desktop/non-Darwin admission tests, CLI denial and actual PyInstaller data collection exclude terminal runtime/assets/guide. Native binary was not rebuilt. |
| A-02 | Explicit component installation, stopped-page/no auto-start, valid shell/cwd, input/resize and invalid paths exercised. Successful and failed idempotency retries plus a live key after258 closed histories do not duplicate PTYs. Corrected setup can retry after failure. |
| A-03 | Multiple tabs, four panes/fifth disabled, both first-split directions and later2×2 arrangement; background/reopen keeps identities. Pane/tab termination scopes checked. A101-character tab title remains bounded with full title text; narrow pane switching and tab overflow use local scrolling. Full arbitrary-name/assistive-tool coverage is not claimed. |
| A-04 | Real creating client exit and web backend restart preserve the original PTY; browser reload restores edited vi alternate buffer. Stop/restart starts empty. Injected manager SIGKILL reports unclean loss, retains uncertainty, and explicit fresh creation never adopts or replays old work. Ordinary idle exit stays stopped after111s; no launchd respawn. |
| A-05 | TERM/HUP/KILL identity gates, original root birth/parent/group/session, ordinary background-job cleanup, stopped-generation conflict, failures and retry observed with synthetic processes. Unknown inspection retains the record/error. Independently detached programs can escape ownership after losing both ancestry and original POSIX session; the guide states this limit. |
| A-06 | Chrome: Unicode clipboard-event paste, CJK width, Ctrl-C/Ctrl-L, ordinary Escape, Shift+Escape/menu/focus return, actual vi200-row alternate screen, resize/reload and binary mouse high-byte transport observed. CSI/DCS queries receive exactly one reply. Physical Korean IME, real OS clipboard combinations, Safari, comprehensive mouse/wheel and screen-reader use remain unverified; physical IME blocks full acceptance. |
| A-07 | Multiple real views, explicit takeover and old-view read-only behavior; stale lease input/binary/resize, reconnect and readiness ordering covered. Connection failure stays distinct from process exit; visible recovery is confirmed before clearing its error. |
| A-08 |0/1/8-shell manager/child measurements and live flood/control/peer timing below meet measured component budgets. Final warm browser/backend/manager/shell RSS and CPU, no-terminal-view background operation and empty Sessions response comparison were also collected. Browser input-to-DOM timing and JS heap are separate. A truly hidden-but-open document, controlled cold/warm representative Sessions/search corpus and long soak remain unobserved; the tool's two windows both reported visible. Do not assert a universal footprint/regression pass. This gap blocks the whole Feature pass. |
| A-09 | Memory-only buffers/layouts, explicit setup/launch and no output ingestion/DB/browser transcript path inspected; source/Session/Usage suites pass. The user's shell/programs retain their own history/logging/network behavior. No shell rc edits or filesystem sandbox promise. |
| A-10 | Real shared navigation/Back, empty/connection/crash/recovery/exited states, wide/narrow/320px containment and pane selector observed. Sessions visit loads no terminal JS/CSS/xterm; whole-suite preserved consumers pass. Existing real search/model latency was not benchmarked. |
| A-11 | HTTP JSON limits and exact origin including scheme, WebSocket rejection before runtime access, local ownership and desktop denial tested. OSC52 inert, no output-triggered URL/file/network execution; mouse binary remains leased. Full arbitrary escape-sequence compatibility is not claimed. |
| A-12 | English/Korean conditional guides explain all close/background/service operations, ID versus service, bounds, update steps, uncertainty, detached-child limits and shell-owned history. No real-IME/Safari/long-run claim. |
| A-13 | CLI directly accesses the same launchd manager after its creating client exits; list/status/help never bootstrap. Pane/all/service scopes and unclean-loss errors match management semantics. Identity fixtures refuse replacement/unowned PIDs; no other user terminal was signalled. |
| A-14 | Actual stop/restart empties work, old shell exits, no temporary launch file or launchd job remains after stop. Generation/scope races, create-during-stop, pending inspection, setup failure/readiness invalidation and unclean loss covered. Source/version conflict shown in actual UI, then explicit restart loaded the current manager empty. No release deployment was performed. |
| A-15 | Wheel supplies both lb/localbrain entrypoints; command target/help/JSON/stderr/exit/confirmation/force tests pass. Healthy stopped bulk stop remains a no-op; unclean stopped bulk stop now fails with empty stdout. No existing global lb or user shell configuration was overwritten. |
| A-16 | Compact primary actions, pane/menu controls, visible/background management, named service actions and scope confirmation inspected at wide and320px. Long tab label bounded; keyboard focus leaves terminal via Shift+Escape while plain Escape reaches TUI. Broad assistive-technology and physical-input acceptance remains separate. |

## Verification

- Final permitted full Python suite: **1,618 tests, OK (19 skipped)**. The skipped
  cases require the explicit isolated PTY engine. All 19 current real-PTY test
  methods have successful observations across the 30-case focused run and the
  targeted snapshot/startup/crash3 and inspection-failure1 runs; these are separate
  executions, not 1,618 real-PTY checks. Final terminal-only 35: OK, 19 skipped.
- Minimum Node20.0.0 additionally passed two real-PTY tests for login/interactive
  startup with ZDOTDIR and owned-child termination/empty restart. This is a
  targeted minimum-version witness, not the whole19-case Node20 matrix.
- Final browser/manager JS syntax and terminal/Mermaid asset checks passed.
  Terminal check also runs the compiled mode-query parser under Node24 and20.0.0.
  Pinned registry URLs and public package integrity match; no engine upgrade.
- Final wheel inspected for both entrypoints and12 source-byte matches including
  manager/ownership/inspector/lock, browser assets and bilingual guide. Actual
  desktop data collection inspected125 admitted files, zero terminal assets.
- Repository privacy passed for1,840 candidate files; generated plan catalog
  and final whitespace checks passed. They do not establish runtime behavior.

One unpermitted whole-suite attempt could not bind the existing Drive transport
fixture's loopback server and hit an unrelated source-atime assertion. The
permitted rerun above passed without changing those consumers or weakening their
tests. Initial Docs fixture inventory/highlighting assertions and two misplaced
test-tail assertions were corrected; they were test-oracle defects. uv sync
initially pruned37 pre-existing optional packages; their exact versions were
restored before subsequent checks. No remaining environment removal is intended.

## Component Performance

| Workload | Observed result |
| --- | --- |
|0/1/8 idle shells | Manager RSS53.3/54.5/64.3 MiB; manager plus shell RSS for1/8:56.9/83.9 MiB. Five-second CPU samples0.0/0.197/0.198% of one core; coarse ps sampling is not a zero-CPU guarantee. |
| Live6.5MB producer | Producer still running; control p95 0.805 ms/max3.173 ms, peer input-to-headless12.0 ms, raw history123,744 bytes, manager RSS77.7 MiB. This is IPC/headless timing, not browser paint. |
| Four TERM/HUP-resistant panes ending | Total3,556 ms including the3s grace; another original-PID pane responds in4.18 ms; control p95 0.506 ms/max0.985 ms. |
| Chrome one active pane |20 local input→DOM plus next-animation-frame samples: p95 48.6 ms/max49.3 ms; JS heap4,729,466 bytes. This is neither whole-browser RSS nor compositor-paint instrumentation. |

Final-code five-second samples additionally separated the DevTools-owned Chrome
process tree from the isolated Python server, manager and shells. The browser
parent was confirmed to be the DevTools tool; the user's other Chrome process
tree was excluded. All sampled process sets stayed stable within their interval.
RSS sums may count shared pages more than once and include the tool browser's
existing cached/render processes; these are warm observations, not a clean
browser startup cost or a causal per-terminal allocation.

| Final state | Tool Chrome RSS / CPU | Backend RSS / CPU | Manager RSS / CPU | Shell RSS |
| --- | --- | --- | --- | --- |
| Sessions baseline, manager stopped |920.4 MiB /1.78% |76.6 MiB /0% |0 /0% |0 |
| Terminal empty, manager stopped |919.0 MiB /0.99% |79.3 MiB /0.198% |0 /0% |0 |
| One shell visible |923.2 MiB /1.386% |79.3 MiB /0.198% |57.3 MiB /0.198% |3.14 MiB |
| Eight shells, four panes visible |930.1 MiB /1.583% |79.3 MiB /0.198% |66.2 MiB /0.198% |25.7 MiB |
| Eight shells, Terminal view closed, Sessions open |865.4 MiB /0% |80.3 MiB /0% |67.8 MiB /0% |25.7 MiB |

Opening an additional Sessions window while Terminal remained visible measured
1,117.8 MiB browser RSS; both windows reported document.hidden=false. It is not
hidden-page evidence. The identical warm, empty synthetic Sessions HTML request
measured 20 samples before/after eight retained shells: p95 4.5/3.6 ms, maxima11.6/4.0 ms.
This checks that fixture response only; it is not real-corpus reading/search,
DOM interaction, a controlled causal performance comparison or model latency.

The launchd resource run preceded the final failure-state/cache/UI repairs; those
measurements are bounded witnesses, not a claim of all-workload final-build memory.
The final Chrome timing follows the compiled-renderer repair. Fresh idle figures
do not predict the footprint after filling all 32 retained screens.

## Independent Challenge And Adjudication

Named `review_challenger`, configured gpt-6.1-sol/max, initial no-history fork;
actual internal model and OS-enforced sandbox fields were unavailable. Each turn
was read-only and non-executing, with no build/test/install/runtime mutation,
publication, delegation or acceptance authority. Initial discovery received raw
frozen baseline/candidate, full contracts/callers/config/guidance and validation,
without author reasoning or candidate hints. Later turns were informed repair or
new-delta review. Context/method independence does not imply independent source
lineage or supplied validation data.

Baseline was HEAD `4ff4a2daf6a714063b19ba077bb169711441bdaa` plus the initial
three planning-file overlays; complete baseline manifest SHA256
`0f157fbb72befc209de208c3eadecc57c667ff069085a29f7595d9ed0e2a6f74`.
Each candidate was a separate immutable full-tree bundle, with matching complete
path/content hashes checked by the reviewer:

| Turn | Candidate manifest SHA256 | Scope / return |
| --- | --- | --- |
|1 | `8e8d98c52a5b422d0f480b522518814892691ed45ba59ae6a7528643312417bd` | Fresh process/auth/concurrency/consumer omission discovery. |
|2 | `08d3ea7ef7a14ff09416de63b56eae5765dd6a309da5273d86b75d508d3122b1` | Informed repairs; original-root identity, stopped-generation and focus candidates. |
|3 | `0e2b6b451c7253fd84c6feb741524e3590045173bc191f3a74342606c8aef677` | Signal-gate and fixture delta; direct node-pty HUP bypass identified. |
|4 | `3449e89488a1f596cf446aca38fae6a7ce3ba3f838514a990a22fab36fd7f574` | Async inspection/signal/readiness repair; no further concrete candidate in scope. |
|5 | `ef8b0aa4fdc88ef53e7012e546b1c44e54ea254419b9ad13994bc792c90e3c1c` | Actual idle-respawn counterexample and bootstrap repair; no further product-lifecycle candidate; setup-test platform assumption noted. |
|6 | `5e39c6666bc9de6aae24f49799626b060a927d9889c82ee57dbaeea7f06a299c` | New cache/crash/failure/compiled-renderer deltas; unclean CLI bulk completion candidate and Node20 loader evidence gap. |
|7 | `b560ecffd955e8ecd3fdd0fe77e31f0d617e4eeab0d34e7bdc77372a7b61b848` | Three-path repair confirmation; both repairs supported, no residual candidate within that delta. Final docs/package/cleanup remain primary responsibility. |

No caller hard time/token limit was imposed. Initial allocation was one fresh
pass plus evidence-driven repair witnesses. Seven turns were spent, with no
pending worker commitment. Additional checkpoints addressed changed source,
observed process/runtime counterexamples or a concrete finding; they were not
unchanged reruns until finding-free. Final validation/docs/cleanup capacity was
reserved. Finding counts and reviewer agreement do not determine acceptance.

| Claim / trigger and causal location | Primary status / action / evidence and limit |
| --- | --- |
| Destructive scope or generation changes after confirmation | supported / fixed: exact runtime-ID/generation snapshots validated at controller and manager; changed/empty/stopped races tested. Existing implementation omission, not an authorized behavioral delta. |
| Duplicate terminal-query replies and lost legacy mouse bytes in browser bridge | supported / fixed: headless alone answers CSI/DCS, including DECRQM; byte-preserving binary transport under lease. Real exact-one DCS/DECRQM and high-byte mouse witnesses. Broad protocol compatibility unproven. |
| Failed creation key prevents corrected retry; later cache pressure evicts live creation identity | supported / fixed: failed keys removed; pending/live keys protected, bounded settled history. Duplicate/retry and258-history real-PTY witness; resource bounds retained. |
| Origin comparison misses scheme | supported / fixed: exact request-origin scheme/host/port checked before mutation or WebSocket runtime operation; mismatch tests. |
| Root PID replacement or ownership loss permits signals; direct pty.kill HUP bypasses gate | supported / fixed: saved birth/parent/group/session and revalidation apply to all TERM/HUP/KILL. Pinned node-pty source confirmed the bypass; pure ownership fixtures discriminate reused roots and detached/reparented children. No broad PID-only fallback. |
| Pane-menu Escape consumes TUI input after focus leaves menu | supported / fixed: focus departure dismisses menu; scoped key handling and composition guard. Real raw Escape byte1b and keyboard menu traversal observed; physical IME remains a gap. |
| Plain launchctl submit respawns an intentionally idle-exited manager | supported / fixed by primary counterexample: transient GUI bootstrap with KeepAlive=false; real111s observation plus independent-client/restart/stop probe. User-domain bootstrap failed; production uses logged-in GUI domain. |
| Setup failure leaves ready marker or chooses helper by Python rather than Node architecture | supported / fixed: marker invalidated before npm replacement, probe before ready, actual Node architecture selects helper. Failed-setup and x64-on-ARM mocks; actual Rosetta execution unverified. |
| New setup tests assume Darwin | supported / fixed: explicit macOS skips. Bootstrap success cleanup directly tested; bootstrap-failure finally cleanup is source-supported, not a dedicated failure-injection unit. |
| Manager crash/inspection failure falsely implies cleanup | supported / fixed: unclean service warning/refusal, retained per-terminal stop error and identity-safe retry. Real synthetic SIGKILL and failed inspector witnesses. Explicit fresh start never establishes old-work cleanup. |
| lb terminal stop --all treats unclean stopped as healthy empty | supported / fixed (high impact/high confidence): destructive guard before shortcut/confirmation; human/JSON/--yes/--force test demands nonzero identity error and empty stdout. Healthy empty no-op preserved; turn7 source-confirmed. |
| Compiled renderer throws ReferenceError in requestMode; Node20 probe imports JS as CommonJS | supported / fixed: actual vi failure traced to re-minifying pinned ESM, select same release's published CJS; compiled DECRQM regression probe. Node20 outside-package failure reproduced; temporary type:module declaration fixes actual minimum-version check. No vendor patch/upgrade. |
| Retained terminal failure is omitted from management rendering/cache | supported / fixed by primary after freeze7: error/closing participates in the render key, concise per-target state and expandable error remain visible. Actual browser response fixture on a background tab showed retained ID, error and retry control at320px; restoring the real response cleared the error. This metadata-only fixture did not inject a process failure and is not a new independent review. |

No concrete supported finding is left unfixed within the reviewed code scope.
That conclusion does not fill physical IME, Safari, truly hidden-view/controlled
corpus baseline, long-soak or user-environment evidence gaps. Scope and approved product
decisions remain unchanged. Formal whole-Feature acceptance stays blocked at the
existing owner; next work is missing evidence, not automatic new implementation.
