# EVAL-0176: Rust Common Settings Runtime

## Metadata

- ID: `eval-0176`
- Status: `complete`
- Evaluator Type: `contract`, `functional`
- Result: `PASS`
- Run: [RUN-260](../run/run-20261118-260-rust-common-settings-runtime.md)
- Attempt: `1`
- Feature: [FEAT-0179](../feature/feat-0179-rust-common-settings-runtime.md)
- Spec: [SPEC-0179](../spec/spec-0179-rust-common-settings-runtime.md)
- Execution Profile: backend-product
- Surface Lane: core/transaction, adapters/consumers, packaging/docs
- Evidence Coverage: `complete` for the selected settings increment on the tested host; platform, physical and whole-backend limits below remain
- Created: `2026-11-18`

The common general/Terminal settings increment passes. Rust owns the seven
common-field rules, ordered merge, byte revision and normal `settings.toml`
publication. Python retains exact TOML syntax/serialization, OS time-zone lookup,
HTTP/CLI/template hosts, recovery copying and shared helpers for other stores.
The new common executable is independent of the optional Terminal payload.
This is bounded contract/functional acceptance, not whole-backend parity,
installation, release approval or evidence of a speed improvement.

## Method And Artifact Identity

Primary performed sequential Spec, Builder, Contract and Functional Evaluator
roles. The required independent data/concurrency challenge used the named
read-only `review_challenger` on frozen old/new source, followed by informed
repair checks. Primary owns adjudication and acceptance; reviewer output is
evidence and did not approve completion.

Baseline is actual archive `e6958df0813b8652074c68a73ac61a8b551e59a8` plus13
preserved planning inputs. Initial619 code/build/test fingerprints and all five
candidate snapshots/diffs remain privately retained. Final candidate5 contains
1,969 files, manifest SHA256
`767a0a8e0962ea5979841fd8b25ecdc1d9f77e3379f253a37ceba5eda17a2e1d`.
Final636 other non-document inputs still match that snapshot; the sole later
packaged-guide delta adds the same recovery instructions in Korean. Executable/
build/test code is unchanged; delivery/native/doc checks are renewed for that
guide. Other later edits close owner documents. No candidate commit is invented.

- Common build: `d5b15e5a6dd79d93114eba752dbbe16bb41f7f23ff5264eb75204197ba44dde9`.
- Final common executable SHA256: `8ccf7238f3802ed28c7f04ae03d98bb77670ff023d662f023422a75db6053e23`.
- Platform wheel SHA256: `b3d66524b67e1171d5c5bea1f8b675e44600747aee274e782acbde5dc2af37c5`; tag `py3-none-macosx_14_0_arm64`, non-pure, Hatchling1.33.0.
- Signed app build-input SHA256: `8fb8de03adf070a6088d5e2cfe89318b1a13dd53d59108069b48bd0d9dd09567`,440 inputs; source remains dirty over the baseline commit.
- App ZIP SHA256: `e6b49f841e5db37e9a9fc0b026c37fd9c3e3f63fa26e0b6783ccff9e45e89d78`.

Immutable snapshots, full reports/harnesses, synthetic native-window captures,
review/adjudication receipt and final check receipt reside under the configured
ignored stage `stage-20261118-common-settings-runtime-evidence`. Tracked outputs
contain synthetic facts and stable identities, with no dependency on temporary paths.

## Acceptance And Source-To-Target Checks

| Feature point / previous owner | Implemented boundary and distinguishing evidence | Result |
| --- | --- | --- |
| 1: Python general/Terminal normal writer | `localbrain-core::preferences` owns rules/merge/commit; both thin facades use neutral `foundation.rust`. No normal Python fallback. Existing `atomic_private_write`/serializer consumers and explicit restore retain their separate owners. Source review and existing recovery/store tests preserve those paths. | PASS |
| 2: Python values/revision/serialization | Retained syntax adapter plus ordered flat typed graph preserves bool/int, huge integers, overflow/nonfinite/signed zero and NaN sign, dates/times/offset/precision, deep tables/arrays, unknown/retired order, exact schema/defaults/error priority, byte SHA and private save. Actual old/new277 cases agree across defaults/read/common save/Terminal read, launch and save, including read-valid/write-refused values and common files larger than8MiB. Terminal retains its existing8MiB/type/identity restrictions. | PASS |
| 3: mutex/flock transaction and recovery | Parent passes the same inherited description and keeps mutex/lease until reap; child never unlocks it. Nested/thread/process contention, wrong descriptor/scope, parent EOF/death, codec/child loss and timeout pass. Ten named directions cover source registration, Session sync, Context sync, backup and restore versus both settings saves, and those producers against a held Rust child. Real file-sync/rename/directory-sync/lost-ack faults and kill-after-temp distinguish unchanged bytes from possible publication/readback. General readback remains outside its lock; Terminal readback stays inside. | PASS |
| 4: Terminal-dependent delivery | Standalone common builder, closed receipt/capabilities/build/hash/target checks and source/wheel/frozen discovery work without Node/models/launchd/Terminal preparation. A valid bundle beneath a folder named `payloads` also passes; preferences dispatch precedes Terminal leasing. Foundation imports no Terminal package. No live payload/job is replaced or stopped. | PASS |
| 5: admitted transport/startup failures | Strict framing/callback graph, seven corrupted-channel probes and kill/reap tests refuse invalid input while preserving the outer lease. Actual default deadline expires at40.008s with bounded diagnostics under1MB stderr. Missing/mismatched runtime refuses before initial startup writes; after healthy preflight, six actual CLI/desktop startup failure paths exit nonzero with fixed diagnostics. HTTP503 and uncertain-save readback remain distinct from malformed preferences409/recovery. Unrelated `doctor` still works. | PASS |
| 6: hosts and consumers | Existing API/auth/onboarding/startup/time-zone/schedule/template tests pass. Both concrete sync services survive a temporary CoreError at loop-read and under-lock-read, record failure and resume. Native outer middleware returns503 before cookie. Settings PATCH, native handshake, Terminal page and dependent async error-template callers run blocking work in the existing worker pool; three deliberate stalled-call HTTP probes retain responsiveness. Browser70 checks preserve loading/retry, actual served controls, settings and adjacent states. | PASS |
| 7: delivered source/wheel/app | Locked source builds, sdist→wheel, actual installed base wheel and final signed relocated Tauri app pass. Wheel335 source Python/HTML/JS/CSS assets match; source/sdist wheels have403 identical package files and identical archive SHA. Installed wheel starts/saves/conflicts/restarts with PATH excluding Cargo/Node and no checkout/Terminal bundle. Actual native controls save General timezone and Terminal cwd, reopen and Quit/relaunch with identical saved bytes/unknown values; runtime outage503 recovers after restore. Final signature, receipt and ZIP digest match. | PASS |

The producer contention probes combine actual Python transaction threads and
the real settings child; they are not every named pair in separate OS processes.
Separate process/lease tests establish the checked cross-process behavior.
Differential cases use actual frozen legacy code, but share fixture author,
unchanged codec/helper lineage and some premises; they are not an independent
exhaustive oracle. Native API probes supplement actual AX controls rather than
standing in for window interaction. No terminal engine or user job was started.

## Findings, Repairs And Rechecks

Fresh challenge found two supported omissions: CoreError could kill both sync
daemons, and native handshake failure escaped the inner HTTP handler as500.
Before/after witnesses support the retry and outer-middleware503 repairs.
Informed checks confirmed those causes and identified native/Terminal async
callers still blocking during child waits; the complete affected render-helper
sweep preserves auth, statuses, arguments and transaction exit. One test-only
in-memory SQLite fixture now permits its existing sequential awaited worker
access; production opens the connection in that worker. Its assertions remain.

Primary additionally repaired the finalizer's actual PyInstaller resource path,
signed NaN transport, invalid inherited-fd ownership, long-path temp-name growth,
syntax/facade exception ownership, preflight/late-startup diagnostics and
standalone `payloads` dispatch. Real990-byte data-dir and kill-after-temp cases
renew the path/cleanup witness. Late startup failure can retain completed earlier
DB/source initialization; no global startup rollback is promised. Browser QA's
obsolete loading literal was corrected to the existing state contract; no
product UI was redesigned.

The final narrow informed review verified all1,969 hashes and both last repairs,
with no new concrete candidate in its inspected delta. Initial author reasoning
was withheld; later review saw rationale/findings. Reviewer executed no reviewed
code and had not seen final delivery/native/full results. The seven-corruption
report was copied after that review and was not independently inspected.
Review/source/fixture lineage and unobservable actual model/cost limits remain
explicit; repeated informed passes are not fresh independent discovery.

## Verification And Cost

- Full Python discovery on final code:1,731 run, PASS,49 optional skips;74.389s.
  Locked Rust tests:11 pass; `cargo fmt --check` passes on Rust1.99.1.
- Final targeted32 startup/settings/responsiveness cases and separate36 affected
  render-consumer cases pass, alongside the differential/fault/lease witnesses.
  The full suite includes the configured contract/builder/helper regressions.
- Source common build, wheel/sdist/rebuilt archive wheel, PyInstaller/Tauri build,
  post-sign identity, deep signature/private-build-path checks and final native
  acceptance pass on macOS26.5.1 arm64/Python3.11.15. Signing is ad hoc;
  notarization and distribution are not part of this result.
- Closing owner tests:17 pass, catalog freshness passes, schema audit retains
 759 objects (647 keep/112 defer),2,365 local links/anchors across23 repository
  documents pass; both changed app-guide sources use their actual renderer's
  link/anchor tests. Privacy1,971 and whitespace pass. Earlier source-changing builds safely refused publication; stale
  reports and sandbox/certificate failures are not presented as final passes.
  Build retrieval used verified system certificates, without disabling TLS checks.

Fresh-process, warm-OS-cache microbenchmark on the same synthetic schema1
compares actual baseline and final code. These are observations, not a budget or
machine-cold result. HTML is an empty Sessions page through TestClient, including
route/template work, without network/browser paint.

| Measurement | Baseline Python | Final common Rust runtime |
| --- | --- | --- |
| First read in fresh host |0.339ms|23.440ms|
| Read,30 samples, median / p95 |0.036 /0.070ms|11.208 /13.045ms|
| Save including readback,10 samples, median / p95 |0.485 /0.667ms|41.029 /46.999ms|
| First HTML response after lifespan |41.310ms|62.845ms|
| Warm HTML response,10 samples, median / p95 |2.690 /3.009ms|17.182 /19.084ms|
| Host peak RSS including web imports |80,560,128bytes|83,902,464bytes|

Observed final child peak RSS is2,523,136bytes; it may include Git discovery,
so it is not a Rust-only allocation claim. One-child-per-operation isolation and
retained syntax callbacks add latency. No speedup, physical UI latency, long-soak
resource bound or minimum-OS performance claim follows. Deliberately stalled
operations no longer block unrelated checked HTTP requests.

## Limits And Route

No unresolved defect or missing required native Settings witness blocks this
bounded pass. Rust1.90/Python3.9 minima and macOS14 hardware were not tested;
available versions above do not establish those results. Other architectures/OS,
recipient installation, physical IME/VoiceOver/sleep, long soak and whole-backend
parity remain unverified.49 optional full-suite skips are not passes; unrelated
Terminal PTY/physical acceptance is not renewed here. Feature177's later window
packet remains pending under its own owner.

Complete FEAT-0179/Run260 and Phase3B's settings increment. Remaining persistence,
source/Session/Usage/Context/retrieval families still require their own approved
boundaries and delivered-consumer evidence. Python codec/zone/hosts/model workers
and Node PTY/VT remain explicit. No installed app, user data/service/job or Git
publication is changed by this acceptance.
