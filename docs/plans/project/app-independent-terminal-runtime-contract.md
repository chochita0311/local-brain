# App-Independent Terminal Runtime Contract

## Status And Ownership

Accepted target contract for [FEAT-0168](../feature/feat-0168-app-independent-terminal-runtime-contract.md),
[SPEC-0168](../spec/spec-0168-app-independent-terminal-runtime-contract.md) and
[PRD-0030](../prd/prd-0030-macos-terminal-work-area.md), consuming the passed
[Rust core/host contract](rust-core-and-host-contract.md).
**Run248 planning baseline:** the app excluded Terminal; these contract Runs
neither installed nor started the target runtime. Later product work delivered
native admission through [FEAT-0171](../feature/feat-0171-native-terminal-integration.md).
The [current Terminal policy](../../policies/project/terminal.md) stays authoritative
for implemented behavior. This owner fixes lifetime/payload/helper/management,
not app HTTP/WS admission, terminal groups or command-status signals.

## Scope And Identity

Preserve the current configured-scope derivation using resolved path strings,
without case folding, new Unicode normalization, trailing-segment substitution or
UI-edition suffix:

```text
scopeSuffix = SHA256(UTF8(resolvedDataDir))[0:10]
runtimeRoot = resolvedCacheDir / ("terminal-" + scopeSuffix)
domain = "gui/" + decimal(currentUid)
label = "dev.localbrain.terminal." + SHA256(UTF8(runtimeRoot))[0:16]
socket = runtimeRoot / "control.sock"
```

Core receives the host's configured paths, repeats owner/private/storage validation
and binds every command to that scope. Same data+cache and compatible payload use
one manager whether invoked from web or app; different data or cache selects its
own root/label. No global service registry or per-UI manager is introduced.

Protocol2 `scope.json` is owner-private schema1 metadata with resolved data/cache
paths and `scopeHash=SHA256(dataDir + NUL + cacheDir)`. It contains no launch
environment or terminal content and is created only by explicit prepare/start.
Identity binds that full hash as well as the root, so a truncated hash collision
or moved/copied root cannot silently adopt another configuration's manager.
Read/list does not create scope.json or directories. A known legacy root lacks
this new receipt; only its verified current protocol/identity management is allowed,
not implicit protocol2 adoption or a fabricated empty scope.

Use the current private directory0700, file0600 and executable0700 ownership rules,
regular/no-symlink/single-link control/identity files and same-user Unix socket.
`control.lock` is the same per-root nonblocking POSIX flock for prepare/install/
start/create/stop/restart/update; settings use the separate existing operations.lock
transaction and do not hold control.lock across it. A busy/unknown owner is a refusal,
not permission to remove locks, bootout or start a second manager.

Explicit preparation also creates owner-private `leases/<payloadId>.lock`. A Rust
command/helper executing from that immutable payload holds a shared lease for its
whole lifetime; a cleanup requires an exclusive lease. Merely inspecting a missing
runtime never creates a lease/file. This protects a still-running helper/management
child even when its parent manager has exited. All acquisitions are nonblocking;
on contention release already-held locks and return busy, never wait with opposite
lock ordering. Manager identity/job liveness independently protects its Node code.

### Control metadata ownership

| Private cache artifact | Single writer / state rule |
| --- | --- |
| Runtime manifest/payload files | Builder defines immutable signed bytes; Core only verifies/stages/copies, never edits an in-use payload |
| scope.json, selection.json and launcher | Core under control.lock, schema1 plus full scope hash, same-directory atomic publication; preserve/refuse unsupported versions or unexpected fields rather than silently replacing them |
| identity.json/socket | Selected manager writes its own validated generation at bootstrap and removes only its own identity/socket at clean exit. Core inspects; it replaces stale identity only through the explicit new-generation/loss-preservation transaction |
| leases | Core creates at explicit preparation; later processes use existing owner-private file locks, with no activity data appended |
| losses | Core records only per-payload last unresolved identity/build before an explicit fresh start can overwrite it. Legacy uses a separate build key. No automatic clear, transcript, VT, input or environment data |

This is deployment/control metadata under the existing private cache owner, not
new product DB/group persistence. It is excluded from application backup/restore
and must not become a reconstructed running session. Unknown schema/type/ownership
is a preservation/refusal result; never truncate it into a fresh empty receipt.

`selection.json` is exactly `{schema:1,scopeHash,payloadId}`; payloadId is64 lowercase
hex or null only for a clean stopped/unprepared runtime. It is the selection source,
not parsing the launcher script or choosing the newest folder. Launcher and selection
must name the same verified payload before bootstrap. Their separate atomic writes
are not a multi-file atomicity claim: interruption before both agree yields explicit
setup recovery and no bootstrap; only a new explicit prepare under the lock repairs it.

## Bundle And Stable Paths

### Resource and runtime layout

Use the existing Tauri resource-tree approach, adding an explicit `terminal/runtime/`
resource to the future builder. Keep execution native-side; no general JavaScript
shell permission, `sh -c` API or new Tauri business logic is needed. Resources can
ship a directory tree, whereas a Node executable alone does not provide PTY modules.
The official [Tauri resources](https://v2.tauri.app/develop/resources/) and
[sidecar](https://v2.tauri.app/develop/sidecar/) guides support distribution, not proof
that this repository's payload already works.

```text
LocalBrain.app/Contents/Resources/terminal/runtime/
  manifest.json
  bin/node
  bin/localbrain-runtime
  manager/{manager,ownership,checkpoint,pty-input,colors,status}.cjs
  engine/node_modules/...
  licenses/...

<runtimeRoot>/
  scope.json, selection.json, identity.json, control.sock, control.lock
  leases/<payloadId>.lock              # content-free kernel use leases
  losses/<payloadId>.json              # unresolved-loss identity metadata only
  localbrain-terminal                 # stable management launcher
  payloads/<payloadId>/               # immutable verified copy of runtime tree
  staging/<unique-id>/                # task-owned preparation only
```

Manager executable, code, engine and helper resolve only inside the selected
immutable payload. Neither manager nor helper depends on a checkout, Homebrew,
user Node/npm/Python, `.app` path or PyInstaller interpreter mode after bootstrap.
Frontend xterm/font/CSS/guide assets remain separately bundled with the app's
served resources and provenance; changing CSS does not itself alter manager build.
D2Coding1.4.0 Regular/Bold/OFL and13px remain; no font download/OS installation.

### Versions, platform and provenance

- First bundle target: Node **24.15.0 darwin-arm64**, observed local ABI137/N-API10;
  node-pty1.1.0, xterm headless6.0.0, serialize0.14.0 and Unicode11 addon0.9.0 from
  the current runtime lock. Core/helper build uses FEAT-0167's Rust1.99.1/declared1.90.
- App minimum macOS14.0 and aarch64 are retained. Official Node24.15
  [platform/build matrix](https://github.com/nodejs/node/blob/v24.15.0/BUILDING.md)
  declares macOS arm64 minimum13.5; that alone is not a native-addon/package pass.
  Include the lock's Darwin spawn-helper assets and owner executable preparation;
  first acceptance exercises arm64 only, not Intel/Rosetta merely because an x64 file exists.
- Build from explicit public/locked ingredients, not a developer's populated runtime
  or arbitrary PATH Node. Verify the official release archive SHA256 and artifact
  provenance, then native addon ABI137/dylib/runtime paths and signatures. The
  release SHA download was not available through the research tool in this Run;
  no digest or verified tarball is invented. The builder must acquire/verify it
  before producing the actual payload.
- Preserve Node MIT/third-party notices, npm dependency license set, Rust dependency
  licenses, D2Coding OFL and generated manifests. Ad-hoc/local signing, quarantine
  and relocation checks are actual build gates. No paid key, notarization or Apple
  submission is authorized here.
- Development web can consume the same verified payload. A prior optional engine/
  Node20+ web installation stays a known legacy management target; no global Node
  upgrade or silent runtime replacement is performed. Protocol2 setup explicitly
  prepares the selected managed runtime, and any live incompatible version must be
  finished/stopped first. Setup is explicit/offline-bundled where available, never
  a network download caused by opening a page.

### Artifact manifest

Manifest schema1 is a closed object containing target triple, minimum OS, manager
protocol2, host protocol1, helper protocol1, checkpoint `xterm6-v3`, Unicode `11`,
the exact Node/core/engine versions, runtime-lock SHA256, build provenance and
`files:[{path,sha256,size,mode}]`. File paths are relative POSIX paths, unique and
sorted; no absolute/empty/`..` segment, traversal, link or unlisted executable.
Each SHA256 is64 lowercase hex, size a nonnegative integer and mode the octal
string `"0600"` or `"0700"` as appropriate. Version/minimum-OS values are strings,
protocol versions/sizes are integers; no floating-point manifest values.
Mode describes the installed private-runtime permission. Source `.app` resource
permissions may be ordinary readable/executable bundle modes; validate provenance/
bytes/path safety there and apply the manifest's private mode on the staged copy.
Do not reject a valid public bundle merely because it is not an owner-private cache.

`payloadId` and protocol2 manager `build` are the SHA256 of the UTF-8 compact,
recursively key-sorted manifest body **excluding payloadId**, with no final newline;
the files array is already path-sorted. `manifest.json` is the one special root
file excluded from its own `files` list; it is validated by the manifest-body hash,
not by a recursive self-file digest. Validate contents/file hashes/modes/versions
before trusting this ID. Runtime file bytes are final **after** signing; copying
retains those bytes/signatures. Font/browser/UI asset manifest is separate and
must still pass its own Unicode/checkpoint/client compatibility checks.

Actual file hashes, release archive digest and build revision are derived from
actual future artifacts; the contract fixes their calculation and required types,
not placeholder values that could pass validation. Unknown manifest/protocol or
wrong target/ABI returns setup/incompatible error, not a best-effort start.

### Atomic preparation and lazy start

1. Read/list/settings inspect source bundle/receipts without copying, network,
   manager start or shell creation. Report `bundleReady` separately from per-user
   `installed`; a verified source bundle can enable explicit New before cache exists.
2. Explicit New/Start/install acquires control.lock and rechecks current identity/
   generation. Live incompatible/unknown blocks new preparation/start for replacement.
   A positively dead/reused manager with unclean loss may be followed by a fresh
   explicit generation as current behavior allows. Before replacing its identity,
   retain minimal unresolved-loss metadata for the old payload (legacy build if no
   payload ID), without commands/VT or automatic adoption. That marker protects
   the predecessor from automatic retirement; starting fresh does not prove its
   old descendants ended.
3. Validate bundle and create owned staging directory under runtimeRoot; copy only
   listed public payload files, set/check permissions, hashes, target/ABI and paths.
   Verify actual executable/native dependencies cannot resolve back into `.app`/
   checkout/Homebrew. Do not copy credentials, personal cache or session content.
4. Flush and atomically rename the complete tree to payloads/payloadId on the same
   filesystem, then atomically write the scope/selection/management metadata.
   Existing identical verified payload is reusable; hash mismatch is failure,
   never overwrite an in-use payload or trust existence alone.
5. Bootstrap transient launchd job with absolute payload Node, manager entry,
   runtimeRoot and a validated helper descriptor. Only allow existing
   HOME/PATH/SHELL/LANG/LC_ALL/LC_CTYPE/ZDOTDIR/TMPDIR launch values; never app secrets.
   RunAtLoad=true, KeepAlive=false, stdout/stderr=/dev/null; no login/root agent.
   Remove the temporary private launch plist in finally. Interrupted inactive
   staging/plists are retired only under the same owner/control checks, not replayed.
6. Wait for matching socket/identity/generation/build before reporting ready. New
   then creates one visible shell using its fixed retry key/launch values; Start
   alone creates none. Failed prepare/bootstrap leaves explicit recovery and never
   claims an absent/partial payload is ready.

## Identity And Compatibility

Protocol2 identity is private JSON: `pid` integer>1, nonempty `born`≤128 characters,
`birthFormat="utc-lstart-v1"`, `generation`32 lowercase random hex, `version=2`,
`build=payloadId`, `scopeHash`64 hex, `helperProtocol=1`, `checkpointVersion="xterm6-v3"`,
`unicodeVersion="11"`. Manager status and receipt must agree on PID/generation/build/
scope; receipt-only PID is not liveness. PID birth mismatch/dead process may establish
unclean loss, not ownership of the reused PID. Failed inspection/legacy birth format
remains unknown and protected.

Current manager protocol1 uses its existing script/lock build hash, not payloadId.
The Core legacy management adapter understands only the explicitly verified1
status/list/stop/tab-stop/shutdown shapes and generation/expected-set semantics.
No new create/claim or protocol conversion against that live legacy payload.
If its old helper is unavailable, termination may fail; retain the record/error
and direct the user to the original compatible management/program controls.
Unsupported protocol or uncertain identity cannot be sent destructive guessed RPCs.

Same-compatible root joins the existing manager and its global32-record limit/single
input lease. Same-data/different-cache roots have distinct labels; same-cache/different-data
roots are separate. Prefix collision/full-hash mismatch rejects rather than adopting
or silently starting over. Explicit Stop always names its discovered scope, never
all installations or an unrelated `.app`/development process.

## Helper And Termination

Manager protocol2 replaces the Python-interpreter argument with a validated absolute
helper descriptor inside its own payload. Invocation is exactly
`<payload>/bin/localbrain-runtime process-snapshot`; no arbitrary executable/command
from a request. Host/Core and manager use this same implementation. The entry is
available without Python or the app, needs no DB/settings and never starts a manager.

It runs `/bin/ps -axo pid=,ppid=,pgid=,lstart=,stat=` with LC_ALL=C/TZ=UTC and resolves
session membership via POSIX getsid. Output is one UTF-8 JSON array and newline:

```json
[{"pid":200,"parent":100,"group":200,"session":200,"born":"Mon Nov 2 03:04:05 2026","dead":false}]
```

The example is synthetic; actual `born` uses the current single-space join of the
five ps time fields. Records contain no command/arguments/environment. PID>1,
parent/group integer, session integer or null, born nonempty C/UTC string, dead strict
boolean. Reproduce current helper semantics: skip short ps lines and disappeared
processes, session EPERM→null, malformed numeric data/other inspection error→failure.
`dead` is true for Z in stat. Never turn permission/timeout/parse failure into `[]`.

Retain ps deadline2s, outer helper3s and8MiB stdout cap. Drain/reap ps on timeout;
no idle polling helper. Concurrent cleanup shares one asynchronous inspection;
creation awaits an existing one then obtains a fresh post-spawn table, preventing
ownership from an inventory captured before the PTY existed.

Node retains its current ownership/signal logic: PID birth/group/session and optional
ownerParent must match; proven live ancestry/session may find descendants after shell
exit; when intentionally detached work loses both proofs, cleanup is not guaranteed.
Recheck exact process identities before each signal. Grace is TERM/HUP up to3s,
then KILL with2s confirmation; force skips grace, not ownership. Service shutdown
RPC12s then up to5s manager/socket exit confirmation remain. Unknown/partial exit
is error with retained records and retry/program controls, not success/killall.

## Lifetime Transition Table

| Event / predicate | Manager/jobs and view | Result / recovery |
| --- | --- | --- |
| Open Terminal/settings/list, no existing runtime | No start/copy/shell; inspect bundle capability | Empty/setup/recovery state, no hidden daemon |
| Explicit New or Split succeeds | Manager owns execution immediately; New visible/selected; Split uses clicked pane values within max4 | Fixed ID/key, max32 scope records including exited; no separate background promotion |
| Hide/Open tab | Change only manager's hidden flag and view attachment | Same tab/layout/IDs/process; not shell bg/fg or a new shell |
| Navigate, inactive/minimized/hidden view | Detach streams/cancel unsent input when hidden; manager continues | Return with supported live checkpoint and actual input rights; do not mark unseen output read just for selecting |
| Window close / last window / ordinary Cmd+Q | Host/backend/bridge children end or detach; no manager shutdown/bootout/payload cleanup | All visible and hidden work retained; Quit does not globally hide tabs |
| Forced app/backend death | Same independent manager; in-flight mutation may have uncertain response | Inspect actual state; reuse a create key only for same launch; no blind replay |
| Mac sleep, including after app Quit | OS may suspend CPU/network; LocalBrain does not terminate work | Wake/relaunch checks actual alive/exited/unknown, reconnects same surviving generation; no promise of continuous computation |
| Program exits or its network fails | Real job/shell state, possibly surviving owned descendants | Do not infer state from output silence or window visibility; retain supported exit/error state |
| Pane/tab × / explicit terminal or all stop | End exactly confirmed ID/tab/full target using current identity rules | Changed set/generation conflicts; stop failure retains record/error |
| Service stop/restart | End all scoped work, confirm then stop; restart starts empty manager only | No shell recreation/replay; does not touch other scopes |
| Empty manager, no records and no IPC | Current idle60s exit, KeepAlive disabled | Stopped; exited retained records prevent the empty predicate |
| Manager crash or dead/reused PID | Memory/layout/VT continuity lost, descendants may remain | Unclean/unknown shown; no empty-list proof, signal to reused PID or restored command |
| OS logout/shutdown/reboot | Old process continuity ends with OS session; no login agent | No previous process/VT/command/auto fresh-shell recovery; a new explicit Start/New is a new generation |
| Manual app update/rollback | Before replacement explicitly end affected work, verify manager/socket stopped | Then switch assets/payload/adapter; ordinary-Quit retention does not imply uninterrupted update |
| Drag app to Trash/remove source checkout | Stable cached manager/helper remain if already running | App-less management still available; no installer silently ends jobs or deletes the active payload |

Independent lifetime does not prevent a program/OS from ending work. Persisting
folder-group metadata after reboot is not decided here; current manager layouts
and VT remain memory-only. No transcript/search/Usage/provider Session inference.

## App-Less Management

The stable per-scope regular executable `runtimeRoot/localbrain-terminal` is a
small mode0700 POSIX launcher generated with properly quoted fixed absolute paths.
It only execs that selected payload's `localbrain-runtime terminal` mode plus the
same scope and user arguments. No JSON parser/Node/Python/jq dependency in the launcher;
no dynamic eval, unquoted path interpolation or shell-command parameter. Write/
replace it atomically only under control.lock while the target runtime is quiescent.

The launcher fixes `terminal --runtime-root <runtimeRoot>` internally, so its user
syntax is `"<runtimeRoot>/localbrain-terminal" list --json` or
`"<runtimeRoot>/localbrain-terminal" service stop --yes`. `lb terminal list` is the
equivalent existing Python-CLI spelling; do not require a duplicated terminal word.

The native management UI/guide must expose a copyable exact command/location when
implemented. After `.app` removal it remains in the known private terminal runtime
folder with scope.json, not in an automatic PATH modification/global service registry.
Default/custom scope and spaces/quotes/Unicode in paths are explicit test cases.

Grammar preserves existing `terminal list [--json]`, `stop ID|--all` and
`service install|status|start|stop|restart` flags/TTY confirmation/--yes/--force/JSON
stdout+error stderr/exit statuses. There is no run/attach/new terminal command added.
App-less install/start can use the existing verified cached payload; if missing,
report setup_required and require an explicit compatible app/build preparation,
not network install or an interpreter fallback. list/status/stop never need to
start a service. Existing `lb`/`localbrain` use the same Core protocol/meaning.

## Retention Update And Removal

- Any current/pending manager identity, unknown liveness, foreign active command/stream or
  matching launchd job protects its selected payload, helper, launcher and control
  metadata. Do not treat the terminal cache as generic disposable data while active.
- Existing storage cleanup uses internal `runtime.retire`: preview reads an already
  owned scope without creating paths/locks and returns a receipt containing full
  scopeHash, clean-stop predicate, selected payload ID and sorted candidate
  `{payloadId,manifestHash,treeHash}` entries. treeHash covers listed paths/bytes/modes
  and rejects unexpected files/links; no terminal content is read. A missing or
  unowned/corrupt lock/receipt in an existing runtime is unknown, not an empty safe
  candidate. A completely absent root reports no candidates without creating it.
  Receipt shape is exactly `{scopeHash,cleanStopped:true,selectedPayloadId,candidates}`;
  selectedPayloadId is64-hex or null and candidates is a sorted list of the three
  64-hex fields above. `manifestHash` covers actual manifest file bytes; treeHash
  covers compact sorted `{path,sha256,size,mode}` records including manifest.json.
  Preview does not delete or clear a loss marker. Loss-marked payloads are excluded
  with an explicit protected reason; no automatic marker-clear operation is added.
  Successful preview result is `{state:"stopped",receipt,protected}`; protected
  entries are `{payloadId,reason}` with reason unclean/in_use/unknown. An absent
  root returns `{state:"absent",receipt:null,protected:[]}`. Live/busy or unknown
  runtime returns the corresponding structured error without a deletion receipt.
- Apply must run from the app/development control executable **outside** any target
  retired tree. Under control.lock and exclusive per-payload use leases, recheck the
  exact `expectedReceipt` and unique `payloadIds` subset, clean stopped manager/socket/job and no foreign in-flight
  usage, then delete only selected verified inactive trees. Keep runtimeRoot and
  control.lock in place; never unlink the lock while using it. Retire a selected
  launcher/receipt only in that same transaction and leave explicit setup-required
  metadata. A command executing from that payload returns busy rather than deleting
  its own image. Changed state/tree returns conflict without deletion.
  Successful apply returns `{retired:payloadIds,scopeHash}`. Unknown fields/types
  are invalid; changed receipt/tree is conflict, in-use/control contention busy,
  owner/hash/path mismatch identity, failed inspection unavailable. Existing storage
  adapters keep their own public error shape and report protected terminal targets
  while allowing independently eligible cleanup, not a new terminal HTTP endpoint.
- A Python generic-storage transaction may already own operations.lock; the Rust
  retirement operation never reopens it and holds control/use locks through the
  actual terminal deletion. The Python caller must not check with Core, drop the
  guard, then recursively delete a runtime tree itself. Data/cache relocation
  requires stopped hosts/runtime and the existing storage-migration contract;
  terminal execution state is excluded from copying/automatic reconstitution.
- If busy/unknown, preserve and report. Backup/restore does not include/recreate
  terminal commands, VT, manager identity/socket/lock/scope/runtime execution.
- Installation can stage a different version without overwriting the selected one,
  but cannot switch/start it until the old manager/work is explicitly stopped and
  exit confirmed. Do not move/copy an active socket/identity into a new scope.
- Retire owned incomplete staging/temporary plist only when inactive. Retire old
  immutable payload/launcher only after no active/pending references and confirmed
  manager absence under the same lock. Missing/corrupt ownership receipt is a
  preservation/refusal state, not broad cache deletion.
- An unresolved-loss marker remains protected even after a fresh generation later
  stops cleanly. It retains only last identity/build and a per-payload unresolved
  flag, not an activity log or process restoration record. Resolving lost programs
  and deliberately retiring that evidence requires the user's program controls/
  explicit manual recovery; this slice never equates a new empty manager to their exit.
  Legacy predecessor markers use `losses/legacy-<build>.json` and protect legacy
  engine/evidence without pretending it is a protocol2 payload.
- Manual uninstall removes `.app` separately. To retire runtime/cache, use explicit
  same-scope stop/confirmation then authorized cleanup. If the executable/helper
  was externally removed, report uncertain owned descendants; do not claim stop or
  delete the remaining evidence. Retain the program's own management route.

## Implementation Handoff And Required Evidence

| Target / existing consumer | Required later implementation and witness |
| --- | --- |
| runtime.py/Core + manager.cjs helper argument | Protocol2 payload/helper/identity; actual spawn with source app renamed/unavailable after bootstrap; existing v1 management retained |
| desktop host/desktop.py/app assembly/backend.spec/build-desktop.py | Select only Terminal assets/routes/settings/guide; ordinary host Quit never stops manager; exact resource/native paths and real package first-New offline without user runtimes |
| Node/PTY/headless/font/license manifests | Actual release/lock/file hashes, ABI137, both helper readiness assets, arm64 native load, signatures/quarantine/dylib relocation; no claim from merely bundling files |
| app access foundation | Per-launch HTTP/WS admission/origin/CSP/least native permissions before any terminal runtime command; not satisfied by this lifetime contract |
| settings/storage/CLI/docs consumers | Common writer unchanged, runtime active/unknown cleanup guard, correct app-less/legacy manager status/stop and no PATH/rc edits |
| actual OS/app/browser | Real packaged Cmd+Q/backend death/sleep/wake/update/mismatch/reconnect, physical Korean IME/shortcuts/clipboard/accessibility and approved resource budgets, separate from synthetic events |

Contract acceptance covers explicit owner/shape/transition/failure rules. Actual
executables, offline app, liveness retention, native performance/IME and recipient/
long-soak evidence are mandatory later product gates and **not proved** by this Run.
No blocking ownership/lifetime/payload/helper/management choice remains in this contract.

## First Runtime Implementation Details

Run251 uses one fixed `payload-lease` helper mode: require the cached executable's
existing shared lease, emit bounded `ready` plus newline, and hold it until the
manager-owned stdin pipe closes. No shell input/content enters this pipe. A lost
lease helper makes protocol2 `leaseHeld` false and new work incompatible; it does
not terminate jobs. Ordinary control/stream commands also hold payload use leases.
The stable launcher unsets obsolete app bundle/runtime environment overrides and
executes its absolute cached helper. Polling verifies manifest/tree metadata;
full file bytes are checked before preparation/execution and retirement. Retirement
treeHash records are path-sorted with recursively key-sorted compact JSON, including
manifest.json. Parent-directory links are rejected throughout private payload,
lease, receipt and lock paths; leases from another scope never authorize deletion.

The selected implementation and actual observations are now recorded in
[Eval0167](../evaluation/eval-0167-rust-terminal-runtime.md) and
[Eval0168](../evaluation/eval-0168-native-terminal-integration.md). The earlier
contract-only acceptance above remains historical. At Run252, final package and
native-host checks passed while a locked Mac blocked the required window packet.
[Run253/Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md) later
closed that particular window gap. Feature177's subsequently changed UI has its
own still-pending window gate in [Eval0174](../evaluation/eval-0174-terminal-activity-and-background-rail.md).
Physical input/sleep and recipient/performance limits remain separately retained.
