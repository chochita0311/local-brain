# EVAL-0162: Terminal Final Audit

- Status: `complete`
- Result: `PASS WITH SUGGESTIONS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Run: [RUN-246](../run/run-20261112-246-terminal-final-audit.md)
- Profile: `fullstack-product`; attempt1, with frozen repair confirmations.

The final audited macOS web implementation passes the checks below. Fresh
review found additional defects after Eval0161; they were reproduced and
repaired, including integration defects introduced during this repair. No
supported finding remains open within the evaluated boundary. This is bounded
technical acceptance, not a guarantee for every terminal program or environment.
Earlier Runs/evaluations retain their original inputs, results and limits.

## Boundary And Preservation

Keep bundled, unmodified D2Coding1.4.0 Regular/Bold, OFL and provenance; URL-only
loading,13px, no OS font installation or installed-font dependence. Keep real
login shells and user rc files, saved launch defaults, macOS web-only admission,
tabs/up to4 panes, background versus explicit termination, current-owner input,
independent manager lifetime and identity-safe process cleanup. No Herdr core,
vendor upgrade, transcript/replay, external terminal, native product or Windows
scope was added. Default-user service, jobs and settings were not changed.

Baseline HEAD4ff4a2daf6a714063b19ba077bb169711441bdaa plus preserved dirty source
has1857 files, manifest bd801f1db377775a805d44c1164aaa2a6079eda370d3d2755c55ddadc6783b7c.
The final reviewed/executed1863-file snapshot has manifest
`a766b930c5395c8527a73af9e0be383a5b1e0ded1ba40ab7dc7180522733061f`.
Later closeout/catalog changes affect documentation, not executable bytes.

A final primary check reproduced false birth-identity mismatch when the caller
used another timezone. UTC normalization/format tagging is included in the final
snapshot and renewed full suite, actual launchd and wheel checks. Browser, native
input, checkpoint, fonts and asset bytes remain identical to the preceding
`a4913ebf619092b11b93d4ca8584d3455bc7907cb44c969e1a0709c9d4e950f4`
integration/performance snapshot; those earlier witnesses retain that exact scope.
No wrong-process shutdown was exercised or observed.

## Findings And Repairs

| Area | Reproduced cause and resulting behavior |
| --- | --- |
| Keyboard tabs | A delayed emulator focus overrode the tab selector after ArrowRight. Repeated arrows now retain tablist focus; pointer selection still focuses the emulator. |
| Cursor and IME anchor | Headless cursor-initialization state hid an already focused browser cursor after resize. Initialization stays browser-local; restored coordinates notify the textarea anchor. Actual focused cursor and nonzero initial-anchor geometry pass. |
| Native composition authority | A late native composition end could transmit pre-loss text after control returned. Cancellation retires deferred native-helper sends and clears input; new composition still commits exactly once. Idle read-only output preserves emulator focus. |
| Rejected keyboard paste | Cmd+V committed pending WebKit Hangul before multiline rejection. Confirmed paste now owns that commit; rejection preserves the preview. Ctrl+V keeps macOS literal-next behavior. |
| Detached color queries | A raw OSC11 query timed out without a browser. Headless now owns ordered OSC4/10/11/12 reports; browser suppression preserves mixed SET commands without duplicate replies. A v3 handshake rejects old reporting renderers before input. |
| Manager input memory | Unread automatic replies grew node-pty's unbounded write queue. All PTY input now uses a256KiB budget, ordered nonblocking writes, bounded pages and delayed EAGAIN retries. Automatic overflow exposes a per-terminal input fault; management and peers remain usable. |
| Cooperative duplex progress | The first pressure repair paused output while input was backed up, deadlocking a normal echo program. Input backlog no longer pauses output. With a raw-ready barrier, the same256KiB accepted input stalls after2044 bytes before repair and drains completely after repair. |
| Partial-input interruption | Rejected middle packets could leave later paste fragments eligible, and normal output cleared the warning. The bridge closes1013 before processing the suffix; the browser discards pending input and retains partial-input/Ctrl+C feedback across output and reconnect. |
| Hidden fault visibility | Background input faults reached the API but were omitted from Management redraw/status. Management now shows the fault before opening its view; plain CLI list also marks input errors. |
| Setup architecture | Only the install-time Darwin helper was executable while readiness stayed true. Setup and explicit Start prepare both bundled helpers, including existing caches; missing helpers invalidate readiness. Actual Rosetta execution remains untested. |
| Manager PID reuse | A stale identity naming an unrelated live PID blocked explicit fresh start. Positive process-birth mismatch permits unclean-loss recovery without signaling that process. UTC/C reads and a tagged time format prevent timezone changes from falsely implying replacement; matching/legacy/unknown-format identities and failed inspections remain protected. |

Writer closure received additional lifecycle hardening: the raw writer owns the
PTY close event independently of later process exit, cancels scheduled work and
rejects new input. A controlled close test exercises actual numeric descriptor
reuse and observes zero replacement-file writes. Closing stdio in a macOS child
did not induce the proposed master-close-before-exit ordering; its failed oracle
is preserved. No actual wrong-target delivery was observed, so that consequence
is not reported as a reproduced product defect.

## Verification

| Evidence | Actual result and checked boundary |
| --- | --- |
| Full Python suite on final frozen execution copy | **1648 passed,0 skipped**,340.446s; includes31 real-PTY cases with the explicit private engine enabled. Earlier1640/1645/1647 passes are separate historical attempts. |
| Terminal Node tests | **67 passed,0 skipped**: VT continuation, Korean-input boundaries, mixed ordered color reports, writer limits/partial bytes/retries/disposal and descriptor reuse. |
| Browser assets | Reproducible bundle/manifest/import check passes; pinned runtime/browser versions and font/license files remain consistent. |
| Chrome/font checks |13 checks; actual custom D2Coding glyph use and13px measured, missing-font recovery, fresh renderer, reconnect and narrow layout. Later native final-bundle evidence also records loaded fonts and13px. |
| Browser VT continuation |36 checks over11 paused producer scenarios, comparing fresh-view future state with uninterrupted headless execution; includes fragmented controls, regions, tabs, saved cursors, palette, links and hidden alternate width. |
| Browser input/cues |14 input and14 status/history checks. Original observer-fixture socket tracking was corrected; the failed tool attempt is retained separately. |
| Final integration |10 checks: fragmented color query across checkpoint yields exactly four PTY reports and zero browser replies; new native composition after cancellation reaches the real PTY once; observer focus stays; continuous legal60KB pastes stop at rejection; partial-input warning survives normal output/reconnect; hidden query fault is visible in Management. |
| Actual macOS input method | Six standalone WebKit→PTY cases pass: full Korean phrase, jamo deletion, resyllabification, Shift compound, rapid syllables and Ctrl+C. Uses AppKit-injected OS events with the selected two-set input method, not a physical keyboard. Input source and prior focus restore successfully. |
| Actual launchd | A separate task-owned GUI-domain job starts a real zsh, survives another client instance, records UTC birth identity, protects it under a Honolulu-time caller, restarts into an empty generation, ends the old shell and removes its transient job/config on stop. Default-user job is untouched. |
| Wheel |392 entries; all29 terminal code/asset/guide files byte-match final source, including font/OFL. No node_modules/runtime state packaged. Native admission/exclusion contracts also pass the Python suite. |
| Repository privacy | Scanner passes; private audit evidence remains in its ignored local owner. Final owner/catalog checks and cleanup are recorded by Run246. |

The final integration's five legal60KB paste events emit300000 bytes; the stalled
child receives256384 accepted bytes, and the remaining suffix is discarded after
the admission error. Already accepted bytes cannot be rolled back. This proves
bounded interruption and feedback for that scenario, not atomic whole-paste
execution or arbitrary-content byte accuracy.

## Resource And Responsiveness Evidence

The owned synthetic corpus has3000 sessions,240000 events,800 documents and1800
search entries. Its source is registered, and Sessions, detail and keyword search
actually render the corpus. A first empty-search attempt is excluded. The324
checks cover0/1/8 shells, four visible panes, actual hidden-tab detach/return,
and a live advancing producer generating at least8MiB during peer/control samples.

- Manager RSS:56.6MiB with one shell,68.9MiB with eight,88.4MiB during verified
  live flood. Five-second idle manager CPU samples round to0% at the sampler's
  resolution; this is a finite sample, not a zero-CPU guarantee.
- Input-to-DOM plus animation-frame p95:33.9ms with one shell,33.5ms with eight,
  and33.6ms during peer flood. Control p95 during flood:2.94ms. Selected150ms/
  250ms responsiveness targets pass.
- Existing route p95 at0/1/8 shells: Sessions22.7/23.3/23.0ms; detail16.0/14.8/
  14.9ms; keyword search11.2/11.4/10.6ms. End-of-run zero-shell samples vary
  up to56.2ms for Sessions; no universal no-regression claim follows.
- Whole Chrome subtree RSS is approximately1.3–1.5GiB, including shared mappings
  and browser infrastructure. Backend RSS rises from94 to144MiB as routes warm;
  shell children use approximately3/26MiB at1/8. These are distinct from manager
  cost and do not establish an additive per-pane browser memory estimate.

Measurements use this arm64 macOS host, Python3.11/Node24 and installed Chrome/
WebKit, with other verification work present. Source and environment metadata,
raw samples, finite producer-liveness evidence and fixture corrections remain in
the private evidence archive. They establish the measured workload, not every
machine, prolonged load or every application.

## Review And Evaluation Disposition

Three fresh named read-only review_challengers independently inspected lifecycle,
input and pinned VT state from frozen source. Their initial discoveries were
preserved before informed repair confirmation. Later turns review supplied
reproductions and changed consumers; they are not additional fresh independent
reviews. The primary owns architecture, fixes, actual tests and acceptance. The late
timezone cause is primary-discovered, followed by a narrow informed lifecycle
confirmation; it is not another independent worker discovery.
Workers executed no reviewed code/tests/GUI and gave no completion approval.

Independence limits are explicit: one normative Spec read exposed earlier closure
claims; an early live diff/reference read by another worker was excluded from
candidate evidence. Actual provider runtime IDs/tokens are unavailable. These
limits do not disappear because final source hashes match. No skill/delegation
effectiveness comparison was performed.

Contract, design, functional and interaction evaluation **PASS for this scope**.
Font/layout roles and concise controls remain; new error details appear only at
the affected pane/Management/input failure. Required defects are resolved without
relaxing A-01–16 or introducing a new product decision.

Remaining evidence limits: physical-keyboard repetition in Safari itself,
VoiceOver announcements, broad grapheme/ZWJ behavior, actual cross-architecture
Rosetta startup, long soaks, other machines/versions and deliberately detached
programs which lose both ancestry and original session membership. They are not
verified by passing counts or source review. Existing truncation/state-budget
and interrupted-paste limitations remain documented in the terminal policy.

Review the delivered behavior after work finishes and an explicit web-server/
terminal-service restart plus browser refresh. Service restart ends its terminals
and starts none automatically. The dependency lock is unchanged in this audit;
font OS installation or routine engine reinstallation is unnecessary. Source
remained local/uncommitted at that audit's closeout; actual-user service update
and publication were separate actions.
