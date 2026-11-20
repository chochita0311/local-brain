# Functional Stability After The Native Backend Cutover

## Scope

[Rust Core Transition](../refactor-0006-rust-core-transition.md) and
[Run261](../../run/run-20261118-261-python-free-backend.md) own this behavioral
follow-up. The user authorized restoring successful user tasks, preserving saved
data, and showing actionable errors. Exact internal representations and
performance are outside this check.

| Comparison | Identity |
| --- | --- |
| Python host baseline | 1,973 frozen source files over `e6958df0813b8652074c68a73ac61a8b551e59a8`. Archive manifest `7f02036fed1e2c892b5c81f2d3f14d1502dd318a6d2b896697f3eca8bf885dc9`. Review manifest `bd2fd14e34d988408bd560e867f9a17f1e9cfb45b33e4c111b45f2bfd6126fe6`. |
| Rust before repair | 1,957 files. Manifest `324b9a0004c4121562bd7c9ed126951309fe53eb3112ca4cf08f0cd1e8cf946e`. |
| First independent review | 1,957 files. Manifest `6c99a6e68e70ac49e72a7e71682b285553db624194db42106912f042cc67ca32`. |
| Final repair | 1,957 files. Manifest `644b6dc70e5dbb2ba2e64ae2bc529fa70a7bdab38de2f967e191fd4dc56aa280`. The same Git HEAD was verified before delivery. |
| Delivered build inputs | Both web and Apple Silicon desktop builds identify `36987b1ea61589d48a4c3aac4f6918d0388dc4a627cdda5b0f6eab5bb7bcb8aa`. |

The final source was frozen at 01:37:51 UTC on 2026-11-20. Execution used macOS
26.5.1 arm64, Rust 1.90.0, Python 3.11.15 for the old host and test tools, and
the pinned Node 24.15.0 release. Python and native lockfile hashes and exact
source mappings are in the private Run261 evidence. The named method has SHA-256
`d29c73b5e815786dab00ffc3bb18ac790e3d94f69880ab632a2675e33fe2235f`.
[SPEC-0180](../../spec/spec-0180-python-free-backend.md),
[Session Ingestion](../../../policies/project/session-ingestion.md),
[Desktop And Settings](../../../policies/project/desktop-app-and-settings.md),
and [Terminal](../../../policies/project/terminal.md) govern the compared paths.

## Changed Surface

The Fullstack lanes are the checkpoint and Session routes in `apps/api`,
Sessions feedback in `apps/web`, source transactions and writer guards in
`crates/core`, and the packaged Terminal transport. The same SQLite schema,
Cargo locks and Node locks serve the final repair. Project-specific outcome
evidence is recorded here and the two changed operating contracts are recorded
in their owner policies.

## Validation Run

| Check | Result |
| --- | --- |
| Rust 1.90 workspace tests, locked and offline | 420 passed, 0 failed, 7 ignored across 85 harnesses. The opt-in native desktop lifecycle test passed separately. |
| Rust formatting and workspace Clippy with warnings denied | Pass. |
| Node and remaining build/check tools | 85 and 51 tests passed, respectively. |
| Staged web and desktop release | Matching input fingerprints, executable hashes, archive checksum, deep app signature and all 103 Terminal payload files verified. Bundles declare the macOS 14 deployment target. |
| Chrome with the staged web bundle | The filtered Sessions bookmark, lock-error feedback, retry on the same page, and long Korean checkpoint after form reload passed. |
| Relocated macOS app and native backend | The actual window passed Terminal launch and input, hide/restore, pane close/recreate, and workspace creation. The extended keyboard workspace move stopped at a foreground-focus guard. The separate packaged host test passed all 10 checks, including authenticated stream access, relaunch with the same manager generation and PTY process IDs, and explicit stop. |

## Review Receipt

Three named semantic review agents independently inspected frozen source with no
conversation fork. The CLI/cancellation, shared sync, and web/Terminal lanes
compared the Python baseline, pre-repair Rust and the first candidate. CLI and
Terminal reviewers received the final repair delta after their findings.
Reviewers used shared source, contracts and test definitions. The primary
executed the process, database, browser and bundle witnesses. The scope used
one bounded discovery pass per lane and repair confirmation for the two changed
lanes. Loopback, signing and app automation used isolated test processes.

## Strict Parity Audit Coverage

| User path | Old and new implementation boundary | Observed outcome and limit |
| --- | --- | --- |
| Workstream checkpoint | Python `workstreams/web.py` and service to native `routes/workstreams.rs`, the checkpoint service and browser submit form | 64,000 permitted characters saved as Korean input and escaped supplementary Unicode. An over-length field still returned 422 and wrote nothing. Chrome reloaded the saved values. |
| CLI scan cancellation | Python CLI and scanner to native `cli/mod.rs`, parsers, scanner transactions and post-scan search preparation | SIGINT with the source file open and zero committed sessions returned 130 with zero sessions on both Python and final Rust. Before repair Rust returned 2 and committed one. The in-process test also preserves earlier committed sources and their IDs on retry. Late search cancellation preserves existing published index bytes. |
| Sync failure and recovery | Python operation guard and sync worker to native operations, sync service, Session status, JSON and NDJSON routes and existing Sessions feedback | An invalid lock with stale running health returns an idle error, rejects both request routes with 503, and imports successfully after repair. Two requests during real cross-process contention result in one scan. Document collection retains its own success clock and retries independently. |
| Terminal and bookmarks | Python terminal WebSocket/workspaces and web router to native Terminal and Sessions routes, runtime and JS | An empty runtime override uses the bundled helper. A nonzero helper exit sends its error frame. A workspace with group/other permissions is refused without overwriting the file. Sessions, Projects and Session detail redirects retain the original query. Initial helper stdin failure has independent source evidence. |
| Existing database | Python-created SQLite3 and TOML to the final Rust bundle | Two sessions, one document, one Workstream and two checkpoints retained their stored values. SQLite integrity, Session and Workstream page reads, and settings readback passed. |

## Candidate Adjudication

| Candidate | Evidence and disposition |
| --- | --- |
| Late search publication after interruption | Supported. The second final preparation callback provides a deterministic cancel witness. The final guard preserves the old active index, and a fresh preparation reuses its unchanged generation. |
| Missing Terminal error during initial request write | Supported by both source paths. The final branch closes the owned helper and sends the error before socket closure. A normal-request fixture exited after accepting the initial pipe write, so it exercised normal EOF. The separate abnormal-exit WebSocket test reached error delivery. |
| Genuine contention becoming a failed request | Refuted. Existing reentrant guard tests and the separate-process lock witness retain one pending scan and recheck completion before collecting. |
| Context-only failure visibility | Existing behavior. The independent Context error is available through Settings JSON. The reviewed UI repair uses the existing Sessions result. |
| Extended native focus navigation | The test stopped when the owned app lost foreground focus during keyboard workspace movement. Earlier actual window checks and the later packaged host lifecycle checks passed. Full keyboard workspace-move evidence remains incomplete. |

## Changed-Input Reconciliation

Both final fixes were traced against the first reviewed candidate and the Python
baseline. The exact repair delta and fresh affected tests are retained with
Run261. Final delivery uses the frozen production inputs. This execution
record was added after those inputs were frozen.

## Merge Assessment

The tested user-facing stabilization flows pass apart from the partial native
window case recorded above. Behavioral parity for the whole cutover and
whole-cutover merge readiness remain provisional. Unreviewed feature paths and
the declared macOS minimum require separate execution evidence for wider claims.

## Parity Proof

Matching input cases reached saved checkpoint content and retained SQLite
records on both runtimes. Cancellation and retry checks established the active
source rollback boundary, retained earlier commits and a successful second
attempt. Terminal tests established local authorization, workspace refusal and
the separate manager lifetime. Each result applies to the paths exercised.

## Intentional / Reviewed Deltas

Lock access errors use explicit retry feedback in Sessions. The JSON and NDJSON
requests return 503 before starting a scan. CLI cancellation emits a short
diagnostic on stderr. The checkpoint transport bounds JSON bytes while honoring
the existing six character limits. These changes preserve the supported jobs
and make failure states actionable.

## Residual Risks

The startup-write Terminal error has source-level coverage. The extended native
keyboard workspace move, physical input methods and other platforms have
separate evidence limits. Byte-range and noncanonical API spellings from the
earlier review are outside the user-facing repairs. Cancellation observes
defined transaction/publication boundaries. Long synchronous work can still
delay that observation.

## Next Action

The locally verified builds are available through the existing `lb` alias and
the Apple Silicon app archive. A future whole-window acceptance can resume with
exclusive foreground focus on a separately owned app instance.

## Session Close Verification

The final recheck used the original 1,973-file Python baseline and a sealed
1,958-file working-tree snapshot over the same Git HEAD. The candidate manifest
SHA-256 was `f901a50b25949d49045351f8cb1ce9e572271284719553ef16315d4cd51e579c`.
Relative to the preceding final review, the snapshot includes this record and
the Run261 stability entry. Both delivered bundles still match the 454 build
inputs recorded above. The working tree contains other pending local changes.

Three named independent source reviewers traced the runtime and retirement,
storage and browser behavior, and logging and model paths. The primary reran
the build and execution witnesses below. The reviewers shared the method and
code lineage, and the model reviewer encountered archived measurement summaries
and later saw sibling status summaries. The first cancellation candidate preceded
that later exposure. The source reviewers used one bounded discovery pass each.
Follow-up execution covered the two concrete interruption candidates and targeted
browser checks. No user deadline was set. The ignored Run261 evidence owner
retains the exact comparison identities, observed checks and limits.

| Verification | Result |
| --- | --- |
| Runtime retirement and delivery | Both native bundles, the signed app extracted from the ZIP, and all 103 Terminal payload files per bundle matched. The `lb` shell alias points to the tested web binary. With OS-denied Python execution and an empty PATH, it imported a synthetic session and served health, Session detail and sync status. Both access-log modes passed, including actual encoded paths, status, time and omission of query/header markers. |
| Rust and developer tooling | Rust 1.90 locked/offline workspace tests passed 420, with 7 ignored by default. The opt-in desktop host test and the actual-model CPU and Metal tests passed separately. Both formatter checks, workspace Clippy, 85 Node tests, 51 build/check tool tests and the privacy check passed. |
| User-facing web and desktop | Chrome navigation and UI state suites passed 54 and 70 checks. The actual packaged Mac app passed 16 checks, including both directions of keyboard workspace movement with the same PTYs and reconnect after relaunch. This resolves the earlier keyboard-move coverage gap. The expanded Chrome Terminal suite timed out at two different steps. A keyboard retest passed ordering rollback after both requests failed, and the focused font-reload case restored the same connected PTY. Full expanded-suite coverage stays partial. |
| Local embeddings | The sealed optimized source matches the archived exact-vector and four-query ranking/index comparisons. Actual Qwen 0.6B CPU and Metal rechecks passed at 512 and 1024 dimensions, including the 1024/1025-token limit, the whitespace boundary, normalized output and pre-cancellation. Overall elapsed time varies by workload and device. |

### Final Candidate Adjudication

| User-visible condition | Evidence and disposition |
| --- | --- |
| `Ctrl+C` during `lb search query` | Supported migration regression. The old Python command catches interruption around retrieval. The current CLI token is detached from model verification and retrieval in `search/model.rs` and `search/retrieval.rs`. In a normal query control the release returned the synthetic result. Three interrupted release queries all printed result JSON and then `SEARCH_INTERRUPTED`, returning 130 after the work. This remains open in the current release. |
| `Ctrl+C` inside `lb simulate` encoding | Supported migration regression. The old Python simulation records `interrupted`. The native encoder returns `MODEL_CANCELLED`, which `auto_work/simulation.rs` records as `failed`. Both release trials returned 130 and printed `SIMULATION_INTERRUPTED`, then reported `SIMULATION_FAILED` through `--status`. The previous report stayed byte-for-byte intact, and retry completed. This remains open in the current release. |

The Python-free Rust backend, application layout and local delivery goals are
met on the tested Apple Silicon host. The interruption cases prevent a full
behavioral-parity judgment. Native Korean IME, physical sleep and the declared
minimum macOS on hardware remain outside this execution evidence. This is a
local verification result for the existing implementation and delivery.

## CLI Interruption Repairs And Chrome Recheck

The two interruption cases above are resolved in the refreshed local release.
The CLI query passes its cancellation token into model verification and
retrieval, then emits the result at the completion boundary. The simulation
translates native model cancellation to the interrupted state before writing
progress. Reading earlier `failed` records with `MODEL_CANCELLED` also reports
interruption. The read keeps the stored record intact. An independent repair
review traced these paths and the existing web and scan callers.

The old and new packaged commands were run with the same synthetic SQLite data
and the pinned public Qwen assets. Real SIGINT during early query work and after
the active index was open yielded only `SEARCH_INTERRUPTED` with exit code 130
on the new bundle. A normal query and a retry matched the previous results
apart from timings, and the published index bytes matched. SIGINT during
simulation encoding now persists and reports `SIMULATION_INTERRUPTED`.
The preceding report stayed byte-for-byte intact and retry completed.

The Chrome harness now waits for the confirmed tab-order state, the drag target,
and the new document after the font retry. The full Terminal workspace browser
check passed all 143 assertions with the updated Rust fixture and packaged
Terminal payload. It exercised the ordering rollback, font recovery, workspaces
and real temporary PTYs. The earlier instrumented run completed 142 behavior
assertions before one DevTools interception error. The final run completed with
zero runtime exceptions or interception errors.

Rust 1.90 workspace tests passed 421 with 7 ignored by default. The targeted
search and simulation suites, formatting, Clippy, 85 Node tests and repository
privacy check passed. The web bundle and signed Apple Silicon app match build
input `dbfd2562e0093415524470a32922cc1264e087ce5deb214e76c0636757774559`.
Their packaged API startup, Session read and shutdown passed with Python
execution denied. Both workspace deliverables were refreshed. The verified
scope here is the interruption paths and extended Chrome Terminal test on the
tested host.

## Compatibility Repairs And Sessions Dashboard Timing

The local release restores six cases confirmed during the overall review.
Settings accept parent components in a configured data path and retain the
Terminal check for trailing-dot and trailing-slash symlink forms. Repeated
separators after `~` preserve the registered Session source and its retained
Session identity. New usage records sample attribution independently before
calculation and import timestamps. Reimport preserves frozen attribution.

Search readers and refreshes use the device and batch size of the complete
native index, verify the full numerical contract, and can retry when
publication replaces that file during a read. Forced recovery remains bound
to the affected generation. The packaged CLI and browser search used a CPU
index prepared with batch size 16 through query and refresh. Auto-work
inventory prints coverage. Simulation ran inference with batch sizes 1, 64,
65 and 256 and refused 0 and 257 with `INVALID_BATCH_SIZE`.

On a read-only SQLite snapshot, the default dashboard selected 78,551 usage
records. The original SQLite cursor pass took about 117 ms and subsequent
row conversion and aggregation accounted for most of the remaining time.
Reusing decoded fields, local-day conversion and exact Decimal inputs reduced
median first read-model time from 393 ms to 215 ms across three fresh
processes per version. Ten default and alternate projections matched
byte-for-byte. With a separate synthetic database at comparable scale, median
first packaged HTTP response time fell from 333 ms to 189 ms. Five page
outputs matched after normalizing the ephemeral loopback ports.

Three reviewers covered data compatibility, model and CLI flows, and the
dashboard. Focused follow-ups confirmed the symlink and generation-publication
repairs in source. The final candidate passed 426 Rust tests, with 7 ignored
by default, plus 51 build-tool tests, 85 Node tests and 124 Chrome navigation
and state checks. Formatting, Clippy, repository privacy checks, bundled
Desktop backend startup and shutdown, and ZIP extraction and signature
verification passed. The schema presentation and audit changed only source
fingerprints. Both local packages use Rust 1.90 and source input
`4a6cb452a3877efa7753b3916a55e36f8e4184801e6e706359983d2aeae73cce`.
Runtime evidence is from the Apple Silicon macOS 26.5.1 host. The Mach-O
load commands declare minimum macOS 14.0. A second macOS version and the
combined live publication and cache-corruption race remain outside the runtime
witnesses for this check.

## Default Sessions Dashboard Entry And Refresh

This intermediate Fullstack Product checkpoint covers the native default-summary
cache, Session sync and HTTP integration, and browser refresh and navigation.
The later [complete-entry checkpoint](#sessions-dashboard-entry-without-intermediate-states)
supersedes its cold loading state.
The default 30-day view may show its same-day, same-database and same-zone
saved result while a separate request updates it. A first visit without a
saved result shows the heading and loading state before calculating values.
The existing Usage Record calculations and filtered views supply the results.

On the same synthetic SQLite data with 266,657 Usage Records and about 78,500
in the default range, the median first default response across three new
processes per version fell from 185.75 ms to 4.60 ms with an eligible saved
summary in the new version. The intermediate cold shell response took 5.56 ms
while its separate calculation took 184.54 ms. The stale
summary response took 5.11 ms. The new HTML values and chart matched the prior
package. Real Session sync prepared the saved summary before completion, and
the signed app's native backend used that saved result after restart.

The independent source challenge identified a cache-miss focus and scroll
problem and a horizontal scroll reset. The repair keeps complete-result
responses for in-page filter and history transitions and captures horizontal
position before replacing the page region. Focused review confirmed both
repairs and Chrome executed the narrow-viewport and cold keyboard witnesses.

The final packages passed 427 Rust tests with 7 ignored by default, 133
Chrome checks, 85 Node tests and 51 build-tool tests. Formatting, Clippy,
privacy scanning, bundle startup and shutdown, and ZIP signature verification
also passed. The local web and Apple Silicon packages use build input
`2283c0d65694d3c71a8f7a63b25278d0e23d0eec98a6d0371454c3a6eac66389`.
The browser interaction witnesses used Chrome, and the packaged macOS witness
exercised the native backend lifecycle.

## Sessions Dashboard Paint Follow-up

The Frontend Product scope covers the Sessions Dashboard heading, loading
layout, and background refresh. At a 480 px viewport, the prior successful
refresh moved the summary up by 51.5 px when the notice left the layout.
The caption now holds that state in the heading. Chrome measured a 0 px
summary movement on the same refresh and kept the existing heading and
summary nodes mounted. With an empty summary cache, the cards and chart
loaded at the reserved positions, with 0 px movement at their start edges.
The browser checks confirmed that horizontal chart scroll, keyboard focus,
and filter history still work.

The two Chrome suites passed 138 checks. The Rust workspace passed 427 tests
with 7 ignored by default, and the build-tool suite passed 51 tests. The web
and Apple Silicon bundles came from build input
`c5d4700c033ea2ebc6a88c2f6a35f088193305ce04749e144b1990bae71adb5f`.
Both packaged backends started, served the loading and refreshed views, and
shut down. The app and extracted archive passed signature verification.
Chrome also completed a refresh using the previous template with the current
browser script during the local update.

## Sessions Dashboard Entry Without Intermediate States

The Fullstack Product scope covers the native cache-miss response, the
browser heading and results, and their integration on entry and refresh.
The prior layout fix still exchanged the heading description for temporary
copy and presented a skeleton on an empty cache. A cold entry now builds
the complete result in the document request. With a saved summary, the
ordinary heading and values appear immediately and the background refresh
keeps the same heading. The retry stays available when calculation fails.

Chrome kept Sessions as the committed document during a 220 ms injected
delay before a cold dashboard navigation. All 12 initial styled samples
contained the description, four values, and chart. The two captured images
before and after an unchanged saved-summary refresh matched byte for byte.
The browser retry check preserved the saved results and recovered after an
injected refresh failure. The HTTP suite also checked the first-calculation
error and its retry URL.

The two Chrome suites passed 146 checks. The Rust workspace passed 428 tests
with 7 ignored by default, and the build tooling passed 51 tests. API Clippy,
formatting, and the repository privacy scan passed. Both packaged backends
passed first entry, saved results, refresh, and shutdown checks. The app and
extracted ZIP passed signature verification. The installed builds use input
`b8fb1ab7c7ba5faeac0395b787988b9b334d967b75c3fb6b748779165b82b299`.

## Final Backup, Cancellation And Bookmark Repairs

The follow-up fixes three reproduced regressions. A backup restores valid TOML
dates, nonfinite numbers and large integers with the original file bytes.
Session-source discovery reports an invalid profile without dropping valid
siblings. Editing a malformed profile file and submitting a stale revision both
return 409 with the corresponding recovery message. A simulation interrupted
before its commit point records `SIMULATION_INTERRUPTED`, preserves the previous
reports and allows retry. Once publication begins, a successful operation emits
one completion. Legacy trailing-slash bookmarks redirect with the original query
string, including authenticated Context and Natural Search links in the desktop host.

Three named review challengers compared the Python baseline at
`e6958df0813b8652074c68a73ac61a8b551e59a8`, the pre-repair Rust bundle
`a839402f2fa4e0c269c8b54b6ac93c3dfb8562aeaadc8759287dbbed97e1d45e`, and the first
repaired bundle `8e767e6c68fc115e9dfe2f91c4b7108b488b4ef62e5246c7df9f576c225f1c1c`.
Initial discovery used no conversation fork. The reviewers found delayed signal
propagation, cancellation being reported as failure on a simultaneous error,
source profile isolation, and the two desktop alias omissions. They confirmed
the changed paths in the frozen second bundle
`019cb2366e292beac02e7b22910fc024d8793a68369734db006b2b53f3982075`. An additional
profile-write error response was repaired and confirmed on the final manifest
`1988197d0bdbfbfe02dbda8ac9fdef073409215181fa06fbdb10d2658d80f296`.

The packaged web and desktop hosts restored their own ZIP under a Python
execution denial, with exact TOML readback after restart. The same fixtures
retained a healthy profile, reported the bad sibling, and returned both 409
responses. Web checked seven saved routes. Desktop checked admitted redirects,
their rendered destinations, unauthenticated 401 and the strict Dashboard route.
Real SIGINT covered inventory rollback and retry, full-simulation validation,
pending report staging, and a signal after the new report became visible. The
recovery-test wait observes the scanner before status polling to avoid contending
for its operation lock while a stale marker still says running.

Both packages use input
`adc7d1f09f392659afeb05f36d90e503495243444ba3cb7e8cbb5c30eda3feb4`.
The ZIP checksum is
`e562bf7008e376d5e83c8c860ad43d64e31c6729a7f45f5b27a28faf19e06245`.
The app signature was verified in the bundle and after ZIP extraction. The
arm64/macOS 14 metadata and all 103 Terminal payload files were checked.
The complete build is staged under `dist/localbrain-adc7d1f09f39` because the
`lb` server is live and changing Terminal payload identity can mark an active
manager incompatible. A later read-only check on November 20 at 17:21 KST
matched the port 8000 listener to the default `dist/api/bin/lb` executable
from build `b8fb1ab7c7ba5faeac0395b787988b9b334d967b75c3fb6b748779165b82b299`.

The relocated web and desktop hosts started and served the restored settings
and Natural Search bookmark on their own loopback listeners. Rust 1.90 passed
431 workspace tests with seven default opt-outs and the desktop host lifecycle
test passed separately. Rust formatting, Clippy and the privacy scan passed.
Node passed 85 tests and build tooling passed 51.
Chrome passed 76 navigation, 70 initial-state and 143 real-PTY Terminal checks.
Navigation and initial-state checks preceded the final settings-refusal delta.
The Terminal browser run used the final shipped payload. Packaged-host and
native tests covered the settings-refusal delta with the final code.

The browser Terminal run used synthetic PTYs on macOS 26.5.1. Physical macOS 14,
native IME, and sleep/wake still need separate device evidence. The simulation
golden tests cover grouping outcomes. Edge-by-edge near-threshold similarity
comparison remains unmeasured.
