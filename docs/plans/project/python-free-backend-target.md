# Python-Free Backend Target

## Status And Authority

The user clarified on2026-11-18: the completion goal is removing Python from
the backend, and the measured settings regression requires optimization.
This is the final target for [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
and [REFACTOR-0006](../refactoring/refactor-0006-rust-core-transition.md).
The user subsequently approved `apps/api`, `apps/web`, `apps/desktop` and shared
`crates/`, and authorized completing implementation, retirement and independent
verification with subagents. [FEAT-0180](../feature/feat-0180-python-free-backend.md)
and [RUN-261](../run/run-20261118-261-python-free-backend.md) own that execution.
The directories and native backend are implemented and the tested-host runtime
exit passes [Eval0177](../evaluation/eval-0177-python-free-backend.md). Final
artifacts, regression repairs, minimum Rust and packaged performance are checked;
physical/other-platform, model-quality and strict-parity limits remain explicit.
Code remains the implementation truth.

Prior Terminal and common-settings passes remain bounded increment evidence.
They do not establish backend completion. Retaining Python HTTP/CLI, TOML/zone
adapters or model workers is an intermediate state rather than a final exception.
Earlier first-slice contracts retain their historical scope and results; this
clarification supersedes interpreting their retained Python as the final target.

## Runtime Completion Conditions

- The backend server, CLI, settings, persistence/recovery, source registration,
  Session/Context ingestion, Usage, jobs, retrieval and every currently admitted
  backend feature execute without a Python interpreter or Python helper process.
- HTTP/WS handlers, template rendering, startup/lifecycle and model installation/
  inference paths have native replacements. An optional Python model worker still
  counts as remaining backend Python; do not silently exempt it or remove the
  associated functionality. Native model execution must preserve or explicitly
  reconcile tokenizer/model fingerprints, numerical behavior and index compatibility.
- Delivered application/runtime files contain no PyInstaller backend, libpython,
  Python runtime packages or Python launch wrapper. Exercise actual packaged
  web/app/CLI flows on a host environment without Python, beyond source inspection.
- Preserve existing data/schema/IDs, private storage, authentication, provenance,
  feature admission, failure/cancellation/concurrency and UI/CLI contracts.
  Suspended native product features keep their source/evidence/data without
  being activated by migration or counted as delivered native functionality.
  The user's subsequent cleanup direction retires obsolete standalone Python
  research/reference programs and their tests; it does not activate those trials.
- Python remains only in current build/check/QA tooling and its tests, outside
  the shipped runtime. Obsolete executable Python parity/reference engines,
  benchmarks and compatibility launchers are removed. Frozen JSON/native golden
  observations and immutable historical evidence remain comparison records,
  not executable backend fallbacks. The independent Node PTY/VT engine is retained.
- Pass the declared Rust minimum and target-platform checks, separately from the
  available compiler/OS result. Once backend Python is removed, an old Python
  runtime minimum is not a remaining product-runtime gate.

Completion requires the full producer/consumer map from the
[migration inventory](rust-backend-migration-inventory.md), actual artifact
evidence and a remaining-Python count of zero for runtime dependencies. A settings
or Terminal slice must continue to be reported as a slice.

## Application Layout

```text
apps/
  api/                         # Rust HTTP/WS host, lifecycle and service wiring
  web/                         # shared app/browser templates, CSS/JS and assets
  desktop/                     # Tauri window, OS integration and app delivery
crates/
  core/                       # shared Rust domain, storage and service rules
  runtime/                    # CLI/helper and independent Terminal management
  models/                     # native assets, tokenizer and model execution
```

The API and CLI call common Rust functions directly. Tauri owns window/OS and
backend lifetime rather than duplicating domain rules. The desktop window and
development browser share web assets and their behavior contracts. Separating
these directories does not select React/Next.js, introduce a second UI, change
URLs or require rewriting the existing HTML/CSS/JavaScript.

Retired-source-to-current ownership:

| Retired source | Current responsibility |
| --- | --- |
| `src/localbrain/app/`, public Python entrypoints and feature web/CLI adapters | native `apps/api` and Rust CLI adapters |
| `src/localbrain/` rules, stores, ingestion, retrieval and model execution | native feature/service modules under the shared Rust backend, with explicit model compatibility evidence |
| `src/localbrain/templates/`, `static/`, `content/` | `apps/web`; Python template execution is separately replaced in the Rust host |
| `desktop/src-tauri/` and desktop-only startup/window assets | `apps/desktop`; preserve Tauri authority, auth, lifecycle and OS commands |
| `desktop/backend-entry.py`, `backend.spec` and PyInstaller packaging | retired after the Rust backend artifact replaces their delivery contract |
| `rust/localbrain-core/`, `rust/localbrain-runtime/` | `crates/` shared library/runtime, preserving app-independent Terminal management |

The moves include build/resource/discovery paths, scripts, tests and owner
documentation. The Python product package, PyInstaller entry/spec and obsolete
bridge packaging are removed. An immutable private comparison baseline and
current build/check tools remain outside the product runtime. Obsolete executable
Python research/reference fixtures and their dependent tests are retired;
historical methods and frozen native/JSON observations remain evidence only.
Generated runtimes and private application data retain their current external
storage/build owners; an application directory is not a runtime-data directory.

## Performance Requirement And Verification

The earlier Eval0176 observed warm-cache source medians of11.208ms per settings read and
41.029ms per save/readback, versus Python0.036/0.485ms; empty Sessions HTML
17.182ms versus2.690ms. Those measurements recorded an intermediate regression, not a successful
optimization or evidence that Rust computation itself is slower. Run261 resolves
the settings regression using the matched packaged comparison below; the
historical TestClient measurement boundary is not rewritten.

That intermediate source created one Rust child per common operation. A general
save invokes preflight, save and readback as three operations, with Python
syntax callbacks; source mode also recomputes the configured input fingerprint.
These boundary costs are included in that benchmark. Their individual shares
have not been profiled and must not be invented.

The target is a persistent Rust backend using native codec/time-zone and direct
core calls for ordinary requests. Preserve mutex/flock, stale-revision refusal,
unknown values, atomic publication and the distinct common/Terminal readback
stages. Purposeful process isolation for Terminal or model work retains its own
lifetime contract. Removing validation, skipping durability or caching stale
settings is not an acceptable latency fix.

The persistent Rust host calls native settings and services in process. Run261
compares the actual packaged release against pure Python and the intermediate
Python/Rust-child host with the same synthetic requests, PATH, client and extra
OS-profile condition. All four measured native medians and p95s improve; Eval0177
owns the complete values/method and residual model-timing limits. Earlier
source/debug/TestClient figures are not substituted for this delivered evidence.

Sampling identified Apple's F_FULLFSYNC in the intermediate native writer as the
remaining save cost. The final writer uses the original POSIX fsync on file and
parent, retains atomic rename, leases/revisions/private modes and distinct
readback stages, and passes actual injected failure/lost-ack controls. Complete
existing paths resolve once with the unchanged fallback and fresh validations;
no persistent stale-settings/path cache is introduced. Runtime inventory and
actual app/API/CLI/archive checks find0 LocalBrain Python runtime dependencies.
Blocked interpreter/library negative controls and real native process flows are
checked separately from the fair performance condition.

New product behavior/admission, installed user app/service replacement and
publication remain separate decisions. Physical minimum-OS, Windows, input/soak,
real large-model quality and exhaustive strict parity remain explicit evidence
limits rather than remaining backend Python or undisclosed unported owners.
