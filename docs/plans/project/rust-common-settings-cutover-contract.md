# Rust Common Settings Cutover Contract

## Status, Authority And Selected Increment

Selected contract for approved [FEAT-0178](../feature/feat-0178-rust-common-settings-cutover-contract.md),
[SPEC-0178](../spec/spec-0178-rust-common-settings-cutover-contract.md) and
[RUN-259](../run/run-20261117-259-rust-common-settings-cutover-contract.md),
under [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md).
Run259 fixed this contract before implementation. The later approved
[Run260](../run/run-20261118-260-rust-common-settings-runtime.md) implements it;
its evaluation owns actual delivery and acceptance, separately from Run259. The
[first-slice core contract](rust-core-and-host-contract.md#shared-settings-writer)
remains the historical first-slice boundary. Current policy ownership changes
with the product cutover without retroactively changing that evidence.

Run260 moves known common/terminal settings rules, ordered merge,
revision checks and the normal settings-file commit into `localbrain-core`.
The existing Python host retains a **syntax codec**: conversion between TOML bytes
and typed values using current `tomllib`/`tomli` and `toml_text`, plus the current
OS time-zone provider. The codec performs no settings selection, merge, default,
revision, lock or file-write decision. It is an explicit dependency of this
increment, separate from optional model workers. This does not complete Python
settings removal or the whole backend migration. A later codec replacement must
meet the same value/format contract under its own boundary.

Why retain it: the observed Python baseline reads/saves an unknown `2**100`,
accepts an overflowing float as infinity, retains date/time values and truncates
fractional seconds to Python precision. It also reads mixed arrays that its
serializer refuses to save. The inspected cached `toml_edit 0.25.17+spec-1.1.0`
converts integer scalars to `i64` and rejects float overflow. Its newer TOML
grammar is not an approved syntax change. No new Rust TOML dependency is selected.
Retaining the exact codec avoids treating a different parser as equivalent.

## Ownership And Complete Consumer Map

| Current path | Selected target and preserved output/effect |
| --- | --- |
| `foundation/preferences.py` defaults/read/save/effective/presentation | Compatibility facade over common Rust operations. Rust owns values/merge/normal commit; facade reconstructs Python `raw` with the codec. Presentation fallback still handles preferences errors, not missing/mismatched runtime. |
| `foundation/operations.py` | Parent retains the directory mutex, nonblocking flock and reentrant lifetime; expose the existing held descriptor as an internal lease. All non-settings users keep the same lock. |
| `terminal/settings.py` | General and Terminal defaults use the same common runtime and Rust transaction. Reuse current Rust terminal validation; no `foundation` import of `terminal/core.py`. Keep launch/read/error/public response differences. |
| `rust/localbrain-core/src/settings.rs` | Existing path/section/default-shell validation is reused through typed core calls. The same core gains common semantic/transaction operations; no Tauri/FastAPI/Node dependency or second validation implementation. |
| `app/settings.py` preferences GET/PATCH and onboarding | Same saved/effective/source/revision and error details; internal `raw` stays omitted publicly. Successful PATCH still notifies Session and Context schedulers only after successful readback. |
| `app/lifecycle.py` and `app/edition.py` | First absent-file initialization stays in startup after source/context discovery; native start still chooses onboarding/saved startup/settings recovery under existing token/origin rules. Runtime capability preflight precedes startup writes. |
| `app/web.py`, `app/templating.py`, `usage/web.py` | Preserve native root redirect, preferences template global/presentation fallback, next-render time zone and Dashboard aggregation. Do not flatten missing/invalid state into a valid saved value. |
| `sources/sync.py`, session/context sync | Same resolved preferences, completion-based schedule, enabled/manual behavior and shared lock; changes affect the next scheduling decision without interrupting active work. |
| `app/storage/recovery.py` | Retained explicit backup/restore owner; same backend storage lease and operations lock. Restore can replace settings as part of its existing multi-file recovery protocol. It is not a second normal settings writer or fallback. |
| source registry/settings and `persistence/migrations/sources.py` | Keep separate Session-source TOML, DB/reconnect/migration transactions and shared serializer/atomic helper. No transfer of those stores into common settings. |
| `terminal/workspaces.py`, presentation/shell integration; sync health | Keep their JSON/assets and shared atomic helper callers. Moving normal settings commits does not delete or change the helper they still use. |
| models/search/Context stores; suspended Drive preference consumer | Their own files/DB/locks and admission remain. Drive's time-zone consumer is retained but inactive in default assembly; no activation. |
| root CLI, `desktop.py`, native host and builders | Retain public CLI dispatch, current Python HTTP/CLI hosts and GUI. Provide the same trusted common executable in source/wheel/frozen layouts; app-less terminal management keeps its independent immutable payload. |

## Values, Codec And Exact State Semantics

The [approved Feature's common-value table](../feature/feat-0178-rust-common-settings-cutover-contract.md#inherited-common-values)
is binding: all seven fields, their exact types/defaults, schema1, retired raw
fields, ignored preference environment variables and first-start conditions.
Common `saved` equals `effective`; `source` is only saved/default. Rust requests
the current host's system-zone candidate for the real global config, or the
explicit config's time-zone candidate for isolated callers. The host uses the
existing `ZoneInfo` facility to answer validity; Rust selects UTC only for an
invalid default candidate. A saved/updated invalid zone is an error, not fallback.
No Rust time-zone catalog replaces the host's installed zones, aliases or cache.

### Lossless Ordered Exchange

All values cross the private codec channel as tagged nodes, never untyped JSON
numbers or an unordered raw object. Node keys are closed:

| Kind | Exact representation of the `value` field |
| --- | --- |
| `string` | JSON string, unchanged Unicode content |
| `boolean` | JSON boolean; never an integer |
| `integer` | signed decimal string of the Python integer, arbitrary precision within the actual Python codec's accepted input; no i64/u64 coercion |
| `float` | `float.hex()` string for finite values, `inf`/`-inf`/`nan`/`-nan` otherwise; preserve readable NaN sign and reconstruct the Python float before the existing serializer applies its own normalization |
| `date`, `time`, `datetime` | distinct ISO strings from the actual Python value; reconstruct the matching Python type, including offset/naive distinction and existing microsecond precision |
| `array` | ordered list of child node indexes |
| `table` | ordered list of `[string-key, child-index]` pairs; duplicate keys are invalid; updates replace in place and new keys append |
| `null`, `unsupported` | input-validation-only nodes, with `value: null`; never valid TOML output. They preserve invalid application input as invalid instead of transport coercion. |
| `surrogate-string` | input-only list of Unicode code points, including unpaired surrogates; preserves invalid application strings until their existing stage-specific refusal. Never TOML output. |

Use `{ "kind": ..., "value": ... }` for every node inside a flat exchange object
with exactly `root` (integer0) and `nodes` (node list). Nonempty nodes start with
the root; child indexes are exact nonnegative integers, not booleans, greater
than their parent and within the list. Every nonroot node has exactly one parent;
all nodes are reachable. This is an ordered tree in a flat wire representation,
without cycles, aliases or recursive JSON nesting. Codecs flatten/reconstruct
iteratively; Rust traverses the indexes. Tables preserve Python dict insertion
order independently of Rust JSON-map ordering. Do not add a JSON parser/encoder
nesting ceiling to TOML accepted by the current Python codec; retain that codec's
actual depth/refusal behavior. The TOML callbacks alone call existing decode/
encode logic on supplied bytes/trees. They receive no filesystem path or
arbitrary module/command. The codec reads/writes no settings files and performs
no business merge. The fixed `timezone.valid` callback uses only the supplied
zone string and existing OS/Python zone facility. `json.measure` receives the
former Terminal envelope, including path text as inert metadata; it measures
encoding without resolving/opening that path or gaining command/file authority.

`decode` applies UTF-8 and current TOML syntax; zero file bytes produce the
existing `{schema_version: 1}` raw value. Nonempty TOML without schema1 remains
invalid. `encode` applies the existing `toml_text` ordering/quoting/type/refusal
behavior, including nested tables and arrays-of-tables. A read-valid but
unserializable tree must still read and must refuse save before publication.
Finite/nonfinite floats, negative zero, Unicode, dates and large integers cannot
be silently narrowed, stringified as TOML strings, dropped or newly accepted.
Comments/original lexical spelling are not preserved by the current serializer;
this contract adds no such requirement. Output bytes must match the current
serializer for the same ordered post-merge tree.

### Read And Mutation Rules

- `common.read` opens one current byte snapshot, computes its SHA256 and decodes
  that same snapshot. It returns common values/source/revision plus raw typed
  tree. It does not acquire operations.lock or create data/cache/settings/service
  state. `common.defaults` does not open settings. Generic read preserves its
  current filesystem/error semantics; do not apply terminal-only owner/link/8MiB
  file restrictions to every common read. Generic atomic save still rejects a
  symlink target; terminal operations retain their existing stricter file checks.
- Common save first rejects a non-table `changes` or keys outside the seven
  common fields before acquiring the writer lock. A read-only `common.preflight`
  handles this check. It does not validate changed values yet or create state.
  Under the lock, re-read/validate current settings, compare requested revision,
  merge changes, validate the complete result, encode, then commit. Preserve
  current error precedence, not just the final failure class.
- General merge is the ordered equivalent of
  `{schema_version: 1, onboarding_completed: resolved_value, **current_raw, **all_common_values}`.
  It fills missing common values on explicit save and preserves unknown/retired
  fields and the entire raw terminal value, even if that value needs terminal repair.
- Terminal save locks first, validates current common values/revision, then
  validates its existing terminal section and proposed cwd/shell. Merge only
  cwd/shell into the current terminal table. Root ordering is the equivalent of
  `{schema_version: 1, onboarding_completed: current_common_value, **updated_raw}`;
  do not materialize every other missing common field as a side effect.
- Terminal read can show deleted paths for repair; launch validates actual cwd
  and executable shell. An explicit cwd override replaces an unused missing
  saved cwd without skipping saved shell validation. Preserve spaces, tilde/
  account/default-shell rules, blank vs missing values and type/length errors.
  Saving defaults does not change existing jobs, workspaces or terminal scope.
- Common save releases the outer operation lock **before** its final readback,
  matching current `save_preferences`; another valid writer may be reflected by
  that read. Terminal save performs its readback **inside** the lock, matching
  current `save_launch_settings`. Keep raw bytes, revision and decoded result
  paired for each read. Do not move these stages merely to simplify transport.
- Startup checks common-runtime capabilities first, then follows the existing
  storage/source/context initialization. Only an absent preferences file is
  initialized with all defaults and the established-registration onboarding
  correction. Existing empty/partial/invalid files are not startup rewrites.
  Startup choice applies next launch, time zone next render, schedules at the next
  decision; active collection and existing terminal jobs are not interrupted.

Preserve the actual startup selection predicate
`not (data_dir / "settings.toml").exists()`, not `not is_file()`. Generic read
likewise reads bytes when `path.exists()` and uses empty bytes otherwise.
A directory at that path is an existing read error, not a missing preferences
file to replace. A dangling symlink must still be refused by the existing save
symlink check, not turned into a new regular file by initialization.

## One Lock Lifetime And One Normal Commit

The parent remains owner of the per-resolved-data-directory thread mutex and
`operations.lock`, opened with the existing private O_NOFOLLOW/nonblocking flock.
The internal reentrant-held map must retain the actual descriptor/lease, not only
the path. Nested same-thread calls reuse it; other threads/processes retain the
existing busy outcomes. `purpose` does not create per-feature locks.

For a save, pass a duplicate reference to that **same open file description**
using POSIX `Popen(pass_fds=(lease_fd, ...))`. The child verifies descriptor mode,
file identity against that scope's lock and the request binding before reading
for mutation. It may confirm exclusive nonblocking flock on the inherited
description; it must not reopen/acquire a second writer-lock description. The
child closes its reference and never calls `LOCK_UN`, which would unlock the
parent's shared lock. Parent retains its mutex/descriptor until the child is
reaped, including cancellation and callback/transport errors. An outer caller
continues holding the lock after an inner settings call returns.

The host derives `LOCALBRAIN_HOST_PACKAGE_ROOT` and `LOCALBRAIN_HOST_DATA_DIR`
only from its installation/original configured data path, and forwards existing
SHELL/public-Hub cache environment for terminal identity/default-shell rules.
Rust applies these terminal-only checks at the existing terminal stage after
common/revision validation. Browser/preferences cannot select them; generic
common reads do not acquire terminal installation/cache restrictions.

Every child also inherits the read end of a separate parent-lifetime pipe;
trusted argv names `--parent-fd` and, for mutation only, `--lease-fd`. The parent
keeps the lifetime writer open until the operation finishes. Child EOF monitoring
does not compete with codec stdin reads and sets cancellation before publish;
EOF racing the final cancellation check/rename leaves a possibly committed
result. No process-global unlock, PID-only ownership or parent-alive guess is used.

Rust commits only after successful complete validation/codec encoding and the
under-lock revision check. It alone creates the same-directory private temp,
writes/flushes/fsyncs, atomically replaces settings and fsyncs the parent directory.
Preserve 0600 file, private new-directory mode, schema then onboarding ordering,
temp cleanup, and current OS error categories. The retained recovery copier may
replace settings only under its existing lease/operations-lock/recovery journal.
Do not reuse the manager control lock, start a manager or release the writer lock
while waiting for a settings child or codec response.

The descriptor mechanism follows [Python3.11 `pass_fds`](https://docs.python.org/3.11/library/subprocess.html#subprocess.Popen)
and [Apple flock duplicate-reference semantics](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html).
Isolated current-Mac probes corroborate inheritance, blocked reopen, retention
after parent-reference close and release after final child close; they do not
validate the future Rust implementation.

## Common Runtime API And Failure Contract

### Runtime And Public Boundaries

Keep one shared `localbrain-core` library and `localbrain-runtime` executable.
Add a distinct `preferences` mode and `preferences --capabilities` entry; no
Tauri/HTTP/Node/launchd requirement or persistent settings service. A new
`foundation/rust.py` transport owns this common child/codec lifecycle and imports
no terminal feature or preferences error class. It raises neutral transport
errors; preferences and terminal facades map them at their owning boundary.
Existing terminal `control`, stream/helper/manage modes, host protocol1 and
manager protocol2 stay separate. App-less terminal management continues using
its immutable Node/helper payload even if the app/common executable is removed.

Capabilities return closed fields `contract`, `codec`, `build`, `target`,
`minimumOs`, `operations`; selected values are contract1, codec1, and exactly
the operations below. The manifest records the separate executable SHA256 and
source/build-input fingerprint. A matching package version alone is insufficient.
The runtime reports its compile-time build fingerprint, not a value read from a
mutable receipt or runtime environment; compare it with the packaged receipt.
Reject missing/mismatched capability, binary/hash/target or manifest before
startup writes. Do not fall back to an old runtime or the Python normal writer.

| Operation | Input and stage | Result |
| --- | --- | --- |
| `common.defaults` | trusted config/system-zone candidate; no settings I/O | seven resolved defaults |
| `common.read` | trusted data/home context; no lease | saved/effective/source/revision and raw tagged tree |
| `common.preflight` | tagged changes; no lease/file I/O | valid flag or existing unsupported-changes preferences error |
| `common.save` | inherited lease, tagged changes and expected revision; repeat preflight and ordered locked validation | commit acknowledgement; wrapper then releases lock and calls common.read |
| `terminal.read` | trusted context; common read plus existing terminal interpretation | cwd/shell/default_shell/revision and public preferences subset |
| `terminal.launch` | same plus optional typed cwd override | fixed cwd/shell only, after launch validation |
| `terminal.save` | inherited lease, typed cwd/shell and expected revision | common/terminal readback under the same retained lock |

Public HTTP/CLI shapes, authentication, status mappings, allowed actions and
normalization stay with existing adapters. General busy remains OperationBusy;
terminal busy keeps its current PreferencesError wording. Preferences validation
maps to existing 409/detail; terminal validation/identity keeps its existing
kind/code/message mapping. Preserve current post-encode filesystem OSError
behavior rather than disguising it as a validation success.

### Private Framing And Codec Calls

One child handles one operation. Every UTF-8 JSON-line frame has closed keys,
`wire:1`, request `id` and a discriminating `type`; the initial call also names
`contract:1`, operation, trusted context and expected stream identifiers. Fixed
arguments are described above; arbitrary operations, fields, paths from browser
payloads, callback imports and shell commands are forbidden. Mutation descriptors
arrive only through inherited descriptors and trusted argv, never HTTP data.

Use call/result/error/codec/codec-result and begin/chunk/end frame types. Scalar
metadata frames have a 128KiB byte limit. Large raw TOML or encoded tagged JSON
travels as named streams: begin gives the expected UTF-8 byte length; chunks carry
strict increasing sequence numbers and at most 16KiB decoded UTF-8 each; end
gives SHA256. Verify length, digest, order, request/callback binding and stream
completion before decode or commit. Split only at UTF-8 boundaries; worst-case
JSON escaping still fits the metadata-frame bound. Codec callback operations are
exactly `toml.decode`, `toml.encode`, `timezone.valid` and `json.measure`, with typed result/error.
Callbacks are never forwarded to a browser or external service.

Common settings have no new total-file-size cap: the old common reader accepts
files larger than terminal's separate 8MiB bound. Stream framing bounds messages,
not accepted source population. Memory remains proportional to the decoded file
as in the current TOML reader; this contract claims no lower memory usage.
Drain both child pipes concurrently; retain only bounded 4KiB stderr diagnostics
and no permanent/private-content log. Codec requests operate only on the exact
supplied snapshot/tree, with no reread or hidden save.

Use a 40-second child-operation deadline after spawn, including codec exchange,
and explicit kill/drain/reap on timeout/cancel. This is a **new internal transport
failure boundary** for common preferences, not an old Python timing guarantee or
a task deadline; downstream product approval/functional checks must include it.
Transport/version/identity failure is unavailable503 at the common HTTP boundary,
not saved/default success; CLI/startup reports a fixed diagnostic and nonzero
exit. Startup preflight fails before DB/settings initialization if the required
common executable is missing. Preferences-content errors still expose existing
Settings recovery/presentation defaults when the runtime is healthy.
This guard applies to backend/settings entrypoints that require the new runtime;
do not add a global CLI guard to unrelated doctor/models/storage/init/scan paths
that do not call migrated settings. Preserve their actual existing dispatch.

### Closed Frame Schema

Common fields in every frame are exactly `wire`, `id`, `type` plus the row's
fields below. `wire` is the exact integer1, not boolean; `id` is a nonempty
request identifier of at most128 characters. Unknown keys/types/sequence/state
are protocol errors. Context keys are exactly `dataDir`, `cacheDir`, `homeDir`
(trusted absolute strings) and `defaultZone` (a tagged candidate). Presence of
cacheDir does not authorize checking/creating the terminal cache for preferences.

| Type | Additional fields | Direction and constraint |
| --- | --- | --- |
| `call` | `contract`, `operation`, `context`, `argsStream` | parent→child first frame; contract integer1; argsStream exactly `arguments`, whose tagged table follows |
| `codec` | `seq`, `operation`, `inputStream` | child→parent; seq starts0/increases1; fixed callback operation; input stream exactly `codec-N-input` for seq N |
| `codec-result` | `seq`, `ok`, `outputStream`, `error` | parent→child; same seq; exact boolean ok; success names `codec-N-output` and error null, failure has outputStream null and typed error |
| `result` | `resultStream`, `commit` | child→parent only after input/callbacks finish; resultStream exactly `result`; commit is `none` or `published`; exactly one final result/error |
| `error` | `error` | child→parent final typed error; no result stream |
| `begin` | `stream`, `length`, `encoding` | promised named stream only; nonnegative integer byte length; encoding exactly `utf8` |
| `chunk` | `stream`, `seq`, `data` | direction of active stream; seq starts0/increases1; data JSON string within decoded chunk limit |
| `end` | `stream`, `sha256` | ends exactly declared length; SHA256 lowercase64-hex of concatenated unescaped UTF-8 bytes |

The arguments stream is a flat exchange whose root is a tagged table with only
the operation table's fields:
defaults/read/terminal.read have none; preflight has changes; common.save has
changes/revision; terminal.launch has optional cwdOverride; terminal.save has
cwd/shell/revision. Revision and proposed values remain typed nodes until their
stage-specific validation; malformed revisions must not bypass current-file
validation. The result stream is UTF-8 JSON of the row's fixed public/internal
result, with a flat tagged raw tree only where specified. A defaults/read call still
receives context but does not gain a mutation lease.

Codec input/output streams are UTF-8 JSON: decode consumes a JSON string of TOML
and returns a flat exchange with a table root; encode consumes that exchange and
returns a JSON string of encoded TOML; timezone.valid consumes a flat exchange
with a string root and returns an
exact boolean. Rust checks known field types before requesting timezone validity.
`json.measure` consumes a flat exchange of the former terminal control envelope
and returns its exact existing Python JSON/UTF-8 byte length. Rust alone applies
the retained128KiB terminal request bound before terminal value validation; this
adds no common-file cap. This Run260 syntax-only refinement preserves large-input,
nonfinite-number and unpaired-surrogate failure precedence discovered during
differential execution. It selects no command, path, rule or write. The host
retains an original local codec exception for its existing failure category;
wire/HTTP diagnostics never include raw source bytes or arbitrary stderr.
Codec failures use the same typed error shape, with commit state not-published.
Typed errors have exactly `kind`, `code`, `message`, `errno`, `commit`: kind is
preferences/terminal/transport/io; code/message strings; errno an integer or null;
commit is not-started/not-published/unknown/published. Preserve existing validation
messages at the facade; I/O errors retain errno/category. No raw codec bytes,
traceback or arbitrary child stderr becomes an HTTP/CLI error message.

### Failure And Recovery Matrix

| Predicate/stage | Required outcome |
| --- | --- |
| non-table/unknown changes before lock | existing PreferencesError; no settings/lock/data creation |
| same-thread outer lock / competing thread or process | reuse inherited lease / existing nonblocking busy; no second lock file or fallback write |
| malformed UTF-8/TOML, unsupported/noninteger schema, invalid current common field | preserve file; current preferences error before stale-revision/changed-value checks |
| stale/malformed expected revision after current-read validation | current conflict; no encoding/publication |
| readable but unserializable unknown value | read remains available; encode error preserves existing bytes and cleans any temp |
| wrong/missing inherited descriptor or scope/callback/stream mismatch before publish | refuse, reap/close child reference; parent/outer lock remains until its own release |
| codec/child error or cancel before rename | no published patch; clean temp; close/reap before releasing parent lease |
| parent dies during operation | inherited child reference keeps serialization until child exit; EOF cancels the operation, with a publish race treated as unknown rather than presumed rollback |
| rename may have happened, directory fsync fails, child/response lost | commit is possible/known; read current revision/values before any user retry. No blind rollback, stale replay or claimed all-or-nothing failure |
| old/new binary or incompatible platform/receipt | unavailable before startup writes; retain file and old install for explicit rollback, no auto-upgrade/manager restart |
| successful settings save | no existing terminal input/replay/kill/restart, workspace reset, rescan or model action; preserve schedule notification and readback stage |

## Source, Wheel And Frozen Delivery

First implementation target is the existing Rust/native target:
`aarch64-apple-darwin`, minimum macOS14. This is a scoped first product, not
new Windows/Intel/Linux support, a universal wheel or a silent minimum-OS promise
for every old Python installation. Unsupported installs remain on their prior
supported delivery; do not auto-upgrade them or delete their code/data. Broader
runtime delivery requires its own admitted target/evidence.

| Layout | Required common executable provision and discovery |
| --- | --- |
| source/web | trusted build command compiles the locked workspace and produces `dist/common-runtime/bin/localbrain-runtime` plus `common-runtime.json`; source bridge discovers that exact receipt. Rust is a source build prerequisite. No Node/npm/model action in this common builder. |
| installed wheel | build hook stages the same binary/manifest into package `bin/` and emits a platform wheel tagged `py3-none-macosx_14_0_arm64`; a Mach-O payload must not ship in `py3-none-any`. Installation requires no Rust/Node compiler. Build/prebuilt-input validation belongs to the new product implementation. |
| frozen app | package the common binary/receipt independently of `terminal/runtime`; include in final code signing, notices and BUILD-INFO/hash checks. The Python host chooses its packaged path; no checkout/Cargo/PATH dependency. |
| explicit development override | only trusted absolute `LOCALBRAIN_CORE_RUNTIME`, paired with its compatible receipt; never browser/user-settings values, PATH lookup or `LOCALBRAIN_TERMINAL_BUNDLE`. Override mismatch refuses rather than falling through. |

Discovery precedence is explicit override → known installed/frozen package path
→ source receipt in an actual checkout. A selected but invalid candidate is a
failure, not permission to search another version. Validate target/capabilities/
post-sign binary hash/input identity. Common startup, settings and repair do not
require terminal assembly/cache/Node/helper/launchd, install a terminal payload,
replace a live manager or change existing services. The terminal builder may use
the same Cargo-produced executable for its own immutable payload; that payload
keeps its own signed manifest/version/lease and explicit update rules.

The common receipt has exactly schema1, contract1, codec1, build (source-input
SHA256), target, minimumOs, executable (`bin/localbrain-runtime`) and
executableSha256. Its build input manifest covers the relevant Rust sources/locks,
host codec/bridge and common-build/packaging inputs, separate from the final
signed executable digest. Every layout keeps this relative bin/receipt structure;
an override names that generated `bin/localbrain-runtime` and resolves the receipt
at its parent bundle root. A bare Cargo output without the receipt is not an
installed common runtime. Neither browser nor preferences can select it.
The platform-wheel requirement follows the
[PyPA compatibility-tag specification](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/);
the existing Hatch build backend remains, with its actual hook version/API and
artifact inclusion verified during product implementation rather than inferred
from current generic packaging metadata.

Selected existing dependencies stay serde1.0.229 (declared Rust1.56),
serde_json1.0.154 (1.71), libc0.2.191 (1.65), sha2 0.10.9 (no declared MSRV);
MIT OR Apache-2.0 licenses are present in their cached upstream manifests.
Workspace declaration stays Rust1.90/edition2021; observed local cargo/rustc are
1.99.1, accessible via the installed absolute toolchain path. Minimum1.90 was
not executed here. Python base remains3.9+ with current pinned/declared tomli
fallback; observed baseline tests use Python3.11.15. No parser/toolchain/host
upgrade is selected, and no future dependency-integrity/build pass is inferred.

The codec contract follows the [Python3.11 TOML conversion table](https://docs.python.org/3.11/library/tomllib.html#conversion-table)
and the actual repository serializer, not a claim that tomllib writes TOML.
[Python subprocess pipe/timeout rules](https://docs.python.org/3.11/library/subprocess.html#subprocess.Popen.communicate)
inform concurrent drain and explicit child cleanup. Actual locked sources,
checksums/licenses and supported-target/MSRV builds remain product gates.

Rollback uses the recorded old source/wheel/app with unchanged schema1/data;
there is no data migration or automatic downgrade. Stop incompatible normal
writers before switching installation; preserve settings and existing terminal
manager/payload/jobs. A running old host can still use its old Python transaction
under the same lock/revision contract, but is not a hidden fallback inside the
new host. Arbitrary-version rollback, uninterrupted binary replacement and
performance improvement are not promised.

## Downstream Implementation And Acceptance Gate

One product Feature implements this entire normal-settings transaction and its
common host/delivery consumer wiring. Retained syntax/time-zone adapters and
recovery/shared helpers are explicit; no second normal Python writer. No other
settings store, DB schema, UI framework, model/VT engine or feature admission is
part of that slice. A complete product must include:

1. Frozen actual old/new code/dependencies/config/guidance and the full map above;
   independent data/concurrency omission challenge and informed repair review.
2. Differential read/default/common-save/terminal-read/launch/save cases for
   known/missing/invalid/retired/unknown types, exact error order and serializer
   bytes. Include large integers, float overflow/nonfinite/negative zero,
   date/time/offset precision, nested arrays/tables, read-valid/write-refused
   mixed values, stale revision, Unicode/spaces and terminal8MiB vs common limits.
3. Real inherited-fd/outer-lock and two-process/thread competing settings/source/
   scan/backup/restore cases; child/codec failure, deadline, parent loss, rename/
   fsync/ACK-loss races, temp cleanup and safe readback. Never operate user jobs.
4. Fresh/existing/empty/partial/corrupt-file startup and second unchanged restart,
   initial onboarding correction, both save/readback stages, template/time-zone/
   schedule consumers, origin/native token guards and no service/model side effects.
5. Isolated source and installed-wheel startup with terminal package omitted and
   Node/model prerequisites absent; correct wheel tag, binary/receipt/capability
   bytes, missing/mismatched/unsupported refusal and existing CLI commands.
6. Locked Rust builds/tests, declared minimum compiler or explicit acceptance
   gap, actual arm64 packaged-backend/native Settings save/reopen and resource
   observations separated from source/browser evidence. No installed-app
   replacement or deployment is inferred from an implementation approval.
7. Update architecture/current settings/storage/developer/build/README/app guides
   at the actual behavior change; renew catalog/owner/link/privacy checks and
   remove owned scratch. Report retained Python codec/model/host and Node debt,
   measured limits and the still-separate Terminal177 native gate.

Run259 evaluates only contract completeness/current-source consistency. It does
not pass this implementation gate, actual runtime packaging, whole-application
parity, independent code review, native/physical input or performance acceptance.
