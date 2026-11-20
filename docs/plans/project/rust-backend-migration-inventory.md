# Rust Backend Migration Inventory

## Current Implementation And Retirement — 2026-11-19

The selected target is a Python-free backend with `apps/api`, `apps/web`,
`apps/desktop` and shared `crates/`. Native HTTP/WS, CLI, rendering, settings,
persistence, ingestion, retrieval, jobs and model execution are integrated.
The former `src/localbrain` backend, Python wheel metadata/hook, PyInstaller
entry/recipe and one-operation common-runtime builder have been retired locally.
[Run261](../run/run-20261118-261-python-free-backend.md) passes
[Eval0177](../evaluation/eval-0177-python-free-backend.md) for the native
implementation, retirement and tested delivered runtime. That evaluation owns
whole-candidate challenge, actual artifacts, minimum Rust, regression/performance
and evidence limits; this map alone is not their pass receipt. Historical source/test locators below refer to the
frozen Python baseline, not current executable paths.

| Family | Current implementation owner | Verification owner |
| --- | --- | --- |
| F01 Preferences/files | `crates/core/src/preferences/`, backend preferences/storage/unicode; native API settings | Native preferences, Terminal, HTTP and frozen codec/parameter suites |
| F02 Persistence/recovery | backend `db.rs`, `storage/`, compiled schema resources | Native storage/contracts/resources/schema suites |
| F03 Registry/scheduling | backend `sources/`, `ingest/sync_service.rs` | Native storage/source and ingestion sync suites |
| F04 Ingestion | backend `ingest/`, shared JSON/UCD14, native Context scan | Frozen provider DTOs, source scans, retention/observer and JSON edge suites |
| F05 Session reading | backend `sessions/`; API Sessions/Projects | Native Sessions/clock and HTTP/browser suites |
| F06 Usage | backend `usage/` and Sessions Dashboard | Full frozen pricing/selection/timestamp projections and native HTTP |
| F07 Local Context | backend `contexts/`, rendering/references; API Documents | Native Context file/Notes/timestamps/HTML/HTTP suites |
| F08 Shared resources | backend `references/`, `resources/` | Native URL/IDNA/catalog/resource/related-reading suites |
| F09 Retrieval | backend `search/`; API search/CLI | Native eligibility/index/retrieval and frozen legacy search suites |
| F10 Models | `crates/models`; backend model setup; API CLI/download worker | Native asset/tokenizer/generation contracts and bounded cached0.6B CPU/Metal evidence |
| F11 Host/rendering/Docs | `apps/api`; `apps/web`; shared native Markdown/YAML/highlighting | Native host/auth/CLI/HTTP, frozen rendering and actual Chrome suites |
| F12 Learning | backend `learning/`; API learning/dashboard/CLI | Frozen/native learning behavior and HTML suites |
| F13 Work organization/tasks | backend `workstreams/`, `maintenance/`; API routes | Frozen Workstream projections and real owned synthetic child/cancel/rollback suites |
| F14 Insights | backend `insights/`; API Insights and host lifecycle | Frozen evidence/guidance/presentation/accounting plus synthetic process suites |
| F15 Workflow/Auto Work | backend `workflow/`, `auto_work/`; API routes and simulation CLI | Frozen projections/assertions/corrections, native simulation/affinity/preview and HTTP suites |
| F16 Atlassian | backend `atlassian/`; API Atlassian controllers | Frozen catalog/evidence/registration/refresh/browse and actual HTTP suites |
| F17 Terminal | shared core/runtime, independent Node engine; API transports; Tauri shell | Rust/Node contracts, native host, browser and separately packaged Terminal checks |
| F18 Developer tools and retired experiments | Native simulation/model-registration CLI and current standard-library build/check tools; obsolete Python research/reference/benchmark closure retired | Native simulation/model suites and current build/check tests; former research procedures are historical records, not current executables |
| F19 Suspended Context Search | backend `context_search/`; explicit API composition and owned worker | Native synthetic tools/answer/service/cancellation suites; default suspension retained |
| F20 Suspended Google Drive | backend `google_drive/`; explicit API composition | Native synthetic API/auth/transport/journal/job suites; default suspension retained |

Python build/check orchestration is outside the delivered runtime. At the user's
subsequent cleanup direction, the Python research/reference engine, historical
search benchmarks, compatibility launchers and their dependent tests are retired.
Current product tests invoke native executables without Python. The
[retired-procedure record](../research/retired-python-research-tools.md) retains
the former methods and limits; it provides no runnable fallback or new trial
approval. Native simulation/model-registration commands remain available. Existing
private source/output guards and feature suspensions remain in force. No real
user corpus, remote runner, credential flow or model download was started for
this cleanup. The original migration's retained-research counts below describe
their dated snapshot, not current source ownership.

## Historical Planning Status And Evidence Boundary

Current final target, clarified on2026-11-18: the backend must run and ship
without Python. The [runtime exit conditions and approved apps layout](python-free-backend-target.md)
include host/rendering, syntax/zone and optional model execution. Earlier Python
retention below describes the dated baseline or an intermediate step, not a
permanent exception. The later user-approved full implementation is tracked by Run261 and the
current family table above; the ordering below is historical.

Phase3 planning input for [REFACTOR-0006](../refactoring/refactor-0006-rust-core-transition.md)
under [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md), observed
2026-11-17 at clean source `e6958df0813b8652074c68a73ac61a8b551e59a8`.
This inventory proposes sequencing; the [core/host contract](rust-core-and-host-contract.md)
and current policies still own accepted behavior. No Phase3 port or parity pass
is delivered by this planning snapshot.

Later 2026-11-17 execution: the user approved FEAT-0178 and
[Run259/Eval0175](../evaluation/eval-0175-rust-common-settings-cutover-contract.md)
passes the [common-settings contract](rust-common-settings-cutover-contract.md).
[Product FEAT-0179](../feature/feat-0179-rust-common-settings-runtime.md) subsequently
received implementation approval on2026-11-18 and passes
[Run260/Eval0176](../evaluation/eval-0176-rust-common-settings-runtime.md).
That Run owns actual Rust rules/normal commit and source/wheel/native settings
evidence, explicitly retaining Python syntax/OS-zone adapters. The census,
family/consumer descriptions and generic-Python-transaction wording below remain
the dated pre-cutover planning baseline rather than a new runtime inventory.

The source census covers all 246 Python modules, in 25 feature/support packages
plus the four package-root modules; the table below accounts for all 26 groups.
Static inspection found 128 explicit HTTP/WebSocket registration expressions in
nine files, including conditional, legacy and suspended registrations. This is
an inventory count, not the number of routes offered by either running edition.
The route appendix, CLI/lifecycle map and delivery inputs identify consumers;
they do not replace each later slice's full query/write/failure audit.

Terminal control already uses Rust. Its Python HTTP/WS/CLI adapters, generic TOML
transaction and workspace/presentation/shell integration remain. Latest Terminal
UI [FEAT-0177](../feature/feat-0177-terminal-activity-and-background-rail.md) retains
its actual-window acceptance gate; beginning Phase3 neither closes nor blocks on
that separately owned UI packet.

## Admission And Migration Disposition

- Common app/development-web flows: Sessions, Projects, Sessions Dashboard,
  Local Context, keyword/optional semantic search, settings/onboarding and Docs;
  Terminal is admitted on macOS with its existing installation/access checks.
- Development-web gaps to inventory for later app admission: reviewed learning,
  Workstreams/Threads/checkpoints/Suggestions, Insights, Session workflow,
  Auto Work, Atlassian, Sources/scan, Schema and local-resource detail. Root `/`
  redirects to the saved common surface when desktop onboarding is complete,
  otherwise to onboarding; it is the learning dashboard in development web.
  A backend port alone does not admit these native routes.
  Their eventual admitted-function parity obligation remains with PRD-0029.
- [Context Search and Google Drive](feature-availability.md) remain suspended in
  default web/app. Preserve code/tests, registrations, public model assets,
  Drive credentials/copies/jobs and data; do not start workers/sync or delete state.
  Explicit synthetic composition is not a user feature toggle.
- Workflow/reconstruction/claims experiments retain their paused, blocked or
  one-time trial boundaries in the [Plans Index](../README.md#execution-state).
  Inventorying their code authorizes no extraction, private corpus or new trial.
- Current source/web instructions and native delivery target macOS; the Rust
  terminal payload targets Apple Silicon/macOS14. Windows/Intel/Linux delivery
  remains separately proposed/unverified, without a new support or retirement
  decision. No UI, model, database or terminal-engine replacement is selected.

Assembly and authentication are distinct checks:
`src/localbrain/app/features.py` (features.py) selects packages,
`src/localbrain/app/application.py` (application.py) installs routes and
services, and `src/localbrain/app/edition.py` (edition.py) applies native
loopback/token/origin/path admission. A permissive path pattern alone does not
install a suspended package. Optional reference observers and cache handlers
follow assembly, including CLI scans.

## Source-To-Target Family Map

`Retained` below means current Python owner, pending a separately approved Rust
slice. Proposed targets describe responsibility, not implemented Rust modules.
Common SQL/FTS, IDs, revisions, null/error meaning and transaction boundaries
must be inherited from each linked owner, not reconstructed from table labels.

| Family | Entry → existing rules/store → outputs and consumers | Proposed boundary and preservation evidence |
| --- | --- | --- |
| F01 Common preferences and file/lock primitives | Settings/onboarding/startup and terminal defaults → `foundation/preferences.py`, `operations.py`, config/paths/files → settings APIs, templates, schedules, Dashboard time zone, native startup; raw TOML remains private | First proposed contract below; one common transaction, independent of Terminal assembly. Source registry/search/model/Context stores remain separate. Preserve [common settings](../../policies/project/desktop-app-and-settings.md#common-settings-contract) and [storage](../../policies/project/installation-and-storage.md#storage-ownership-and-configuration). |
| F02 Persistence, schema and recovery | startup / `init` / storage APIs and CLI → `persistence/db.py`, `bootstrap.py`, migrations, schema, `app/storage/` → every SQL consumer, backups/restore/cache/layout and packaged Schema presentation | Separate connection/bootstrap and recovery contracts before data-writing ports. Keep preflight/copy/schema/migration/commit/retirement order, FK/FTS, WAL, data/cache/weights ownership, restart-only restore and lease/lock. All historical tables survive excluded features. [Data Model](../../policies/project/data-model.md), [storage](../../policies/project/installation-and-storage.md). |
| F03 Session-source registry and scheduling | Settings source edits / startup reconciliation / Sync / `scan` → `sources/registry.py`, `settings.py`, `profiles.py`, `sync.py`, session/context sync → `session-sources.toml`, sources/source_files rows, reconnect journal and domain health JSON | Retained; depends on shared lock and F02 for TOML+DB rollback/reconnect. Keep identity, array order, disable vs unregister vs purge, numeric revision admission, completion-based scheduling and active-run noninterruption. [Source lifecycle](../../policies/project/desktop-app-and-settings.md#source-lifecycle-contract). |
| F04 Session ingestion and normalization | periodic/manual/CLI scans → `ingest/providers`, `sync`, `evidence`, scanner/extensions → Sessions/events, Usage facts/snapshots, skills, references, FTS, DB stamp and optional observers | Port per provider/container and repair lane with F03/F02/F06/F08. Preserve JSONL/Zstd replacement/retention, direct/subsession/maintenance eligibility, IDs, revisions, frozen attribution, rollback and unchanged second scan. [Ingestion](../../policies/project/session-ingestion.md), [Usage](../../policies/project/usage-and-cost.md). |
| F05 Sessions, Projects and related reading | `/sessions`, `/projects`, detail/subsession/legacy redirect, Chart/activity, pin/unpin/title/visibility → `sessions/` queries, presence, reading, pins, titles, skills, references → templates, Chart JS, reading/related-resource rail | Read and mutation slices may split after F02/F08. Preserve ordering/pagination/filters, missing-source truth, title/pin/visibility state, direct provenance and Markdown/related-reference consumers. [Sessions](../../policies/project/sessions.md). |
| F06 Usage and Dashboard | ingestion writes / Sessions Dashboard → `usage/records.py`, `pricing.py`, `queries.py`, `web.py` → immutable price snapshots and source/project/time-zone-scoped totals/trends | Separate normalization/write boundary from analytical read boundary. Preserve direct/subsession/maintenance inclusion, replay exclusions, partial/unavailable pricing and date/month boundaries; never reprice history as a port side effect. [Usage](../../policies/project/usage-and-cost.md). |
| F07 Local Context | settings folder/file/Apple Notes add/remove/order; Context and document routes; context sync → `local_context/`, `ingest/sync/contexts.py` and scanner → context roots/documents, FTS, resource bindings, reader tree/body | F02/F08 before writes; Notes retains explicit macOS permission. Preserve root ownership, deletion boundary, same-path rebinding, full document/Obsidian syntax and reference provenance. [Local Context](../../policies/project/local-context.md). |
| F08 Shared references and resources | Session/document evidence, local-resource reader and organization links → pure `references/`, `resources/catalog.py`, store/related_context → shared identities and distinct document/path/URL bindings, notes/content, related rail and optional outgoing mappings | Separate identity/store contract with F02. Do not couple common evidence to Atlassian registration or Workstream membership. Feature mapping deletion does not delete shared resources/observations. [Resource data model](../../policies/project/data-model/work-organization-and-resources.md). |
| F09 Keyword and optional semantic retrieval | `/natural-search` status/query/evidence/prepare/cancel and `search` CLI → `search/keyword.py`, lexical, `natural_search/` conditions/molecules/source/index/service → FTS/evidence, index/metadata and frontend results | Query/read and preparation/job slices after source eligibility/F02/F10 contracts. Preserve exact identifiers, filters and current eligibility/revision checks before the 500-fragment lexical cap; candidate/page limits do not narrow corpus admission. Keep stale-response/cancel behavior, model-free operation and index/model fingerprints. `search/legacy.py` also serves F16. [Search](../../policies/project/natural-language-search.md). |
| F10 Public model assets and optional workers | Settings install/cancel/folder actions, `doctor`, `models`, frozen install worker → `models/` catalog/storage/installation/setup/embedding/generation → public shared weights, private registration, progress/cancel/readiness consumed by F09 and retained experiments | First retain current Python model execution; port management only under its own boundary. Keep pinned model+tokenizer revisions, each content hash, dimension/normalization/index compatibility, offline verification, explicit downloads, trust store and parent-lifetime cleanup. No model load/download on status/import. [Model storage](../../policies/project/installation-and-storage.md#optional-local-models). |
| F11 Host, rendering, Docs and assembly | `main`, `desktop`, root CLI, app lifecycle/routes/settings/docs/templating/guards/picker plus `rendering/` → FastAPI/Jinja/Markdown, local files/schema assets → web/native HTML/JSON/WS, startup handshake, navigation/history and shutdown | Retain Python hosts/GUI while bounded rules move to shared Rust. No Tauri dependency in business core. Preserve response/status/auth/CLI semantics, safe Markdown/math/diagrams, template context, asset/Docs language, focus/history/state, worker startup/shutdown and edition exclusions. [Architecture](../../policies/project/architecture.md), [Docs](../../policies/project/app-documentation.md), [navigation](../../policies/project/navigation-and-history.md). |
| F12 Reviewed learning | web root/dashboard, learning reader/note/attempt/assessment/visibility and `learning import` → `learning/service.py`, app dashboard queries → immutable lessons/source revisions, private attempts/visibility and next-review presentation | Development-web/explicit CLI owner retained; native reader admission and existing untested functional transitions are separate. Preserve reviewed import authority, question depth and immutable lesson vs personal review state. [Learning](../../policies/project/work-grounded-learning.md), [code/command learning](../../policies/project/code-command-learning.md). |
| F13 Work organization and Maintenance | Workstreams/Threads/checkpoints, links/resources, Suggestions, Run create/status/cancel → `workstreams/`, `maintenance/` → curated DB relationships, snapshots, pending review and durable Run ledgers/artifacts/streams | Development-web only. Depend on F02/F08 and explicit runner/approval contracts. Separate common process/cancel/recovery from feature task rules. Preserve reversible Suggestions, explicit acceptance, artifact/ledger lifetimes, failure rollback and no hidden organization edits. [Product](../../policies/project/product.md), [Task Runner](../../policies/operations/claude-task-runner.md). |
| F14 Personal Insights | Sessions Dashboard Insights, analysis create/cancel/status/download → `insights/` evidence/guidance/runs/skills/usage → frozen manifest/report/stream/usage and skill rankings | Development-web only; separate from Maintenance. Preserve analysis-only authorization, exact frozen inputs/guide versions, accounting and parent/subprocess/cancel recovery. No intervention or broader private extraction. [Insights](../../policies/project/personal-insights.md). |
| F15 Workflow and Auto Work | Session workflow/corrections and Auto Work page/refresh, explicit `simulate` / module CLI → `workflow/`, `auto_work/` → deterministic projections, append-only assertions, simulation/preview caches and passive affinity/map | Development-web/explicit CLI retained; current paused planning and trial budgets remain. Distinguish deterministic display/corrections from model experiments; preserve version/fingerprint/correction and cache/writer ownership. [Workflow](../../policies/project/workflow.md), [Auto Work](../../policies/project/auto-work.md). |
| F16 Atlassian and legacy search | local Browse/add/access/Space discovery/register/evidence sync/item/reference/classification/link/refresh and legacy `/search` → `atlassian/`, `search/legacy.py`, optional ingestion observer → site/item/reference/shared-resource rows, reviewable refresh and runner outputs | Development-web only. Common Session URLs remain independent. Default remote executor is unconnected; no remote read/write permission is added. Keep local admission, provider dispatch, provenance, partial/unknown states, exact links and transactional result application. [Atlassian](../../policies/project/atlassian.md). |
| F17 Remaining Terminal host rules | terminal workspace/view-order actions, host-created zsh integration and storage cleanup → retained `terminal/workspaces.py`, presentation/shell/storage/web/CLI plus shared Rust control → workspace JSON, UI order, shell assets, host adapters | Runtime control already migrated; these remaining Python rules are separate debt. F01 must preserve common/terminal saves together. Node PTY/VT and optional model workers remain selected runtimes. Preserve no replay, execution identity, lease/checkpoint/bounds and explicit stop. [Terminal](../../policies/project/terminal.md). |
| F18 Explicit experiment tooling | `experiments/claims`, context, reconstruction, script entrypoints and their tests → frozen synthetic/explicit inputs, trials/scorers → private experiment/report/cache artifacts | Retain; no automatic product port or fresh trial. Any proposed Rust move requires the existing experiment owner, consumed budget and quality/admission state; imported Python model execution may remain. [Plans execution state](../README.md#execution-state). |
| F19 Suspended Context Search | retained `context_search/` routes/service/tools/worker; frozen `--context-search-worker` and answer models → local tool/generation results only if explicitly composed | Excluded from default web/app; preserve source/tests/assets/registrations. No activation or accepted-quality claim. [Availability](feature-availability.md). |
| F20 Suspended Google Drive | retained `google_drive/` settings APIs/service/auth/transport/store/engine and automatic jobs → CLI-owned credentials, selections/checkpoints/received copies | Excluded from default web/app; preserve all existing state and prior two-account/native gaps. No remote requests or synchronization for this inventory. [Availability](feature-availability.md). |

### Complete Python Package Coverage

Counts include `__init__.py` and all nested Python files at the frozen baseline.
Shared packages have a primary inventory family and named cross-family consumers.

| Package/root | Modules | Families |
| --- | ---: | --- |
| package root (`__init__`, `main`, `cli`, `desktop`) | 4 | F11; CLI dispatch below |
| `app/` including `storage/` | 20 | F11, F01/F02/F12 |
| `foundation/` | 13 | F01; shared primitives in other families |
| `persistence/` including migrations | 21 | F02; historical schema for every data family |
| `sources/` | 9 | F03, F04/F07 |
| `ingest/` | 19 | F04, F06/F07/F08 |
| `sessions/` | 12 | F05, F08 |
| `usage/` | 5 | F06 |
| `local_context/` | 5 | F07, F08 |
| `references/` | 4 | F08, F16 |
| `resources/` | 5 | F08, F13/F16 |
| `search/` | 5 | F09, F16 |
| `natural_search/` | 12 | F09 |
| `models/` | 9 | F10; optional F09/F18/F19 consumers |
| `rendering/` | 2 | F11; Session/document/learning readers |
| `learning/` | 4 | F12 |
| `workstreams/` | 6 | F13 |
| `maintenance/` | 4 | F13, F16 |
| `insights/` | 7 | F14 |
| `workflow/` | 9 | F15 |
| `auto_work/` | 10 | F15 |
| `atlassian/` | 13 | F16 |
| `terminal/` | 12 | F17, F01; runtime/processes remain legacy parity fixtures |
| `experiments/` | 21 | F18 |
| `context_search/` | 6 | F19, suspended |
| `google_drive/` | 9 | F20, suspended |
| Total | 246 | All 26 groups accounted for |

## CLI, Lifecycle And Delivered Consumers

| Entry or contribution | Existing owner and output/effect to preserve |
| --- | --- |
| `lb` / `localbrain` | Same `cli:main` dispatch. `init` initializes DB; `serve --host/--port` binds loopback without access logs; `scan [--full]` scans admitted sources/observers and refreshes search. Keep arguments, JSON/stdout/stderr/exit/error boundaries. |
| `doctor`; `models status/install/verify` | F10 readiness without source/model execution on status; install/verify of embedding/4b/8b retains explicit invocation, offline option and fixed diagnostics. Suspended GUI generation cards do not delete existing CLI capability. |
| `storage status/cleanup/migrate` | F02 accounting and default preview; explicit apply, inactivity/WAL refusal, known cache owners and optional development-archive boundary. |
| `search status/prepare/query`; `learning import` | F09/F12 direct delegated CLI, including existing JSON/exit/error and reviewed import contracts; no new CLI is inferred for every screen. |
| `simulate`; `python -m localbrain.auto_work`; explicit experiment scripts | F15/F18 existing composition flags and explicit-only compute/trial authority. Preserve module/script entrypoints and paused/blocked/consumed allowances. |
| conditional `terminal` and app-less Rust management | F17 macOS/development CLI dispatch; independent payload management remains after app Quit/removal. No service start or terminal input from this planning task. |
| Backend storage lease and startup | `app/lifecycle.py` acquires recovery/storage lease, initializes DB, recovers/migrates source settings, maintains included-feature caches, reconciles registry and initializes absent common preferences; existing partial/invalid files are preserved. |
| Background collection and search | Session/context sync completion clocks and preferences; optional ingestion observers; search watch thread and model-setup worker. Keep stop/join/cancel order and no model download on startup. |
| Optional lifecycle contributions | Development-only Maintenance/Insights interrupted-run recovery/shutdown; factories/cache hooks only for included packages. Suspended Drive/Context Search factories remain unconstructed. |
| Native host lifecycle | `desktop.py` per-launch token/random loopback readiness, parent pipe, shutdown; Tauri window/commands/build resources. Terminal manager lifetime differs from backend lifetime under its existing contract. |
| Framework and middleware entries | Static mount, framework OpenAPI/docs routes and `/desktop/start` handshake are not counted as explicit route syntax below. Keep edition guards, exact-origin mutations and separate WS admission; middleware path allowance does not establish availability. |
| Packaged assets and generated data | Jinja templates, static/CSS/JS/fonts, Docs, schema/registry/guide JSON and `schema.sql` use package-root resolution in source/wheel/frozen layouts. Preserve generators and their source owners, not only copied outputs. |
| Build and verification inputs | `pyproject.toml`/`uv.lock`, `rust/` and desktop Cargo locks/manifests, desktop backend spec/npm locks/config, `build-desktop.py`, `build-terminal-runtime.py`, terminal/Markdown/Mermaid/schema/value/catalog builders and related tests/QA. Binary/source/ABI/manifest identity and actual host checks are separate gates. |

## Dependency Order And First Handoff

The following is a proposed dependency order, not approval of every listed port.
Each family still needs a bounded Feature. Existing tables/fixtures may support
read-only slices before the corresponding ingester is ported; do not require a
whole-backend rewrite before the next usable increment.

1. **Common settings cutover contract (F01/F11/F17):**
   [FEAT-0178](../feature/feat-0178-rust-common-settings-cutover-contract.md)
   passes Run259. Its [selected contract](rust-common-settings-cutover-contract.md)
   fixes one settings transaction owner, cross-process lock/outer-lock behavior,
   TOML value/format/error compatibility and a common runtime available without
   a Terminal payload. This foundation is contract-only; the separate product
   below implements it and wires common/terminal consumers.
2. **Common settings product slice — passed:** [FEAT-0179](../feature/feat-0179-rust-common-settings-runtime.md)
   implements the passed contract in Run260 for the first macOS14/
   Apple Silicon source/wheel/native target, with no Node/model/terminal setup prerequisite.
   Python syntax/OS-zone adapters remain; the normal writer/rules now live in Rust.
   Eval0176 verifies default/partial/invalid files, read-only behavior, first start/restart,
   general/terminal save entrypoints, scheduling/time-zone consumers, race/lost-response,
   backup/restore and real artifact identity. Do not silently keep a second normal
   Python settings writer as a success fallback.
3. **Persistence/identity and recovery boundaries (F02/F08):** freeze SQLite
   connection/transaction/bootstrap/recovery/FTS and shared-resource contracts;
   implementation slices keep schema/data/IDs and historical optional tables.
   F01 is not permission for DB ownership transfer. Read-only F05/F06 pilots can
   follow a passed connection/read boundary on a seeded compatible database.
4. **Sources and write producers (F03/F04/F06/F07/F08):** coordinate registry,
   reconnect, provider/container normalization, Usage snapshots and reference/FTS
   writes per complete transaction/repair lane. Do not migrate the Session lane
   while leaving required Usage/provenance side effects unowned. Context and Notes
   can be a separate coherent writer slice under their own deletion contract.
5. **Readers and local retrieval (F05/F06/F07/F09/F10):** complete remaining
   inventory/detail/chart/resource/usage/query/prepare flows; retain optional
   Python model workers until separately selected. No claim of embedding/index
   equivalence from dimensions alone or of a faster GUI from a faster query.
6. **Remaining admitted development-web families and app gaps (F12–F17):**
   learning, organization/runner, Insights, workflow/Auto Work, Atlassian and
   Terminal host rules each retain an owner and separate runtime/admission checks.
   Inventory and preserve explicit CLI/module tools (F18); do not run experiments
   or reactivate F19/F20. Revisit admitted native parity under the parent boundary.
7. **Host/HTTP/rendering retirement and final delivery (F11):** only after every
   admitted family/consumer is mapped, remove remaining application Python host
   responsibilities through approved slices. Optional Python model execution
   and Node VT remain separate choices. Full completion requires inventory-wide
   coverage, actual source/wheel/native delivery and retained evidence limits.

### Why Settings Comes First

The current shared Rust core has no TOML parser/writer or SQLite dependency.
`terminal/core.py` locates a Terminal runtime/bundle and imports the Python
preferences error, so calling it from `foundation/preferences.py` would reverse
the foundation dependency and risk a cycle. A normal Python wheel currently has
no automatically bundled common Rust executable. Moving Settings must therefore
settle a common transport/delivery boundary as well as the file transaction.

`operation_lock` is a data-directory mutex plus nonblocking `operations.lock`
flock with same-thread reentrancy. Its `purpose` parameter does not create
separate per-feature locks: scans, source edits, backup/restore and preferences
serialize together. Reopening that parent-held lock in a child is not reentrant.
The first contract must choose a verifiable handoff/ownership rule, including
outer-lock callers, crash/cancel and retained recovery writes. No new lock file,
manager `control.lock` nesting or automatic retry may change that invariant.

Normal common saves and terminal saves share `settings.toml`. The source registry
uses `session-sources.toml`; search settings and model registrations have separate
JSON owners, and Context settings use DB rows. Sharing a lock or serializer does
not transfer those stores into the first product slice. Preserve the shared
`toml_text`/`atomic_private_write` callers until their owners change separately.

## Per-Slice Validation And Remaining Debt

Before each implementation/parity claim, freeze actual baseline and candidate,
dependencies/configuration/guidance and delivered inputs. Map entry → rules →
query/write → output/side effects → every affected CLI/GUI/job consumer, with
normal, missing/unknown, error, retry/cancel, race/rollback and restart witnesses.
Apply [regression control](../../policies/project/change-scope-and-regression.md)
and the refactor track's independent challenge/re-review gates. A passing
formatter, source test or inventory is not whole-family parity or a merge decision.

Existing test anchors include preferences/startup, terminal settings/core/build,
desktop boundary/settings/build/onboarding, feature assembly, source settings and
sync, schema migrations/shared resources, parsers/compressed/retained sessions,
Usage contracts/dashboard, Local Context, search/models, learning, runners,
Insights, workflow and Atlassian. Select actual test methods and fill their gaps
at the chosen slice; filenames alone are not audited behavior evidence.

No Phase3 implementation has passed. All retained families above remain migration
debt. Native/physical IME, sleep/VoiceOver, recipient/minimum-OS/performance and
declared-MSRV limits retain their existing owners; this inventory produces no new
runtime measurement, database migration, native-window pass or deployment.

## Explicit Route Registration Snapshot

This appendix records each baseline registration expression once, with its
owning source, inventory family and local branch predicate. Parent installer and
edition restrictions above also apply. `always` means no local `if` around the
expression, not that the route is offered by every installation. Dynamic action
parameters retain their handler allowlists; the table does not expand authority.

### app/docs.py — 2 registrations

Source: `src/localbrain/app/docs.py` (app/docs.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F11 | `GET /help` | `getting_started:105` | `always` |
| F11 | `GET /help/{slug}` | `guide_page:109` | `always` |

### app/routes.py — 80 registrations

Source: `src/localbrain/app/routes.py` (app/routes.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F15 | `GET /auto-work` | `auto_work_web.auto_work_page:33` | `'auto_work' in selected` |
| F15 | `POST /auto-work/refresh` | `auto_work_web.auto_work_refresh:34` | `'auto_work' in selected` |
| F11/F12 | `GET /` | `app_web.dashboard:35` | `always` |
| F06 | `GET /sessions-dashboard` | `usage_web.sessions_dashboard:36` | `always` |
| F14 | `GET /sessions-dashboard/insights` | `insights_web.session_insights:38` | `not DESKTOP` |
| F14 | `POST /sessions-dashboard/insights/runs` | `insights_web.create_insight_run:39` | `not DESKTOP` |
| F14 | `POST /sessions-dashboard/insights/runs/{run_id}/cancel` | `insights_web.stop_insight_run:40` | `not DESKTOP` |
| F14 | `GET /sessions-dashboard/insights/runs/{run_id}/download` | `insights_web.download_insight_report:41` | `not DESKTOP` |
| F14 | `GET /api/insight-runs/{run_id}` | `insights_web.insight_run_status:42` | `not DESKTOP` |
| F13 | `GET /workstreams` | `workstreams_web.workstreams_page:44` | `'workstreams' in selected` |
| F13 | `GET /workstreams/{workstream_id}` | `workstreams_web.show_workstream:45` | `'workstreams' in selected` |
| F13 | `GET /runs/{run_id}` | `maintenance_web.show_run:47` | `selected & {'atlassian', 'workstreams'}` |
| F05 | `GET /sessions` | `sessions_web.sessions_page:48` | `always` |
| F05 | `PUT /sessions/chart/project-visibility` | `sessions_web.save_chart_project_visibility:49` | `always` |
| F07 | `GET /context` | `local_context_web.context_page:50` | `always` |
| F16 | `GET /atlassian` | `atlassian_web.atlassian_page:52` | `'atlassian' in selected` |
| F16 | `POST /atlassian/sync` | `atlassian_web.atlassian_sync:53` | `'atlassian' in selected` |
| F16 | `GET /atlassian/add` | `atlassian_web.atlassian_add_page:54` | `'atlassian' in selected` |
| F16 | `GET /atlassian/connections` | `atlassian_web.atlassian_connections_page:55` | `'atlassian' in selected` |
| F16 | `POST /atlassian/register` | `atlassian_web.atlassian_register:56` | `'atlassian' in selected` |
| F16 | `POST /atlassian/access` | `atlassian_web.atlassian_register_access:57` | `'atlassian' in selected` |
| F16 | `GET /api/atlassian/registration-preview` | `atlassian_web.atlassian_registration_preview:58` | `'atlassian' in selected` |
| F16 | `POST /atlassian/connections/{source_instance_id}/sites/{site_id}` | `atlassian_web.atlassian_update_connection:59` | `'atlassian' in selected` |
| F16 | `POST /atlassian/spaces/discover` | `atlassian_web.atlassian_discover_spaces:60` | `'atlassian' in selected` |
| F16 | `POST /atlassian/spaces/register` | `atlassian_web.atlassian_register_space_candidate:61` | `'atlassian' in selected` |
| F16 | `GET /atlassian/items/{item_id}` | `atlassian_web.atlassian_item_page:62` | `'atlassian' in selected` |
| F16 | `GET /atlassian/references/{reference_id}` | `atlassian_web.atlassian_reference_page:63` | `'atlassian' in selected` |
| F16 | `POST /atlassian/items/{item_id}/local` | `atlassian_web.atlassian_update_local:64` | `'atlassian' in selected` |
| F16 | `POST /atlassian/items/{item_id}/links` | `atlassian_web.atlassian_add_local_link:66` | `{'atlassian', 'workstreams'} <= selected` |
| F16 | `POST /atlassian/items/{item_id}/links/{scope_type}/{scope_id}/{link_id}` | `atlassian_web.atlassian_remove_local_link:67` | `{'atlassian', 'workstreams'} <= selected` |
| F16 | `GET /atlassian/refresh` | `atlassian_web.atlassian_refresh_page:69` | `'atlassian' in selected` |
| F16 | `POST /atlassian/refresh` | `atlassian_web.atlassian_start_refresh:70` | `'atlassian' in selected` |
| F05 | `GET /projects` | `sessions_web.projects_page:71` | `always` |
| F03 | `POST /sessions/sync` | `sources_web.sync_sessions_page:72` | `always` |
| F05 | `POST /sessions/{session_id}/pin` | `sessions_web.pin_session_page:73` | `always` |
| F05 | `POST /sessions/{session_id}/unpin` | `sessions_web.unpin_session_page:74` | `always` |
| F05 | `POST /sessions/{session_id}/title` | `sessions_web.save_session_title:75` | `always` |
| F03 | `GET /sources` | `sources_web.sources_page:77` | `not DESKTOP` |
| F03 | `POST /sources/scan` | `sources_web.scan_sources_page:78` | `not DESKTOP` |
| F02 | `GET /schema` | `persistence_web.schema_page:79` | `not DESKTOP` |
| F05 | `GET /sessions/{session_id}/chart-activity` | `sessions_web.show_session_chart_activity:80` | `always` |
| F05 | `GET /sessions/{session_id}` | `sessions_web.show_session:81` | `always` |
| F15 | `GET /sessions/{session_id}/workflow` | `workflow_web.show_session_workflow:83` | `'workflow' in selected` |
| F15 | `POST /sessions/{session_id}/workflow/corrections` | `workflow_web.correct_session_workflow:84` | `'workflow' in selected` |
| F05 | `GET /sessions/{session_id}/subsessions/{file_name}` | `sessions_web.show_subsession:85` | `always` |
| F05 | `GET /sessions/{session_id}/subagents/{file_name}` | `sessions_web.redirect_legacy_subagent_route:86` | `always` |
| F07 | `GET /documents/{document_id}` | `local_context_web.show_document:87` | `always` |
| F08 | `GET /local-resources/{resource_id}` | `resources_web.show_local_resource:89` | `not DESKTOP` |
| F09 | `GET /natural-search` | `natural_search_web.natural_search_page:90` | `always` |
| F09 | `GET /api/natural-search/status` | `natural_search_web.natural_search_status:91` | `always` |
| F09 | `POST /natural-search/prepare` | `natural_search_web.natural_search_prepare:92` | `always` |
| F09 | `POST /natural-search/cancel` | `natural_search_web.natural_search_cancel:93` | `always` |
| F09 | `GET /natural-search/evidence/{rowid}` | `natural_search_web.natural_search_evidence:94` | `always` |
| F11 | `GET /search` | `app_web.desktop_legacy_search:96` | `DESKTOP` |
| F16 | `GET /search` | `search_web.search_page:98` | `else: DESKTOP; 'atlassian' in selected` |
| F13 | `POST /api/workstreams` | `workstreams_web.api_create_workstream:100` | `'workstreams' in selected` |
| F07 | `POST /api/context-roots` | `local_context_web.api_add_context_root:101` | `always` |
| F07 | `POST /api/context-files` | `local_context_web.api_add_context_file:102` | `always` |
| F07 | `POST /api/context-sources/apple-notes` | `local_context_web.api_add_apple_notes_source:103` | `always` |
| F07 | `POST /api/context-sources/order` | `local_context_web.api_reorder_context_sources:104` | `always` |
| F07 | `DELETE /api/context-roots/{root_id}` | `local_context_web.api_remove_context_root:105` | `always` |
| F07 | `DELETE /api/context-sources/{source_id}` | `local_context_web.api_remove_context_source:106` | `always` |
| F13 | `PUT /api/workstreams/{workstream_id}` | `workstreams_web.api_update_workstream:108` | `'workstreams' in selected` |
| F13 | `POST /api/workstreams/{workstream_id}/threads` | `workstreams_web.api_create_thread:109` | `'workstreams' in selected` |
| F13 | `PUT /api/threads/{thread_id}` | `workstreams_web.api_update_thread:110` | `'workstreams' in selected` |
| F13 | `POST /api/workstreams/{workstream_id}/checkpoints` | `workstreams_web.api_create_checkpoint:111` | `'workstreams' in selected` |
| F13 | `POST /api/links` | `workstreams_web.api_add_link:112` | `'workstreams' in selected` |
| F13 | `DELETE /api/links/{scope_type}/{scope_id}/{link_id}` | `workstreams_web.api_remove_link:113` | `'workstreams' in selected` |
| F13 | `POST /api/external-resources` | `workstream_resources_web.api_create_external_resource:114` | `'workstreams' in selected` |
| F13 | `POST /api/local-resources` | `workstream_resources_web.api_create_local_resource:115` | `'workstreams' in selected` |
| F13 | `POST /api/workstreams/{workstream_id}/suggestions` | `workstreams_web.api_generate_suggestions:116` | `'workstreams' in selected` |
| F13 | `POST /api/suggestions/{suggestion_id}/{action}` | `workstreams_web.api_resolve_suggestion:117` | `'workstreams' in selected` |
| F13 | `POST /api/workstreams/{workstream_id}/runs` | `workstreams_web.api_start_task_run:118` | `'workstreams' in selected` |
| F13 | `GET /api/runs/{run_id}` | `maintenance_web.api_run_status:120` | `selected & {'atlassian', 'workstreams'}` |
| F13 | `POST /api/runs/{run_id}/cancel` | `maintenance_web.api_cancel_run:121` | `selected & {'atlassian', 'workstreams'}` |
| F03 | `POST /api/scan` | `sources_web.scan_sources:123` | `not DESKTOP` |
| F03 | `POST /api/sessions/sync` | `sources_web.sync_session_sources:124` | `always` |
| F03 | `GET /api/sessions/sync/status` | `sources_web.session_sync_status:125` | `always` |
| F03 | `POST /api/sessions/sync/stream` | `sources_web.stream_session_sources:126` | `always` |
| F11 | `GET /api/health` | `app_web.health:127` | `always` |

### app/settings.py — 11 registrations

Source: `src/localbrain/app/settings.py` (app/settings.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F01/F11 | `GET /settings` | `settings_page:59` | `always` |
| F01/F11 | `GET /onboarding` | `onboarding:63` | `always` |
| F01/F11 | `GET /api/settings` | `get_settings:71` | `always` |
| F09 | `GET /api/settings/search` | `get_search_settings:97` | `always` |
| F09 | `POST /api/settings/search` | `search_settings_update:101` | `always` |
| F01/F11 | `PATCH /api/settings/preferences` | `preferences_update:119` | `always` |
| F03 | `POST /api/settings/session-sources` | `sources_update:128` | `always` |
| F01/F11 | `POST /api/settings/choose-path` | `choose_path:135` | `always` |
| F10 | `POST /api/settings/model/{action}` | `model_action:152` | `always` |
| F10 | `POST /api/settings/model-folder/{action}` | `model_folder_action:171` | `always` |
| F10 | `POST /api/settings/model/{key}/{action}` | `generation_model_action:187` | `always` |

### app/storage/web.py — 5 registrations

Source: `src/localbrain/app/storage/web.py` (app/storage/web.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F02 | `GET /api/settings/storage` | `storage:21` | `always` |
| F02 | `POST /api/settings/backup` | `backup:29` | `always` |
| F02 | `POST /api/settings/backup/export` | `export_backup:35` | `always` |
| F02 | `POST /api/settings/restore` | `restore:63` | `always` |
| F02 | `POST /api/settings/cache/clear` | `cache_clear:84` | `always` |

### context_search/web.py — 4 registrations

Source: `src/localbrain/context_search/web.py` (context_search/web.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F19 | `GET /context-search` | `context_search_page:16` | `always` |
| F19 | `GET /api/context-search/status` | `context_search_status:20` | `always` |
| F19 | `POST /api/context-search/unload` | `context_search_unload:27` | `always` |
| F19 | `POST /api/context-search/answer` | `context_search_answer:32` | `always` |

### desktop.py — 1 registrations

Source: `src/localbrain/desktop.py` (desktop.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F11 | `POST /desktop/shutdown` | `shutdown:37` | `always` |

### google_drive/web.py — 6 registrations

Source: `src/localbrain/google_drive/web.py` (google_drive/web.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F20 | `GET /api/settings/google-drive` | `status:22` | `always` |
| F20 | `POST /api/settings/google-drive/connections` | `add:26` | `always` |
| F20 | `POST /api/settings/google-drive/{connection_id}/connect` | `authenticate:33` | `always` |
| F20 | `POST /api/settings/google-drive/{connection_id}/browse` | `browse:44` | `always` |
| F20 | `PATCH /api/settings/google-drive/{connection_id}/jobs/{job}` | `configure:48` | `always` |
| F20 | `POST /api/settings/google-drive/{connection_id}/jobs/{job}/run` | `run:54` | `always` |

### learning/web.py — 6 registrations

Source: `src/localbrain/learning/web.py` (learning/web.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F12 | `GET /learning` | `learning_library:124` | `always` |
| F12 | `GET /learning/{lesson_id}` | `learning_reader:129` | `always` |
| F12 | `GET /learning/{lesson_id}/note` | `learning_note:135` | `always` |
| F12 | `POST /learning/{lesson_id}/attempts` | `learning_submit:152` | `always` |
| F12 | `POST /learning/{lesson_id}/assess` | `learning_assess:176` | `always` |
| F12 | `POST /learning/{lesson_id}/visibility` | `learning_visibility:200` | `always` |

### terminal/web.py — 13 registrations

Source: `src/localbrain/terminal/web.py` (terminal/web.py); line locators refer to the frozen baseline.

| Family | Method and path | Handler (line) | Local predicate |
| --- | --- | --- | --- |
| F17 | `GET /terminal` | `terminal_page:74` | `always` |
| F17 | `GET /api/terminal` | `terminal_state:78` | `always` |
| F17 | `POST /api/terminal/workspaces/{action}` | `workspace_action:94` | `always` |
| F17 | `POST /api/terminal/view-order` | `view_order:114` | `always` |
| F17 | `POST /api/terminal/install` | `install:135` | `always` |
| F01/F17 | `GET /api/terminal/settings` | `launch_settings:140` | `always` |
| F01/F17 | `POST /api/terminal/settings` | `update_launch_settings:146` | `always` |
| F17 | `POST /api/terminal/service/{action}` | `service_action:153` | `always` |
| F17 | `POST /api/terminal/terminals` | `create:165` | `always` |
| F17 | `POST /api/terminal/stop` | `stop_all:199` | `always` |
| F17 | `POST /api/terminal/terminals/{terminal_id}/stop` | `stop:206` | `always` |
| F17 | `POST /api/terminal/tabs/{tab_id}/{action}` | `tab_action:218` | `always` |
| F17 | `WEBSOCKET /api/terminal/terminals/{terminal_id}/stream` | `stream:228` | `always` |
