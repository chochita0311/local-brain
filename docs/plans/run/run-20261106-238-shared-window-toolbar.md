# Run238: Shared Window Toolbar

## Metadata

- ID: `run-20261106-238`
- Status: `passed`
- Feature: [FEAT-0162](../feature/feat-0162-shared-window-toolbar.md)
- Active Spec: [SPEC-0162](../spec/spec-0162-shared-window-toolbar.md)
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Attempt: `1`
- Created: `2026-11-06`

## Boundary And Evidence Plan

Native-window/shared-header, web navigation, sidebar state and search/Docs lanes.
Screen-alignment extend and clean-code responsibility boundaries. Dirty baseline
and manifests captured before this task; previous source/build changes preserved.
No backend/data contract change. Native overlay API is verified against installed
Tauri2.12.4/Tao0.37.1 and official window-customization documentation.
One fresh non-editing/non-executing named omission challenge is allocated after
freezing source; later passes only for material repair evidence. No hard user
resource budget. Runtime and foreground-native evidence remain separate.

Reuse recorded lessons: test pending and settled view readiness, source/frozen
identity and canonical-path delivery; distinguish fixture scheduling from product
behavior. Preserve initial reviewer return and adjudicate with actual witnesses.
Temporary builds stay task-owned; only normal dist is a final deliverable.

## Implementation And Review

One shared DOM toolbar occupies the macOS overlay titlebar and the browser page
header. Native traffic lights retain their OS ownership; only start-dragging was
added to the existing capability. Host-only initialization selects native layout,
including a startup/recovery drag strip. Navigation owns both retained directions;
shell presentation owns sidebar session metadata and platform shortcuts. Search
keeps its GET form/mode/IME rules. Both first-use guides and canonical navigation,
desktop, privacy and design owners were updated.

The fresh named static challenger inspected the frozen pre-task dirty baseline
and all23 initial changed paths. C1 (custom Atlassian modal shortcut escape) and
C2 (Alt arrows consumed by focused view controls) were supported by actual
before/after witnesses. The shell now recognizes custom modal/inert ownership and
captures only recognized window shortcuts before view handlers. Plain arrows
retain their local action. One focused six-file repair review found no concrete
residual in that delta. Workflow shares the inspected protection; it has no
separate runtime witness. Reviewer never executed, edited, delegated or accepted
the work; primary owns final integration and judgment. Initial and informed
returns, complete frozen manifests/trees and witnesses remain private evidence.

## Evaluation

| Evaluator | Result and scope |
| --- | --- |
| Contract | PASS: retained latest50 history/back/forward branching, unchanged URL/view state ownership, bounded sidebar session metadata, actual shortcut hints and modal isolation; no DB/API/source/model change. |
| Design | PASS within measured host layouts: native640/700/920/1440 and web320/700/920/1440 containment, OS-control inset, one header/body boundary and collapsed rail. Wide/native minimum/web narrow screenshots inspected; physical OS controls remain unverified. |
| Functional | PASS: Python1,534; toolbar50; chronological navigation46; trial94; common web UI70. Both reviewer witnesses fail before and pass after repair. Storage denial, shell asset failure, IME, modal focus and optional web search scope are covered. |
| UX heuristic | PASS within automated scope: disabled directions retain position, hidden rail loses tab stops/focus, sidebar persists across visits/reload/BFCache, search/tooltip shortcuts remain discoverable. |
| Packaging/host | PASS within stated scope: original frozen backend21 checks at staging and again at canonical path;11 source-identical assets,5 shared headers,3 excluded desktop routes and2 guide languages. Actual packaged Tauri executable with a synthetic fixture backend observes host marker, read-only native version IPC,58px header/body boundary,96px sidebar-button inset, collapse and search focus. |

Actual-host evidence uses the production Tauri code in a private copy with a
synthetic backend and passive observer. That copy was ad-hoc re-signed: all
file-backed Mach-O sections match the canonical executable, while whole-file
signature digests differ. Original production frozen backend checks are separate
and unmodified. The browser native-layout simulation
and installed-SDK command-dispatch mock do not prove physical window movement.
AX/screen/event permissions were unavailable and were not changed. Physical drag,
double-click, native traffic-light hit regions/minimize/resize and startup/recovery
interaction remain a human check; normal Quit and canonical relaunch did run.
No actual Windows environment, recipient acceptance or public notarization claim.

Two private bundle-probe oracle errors were corrected: the first guide is /help,
and displayed Mac shortcuts use the ⌘ symbol. No product repair was made for them.
The final21 checks passed; transient failed probes remain classified in evidence.

## Canonical Delivery

- App: `dist/LocalBrain-apple-silicon/LocalBrain.app`; ZIP/checksum retain normal owners.
- Version0.0.1, dirty HEAD52a99d87fbce8ee0c1162f03b534d946b397ce00.
- Built UTC2026-11-06T05:23:24.225179+00:00;372 build inputs.
- Input SHA256: `49ae07716d49fe79f52b0ab0036ec9a3eca0602417849eade54cd469f2534a54`.
- ZIP SHA256: `dbf4c971c4e0bdb5709139f3750432b90a9cdfdc8ee9da154b65ecc3525fe5c2`.

The old app was normally Quit for the isolated host check. With all app/backend
processes absent, verified outputs replaced the original paths using the existing
backup/rollback publisher. Source identity, deep signature and ZIP digest were
verified before/after publication. Canonical-path native/backend were relaunched;
the isolated canonical frozen check also passed. No forced user-app termination,
settings/data reset, source registration, model install, commit or push.

## Closing Checks

Privacy1,789 candidates, whitespace, generated artifact catalog and32 local owner
links pass. Final source/build-input identity matches the canonical BUILD-INFO.
All15 file-backed native sections match the private re-signed host copy. Before
cleanup no task process remained; task-owned temporary apps, synthetic profiles,
runtime data, Swift cache, staging outputs and pointer were removed. Normal
canonical app/backend remain running; configured build caches are preserved.
Private frozen reports/manifests/receipts survive only under their declared
ignored evidence owner. No tracked evidence or publication was introduced.

## Sidebar And Tooltip Follow-up — 2026-11-06

Owner requested the collapse control beside the brand, a compact icon rail, Google
icons replacing numbers/Docs question mark, and stable hover/focus hints with
separate shortcut keys. This replaces the prior hidden-rail rule. Frontend profile,
shared shell/tooltip lanes, screen-alignment extend. Preserve navigation/search,
modal ownership, storage scope and existing dirty work. No History/data/API/native
capability or dependency change. Bundle official SVGs/license for offline use.
One bounded fresh static challenge covers shared tooltip/focus lifecycle; primary
owns all edits, runtime validation and acceptance. Rebuild the normal canonical
app; existing native physical/Windows/recipient evidence limits remain.

### Sidebar Follow-up Evaluation And Delivery

PASS within the recorded automated scope. Compact64px rail retains real menu
links, active state, home, expand, Docs and Settings. The brand-right toggle stays
outside the home link. Official Google Material Symbols Outlined replaces numeric
marks and Docs ?.14 paths are combined locally with unchanged source paths and
Apache2 license, pinned at10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7.
No external font/network dependency or new package is required at runtime.

Tooltips use one body-owned, control-anchored surface; mouse motion inside a
control cannot move it. Action text and individual keycaps replace parentheses.
Delayed hover, keyboard focus, Escape, entry into help, peer changes, modal/inert
isolation, resize/blur/pagehide and viewport containment are covered. Tab-generated
menu scrolling reanchors keyboard help; explicit wheel/key movement dismisses it.

| Evaluator | Follow-up result/evidence |
| --- | --- |
| Contract | PASS: same route gates, search GET/mode/IME, history/state ownership and session metadata; no backend/schema/native capability change. |
| Design | PASS: expanded/compact1440/920/700/320 web and native640/700/920/1440 layouts, actual painted SVG geometry, brand/toggle separation, keycap clarity and stable tooltip coordinates; selected screenshots inspected. |
| Functional | PASS: Python1,534; final toolbar85, navigation46 and trial94. Focused short-window16 and composing-event before/after witnesses discriminate repairs. |
| UX heuristic | PASS within tested hosts: every compact menu is reachable, active state remains, tooltip can be read by pointer/focus and dismissed;640×480 footer and offscreen-Tab reachability verified. |
| Original package | PASS:24 original frozen checks at staging and canonical paths:14 source-identical assets,5 headers,3 exclusions and2 guide languages. |
| Actual Mac host | PASS within DOM/IPC scope: real Tauri code with synthetic fixture backend observes Google SVG geometry, brand toggle,64px rail/main inset, titlebar Back inset, live read-only IPC, tooltip keys and composing-event routing. Private host copy was ad-hoc re-signed;15 file-backed sections match canonical code. |

One fresh static challenge plus one informed repair pass were retained privately;
reviewer executed/edited nothing and did not accept completion. Its C1 composing
Escape candidate was supported for event routing (prevented/input receipt changed
true/false to false/true) and fixed. Primary-origin cases also fixed: native narrow
rail top116/bottom538 becomes58/480, footer522 becomes464; offscreen Workstreams
Tab at scroll5 changes missing hint to visible. Final focused review found no
concrete residual in that five-file repair. OS Korean IME cancellation remains
unobserved; programmatic composing-key routing is the actual evidence. Physical
OS drag/buttons/resize, actual Windows and recipient acceptance remain separate.

Visual inspection caught an SVG symbol/outer viewport mismatch before delivery;
visible-glyph bounds are now tested. Old tests bound to numeric labels/attribute
order were corrected while preserving their navigation-order/search assertions.
An initial Python run lacked sandbox loopback permission; full1,534 passed with
that permission. A build retry loaded installed Cargo; the next candidate was
correctly rejected when inputs changed during packaging. Final clean-input build
and signatures/digests passed. No dependency/toolchain migration was introduced.

Latest canonical app/ZIP/checksum retain normal dist owners and were normally
replaced/relaunched after isolated host Quit. Version0.0.1; dirty HEAD unchanged.
Built UTC2026-11-06T06:03:31.533479+00:00;376 inputs.
Input SHA256: f34d28298ce6863ce68d0e0d98aad4e1183abfdb7081e32b48f67aad002d943f.
ZIP SHA256:8432b4502a143755e6919769b58092ddef98200a79953cddc5b41e12255dcb99.
Privacy1,793, whitespace and generated catalog checks pass. No commit/push or user
source/model operation. Prior source/native episodes remain historical.

Follow-up closing: final source identity, whitespace/catalog, seven local owner
links and private Git exclusion pass. Frozen review/repair trees rehash exactly.
After zero active task processes, owned temporary apps/profiles/runtime/cache,
staging/superseded outputs and pointer were removed. Canonical app/backend remain
running; ordinary configured build caches and all unrelated dirty work are kept.

## Header Hint Geometry Follow-up — 2026-11-06

Owner reports dark hints remaining at the upper-left for Back/Forward/query/Search
and removes the footer’s Local index online / Private on this Mac statements.
Prior actual-host checks asserted visibility/keys, not all four hint coordinates;
that evidence does not establish the reported behavior was absent. Frontend
shared-shell lane, screen-alignment extend. Reproduce with the delivered host and
original frozen assets; distinguish original backend from fixture instrumentation.
Current tool lacks native mouse/screen/AX access; record DOM-event/native-WebKit
checks separately from physical hovering and ChatGPT comparison. Local tooltip
measurement/display repair preserves all existing ownership/IME/modal contracts;
no new architecture/capability/data change warrants another fresh static review.

### Header Hint Follow-up Result

PASS within the recorded scope. Owner’s final correction removes query/Search
hover hints, keeps the visible Cmd/Ctrl+K badge, and replaces disabled-direction
explanations with a not-allowed cursor and no popup. Enabled directions retain
short action/keycap hints. Footer status/privacy slogans and unused local-status
styles were removed; the Run console’s shared status-dot consumer remains.

The original frozen backend and production Tauri code reproduced the reported
origin failure with a two-second CSS response delay. At controller initialization
its cached gap/delay were NaN and the raw property was empty. Once CSS loaded,
raw gap became8px while query/Search hints remained at0,0. The earlier fixture
host did not expose this because its stylesheet had already loaded.

The controller now reads timing on demand, gates on its fixed-position stylesheet,
measures resolved pixel padding invisibly, validates geometry and locks its width
inside the scrollbar-free layout viewport before becoming visible. Window load
resumes the current hover/focus owner. Search’s former edge wrapping was also
caused by measuring against innerWidth including the scrollbar.

| Evaluator | Follow-up scope/result |
| --- | --- |
| Contract | PASS: approved hint/cursor/footer changes; search GET/IME/shortcuts, history50/state, modal isolation and collapsed navigation retained; no API/DB/native capability/dependency change. |
| Design | PASS: enabled Back/Forward screenshots inspected, names/keycaps remain distinct, footer clean, disabled not-allowed styling and search hint absence verified. |
| Functional | PASS: Python1,534 and browser92; runtime origin-measurement guard, both enabled directions, four suppressed states, focus/IME/modal/storage and narrow-window paths. |
| Native/package | PASS within DOM scope: actual Tauri/WebKit with original frozen backend, loopback proxy/delayed CSS and a probe appendix. Early hint stays hidden; load resumes it. Initial disabled Back/Forward and query/Search show none; disabled cursor computes not-allowed. Enabled Back/Forward appear at y52.5 below anchors ending44.5, remain stable, and expose no origin measurement. Original uninstrumented assets/headers/gates/guides24 pass at staging and canonical paths. |

Native probe app is a private ad-hoc re-signed copy;15 file-backed native sections
match canonical code. Probe appends observer code to one served controller asset;
original backend and other assets remain unchanged. Uninstrumented package hashes
are checked separately. A private proxy path mistake was corrected; a BrokenPipe
on a response after the probe’s normal Quit is client teardown, not a UI failure.
Actual OS mouse events/screen capture/AX were unavailable and not enabled. DOM
pointer events in real WebKit are the evidence; no claim of physical hovering or
a direct ChatGPT app comparison. Prior broad visibility checks did not establish
all four coordinates and are not presented as such. No additional fresh review
was allocated for this localized measurement/eligibility repair.

Normal canonical app/ZIP/checksum were replaced and the app/backend relaunched.
Version0.0.1; dirty HEAD unchanged;376 inputs. Built UTC2026-11-06T06:36:02.107678+00:00.
Input SHA256:4fc7f580de92fb17c0ba2c5d441d67405cbf37ddb240a4ec74b80955f2511386.
ZIP SHA256:d443d2a045536fcda1c27710bc0c04e5f5edb162549634d65a94dd0f85442cd0.
Privacy1,793, whitespace and artifact catalog pass. No source/model registration,
reset, commit, push or public release action.

Header follow-up closing: source identity, signature/ZIP, privacy1,793,
whitespace/catalog and evidence exclusion passed. Exact owned scratch/profiles,
proxy runtime, temporary apps, Swift cache and pointer were removed after no
task process remained. Normal canonical app/backend remain running; ordinary
configured build caches and previous dirty work/evidence were preserved.

## Disabled Direction Hint Correction — 2026-11-06

Owner clarified that disabled Back/Forward retain their short action/keycap hover
hints; only no-screen explanatory copy is removed. Keep the forbidden cursor,
disabled activation, no search hints and footer removal. Frontend/shared shell,
screen-alignment extend; this supersedes the prior popup suppression. A normal
wrapper receives hover when WebKit suppresses events on disabled buttons. Tooltip
eligibility is explicitly opted in at those two controls. Reuse focused behavior
and native delayed-CSS checks, rebuild/publish the canonical app; no new API,
History/data/native-capability change or fresh-review allocation.

Correction evaluation: Python1,534 and browser97 pass. Real disabled hit targets
remain wrappers with not-allowed cursor, show exactly 뒤로/앞으로 and platform
keycaps, and remain non-actionable. The installed Tauri2.12.4 drag script confirms
explicit data-tauri-drag-region=false blocks native drag through those wrappers;
its mocked-dispatch browser scenario passes. Original frozen backend plus private
re-signed Tauri host/probe appendix under delayed CSS also passes disabled/enabled
hints, two absent search hints, geometry and invisible-origin measurement checks.
Normal DOM hit testing returns SPAN for both disabled controls, with correct
cursor; labels appear below anchors ending44.5 at y52.5.

Native probe setup initially targeted internal SVG nodes, then encountered window
blur and a focused skip-link overlay; those are retained as interrupted/oracle
evidence, not product defects. Controlled app activation, normal control surfaces
and clearing that keyboard-only overlay yield the matching pass. Physical OS
mouse/screen/ChatGPT comparison remains unobserved. No production repair beyond
the requested disabled-hover opt-in and wrapper was made for probe setup.

Canonical correction delivery: normal dist app/ZIP/checksum replaced and app
restarted. Version0.0.1, dirty HEAD unchanged,376 inputs. Built UTC
2026-11-06T06:54:47.226799+00:00.
Input SHA256:fec1acd43d3ffe2eaa48e6434103b138d7e50d2b42d3107c890a95a1c3e29bb2.
ZIP SHA256:4333b49ca6ac9b9fb8fe4d08946497ca3918810f003a8622991d3fc29d176348.
Original uninstrumented frozen24 checks pass at staging and canonical paths;15
file-backed native sections match the re-signed probe copy. Privacy1,793 and
whitespace/catalog pass. No commit/push, original source registration or model
operation. The retained native pass uses DOM events/hit tests, not OS mouse input.

Disabled-hint closing: canonical source fingerprint/signature/checksum,
privacy1,793, whitespace/catalog and private exclusion pass. Owned test
apps/profiles/proxy/cache/staging/pointer were removed after no task process
remained. Normal app/backend remain running; ordinary caches and previous
dirty work/private evidence are preserved.

## Session Closeout Repair And Delivery — 2026-11-06

The requested preset1 closeout reviewed the complete session-owned change set,
with independent docs-structuring and docs-shaping discovery and a fresh code
omission challenge. Later repair confirmations were informed. The owner explicitly
approved major temporal reconciliation of PRD0027 and early-access readiness;
initial proposals, failure observations, all build identities and acceptance limits
remain historical evidence. Current definitions stay with policies/app guides;
this Run and Eval0155 retain delivery evidence, and Plans Index only routes to it.

Two reproduced defects were fixed within the existing Chart/history contract:

- When database visibility preferences were unavailable, replacing scope state with
  an entry camera discarded its hidden-project fallback. Capture scope visibility
  independently; authoritative database[] still wins, failed reads keep their
  warning, and restoring the fallback never issues an automatic preference PUT.
- A one-second unlock allowed another Back during a slow document traversal and
  could skip the retained target. Keep one requested marker pending until actual
  entry/reentry or matching observable cancellation. A partial view/hash update
  can abort an optional API signal while the document still loads; it cannot
  release that request. Hosts without a usable signal, or with ambiguous changes,
  recover through full-document navigation/reload, not a partial view switch.

Synthetic before/after controls reproduce both failures and their repairs. The
permanent navigation regression seeds a genuinely nonempty incoming fallback
and checks the actual server[] positive control after outgoing pagehide. It holds
a real response while outgoing timers run, applies a Projects partial update,
and observes exactly one native Back beyond1.3s and the retained Help destination.
An additional native-Forward browser control cancelled the actual held request;
its output omits hashes, so it does not verify the exact retained fragment.
Chrome with its optional API shadowed is a fallback-path fixture, not an older
Mac or Windows environment. No API/schema/model/provider-write change was added.

Final source verification: Python1,534 passes; navigation54, window toolbar94,
trial delivery94 and UI-state70 browser assertions pass with zero Runtime
exceptions. The shared regression batch matched all1,793 frozen repaired candidate files
before this Run/Index status update; runtime/test/build inputs stayed unchanged.
These counts are new observations, not relabelled
prior97/46 results. Privacy1,793, whitespace, plan catalog and generated schema
presentation checks pass. Scope/camera, pending/target and fallback owner docs
match the code. Rendered synthetic Chart before/after retained the established
screen design while restoring the intended hidden Project.

The rebuilt original frozen backend passes24 asset/header/gate/guide checks at
both staging and canonical paths. Actual production Tauri/WebKit in private
ad-hoc re-signed copies also confirms:

- All six disabled/enabled Back/Forward and query/Search states; disabled wrappers
  retain action/keycaps and not-allowed hit cursors on disabled controls. Browser
  activation checks establish their non-actionability. Search
  hints stay absent. Delayed CSS keeps early help hidden; settled help is below
  its anchor at y52.5, stable during movement, with zero exposed origin geometry.
- Scope visibility survives the unavailable-preference/entry-camera path with a
  visible warning and no automatic PUT. WebKit actually restores the retained
  Help document from BFcache and releases the pending guard on document reentry.
  It bypasses the delayed server request, so the slow-document serialization
  claim above remains Chrome-scoped rather than a native delay observation.

Both native copies retain15 identical file-backed executable sections compared
with the canonical source app; replacing their backend launcher/proxy observer
and re-signing changes whole-bundle hashes. The proxy uses the original frozen
backend with owned synthetic offline data, a preference-read failure projection,
and observer appendix. Original uninstrumented asset parity is checked separately.
Early native attempts had no receipt until the exact probe application was
activated; another observer expected a new document rather than WebKit's actual
BFcache pageshow. Those are setup/oracle limits, not additional product defects.
No physical mouse/OS IME/screen capture/AX access or direct ChatGPT comparison was
performed. Human/recipient, older-minimum-macOS, Windows port/build/install/optional
AI and public signing/notarization acceptance remain separate and unverified.

Canonical app, archive and checksum were replaced after normal Quit, verified,
and the canonical app/backend relaunched. Version0.0.1; build-time source commit
52a99d87fbce8ee0c1162f03b534d946b397ce00, dirty:true;376 inputs. This is a truthful
pre-commit build identity; later source publication is separate, and its matching
input fingerprint is checked independently.
Built UTC2026-11-06T10:39:43.871705+00:00.
Input SHA256:e36c2eb7058bb2478242c8ab2002c9ebc5119f3161055014aff2ae332509fdf5.
ZIP SHA256:f0ae8470bd6e189186d9f8fef6d11ea75bf1e962a3fad689ffb39ef612983c80.
Signing remains ad-hoc; notarization/public binary publication was not requested.
No personal source registration, model preparation/download or runtime reset was
performed. Common-source and product Git publication receipts remain separate
from these runtime acceptance results.
