# PRD-0012: Multiple Local AI Session Sources And Inventory Integrity

## Metadata

- ID: `prd-0012`
- Status: `passed`
- Owner role: `human`
- Created: `2026-08-02`
- Updated: `2026-08-03`
- User review status: `implemented and accepted`
- Approval mode: `completed`
- Canonical passed boundary: this PRD

## Request Summary

- Treat each independently configured local Session root as a peer user-facing
  AI source, even when two roots share one provider parser and Usage
  normalization contract.
- Continue importing the existing Claude and personal Codex sources and add the
  company Codex source without merging their native account boundaries.
- Let Sessions and Sessions Dashboard show combined totals and independently
  selectable `Claude`, `Codex`, and `Codex Company` statistics.
- Reconcile the owner's observation that Session counts can decrease over time
  and record the accepted source-mirror lifecycle without expanding this PRD
  into a new Session-retention feature.

## Source Set

### Human Request

- Continue importing the personal Codex home and additionally import the company
  Codex home.
- Present `Claude`, personal `Codex`, and `Codex Company` as peer AI source
  scopes in Sessions and Usage views. `Codex` continues to mean the existing
  personal source; no separate combined-Codex primary tab is required.
- Keep the two Codex sources on the same Codex parser, model handling, token
  normalization, and price-snapshot contracts while reporting their statistics
  independently.
- Keep the source-identity contract extensible to another local AI tool or root.
  Gemini is an illustrative future example, not an ingestion target in this PRD.
- Count every collected eligible Session except the already approved exclusions,
  including Maintenance Sessions and Subsessions where their consumer contract
  intentionally excludes them.
- Determine whether current Session counts age out or otherwise decrease rather
  than assuming the observed change is user error.

### Golden Sources

- Human direction in this request is the primary product source.
- The owner-maintained local operating note supplied with this request confirms
  two independent Codex homes:
  - personal: `~/.codex`
  - company: `~/.codex-company`
- That operating note also fixes the boundary that authentication, native
  `resume` lists, Session files, history, state databases, logs, caches, and OAuth
  state remain separate between the two homes. LocalBrain may read both Session
  roots without linking the homes to each other, while reusing the same Codex
  adapter and Usage normalizer.
- [Claude Code application-data documentation](https://code.claude.com/docs/en/claude-directory)
  confirms that native Session transcripts are deleted on startup after
  `cleanupPeriodDays`, whose default is 30 days. This is source-lifecycle
  evidence, not authorization for LocalBrain to change Claude Code settings.

### Supporting Documents

- [Product Model](../../policies/project/product.md): local-first Session history,
  provenance, source roles, and explicit organization.
- [Project Architecture](../../policies/project/architecture.md): direct Claude
  and Codex ingestion, normalized Session and Usage ownership, and adapter
  boundaries.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): private
  runtime storage, source inspectability, source-specific retention, credential
  exclusion, and separation of index removal from original-source deletion.
- [Source Registry And Scans](../../policies/project/data-model/source-registry-and-scans.md):
  current per-kind source identity and stale-file reconciliation.
- [Workspace And Session Activity](../../policies/project/data-model/workspace-and-session-activity.md):
  current Session identity, classification, deletion, and recovery contract.
- [PRD-0002: Session Browsing And Subsession Organization](prd-0002-session-browsing-and-subsession-organization.md):
  accepted primary-Session inventory, pagination, Subsession, source-filter, and
  Session-only synchronization behavior.
- [PRD-0004: Session Usage And Cost Dashboard](prd-0004-session-usage-and-cost-dashboard.md):
  accepted Usage Record inclusion, source scope, and daily, weekly, cumulative,
  and custom period semantics.
- [Project Backlog](../project/backlog.md): unresolved per-source retention,
  removed-source relationship preservation, purge, backup, and restore work.

### Current Implementation References

- `src/localbrain/config.py`: one `codex_root` setting backed by one
  `LOCALBRAIN_CODEX_ROOT` value.
- `src/localbrain/ingest/scanner.py`: one `codex` scan invocation, per-kind source
  upsert, root-wide stale reconciliation, and aggregate scan report.
- `src/localbrain/ingest/codex.py`: source-neutral Codex JSONL parsing and Usage
  Record normalization.
- `src/localbrain/schema.sql`: unique source kind, source-scoped Session identity,
  scan evidence, Session classifications, Usage Records, pins, and relationships.
- `src/localbrain/queries.py`: all-time primary-work Session inventory counts,
  source inventory, pagination, and explicitly recent activity metrics.
- `src/localbrain/usage_queries.py`: period-scoped usage and primary-work Session
  denominators.
- `src/localbrain/templates/sessions.html`, `sources.html`, and
  `sessions_dashboard.html`: current provider-level provenance, counts, source
  state, and Usage scope controls.

## Current Findings

### Multiple Local AI Sources

- LocalBrain can currently represent only one configured Codex Session root.
- `sources.kind` is unique and `_upsert_source` conflicts on `kind`, so adding a
  second root under the same `codex` kind would overwrite the registered root
  rather than create an independent source boundary.
- The Session uniqueness rule is `source_id + external_id`. It is safe for two
  homes only after each home has a stable, distinct source identity.
- Session synchronization and its response currently expose one `codex` result.
  A failure, freshness state, or count cannot be attributed to a specific Codex
  home.
- Sessions, Sources, and Usage views currently hard-code provider-level `All`,
  `Claude`, and `Codex` scopes. They cannot present the existing personal Codex
  source and a company Codex source as peer user-facing AI sources.
- LocalBrain currently scans only the personal Codex Session root. Company Codex
  Sessions are therefore absent until the source model and scanner support more
  than one Codex instance.
- The Codex parser and Usage normalizer are already source-root neutral. The
  required distinction is source identity, attribution, and presentation, not a
  second Codex parsing contract.

### Count And Lifecycle Audit

- Sessions `전체 세션`, the paginated Session total, and per-source Session
  counts do not contain an age or rolling-date predicate. They count retained
  `work + primary` Sessions across all dates.
- `Maintenance` Sessions and all `Subsessions` are intentionally excluded from
  those primary-work counts. They remain stored under their separately approved
  metadata, detail, and Usage contracts.
- `최근 활성 경로` is intentionally limited to the latest seven days. The label
  does not currently state the exact window, so this metric can decrease as time
  passes even when no Session row is deleted.
- Sessions Dashboard `Daily` is a rolling 30-day Usage view and `Weekly` is a
  rolling 12-week view. Their Usage and Session counts can decrease as the
  selected period advances. `Cumulative` uses all eligible retained Usage
  history.
- Before scanning a present source root, the scanner treats the current JSONL
  path set as authoritative. A previously imported Session whose source path is
  no longer present is physically deleted. Related Activity Events, Usage
  Records, and Session pins cascade, while application-addressed historical
  links can be left unresolved.
- A missing source root returns without stale deletion, but a present root with
  older files removed triggers stale deletion on the next scan.
- Claude Code's default native cleanup can therefore remove old source JSONL,
  after which LocalBrain's next scan can reduce all-time Session and source
  counts. The owner's observation is consistent with current implementation and
  source behavior; it is not explained by a hidden date filter on the all-time
  Session inventory.
- The read-only 2026-08-02 audit confirmed one concrete occurrence rather than
  only a theoretical risk. The 2026-07-27 backup contained 81 eligible primary
  work Sessions versus 80 in the current database. Twenty-seven older Claude
  rows were absent: 9 primary work Sessions and 18 Subsessions dated from
  2026-06-24 through 2026-06-29. None of those absent rows was pinned. Additions
  during the same interval partly offset the visible count decrease.
- The last scan known to contain those rows completed at 2026-07-27 08:59 KST;
  their deletion was reflected by the 2026-08-02 11:26 KST scan. No native
  deletion audit log was found, so the exact source-file deletion time within
  that interval remains unknown. The dates and then-unset 30-day Claude default
  make upstream cleanup the best-supported explanation, not direct proof of the
  exact deletion event.

## Product Intent

- Let one local user review all configured AI activity together or select one AI
  source as a statistically independent scope.
- Present `Claude`, `Codex`, and `Codex Company` as peer source lanes without
  pretending that the two Codex roots require different parsers or Usage
  normalization rules.
- Make it immediately clear which local AI source produced a Session, Usage
  Record, count, freshness state, or scan failure.
- Make every count's time scope and inclusion rule understandable, so a decrease
  can be attributed to a selected period, an approved exclusion, a source
  lifecycle event, or an explicit user action.
- Prevent synchronization of one AI source from overwriting, colliding with, or
  deleting records owned by another source.

## Confirmed Scope

### AI Source Identity And Extensibility

- Support multiple explicitly registered local Session source instances for the
  same provider kind.
- Separate the stable user-facing source identity from the provider adapter
  identity. Each configured root has a stable source key, user-readable label,
  provider kind, root locator, freshness, and error state.
- Use these initial identities and meanings:

  | User-facing scope | Stable source key | Provider kind | Meaning |
  | --- | --- | --- | --- |
  | `Claude` | `claude` | `claude` | existing Claude source |
  | `Codex` | `codex` | `codex` | existing personal Codex source |
  | `Codex Company` | `codex-company` | `codex` | company Codex source |

- Treat source keys as durable identity and labels as presentation. `Codex`
  continues to select the existing personal source so current user expectations
  and direct links do not silently expand to company data.
- Keep the identity contract extensible to another configured root or provider
  without another schema redesign. A new provider still requires its own
  approved adapter; multiple roots of an existing provider reuse that adapter.
- Treat account labels as local presentation and provenance, not authentication
  identity. LocalBrain must not infer or store account email, workspace
  membership, OAuth subject, entitlement, or credential material.
- Preserve the existing Claude and personal Codex source identities and normalized
  descendants through compatible migration. Existing Sessions, Usage Records,
  pins, Workstream or Thread links, checkpoints, search identity, and source
  evidence must not be duplicated or renumbered merely because source instances
  are introduced.

### Independent Ingestion And Reconciliation

- Scan each registered Codex Session root independently with the same approved Codex
  parser and Usage normalization contract.
- Scope Session, source-file, parent-child, Usage, freshness, and stale-input
  reconciliation to one source instance.
- Keep identical source-native Session IDs from different Codex homes as distinct
  LocalBrain Sessions.
- A missing, failed, partially written, or stale Codex home must not
  delete or downgrade records owned by another Codex home.
- Session-only synchronization can scan registered AI sources independently and
  reports per-source imported, unchanged, and failed outcomes in a bounded form.
  The wider Sources scan preserves its Local Context scope.
- Continue reading only approved Session JSONL inputs. Do not ingest `auth.json`,
  `config.toml`, native history, state, memory, goal, log, cache, shell snapshot,
  generated-image, plugin, or OAuth files.

### Sessions And Sources Provenance

- Present the primary Sessions source scopes as peer tabs: `전체`, `Claude`,
  `Codex`, and `Codex Company`.
- `전체` combines eligible Sessions from every included AI source. `Codex` selects
  only the existing personal source, and `Codex Company` selects only the company
  source. Do not add a separate combined-Codex primary tab.
- Generate source tabs from stable registered source identities rather than a
  hard-coded provider list so another approved source can join the same control
  without a new classification model.
- Show AI-source provenance across Session surfaces with compact `CL`, `CX`, and
  `CC` cues. The configured source label remains in accessible text, Codex
  Company uses the approved blue provenance treatment, and every Session or
  Subsession icon derives the same cue from stable source identity rather than
  provider kind. Ordinary cards, Pinned cards, detail headings, and detail
  Subsession rows do not repeat the configured source name visibly.
- Show each local Session source instance independently in source status and
  Sources inventory, including root, availability, last scan, eligible Session
  count, tracked file count, and bounded failure or unavailability state.
- Preserve direct-link scope with stable source keys. Source changes reset the
  source-owned result page to its intentional beginning while preserving a valid
  Project filter when the combination is supported.
- Preserve current 15-item primary Session pagination, Project scope, pins,
  parent-owned Subsession disclosure, and direct detail routes.

### Usage Separation

- Attribute every normalized Usage Record to the same source instance as its
  owning Session while retaining provider kind for parser, model, token, and
  price-normalization behavior.
- Give Sessions Dashboard the same peer source scopes as Sessions: `All`,
  `Claude`, `Codex`, and `Codex Company`.
- Under `All`, show one combined summary and an AI-source composition that
  separates Claude, personal Codex, and company Codex usage. Selecting one source
  applies the current range, metric, model, and Project analysis contracts only
  to that source.
- Group the user-facing source breakdown by stable source identity, not provider
  kind. A combined provider-level Codex tab or default scope is not required.
- Reuse the same Codex parser and Usage normalizer for both Codex sources; source
  separation changes attribution and statistics, not token or price semantics.
- Preserve the approved rule that direct real-model Maintenance and Subsession
  usage participates in Usage totals while the separately labeled Session-count
  denominator counts eligible primary work Sessions only.
- Preserve immutable price snapshots, Session-time Project attribution, token
  normalization, and cumulative-delta repair behavior.

### Count Semantics

- Define and test one shared `eligible primary work Session` denominator for the
  Sessions headline, pagination total, source status, Sources inventory, and
  Project-derived Session totals.
- Do not apply an undocumented age cutoff to any count labeled `전체`, `All`, or
  `Cumulative`.
- Preserve the accepted rolling periods for recent activity and Usage views.
  Those selected-period counts may decrease as time advances and remain distinct
  from all-time retained Session counts.
- Continue treating disappearance of a native Session JSONL from a present source
  root as deletion authority for its normalized LocalBrain Session and cascading
  descendants. This may reduce an all-time count after a source cleanup.
- No new tombstone, unavailable-source preservation, deletion warning, scan-delta
  explanation, restore, or explicit-purge product behavior is required by this
  PRD. The owner accepts the current source-mirror tradeoff after review.

### Privacy And Local Boundaries

- Keep every configured local AI source and all imported content on the local
  machine.
- Do not transmit company or personal Session content, paths, usage, labels, or
  source metadata to an external service.
- Keep credentials managed by each Codex home. LocalBrain neither validates nor
  reuses Codex authentication to read local Session files.
- Use only synthetic roots, account labels, Session data, and Usage facts in
  tracked tests, screenshots, docs, and evaluation artifacts.

## Excluded Scope

- Merging, linking, copying, or synchronizing native Codex authentication,
  `resume` lists, histories, state databases, memories, goals, logs, caches,
  plugins, skills, configuration, or OAuth state between homes.
- Changing the `cod` or `codc` shell functions or the owner's Codex login setup.
- Moving a native Session from one Codex home to another or enabling cross-home
  resume inside Codex.
- Inferring personal or company identity from Session text, filesystem contents,
  Git remotes, account APIs, or credentials.
- Company quota, entitlement, invoice, billing, organization, employee, or
  workspace-governance integration.
- Ingestion, parsing, authentication, pricing, or UI behavior for Gemini or any
  other additional provider. Such providers are examples of future extensibility,
  not part of this PRD's delivered source set.
- Changing Claude Code or Codex native cleanup settings, restoring already
  deleted source transcripts, or deleting original source files.
- Cloud sync, multi-user access, remote upload, or mandatory external analysis.
- Feature, Spec, schema, migration, parser, query, template, or runtime changes
  before the human owner approves this PRD boundary.

## Resolved Decisions

### Resolved: Peer AI Source Presentation

- Status: `confirmed by human owner on 2026-08-02`.
- The user's primary distinction is the independently selectable AI source, not
  only the parser provider. Sources that share a provider may still own separate
  Sessions, statistics, freshness, failures, and UI scopes.
- The initial peer scopes are `전체` on Sessions and `All` on Sessions Dashboard,
  followed by `Claude`, `Codex`, and `Codex Company`. `Codex` means the existing
  personal source. There is no separate combined-Codex primary tab.
- Personal Codex and Codex Company share the Codex parser and Usage normalization
  contracts. Their separation is identity, provenance, and analytical scope.
- Gemini was an extensibility example only. This PRD does not add Gemini
  ingestion or another provider adapter.

### Resolved: Imported Session Retention After Source Disappearance

- Status: `confirmed by human owner on 2026-08-02`.
- Claude Code native Session retention is set locally to 180 days, approximately
  six months. This is an owner-managed Claude setting outside LocalBrain and is
  not a LocalBrain configuration or tracked runtime value.
- LocalBrain keeps its current mirror-style deletion behavior. When a registered
  source root exists and one native JSONL disappears, the next scan removes the
  normalized Session and its physically owned Activity Events, Usage Records,
  search projection, and optional Session pin.
- The owner accepts that a pin does not override this source lifecycle and that
  Session history older than the native retention period can leave LocalBrain
  after synchronization.
- No unavailable tombstone, imported-history archive, retention override, restore
  flow, deletion preview, or LocalBrain-specific purge behavior is planned in
  this PRD. Broader backup, restore, and purge controls remain owned by the
  existing Project Backlog.

### Resolved: Synchronization Scope

- Status: `confirmed by human owner on 2026-08-02`.
- The Sessions action keeps its existing `동기화` label.
- One invocation scans the registered `Claude`, `Codex`, and `Codex Company`
  sources. The currently selected source tab does not narrow synchronization;
  tabs control browsing and analytical scope only.
- The result remains attributable per source so an unavailable or failed source
  is distinguishable from the sources that synchronized successfully.

### Resolved: Local Session Source Registration

- Status: `confirmed by human owner on 2026-08-02`.
- One local-only settings file is the authoritative registration contract for
  every local AI Session source. Claude, personal Codex, and Codex Company are
  explicit peer entries in that file; none is managed as a special implicit
  default outside the shared source list.
- Each entry carries at least a stable source key, display label, provider kind,
  and root locator. The file contains no credentials or Session content and
  remains outside tracked repository artifacts.
- The file lives beside the LocalBrain database under the configured runtime data
  directory. Its canonical locator is
  `<LOCALBRAIN_DATA_DIR>/session-sources.toml`, which resolves to
  `~/Library/Application Support/LocalBrain/session-sources.toml` under the
  current default. It is private user configuration and is not a tracked
  repository artifact.
- The target state does not split Session source management between dedicated
  environment variables, built-in roots, and the local settings file. Exact file
  format, validation, and compatibility migration belong to dependent Foundation
  Feature and Spec work.

### Resolved: No Session Source Disablement In This Scope

- Status: `confirmed from the requested boundary and current implementation on
  2026-08-02`.
- LocalBrain had an internal `sources.enabled` column at planning intake, but it
  exposed no user-facing Claude or Codex source-disable action. Session source
  upsert set the row back to enabled, so this column was not a user-managed
  Session source lifecycle contract. The owner approved removing it as the first
  Foundation implementation slice.
- This PRD does not introduce a Session source enable/disable control. Every
  source entry in the local settings file participates in `동기화`, source views,
  and aggregate statistics.
- A temporarily missing or unreadable registered root is an unavailable or failed
  source, not a disabled source. Its previously imported records follow the
  existing failure-preservation behavior; source removal and purge remain outside
  this PRD.

### Resolved: Configuration Failure Is Non-Destructive

- Status: `confirmed by human owner on 2026-08-02`.
- Configuration parsing, identity validation, and root validation complete before
  a source can run stale-input reconciliation. A malformed file, invalid entry,
  mistyped path, unreadable path, duplicate root, removed registration entry, or
  unaccepted root change does not authorize deletion of normalized Sessions,
  Usage Records, pins, or user-curated relations.
- A whole-file error prevents a Session-source scan from starting. A source-local
  path or entry error may fail only that source while independently valid sources
  synchronize. Both cases retain the last accepted registry identity and existing
  imported data and expose a bounded actionable error.
- A root-locator change is distinct from native-file disappearance. It must pass a
  separately specified safe registration or relocation contract before the new
  root becomes deletion authority.
- After the accepted root remains unchanged and is present and readable, actual
  disappearance of an individual native Session JSONL retains the approved mirror
  behavior and removes its LocalBrain Session descendants on synchronization.

## User-Visible Flows And Interaction Expectations

### Synchronize Local AI Sources

- The user invokes the existing `동기화` action once, regardless of the selected
  source tab, and sees separate bounded results for Claude, personal Codex, and
  company Codex.
- One unavailable source is visible as unavailable while successful sources keep
  their own results. A partial failure does not appear as complete success and
  does not erase another source's records.

### Browse Combined Or AI-Scoped Sessions

- The default Sessions view combines eligible primary work Sessions from every
  registered local Session source and orders them by the existing activity
  contract.
- The user can switch between `전체`, `Claude`, `Codex`, and `Codex Company` as
  peer tabs and identify source identity in list and detail views through the
  stable accessible source cue.
- `Codex` never silently includes company Sessions, and no nested instance
  selector is required for the initial source set.
- Pagination, Project filtering, AI-source filtering, and return navigation
  preserve one reproducible URL state.

### Compare Combined And Per-Source Usage

- The user can view aggregate usage across all AI sources or select Claude,
  personal Codex, or company Codex for the same period, metric, model, Project,
  and breakdown contracts.
- Under the aggregate scope, source composition exposes each AI source as its own
  row so the combined total remains traceable to source-level statistics.
- The screen states that Usage totals and the primary-work Session denominator
  have different approved inclusion rules.

### Understand A Decreasing Count

- A time-window count names its period.
- An all-time retained Session count may decrease after the source tool removes a
  native transcript and LocalBrain synchronizes the present root.
- The current source-mirror deletion and cascading pin behavior remain accepted;
  this PRD does not add a new warning or recovery interaction.
- A present native JSONL that contains metadata but no normalized Activity Event
  and no direct Usage Record is an empty stub rather than an eligible Session. A
  successful sync removes its normalized projection and source-file evidence but
  never deletes the native file; later meaningful file growth is importable.

## Constraints

- Human direction and this approved boundary will govern scope.
- Existing Claude/Codex parsers and source JSONL remain implementation truth for
  content normalization; AI-source identity and retention policy remain
  LocalBrain-owned contracts.
- Provider kind, stable AI source key, display label, authentication account,
  Session, and Project are distinct identities and must not be collapsed into
  one field.
- Existing source-derived IDs and user-curated relationships must survive a
  compatible migration.
- LocalBrain remains local-first and single-user. No network call is required to
  discover, scan, browse, count, or compare the configured local Session roots.
- Missing, unreadable, empty, and partially failed sources require
  distinct states.
- The expected execution sequence begins with Foundation Contract work before
  visible Fullstack Product work.
- Affected surface lanes:
  - foundation and data: source registry, compatible migration, Session and Usage
    ownership, source-mirror deletion, and count denominators;
  - ingestion and operations: configuration, independent scanners, parent
    reconciliation, incremental freshness, and cross-source isolation;
  - backend reads: Sessions, Projects, source inventory, pins, Usage scope, and
    provenance queries;
  - frontend: Sessions, Session detail, Sources, Projects-derived counts, and
    Sessions Dashboard;
  - privacy and documentation: source inspectability and synthetic evidence.
- Visible Features use the `fullstack-product` profile and must apply the Design
  Constitution, Design Evaluation, Functional Evaluation, and Interaction
  Evaluation. Foundation Features use `foundation-contract` with Contract and
  Functional evaluation.

## Acceptance Envelope

- Two configured Codex homes can be scanned in one LocalBrain runtime and remain
  distinct through source identity, Session identity, Usage attribution,
  freshness, errors, counts, and UI provenance.
- Existing Claude and personal Codex data migrate without duplication, identity
  churn, pin loss, broken user-curated relationships, Usage loss, or search loss.
- The same source-native Session ID in two Codex homes produces two distinct,
  correctly attributed LocalBrain Sessions.
- Personal Codex and Codex Company use the same Codex parser and Usage
  normalization contracts while retaining distinct source attribution.
- The Sessions action remains labeled `동기화` and scans Claude, personal Codex,
  and Codex Company together; selecting a source tab does not narrow its scope.
- Claude, personal Codex, and Codex Company are explicit entries in one local-only
  settings file; none depends on a separate implicit default or dedicated
  environment-variable registration contract.
- This PRD adds no Session source disablement. Every registered entry participates
  in synchronization and aggregate statistics, while temporary unavailability
  preserves that source's existing imported records.
- Failure, absence, or stale reconciliation in one source instance
  cannot remove or rewrite another instance's Sessions or Usage Records.
- Sessions exposes peer `전체`, `Claude`, `Codex`, and `Codex Company` scopes;
  `Codex` selects only the existing personal source and no combined-Codex primary
  tab is present.
- Sessions Dashboard exposes one combined `All` total and per-source statistics
  for Claude, personal Codex, and Codex Company under the same selected period
  and metric contract.
- Aggregate all-source counts equal the sum of their eligible source counts under
  the same inclusion and time scope.
- Sessions all-time counts apply no undocumented age window and exclude the
  explicitly approved non-primary, non-work, and empty-native-stub categories.
- Usage views preserve the approved rolling and cumulative windows and expose
  AI-source scope without changing token, price, or Session-denominator
  semantics.
- Adding a future approved AI source does not require another source-identity or
  UI-classification redesign, although a new provider still requires its own
  separately approved ingestion and normalization support.
- Per-source scanning preserves the current source-mirror lifecycle: a
  Session removed from its owning present root may be deleted without affecting
  Sessions owned by another source instance.
- No credential, native account state, real Session content, company identifier,
  or machine-specific path enters tracked artifacts or leaves the local machine.
- Synthetic contract, migration, ingestion, query, route, UI, browser, and privacy
  checks pass for combined, per-source, collision, unavailable, partial-failure,
  and source-disappearance cases.

## Candidate Features

- [**Session Source Enabled Field Removal**](../feature/feat-0065-session-source-enabled-field-removal.md)
  (`foundation`, `foundation-contract`, `passed`): remove the unused `sources.enabled`
  schema and consumer surface without touching the real enablement contracts on
  `context_roots` or `external_source_instances`.
- [**Local AI Source Identity Contract**](../feature/feat-0066-local-ai-source-identity-contract.md)
  (`foundation`, `foundation-contract`, `passed`): separate stable source key from
  provider kind while preserving existing registry and descendant identity.
- [**Local Session Source Settings And Safe Registration**](../feature/feat-0067-local-session-source-settings-and-safe-registration.md)
  (`foundation`, `foundation-contract`, `passed`): establish the private TOML source
  list, compatible bootstrap, validation, and non-destructive configuration-failure
  behavior.
- [**Multi-Source Session Synchronization And Health**](../feature/feat-0068-multi-source-session-synchronization-and-health.md)
  (`product`, `fullstack-product`, `passed`): scan registered local AI sources
  independently and expose source-attributed success, partial failure, and health.
- [**Session Source Scope And Provenance**](../feature/feat-0069-session-source-scope-and-provenance.md)
  (`product`, `fullstack-product`, `passed`): add peer source scopes and readable
  provenance to Sessions inventory and detail behavior.
- [**Usage Source Scope And Composition**](../feature/feat-0070-usage-source-scope-and-composition.md)
  (`product`, `fullstack-product`, `passed`): expose combined and independently
  selectable source Usage statistics without changing normalization semantics.
- [**Meaningful Session Eligibility And Empty Stub Reconciliation**](../feature/feat-0071-meaningful-session-eligibility-and-empty-stub-reconciliation.md)
  (`product`, `backend-product`, `passed`): keep metadata-only, zero-Event,
  zero-Usage native stubs out of normalized Session state and reconcile prior rows
  without deleting the source file.

All seven Features passed in dependency order. Any later source-removal,
root-relocation, retention, archive, restore, or new-provider behavior requires a
separately approved planning boundary.

## Continuity Notes

- `2026-08-02`: created the draft from the dual-Codex-home request, the owner-
  maintained local operating note, current source/schema/query contracts, a
  read-only local Session-count audit, and official Claude transcript-retention
  behavior. Kept imported-Session retention after source disappearance as the
  required human decision before downstream planning.
- `2026-08-02`: the owner selected 180-day Claude native retention and explicitly
  retained LocalBrain's current source-mirror deletion, including cascading pin
  removal. Removed unavailable-tombstone, archive, warning, restore, and explicit-
  purge behavior from this PRD and kept only multi-source count consistency.
- `2026-08-02`: the owner generalized the user-facing classification from
  provider-only Claude/Codex scopes to peer local AI sources. `Codex` remains the
  existing personal source, `Codex Company` is a separate statistical and browse
  scope, both reuse the Codex parser and Usage normalizer, and no combined-Codex
  primary tab is required. Gemini remains an extensibility example, not scope.
- `2026-08-02`: the owner kept the existing `동기화` label and confirmed that one
  invocation scans Claude, personal Codex, and Codex Company regardless of the
  currently selected source tab.
- `2026-08-02`: the owner selected one local settings file as the consistent
  registration owner for Claude, personal Codex, and Codex Company, with all
  three represented as explicit peer entries rather than implicit defaults or a
  mix of configuration mechanisms. The current Session-source disablement
  question was removed from scope because no such user-facing feature exists;
  every registered entry synchronizes and participates in aggregate statistics.
- `2026-08-02`: the owner approved sequential implementation beginning with
  removal of the unused `sources.enabled` field. This approval does not merge the
  later multi-source registry, configuration, ingestion, and UI work into the
  first Foundation Feature.
- `2026-08-02`: FEAT-0065 and RUN-20260802-70 passed Contract and Functional
  evaluation. Fresh and compatible schemas now omit the unused field while the
  real Context and external Source Instance enablement contracts remain intact.
- `2026-08-02`: the owner placed the private Session source settings file beside
  the database and confirmed that configuration mistakes must never become
  deletion authority. Feature Planner split the remaining work into source
  identity, safe settings, synchronization and health, Sessions scope, and Usage
  scope so each execution loop has one evaluable outcome.
- `2026-08-02`: the owner approved FEAT-0066 through FEAT-0070 for dependency-ordered
  sequential execution, with only one Feature active in the loop at a time.
- `2026-08-03`: after separating the workflow-journal discovery bug from a valid
  top-level Claude metadata stub, the owner approved FEAT-0071: zero-Event and
  zero-Usage files remain native but lose normalized Session/source-file state on
  successful synchronization and can be imported if they later gain activity.
- `2026-08-03`: FEAT-0065 through FEAT-0071 and RUN-20260802-70 through
  RUN-20260803-81 passed their required evaluator sets and repository checks.
  Human post-run review accepted the completed multi-source, Usage, provenance,
  candidate-discovery, and meaningful-Session outcomes and closed this PRD as
  `passed`.
