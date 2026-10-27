# EVAL-0139: Standalone Test App Integration

## Metadata

- ID: `eval-0139`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `FAIL` for complete distribution acceptance: the required teammate receipt is unavailable; the local checks below pass.
- Run: [RUN-177](../run/run-20261018-177-standalone-test-app-delivery.md)
- Feature: [FEAT-0139](../feature/feat-0139-standalone-test-app-delivery.md)
- Spec: [SPEC-0139](../spec/spec-0139-standalone-test-app-delivery.md)
- Execution Profile: `infra-devtool`, with Fullstack dependencies
- Surface Lanes: shared web, local persistence, model worker, native shell, delivery
- Evidence Coverage: `partial`
- Created: `2026-10-18`
- Updated: `2026-10-26`

## Session Closeout — 2026-10-26

This closes the source/documentation work in the current repository, from the
public Mac app discussion through the final profile/palette/pin corrections and
shared evaluation lessons. It reconciles PRD-0021, FEAT/SPEC-0128–0140,
Runs166–204, FIX-0131, foundation evaluations and the dated receipts below.
The original **13 Features / 21 estimated commits** remains a planning estimate,
not a count of Git commits or evidence of complete distribution acceptance.

The owner now explicitly authorizes this repository's session changes to be
reviewed, tested, committed and pushed. Drive upload, teammate messages, paid
Apple enrollment and Apple submission remain outside that authorization.
Separate Learning implementation and its mixed-file edits are preserved in the
original working tree and excluded from this publication candidate. Checks below
apply to that isolated candidate, not to the full mixed working tree.

### Reconciled Outcomes And Owners

- [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
  preserves the choices and rationale: Tauri/Apple Silicon, an early ad-hoc `.app`
  ZIP, and a company-independent public product as the later distribution goal.
  The portable test artifact does not satisfy normal-Gatekeeper public acceptance.
  Sessions, Sessions Dashboard and Local Context remain the product focus; the
  specified unfinished features stay outside the app edition.
- The [desktop/settings contract](../../policies/project/desktop-app-and-settings.md)
  owns local file precedence, separate domain stores, fixed current-home path
  display, compact autosaving General settings, the overlay setup wizard,
  independent Session/Context Sync selectors, optional local AI search and
  same-installation recovery. Earlier environment override, display-root,
  checkbox and status-card iterations remain dated history, not current rules.
  Session defaults to enabled/10 minutes and Context to enabled/30 minutes;
  existing values win, Off preserves the prior interval, and each domain schedules
  from its own completion. The manual Sessions action remains.
- The [Source registry](../../policies/project/data-model/source-registry-and-scans.md)
  and profile contract distinguish numeric primary key, provider, nickname, path,
  color and order. Current string aliases are removed; legacy reads are confined
  to migration. Existing imported IDs and frozen provenance survive. The
  [Usage owner](../../policies/project/data-model/usage-and-cost-records.md)
  retains eligible analysis/Maintenance usage in overall totals, history and
  Source/Model composition. Project includes only work Sessions and work
  subsessions; displayed paths, including `~`, do not rewrite stored attribution.
- The [design constitution](../../policies/design/design-constitution.md),
  [DESIGN](../../../DESIGN.md) and dated receipts retain the interaction rationale:
  requested dropdowns, compact controls, Home-first registration, reversible
  registration removal, reorder feedback/keyboard support, aligned color menu
  geometry, explicit pointer/keyboard focus, displayed-path pin sorting and
  bounded hidden labels. Source instructions move to the relevant README usage
  section; the documentation map now links both desktop owners.

### Shared Evaluation Experience — 2026-10-26

The owner authorized generalizing this session's reusable UI/UX findings into
ai-assets. [Commit dc15bf9](https://github.com/chochita0311/ai-assets/commit/dc15bf9ad9aae2eaa6c819117a28e807cfbdb755)
updates its Design/Interaction Evaluation policies and standalone screen-alignment
procedure, with three generalized evidence records. The eight concerns are
requested-control preservation; frame/painted/hit-area geometry; sequential input
and focus; reorder feedback and commit; autosave confirmation and races; displayed
sort semantics; actual-host/native-action evidence; and hidden-content overflow.
Two documentation reviews corrected export-link portability and record subject
discovery; package, schema, links, privacy and public-fitness checks passed. This is shared
source publication, not a refresh of LocalBrain's installed harness or proof of
improved future agent behavior. Private original receipts remain at their owners;
public examples retain recorded-execution and unrun-scenario limits.

### Closeout Review And Verification

The two independent documentation reviewers applied `docs-structuring` and
`docs-shaping` to the resolved repository/session boundary, original session
inventory, implementation references and all 39 dated Runs. Their findings were
checked against source evidence, not adopted as new requirements. Repairs align
current identity/Sync contracts, distinguish old observations from current rules,
restore the full public-product proposition, fix owner placement/navigation and
preserve existing deferred decisions. All 39 Run bodies retain their original content; only a trailing blank line in
Runs187/188 was removed for the publication whitespace check. Historical model, build and execution observations
retain their original dates and limits. Both final independent reviews found no unresolved documentation finding.
The structural review checked 106 Markdown documents and 2,861 local targets
without a missing path or anchor. A review question about elapsed test time was
resolved against the publication-candidate rerun (26.186 s), distinct from the
earlier 24.781 s run. Reviewers did not rerun code or inspect private runtime data.

The primary code review inspected the source-identity migration and PK retention,
settings validation/revision/readback, source reconnect rollback, shared writer
locks and separate completion clocks, recovery/cache boundaries, desktop admission
and native navigation, model opt-in/build privacy, usage/pin projections and
settings event handling. Separation review caught a missing baseline web Dashboard
import and unrelated Learning prose; the import was restored and only the unrelated
prose was excluded. No behavior defect remained in the reviewed candidate scope.

- **Python:** the complete candidate suite passes **1,250 tests** in **26.186 s**.
  The first isolated run had three schema audit/presentation expectation failures;
  reviewed source/profile/Context changes required 523 columns, 58 physical and
  28 application relationships. The current ledger has 706 objects: 594 keep,
  zero change/remove and the same 112 deferred decisions. The authoritative
  profile-color fallback labels now describe colors; generated owners are rebuilt.
  These results supersede neither the dated 1,174/1,178 result nor its different
  mixed-workspace scope.
- **Browser:** an isolated synthetic backend/profile exercised wizard Next and
  Set up later; a 720×560 settings frame; startup options in navigation order;
  a 240×32 dropdown whose menu starts below and matches the trigger width;
  separate 10/20/30/60/Off Sync choices; Off preserving the saved 10-minute interval;
  Home-derived profile creation; persisted profile color and keyboard ordering;
  editor reset on category return; unregister confirmation/cancel; and independent
  Context ordering with focus return. The color menu and trigger both measured
  32px wide with matching left edges and no color-name title attributes on choices.
  The observed narrow viewport was 500px, with no outer horizontal overflow;
  the requested 390px window resize was constrained by this browser host, so it
  is not a new 390px check. This pass used DevTools clicks/keys and some scripted
  form setup/API seeding; it does not establish physical input or native chooser
  selection in Tauri.
- **Restart/routes:** after a clean verification-backend restart, Off/interval,
  profile order and Context order persisted. Web Dashboard, Sessions, Chart,
  Projects, Sessions Dashboard, Context, Settings and keyword Search returned 200.
  The console includes one connection-refused resource message across the
  deliberate backend restart; no application JavaScript exception was observed.
- **Static/generated/privacy:** JavaScript syntax, generated dictionaries/schema,
  schema-owner and cleanup-audit checks, plan catalog, reviewed local links and
  diff whitespace pass. Repository privacy passes for the isolated publication
  tree, including the local private-pattern set. These checks do not validate
  native rendering or public-release readiness.

No model was downloaded or installed during this closeout; the verification
backend used isolated data and offline model settings. No user runtime database,
settings, installed app or existing model cache was changed. The current environment
has no available Cargo/Tauri build toolchain, so the app/ZIP was **not rebuilt**;
prior dated bundle and WKWebView evidence remains historical and is not a binary
receipt for this separated source tree.

### Remaining Work And Evidence Limits

Complete native/recipient/public-release acceptance remains unfulfilled: physical
chooser valid-selection/save/reopen behavior, native menu/close/Dock/shortcut and
VoiceOver coverage, the downloaded artifact on another Mac, minimum macOS 14 and
other memory configurations, Notes/PDF permission paths, physical sleep/resume
and large real-corpus performance need their own applicable evidence. Code mocks,
a helper dialog, injected WKWebView input and developer-Mac execution do not stand
in for those observations. Developer ID/notarization remains later work while
paid enrollment is unavailable; standard macOS security is still the public goal.

Runs197 and201 separately observed desktop-backend unavailability when web and
app were started together; sequential restart recovered. The cause was not
established. Shared-writer tests do not establish simultaneous-start acceptance,
and this open runtime finding is retained separately from the native-input gaps.

AI indexing independent control, data/settings transfer and path translation,
changing the live storage root, Intel and automatic updates remain deferred.
No feature, release or external-delivery approval is inferred from source commit
or push. Git records identify the actual commit; the final closeout response must
report remote verification and any remaining publication blocker after that action.

Task-owned candidate, synthetic runtime and diagnostic scratch are temporary
verification state. The recorded scope/results above are the durable evidence;
no owner document depends on a temporary path. Cleanup occurs only after the
verification processes and reviews finish and publication/recovery no longer
needs the private comparison copies.

## Startup Correction — 2026-10-19

The owner opened the initial app and received an authentication JSON error with
unreadable Korean. Its initial native window/process checks did not establish
successful first-page rendering. The initial ZIP is superseded by the repaired
artifact recorded below; its earlier model/recovery/browser measurements remain
historical evidence within their original scopes.

[FIX-0131](../fix/fix-0131-desktop-startup-cookie.md) reproduced HTTP 401 on the
original frozen backend. `SameSite=Strict` omitted the launch cookie on WKWebView's
first cross-scheme redirect; missing JSON charset caused an EUC-KR guess. The
repair uses HttpOnly/Lax while retaining token/loopback/origin restrictions,
explicit UTF-8 errors and no-store handshake/error responses.

The new macOS WKWebView regression check fails against the original backend and
passes against the rebuilt backend with fresh and previous-launch cookies. It
checks actual shell rendering, UTF-8, authenticated health/settings requests,
settings dialog open/close and a token-free landing URL. A synthetic snapshot
was inspected through WKWebView's own snapshot API, without changing system
capture/Accessibility permissions. This is narrower than all Tauri-native controls.

Six new middleware tests pass. The startup-repair suite had **1,178 tests: 1,174 passed,
four pre-existing learning inventory failures, no errors**. The repaired app is
at the same output path, with user data/settings preserved. Native file chooser,
menu/close/Dock, recipient permissions and teammate Mac acceptance remain open.

## Scope And Trace

The owner authorized the full bounded implementation and related tests, browser
and app execution. In the initial implementation, the primary agent performed the work without
subagents; the later closeout above adds two independent documentation reviews.
The initial receipt covers the integration of these separately tracked units:

| Feature | Spec | Run |
| --- | --- | --- |
| [FEAT-0128](../feature/feat-0128-local-settings-contract.md) — 공통 로컬 설정 계약 | [SPEC-0128](../spec/spec-0128-local-settings-contract.md) | [RUN-166](../run/run-20261018-166-local-settings-contract.md) |
| [FEAT-0129](../feature/feat-0129-session-source-lifecycle-contract.md) — 사용자 세션 소스와 수집 소유 계약 | [SPEC-0129](../spec/spec-0129-session-source-lifecycle-contract.md) | [RUN-167](../run/run-20261018-167-session-source-lifecycle-contract.md) |
| [FEAT-0130](../feature/feat-0130-search-availability-contract.md) — 모델 선택 검색 계약 | [SPEC-0130](../spec/spec-0130-search-availability-contract.md) | [RUN-168](../run/run-20261018-168-search-availability-contract.md) |
| [FEAT-0131](../feature/feat-0131-standalone-macos-runtime.md) — Tauri 독립 실행 앱 | [SPEC-0131](../spec/spec-0131-standalone-macos-runtime.md) | [RUN-169](../run/run-20261018-169-standalone-macos-runtime.md) |
| [FEAT-0132](../feature/feat-0132-settings-and-product-navigation.md) — 설정 창과 제품 탐색 | [SPEC-0132](../spec/spec-0132-settings-and-product-navigation.md) | [RUN-170](../run/run-20261018-170-settings-and-product-navigation.md) |
| [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md) — 사용자 소스 설정 | [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md) | [RUN-171](../run/run-20261018-171-user-managed-source-settings.md) |
| [FEAT-0134](../feature/feat-0134-general-and-project-settings.md) — 일반 설정과 프로젝트 표시 | [SPEC-0134](../spec/spec-0134-general-and-project-settings.md) | [RUN-172](../run/run-20261018-172-general-and-project-settings.md), [RUN-179](../run/run-20261020-179-work-session-project-usage.md), [RUN-180](../run/run-20261020-180-project-copy-removal.md) |
| [FEAT-0135](../feature/feat-0135-model-optional-keyword-search.md) — 모델 없는 통합 검색 | [SPEC-0135](../spec/spec-0135-model-optional-keyword-search.md) | [RUN-173](../run/run-20261018-173-model-optional-keyword-search.md) |
| [FEAT-0136](../feature/feat-0136-optional-search-model-setup.md) — 선택형 검색 모델 설치 | [SPEC-0136](../spec/spec-0136-optional-search-model-setup.md) | [RUN-174](../run/run-20261018-174-optional-search-model-setup.md) |
| [FEAT-0137](../feature/feat-0137-first-run-local-setup.md) — 첫 실행 안내 | [SPEC-0137](../spec/spec-0137-first-run-local-setup.md) | [RUN-175](../run/run-20261018-175-first-run-local-setup.md) |
| [FEAT-0138](../feature/feat-0138-local-storage-recovery.md) — 로컬 저장소 확인과 복구 | [SPEC-0138](../spec/spec-0138-local-storage-recovery.md) | [RUN-176](../run/run-20261018-176-local-storage-recovery.md) |
| [FEAT-0139](../feature/feat-0139-standalone-test-app-delivery.md) — 독립 테스트 앱 전달 | [SPEC-0139](../spec/spec-0139-standalone-test-app-delivery.md) | [RUN-177](../run/run-20261018-177-standalone-test-app-delivery.md) |
| [FEAT-0140](../feature/feat-0140-periodic-local-session-sync.md) — 공통 10분 세션 동기화 | [SPEC-0140](../spec/spec-0140-periodic-local-session-sync.md) | [RUN-178](../run/run-20261018-178-periodic-local-session-sync.md) |

The estimate remains 13 Features / 21 commits; it is not a record of created Git
commits. Pre-existing learning/schema/workflow changes were preserved. Program
upload, teammate messages, public Git publication and paid signing were not performed.

## Initial Directly Observed Local Checks

- Environment: Apple Silicon, macOS 26.5.1, 64 GiB RAM. The declared minimum is
  macOS 14; every bundled Mach-O deployment target is at most 14.0. This is not an
  execution test on macOS 14 or on a smaller-memory Mac.
- `scripts/build-desktop.py`: bundled Python 3.11.15, Tauri 2, arm64 `.app`, ad-hoc
  signing, deep strict codesign verification, ZIP, SHA-256 and upstream notices.
- The actual packaged native executable, launched outside the checkout with only
  system tools on PATH and a synthetic data directory, produced a visible
  window (initial observation 1280×850; final relocated ZIP run 1152×766) and its own random loopback backend. A second instance returned to the
  first; a macOS application quit request exited it and reaped the owned backend.
- The final ZIP was extracted to a separate path containing spaces. The relocated
  native app repeated window/single-instance/quit checks with system-only PATH;
  the relocated frozen backend repeated its route/authentication/parent-loss checks.
  This is a local transport check, not an internal Drive or recipient Gatekeeper test.
- Frozen backend requests: admitted health/onboarding/settings/Sessions/Context,
  rejected Workstreams/Auto Work/Atlassian/Insights/workflow, required per-launch
  authentication, and exited normally after its parent pipe closed. Browser
  cross-origin mutation requests returned 403.
- Fresh Chrome profile: first automatic collection, two custom Session profiles,
  Context registration, manual collection, keyword search over two Sessions plus
  one document, confirmed reconnection with stable Session IDs, overlap refusal
  with input retained, disabled-source search exclusion and backup download.
- The final frozen backend retained incomplete onboarding across restarts, restored
  the same installation backup only after restart, applied its saved startup screen
  and interval, and retained a pre-restore recovery copy. Clearing its owned private
  search cache rebuilt a working index while preserving original files/public weights.
- UI checks: 320/390/1280 widths without outer overflow, no JavaScript page errors,
  settings shortcut/Escape, preserved input/focus during collection, explicit
  result refresh, Project labels, selected time zone, List/Chart/Projects/Dashboard/
  Context/search routes and keyword evidence return retaining query and mode.
- The public pinned embedding weights downloaded into an isolated empty cache.
  Cancellation and a deliberately retained partial download were followed by
  verified resume, model registration, a one-Session/one-fragment index, an AI
  query and normal backend exit. A separate existing-cache run used offline mode.
  Private text was synthetic and inference stayed local. This establishes execution,
  not general retrieval quality over real corpora.
- A synthetic 1,000-file benchmark (one short user event per file) imported 1,000
  files in 0.591 s; the unchanged pass took 0.047 s, reported 1,000 unchanged and
  imported zero. Process peak RSS was about 36.6 MiB. This is not representative
  of long conversations, large existing indexes or slow/external volumes.
- Native shell/backend sampled idle RSS totaled about 186–191 MiB; the synthetic
  download/index/query run peaked at about 2.70 GiB of summed backend/worker RSS.
  These are process observations, not whole-system/GPU measurements or minimum
  memory recommendations.
- The isolated public model cache occupied 1,207,470,234 bytes. The one-fragment
  private index/status used about 62 KB and reported about 62 KB peak index disk
  usage. Larger corpora need additional index and temporary space.

## Initial Automated Checks

- Full suite: **1,172 tests; 1,168 passed, four failures, no errors**.
- New settings/lifecycle/recovery contracts: 20 passed. Existing source/sync tests:
  55 passed; natural-search tests: 41 passed. These counts are subsets of the suite.
- JavaScript syntax checks, Python compilation, Rust release build and
  `git diff --check` passed. Repository privacy checking passed.
- Bundle inventory contains packaged code/assets/public dependencies and their
  notices; no personal runtime DB, Session JSONL, settings, model weights, private
  index or credentials. Bundled `certifi/cacert.pem` is the public CA bundle,
  not a private certificate or user credential. All resource symlinks stay in the app.

The four suite failures concern pre-existing learning additions: missing owner
inventory for `learning_attempts`, `learning_lessons`, `learning_visibility`, stale
schema/audit totals (48 vs 45 tables; 49 vs 46 audit entries), and value-family
count 87 vs 81. They occur in `test_data_model_docs`, two `test_schema_cleanup_audit`
checks and `test_value_registry`. This implementation introduced no new business
DB tables and does not rewrite the unrelated learning work to make those pass.

## Corrections Made During Verification

- Added missing frozen renderer data and corrected ad-hoc Python signing so the
  bundled interpreter loads its libraries without a paid signing identity.
- Kept removed sources explicitly disabled, preserved identity on re-enable,
  and coalesced manual requests with another backend's intervening completion.
- Extended saved Project/time-zone display through Chart/pins/Dashboard without
  changing frozen attribution or source identity.
- Kept TLS verification while using the Mac's trust store in the isolated download
  worker; the original certificate failure on the managed network was reproduced.
- Replaced buffered-stdin parent watching with raw-descriptor reading: successful
  worker exit no longer aborts Python finalization, while parent loss still stops
  a download. Both paths have regression tests.
- Cache cleanup checks the index owner and database binding, including interrupted
  owned build files; unknown ownership preserves the file and reports the failure.

## Evidence Gaps And Acceptance Impact

| Gap | Owner | Impact |
| --- | --- | --- |
| A teammate downloads this exact ZIP from internal Drive and runs it on another Apple Silicon Mac | PRD A12 / FEAT-0139 | Blocking complete distribution acceptance; upload/receipt are external follow-up |
| Actual red-close/Dock reopen, ⌘, and native chooser interaction | PRD A04/A06, UI evidence rule | Native interaction acceptance remains open. The repair adds a synthetic WKWebView snapshot and owner confirmation of the actual app's first screen; these do not exercise the remaining controls. No system permissions were changed |
| Notes permission grant/denial/revocation and Spotlight PDF extraction on the recipient Mac | PRD A12 / FEAT-0133/0139 | Manual recipient confirmation; existing adapter behavior is retained, not newly certified |
| macOS 14 execution, physical sleep/wake, low-memory hardware and large personal corpus | PRD A04/A12/A14 | No compatibility/performance guarantee; scheduler logic and small synthetic execution are the checked scopes |
| Learning schema/catalog failures | Existing learning track | Full repository suite is not green; current test app excludes learning |

## Initial Artifact — 2026-10-19 (Superseded)

- Local output: `dist/LocalBrain-apple-silicon.zip`, its sibling `.sha256`, and the
  extracted `dist/LocalBrain-apple-silicon/LocalBrain.app`.
- Version: 0.2.0. ZIP: 264380190 bytes (252.13 MiB).
- ZIP SHA-256: `ed171643c12e5b3960ec319ea4dca37ad457ad2813c4381d6a2ec03bfb29bb06`.
- Final ZIP CRC, file bytes, executable modes and symlink targets match the
  app exercised from the separate extraction. Its `BUILD-INFO.md` records the
  app inventory and executable hashes; `THIRD-PARTY-NOTICES.txt` includes Python
  interpreter and packaged dependency notices. Deep strict codesign verification passed.
- Final repository privacy scan: 1,409 candidate files passed. Task-owner document
  link targets (48 documents), generated catalog freshness and diff whitespace passed.
- Temporary tools, synthetic fixtures, caches, screenshots, logs, generated Tauri
  schemas and intermediate build products were removed after the owned processes
  stopped. The final app/ZIP/checksum/notices and source documents remain; no
  durable artifact depends on a temporary path.

## Startup Repair Artifact — 2026-10-19 (Superseded By Display Cleanup)

- Local output remains `dist/LocalBrain-apple-silicon.zip`, its sibling `.sha256`,
  and `dist/LocalBrain-apple-silicon/LocalBrain.app`, version 0.2.0.
- ZIP: 201606634 bytes (192.27 MiB).
- ZIP SHA-256: `caad45df09a2bcaf6a952b95e4f2ceb4dad12eac7f7dbcb488fecb9f51c2b3df`.
- App inventory SHA-256: `15617fd6d72e5a0ea27b8b6174011c5598436d857be613bd8b35208c58c3ae73`
  (4,710 regular files). The smaller ZIP preserves 28 internal PyInstaller
  relative symlinks instead of duplicating their targets; each target stays
  inside the app and matches the previous dependency bytes.
- Final ZIP CRC, every app file's bytes and mode, symlinks and bundled launch
  guide were verified. Deep strict codesign verification passed after extracting
  the final ZIP to a separate location.
- Repository privacy check passed for 1,412 candidate files.
- Repair owner-document links, generated catalog freshness and diff whitespace
  passed. The synthetic server was stopped and task-owned temporary build tools,
  fixtures, caches, diagnostics, extraction and rollback copies were removed.
  The confirmed working app remains running; final delivery files remain in `dist/`.

## Sync Display Cleanup Artifact — 2026-10-19 (Superseded)

- The owner requested removal of the common automatic-sync strip and
  updated-records link. The three shared template/assets were updated in source
  and the app; the repaired frozen backend, schedule and user data/settings remain.
- Local output: `dist/LocalBrain-apple-silicon/LocalBrain.app`,
  `dist/LocalBrain-apple-silicon.zip` and its sibling `.sha256`, version 0.2.0.
- ZIP: 201606687 bytes (192.27 MiB).
- ZIP SHA-256: `cd584caa2d6fa3f009299868e39f3aa79eb29336d7360fc49026deca633d1f33`.
- App inventory SHA-256: `a577404c3d0794fbb039f99e398e161167ccd359408df13e55f4dc4922bdde0a`
  (4,710 regular files; relative dependency symlinks preserved).
- Relevant tests: 42 UI contract + 20 settings/lifecycle + 24 sync tests passed;
  JavaScript syntax passed. This change did not rerun the full suite; its last
  observed four unrelated failures remain recorded above.
- Synthetic WKWebView checks and snapshots cover Sessions at requested 1100/320
  widths, Sessions Dashboard and Context. Twelve checks per run passed, including
  no strip/link or residual strip space, default ten-minute scheduling settings,
  dialog behavior and live running/completed controls using synthetic status
  responses. The Sessions manual action and retained query also passed.
- The actual user app was gracefully replaced and relaunched. Its authenticated
  local responses confirm health, absent strip/link, manual/settings controls and
  the refreshed script. This is distinct from the synthetic rendered checks;
  no new owner visual confirmation or teammate observation was collected.
- Final ZIP CRC, all inventory bytes/modes/symlinks, guide/build/notices content
  and deep strict signing after extraction passed. Privacy check passed for
  1,412 candidate files; catalog freshness and diff whitespace passed.
- Owned temporary tools, synthetic stores, snapshots, extracted copies and the
  previous delivery were removed after all checks stopped. The updated user app
  remains running; final app/ZIP/checksum and durable records remain.

## General Settings Selection Artifact — 2026-10-19 (Superseded)

- The agent interpreted the request as direct startup selection, selectable
  time zones and an explanation of their effect. The owner subsequently corrected
  the control type; the dropdown correction below supersedes that interpretation. Only `_settings.html`, `settings.js` and
  `settings.css` changed in the app; the frozen backend, native implementation,
  previous startup/authentication fix and user settings/data were retained.
- Local output remains `dist/LocalBrain-apple-silicon/LocalBrain.app`,
  `dist/LocalBrain-apple-silicon.zip` and its sibling `.sha256`, version 0.2.0.
- ZIP: 201609669 bytes (192.27 MiB).
- ZIP SHA-256: `434bd8263cc16b9d545cb9819e28fbcb9e6b839204edcf53743027074472dd6f`.
- App inventory SHA-256: `5146765c7548281017dc0ffa1d2ec7f49837d2344b8e0bc0b17916fb1c90c9d5`
  (4,710 regular files; dependency symlinks retained).
- Related tests: 43 UI contract, 20 settings/lifecycle and 15 Usage dashboard
  tests passed, including a UTC/Seoul date-boundary regression with unchanged
  stored Usage rows. JavaScript syntax passed. No fresh full-suite result is
  claimed; the prior unrelated failures remain as recorded above.
- Synthetic WKWebView: sixteen checks at requested 1100/320 widths and eight
  fallback/error checks passed. Direct startup choices, in-flow bounded time-zone
  search, no-match retention, saved aliases, pending versus saved values, real
  API save, completed dialog reload and synthetic save-failure retention were
  exercised. Expanded/closed screenshots were inspected. Search-result height
  shrinks for short lists and does not overlay adjacent fields.
- The actual user app was replaced and relaunched. Authenticated loopback reads
  confirm health, the new markup and current script; the private response body
  and per-launch token were not printed. This is distinct from the synthetic
  rendering evidence and does not claim a new owner visual confirmation.
- ZIP CRC, every inventory byte/mode/symlink, guide/build/notices content and
  deep strict signing after separate extraction passed. Privacy check passed
  for 1,412 candidate files; catalog freshness and diff whitespace passed.
- The [general-settings Run](../run/run-20261018-172-general-and-project-settings.md)
  owns the UI scope, time-zone explanation, tests and remaining evidence limits.
- Task-owned tools, fixtures, screenshots, extracted copies and the prior app
  were removed after all verification processes exited. The updated user app
  remains running; final delivery files remain in `dist/`.

## Corrected Settings Dropdowns Artifact — 2026-10-19 (Superseded)

- The owner corrected the startup interaction: restore the dropdown and evaluate
  the expanded menu below its selected control. Time zone now has exactly `UTC`
  and `Asia/Seoul`. The prior radio/search interpretation is superseded.
- Output remains `dist/LocalBrain-apple-silicon/LocalBrain.app`,
  `dist/LocalBrain-apple-silicon.zip` and its sibling `.sha256`, version 0.2.0.
- ZIP: 201609485 bytes; SHA-256:
  `39b963f8466b44e0f372be50807eba05ff72c089995b27b6eb51e08db7ec9ceb`.
- App inventory SHA-256:
  `df607aa21b231eb84257ded09d0f5e20080254bfa8f9f1ec335bb950682e7d91`
  (4,710 regular files; 28 relative dependency symlinks).
- Changed bundled files: `_settings.html`, `settings.js`, `settings.css`; existing
  backend/native implementation and user preferences/data were preserved.
- Related tests: 43 UI contract, 20 desktop settings and 15 Usage dashboard tests
  passed. JavaScript syntax, catalog freshness, diff whitespace and privacy check
  (1,412 candidate files) passed. No new full-suite result is claimed.
- Four synthetic WKWebView runs passed 24 checks each at measured 1100/320 widths.
  Both expanded menus were inspected. Below-trigger position, equal width,
  unobscured trigger, containment, all startup choices, two literal zone labels,
  one open menu, selection/dismissal, scripted keyboard handling, real API save
  and dialog reopen, simulated failure retention and existing non-listed-zone
  preservation passed. Keyboard events were scripted; VoiceOver and physical
  keyboard operation were not observed. The
  [general-settings Run](../run/run-20261018-172-general-and-project-settings.md)
  and [design evaluation](eval-0139-design-standalone-test-app.md) own the detail.
- The actual user app was gracefully replaced and relaunched at the same path.
  Authenticated loopback reads passed health and current dropdown markup;
  served JavaScript/CSS match the shared source. Tokens/private content were
  not printed. This does not claim a new owner visual confirmation.
- ZIP CRC, every manifest file byte/mode/symlink, guide/build/notices identity
  and deep strict signature verification after separate extraction passed.
  No model weights were downloaded and no upload/publication occurred.
- Task-owned probes, fixtures, screenshots, extracted copy and replaced-app
  backup were removed after verification processes exited. The updated user
  app remains running; final artifacts remain in `dist/`.

## Four Compact Dropdowns Artifact — 2026-10-19 (Superseded)

- Owner follow-up: Project display and Automatic sync use the same dropdown as
  Startup and Time zone. All four boxes share a compact maximum width of 320px
  at the default scale and shrink within narrower panes; menu width matches.
- Output remains `dist/LocalBrain-apple-silicon/LocalBrain.app`,
  `dist/LocalBrain-apple-silicon.zip` and its sibling `.sha256`, version 0.2.0.
- ZIP: 201610058 bytes; SHA-256:
  `72ff5cf61c378aab86cb89b4667bf79f0b89c4aa732d4c2964f257b521c2b096`.
- App inventory SHA-256:
  `189efc314dc6676b25965b15c683e4f25f6a428d474552421f6255bdd78c892a`
  (4,710 regular files; 28 relative dependency symlinks).
- Bundled changes are `_settings.html`, `settings.js`, `settings.css`; backend
  and native implementations are retained. Saved sync values load before the
  four dropdown displays refresh. Submitted values and save timing are unchanged.
- Related tests passed: 43 UI contract, 20 desktop settings, 24 session sync
  (87 total). JavaScript syntax, catalog freshness, diff whitespace and privacy
  check (1,412 candidate files) passed. Full suite was not rerun.
- Six frozen-backend/WKWebView runs passed 22 checks each at measured 1100/320
  widths. Closed screens and open Project display/Sync menus were inspected.
  Every option in all four controls passed placement/selection; equal compact
  widths, containment, Escape, scripted keyboard choice, one-open-menu/outside
  dismissal, actual save/reopen, non-default/off labels, off preserving the
  interval, re-enable and simulated failure retention passed. No model downloaded.
- The actual app was gracefully replaced and relaunched. Authenticated health,
  four-dropdown markup and served JavaScript/CSS matching the shared source
  passed. No real user preference was changed by the synthetic fixtures, and
  no private response content or per-launch token was printed.
- ZIP CRC, all inventory bytes/modes/symlinks, guide/build/notices identity and
  deep strict signature verification after independent extraction passed.
- Task-owned probes, synthetic data, screenshots, extracted app and prior-app
  backup were removed after verification processes exited. The updated app
  remains running; final app/ZIP/checksum remain in `dist/`.
- The [general-settings Run](../run/run-20261018-172-general-and-project-settings.md)
  and [design evaluation](eval-0139-design-standalone-test-app.md) own detailed
  scope. Scripted keyboard checks do not establish VoiceOver or physical-key
  acceptance; unrelated native and teammate gaps retain their prior status.

## Route

Use the [current test artifact](#pin-order-and-palette-focus-delivery--2026-10-26-current). The original startup-failing ZIP is superseded. Full product
acceptance stays open until the native interaction and teammate receipt are
recorded. Use the [test app guide](../../policies/project/standalone-test-app-guide.md)
for the exact launch, update, local-data and same-installation recovery boundaries.
No statement here authorizes an upload or a teammate message.

- `2026-10-19` owner confirmation: after replacement and relaunch at the same path,
  the owner confirmed “정상 화면이 보여요”. This confirms the actual Tauri app
  landing on this Mac. It does not close the other native-control or teammate
  acceptance gaps.

## Fixed Home Display Delivery — 2026-10-19 (Previous)

This supersedes the four-compact-dropdowns artifact above. [C07's Run](../run/run-20261018-172-general-and-project-settings.md#fixed-home-display--2026-10-19)
owns the correction and test/probe details. The current version remains 0.2.0.

- Local app: `dist/LocalBrain-apple-silicon/LocalBrain.app`; ZIP and checksum remain
  `dist/LocalBrain-apple-silicon.zip` and `.sha256`.
- ZIP: 201609499 bytes; SHA-256:
  `2f8d34a6a0d385da55bc6872e34ec6e36a5d565ea526d64dfe39638629030006`.
- App regular bytes: 576461782; 4710 regular files, 28 relative symlinks.
- App inventory SHA-256: `deda87d0f4c6c08cccd1244ed857d984544ee7233ceff5a114eb5533e3b99df5`.
  Sorted path entries; file path/mode/sha256 or link path/target; compact UTF-8
  JSON, `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256: `dfb62e37a61fc1f144755a5a07c985f352a6f49c931b65307756207fc5388780`.
- Backend SHA-256: `c6bcfecae36cee7c79c598caf89072569d160adddd555f8bdf3909c7d36e7e0c`.
- Rebuilt frozen Python/resources; existing native host reused and re-signed.
  Full-build fallback followed unavailable cargo. No Rust/source API change or
  model download. Source and bundled template/JS/CSS bytes match.
- Final related tests: 173 pass, plus 25 settings tests after synthetic placeholder
  cleanup. Initial access-time-only sync comparison failed once and passed on
  unchanged module/combined reruns. The full suite was not rerun.
- Five source/web/frozen WKWebView runs passed 23 behavior/layout conditions each
  with measured 320px/253px control widths; fixture corrections and visual bounds
  are detailed in C07. No user preferences were used for the synthetic writes.
- The published native app was opened and passed authenticated health, active
  settings without retired fields, exactly three controls, removed editor markup
  and fresh JS/CSS equality. User settings and Session-source file hashes stayed
  unchanged. UI scripting does not establish physical keyboard/VoiceOver checks.
- Final ZIP CRC, every file byte/mode/link and guide/build/notices identity passed.
  The extracted app passed deep strict codesign verification. No runtime DB,
  JSONL or log files occur in the packaged LocalBrain resources.

Other-Mac download/Gatekeeper, minimum OS, native chooser, physical sleep and
optional-model behavior on this newly rebuilt backend are not newly verified.
Earlier observations remain historical and the overall acceptance result above
is unchanged. No Drive upload, teammate message or Git publication was performed.

Temporary synthetic servers were stopped. Task-owned build tools, npm staging,
fixtures, screenshots, extracted/recovery copies and private scratch were removed.
The published app remains running from `dist`; final deep strict codesign and
ZIP checksum checks passed after cleanup.


## Project Usage Label Delivery — 2026-10-19 (Previous)

This supersedes the fixed-home-display artifact above. Version remains 0.2.0.
[C07's Run](../run/run-20261018-172-general-and-project-settings.md#unassigned-usage-labels--2026-10-19)
owns the bounded correction; frozen attribution and the wider acceptance boundary remain.

- Local app: `dist/LocalBrain-apple-silicon/LocalBrain.app`; ZIP and checksum:
  `dist/LocalBrain-apple-silicon.zip` and `.sha256`.
- ZIP: 201608256 bytes; SHA-256: `68a6cf347e7900b6abda4218d6519e7a7699eef29c988145b4c465c1a84e3177`.
- App regular bytes: 576462006; 4710 regular files, 28 relative symlinks.
- App inventory SHA-256: `2e2f1f89fdc887d5faeb60622421af550d2ea209c5464791b398bc696381285f`.
  Sorted relative entries, file path/mode/sha256 or link path/target, compact UTF-8
  JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256: `07dfaff38273e8e9885a94e90edcd606c0a65cb2e157d35f02afba8b7e3061d2`.
- Backend SHA-256: `bc79fe204ffb184ea1be47bf75a095a0134e351034e6a327437e327d9a039575`.
- Frozen Python/resources rebuilt with PyInstaller 6.22.3; existing Tauri host reused
  and bundle re-signed. Rust/cargo and model downloads were not needed.
- 99 related tests passed. Six post-change source/web/frozen WKWebView runs passed
  16 conditions each at measured 1100/320 widths; two original-build baselines
  reproduced the old merged category. Category switches, source filters, both
  metrics, dates, stable summary/shell and bounded table scrolling passed.
- ZIP CRC, all file bytes/modes/links, guide/build/notices identity and extracted-app
  deep strict signature passed. Bundled templates/assets match current source;
  packaged LocalBrain resources contain no runtime databases, JSONL or logs.
- Actual app replaced and relaunched. Authenticated health/new category/current
  asset responses passed; original settings/source-file hashes and the retained
  previously-unassigned Usage rows were unchanged. No real settings were edited
  by synthetic verification. Only query presentation classifies the records.

Scoped functional PASS. No full-suite, optional-model, physical keyboard/VoiceOver,
other-Mac, minimum-OS or broad native acceptance rerun is claimed. The product's
remaining recipient/native evidence gaps are unchanged. No upload or Git publication.

Task-owned temporary artifacts are removed and all synthetic servers have exited.
The updated app remains running from `dist`; final deep strict codesign and ZIP
checksum verification passed.

## File Preferences Delivery — 2026-10-19 (Previous)

This supersedes the Project Usage Label artifact above. Version remains 0.2.0.
[C07's Run](../run/run-20261018-172-general-and-project-settings.md#file-owned-general-settings--2026-10-19)
owns the correction: general preferences follow the local settings file, missing
fields use defaults, and the former environment override/UI explanation is removed.

- Local app: `dist/LocalBrain-apple-silicon/LocalBrain.app`; ZIP and checksum:
  `dist/LocalBrain-apple-silicon.zip` and `.sha256`.
- ZIP: 201608871 bytes; SHA-256: `65a97278a9ce49850452d7efc28a0a5c409843292420e63f355058fc6ea60d44`.
- App regular bytes: 576460407; 4710 regular files, 28 relative symlinks.
- App inventory SHA-256: `5139c5a24648dd312833dfba302ac36dd00ddf938ff139b55839ba36d1ee4c41`.
  Sorted relative entries, file path/mode/sha256 or link path/target, compact UTF-8
  JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256: `2d0328c483d283d7b3967129aa39f7a0117e020dd7e2f53fdcdc284c70eeaef0`.
- Backend SHA-256: `ac45818e76008e92b59e77044e549beee15810b5dfe6256531f0a92ef601278b`.
- Python/resources rebuilt with PyInstaller 6.22.3; existing Tauri host reused and
  re-signed ad hoc. No native source change or new Rust build. No model download.
- **131 related tests passed**; focused settings tests: 28 pass. Two original
  frozen-backend WKWebView baselines passed eight expected-old checks each.
  Six final source-desktop/web/frozen-backend runs at measured 1100/320 widths
  passed 20 checks each. Actual file values, save/reopen/runtime application,
  conflict-error recovery, removal and layout checks are detailed in C07.
- Source and frozen processes restarted with conflicting old environment variables
  retained saved startup/time-zone/sync values, correct runtime/route behavior and
  the preserved unknown TOML field. Synthetic fixtures never changed real settings.
- ZIP CRC, every packaged byte/mode/link, guide/build/notices identity and source
  asset equality passed. Extracted-app deep strict signature passed. Packaged
  LocalBrain resources contain no runtime databases, JSONL or logs.
- Actual app replaced and relaunched. Authenticated health, three-control markup,
  short help, removed override rows and current asset bytes passed. Existing real
  settings/source-file hashes and saved preferences were identical. API saved and
  effective values match; sources contain only saved/default.
- Final installed-app deep strict codesign and ZIP checksum checks passed.

Scoped functional PASS. No full-suite, optional-model, physical keyboard/VoiceOver,
other-Mac, minimum-OS or broad native acceptance rerun is claimed. The product's
remaining recipient/native evidence gaps are unchanged. No upload or Git publication.

Privacy check passed for 1413 candidate files; catalog freshness, JavaScript syntax,
diff whitespace and changed owner-document local link targets passed. All synthetic
servers exited and task-owned tools, fixtures, probes, screenshots, extracted builds
and recovery copies were removed after checking active use. The updated native app
remains running from `dist`.

### First-Startup Confirmation — 2026-10-19

The owner confirmed automatic default-file creation on first launch and subsequent
saved-file precedence. This behavior already exists in the shared application
lifecycle; no application code, native host or distribution artifact changed.

Two added regression tests passed across twelve independent app/web lifecycle
processes, and all 28 existing settings tests passed (30 tests total). The existing
frozen backend was independently started three times against synthetic private
data. Authenticated HTTP checks passed fresh `settings.toml` creation with schema
and defaults, private permissions, empty source registrations, API save, runtime
sync values, unchanged saved/unknown values after restart, and malformed-file error
preservation. Conflicting retired environment variables did not alter preferences.
Creation occurred before onboarding or a settings-screen save.

The [foundation Run](../run/run-20261018-166-local-settings-contract.md#first-startup-confirmation--2026-10-19)
owns exact scope. All synthetic processes exited and temporary data/logs were removed;
real user data and the running user app were untouched. No model download, new
native-shell/other-Mac evidence, upload or publication. Existing delivery hashes and
the wider acceptance boundary remain unchanged.

## Sync Label Delivery — 2026-10-19 (Previous)

The settings field and interval/off status use `동기화` without `자동`. Version
remains 0.2.0. Only the shared template/JavaScript and guide changed in the app;
the existing Tauri host was re-signed ad hoc and the Python backend is unchanged.

- App: `dist/LocalBrain-apple-silicon/LocalBrain.app`; ZIP/checksum remain siblings
  `dist/LocalBrain-apple-silicon.zip` and `.sha256`.
- ZIP: 201609396 bytes; SHA-256: `c618dc75c8a27e174bd87ef6029f73d7b03b49c29fd5bbf25be7b67f88cfe1ca`.
- App regular bytes: 576460386; 4710 regular files, 28 relative symlinks.
- Inventory SHA-256: `c10f9e11ca5d262239c53203056f8d17c8b67cbf02990fe4770990cd3c5ec203`.
  Sorted relative file path/mode/sha256 or link path/target entries; compact UTF-8
  JSON, `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256: `93071dc75708a20443a102fae9986ccfb356c58d6c9b29f38059cc6afcc140cb`.
- Backend SHA-256: `ac45818e76008e92b59e77044e549beee15810b5dfe6256531f0a92ef601278b`.
- The focused general-settings UI test and JavaScript syntax passed. One original
  1100px and two updated 1100/320px WKWebView runs passed 11 checks each; before/after
  screenshots were inspected. Field/status copy, manual availability, options,
  pending values, menu geometry, containment and unchanged preferences passed.
- ZIP CRC, packaged file bytes/modes/links and separately extracted-app deep strict
  signature passed. Shared settings resources match source. No model download.
- Actual app replaced and reopened. Authenticated health, new label, matching
  JavaScript and unchanged saved preferences/settings-source file hashes passed.

Scoped design/functional PASS. The [Run](../run/run-20261018-172-general-and-project-settings.md#sync-wording--2026-10-19)
records the probe correction and evidence scope. No full-suite, physical-input,
other-Mac or whole-product acceptance rerun is claimed. Broader gaps remain.

Final privacy check (1414 candidates), catalog freshness, diff whitespace, installed
app signature and ZIP checksum passed. All synthetic processes exited; task-owned
probes, data, screenshots, staged/extracted builds and recovery copies were removed
after an active-use check. The updated app remains running; no external publication.

## Compact Settings Delivery — 2026-10-19 (Previous)

Settings now has a maximum 720×560 CSS-pixel surface with a 160px desktop category
rail, fixed header/close, scrolling content and a shared 700px breakpoint. Category
changes retain pending values and reset scroll; save/error feedback becomes visible.
Version remains 0.2.0. Shared CSS/JavaScript and the guide changed; the existing
native host was re-signed ad hoc, with no Python/Rust rebuild or model download.

- App: `dist/LocalBrain-apple-silicon/LocalBrain.app`; ZIP/checksum remain siblings
  `dist/LocalBrain-apple-silicon.zip` and `.sha256`.
- ZIP: 201610025 bytes; SHA-256: `1353542f0a3495e40ebda7e6793ba5aa29ec2207aab2ccb6725f55877a81e922`.
- App regular bytes: 576460890; 4710 regular files, 28 relative symlinks.
- Inventory SHA-256: `55bd9f1326886927dd6bbd00a0aecb109289796a106e9fd57fb728cca361c2d1`.
  Sorted relative file path/mode/sha256 or link path/target entries; compact UTF-8
  JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256: `2728911350f3833e9b2e74ff6ab6125862b2c80854b028fd8df2b0353844008a`.
- Backend SHA-256: `ac45818e76008e92b59e77044e549beee15810b5dfe6256531f0a92ef601278b`.
- Two focused UI contract tests and JavaScript syntax passed. One original
  WKWebView baseline confirmed 992×800. Four frozen-backend runs at 1440×900,
  900×450, 700×650 and 320×650 plus ordinary web at 1100×800 passed 23 checks each.
  All categories, scroll/menu containment, pending/save/reopen, focus return and
  conflict-error visibility/input retention/retry passed. Before/after screenshots
  were inspected. The [settings-shell Run](../run/run-20261018-170-settings-and-product-navigation.md#compact-settings-dialog--2026-10-19)
  records the feedback fix, probe corrections and exact evidence limits.
- ZIP CRC, every packaged file byte/mode/link and separately extracted-app deep
  strict signature passed. The bundled guide and shared assets match source.
- Actual app replaced and relaunched. Authenticated health, three-control markup,
  CSS/JavaScript bytes and unchanged saved preferences/settings-source file hashes
  passed. The native probe initially used a nonexistent `/health` route; rerunning
  against the application's `/api/health` passed before and after replacement.
- Final installed-app deep strict signature and ZIP checksum passed.

Scoped design/functional PASS. No full-suite, optional-model, physical-keyboard,
VoiceOver, other-Mac, minimum-OS or broad native acceptance rerun is claimed.
Broader recipient/native evidence gaps remain; no upload or Git publication.

Catalog freshness, diff whitespace and changed owner-document local link targets
passed. All synthetic processes exited; task-owned tools, fixtures, screenshots,
staged/extracted builds and recovery copies were removed after an active-use
check. The updated app remains running from `dist`.

## Work Session Project Delivery — 2026-10-20 (Previous)

[Run 179](../run/run-20261020-179-work-session-project-usage.md) applies the owner's
work-only Project decision, superseding the app-analysis Project category. Labels
remain By Project / Project. Work subsessions and home/folder grouping remain;
Project values/shares exclude all Maintenance, while overall/history/Source/Model
retain its usage. Frozen attribution and stored Usage are preserved.

- 118 related tests passed: Usage dashboard, personal-insight accounting, UI contracts,
  desktop boundary/settings, preferences startup and schema presentation. Full suite
  and optional-model execution were not rerun; earlier failures retain their scope.
- Ordinary web at 1100/320 and final frozen backend at 1440/920/700/320 each passed
  18 scripted checks: names, home/unknown identities, totals, costs, work-subsession
  inclusion, shares, source/model preservation, exact-source filtering, maintenance-only
  empty state, date retention, settings open/close, restored All and edition navigation.
  Table frame/page containment passed; before/after wide/narrow captures were inspected.
- Two original-build baseline runs at 1100/320 established the prior combined grouping.
  The first staging copy hit a Finder metadata restriction; the incomplete copy still
  used the old backend and correctly failed new-scope checks. A fresh task-owned copy
  excluding Finder metadata, with verified source/assets, passed the final checks.
- Backend rebuilt offline with cached PyInstaller 6.22.3, Python 3.11.15 and existing
  dependencies. Bundled distribution metadata versions match the previous app. No
  model weights were downloaded. Existing Tauri host reused and re-signed ad hoc.
- ZIP CRC, every app file byte/permission mode/link, extracted inventory and deep
  strict codesign passed. Source templates/CSS/settings assets/manifest match the
  bundle. The current guide and existing dependency notices are included.
- App: `dist/LocalBrain-apple-silicon/LocalBrain.app`; ZIP/checksum remain
  `dist/LocalBrain-apple-silicon.zip` and `.sha256`.
- ZIP: 259597583 bytes; SHA-256: `ad179a4d86f691620b2ae5ceb2319ff7213dd90a3596d9824e9ffa5d11248f53`.
- App regular bytes: 841509105; 4717 regular files, 0 symlinks.
- Inventory SHA-256: `8507482419db24db670df53f1b42f134c95f3b097105f996be9586a4d93dc9a5`.
  Sorted relative file path/integer permission mode/sha256 or link path/target;
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256: `3f74fb2a62478da44f56af9ef2066273c39dabc78855b8cc07dd44f0b09ca575`.
- Backend SHA-256: `59867083b9b24e7ce68cc11ff67d7a8af696c7d2897ad24f6b23eefaaed565c0`.

Actual native post-replacement and final cleanup checks are recorded in Run 179.
Scoped functional/design PASS does not close the broader native controls, physical
input, VoiceOver, minimum-OS or teammate-Mac acceptance gaps. No upload/publication.

## Project Notice Removal Delivery — 2026-10-20 (Superseded Artifact)

[Run 180](../run/run-20261020-180-project-copy-removal.md) removes the owner-rejected
Project scope/total paragraph and its CSS spacing. The table directly follows the
heading and controls. By Project / Project, data membership, row values, shares,
empty state and settings remain unchanged. Only the shared template/CSS assets
were replaced; no Python/Rust rebuild or model download was needed.

- 44 UI contract and 17 usage tests passed (61 total). The UI contract prevents
  reintroducing the paragraph or separate total into this template.
- Original frozen baseline at 1100/320 and updated ordinary web/frozen backend at
  1100/320 each passed eight scripted checks for notice state, table adjacency,
  labels, values, overall total, containment, composition switching and settings.
  Wide/narrow before/after captures were inspected.
- Ad-hoc signature, ZIP CRC, every app file byte/mode/link, extracted inventory and
  deep strict signature passed. The bundled template and CSS match source.
- App remains `dist/LocalBrain-apple-silicon/LocalBrain.app`; ZIP/checksum are
  `dist/LocalBrain-apple-silicon.zip` and `.sha256`.
- ZIP: 259597845 bytes; SHA-256 `bd47057c6ea3572997267cad0f98cc9cc4520e1f204c9bde5df4cf43574b517a`.
- App regular bytes: 841508600; 4717 files, 0 symlinks.
- Inventory SHA-256 `231a0418c9b5626d7846aa9ba480f4168cd802a945bd078d21a8db97a9c3d0e7`; sorted relative entries with
  file path/integer mode/sha256 or link path/target, compact UTF-8 JSON,
  `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `299819e85ae0aeb2ca863f8d3ef064f03e6abb9e46e77be081845610d78be404`.
- Backend SHA-256 `59867083b9b24e7ce68cc11ff67d7a8af696c7d2897ad24f6b23eefaaed565c0` (unchanged from Run 179).

Actual native post-replacement and cleanup results belong to Run 180. Scoped
functional/design/interaction PASS preserves broader native, physical-input,
VoiceOver, minimum-OS and teammate evidence limits. No full-suite or model rerun.


## Pinned Scroll Containment Delivery — 2026-10-20 (Superseded Artifact)

[Run 181](../run/run-20261020-181-pinned-scroll-containment.md) repairs blank space
below Sessions. The Pinned Sessions scroller now owns the containing block of
its absolutely positioned accessibility labels. Labels, membership, grouping,
spacing, responsive behavior and application data remain. Only CSS was replaced.

- **Result: PASS for this scroll correction. Evidence coverage: scoped.**
- 69 focused tests passed: Session pins, pin UI (including the new containing-block
  regression), inventory and shared UI contract. No full-suite rerun.
- A synthetic 47-pin original frozen screen measured document/shell heights of
  4,148/2,226px. A temporary containing-block rule removed the 1,922px overflow;
  removing the rule restored it. Repeated scrolling did not incrementally load rows.
- Four ordinary-web and five updated frozen-backend WebKit cases passed 138
  targeted checks at 1280/920/700/320px. Cases include zero/five/47 pins, full and
  two-row main lists, label retention, document bounds, repeated end scrolling,
  last-pin access, narrow document flow, pagination links, inventory switching
  and settings open/close. Seven first-page cases additionally verify pin/unpin
  refresh, document/panel scroll and focus preservation, and restored membership.
- Two exploratory fourth-page pin probes timed out during navigation. Code
  inspection indicates the existing full-page fallback in the pin handler;
  these attempts are not passed pin checks. Final fourth-page cases establish
  layout and non-mutation controls only. Paginated pin continuity was neither
  certified nor changed by this CSS correction.
- Synthetic before/after wide, short-main and narrow captures were inspected.
  The actual app backend's document height changed from 2,975 to 2,226px at
  1280×800, equal to its unchanged shell height; eight repeated end scrolls stay
  at that bound. This removes the observed 749px blank overflow.
- The actual native app was gracefully replaced and reopened at
  `dist/LocalBrain-apple-silicon/LocalBrain.app`. Authenticated health and served
  CSS/source equality passed. Saved settings and source-registry file hashes
  were preserved. Measurements used WebKit against the running app backend;
  physical trackpad/VoiceOver and unrelated native/teammate checks remain separate.
- Ad-hoc deep strict signature, ZIP CRC, every app file's bytes/mode/link,
  extracted inventory/signature and installed ZIP checksum passed.
- ZIP: 259598257 bytes; SHA-256 `549437e432601024b06e832864f1e651e2921ba0099c14fe55ae9965f2c8182e`.
- App: 841508697 regular bytes, 4717 files, 0 symlinks.
- Inventory SHA-256 `f9d3e7f6bcc9860db1477ecf50dd7bcff874c4940e4fda51c979f495c6b9c2a8`; sorted relative file
  path/integer mode/sha256 or link path/target; compact UTF-8 JSON,
  `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `fe570d88ed402a8f29ce95dd7ac391b0ba4bf156269d3acb1225d4bcec6ee923`.
- Backend SHA-256 `59867083b9b24e7ce68cc11ff67d7a8af696c7d2897ad24f6b23eefaaed565c0` (unchanged).

No Python/Rust rebuild, model download, upload or publication. App/ZIP/checksum
paths remain unchanged. This section supersedes the prior artifact identity;
it does not close broader standalone acceptance gaps.

## Portable Python Metadata Delivery — 2026-10-20 (Superseded Artifact)

[Run 182](../run/run-20261020-182-portable-python-build-metadata.md) removes the
builder's private interpreter prefix from compressed sysconfig metadata. Python
installation paths now derive from the running bundle location. User data and
settings continue to use the current user's home independently of the app location.

- **Result: PASS for the metadata/privacy correction. Evidence coverage: scoped.**
- 42 focused tests passed: six build-metadata/privacy tests plus desktop boundary,
  settings and startup-preference tests. No full-suite rerun. An initial test
  fixture placed a private constant after an unconditional raise, so Python
  eliminated it; moving the assignment before the raise corrected the fixture.
- PyInstaller 6.22.3 rebuilt the Python 3.11.15 backend offline. The full builder's
  first attempt stopped because the local Tauri CLI was unavailable. The unchanged
  native shell was reused and the app re-signed; no Rust/native rebuild is claimed.
- Comparing old/new embedded Python code confirms all 100 LocalBrain modules are
  unchanged. Of 957 sysconfig fields, exactly 20 installation-path fields changed;
  the other 937 retain their values. The builder's Python installation was not edited.
- A temporary frozen probe using the same PYZ, runtime hooks and shared libraries
  passed seven checks at each of two runtime locations, including a path with
  spaces: frozen mode, runtime prefix, sysconfig paths, current-home data defaults,
  NumPy arithmetic, synthetic Qwen inference and TLS verification. The tiny random
  model was created in memory; no pretrained weights were downloaded. The probe
  was removed before packaging.
- The old app fails the compressed metadata privacy guard. The new distribution
  passes inspection for known builder home, checkout and temporary-build paths
  in raw/compressed contents. This is a bounded path-leak check, not a universal
  content-sensitivity guarantee.
- Isolated packaged startup returned 200 for health/settings, Sessions, Session
  Dashboard, Context and keyword search. Unauthenticated health returned 401.
  Fresh settings were created, the source list was empty and no model was installed.
  WKWebView passed shell, UTF-8, authenticated health/settings, dialog open/close
  and token-free landing URL checks.
- The actual app was gracefully replaced and reopened at
  `dist/LocalBrain-apple-silicon/LocalBrain.app`. Authenticated health/settings
  and all six startup WebKit checks passed against its backend. Three saved files
  (`settings.toml`, `session-sources.toml`, `natural-search.json`) retained identical
  hashes across replacement. No private response contents or launch token were printed.
- Deep strict ad-hoc signature, ZIP CRC, every distribution file's bytes/mode,
  extracted app inventory/signature and installed ZIP checksum passed. The
  native executable's hash changed through re-signing, not a source rebuild.
- ZIP: 259591565 bytes; SHA-256 `f21fba8f94e24b6c924efd7e4fe7834d55a9aea60c155ae8327707324f1a92d1`.
- App: 841509033 regular bytes, 4717 files, 0 symlinks.
- Inventory SHA-256 `3beb5ed2adbe740820097c63a2836293e14ee0b9a0e3f5fe1a1269180ef86655`; sorted relative file
  path/integer mode/sha256 or link path/target; compact UTF-8 JSON,
  `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `a617c9286ec55097315837d3c324ed10bed85a71a703da9106a54fa11ec3c4be`.
- Backend SHA-256 `ab5f21b56295e09d21af125b75ca86a68691b58be0829624518cacb62e350619`.

App/ZIP/checksum locations remain unchanged. No model download, external upload
or publication occurred. Execution on another user's Mac and the broader native
interaction/standalone acceptance gaps remain unverified. This section supersedes
the prior artifact identity while retaining its scoped UI evidence.

## Apply-Timing Copy Removal Delivery — 2026-10-20 (Superseded Artifact)

[The general-settings follow-up](../run/run-20261018-172-general-and-project-settings.md#apply-timing-copy-removal--2026-10-20)
removes the timing paragraph below the controls and the equivalent save-feedback
sentence. Success now says `일반 설정을 저장했습니다.`. No automatic reload or
immediate time-zone redraw was added; explicit Save, startup order and actual
next-launch/next-view application timing remain unchanged.

- **Result: scoped PASS.** 72 UI/settings tests and JavaScript syntax passed.
- Four original/updated frozen-backend WebKit cases at 1100/320 widths each
  passed 16 checks: copy, save/reopen, explicit pending state, retained help and
  order, dropdown placement/dismissal, close/focus, viewport bounds, unchanged
  active page/time zone and updated next-view time zone, UTF-8 and clean URL.
  Synthetic captures were inspected; probe-only initial failures are recorded
  in the Run. No ordinary-web browser rerun or full-suite rerun is claimed.
- The real app was replaced and reopened. Authenticated health/settings, rendered
  notice removal, exact served settings script, bundled/source asset parity and
  six read-only startup WebKit checks passed. The three saved settings/source/search
  files retained identical hashes. Synthetic save checks used isolated data only.
- The template and settings script are the only application-content changes.
  The backend executable and its portable Python metadata are unchanged. Native
  hash changes come from ad-hoc re-signing; no Python/Rust rebuild or model download.
- Raw/compressed known build-path inspection, deep strict app signature, ZIP CRC,
  every distribution file's bytes/mode, extracted inventory/signature and installed
  ZIP checksum passed.
- ZIP: 259591599 bytes; SHA-256 `444cf451af31c9cf6ca2c1ec9de4f2c9ddb783965b4dd9032673978383ed0610`.
- App: 841508860 regular bytes, 4717 files, 0 symlinks.
- Inventory SHA-256 `4ce2c39d16f66e26edcf0a21c54ce8cc1de1b94c59a9a2fd9c9c9e81c6507f23`; the same sorted relative
  path/mode/content-hash, compact UTF-8 JSON algorithm as the prior receipt.
- Native SHA-256 `7e7d553cd1fe447e1a65b32fc83040a56c964abf5a4c9298f532277c72937a55`.
- Backend SHA-256 `ab5f21b56295e09d21af125b75ca86a68691b58be0829624518cacb62e350619` (unchanged).

App/ZIP/checksum paths remain in `dist/`; this identity supersedes the previous
delivery. No upload/publication. Broader native, physical-input, VoiceOver and
recipient-Mac acceptance retain their recorded limits.

## General Settings Autosave Delivery — 2026-10-20 (Superseded Artifact)

[Run 183](../run/run-20261020-183-general-settings-autosave.md) saves a general
preference when the user confirms a changed option. The general Save button and
sync-status/manual-action card are removed. Source forms retain explicit Save;
the Sessions sync button, collection schedule and local sync records remain.
Startup and time-zone application timing is unchanged.

- **Result: scoped PASS.** 97 focused UI-contract, desktop-settings and session-sync
  tests passed; JavaScript syntax passed. No full-suite rerun.
- Two original frozen-backend baselines at 1100/320 widths passed five checks
  each. Four updated ordinary-web/frozen-backend cases at those widths passed
  34 checks each, totaling 136 updated checks. Synthetic before/after captures
  were inspected.
- Checks cover pointer/keyboard confirmation, same-value selection and Escape
  without writes, changed-field patches, quiet success, saved interval retention
  when sync is disabled, busy controls, close/reopen ordering, rejected-write
  rollback, external revision conflicts, ambiguous success confirmed by readback,
  failed-readback disable/reopen recovery, focus, dropdown and viewport bounds,
  retained help/order, unchanged active page and next-view time zone.
- The actual app was gracefully replaced and reopened. Authenticated
  health/settings returned 200; the rendered general form has no submit button
  or sync card, while the Sessions sync form remains. Served script, both bundled
  UI assets and the included usage guide match source.
- Six read-only startup WKWebView checks against the running native app's backend
  passed: clean landing URL, settings dialog, health, settings API, shell and
  UTF-8. These are separate from the isolated synthetic browser mutations.
  Three real saved files (`settings.toml`, `session-sources.toml`,
  `natural-search.json`) retained identical hashes; exactly one native app
  was running after replacement.
- Only the settings template and script changed inside the app. The backend
  executable is unchanged. The native hash changed through ad-hoc re-signing;
  no Python/Rust rebuild, model download, external upload or publication occurred.
- Known builder-home/checkout/temporary-path inspection of raw and compressed
  contents, deep strict ad-hoc signature, ZIP CRC and entry safety, every
  distribution file's bytes/mode, independently extracted inventory/signature,
  and installed ZIP checksum passed.
- ZIP: 259592006 bytes; SHA-256
  `af47a11bc8708a061e264b8fd543bdb16bce8d7fd06c90994f5bcd166af887c2`.
- App: 841509388 regular bytes, 4717 files, 0 symlinks.
- Inventory SHA-256
  `a942970266ed0000ef2837293286cf630bbc09d67a37e454572c23440c630acb`;
  sorted relative entries containing file path/integer mode/sha256 or link
  path/target, compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256
  `461037a3bfdb02577206fa80d31d46b7aa98c5726d85b1777bdd3e1bcf83f53d`.
- Backend SHA-256
  `ab5f21b56295e09d21af125b75ca86a68691b58be0829624518cacb62e350619`
  (unchanged).

Current locations remain `dist/LocalBrain-apple-silicon/LocalBrain.app`,
`dist/LocalBrain-apple-silicon.zip` and its `.sha256` file. This identity supersedes
the prior delivery. Physical native interaction, VoiceOver, recipient-Mac and
broader standalone acceptance retain their recorded evidence limits.

## First-Use Overlay Wizard Delivery — 2026-10-23 (Superseded Artifact)

[Run 184](../run/run-20261023-184-first-use-overlay-wizard.md) replaces the old
standalone onboarding cards with a compact four-step modal above the actual
startup surface. Next saves pending source/document inputs; Back keeps drafts;
Skip leaves drafts unregistered. Explicit completion or Later persists completion,
while quitting before completion leaves it incomplete. Optional models require
their explicit action. The owner's two retired Project keys were removed from
their local file; their incomplete flag and other values were preserved.

- **Result: scoped PASS.** 119 focused onboarding, UI-contract, settings, sync,
  boundary, first-start preferences and build tests passed; JavaScript syntax
  passed. No full-suite rerun.
- Three old frozen baseline views passed 18 checks. Seven source and seven
  packaged-backend layout cases at 1100/320 widths passed 224 checks: real main
  surface, modal/inert background, heading focus, progress, scroll/footer bounds,
  clean URL, UTF-8, no registration or model side effects. Synthetic before/after
  captures were inspected.
- Two nine-case behavioral runs passed 194 checks in total. Seven cases per run
  used source or frozen desktop mode; the two ordinary-web cases per run used
  the source web server. They cover required-field/backend errors, retained
  drafts, Back/Skip, actual source/document saves, duplicate Next suppression,
  re-registering a removed source through Next, incomplete reload, completion
  conflict/retry, ambiguous success readback, Later/cancel, settings-load retry,
  startup destination, no repeat wizard and retained general autosave.
- Two fresh processes using the final packaged backend preserved incomplete/
  completed state and existing synthetic registrations. Each passed six
  cross-scheme startup/cookie WebKit checks, including a stale-cookie replacement.
- The actual app was gracefully replaced and reopened. Authenticated health,
  settings, served asset parity and six read-only startup WebKit checks passed.
  The startup probe now preserves an unfinished wizard instead of clicking its
  persistence-bearing Later action. Three real saved files retained identical
  hashes across replacement; the two retired keys remain absent and onboarding
  was false then. A later final check found only completion changing to true;
  the intervening action was not observed, and that current value was preserved.
  Other general values and source/search configuration remain unchanged.
  Exactly one native app was running; model installation was idle at replacement.
- The Python backend was rebuilt offline using locally cached PyInstaller
  6.22.3 and Python 3.11.15. The native shell was reused and the bundle re-signed
  ad hoc. No model download, native source change, external upload or publication.
- Known private home/checkout/build-path inspection of raw and compressed
  contents, deep strict signature, ZIP CRC/entry safety, every distribution
  file's bytes/mode and independent extracted inventory/signature passed.
  The bundled guide and current settings assets match source.
- ZIP: 264379281 bytes; SHA-256
  `a69aa91573acb3964ee73600f6f0daf92d2c62cbba9d2051b505d086d4a8178f`.
- App: 854767665 regular bytes, 4737 files, 0 symlinks.
- Inventory SHA-256
  `cf8414d49568790d5b221ab285bf7dd51934c3c27bafcbe1fd844fcf8cedc40d`;
  sorted relative entries containing file path/integer mode/sha256 or link
  path/target, compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256
  `be7faa8fa70dc9d30a0d1f3ec55fdf202c47c9067226671b551480eff5dd39ba`.
- Backend SHA-256
  `ed805a838e03db06dee5871b0f7156a4f3b362567f56d4ffab5327100db17daa`.

Current locations remain `dist/LocalBrain-apple-silicon/LocalBrain.app`,
`dist/LocalBrain-apple-silicon.zip` and its `.sha256` file. This supersedes the
prior artifact identity. Browser actions are scripted; physical native input,
VoiceOver, Notes permission dialogs, Finder pickers and recipient-Mac acceptance
retain their existing evidence limits. Initial assertion-selector, health-route
and temporary-folder-selection mistakes were confined to tests/probes, corrected
and rerun; they were not counted as successful product evidence.

## Onboarding Visual Refinement Delivery — 2026-10-23 (Superseded Artifact)

[Run 185](../run/run-20261023-185-onboarding-visual-refinement.md) refines the
first-use modal with a quiet header, centered welcome, four bottom progress dots
and token-based crossfade/offset motion. Step actions and persistence keep their
existing contracts. Normal settings retain their categories and general autosave.

- **Result: scoped PASS.** 119 existing focused onboarding, UI-contract, settings,
  sync, boundary, first-start preferences and build tests passed; JavaScript
  syntax passed. No full-suite rerun. Behavior is checked in rendered browsers
  rather than adding string assertions that duplicate the new implementation.
- Source and packaged WKWebView each passed three 43-check layout/motion cases
  at 1100×800, 320×720 and 700×480: 258 checks combined. Chromium passed 43 checks
  with normal motion and 33 with reduced motion. The initial 320px footer-wrap
  failure was fixed by shortening the final action to `시작하기`; corrected
  cases passed. The shared hidden-form rule also fixes the unintentionally
  visible new-source reconnect checkbox.
- Synthetic browser actions verified failed source validation preserves input,
  Next saves actual source/document registrations, Back keeps drafts, failed
  completion keeps the modal open, and an ambiguous successful write completes
  only after readback. General autosave, menu placement below its trigger,
  new/edit reconnect visibility and ordinary settings Escape remain operational.
  Keyboard events were browser-driven; physical input and VoiceOver were not run.
- The packaged backend passed six cross-scheme/stale-cookie startup checks,
  served-asset parity, empty registration/incomplete-state preservation and
  no model activity. The actual app was gracefully replaced and reopened; health,
  source/served asset parity and six read-only WebKit startup checks passed.
  Exactly one native app is running. Three saved configuration files retained
  identical hashes, including the owner's completed-onboarding flag; model
  installation was idle. No private settings were reset for a preview.
- Native host and frozen backend were reused. Only the settings template/CSS/JS
  were replaced in the app, then the bundle was re-signed ad hoc. The ZIP includes
  the updated guide and build receipt. Known private home/checkout/build-path
  checks of raw and compressed contents, deep strict signature, ZIP CRC/entry
  safety, every distribution file's bytes/mode, and independent extracted
  inventory/signature passed. No model download, native source change, external
  upload, publication or commit.
- ZIP: 261479418 bytes; SHA-256
  `f841f74ffb654d143e1c74e176249592a1e587f7ffbd3d6fb033cb8737f512ba`.
- App: 854773855 regular bytes, 4737 files, 0 symlinks.
- Inventory SHA-256
  `442e5ee64bfbe03baaaceaebd863d362d7bde0345e0b4bcb777bd2122a0bbe95`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256
  `a5ef339c3751dc0420ee72508b63992adedb61d4b822fa2a52d466619270f73f`.
- Backend SHA-256
  `ed805a838e03db06dee5871b0f7156a4f3b362567f56d4ffab5327100db17daa`.

Current locations remain `dist/LocalBrain-apple-silicon/LocalBrain.app`,
`dist/LocalBrain-apple-silicon.zip` and its `.sha256` file. This supersedes the
prior artifact identity. Physical native input, VoiceOver, Notes permission dialogs,
Finder pickers and recipient-Mac acceptance retain their existing evidence limits.
No new distribution approval or broader product acceptance is implied.

## Session Profile Presentation Delivery — 2026-10-23 (Superseded)

[Run 186](../run/run-20261023-186-session-source-presentation.md) refines Session
settings and the first-use Session step into a compact overview and explicit
Add/Edit form. Optional agent-home details are collapsed; removal lives in Edit.
Names, collection paths, warnings/errors and the existing registration lifecycle
remain authoritative. UI changes do not migrate source configuration or data.

- **Result: scoped PASS.** 127 focused onboarding, UI-contract, settings, source
  lifecycle, sync, boundary, first-start preferences and build tests passed;
  JavaScript syntax passed. An existing test's old literal Save label was updated
  to check the retained explicit source-submit control. No full-suite rerun.
- Source WKWebView passed 100 layout checks at 1100×800, 320×720 and 700×480.
  Frozen WKWebView passed 161 across regular settings and onboarding at those
  dimensions. Chromium passed 67 wide/narrow layout checks. Empty/candidate,
  three-profile, long-path/name, unavailable, scan-error and retained-registration
  variants preserve containment and reachable controls. Synthetic candidate/home
  presentation is injected for frozen UI cases; source mutations use its actual API.
- Chromium/source and WKWebView/frozen each passed 30 behavioral checks: required,
  invalid and overlapping paths, optional home, add/rename, busy controls, retained
  drafts/errors, confirmed reconnection, removal cancellation/acceptance and
  stable-ID re-registration. Eight additional Chromium checks cover wizard Back,
  Skip, Next-save/advance, cleared editor, footer/focus stability and no model action.
  General autosave, target-specific reconnection confirmation and browser Enter/Tab
  were also checked. An initial CSS collision and the native probe's unsupported
  Promise return were corrected before their successful reruns.
- The frozen backend and actual app each passed six startup/cookie WebKit checks.
  Actual app replacement/relaunch, authenticated health, served-source asset
  parity and exactly one native app passed. General, Session-source and search
  configuration files retained identical hashes; existing onboarding completion
  was preserved. Model installation was idle. No model download was performed.
- Reused the native host and frozen backend, replaced three UI assets and re-signed
  ad hoc. The guide/build receipt accompanies the ZIP. Known private home/checkout/
  staging-path checks across raw and compressed content, deep strict signature,
  ZIP CRC/entry safety, every file's bytes/mode, independent extracted inventory/
  signature and final installed parity passed. No external upload, publication or
  Git commit; source/session identity and original files were preserved.
- ZIP: 261481345 bytes; SHA-256
  `cd70f98903762d6eaa714fc5bbad6c90524d3800ba6167c70d6d41a7ce0730d5`.
- App: 854785030 regular bytes, 4737 files, 0 symlinks.
- Inventory SHA-256
  `fb3c44b33051a9b2eb7a344e846f51b3fc8fa64ab47f04ba805ac610d1b9b20a`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256
  `c4192ec409498a73ea9dc7334853447b7d57b1e4fa84f84c004859019f7cf10c`.
- Backend SHA-256
  `ed805a838e03db06dee5871b0f7156a4f3b362567f56d4ffab5327100db17daa`.

Current locations remain `dist/LocalBrain-apple-silicon/LocalBrain.app`,
`dist/LocalBrain-apple-silicon.zip` and its `.sha256` file. This supersedes the
prior artifact identity. Physical native input, VoiceOver, native pickers/Notes
permissions and recipient-Mac acceptance retain their existing evidence limits.

## Compact Settings Delivery — 2026-10-23 (Superseded)

[Run 187](../run/run-20261023-187-settings-control-consistency.md) aligns the shared
settings controls and adds editable synchronization minutes. The approved source
list and dialog shell remain; category departure now discards an unsaved source
editor, while wizard Back preserves it. No settings/data migration is required.

- **Result: scoped PASS.** 129 focused tests passed (the prior 127 plus custom
  interval persistence/bounds and scheduling/off/on cases). JavaScript syntax
  passed. Existing UI assertions were updated for the approved control changes;
  no full-suite rerun or broader product completion claim.
- Chromium passed 76 settings checks at wide/narrow sizes. Source and rebuilt
  frozen WKWebView each passed 114 checks at 1100×800, 320×720 and 700×480.
  These exercised actual preference/source writes, 45-minute persistence,
  invalid-input rejection, off/on preservation, conflicting-write recovery,
  lost-response readback, source identity-preserving save, category reset, equal
  controls, dropdown placement, Context kind, restored disclosure/confirmation
  and all revised pane bounds. Test data/cache were isolated from user storage.
- Frozen WKWebView passed 21 wizard checks at the same sizes; Chromium passed
  seven more. Back retains the tool/name draft, Skip does not register it, Context
  kind works, the main surface stays inert and the Search step starts no download.
  Six additional Chromium geometry checks confirmed menu visibility below each
  trigger in the short pane. Real keyboard input plus Enter saved 48 minutes;
  the first automation attempt appended digits because its selection shortcut
  was not effective, correctly triggering range rejection. A proper fill/Enter
  rerun passed. No console warnings/errors appeared in the inspected frozen page.
- The native host was reused and the frozen backend rebuilt offline with existing
  dependencies. Shared assets, guide and build receipt are bundled. Private-path
  inspection across raw/compressed content, deep strict signing, ZIP CRC and
  extracted app inventory parity passed. Bundle symlinks resolve inside the app.
- Actual app replacement/relaunch passed six startup/cookie WebKit checks,
  authenticated health, served asset parity and exactly one native instance.
  General, Session-source and search configuration hashes remain identical;
  the saved interval is 30 and onboarding is still complete. No model worker
  was running. Model installation tests/downloads were not run;
  no external publication/upload or Git commit occurred.
- ZIP: 201609578 bytes; SHA-256
  `34816d8b21f5765bc758e96263abb799bbdd24d5ba49ae6b7603ecb78b942019`.
- App: 576495233 regular bytes, 4709 regular files,
  28 internal symlinks (4737 inventory entries).
- Inventory SHA-256 `dce6a7bb6d977cf019f1fea5ad019fd4290bdbf338851a65cfcd0be9045f52d5`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `68d7ef7689429af613a74c0a110e0a96f8c67663dda6150867160bbc0b7c3a9f`.
- Backend SHA-256 `437ccf54be56a24de00837c64a9e93caf02e6c7464dc158245624e044b4f354e`.

Current locations remain `dist/LocalBrain-apple-silicon/LocalBrain.app`,
`dist/LocalBrain-apple-silicon.zip` and its `.sha256` file. This supersedes Run 186's
artifact. Physical native input, VoiceOver, native pickers/Notes permissions and
recipient-Mac acceptance retain their existing evidence limits.

## Sync Checkbox Delivery — 2026-10-24 (Superseded)

[Run 188](../run/run-20261024-188-sync-checkbox-and-presets.md) replaces the interval
number field and separate Off button with one `동기화 사용` checkbox and a
10/20/30/60-minute dropdown. Remove the range/runtime sentence. Unchecking disables
the selector and preserves minutes; changes autosave. Previously saved custom
intervals remain displayed until explicitly replaced; backend validation, defaults
and completion-based scheduling remain unchanged.

- **Scoped PASS:** 77 focused UI/settings/startup-preference tests and JS syntax.
  Chromium passed 48 checks at 1100×800 and 320×720. The packaged backend passed
  72 WKWebView checks at 1100×800, 320×720 and 700×480. No full-suite rerun.
- Actual API mutations cover all four presets, numeric persistence, off/on value
  preservation, disabled-menu refusal, keyboard selection/Escape, rejected-save
  recovery, lost-response confirmation, reopening and legacy 45-minute retention.
  Control dimensions, below-trigger visibility and pane containment passed.
  Model phase remained idle and no download was requested.
- The frozen backend is byte-identical to Run 187; only three shared UI assets,
  guide/build receipt and app signing were updated. Deep strict signature, changed
  publishable-text private-path checks, ZIP CRC and extracted inventory parity
  passed. Internal symlink targets were checked. Run 187 owns the unchanged
  frozen runtime's raw/compressed path inspection evidence.
- Actual replacement/relaunch passed six WebKit startup checks, health, asset
  parity, signature and exactly one native instance. All three configuration
  hashes are preserved; sync remains 30 minutes and no model worker is running.
  No Git commit, external upload or publication.
- ZIP: 201609298 bytes; SHA-256
  `4bf9bf723fd89028b5c6aecc3ea5f34c6ee9f1de00b069a26c4044711c648cc3`.
- App: 576495039 regular bytes, 4709 regular files and
  28 internal symlinks (4737 inventory entries).
- Inventory SHA-256 `784b2bd91042aae2ffb2f4a7f90a818ea6f23339fc3a5aeb0bbaf8cfad54f57d`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `d73a732f983702c96e28076355d4eb8d44e9df24ff68ae979301105a78bdf94d`.
- Backend SHA-256 `437ccf54be56a24de00837c64a9e93caf02e6c7464dc158245624e044b4f354e`.

The app, ZIP and checksum remain under `dist/LocalBrain-apple-silicon` and
`dist/LocalBrain-apple-silicon.zip` / `.sha256`. This supersedes Run 187's artifact.
Physical native input, VoiceOver, native picker/Notes permissions and recipient-
Mac acceptance retain their existing evidence limits.

## About Identity Delivery — 2026-10-24 (Superseded)

[Run 189](../run/run-20261024-189-about-identity-and-version.md) replaces operational
About prose with the existing mark, name and v0.0.1. All LocalBrain version
metadata is aligned; bundle identity, data paths and schemas remain unchanged.
The reference screenshot remains an attachment, outside the product and repo.

- **Scoped PASS:** 89 existing UI-contract/settings/desktop-boundary/startup/build
  tests, 11 version-source checks and offline lock consistency. Chromium passed
  36 checks at 1100×800 and 320×720; frozen WKWebView passed 54 at those sizes and
  700×480. Identity, tab navigation, close/focus restoration, containment, retained
  general controls/preferences and no model activity passed. No full-suite rerun.
- Native host rebuilt with Rust 1.99.1 using locked dependencies; frozen backend
  rebuilt offline. Temporary Rust installation used owned storage and did not
  change shell profiles. Public tool/crate downloads occurred, no model downloads.
  Existing notices remain valid: both dependency locks are identical after
  normalizing only LocalBrain's version. The initial offline notice command's
  missing cross-target crate is recorded in the Run.
- Raw and compressed known-private-path inspection, deep strict ad-hoc signature,
  ZIP CRC, internal symlink resolution and extracted inventory parity passed.
  Actual replacement/relaunch passed six WebKit startup/cookie checks, health,
  served/bundled asset parity and exactly one native instance. Three configuration
  hashes are identical; sync remains 30 minutes and the model worker is idle.
- Probe corrections for narrow-entry focus and numeric port detection are
  recorded in the Run; only successful final runs support these results.
  No external upload/publication, reference image copy or Git commit.
- ZIP: 201612471 bytes; SHA-256
  `5a08872e6bf9aa1a5dc4aecfa555d7ab310d9130feaec634e4d4ae5a13f6e9cf`.
- App: 576479026 regular bytes, 4709 regular files and
  28 internal symlinks (4737 inventory entries).
- Inventory SHA-256 `1df8820664fe9436418d37d6620edd4f357539b8525028364509f4f0b706aa5b`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `54f29dcd3c38dbdcd05dafbc08690919eb3a196b21fdbd309bc5048556ec1e5d`.
- Backend SHA-256 `93bb4c6d7950dcc236a9ef902039a93367f9acac4af54f89938a67f28dcba3ac`.

The app, ZIP and checksum remain under `dist/LocalBrain-apple-silicon` and
`dist/LocalBrain-apple-silicon.zip` / `.sha256`. This supersedes Run 188's artifact.
Physical native input, VoiceOver, native picker/Notes permissions and recipient-
Mac acceptance retain their existing evidence limits.

## Independent Source Sync Delivery — 2026-10-24 (Superseded)

[Run 190](../run/run-20261024-190-sync-settings-and-context-schedule.md) moves
scheduling into Sync after Search model and before Storage. Session and Local
Context each have independent Use and 10/20/30/60-minute choices. General retains
startup/timezone; Storage stays separate. Context defaults to enabled/30 minutes;
existing Session values and default remain. Independent AI-index controls are a
backlog TODO; existing activated change-driven search refresh is unchanged.

- **Scoped PASS:** 132 focused tests plus JS syntax. Coverage includes independent
  defaults/clocks, old files, off/on, validation, busy/manual-request retention,
  repeated backend completion, incremental Context updates/deletions, stable IDs,
  failures, rollback/cancellation and Notes subprocess timeout/cleanup. Initial
  assertions were updated for the approved defaults/layout and shared clock owner;
  one synthetic path assertion was corrected to compare the registered source ID.
  No full-suite rerun or real Notes access during tests.
- Chromium/source and WKWebView/frozen each passed 117 checks at 1100×800,
  320×720 and 700×480. Real preference writes, four presets per domain, disabled
  menus, retained minutes/custom values, failed-save readback, lost-response
  confirmation, tabs, containment, keyboard Escape, close/focus and reopen passed.
  Seven additional Chromium wizard checks cover isolation, steps and no model action.
  A non-cancelable synthetic Escape probe was fixed; no production keyboard fix
  was needed. Final backend refinement only changes the Notes timeout diagnostic;
  its behavior test passed and the settings assets are identical to the WebKit run.
- Real source and frozen scheduler runs each passed eight checks for initial
  explicit import while periodic collection is off, disabled suppression, resume,
  independent schedules, completion timing, periodic updates, retained IDs, no
  Session scans and idle model. User data was not used in these tests.
- Backend rebuilt offline with cached tooling; native host reused and app re-signed
  ad hoc. Dependency locks/notices are unchanged. Raw/compressed known-private-path
  inspection, deep strict signatures, ZIP CRC, internal symlinks and independently
  extracted inventory parity passed. No model download, external publication or
  Git commit. Final actual-app startup and cleanup are recorded in the Run.
- ZIP: 201611793 bytes; SHA-256
  `baac3a9660b014b45ca3fdb77d63fee170c6ceb4570c0e1c26eaa451b267c14e`.
- App: 576482992 regular bytes, 4709 regular files and
  28 internal symlinks (4737 inventory entries).
- Inventory SHA-256 `cbbe4ac3bfb273c762e292de16591d467c68537e080db12faf456d6f056b443a`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `a652f7e21287ad7d82f7a00ce6e682ee6bd247a77988bda12cc8f8d0f711c17a`.
- Backend SHA-256 `9686233b6a1224d044e352367147d186e49374703a7307a7fe058ca47c19c031`.

Version remains 0.0.1. App, ZIP and checksum remain under
`dist/LocalBrain-apple-silicon` and `dist/LocalBrain-apple-silicon.zip` / `.sha256`.
This supersedes Run 189's artifact. Physical native input, VoiceOver, native
picker/Notes permissions and recipient-Mac acceptance retain their evidence limits.


## Single Sync Select Delivery — 2026-10-24 (Superseded)

[Run 191](../run/run-20261024-191-single-sync-select.md) replaces each Sync checkbox
and interval with one 160px selector: 10/20/30/60 minutes, then Off. Off preserves
saved minutes; a numeric selection enables and sets the interval in one revision-
checked write. Backend defaults, fields, schedules and usage classification remain.
Source help now describes importing records without implying primary sessions only.
Home-first registration is a proposal, not an implemented path migration.

- **Scoped PASS:** 91 existing UI/settings/preferences/onboarding/desktop-boundary
  tests and JavaScript syntax. No full-suite rerun; backend/native code unchanged.
- Chromium/source and WKWebView/frozen each passed 156 checks at 1100×800,
  320×720 and 700×480. All five choices per domain, atomic enable/interval writes,
  Off preservation, independent values, legacy custom values, failed-save readback,
  successful writes with lost responses, keyboard selection/Escape, focus, reopen,
  tab transitions, source-editor reset and menu containment passed. Wide/narrow
  rendered output was inspected. Chromium's initial resize clamped to 500px;
  explicit 320px viewport emulation was then measured and passed.
- Three UI assets updated; existing native/frozen runtime and dependency locks
  reused. Changed publishable-text path checks, deep strict ad-hoc signatures,
  ZIP CRC, internal symlink resolution and extracted inventory parity passed.
  Run 190 owns raw/compressed path inspection of the unchanged frozen runtime.
- Actual replacement/relaunch passed six WebKit startup/cookie checks, health,
  served/bundled/source asset parity and exactly one app/backend instance. All
  three configuration-file hashes are preserved. No model download or publication.
- ZIP: 201611036 bytes; SHA-256
  `0df8a82ce512b959342a9d035e72192a699f5cedde08eb38b08b98f3e6d2598c`.
- App: 576482809 regular bytes, 4709 regular files and
  28 internal symlinks (4737 inventory entries).
- Inventory SHA-256 `f201415917ede1f98db4b47d1518886e894a37d32857da3ecb8f908692b09ca0`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `baf2a393162bab52bd507082a82cac084b02e52c354ed999da93087cee070329`.
- Backend SHA-256 `9686233b6a1224d044e352367147d186e49374703a7307a7fe058ca47c19c031`.

Version remains 0.0.1. App, ZIP and checksum remain under
`dist/LocalBrain-apple-silicon` and `dist/LocalBrain-apple-silicon.zip` / `.sha256`.
This supersedes Run 190's artifact. Physical native input, VoiceOver, native
picker/Notes permissions and recipient-Mac acceptance retain their evidence limits.


## Home-First Source Delivery — 2026-10-24 (Superseded)

[Run 192](../run/run-20261024-192-home-first-source-editor.md) promotes agent home
to the basic profile field, derives Codex `sessions` or Claude `projects`, and
retains explicit record-location overrides in a disclosure. Existing roots remain
authoritative; merely opening an editor does not migrate configuration. Sync
selectors now fit their contents, about 79px at the default scale.

- **Scoped PASS:** 97 existing UI/source-registry/settings/onboarding/desktop-boundary
  tests and JavaScript syntax. No full-suite rerun; backend/native code unchanged.
- Chromium/source and WKWebView/frozen each passed 156 checks: 30 source-editor,
  40 geometry/Sync checks at each of 1100×800, 320×720 and 700×480, and six wizard
  checks. Both tools register from home alone. Legacy home inference, custom and
  home-less root preservation, explicit default reset, invalid/duplicate rejection,
  confirmed relocation with stable ID, cancel/tab reset, Next-save, Back-retention
  and Skip-without-save passed. Picker bridges used a stub; real picker dialogs
  were not exercised. A wizard probe initially clicked Next while Edit was still
  briefly busy; waiting for the existing busy boundary passed without a product fix.
- Rendered baseline/final wide and narrow forms were inspected. All five Sync
  options save and remain readable, selected marks fit, menus stay below controls
  and contained, keyboard Escape/focus and narrow heights pass. A separate Chromium
  check confirmed a saved 1440-minute value remains one line and expands the control.
- Three UI assets updated; existing native/frozen code, dependency locks and notices
  retained. Changed publishable-text path checks, deep strict ad-hoc signatures,
  ZIP CRC, internal symlink resolution and extracted inventory parity passed.
  Run 190 owns raw/compressed path inspection of the unchanged frozen runtime.
- Actual replacement/relaunch passed six WebKit startup/cookie checks, health,
  served/bundled/source asset parity and one app/backend instance. All three
  configuration-file hashes are identical and the model worker is idle.
  No model download, external publication or Git commit.
- ZIP: 201611537 bytes; SHA-256
  `3859d1840876e6da53db6b0576d85c4140ecaf78dcdc4002901164c85f54ea60`.
- App: 576484073 regular bytes, 4709 regular files and
  28 internal symlinks (4737 inventory entries).
- Inventory SHA-256 `c526576493d0a87b4601c6af62f2bd00dc8c7e6a850bd46f6a802ee67237a557`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `6d231d74b5edd74c38f6892766e332f90c59cd4b04b9b6197b6dc6c699fe54f6`.
- Backend SHA-256 `9686233b6a1224d044e352367147d186e49374703a7307a7fe058ca47c19c031`.

Version remains 0.0.1. App, ZIP and checksum remain under
`dist/LocalBrain-apple-silicon` and `dist/LocalBrain-apple-silicon.zip` / `.sha256`.
This supersedes Run 191's artifact. Physical native input, VoiceOver, native
picker/Notes permissions and recipient-Mac acceptance retain their evidence limits.


## Profile List Actions Delivery — 2026-10-24 (Superseded)

[Run 193](../run/run-20261024-193-profile-list-actions.md) introduces Tool,
Profile name, Home and Session-folder labels, red textual required markers,
padded row-level Edit/Unregister actions, a named confirmation modal and same-tab
return to the source list. Backend, schema, identity and collection rules remain.

- **Scoped PASS:** 97 focused UI/source/settings/onboarding/desktop-boundary tests
  and JavaScript syntax. No full-suite rerun. Source Chromium and frozen WKWebView
  each passed 95 assertions: 37 action/failure checks, 17/18/18 geometry/focus checks
  at 1100×800, 320×720 and 700×480, and five wizard checks. After the final explicit
  inert fix, Chromium's 53 layout/focus checks and all 95 WKWebView checks passed.
  Chromium also exercised real Enter/Escape input against the safe Cancel default.
- Synthetic API writes verify selected-only removal, captured identity/revision,
  duplicate suppression, retryable failures, conflict review and lost-response
  readback. Imported session/event/source-file rows, source identity/path and the
  original transcript remain. TOML owns registration state. Wizard Back retains
  a draft, Next saves and Skip does not register; same-category clicks discard
  normal Add/Edit drafts without writing.
- Rendered wide/narrow list, form and modal were inspected. Buttons use 16px inline
  padding and 32px desktop/40px narrow height; narrow actions sit below identity.
  Modal containment, required-marker consistency, focus restoration and compact
  Sync geometry passed. WKWebView initially allowed focus into the parent dialog;
  explicitly making it inert while confirmation is open fixed the failure.
- Three UI assets updated, existing native/frozen code and dependency locks/notices
  retained. Changed-text private-path checks, strict ad-hoc signatures, ZIP CRC,
  internal symlinks and extracted inventory parity passed. Run 190 owns unchanged
  runtime raw/compressed path inspection. Actual replacement/relaunch passed six
  WebKit startup/cookie checks, health, asset parity and one app/backend instance.
  Three configuration hashes are identical and the model worker is idle.
- ZIP: 201612631 bytes; SHA-256
  `056a48bbd369e0c2605f99309bc0c02e5a1cf0e62eacf13bad1b30a768ddcadd`.
- App: 576489846 regular bytes, 4709 regular files and
  28 internal symlinks (4737 inventory entries).
- Inventory SHA-256 `d5dc6d46de286be49aed406a0def960cff22029fcb904bfb6ce9ef309b085333`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `8800514676837b562a17debbe2e03b0c5a9bae27ff1db0ff47e43bf7d7e8fd6d`.
- Backend SHA-256 `9686233b6a1224d044e352367147d186e49374703a7307a7fe058ca47c19c031`.

Version remains 0.0.1. App, ZIP and checksum remain under
`dist/LocalBrain-apple-silicon` and `dist/LocalBrain-apple-silicon.zip` / `.sha256`.
This supersedes Run 192's artifact. No model download, publication or Git commit.
Physical native input, VoiceOver, picker/Notes permissions and recipient-Mac
acceptance retain their evidence limits.


## Compact Profile Controls Delivery — 2026-10-24 (Superseded)

[Run 194](../run/run-20261024-194-compact-profile-controls.md) reduces profile-row
Edit/Unregister typography and horizontal padding and makes the Profile name
placeholder follow Codex/Claude Code. Entered names, validation and ordering remain.

- **Scoped PASS:** 91 existing UI/source/settings/onboarding tests and JS syntax.
  Source Chromium and frozen WKWebView each passed 83 assertions (27/28/28 at
  1100×800, 320×720 and 700×480). Provider hints, custom/saved-name preservation,
  required validation, draft reset, actual rename saving, source ID/provider/root
  preservation, both filter labels/order, confirmation/cancel/focus, containment
  and compact Sync passed. Reversed synthetic TOML confirmed DB-ID order persists.
  No new unit-test files or full-suite rerun were needed for this bounded edit.
- Baseline/final wide and final narrow views inspected. Desktop Edit/Unregister
  widths decreased from about 56/82px to 39/63px; 12px label type and 8px inline
  padding retain 32px desktop/40px narrow targets. Confirmation remains unchanged.
- Three UI assets updated; native/frozen code, dependency locks and notices reused.
  Changed-text private-path checks, strict ad-hoc signatures, ZIP CRC, internal
  symlinks and extracted inventory parity passed. Run 190 owns unchanged runtime
  raw/compressed path checks. Actual replacement/relaunch passed six startup/cookie
  checks, health, source/bundle/served-asset parity and one app/backend instance.
  Three configuration hashes are identical; no model activity or download.
- ZIP: 201612603 bytes; SHA-256
  `7012882920fbe660b055c3c12e2514dc30e4eeac5a6843bb6989d707c246e3b9`.
- App: 576489990 regular bytes, 4709 regular files and
  28 internal symlinks (4737 inventory entries).
- Inventory SHA-256 `d519ded84e362e2c14830298573574c26e9e5282c919d71c5eefdb19278113d2`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `fd82a8959a4ae084393c787762ae71f7d0f14fd9d247adde0fc1a813d514ef9c`.
- Backend SHA-256 `9686233b6a1224d044e352367147d186e49374703a7307a7fe058ca47c19c031`.

Version remains 0.0.1. App, ZIP and checksum remain under
`dist/LocalBrain-apple-silicon` and `dist/LocalBrain-apple-silicon.zip` / `.sha256`.
This supersedes Run 193's artifact. Physical native input, VoiceOver, picker/Notes
permissions and recipient-Mac acceptance retain their evidence limits.


## Generalized Session Profiles Delivery — 2026-10-24 (Superseded)

[Run 195](../run/run-20261024-195-generalized-session-profiles.md) generalizes
profile identity, presentation and ordering. Existing numeric DB IDs now identify
v2 Session configuration and public filters. Names, six colors and TOML-array
order update settings, Sessions and Session Dashboard. Historical namespaces
remain internal for safe reingestion and old links; imported records are retained.

- **Scoped PASS:** all nine focused profile behavior tests, 30 desktop-setting
  tests, seven pin-UI tests and JavaScript syntax. The full suite ran 1,230 tests
  with four failures reproduced from the pre-change snapshot: the data-model
  table-count checker, schema-audit checker/manifest and value-family count.
  These are pre-existing learning-table/inventory drift, not a clean-suite claim.
  Generated schema-presentation/value-dictionary checks, final plan catalog,
  whitespace and repository privacy checks pass.
- Source Chromium exercises numeric identity, color/rename propagation, keyboard
  and drag ordering, selected-filter preservation, lost-response readback,
  rejected-write recovery and existing editor/confirmation behavior. It also
  verifies chart selection retention, dashboard order/scope and detail cues.
  Final frozen WKWebView passes 24 interaction plus 33 geometry assertions at
  1100×800, 320×720 and 700×480. A missing v2 color correctly uses the provider
  default even when the DB previously cached another color.
- Synthetic migration/reingestion preserves source/session/event/usage identity,
  frozen attribution and pins. Tests cover separate same-provider profiles,
  duplicate/invalid IDs/colors/orders, restored IDs, manual-file projection,
  Home-only edits with a fixed custom root, provider wrappers, stale revisions
  and write failures including failure after file replacement.
- Actual local migration compares row counts/digests for all application tables,
  excluding FTS shadow tables and source presentation projection. Existing source
  identity and all compared record rows remain identical; DB integrity and foreign
  keys pass. General and search setting files remain byte-identical. The Session
  config intentionally becomes schema 2 with the same numeric source IDs.
- Backend rebuilt offline using the existing lock. Native source and dependency
  locks/notices are retained; renewing the ad-hoc signature changes native binary
  signature bytes. Raw/compressed private-path checks, deep strict signature,
  ZIP CRC, internal symlink resolution and extracted inventory parity pass.
  No model download, external publication or Git commit was performed.
- Frozen fixture and actual replacement each pass six WebKit startup/cookie checks.
  The final app passes health, numeric settings, source/bundle/served-asset parity
  and one native/backend instance. Early probe requests used nonexistent endpoint
  paths; correcting them to `/api/health` and `/api/settings` passed without a
  product change. Task-owned probes, synthetic servers and scratch were cleaned.
- ZIP: 201638575 bytes; SHA-256
  `4136bd82a0b9a9ec7ee46aa203aa8c3e2b1c51392693401e32363e0d32090f2d`.
- App: 576517632 regular bytes, 4710 regular files and
  28 internal symlinks (4738 inventory entries).
- Inventory SHA-256 `daa0efd7b2d04f5e87807d8bc4d60340c6be6000901edd1e1a0b914f5d9da55e`;
  sorted relative file path/integer mode/sha256 or link path/target entries,
  compact UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`.
- Native SHA-256 `1e35d4513d73cd9de27ad78642c14aa6bb7dd898ebcee210f2cc1548b6f33394`.
- Backend SHA-256 `11b0a38db6d43da113b476f75952afa2dff716ff1faec6a91a257decdd680d1a`.

Version remains 0.0.1. App, ZIP and checksum remain under
`dist/LocalBrain-apple-silicon` and `dist/LocalBrain-apple-silicon.zip` / `.sha256`.
This supersedes Run 194's artifact. Physical native input, VoiceOver, real
picker/Notes permissions and recipient-Mac acceptance remain outside this scoped
pass; broader Feature/PRD acceptance status is unchanged.

## Source Primary Key Only Delivery — 2026-10-24 (Superseded)

[Run 196](../run/run-20261024-196-source-primary-key-identity.md) removes the
redundant source string identifier and converts live references to the existing
numeric PK. Name/provider and path/color/order/health retain their separate roles.
This supersedes Run 195's compatibility decision and distribution artifact.

- **Scoped PASS:** 17 profile behavior tests and the final 61-test focused
  profile/scheduler/desktop group. The full suite runs 1,238 tests with four
  failures matching the pre-change baseline: data-model table ownership/counts,
  schema-audit checker and manifest table count, and value-family inventory.
  These reflect pre-existing learning-table/documentation drift. They remain
  unresolved; this is not a claim that the entire suite passes.
- Source WebKit passes 25 checks; final packaged WKWebView passes 26 including
  cached sync-report PK migration. Checks cover same-provider IDs, shared rename,
  colors/order, selected ID preservation, unchanged roots, editor reset, session/
  dashboard/chart/detail/Context routes, old-alias fallback and no model install.
  Run 195 retains geometry and physical-input evidence; this Run has no redesign.
- Synthetic tests cover one-time dependency conversion, native-key re-ingestion,
  stable opaque IDs, pins and attribution, invalid/conflicting files, ambiguous
  numeric chart aliases, unexpected schema, reconnect recovery and rollback.
  A private actual-data copy and the actual stopped database preserve all table
  counts and unaffected-row digests, source fields/IDs, and repeated-startup state.
  Integrity and foreign keys pass. General, Session and search files remain
  byte-identical; cached sync reports change references alone, preserving clocks,
  outcomes and counts. The app's local migration recovery backup is retained
  under the existing storage lifecycle policy.
- A still-running web server prevented the first actual attempt at the exclusive
  runtime lock, before database/file writes. After both runtimes were stopped,
  backup and migration passed. The replaced actual app passes six WebKit startup/
  cookie checks, health, numeric settings, 18 source/bundle/served asset comparisons,
  unchanged configuration and one native/backend instance. The web server is
  restored at its original loopback address with the same numeric profile contract.
- Offline backend rebuild retains dependency locks/notices and native source.
  All 104 bundled local modules match compiled current source. Raw/compressed
  private-path checks, deep strict ad-hoc signatures, ZIP CRC, internal symlinks
  and extracted distribution inventory parity pass. The model worker remains idle.
  No model download, external publication or Git commit was performed.
- ZIP: 201647554 bytes; SHA-256
  `3c86ff2c2f3445b967a90f67c1b96999846091e27e02917ba906755faa899067`.
- App: 576526257 regular bytes, 4710 regular files and 28 internal symlinks.
  The full distribution adds five accompanying files: 4715 regular files and
  28 symlinks (4743 entries).
- Distribution inventory SHA-256
  `645b79e3f54970041ef9d66f265b73d7f4a34d1997b4b0e7cec75850ede37e65`;
  sorted relative paths encoded as `[path,"file",bytes,sha256,integer_mode]` or
  `[path,"link",target]`, compact JSON with default ASCII escaping. This definition
  covers the whole distribution directory, unlike prior app-only inventories.
- Native SHA-256 `c97d51970e47fbdfab8020311c6cb532aeffdbec05972dace3dbcacd127b1495`.
- Backend SHA-256 `99f691d6d627f58ea92f5942855ec4320f14b7b76ed4d4fe066d6cad004827ae`.
- Final generated schema/value dictionaries, JS syntax, plan catalog, whitespace
  and repository privacy checks pass. Verification processes and task-owned
  temporary data/build/probe artifacts are cleaned at closure; the app and web
  server remain running from their durable locations.

Version remains 0.0.1. Final app, ZIP and checksum remain under
`dist/LocalBrain-apple-silicon` and `dist/LocalBrain-apple-silicon.zip` / `.sha256`.
Physical native input, VoiceOver, real picker/Notes permissions and recipient-Mac
acceptance remain outside this scoped pass. Broader Feature/PRD status is unchanged.

## Profile Settings Presentation Delivery — 2026-10-25 (Superseded)

[Run 197](../run/run-20261025-197-profile-settings-presentation.md) standardizes
Session TOML field order, removes profile dots from source toggles, and presents
settings profiles as independently movable rows with color-only tag controls.
This supersedes Run 196's distribution; the sole numeric-PK contract remains.

- **Scoped PASS:** all 108 existing source/profile/settings/onboarding/UI tests,
  JavaScript syntax and dedicated field-order witnesses for UI writes, optional
  values, bootstrap and v1 upgrade. No new test files or full-suite rerun. The
  four historical learning-table/documentation inventory failures recorded in
  Run 196 are outside this pass; no new clean-suite claim is made.
- Source Chromium and packaged WKWebView each pass 30 behavior and 30 geometry
  checks at 1100×800, 320×720 and 700×480. Color persistence, record cues, text-only
  toggles, numeric selection, keyboard/drag reorder, insertion preview, cancellation,
  failed-write recovery, focus, editor reset and removal confirmation pass.
  Dashboard order/scope/dot checks and five source first-use checks pass. Rendered
  wide, expanded-palette and narrow screens were inspected; containment and shared
  32px/40px control targets remain. Native physical-input/VoiceOver evidence is
  not inferred from scripted events.
- Corrected probe-only mistakes: existing neutral toggle dividers were initially
  counted as dots; close-event checks ran too early; a synthetic Escape was not
  cancelable and closed the WebKit settings dialog. A trial focus delay was reverted,
  and the original focus implementation passes. Final packaged UI bytes exactly
  match the verified source and the extracted ZIP.
- Actual formatting was applied after runtime shutdown and a private settings
  backup, under exclusive runtime ownership and the local writer lock. Parsed
  Session values, array order and source DB rows are unchanged. General/search
  files remain byte-identical. Actual startup verifies the requested field order,
  six WebKit/cookie checks, health, Sessions and Dashboard routes, numeric profiles,
  17 top-level served assets, one native/backend instance and an idle model worker.
- The first simultaneous app/web restart did not produce a ready desktop backend.
  Its stderr is discarded by the existing native shell, so the initial cause is
  unconfirmed. A directly launched diagnostic backend reported ready and exited
  cleanly. Relaunching the app after web startup passed all actual checks. Both
  runtimes remain running; simultaneous-start readiness is not an acceptance claim.
- Offline backend build retains dependency locks, native source and notices.
  All 104 bundled local modules and data resources match the source. Raw/compressed
  private-path checks, deep strict ad-hoc signatures, ZIP CRC, internal symlinks
  and extracted distribution inventory parity pass. Generated metadata, plan
  catalog, whitespace and privacy checks pass. Task-owned temporary verification
  processes, data copies, screenshots, probes and build files are cleaned at closure.
  No model download, external publication or Git commit was performed.
- ZIP: 201647311 bytes; SHA-256
  `4ee9f75abd733a517eb23abb3ffd75a07aa46f5a872295121b8d708a39ced84c`.
- App: 576528102 regular bytes, 4710 regular files and 28 internal symlinks.
  The distribution has 4715 regular files and 28 symlinks (4743 entries).
- Distribution inventory SHA-256
  `6637be8d85c5219bdacdee1857807988b0baaeced6279a339d3c979f67666396`;
  sorted relative paths encoded as `[path,"file",bytes,sha256,integer_mode]` or
  `[path,"link",target]`, compact JSON with default ASCII escaping.
- Native SHA-256 `bb28ef1b7c02abcd3a2272f450c7e7ad5cb2c4081b414328688fa2e26a30e451`.
- Backend SHA-256 `fc09bf4a02c99e87d235c0c8ce7fe4673ccc2893240cdf4978557211651c535f`.

Version remains 0.0.1. App, ZIP and checksum remain under
`dist/LocalBrain-apple-silicon` and `dist/LocalBrain-apple-silicon.zip` / `.sha256`.
Real native drag/key input, VoiceOver, picker/Notes permissions and recipient-Mac
acceptance retain their prior limits. Broader Feature/PRD acceptance is unchanged.

## Context Settings Alignment Delivery — 2026-10-25 (Superseded)

[Run 198](../run/run-20261025-198-context-settings-alignment.md) supersedes the
Run 197 distribution. Version remains 0.0.1; source IDs and imported records retain
their previous meaning.

- **Scoped PASS:** 122 relevant source/settings/onboarding/UI/Context tests,
  including the new durable-order, invalid/stale-write and compatible-migration
  cases. JS syntax, generated schema/value metadata, catalog and whitespace pass.
  No full-suite rerun. The separate data-model documentation checker retains its
  pre-existing learning-table ownership/count failures; no clean all-checks claim.
- Chromium and packaged WKWebView each pass 25 behavior checks and 39 geometry
  checks across wide/narrow/short viewports. Source-only explorer confirmation,
  first-use draft/skip and synthetic Notes error/duplicate-action checks pass.
  Existing native-input, VoiceOver, real Notes/picker and recipient-Mac limits remain.
- Built offline with cached locked dependencies; no model download. All 104 bundled
  local modules and 69 HTML/CSS/JS/SQL/JSON assets match source. Deep strict ad-hoc
  signatures, raw/compressed private-path checks, ZIP CRC, internal symlinks and
  extracted inventory parity pass. The native shell source is unchanged.
- Actual replacement follows graceful shutdown and private configuration/SQLite
  backup. App and web are running from durable paths. Three routes, three changed
  served assets, six WKWebView startup/cookie checks, one native/backend instance,
  settings byte preservation, Context registration/document-ID preservation, legacy
  order and DB integrity pass. An initial port probe missed a listening socket
  because lsof resolved its numeric address to a name; disabling name/service
  resolution corrected the probe, with no additional app restart required.
- ZIP: 201652035 bytes; SHA-256
  `eb2fa052d3d03f9819bc4232190c662e28fc1c06327934ec4010a2158dfe9f8c`.
  Full distribution: 4716 regular files and 28 internal symlinks. Inventory SHA-256
  `56c4772f605dff1131a1cd8fc5db721aa79a8f7f54819fd4a863c603ab29592f`,
  using sorted `[relative_path,"file",bytes,sha256,integer_mode]` and
  `[relative_path,"link",target]` records encoded as compact ASCII-escaped JSON.
- App/ZIP/checksum remain under `dist/LocalBrain-apple-silicon` and the sibling
  `.zip`/`.sha256`. Task-owned synthetic runtimes, backup copies, probes and build
  files are removed at closure. Actual app/web stay running. No publication or
  Git commit; broader Feature/PRD acceptance is unchanged.

## Settings Row Shadow Lines Delivery — 2026-10-25 (Superseded)

[Run 199](../run/run-20261025-199-settings-row-shadow-lines.md) supersedes the Run 198
local distribution with a CSS-only correction. White rows use subtle edges and
resting shadows; no backend or registration/order contract changes.

- Source rendered checks cover both lists' rest/focus/drag styling and wide/narrow/
  short containment. Existing behavior suites were not repeated for this CSS-only
  change. No new model/dependency download or backend compilation.
- Refreshed the existing verified bundle's CSS and signature. All 69 packaged
  HTML/CSS/JS/SQL/JSON assets match current source. Deep strict signatures, ZIP CRC,
  internal symlinks and extracted distribution inventory parity pass.
- Actual app and web restart refresh the asset version. Both serve the exact new
  CSS; six WKWebView startup/cookie checks and saved-settings byte preservation pass.
  One native app/backend remains running. No source-registration or content-mutation
  requests were made.
- ZIP: 201652020 bytes; SHA-256
  `a17a0ed2bdda126970c73b322365852a81b80430710fb0a3f4442163610e5726`.
  Distribution inventory SHA-256
  `6a4964d97434086448f86c473590ad357e732c24783e5189d165bc12a7a4c315`,
  using sorted `[relative_path,"file",bytes,sha256,integer_mode]` and
  `[relative_path,"link",target]` records encoded as compact ASCII-escaped JSON.
- Version remains 0.0.1 in `dist/LocalBrain-apple-silicon/LocalBrain.app`, with sibling
  ZIP/checksum. No publication or commit. Task-owned preview/build/rollback artifacts
  are removed at closure. Broader Feature/PRD acceptance remains unchanged.


## Color Menu And Local Picker Delivery — 2026-10-25 (Superseded)

[Run 200](../run/run-20261025-200-profile-color-menu-and-local-picker.md) supersedes
Run 199. Version remains 0.0.1. Both browser and app now connect Browse to a macOS
chooser; profile colors open a vertical tag menu with light dismissal.

- Scoped PASS: 22 focused picker/onboarding/boundary tests; 26 Chromium and 26
  WebKit interaction checks; real pointer dismissal/toggle checks; rendered
  containment at 1100×800, 320×720 and 700×480. No full-suite rerun. UI picker
  results/native bridge calls use controlled stubs and do not prove OS input.
- Actual helper probes show folder/file panels and normal cancellation. A probe
  attempting OK without valid UI selection returned modal abort; abnormal modal
  completion now produces a visible error rather than silently canceling. Physical
  Tauri-button/file selection confirmation remains unanswered, not passed.
- Built offline from cached locked libraries with no model download. All 105
  bundled local modules and 69 HTML/CSS/JS/SQL/JSON assets match source. The existing
  native shell/dialog plugin is reused; no Rust rebuild is claimed. Strict deep
  ad-hoc signatures, raw/compressed private-path checks, ZIP CRC and extracted
  inventory parity pass. Finder metadata is excluded from the staged distribution.
- Isolated bundled runtime and actual app/web pass authenticated startup, health,
  settings and changed-asset checks, plus invalid-picker-request rejection. Six
  WKWebView cookie/startup checks pass in each context. One native host/backend
  runs; the three saved configurations are byte-identical before/after replacement.
- ZIP: 201654561 bytes; SHA-256
  `2dcb1d83dc40e2212e10cce44ef393e010e42052fa99c4e2bfbee9a30a7d50fd`.
  App regular-file bytes: 576545051. Distribution inventory SHA-256
  `8885047bbc8acda2761784033aaa00ba3b62062cb78d1bf4366da6a7d68b909d`, using the same sorted path/type/size/hash/mode and
  symlink-target compact JSON definition as the preceding receipt.
- App/ZIP/checksum remain under `dist/LocalBrain-apple-silicon` and its sibling
  `.zip`/`.sha256`. Task-owned synthetic servers, probes, build outputs and rollback
  copies are removed at closure. Actual app/web remain live. No upload, publication
  or commit. VoiceOver, recipient-Mac and broader Feature acceptance remain separate.

## Order Motion And Compact Colors Delivery — 2026-10-26 (Superseded)

[Run 201](../run/run-20261026-201-settings-order-motion-and-compact-colors.md)
supersedes Run 200's local distribution. Version remains 0.0.1. Both settings
source lists show whole-row drag previews, animated neighbors and edge scrolling;
the compact below-trigger menu uses horizontal tags.

- Scoped PASS: 53 relevant profile/settings/Context tests; 39 scripted interaction
  checks each in Chromium and macOS WKWebView; real Chromium drag input for both
  lists; wide/narrow/short, reduced-motion and coarse-pointer geometry checks.
  Scripted pointer capture does not establish physical Tauri input. No full-suite
  rerun or broader native/recipient-Mac acceptance is claimed.
- Refreshed JS/CSS in the existing verified app, reusing its frozen backend and
  native shell. No compilation, dependency or model download. All 69 packaged
  HTML/CSS/JS/SQL/JSON assets match source. Deep strict ad-hoc signatures, raw and
  compressed private-path inspection, ZIP CRC, internal symlinks and extracted
  inventory parity pass. The archive reader was loaded from the existing cache
  after the normal environment lacked that optional build dependency.
- Actual app/web pass health/settings/Sessions, exact served-asset checks and six
  WKWebView cookie/startup checks. Three saved configurations remain byte-identical.
  An initial simultaneous launch left the app backend unavailable; sequential
  relaunch after web readiness passed. Its precise cause was not captured, so
  simultaneous-start behavior remains outside this receipt. One native host and
  backend, plus the existing web server, remain running from durable paths.
- ZIP: 201656383 bytes; SHA-256
  `09fe55750ac2a825696f8ceee9421ae8c22af7cb09d6ba0c1c787fec96d2cd14`.
  App regular-file bytes: 576552078. Distribution: 4715 regular files and 28 internal
  symlinks. Inventory SHA-256
  `3821f9bd2220178406260afdc9d6c296a651324b2fccdb65d613dce8542171d5`, using the same sorted path/type/size/hash/mode and symlink-target compact JSON
  definition as the preceding receipt. Finder metadata is excluded.
- Final app/ZIP/checksum remain in `dist/LocalBrain-apple-silicon` and sibling
  `.zip`/`.sha256`. Privacy, JS syntax, whitespace and artifact-catalog checks pass.
  Task-owned synthetic servers, probes, extracted/staged apps and rollback copies
  are removed at closure. No commit, upload or publication. Prior physical-picker,
  VoiceOver and recipient-Mac evidence limits remain unchanged.

## Profile Tag Alignment Delivery — 2026-10-26 (Superseded)

[Run 202](../run/run-20261026-202-profile-tag-alignment.md) supersedes Run 201's
distribution with diagonal row tags, left-facing horizontal menu tags, aligned
painted edges and selection fill/outline replacing the check. Version stays 0.0.1.

- Scoped PASS: 22 interaction/geometry checks in each of Chromium and WebKit,
  responsive fine/coarse-pointer checks, real Chromium trigger input and rendered
  comparison. No new backend behavior or repeated backend suite is claimed.
- Only settings JS/CSS and the app signature are refreshed. All 69 packaged data
  assets match source; private build-path inspection, strict deep signature, ZIP
  CRC, symlink and extracted inventory checks pass. No dependency/model download
  or backend/native compilation. App/web route and exact asset checks plus six
  WKWebView startup checks pass after sequential restart. Three configuration files
  remain byte-identical; one native host/backend and the web server remain running.
- ZIP: 201656496 bytes; SHA-256
  `a250c1170e113e068550cc44db64ccbb2b6a8ba323f90b447f6e19d864fedd15`.
  App regular-file bytes: 576552318. Distribution: 4715 regular files, 28 internal
  symlinks; inventory SHA-256
  `eae54689e02e0386b7bb9489047c99851707797c0828e5ac1e44a841c40d14c6`, using the preceding receipt's compact JSON inventory definition.
- App/ZIP/checksum remain in the existing `dist/` locations. Privacy, JS syntax,
  whitespace and catalog checks pass. Task-owned preview/probes and staging,
  extraction and rollback copies are removed at closure. No publication or commit;
  physical native input, VoiceOver and recipient-Mac acceptance remain separate.

## Profile Palette Width Delivery — 2026-10-26 (Superseded)

[Run 203](../run/run-20261026-203-profile-palette-width.md) supersedes Run 202's
distribution with tooltip-free menu choices, a frame matching the trigger
background and equal painted tag widths. Version remains 0.0.1.

- Scoped PASS: ten geometry/tooltip/reachability checks at four Chromium and three
  WKWebView viewports, plus ten selection/save/focus/dismissal checks per engine.
  This presentation-only correction does not repeat backend suites or establish
  broader physical native/recipient-Mac acceptance.
- Refreshed settings JS/CSS and app signature; all 69 packaged data assets match
  source. Strict signatures, private-path inspection, ZIP CRC and extracted file/
  symlink/mode inventory parity pass. Actual app/web serve matching assets and
  pass health/settings/Sessions plus six WKWebView startup checks. Three saved
  configurations remain byte-identical; one app/backend and web server remain live.
  No backend/native compilation, dependency or model download.
- ZIP: 201656526 bytes; SHA-256
  `ab1c3cb72a009e5c572dc87d57a8a7ab5892acf26a1e7c064b3706f0974bd455`.
  App regular-file bytes: 576552243. Distribution: 4715 regular files, 28 internal
  symlinks; inventory SHA-256
  `364409e0d6e06f841a05a5d6d2db3a63ca07d46b5fe3b3e70d436afffd26c018`, using the established compact JSON inventory definition.
- Final app/ZIP/checksum remain in `dist/`. Privacy, JS syntax, whitespace and
  artifact-catalog checks pass. Task-owned preview/probes and staging/extraction/
  rollback copies are removed at closure. No commit or publication; existing
  native-input, VoiceOver and recipient-Mac evidence limits remain separate.

## Pin Order And Palette Focus Delivery — 2026-10-26 (Current)

[Run 204](../run/run-20261026-204-pin-order-and-palette-focus.md) supersedes Run
203's distribution. Version remains 0.0.1. It restores sorting by the displayed
home-abbreviated path when cached workspace names mix old and new formats, and
corrects pointer/keyboard focus in the profile palette.

- Scoped PASS: 18 pin behavior/template tests, including a regression for one
  incrementally refreshed name among legacy names. The synthetic browser route
  places Git paths alphabetically before non-Git paths. Actual app/web HTML
  readback confirms the reported first group is restored. Pin membership and
  timestamps remain identical; no data migration or imported-record rewrite.
- Native WKWebView sequential pointer input reproduces the SVG-hit focus error;
  the corrected menu passes nine center/edge states, two keyboard focus states
  and saved-choice reopening. Chromium sequential menus, mixed keyboard/pointer
  input, dismissal, geometry and accessible names pass. The
  [design receipt](eval-0139-design-standalone-test-app.md#palette-pointer-and-keyboard-focus--2026-10-26)
  records input modality and evidence limits.
- Frozen Python backend rebuilt offline from the locked existing package cache;
  unchanged native host reused. All 105 frozen local modules and 69 packaged
  data assets match source. No model download or dependency upgrade. Deep strict
  ad-hoc signatures, raw/compressed private-path inspection, ZIP CRC, internal
  symlinks and extracted inventory parity pass.
- Actual app/web health/settings/Sessions and served asset checks pass after
  sequential restart. Six WebKit cookie/startup checks pass. Three saved
  configurations remain byte-identical. One native app/backend and the web server
  remain running from durable paths.
- ZIP: 201657461 bytes; SHA-256
  `6b5417d8935a6d78ac14579343234a22dca130cac37193cddda7cd9fae866ed1`.
  App regular-file bytes: 576552834. Distribution: 4715 regular files, 28 internal
  symlinks; inventory SHA-256
  `6fb7653d5a8817904c1e1d99d51f7c92eed2534f1ce1af8e8b096f0f8900ea40`,
  using the established compact JSON path/type/size/hash/mode and link-target
  definition. App, ZIP and checksum remain in the existing `dist/` locations.
- Privacy, JS syntax, whitespace and catalog checks pass. Task-owned synthetic
  preview/probes, isolated build environment/cache, staged/extracted apps and
  rollback copies are removed at closure. No commit or publication. Physical
  Tauri input, VoiceOver, the pending native-picker confirmation and recipient-Mac
  acceptance remain outside this scoped result.
