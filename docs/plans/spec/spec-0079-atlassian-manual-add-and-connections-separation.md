# SPEC-0079: Atlassian Manual Add And Connections Separation

## Metadata

- ID: `spec-0079`
- Status: `approved`
- Run ID: `run-20260829-89`
- Attempt: `1`
- Parent Feature: [FEAT-0079](../feature/feat-0079-atlassian-manual-add-and-connections-separation.md)
- Parent PRD: [PRD-0014](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `registration contract -> Add entry -> structural handoff -> Connections -> docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Source Set

- Human decision: approve each PRD-0014 Feature sequentially and continue to
  completion.
- Parent Feature and PRD: FEAT-0079 and PRD-0014.
- Passed foundations: FEAT-0062/0063 access and local-registration contracts,
  FEAT-0075 Explorer family/state, FEAT-0077 hierarchy/list, and FEAT-0078
  selected Item preview.
- Golden runtime sources: current URL recognizer/registration service, current
  access binding and connected-discovery services, current Explorer action
  region, Workstream secondary-settings composition, and FEAT-0078 modal
  lifecycle.
- Durable baselines: Product Model, Atlassian Source Memory, Design
  Constitution, Design Evaluation, and Interaction Evaluation.
- Alignment skill: `screen-alignment` in `extend` mode.

## Implementation Goal

- Make Add one locally inferred Atlassian URL task, keep it executable as a
  dedicated server page and progressively enhance it as a bounded Explorer
  dialog/sheet, and move every optional access or connected-discovery concern
  to a separate Connections destination without changing remote authority.

## Route And Ownership Contract

- `/atlassian` is the Explorer only. Its action order starts with primary
  `Add`, retains explicit `Refresh preview`, and exposes `Connections` as an
  ordinary link inside a secondary native overflow disclosure. The disclosure
  uses links and native disclosure behavior, not an ARIA menu role with
  unimplemented arrow-key semantics.
- Canonical Add entry is `GET /atlassian/add`; canonical optional setup is
  `GET /atlassian/connections?view=jira|wiki`. `jira` and `wiki` render `200`.
  `confluence` redirects with `303` to `view=wiki`; omitted, `all`, or an
  unsupported value redirects with `303` to `view=jira`. Connections never
  creates an All-service remote configuration form.
- Legacy `GET /atlassian?mode=setup&method=url` redirects with `303` to Add.
  Legacy `method=connected` redirects with `303` to Connections while
  preserving a compatible service, catalog Run, and bounded notice where
  present. The legacy combined setup composition is never rendered.
- Add, Connections, and Explorer use separate server contexts. Direct Add does
  not load Browse inventory, registered scopes, Source Instances, access,
  capability, or discovery state. Connections does not load the Explorer
  hierarchy/list/detail or render the Add form.
- Existing POST paths remain stable: `/atlassian/register` owns manual URL
  registration; `/atlassian/access`, nested connection update, Space discover,
  and candidate registration remain Connections-owned actions. Every access,
  update, discovery, and candidate error or non-handoff success returns to the
  canonical Connections page rather than a legacy setup URL.

## One-URL Add Contract

- The Add first state contains exactly one visible required user input:
  `url`, an HTTP(S) Atlassian URL capped at `8,000` Unicode code points. A
  bounded hidden local `return_to` is navigation state, not a second user
  choice. No service selector or hidden service, Site selector, Provider,
  Source Instance, connection reference, capability, runner, or discovery
  control appears in the form.
- The shared form decoder remains bounded to `128` fields and a `160 KiB`
  encoded body. That envelope is intentionally large enough for the worst-case
  percent encoding of one `8,000`-code-point URL plus the bounded `return_to`;
  it does not lower the user-visible URL limit based on character encoding.
- Jira issue/project and Confluence Page/Space recognition remains the strict
  existing recognizer. Key-only text, REST endpoints, unsupported paths,
  non-HTTP(S) input, fragments as identity, malformed hosts, and oversized
  values remain invalid.
- Preview calls `/api/atlassian/registration-preview?url=...` without a service
  parameter. It returns only inferred service, kind, normalized URL/domain, and
  available key/ID. It performs no SQL mutation, Source Instance/access lookup,
  provider/model/capability call, source scan, Refresh, maintenance Run, or
  network read.
- `/atlassian/register` and its direct registration helper read `url` as their
  only identity input; the route additionally reads safe `return_to` as
  navigation state. Service is derived from the recognized locator and is the
  single registration authority. Add never passes an expected service into
  recognition, and a legacy HTTP `service` field is ignored rather than
  narrowing or overriding the inferred result.
- The internal registration helper wraps Site resolution plus Item/Space
  creation or reuse in one savepoint so late identity, URL, or persistence
  failure leaves no orphan Site, Space, Item, External Resource, Source
  Instance, binding, or Run even when the helper is called outside the route's
  outer transaction.
- Idempotency is the existing pre-confirmation identity: the same Site and
  exactly normalized URL reuses one local reference. Similar unconfirmed Jira
  keys or Confluence Page IDs appearing at different normalized URLs are not
  silently merged; remote-confirmed identity remains the only later alias
  authority.
- Validation/conflict failure returns `422`, preserves the entered URL, marks
  it invalid, exposes one adjacent alert and local correction path, and commits
  no partial row. Preview failure never disables ordinary server submission.
- A successful created or reused Item redirects with `303` to a fresh
  service-specific Explorer state carrying owner `site_id`, known `space_id`
  when present, and selected `item`. When no Space is persisted, it carries
  Site-local `structural_scope=unclassified` instead of inferring containment
  from a key embedded in the submitted URL. Query and unrelated filters reset
  so the Item is reachable. A reused archived Item additionally carries
  `attention=archived`; registration never silently unarchives it.
- A successful manual Project/Space redirects with `303` to its explicit
  service, owner `site_id`, and `space_id`, with no Item selection. Created and
  reused notices remain distinct. The same structural handoff is used after an
  explicitly confirmed connected-discovery candidate is registered.

## Empty Structural Handoff Exception

- The Explorer normally projects only Item-backed Service/Site/Space nodes.
  FEAT-0079 adds one narrow URL-backed exception: when a valid explicit
  service, owner `site_id`, and persisted `space_id` select a Space with zero
  Items in the current eligible projection, the hierarchy injects only that
  active `0`-count Space and its owner Site/service ancestors. This includes a
  physically empty Space and a known Space whose archived/query/filter state
  currently excludes every Item.
- The exception is derived from the explicit structural URL and targeted
  persisted Space/Site ownership, never from a transient notice. Reload,
  back/forward, and direct entry therefore produce the same active branch.
- Root and sibling projections remain Item-backed. The empty branch is not
  shown without its explicit selection, does not change the eligible/list
  population, and preserves `active node count == list count == 0`.
- The active label comes from the persisted Site/Space owner. The empty result
  explains that the current Explorer scope contains no matching registered
  Item links and, on an Add/candidate handoff, that registration did not
  discover remote Items. It never fabricates an Item, nested hierarchy, remote
  confirmation, or Refresh.

## Add Presentation And Interaction Contract

- The Explorer server-renders the isolated Add form inside a closed native
  `<dialog>`. The ordinary Add anchor still points to `/atlassian/add`; when
  supported JavaScript is active, the controller prevents that navigation and
  opens the embedded form with `showModal()`.
- Wide (`>920px`) Add is a centered bounded dialog using the existing dialog,
  scrim, radius, elevation, and drawer-width tokens. Compact (`701–920px`) is a
  right drawer. Narrow (`<=700px`) is a full-width sheet below the sticky shell
  with its own vertical scroll and full-width primary/secondary actions.
- The direct `/atlassian/add` page renders the same form content as one focused
  in-flow card and never pretends to be a modal. It is the no-script, failed-
  enhancement, reload, and direct-entry path.
- On open, the URL input receives visible focus. The named dialog owns one
  modal lifecycle, native top-layer/background isolation, contained Tab order,
  Escape, explicit close, and focus restoration. Add has modal priority while
  open; the compact Item preview must not simultaneously claim dialog/inert/
  body-lock ownership.
- Cancel, Escape, or close restores the exact Add trigger when it remains
  reachable. If a breakpoint change makes an existing selected Item sheet the
  valid modal owner, closing Add re-establishes that sheet and focuses its
  heading rather than focusing behind it. A missing trigger falls back to the
  Explorer heading.
- `return_to` accepts only the existing canonical same-origin `/atlassian`
  state, is revalidated at GET, POST, and emitted-link boundaries, and appends
  the stable Add-trigger fragment only after validation. External, oversized,
  malformed, setup, or structurally incompatible values fall back to root.
- URL preview debounces input, aborts prior requests, and ignores stale
  responses without moving focus. Preview text is a polite live status inside
  the active Add surface.
- Enhanced dialog submission uses the same POST with
  `X-LocalBrain-Partial: atlassian-add`. Pending state is announced, marks the
  form busy, prevents duplicate submission, and keeps the modal from being
  dismissed until the bounded local response settles. A `422` replaces only
  the Add form state, retains input, and focuses the owning invalid field or
  alert. A redirect performs normal full navigation to the canonical Explorer
  destination. Enhancement failure falls back to ordinary form submission;
  exact-URL idempotency makes a repeated post safe if a response was lost.
- Successful navigation focuses the destination selected Item preview or
  structural/results heading, not the old Add trigger. Errors remain in the
  Add surface; only later dismissal restores the trigger.

## Connections Contract

- Connections has reversible Jira/Wiki service tabs and owns only persisted
  registered-scope orientation, access creation, connection inventory/editing,
  readiness/capability facts, connected discovery, current catalog Run state,
  and explicit candidate confirmation.
- Connections GET reads only persisted Site and Space rows, Source Instance/
  binding/Provider/configuration/enabled state, cached local capability and
  executor/runner readiness facts, aggregate Item counts grouped by Site, and
  a selected local catalog result. Item rows may contribute only through SQL
  aggregate counts and are never materialized into the Connections read model;
  Item URLs, remote state/content, local memory, classification, evidence,
  organization, Session/Document bodies, provider/model data, and live remote
  sources are not read.
- The wide page uses the existing secondary-settings family: registered scope,
  connection inventory, and candidate results in the fluid main column;
  access setup and connected discovery in a bounded secondary tools rail.
  Compact enters document flow, and narrow becomes one inventory → access →
  discovery → result sequence with native disclosures and touch controls.
- With zero connections, access setup is the first open recovery owner when a
  registered Site exists. Discovery remains optional and cannot make Add,
  Explorer, exact search, detail, classification, or later Sync unavailable.
- Access setup preserves the passed Site/service/Provider/config-reference
  rules. Connection edit authority comes from its Source Instance/Site path;
  no hidden service field may override it. Edits preserve immutable Provider/
  bound-reference identity and only the approved enabled/reference behavior.
- Connected discovery preserves target `site_id` → compatible `binding_id` →
  Claude or Codex runner order. The server resolves Site, Source Instance,
  service, and domain from the binding, rejects a Site/binding mismatch before
  capability or Run work, and never trusts a posted domain/service identity.
  Changing Site filters and clears an incompatible binding.
  Missing executor, runner, permission, capability, or binding remains a
  Connections-scoped readiness error and creates no Run.
- A valid discovery submit starts at most the current approved single bounded
  remote read with `call_budget=1`: Jira metadata admits at most `100` project
  results and Confluence metadata at most `200` Page results. It registers
  nothing automatically and retains queued/running/partial/failed/no-result
  truth. The local candidate projection remains explicitly partial and capped
  at `200`.
- Candidate confirmation posts only `catalog_run` plus one candidate key. The
  server re-reads that Run's service, Source Instance, target Site, and bounded
  candidate payload, then resolves name/remote ID from the selected candidate.
  Client-posted Site, Source, service, name, or remote ID is never identity
  authority. A missing, mismatched, or no-longer-present candidate creates no
  Space. One explicit confirmation persists at most one local Space and starts
  no additional remote work.
- Access, connection-edit, discovery, and candidate forms own separate retained
  state and error identity. An error opens and focuses only its owning
  disclosure/row/result; values from one form never populate another.
- Successful access/update redirects to the canonical connection row fragment
  and focuses it. Discovery redirects to its canonical catalog Run state and
  retains polling. Confirmed candidate registration uses the structural
  Explorer handoff defined above.

## Out-Of-Scope Behavior

- New Provider types, credentials, capability checks, discovery operations,
  remote writes, automatic discovery, or automatic candidate registration.
- Local evidence Sync, Refresh execution changes, AI retrieval, Item detail or
  exact-query changes, nested Page/issue hierarchy, or general display of
  empty Spaces outside the selected structural exception.
- Merging URL aliases from an unconfirmed key/Page ID, creating a Source
  Instance during Add, or persisting dialog/disclosure UI state.
- Schema changes.

## Affected Surfaces

- `src/localbrain/atlassian_registration.py`
- `src/localbrain/atlassian_browse.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/atlassian.html`
- a shared Add form partial and dedicated Add page
- a dedicated Connections page
- `src/localbrain/static/atlassian.js`
- `src/localbrain/static/styles.css`
- registration, Browse, route, UI-contract, and browser tests
- Product Model and Atlassian Source Memory for the selected empty-Space
  projection exception and canonical action ownership

## Surface Lanes

- Registration contract:
  - responsibility: service inference, exact-URL idempotency, helper atomicity,
    result handoff facts, and zero hidden I/O
  - dependency order: first
  - evaluator ownership: contract, functional
- Add entry:
  - responsibility: isolated form, direct page, progressive native dialog,
    preview/submit state, focus, fallback, and safe cancel
  - dependency order: after registration contract
  - evaluator ownership: design, functional, ux-heuristic
- Structural handoff:
  - responsibility: Item selected URLs, archived reachability, selected empty
    Space branch, truthful zero state, and count parity
  - dependency order: after registration result shape
  - evaluator ownership: contract, functional, ux-heuristic
- Connections:
  - responsibility: dedicated route, settings-family composition, separated
    form states, existing access/discovery semantics, and candidate handoff
  - dependency order: after route separation
  - evaluator ownership: contract, design, functional, ux-heuristic
- Documentation:
  - responsibility: owner parity without duplicating implementation detail
  - dependency order: after runtime behavior is fixed
  - evaluator ownership: contract

## State And Interaction Contract

- Add default: empty URL, local-only orientation, no service or connection
  choice, no remote work.
- Add preview: inferred service/Site/kind/identity; input focus is unchanged.
- Add invalid/conflict: URL retained, adjacent alert, no partial mutation.
- Add pending: one busy local submit, no duplicate or dismiss race.
- Add success: Item selected Explorer or explicit Project/Space branch with a
  truthful created/reused notice.
- Add cancel: current Explorer DOM/state remains and focus returns to its
  reachable trigger/fallback.
- Connections empty/unavailable: local Add remains complete; one scoped
  recovery disclosure explains access only.
- Connections discovery: target, binding, runner, readiness, Run, candidate,
  and confirmation remain separate observable states.
- Legacy setup: canonical redirect; combined setup markup never renders.

## Screen-Alignment Consistency List

- Retained components: shell, page heading, semantic buttons, native details,
  form/field/help/error/status families, connection rows, editor panels,
  catalog candidates, and FEAT-0078 focus/inert lifecycle principles.
- Retained visual roles: semantic spacing, type, color, border, radius,
  elevation, drawer, breakpoint, touch-target, and scroll tokens.
- Deliberate change: one new native-dialog presentation of an existing form and
  a dedicated settings composition; no new visual system or persistence.
- Add contains no hidden Connections subtree. Connections contains no hidden
  Add form.
- New design-system component: none; native dialog and existing secondary-
  settings primitives are composed for this surface.

## Contract Surfaces

- Add input/output: one URL, local inferred locator, created/reused result,
  safe return, and canonical selected/structural redirect.
- Structural projection: explicit persisted empty Space only, targeted owner
  resolution, zero count, no sibling/root leakage.
- Connections input/output: service-scoped local settings, path-owned
  connection edits, Site/binding/runner discovery, existing bounded Run, and
  Run-owned explicit candidate confirmation.
- DOM/JavaScript: one active modal owner, normal Add anchor/form fallbacks,
  stale-safe preview, bounded submit state, native overflow link, and scoped
  form errors.
- External boundary: Add performs zero provider/model/network/capability/Run
  work; only explicit Connections discovery may start the already approved
  bounded remote read.

## Required Evaluators

- Contract: inferred service authority, atomicity/idempotency, route ownership,
  selected empty-Space exception, bounded I/O, and owner-doc parity.
- Design: screen-alignment extend consistency, isolated dialog/direct page,
  Connections settings composition, action hierarchy, four-width containment,
  and long/error/empty states.
- Functional: four URL kinds, create/reuse/failure, exact redirects, legacy
  normalization, no-script/partial fallback, modal lifecycle, all existing
  access/discovery/candidate behavior, and regressions.
- UX heuristic: one-field task clarity, focus/restoration, one-modal ownership,
  error recovery, secondary Connections discoverability, readiness truth, and
  narrow reading order.

## Acceptance Mapping

- Unit tests cover all four URL kinds without HTTP service input, exact
  normalized-URL reuse, unconfirmed alias non-merge, helper savepoint rollback,
  result Site/Space/attention facts, and zero external work.
- Route/template tests cover isolated Add/direct/no-script/partial-error state,
  one required visible field, safe return, created/reused Item and Space
  redirects, archived selection, legacy redirects, and absence of setup
  coupling.
- Browse tests cover explicit persisted Space injection when the current
  eligible projection is zero (physically empty, archived-only, and filtered),
  owner labels, reload/direct parity, active count/list zero, root/sibling
  omission, and truthful scope-relative empty copy.
- Connections tests cover empty/multiple access paths, bind/update validation,
  immutable identity, target-compatible filtering, unavailable/current runner
  and executor, Site/binding mismatch before execution, single bounded
  discovery, polling/partial/no-result/failure, tampered candidate identity
  rejection, and explicit Run-owned candidate handoff.
- Chrome at `1440`, `920`, `700`, and `320` covers Add default/preview/error,
  dialog/drawer/sheet geometry, focus/inert/Escape/close, one modal owner,
  direct-page/no-script fallback, Connections empty/populated/error states,
  long URL/domain containment, and zero page overflow.
- Focused/full tests plus privacy, JavaScript, diff, data-model, and artifact-
  catalog checks cover Explorer/detail/Refresh and source-owner regressions.

## Evaluation Focus

- Confirm no rendered or trusted service choice and no access/discovery field
  in Add, including hidden DOM and form payloads.
- Confirm invalid or late-failing registration leaves no Site/Space/Item/
  Resource/Source/Run residue.
- Confirm a new empty Space is reachable only through its explicit URL-backed
  active branch and never appears as an invented sibling or Item.
- Confirm Add and Item preview never own modal focus/inert/body lock
  simultaneously.
- Confirm Connections remains discoverable in the approved secondary overflow
  and retains all passed access/discovery safety without blocking local work.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-29`: approved for RUN-89 after FEAT-0078 passed and the owner had
  authorized sequential Feature approval and execution. Connections overflow
  ownership and selected Item success were already resolved by the Feature.
- `2026-08-29`: preflight locked exact normalized-URL reuse without unconfirmed
  alias merge, helper-level atomicity, archived Item reachability, and the
  explicit persisted empty-Space `0`-count branch required for truthful
  Project/Space handoff.
