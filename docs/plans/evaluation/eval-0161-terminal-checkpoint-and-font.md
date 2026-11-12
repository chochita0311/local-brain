# EVAL-0161: Terminal Checkpoint And Bundled Font

- Status: `complete`
- Result: `PASS WITH SUGGESTIONS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Run: [RUN-245](../run/run-20261111-245-terminal-checkpoint-and-font.md)
- Profile: `fullstack-product`; attempt1.

The installation-independent font and supported checkpoint repairs pass the
checks below. Actual macOS Korean input also exposed a WebKit input path omitted
by the previous audit; that path is repaired and observed through the OS input
method, browser and real PTY. No supported finding remains open in the reviewed
scope. Eval0160 remains complete/FAIL for its earlier fixed inputs.

## Delivery And Preservation

- Bundle the public D2Coding1.4.0 Regular/Bold WOFF2 faces, OFL and provenance.
  Both faces load before opening/measuring panes; the default stays13px and
  coding ligatures stay disabled. No installed D2Coding, OS font installation,
  iTerm2 preference import or runtime font download is required. Absence of one
  installed font never meant that every system would necessarily corrupt Hangul.
  Missing glyphs, fallback selection, encoding and Unicode width are distinct.
- Replace the current web path's VT repaint with the pinned `xterm6-v2` typed
  checkpoint. Preserve both buffers, stored line widths, parser/decoder state,
  modes, regions, cursor/charset/tab state, links and dynamic colors. Recreate
  handlers, markers and prototypes locally; never transfer executable callbacks.
- Preserve the1,900KiB checkpoint/2MiB response budget. Drop only old history to
  fit; disclose omission through delta, control, error and exited states. An
  oversized active state fails explicitly while the job and management survive.
  Manager resize invalidates deltas and supplies a new canonical checkpoint.
- Add a small local WebKit Korean-input adapter: hold and preview the unsent
  range, replace/delete its jamo, commit at boundaries, preserve menu/bracketed
  paste order and leave native composition/Chromium on xterm's original path.
  Keep screen-reader mode. Cancel held input on lost authority, connection,
  hiding or disposal; never replay it on reconnect.
- Preserve process/input ownership, defaults, optional setup, private storage,
  no transcript/replay, CLI and macOS web/desktop separation. User jobs and the
  default-user service/settings were not stopped or changed. No commit, push,
  release or LocalBrain desktop product build occurred. A temporary AppKit test
  program was compiled solely for native-input verification.

The public font bytes come from D2Coding revision
`b0dc372e28d7abdba7f3cba854855ceffbd490a8`; their hashes and license ship beside
the assets. Published xterm6.0.0 sources, including43 matching common files from
its source maps, were used to inspect the pinned private state contract.
See the [terminal owner](../../policies/project/terminal.md) for current behavior
and [the source tests](../../../tests/terminal-checkpoint.test.cjs) for executable
continuation counterexamples.

## Verification And Evidence Scope

| Evidence | Observed result and limit |
| --- | --- |
| Full Python suite |1,640 passed, zero skipped; all27 macOS real-PTY cases ran. Corrected explicit engine environment;284.569s, exit0. Includes version rejection, RPC resize invalidation and oversized-state recovery without a new PID/replay. |
| Final terminal suite |57 passed:45 checkpoint/continuation cases and12 input-boundary cases. Headless and browser engines use the pinned release. Unit fixtures alone do not establish native browser behavior. |
| Actual DOM and PTY |14 final input checks: preview, final syllable, resyllabification, Shift, empty-range Backspace, menu/bracketed paste, rejected multiline paste, native-composition handover, ordinary229 fallback, lease loss/recovery and same PID. Chrome with a WebKit UA activates the adapter; this is DOM-trace integration, not native WebKit evidence. |
| Actual macOS input method |A separate temporary AppKit/WKWebView test window selects the real built-in2-set Korean input source and sends keys only to its own application. Six scenarios passed twice on final bundle `03120ee0fce769817f51d8abbe64f44baa13a780c549bf3da8949623cf2d60c3`: phrase/committed Backspace/Enter, pending-jamo deletion, 받침 transfer, Shift compound, queued rapid syllables and Ctrl+C ordering. Original input source and focus restored in both runs. This tests the OS input method, not a human-operated hardware keyboard or the Safari application. |
| Chrome composition and fonts |13 final checks passed: normal composition/commit, final-consonant transfer, cancellation, Backspace, bundled custom-font glyph rendering,13px, disabled ligatures,320px containment, same PID after new renderer, font404 and reload recovery. Both faces loaded from local URLs; URL-only font faces cannot select an installed D2Coding instead. |
| VT browser continuation |36 checks across11 actual PTYs/new renderers passed: fragmented CSI/OSC, regions, cursor save, tabs, extended/protected cells, charset/Unicode join, unprinted links, alternate-width shrink/grow, palette reset and links. The checkpoint source matches the final candidate; later changes affect the input adapter only. |
| Omitted history |14 checks passed with real dense output forcing manager history fallback. Cue survives paint, delta, lease transfer/recovery, injected retained-error metadata and actual exited socket closure; a complete snapshot clears it, with the same PTY. The injected error is a UI record fixture, not a failed process termination. |
| Version/cache matrix |Eight final checks passed: new page rejects oldv1 service input, matchingv1 client still works withv1, explicit restart creates no terminals/replay, v2 works afterwards, cachedv1 cannot take over v2. New-page/old-service feedback directs explicit service restart; it does not keep asking an already-current page to refresh. |
| Web package and desktop exclusion |Asset generation/check passed. Built wheel contains27 selected terminal files byte-for-byte, including both fonts/license, adapter, runtime, template and both language guides. Actual desktop collection patterns produced125 data entries/234 modules with zero terminal/font leaks. No desktop product rebuild. |
| Layout/interaction |Primary inspected final1440px/320px screenshots. Existing shell, concise controls,13px glyphs and contained tabs/pane remain legible; no new explanatory banner. Failure/retry, omission, readonly/ownership and termination states were exercised separately. |

Python validation used immutable review4 copied to a writable execution tree;
the final browser-only delta used review5. All Python/manager/checkpoint files
are unchanged between them. Review4's1,857-entry manifest is
`3c85a7a6b791beab3d867405da4bb27a68c66071ed23dee7441ab32c3ac2c7ef`;
review5's is
`8b051947b8f3c4db98d907e7959eb62a1a0243db7bf1280af4c02451cc69fc3e`.
Both execution inventories matched, with no extra bytecode. The first verification
command used a mistyped engine variable and skipped27 real cases; its result is
retained as non-authoritative and excluded from these totals.

Native-driver failures are retained separately. Manually activating a WebKit
input context and posting zero-duration key pairs produced inconsistent event
streams; early fixtures also targeted an old pane or checked before readiness.
The admitted final driver uses a separate application identity, the OS input-source
API, a confirmed target/prompt, and key delivery in order. Generic textarea
comparison composed the Korean phrase; its default smart-quote substitution is
not a terminal failure. A separate pre-adapter native comparison failed to reach
the input-ready state and is excluded as a negative witness. The user separately
reported normal direct Korean input; that report does not identify this build.

Environment: macOS26.5.1/arm64, system WebKit21624.2.5.11.4, Chrome156.0.8078.96,
Node24.15.0, test Python3.11.15. No claim is made that this run covers every
supported OS/browser version or a new minimum-Node verification.

## Representative Performance

Synthetic corpus:3,000 sessions,240,000 activity events,800 documents and1,800
search records. Actual private content was not copied into the fixture. The
324-check run covered0/1/8 shells, real hidden-page detachment/return,25 warm
requests per route/state and input/control while an owned producer kept flooding.

| Metric | Observed |
| --- | --- |
| Manager RSS,1/8 idle shells |55.97/69.22MiB; below96/160MiB targets. Five-second ps samples reported0% idle CPU; coarse observations, not proof of zero CPU. |
| Local input→DOM plus next frame, p95 |33.6/33.4ms for1/8 shells,20 samples each; target150ms. |
| Live flood |Producer bytes advanced8.7→9.2MiB; peer input p9547.5ms, control p952.334ms;20/50 samples. Manager86.38MiB. Target control250ms. |
| Whole-process costs |Chrome process RSS sums around1.46–1.50GiB including browser baseline/shared processes; backend132.3–135.1MiB; eight shell roots25.44MiB. RSS sums are not unique physical memory or terminal-only browser cost. |
| Existing screens |Sessions-list p9518.84/19.26/18.98ms at0/1/8; search19.85/19.79/19.89ms. Detail median stayed around5.6ms while p95 varied6.27/6.28/18.65ms; retain that tail variation rather than claiming no regression universally. |
| Truly hidden view |`document.hidden` became true, all four visible streams closed, and return reattached to the same eight PIDs. An additional visible window alone was not accepted as hidden-view evidence. |

This finite warm test meets the selected workload targets; it is not a long soak,
a controlled every-device causal benchmark or a guarantee of constant memory.
The first flood fixture had invalid Python and was discarded; the admitted run
checks producer readiness, liveness and increasing bytes throughout measurement.
Later input-only repairs do not alter the measured manager/parse/resource paths.

## Independent Challenge And Adjudication

Research-SADR used fresh named research workers for font distribution and the
pinned VT state question, followed by a fresh state challenger and client
challenger and informed repair confirmations. A separate fresh research worker
investigated the native WebKit counterexample. Roles used their configured
bindings with no inherited author conversation; actual serving internals are
unobservable. Challengers were read-only/non-executing. The fixed verifier ran
only assigned execution packets. Primary owns architecture, rights/provenance,
implementation, evidence admission, privacy and the acceptance conclusion.

| Candidate | Primary disposition and distinguishing evidence |
| --- | --- |
| Constructor omits13px |Refuted: Pane.open sets computed13px before Terminal.open; actual browser metrics agree. Initial broad review was partial/interrupted, not a full pass. |
| Alternate cells disappear or checkpoint rejects after width shrink |Supported/fixed: preserve each stored line width; differential and real browser30→17→30 retain hidden right cells. |
| Unprinted/named/dangling/retired links lose lifetime |Supported/fixed: transport actual referenced/named anchors, recreate receiver-native marker ownership, preserve retired permanence and dangling decoration. Future-URI differentials discriminate the failure. |
| Height shrink leaves a marker beyond current rows |Supported/fixed: accept valid native marker rows after bottom-row pop;8→4→8 continuation test. |
|2,160 anchors assumed a native limit |Supported/fixed: coalesce equivalent live lifetimes and permanent retired anchors;2,161 source anchors transport one equivalent permanent anchor. This does not bound native-engine heap/time. |
| Omitted history changes independent local reflow |Supported outside the app's resize path; not retained as an app defect. The app sends resize to the manager and reimports canonical state; amended actual RPC and Node tests verify invalidation and matching viewport. |
| Omission cue overwritten during control/error/close |Supported/fixed: one status writer retains the omission flag; actual fallback/delta/transfer/error/exit/clear witnesses above. |
| WebKit Korean replacements never reach onData |Supported/fixed for the observed no-composition path: local capture adapter plus direct OS/PTY checks. Disabling screen-reader mode alone does not handle replacement events. |
| Empty held range traps another Backspace; menu paste overtakes it;229 stays suppressed |Supported/fixed: empty-range/key-order cleanup, paste boundary before xterm and per-edit229 suppression. New unit and actual xterm/PTY witnesses; informed review5 confirmation found no remaining supported candidate in those paths. |

Upstream proposals are evidence, not adopted dependencies: xterm
[6285](https://github.com/xtermjs/xterm.js/pull/6285) remains open and explicitly
does not fix screen-reader/rollover paths; [5704](https://github.com/xtermjs/xterm.js/pull/5704)
has unresolved review comments. The author of [6084](https://github.com/xtermjs/xterm.js/issues/6084)
retracted the diagnosis and deprecated its addon; that addon was not adopted.
No third-party bridge source was copied.

There was no caller hard time/token budget. Research/review checkpoints were
reassessed only for new concrete counterexamples and repairs; unchanged inputs
were not rerun to manufacture agreement. Initial fresh returns and later informed
confirmations are kept distinct. Frozen sources, raw returns, probe code and logs
are preserved in the existing private evidence store; task scratch is removed
after verified archival and test-process cleanup.

## Acceptance And Remaining Limits

Contract, functional, design and interaction evaluation pass for these repairs.
The original fresh-view checkpoint blocker and missing real OS-IME/hidden-view/
representative-workload witnesses now have direct evidence. This supports closing
the bounded Run without changing A-01–16 or adding IDE convenience requirements.
Earlier Runs/evaluations retain their historical blocked/fail results.

Coverage remains partial for hardware-keyboard/Safari-app repetition, VoiceOver
announcements, complex grapheme/ZWJ emoji, long soaks and other machine/browser
versions. Keeping accessibility DOM does not establish complete assistive-tool
behavior. Font choice UI, search, full Nerd Font coverage, shell integration and
IDE completions remain separate conveniences; existing shell completion works.
Engine control/combining state has a documented memory limit caveat; the tested
workload is not an all-situations lightness guarantee.

The actual user's service was left running. After finishing its jobs, apply the
new Python bridge with a web-server restart, restart the terminal service
explicitly, and refresh the browser. Service restart ends its terminals and
creates no shells. Engine reinstallation is needed only if its lock/modules
require it; bundling the font adds no per-install OS-font setup.
