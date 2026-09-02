# SPEC-0080: Atlassian Local Evidence Sync

## Metadata

- ID: `spec-0080`
- Status: `approved`
- Run ID: `run-20260829-90`
- Attempt: `1`
- Parent Feature: [FEAT-0080](../feature/feat-0080-atlassian-local-evidence-sync.md)
- Parent PRD: [PRD-0014](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `persisted-source projection -> reconciliation -> action/report -> Explorer continuity -> docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Source Set

- Human decision: approve each PRD-0014 Feature sequentially and continue to
  completion.
- Parent Feature and PRD: FEAT-0080 and PRD-0014.
- Passed foundations: FEAT-0047 bounded Atlassian evidence, FEAT-0073 bounded
  persisted Session references, FEAT-0075 Explorer family/state, FEAT-0077
  hierarchy/list, FEAT-0078 selection continuity, and FEAT-0079 separated Add,
  Connections, and Refresh actions.
- Golden runtime sources: `atlassian_evidence.py`, `session_references.py`,
  persisted Session/Context tables, current Explorer template/controller, and
  the Sessions Sync form/status family.
- Durable baselines: Product Model, Architecture, Privacy, Atlassian Source
  Memory, Design Constitution, Design Evaluation, and Interaction Evaluation.
- Alignment skill: `screen-alignment` in `extend` mode.

## Implementation Goal

- Add one explicit, zero-input local action that reconciles Atlassian Item URL
  evidence already available in bounded persisted Session and Local Context
  projections, reports honest source and target outcomes, and updates the
  current Explorer without invoking source import or remote work.

## Persisted Input Contract

### Session Projection

- The considered Session source population is every persisted Session. The
  eligible subset is `work` + `primary` + `full`; Maintenance Sessions,
  Subsessions, and metadata-only Sessions are source-level excluded outcomes
  and never contribute a URL candidate.
- Sync never reads Claude/Codex JSONL, `source_files.path`, the filesystem,
  Session conversation bodies, or `activity_events.text`; it never invokes a
  parser or Session source synchronization. Sync treats the fingerprint and
  extractor version already recorded by `session_reference_scans` as the input
  revision; it does not recompute that identity from `source_files`.
- The only Session candidate authority is the bounded
  `session_reference_evidence` projection owned by FEAT-0073. A usable Session
  requires a matching `session_reference_scans` row in `ok` or `partial`
  state and the current reference extractor version. The row's recorded
  `source_fingerprint` is the retained projection's input revision; Sync does
  not reopen `source_files` to independently recompute its freshness.
  Missing, extractor-stale, or error projection state is one source-level
  `unavailable` outcome and retains all prior Atlassian evidence.
- A `partial` Session projection reconciles its retained rows and reports the
  scan's exact `observed_target_count - retained_target_count` as generic
  reference-projection overflow. That difference is not labeled as an
  Atlassian URL count because the omitted target kinds are unknown. It makes
  the action outcome partial; it does not read a source file to reconstruct
  the omitted targets.
- An admitted Session row has `target_kind = url`, a non-empty normalized URL,
  a stable source path/event/line/ordinal location, and evidence kind
  `user_mention`, `assistant_mention`, or `tool_result`. `resource_read` is not
  admitted because that projection can represent call arguments and key-only
  target hints rather than an approved result URL. An already-resolved
  `atlassian_item` row is also not reinterpreted because its original URL
  versus key-only form is no longer observable.
- FEAT-0073 intentionally removes URL query/fragment data and drops unsafe or
  unresolved references before persistence. Sync reports only candidates and
  overflow actually observable in that projection. It never invents exact
  counts for discarded key-only, unsafe, query-only, or opaque values; the UI
  states that these are outside the retained Session projection.
- Existing FEAT-0073 caps remain the executable Session bound: at most `100`
  retained targets and `50` locations per target for one Session. Sync reads
  rows in stable Session ID, target key, source path, event, line, and ordinal
  order.

### Local Context Document Projection

- Sync enumerates persisted Context Documents and revalidates each owning root
  immediately before mutation. Only an enabled, readable root in `ready` state
  contributes its persisted `body` and `content_hash`; no file or provider is
  opened.
- A disabled Document is a source-level excluded outcome and Sync performs no
  mutation for it. An orphaned, unreadable, or non-ready enabled Document is
  source-level unavailable and retains prior evidence. A Document deleted
  before its turn is unavailable and creates no replacement identity.
- Eligible persisted Document bodies use the existing visible-URL extractor,
  strict configured Item recognizer, and content-hash fingerprint. The body is
  read from SQLite as `64 KiB` UTF-8 byte chunks with an incremental decoder,
  an at-most-`8,000`-code-point URL carry, and continuous line/ordinal state;
  it is never materialized as one unbounded application string. The same pass
  may count standalone Jira-key occurrences outside URL spans as key-only
  skips, but never treats them as Item identity.
- The first `500` visible URL candidates in source order retain the existing
  `MAX_SOURCE_EVIDENCE` reconciliation limit. The chunked pass still counts
  later visible URL candidates through the finite persisted body, reports
  their exact generic-URL overflow as `document-url-limit`, and makes the
  action partial. It does not call those omitted candidates Atlassian URLs and
  does not persist a cursor or rotate which prefix is admitted on retry.
- Standalone Jira-key occurrences outside URL spans are counted only as
  key-only candidate skips; they never become identity. Bare Confluence
  numbers are not guessed.
- The action performs one finite, stable-ID pass over the currently persisted
  source rows. Per-Session retained-reference and per-Document evidence caps,
  rather than an arbitrary age window, bound candidate work without silently
  omitting an otherwise eligible source.

## Recognition And Reconciliation Contract

- The admitted locator remains FEAT-0047's configured Jira issue or Confluence
  Page HTTP(S) URL. Jira Project, Confluence Space, REST, key-only, malformed,
  credential-bearing, unsupported, unknown-domain, or ambiguous-domain values
  create no Item or evidence.
- Configured scope is exactly one current local Site/service mapping derived
  from enabled bindings or persisted Item/Space ownership. A Source Instance
  is optional for local evidence and no access readiness is required.
- A recognized target creates or reuses the existing reference-coverage Item
  through the current stable stub contract. Existing Item ID, exact URL
  identity, attention, remote state/content, local memory, classification,
  Workstream/Thread organization, and Refresh history are never reset or
  promoted by Sync.
- Session reconciliation is merge-only. It may insert a missing bounded
  `atlassian_item_evidence` location or reuse an exact existing location, but
  it never updates `atlassian_evidence_scans`, deletes Session evidence, or
  overwrites a richer observed URL/title/remote ID with the reduced Session
  projection. Authoritative Session source sync remains the replace-derived
  owner.
- An exact existing Session evidence location is matched by Item, Session,
  source path, event, line, ordinal, normalized URL, and channel before
  insertion. A repeat action performs no timestamp-only write for that
  location.
- Eligible Document reconciliation reuses FEAT-0047's complete persisted-body
  replace semantics and scan fingerprint whenever chunking reaches EOF and
  therefore fixes the complete deterministic first-`500` evidence set.
  Obsolete evidence for that Document may disappear; the Item and every
  independently owned state remain. More-than-`500` overflow is user-visible
  partial but may still replace to that complete bounded set and advance the
  Document scan. Only a chunk/decoder/reconciliation failure before the set is
  known remains merge-only or no-write and retains prior scan/evidence state.
- Each source owns a savepoint or transaction and a bounded error conversion.
  One source failure retains its prior valid evidence, increments `failed`,
  and does not roll back committed or successfully reconciled peer sources.
- The action performs no schema migration and creates no maintenance Run,
  Refresh record, connected-discovery result, relationship, Suggestion, or
  source-sync record.

## Report And Outcome Contract

- The aggregate shape is fixed and keeps unlike units separate:
  - `status`: `complete`, `partial`, `failed`, or `busy`;
  - `sources`: `considered`, `eligible`, `scanned`, `partial`, `unavailable`,
    `failed`, and `excluded`, with
    `eligible = scanned + unavailable + failed` and `partial <= scanned`;
  - `items`: action-wide disjoint distinct External Resource ID counts `new`
    and `reused`;
  - `evidence`: distinct evidence-key counts `new`, `reused`, and `removed`;
  - `candidate_skips`: `key_only`, `unsafe_url`, `unsupported_locator`,
    `unconfigured_domain`, `ambiguous_site`, and `invalid_location`;
  - `scope_limits`: `session_projection_sources`,
    `session_reference_overflow`, and `document_url_overflow`.
    `session_projection_sources` counts every eligible Session actually scanned
    through the retained FEAT-0073 URL projection, including both complete and
    partial projections; unavailable, failed, and excluded Sessions do not
    enter it.
- Every considered source has one fixed-size record with kind (`session` or
  `document`), positive `local_id`, outcome (`excluded`, `complete`, `partial`,
  `unavailable`, or `failed`), counts (`urls`, `new_items`, `reused_items`,
  `new_evidence`, `reused_evidence`, `removed_evidence`, `skipped`), and fixed
  reason codes. Per-source reused Item sets may overlap; aggregate Item counts
  are distinct and intentionally are not their sum.
- The reason vocabulary is `ineligible-session`, `disabled-document`,
  `session-projection-missing`, `session-projection-stale`,
  `session-projection-error`, `session-projection-partial`,
  `context-unavailable`, `document-url-limit`, `invalid-location`,
  `unsafe-url`, `unsupported-locator`, `unconfigured-domain`,
  `ambiguous-site`, and `reconciliation-error`.
- No source path, source title, body, excerpt, raw exception, URL, or Item
  identity is returned. Source records use only `Session #ID` or
  `Local Context #ID` orientation and never become source-content identity.
  Sources are fetched and processed in database batches of `100`; no hard
  source prefix cap may starve later IDs.
- The aggregate always remains visible. Per-source consequences appear in one
  collapsed, internally scrollable native disclosure so successful peers,
  excluded/unavailable inputs, and failed sources remain independently
  inspectable without replacing the Explorer list. There is no selected-source
  retry; visible recovery states that Sync repeats the whole batch.
- `complete` means every eligible source completed; candidate skips and zero
  eligible/zero targets are valid complete outcomes. `partial` means any
  scanned-partial, unavailable, or failed source with at least one scanned, or
  an unavailable-only eligible set. `failed` means `scanned = 0` and
  `failed > 0`, or an action-level fatal error. `busy` is not failure.
- Retry is the same whole-scope Sync action. It never becomes a source selector
  or per-link confirmation flow.

## Request, Single-Flight, And Receipt Contract

- `POST /atlassian/sync` is the single executable route for ordinary and
  enhanced use. The form has zero execution inputs. Its only field is one
  `return_to` value capped at `4,000` characters; total form size is `8 KiB`.
  Unknown or repeated fields return `422` before mutation. `return_to` is
  navigation state and is revalidated through the canonical Explorer
  allowlist plus structural/service database normalizer before and after work.
- The local application process owns one non-blocking Sync lock. A concurrent
  tab/request receives `busy`, makes zero writes, and can retry after the
  existing action completes. The supported deployment is LocalBrain's one
  local application process; this Feature does not invent a cross-process job
  or durable Run protocol.
- Ordinary submission uses POST/Redirect/GET. Every bounded outcome, including
  complete, partial, failed, and busy, redirects with `303` to the sanitized
  current Explorer plus one server-generated opaque receipt token. The receipt store is process-local,
  thread-safe, contains only the bounded aggregate and minimal per-source
  outcome records above, expires after `5` minutes, retains at most `32`
  entries, and never persists to SQLite.
- A receipt is bound to the exact normalized Explorer return path that created
  it. It is generated with `secrets.token_urlsafe(24)` and renders only when
  the current canonical state, excluding the receipt itself, equals that
  binding. Mismatch behaves like an invalid receipt.
- A valid receipt may be rendered repeatedly until expiry so browser reload
  does not resubmit the action. Unknown, malformed, evicted, expired, or
  process-restart receipts render the normal idle scope message, perform no
  work, and never become count authority. Explorer links and future
  `return_to` values omit the receipt.
- Enhanced submission sends the same POST with
  `X-LocalBrain-Partial: atlassian-local-evidence-sync` and receives the same
  bounded report as `{ "report": <exact-report> }` JSON. Complete, partial, and
  failed reports use `200`; busy uses `409`; request validation uses bounded
  `422` JSON and performs no mutation. A non-abort request failure restores the
  same Sync action and reports a local retry; it never falls through to Refresh.

## Explorer Presentation Contract

- Heading action DOM and visual order is `Sync` secondary POST, `Add` primary,
  then native `More` containing `Refresh preview` and `Connections`. This keeps
  the approved two top-level product actions and one dominant action while
  remote all-known Refresh remains explicit but secondary. Sync is global
  persisted-source work and never appears inside All/Jira/Wiki scope controls.
- One stable full-width Sync region follows the heading and precedes the
  service toolbar. Its idle copy states eligible primary Sessions + enabled
  Local Context Documents, local-only execution, and no remote read. The Sync
  button references that visible scope copy with `aria-describedby`.
- Running uses info/status treatment; change and zero completion use
  success/status; partial uses warning/alert; fatal uses danger/alert. The five
  user-facing meanings remain new=`success`, reused=`info`, skipped=`neutral`,
  unavailable=`warning`, failed=`danger`. Aggregate source and target counts
  lead; fixed reason and minimal per-source outcomes remain in a collapsed,
  height-bounded native disclosure.
- Starting disables and marks only Sync busy. Explorer search, hierarchy,
  list, current preview, Add, and navigation remain readable and interactive.
  Start and completion do not move focus unless disabling left focus on body;
  that fallback restores Sync with `preventScroll`.
- If Add or a compact Item preview owns modal focus when Sync completes, the
  result DOM may update but the modal, inert/body-lock, announcement, and close
  restoration owner do not change. The result announcement is deferred until
  modal close, then emitted once.

## Enhanced In-Place Refresh Contract

- Enhanced completion captures the latest state at completion time, not the
  state at start. It fetches the current canonical Explorer URL and replaces
  only named service toolbar/count, wide hierarchy, compact hierarchy, and
  results/list fragments. Heading/actions/status, Add dialog, selected preview,
  URL, and current history entry remain mounted.
- Stable selectors are `data-atlassian-explorer-toolbar`,
  `data-atlassian-hierarchy-rail`, `data-atlassian-hierarchy-compact`, and
  `data-atlassian-results`. The response must contain exactly one of each.
- Before replacement the controller records window, result-list, and preview
  scroll, compact hierarchy disclosure, active element, selected Item ID, and
  the first visible result row plus its offset. It restores the row anchor when
  still present and raw list offset otherwise; page/preview scroll, disclosure,
  selected state, URL, and history are unchanged.
- Root click delegation remains mounted. Any direct list scroll listener is
  rebound exactly once to the replacement list, and current history state is
  replaced with the restored offsets without adding an entry.
- Item-selection requests that would make the patch stale are aborted or
  generation-guarded. After replacement the existing modal synchronizer runs
  with `focus: false` so newly inserted background fragments remain inert when
  a compact preview is open.
- No-script completion preserves semantic service/structure/query/filter/item
  URL state and shows its verified receipt beside the action. Exact pixel
  scroll and arbitrary focus restoration are progressive-enhancement behavior;
  ordinary navigation retains a reachable selected row/heading and native
  browser history.

## Responsive Contract

- At `1440`, heading copy and Sync/Add/More remain one intrinsic row; the Sync
  region spans the content width below it.
- At `920`, the heading stacks and Sync/Add/More form one equal, full-width
  three-column row without changing DOM order.
- At `700` and `320`, Sync and Add form the first two columns and More follows
  as a bounded full-width row. Controls use touch height, labels may wrap, the
  disclosure is bounded to the viewport, and outcome counts wrap without
  replacing the primary link list.
- No new breakpoint, visual primitive, dialog, drawer, scrim, or Run console is
  introduced. Reduced motion, focus tokens, status vocabulary, and semantic
  action families remain inherited from the Constitution.

## Zero Hidden I/O Contract

- Sync may read/write only LocalBrain SQLite state and process normalized URLs
  locally. Calls to Session/Context source scanners, filesystem readers,
  providers, MCP, capabilities, executors, runners, models, embeddings,
  connected discovery, Refresh preview/execution, and maintenance Runs are
  exactly zero.
- Stored output is limited to current Item/URL identity and bounded source
  evidence already allowed by FEAT-0047. Session/Document excerpts, prompts,
  comments, opaque tool payloads, credentials, remote bodies, and report
  receipts are never persisted.

## Out-Of-Scope Behavior

- Source import/rescan, file access, live remote work, AI retrieval, Space or
  Project discovery, key-only inference, unsafe-candidate reconstruction, or
  per-link approval.
- Durable Sync history, cross-process job coordination, maintenance Run reuse,
  background scheduling, source selectors, or a new schema table.
- Changes to Add, Connections, exact query, Item detail, classification,
  Workstream/Thread organization, or Refresh semantics.

## Affected Surfaces

- `src/localbrain/atlassian_evidence.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/static/atlassian.js`
- `src/localbrain/static/styles.css`
- evidence, Sync route, Browse/UI-contract, and browser tests
- Product Model, Architecture, Privacy, Atlassian Source Memory, and Design
  Constitution outcome mapping

## Surface Lanes

- Persisted-source projection:
  - responsibility: exact Session/Document population, readiness, caps, and
    unobservable-input honesty
  - dependency order: first
  - evaluator ownership: contract, functional
- Reconciliation:
  - responsibility: merge-only Session evidence, complete Document reconcile,
    stable Item/evidence identity, source isolation, and zero hidden I/O
  - dependency order: after projection
  - evaluator ownership: contract, functional
- Action/report:
  - responsibility: one POST, single-flight, report units/reasons, verified
    receipt, partial/fatal/busy recovery
  - dependency order: after reconciliation
  - evaluator ownership: contract, functional, ux-heuristic
- Explorer continuity:
  - responsibility: action hierarchy, stable feedback, named patch, state/
    focus/modal/scroll preservation, and responsive geometry
  - dependency order: after action/report
  - evaluator ownership: design, functional, ux-heuristic
- Documentation:
  - responsibility: source-sync, local Sync, and Refresh owner parity
  - dependency order: after runtime contract is implemented
  - evaluator ownership: contract

## Required Evaluators

- Contract: persisted input authority, merge/replace ownership, report units,
  receipts, single-flight, zero hidden I/O, and owner-doc parity.
- Design: action order, semantic outcomes, stable status, four-width layout,
  narrow density, and screen-alignment extend consistency.
- Functional: eligible/ineligible/partial/unavailable sources, new/reused/
  skipped evidence, source isolation, idempotency, receipt/return safety,
  concurrency, named patch, and Refresh regression.
- UX heuristic: local-versus-remote clarity, progress and zero/partial/error
  recovery, no focus theft, modal concurrency, list continuity, no-script
  fallback, and responsive reading order.

## Acceptance Mapping

- Persisted-only scope -> SQL trace tests forbid parser, source scan, file,
  provider, model, capability, Run, and Refresh calls.
- Session honesty -> ok/partial/error/missing/stale projection fixtures,
  admitted evidence kinds, query/key/unsafe loss disclosure, and merge-only
  prior-evidence preservation.
- Document lifecycle -> enabled ready, disabled no-mutation, unavailable
  retention, content change, no match, overflow replacement, and per-source
  failure fixtures.
- Deterministic outcomes -> distinct Item/evidence units, fixed reasons, zero,
  partial, all-failed, repeat idempotency, and peer success retention.
- Server execution -> ordinary POST/303/verified receipt, invalid/expired
  receipt, complex safe return, concurrent busy, and no resubmit on reload.
- Enhanced continuity -> completion-time state, named fragments, row anchor,
  raw scroll fallback, one listener, selection/history, pending Item request,
  and Add/preview modal-open completion.
- Chrome at `1440`, `920`, `700`, and `320` -> action grid, idle/running/change/
  zero/partial/fatal states, long counts/reasons, focus/announcement/inert,
  exact enhanced scroll, no horizontal overflow, console, and Lighthouse.
- Focused/full tests plus privacy, JavaScript, diff, data-model, schema, and
  artifact-catalog checks cover passed Explorer/Add/Connections/Refresh work.

## Evaluation Focus

- A lossy Session projection must never replace richer FEAT-0047 evidence or
  claim counts for values no longer persisted.
- `new` and `reused` must not mix Item and source-location units; unavailable
  and failed must identify source units without exposing source identity.
- A second tab must not start duplicate work, and no receipt may become a
  durable or user-supplied result authority.
- The in-place patch must use the user's latest Explorer state and must not
  break the selected preview, list history listener, or current modal owner.
- Sync must remain visibly local and independent from remote Refresh and
  optional Connections readiness.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-29`: approved for RUN-90 after FEAT-0079 passed and the owner had
  authorized sequential Feature approval and execution.
- `2026-08-29`: preflight selected the existing bounded Session-reference
  projection rather than source/body reconstruction, merge-only Session
  evidence, separate source/target/evidence units, a short-lived verified
  receipt, process-local single-flight, and named in-place Explorer refresh.
