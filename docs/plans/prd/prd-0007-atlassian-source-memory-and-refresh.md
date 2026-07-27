# PRD-0007: Atlassian Source Memory And Explicit Refresh

## Metadata

- ID: `prd-0007`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-23`
- Updated: `2026-07-24`
- User review status: `confirmed`
- Approval mode: `strict`
- Canonical passed boundary: this PRD
- Canonical planned follow-up: [PRD-0008](prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)

## Request Summary

- Turn Jira tickets and Confluence pages referenced by the user's work into durable, searchable LocalBrain Source Items without mirroring the entire company Atlassian estate or refreshing remote content during ordinary local use.
- Keep remote Atlassian facts, local organization, and Session or Local Context evidence separate while allowing one stable item to participate in search, Topics, Tags, Workstreams, Threads, and checkpoint resource snapshots.
- Access company Atlassian only through an approved read-only MCP or MCP Gateway path mediated by a Claude or Codex maintenance Run, with explicit refresh scope, preview, freshness, provenance, and retained last-known content.

## Planning Context And Reconciliation

### Scope

- Workflow root and current repository: the LocalBrain repository root
- Related repositories: none in scope
- Current goal: preserve the completed Jira and Confluence read-only source boundary and hand connected validation or classified follow-up to PRD-0008
- External systems in scope: company Jira and Confluence through approved MCP or MCP Gateway capabilities
- Capability checks completed while drafting: connected Gateway Jira and Wiki backends plus one official Atlassian Cloud Jira Site; only bounded metadata connectivity was checked and no ticket or Page body was added to this planning artifact

### Source Inventory

| Source | Type | Role | Freshness | Owner or update path |
| --- | --- | --- | --- | --- |
| Owner decisions from the Atlassian planning conversation | historical note and planned work | primary product direction | current through `2026-07-23` | human review of this PRD |
| [Product Model](../../policies/project/product.md) | policy | authoritative product contract | checked `2026-07-23` | `docs/policies/project/` |
| [Project Architecture](../../policies/project/architecture.md) | policy | authoritative intended architecture | checked `2026-07-23` | `docs/policies/project/` |
| [Privacy And Data Handling](../../policies/project/privacy-and-data.md) | policy | authoritative privacy and external-access contract | checked `2026-07-23` | `docs/policies/project/` |
| [Work Organization And Resources](../../policies/project/data-model/work-organization-and-resources.md) | policy | authoritative current resource ownership contract | checked `2026-07-23` | `docs/policies/project/data-model/` |
| [Maintenance Execution](../../policies/project/data-model/maintenance-execution.md) and [Claude Task Runner](../../policies/operations/claude-task-runner.md) | policy | authoritative current Run contract | checked `2026-07-23` | data-model and operations owner docs |
| [Design Constitution](../../policies/design/design-constitution.md), [Design Evaluation](../../policies/design/design-evaluation.md), and [Interaction Evaluation](../../policies/experience/interaction-evaluation.md) | policy | authoritative visible-surface and evaluation contract | checked `2026-07-23` | design and experience policies |
| Current schema, ingestion, retrieval, Workstream, and Runner code | repository | implementation truth | checked `2026-07-23` | `src/localbrain/` and `src/localbrain/schema.sql` |
| [Project Roadmap](../project/roadmap.md) and [Project Backlog](../project/backlog.md) | plan | planned external-source sequencing | checked `2026-07-23` | `docs/plans/project/` |
| Company MCP or MCP Gateway capability inventory | runtime or operational source | implementation capability evidence | partially checked `2026-07-23`; separate Gateway Jira, Gateway Wiki, and official Atlassian Cloud Jira access boundaries are visible, while Cloud Confluence is unavailable; bounded tool schemas and accessible-resource metadata were rechecked without retrieving ticket or Page bodies | approved company gateway and runner configuration |

### Source Relationships And Truth Rules

- This PRD is the canonical passed boundary and execution history for the Atlassian increment. It does not replace implementation truth or approved durable policies.
- Explicit human direction owns product scope. Current code owns existing behavior. Approved policies own current durable constraints. Live approved Atlassian results own remote facts only when an explicitly authorized connected Run retrieves them.
- A live approved source outranks cached remote facts for current Atlassian state. Cached facts remain historical evidence and must be labeled stale or unavailable rather than silently overwritten or deleted.
- User-created notes, Topics, Tags, attention state, and Workstream or Thread relationships are local authority. Remote synchronization must never overwrite them.

### Reconciliation Results

| Claim | Status | Reconciliation | Follow-up target |
| --- | --- | --- | --- |
| Atlassian is a read-only external source behind an approved MCP boundary | aligned | Human direction, product policy, privacy policy, architecture, and roadmap agree | preserve in every child Feature |
| Company access is mediated by Claude or Codex rather than a credentialed direct LocalBrain connector | aligned | FEAT-0045 now supplies one Claude/Codex-neutral maintenance contract while FEAT-0044 keeps provider dispatch in an approved read-only host boundary; LocalBrain stores no provider credentials | preserve the runner-neutral manifest/result contract in downstream Features |
| Existing manual External Resource identity must survive later Atlassian resolution | aligned | FEAT-0046 passed with a strict one-to-one `atlassian_items.external_resource_id` extension, automatic unambiguous manual reuse, in-place remote binding, scoped aliases, and exact compatible relationship preservation | preserve in evidence, registration, refresh, and visible Item Features |
| Work Session URL discovery may use selected MCP result fields | aligned | FEAT-0047 passed with visible-text URL extraction plus URL/remote-ID/title projection from only approved matched read-result containers; it retains no opaque payload or excerpt and excludes maintenance/subsession feedback loops | preserve the bounded evidence contract |
| External synchronization is maintenance, not ordinary work activity | aligned | FEAT-0045 preserves native Claude or Codex Sessions as maintenance, primary, and metadata-only while directly observed Usage Records remain cost-eligible | preserve in Item application and refresh UI Features |
| Separately connected old and new Atlassian domains remain independent source boundaries | aligned | The owner requires each domain to be inspected and managed independently; migration reconciliation, successor inference, and cross-domain automatic merge are not product responsibilities | Source Instance identity contract and explicit non-goal |
| Jira and Confluence remote content remains distinct from local evidence and classification | aligned | FEAT-0046 and FEAT-0050 implement separate remote-state/content, local note/classification, evidence, and role-based FTS ownership | preserve the split in connected validation and later adapters |
| PRD product boundary | aligned | The owner approved the product boundary on `2026-07-23`; FEAT-0044 through FEAT-0051 passed under that boundary | keep connected first-use evidence and any new behavior in PRD-0008 |

### Source Sync Status And Drift Watchlist

- Checked this session: owner decisions represented in the conversation, repository planning rules, current product and privacy policies, relevant data-model and Runner contracts, current implementation references, visible-surface evaluation contracts, Gateway Jira and Wiki tool catalogs and bounded read schemas, and official Atlassian accessible-resource metadata.
- External recheck before connected execution: only on explicit capability recheck or authorization/schema mismatch. FEAT-0044 established separate Source Instances, cached capability observations, exact bounded read dispatch, and fail-closed behavior; ordinary preview or synchronization must not poll capabilities.
- Likely drift points:
  - company gateway tool names and supported result fields
  - Jira and Confluence API field shape and body format
  - Claude and Codex maintenance marker and structured-result parity
  - Atlassian URL forms and redirect behavior
  - large-Space pagination limits
- Next handoff: FEAT-0044 through FEAT-0051 are passed. Passed [PRD-0008](prd-0008-connected-atlassian-validation-and-schema-erd-routing.md) completed connected first-use validation through FEAT-0053 and the registered-scope-led Add-flow correction through FEAT-0054.

## Product Intent

- Make Atlassian references behave like durable local memory: easy to add, reconnect to originating work, search from a local cache, organize by the user's own Topics and Tags, and refresh only when the user intends to spend remote calls and model tokens.
- Let Atlassian items stand on their own as a knowledge base. Workstream membership is useful but optional and must not be required for collection, search, classification, or refresh.
- Preserve the distinction between what Atlassian currently says, what LocalBrain last observed, where the user encountered the item, and how the user has organized or interpreted it locally.

## Baseline Findings At Approval

- At approval, LocalBrain had an Atlassian navigation destination but only a navigation shell without external ingestion.
- `external_resources` already stores user-curated Jira, Wiki, Slack, Git, document, and URL references and can link them to Workstreams and Threads. Those records are non-rebuildable user-managed state.
- Workstream links, Thread links, and checkpoint resource references currently address External Resources through a stable local ID. Any new source model must preserve those relationships rather than creating a second disconnected copy.
- Global retrieval currently indexes eligible primary work Session text, tool names, and Local Context documents, but intentionally excludes opaque tool-result payloads and maintenance Session content.
- Existing maintenance Runs have durable manifests, structured results, MCP call accounting, source snapshots, artifacts, Workstream attribution, and native Claude Maintenance Session linkage. Direct maintenance Usage Records contribute to token and cost reporting, while maintenance content remains outside ordinary Search, statistics, and organization candidates.
- Existing Workstream maintenance tasks remain Claude-focused, while FEAT-0045 adds a separate provider-neutral external synchronization path for Claude or Codex under one manifest/result contract.
- At approval, the roadmap and backlog already planned explicit external persistence modes, freshness, deep links, unavailable states, Jira and Confluence read-only ingestion, and approved MCP Gateway access.

## Product Vocabulary And State Axes

### Atlassian Source Instance, Site, Space, And Source Item

- An **Atlassian Source Instance** identifies one independently configured access boundary, such as one Gateway Jira backend, one Gateway Wiki backend, or one official Atlassian Cloud connection. Separately connected old and new domains are different Source Instances.
- An **Atlassian Site** is a durable local representation of one remote tenant or normalized domain below a Source Instance. One Source Instance may expose multiple Sites; a Site may later bind a provider remote Site ID without changing its local identity. The same Jira key or remote ID on two Sites represents two different remote items.
- A **Space** is a registered Jira or Confluence organizational scope. Registration controls catalog and content coverage; it does not create a Workstream.
- An **Atlassian Source Item** is one stable local representation of a Jira ticket or regular Confluence Page.
- An **Observed URL** is the exact URL found in a Session, Local Context document, manual entry, or approved tool result.
- A **Canonical URL** is the normalized representative address used for local deduplication and reopening.
- A **URL alias** preserves a prior, redirected, alternate, or deep-link form that resolves to the same Source Item.

### Independent State Axes

The product must not collapse these into one `tracked` flag:

1. **Content coverage**
   - `reference`: URL and local identity only; no successful remote metadata retrieval is implied
   - `metadata`: remote identity and bounded remote fields are stored; Jira description and Confluence body are not metadata
   - `indexed`: eligible remote description or page body is stored and searchable
2. **Attention**
   - `normal`
   - `pinned`
   - `ignored`
   - `archived`
3. **Organization**
   - zero or more Workstream and Thread relationships
   - zero or more local Topics and Tags

Changing one axis must not silently change another. In particular, pinning does not create a Workstream relation, indexing does not imply attention, and archiving does not purge remote or local history.

### Remote, Local, And Evidence Ownership

- Remote metadata includes bounded fields such as Site, Space, remote ID, Jira key or Page ID, title or summary, item type, status, assignee when available, labels, hierarchy, remote update time, and remote version when the source exposes one.
- Remote content includes the Jira description or Confluence Page body. It is separately stored from remote metadata and may have a different applied timestamp and freshness state.
- Local information includes attention, user notes, Topics, Tags, Workstream and Thread links, and user-confirmed interpretations. Remote refresh never overwrites this information.
- Evidence records where an Observed URL was encountered in a Session or Local Context document. Evidence remains source-separated and links back to the owning source; its text is not copied into the remote content body.
- Generated classification or summary, if approved later, remains derived, versioned, and reviewable. It never becomes remote fact or user-confirmed local fact automatically.

## Confirmed Scope

### Stable Identity, URL Normalization, And Compatibility

- Every manually added or automatically discovered Atlassian Source Item begins with an actual HTTP or HTTPS URL.
- A Jira-key-shaped string such as `ABC-12` without a URL is ignored. It does not create an Item, stub, unresolved evidence record, or remote lookup request.
- Manual addition requires a URL. Site, Jira key, Space key, or Page ID may be derived or supplied when available, but none replaces the URL requirement.
- The exact Observed URL is retained for provenance. Normalization produces a Canonical URL without discarding meaningful deep-link context.
- Local deduplication first uses Source Instance plus normalized Site domain and Canonical URL identity. Once remote identity is confirmed, Source Instance plus Site plus service plus remote ID is the authoritative duplicate boundary.
- The same Jira key on different Source Instances or Sites remains distinct. A key, title, or URL change inside one confirmed remote item must not sever its stable local identity.
- Separately connected old and new domains are never merged, related, or interpreted as migration stages automatically. Any knowledge the user gains by comparing them remains local evidence or an explicitly created ordinary relationship outside the synchronization identity contract.
- A manual External Resource and a later synchronized Atlassian Source Item for the same remote object become one linkable local resource rather than parallel duplicates.
- Existing Workstream links, Thread links, checkpoint references, local notes, attention, Topics, and Tags survive URL aliasing, remote resolution, key changes, and content refresh.
- Redirects, alternate Atlassian URL forms, and contextual deep links may become aliases after confirmation. A remote identity collision must be reviewable and must not silently merge conflicting user-managed items.

### URL Discovery And Local Evidence

- Discovery scans only changed eligible primary work Sessions and changed enabled Local Context documents.
- Session discovery examines visible user and assistant text and may examine an allowlisted bounded projection of approved MCP tool results containing only fields such as URL, remote ID, and title.
- The system must not retain or index an opaque tool-result payload merely to discover an Atlassian URL.
- Maintenance Sessions, maintenance artifacts, and maintenance structured results are excluded from ordinary URL discovery so synchronization cannot discover its own output and create a feedback loop.
- Repository-wide source-code scanning is excluded from this increment. Only user-managed Local Context documents and eligible Sessions participate automatically.
- Repeated sightings attach additional evidence to the existing Source Item. They do not duplicate the Item or copy source text into its remote body.
- Discovery is local-only. It does not contact Atlassian, run an LLM, or upgrade content coverage by itself.

### Manual Item And Space Registration

- The user can add an individual Jira or Confluence URL directly without first registering its Space.
- The user can register a Space through either of two entry paths:
  - explicitly fetch the accessible Jira or Confluence Space list through an approved remote maintenance action and select from it
  - paste a Space URL directly
- Fetching the accessible Space list is an explicit remote action, not a background page-load side effect.
- Direct URL registration may create a local reference immediately. Remote identity, metadata, or content remains unknown until an explicit approved refresh succeeds.
- Space registration controls catalog and content coverage but does not automatically pin Items or connect them to a Workstream.

### Jira Coverage

- The default registered Jira Space coverage is `selected-content`:
  - retain Space catalog metadata needed to identify and browse the registered scope
  - retain bounded ticket metadata for locally known Items when retrieved
  - store and index Jira descriptions only for selected Items
- Selected Items include tickets added manually, discovered from eligible Sessions or Local Context documents, pinned by the user, or already mapped to a Workstream or Thread.
- Jira comments and attachments are excluded from the first increment.
- Registering a Jira Space does not authorize a full description mirror of every ticket in that Space.
- Jira custom fields beyond a small approved common allowlist remain outside the baseline until a child Feature confirms their value, size, and gateway availability.

### Confluence Coverage

- The default registered Confluence Space coverage is `full-content` for eligible regular Pages.
- The stored and searchable Confluence baseline includes:
  - Page identity and Canonical URL
  - title and current body
  - Space identity
  - current version and remote update time when available
  - Page hierarchy
  - labels
- Comments, attachments, blogs, whiteboards, databases, and revision-history bodies are excluded from the first increment.
- Full content remains explicit-refresh content. Registering or browsing a Space does not silently fetch every Page body during an ordinary local request.

### Explicit Remote Refresh

- Ordinary Atlassian browsing, local search, Item opening, Topic or Tag editing, and Workstream navigation never trigger a remote request or LLM call implicitly.
- Approved remote actions may target:
  - one Item
  - one registered Space
  - one Thread's directly linked Atlassian Items
  - one Workstream's direct Items plus all Items linked to its Threads, deduplicated
  - all Atlassian Sites, Spaces, and Items currently known to LocalBrain, not the entire remote company estate
- Workstream and all-known refresh require a local preview before execution. The preview itself performs no remote calls.
- The preview shows at minimum:
  - target count and scope
  - checkboxes for inclusion or exclusion
  - service, Site, Space, and Item identity where known
  - freshness state
  - last successful remote check time
  - last remote-content applied time when content exists
- Preview defaults select unknown, unverified, due, stale, and previously unavailable targets. Current targets remain visible but unchecked.
- A registered-Space refresh uses its saved coverage policy. Large or partially known Spaces must expose pagination, expected scope, or another bounded confirmation before execution; exact limits belong to the dependent Feature.
- The user can intentionally include a current target or exclude a stale target before starting the maintenance Run.
- Refresh remains user-initiated in the first increment. There is no scheduler, background poller, page-load refresh, or automatic refresh caused solely by opening related local content.

### Freshness And Efficient Synchronization

- Each remotely resolved Item exposes a local freshness state from this vocabulary:
  - `unknown`: never checked successfully or insufficient remote evidence exists
  - `current`: last successful check found no known newer remote state under the active policy
  - `due`: locally considered ready for recheck because the configured interval elapsed; this does not prove the remote item changed
  - `stale`: LocalBrain has evidence that the remote state changed or that locally applied content no longer matches the confirmed remote version
  - `unavailable`: the latest attempted check could not read the remote item, including permission, authentication, gateway, deletion, or not-found outcomes
- The initial due policy is seven days after the last successful Jira check and 30 days after the last successful Confluence check. Due is local advisory state only: it performs no remote or model call, does not imply stale content, and affects only preview defaults until the user explicitly refreshes.
- Freshness is not content coverage. A metadata-only Item can be current, and an indexed Item can be stale.
- Last remote check and last content-applied time remain separate. A successful no-change check updates the former without rewriting the content or FTS row.
- Refresh prefers batches and bounded manifests over one agent invocation per Item.
- The maintenance input contains only the selected identifiers, URLs, known fingerprints, requested fields, coverage policy, and minimum provenance needed for the remote operation. It does not include unrelated Session or Local Context bodies.
- When the gateway exposes remote versions or update timestamps, the runner first determines whether the relevant remote state changed and retrieves a body only when required by coverage and change state.
- A content hash gates remote body persistence and FTS replacement. An unchanged hash does not rewrite content or re-run downstream analysis.
- A future classifier or summarizer may run only when explicitly approved and when both the relevant content hash and classifier version require it. Synchronization itself does not generate summaries, Topics, Tags, or Workstream relations.
- On permission failure, authentication failure, gateway failure, deletion, or not-found response, LocalBrain retains the last-known metadata, content, evidence, and local organization as `unavailable`. `stale` is reserved for a known remote change or confirmed local projection mismatch.
- Purging retained remote content or deleting the stable local Item is an explicit destructive local action outside refresh.

### Maintenance Run And Provider Contract

- Every external synchronization execution is represented as a maintenance Run with a bounded source-neutral task such as `external_source_sync` and a declared source kind, service scope, target scope, and runner.
- Claude is the expected company-default runner, and Codex is an allowed alternative. The product contract must not make synchronized Atlassian identity or content depend on which approved runner executed the Run.
- The intended company path is:

```text
LocalBrain refresh manifest
        -> Claude or Codex maintenance runner
        -> approved read-only MCP or MCP Gateway tools
        -> Jira or Confluence
        -> bounded structured result with provenance
        -> LocalBrain validation and persistence
```

- Prompt instructions alone are not sufficient read-only enforcement. The approved tool or gateway allowlist must prevent external mutation for this increment.
- Structured results contain the minimum source-backed fields needed to validate identity, freshness, remote metadata, eligible content, source timestamps or versions, and per-target errors. Agent-generated prose is not accepted as remote fact.
- The maintenance Run and its linked native Session use the existing maintenance exclusion semantics: primary maintenance classification, metadata-only Session indexing, no ordinary Search, workflow statistic, Workstream candidate, or checkpoint-Session eligibility.
- Direct real-model Usage Records from synchronization remain eligible for the existing token and estimated-cost dashboard under the same source-neutral Usage Record contract as other maintenance activity.
- A synchronized Atlassian Item linked to a Workstream or Thread may appear in a checkpoint resource snapshot. The maintenance Session that fetched it does not become a checkpoint resource merely because it ran for that Workstream.
- Run manifests, selected target counts, runner, model when available, tool policy, MCP usage, result status, and per-target failures remain inspectable through the maintenance Run boundary.

### Local Classification And Workstream Organization

- Topics are reusable user-created groupings independent of Workstreams. The initial Topic model is flat, many-to-many with Source Items, and may have a name plus optional description.
- Tags are lightweight free-form labels, many-to-many with Source Items, and independent of Topics and Workstreams.
- An Item may have multiple Topics, multiple Tags, multiple Workstream or Thread links, or none of them.
- Local notes, Topics, Tags, attention state, and user-confirmed links remain usable when remote content is stale or unavailable.
- Local classification changes never write back to Jira or Confluence.
- Any future AI-proposed Topic, Tag, or Workstream relationship must be evidence-backed, visibly inferred, reversible, and accepted before it changes user organization.

### Browse, Detail, And Search

- Atlassian remains a stable Workspace navigation destination and fits the existing browse-and-inventory screen family.
- The Atlassian inventory supports Jira and Confluence together while preserving service, Site, Space, Item type, content coverage, attention, freshness, and local organization as distinct filters or metadata roles.
- Item detail separates at least these regions:
  - remote identity, metadata, description or Page body, version, and freshness
  - local attention, notes, Topics, Tags, and Workstream or Thread relationships
  - Session and Local Context evidence that observed the URL
  - refresh history or latest relevant maintenance Run state
- Opening a stored Item uses the local last-known representation and never blocks on remote availability. The original or Canonical URL remains available as a user-activated deep link.
- Local search includes remote metadata for resolved Items and remote descriptions or Page bodies only when content coverage is `indexed`.
- A search query never performs a live Atlassian request, launches a maintenance Run, or asks a model to answer the query.
- Search results resolve to the stable local Source Item and show enough service, Site, Space, type, freshness, and coverage context to judge the result.
- Search supports source-aware narrowing by at least service, Site or Space, Item type, content coverage, freshness, attention, Topic, Tag, and optional Workstream relation.
- Matching Session or Local Context evidence remains a separate result or related-evidence section rather than being blended into an unattributed remote snippet.
- Archived Items remain directly addressable and recoverable. Whether archived Items appear in an unfiltered default inventory or search is a bounded interaction decision for the visible Feature.

### Design And Evaluation Boundary

- Expected foundation execution profile: `Foundation Contract` for external provider, identity, lifecycle, freshness, structured-result, and search projection contracts.
- Expected visible execution profile: `Fullstack Product`.
- Affected surface lanes:
  - source-neutral maintenance provider and approved MCP boundary
  - Atlassian identity, persistence, compatible schema evolution, freshness, and FTS projection
  - Session and Local Context URL-evidence extraction
  - Atlassian Space and Item registration
  - scoped refresh preview and maintenance Run handoff
  - Atlassian inventory, detail, Topic, Tag, and search integration
  - Workstream, Thread, checkpoint, and External Resource compatibility
- The Design Constitution remains the visual and responsive baseline. This PRD adds source-specific states and controls but does not create a new visual family or redesign the persistent shell.
- Visible Features require Contract, Design, Functional, and UX Heuristic evaluation as applicable, including long URLs and titles, empty, unknown, current, due, stale, unavailable, partial-success, direct-entry, history, focus, selection, and responsive states at representative `1440`, `920`, `700`, and `320` widths.

## Excluded Scope

- Jira, Confluence, or any other external write-back, including comment creation, ticket transition, field update, label update, Page edit, or deletion.
- Prompt-only claims of read-only behavior when the runner can still invoke mutating external tools.
- A credentialed direct LocalBrain-to-Atlassian connector as the company-default path for this increment.
- Slack, email, hosted Git, or generic web Source Item schemas. They may later reuse the provider, Run, provenance, and stable Resource patterns without sharing Atlassian-specific fields.
- Automatic Item creation from key-shaped strings without URLs, including unresolved `ABC-12` evidence.
- Repository-wide code scanning or a background repository watcher for Atlassian links.
- Full Jira description ingestion for every ticket in every registered Jira Space.
- Jira comments, attachments, change history, and unrestricted custom-field capture.
- Confluence comments, attachments, blogs, whiteboards, databases, and revision-history body storage.
- Mirroring every accessible Atlassian Site, Space, ticket, or Page merely because the gateway can enumerate it.
- Scheduled polling, implicit refresh on page load, implicit refresh on local search, or ordinary local interactions that spend remote calls or model tokens.
- Live federated remote search on every query.
- Copying Session or Local Context text into the remote Item body or presenting it as Atlassian content.
- Retaining opaque MCP tool arguments or result payloads solely to detect URLs.
- Model-generated summaries, automatic topic classification, automatic tags, or automatic Workstream organization as part of synchronization.
- Mandatory external embeddings or another external AI service beyond the approved Claude or Codex maintenance runner needed to access company MCP tools.
- Treating synchronization Sessions as meaningful work Sessions, personal workflow evidence, ordinary Search content, Workstream organization candidates, or checkpoint Session resources.
- Preserving every remote revision or implementing a local Atlassian version-history mirror.
- Detecting, reconciling, or representing migration relationships between separately connected old and new Atlassian domains, including successor inference, cross-domain key matching, and automatic Resource merge.
- Spec, schema, database-upgrade, adapter, route, template, style, script, or implementation work before one child Feature is explicitly approved.

## Uncertainty

No unresolved item below changes the approved product direction. Each must be resolved by its dependent Foundation or Product Feature before Spec handoff:

- Complete the initial company-approved Jira and Confluence MCP capability inventory, including authentication behavior, enforceable read-only allowlists, result provenance, pagination, batching, version fields, Cloud Confluence availability, and error shapes.
- Decide how the provider-neutral Run contract captures source-backed MCP output independently from model-authored synthesis for both Claude and Codex.
- Define the Codex maintenance Run marker, native Session linkage, artifact ownership, and structured-result behavior equivalent to the current Claude path.
- Fix the exact schema relationship between stable External Resource identity and service-specific Atlassian identity, metadata, content, aliases, evidence, freshness, and refresh history.
- Define conflict handling when two existing manual Resources later resolve to one remote ID or one Canonical URL appears to redirect across Sites.
- Define the bounded allowlist and parser path for URL, remote ID, and title extraction from approved work-Session MCP results without storing opaque payloads.
- Define canonicalization for the verified Jira and Confluence URL forms exposed by the company environment.
- Select the initial bounded Jira system-field and custom-field allowlists after gateway inspection.
- Define Jira ADF, Confluence storage format, or other body normalization into safe local readable text and FTS without treating rendered output as source authority.
- Define large-Space pagination, batch size, concurrency, cancellation, partial success, and resume limits.
- Decide the final control placement for Item, Space, Thread, Workstream, and all-known refresh without creating an action wall. The approved scopes and preview requirements remain fixed even if several scopes share one menu or contextual action.
- Decide whether archived Items appear in unfiltered inventory and search by default while preserving direct access and explicit filtering.
- Decide Topic management entry points and whether Topic descriptions appear inline or only in detail management.

If the approved company gateway cannot provide a required bounded read-only capability, the dependent Feature must report a blocker or return to PRD review. It must not silently introduce a direct connector, broaden retained payloads, or downgrade provenance.

## User-Visible Flows And Interaction Expectations

### Add An Individual Link

- The user pastes a Jira ticket or Confluence Page URL.
- LocalBrain reuses an existing canonical or aliased Item when possible and otherwise creates a reference-only local Item.
- No remote request occurs until the user chooses an explicit resolve or refresh action.
- A later successful resolution enriches the same stable Item and preserves every local relation.

### Register A Space

- The user either requests the accessible Space list and selects a result or pastes a Jira or Confluence Space URL.
- The remote-list path clearly enters a maintenance action and shows failure or unavailability without losing an already registered Space.
- The registered Space displays its service and coverage policy: Jira `selected-content` or Confluence regular-Page `full-content` by default.

### Discover A Referenced Item

- A changed eligible Session or Local Context document contains an Atlassian URL.
- LocalBrain attaches the exact source-backed sighting to one stable reference Item without contacting Atlassian.
- A key-shaped string without a URL produces no Item or evidence.
- Repeated sightings increase related evidence without duplicating the Item.

### Preview And Refresh A Workstream

- The user starts refresh from a Workstream.
- A local preview lists the deduplicated Workstream-level and Thread-level Atlassian targets, their freshness, last check, last content application, and initial checkbox selection.
- The user adjusts the selection and starts one bounded maintenance Run.
- Current local content stays readable while the Run is active. Completion updates only validated changed targets; partial failure leaves successful and failed targets distinguishable.

### Refresh All Known Atlassian Resources

- The user requests a preview of all Sites, registered Spaces, and Items currently known to LocalBrain.
- The preview does not imply enumeration of the entire company estate and does not make a remote call.
- Unknown, due, stale, and unavailable targets are selected by default; current targets remain visible and optional.
- The resulting maintenance Run is inspectable and reports per-target success, no-change, unavailable, and failure outcomes.

### Search And Inspect An Item

- The user searches the local index and narrows results by Atlassian source, Site or Space, type, freshness, Topic, Tag, attention, coverage, or Workstream relation.
- The result shows a local snippet only from eligible indexed remote content and identifies its last-known freshness.
- Item detail keeps remote content, local organization, and Session or Local Context evidence visually and semantically separate.
- Following related evidence returns to the owning local source; following the Canonical URL is an explicit user-activated external action.

### Organize Without A Workstream

- The user pins, archives, adds notes, assigns Topics, or adds Tags to an Item without connecting it to a Workstream.
- That Item remains searchable and refreshable as part of the local knowledge base.
- Connecting or disconnecting a Workstream or Thread later does not erase its classification or remote cache.

### Recover From Remote Failure

- A refresh encounters authentication, permission, gateway, deletion, or not-found failure.
- The last-known metadata, content, local notes, classifications, relations, and evidence remain visible with an unavailable or stale state and the latest attempt time.
- The product offers a bounded retry path and does not present retained content as current.

## Constraints

- LocalBrain remains local-first, single-user, and read-only toward Atlassian in this increment.
- External access uses only approved company MCP or MCP Gateway capabilities through an approved Claude or Codex maintenance runner.
- Credentials remain in existing operating-system, runner, MCP, or gateway facilities and are not persisted as LocalBrain Source Item data or tracked artifacts.
- Synchronization input and output follow data minimization: selected URLs and IDs, bounded requested fields, fingerprints, timestamps or versions, content required by coverage, and per-target provenance or errors.
- Remote source content is imported data. Local relationships and classification are user-managed data. Search rows, freshness derivations, and later analysis are rebuildable projections or derived state.
- Existing manual External Resources are never discarded or renumbered merely because a source-specific identity becomes available.
- A refresh failure cannot clear last-known content, accepted organization, or user notes.
- Generated inference cannot alter Topics, Tags, attention, Workstream links, Thread links, or checkpoints without explicit review and acceptance.
- Search and browse must remain useful offline from the last-known local state.
- All tracked tests, screenshots, examples, and evaluation artifacts use synthetic Atlassian Sites, Spaces, keys, URLs, content, users, and Workstream relations.
- This approved PRD authorizes Feature planning only. Spec work, policy changes, schema work, and implementation still require an explicitly approved child Feature and the repository's remaining human approval gates.

## Acceptance Envelope

- One stable local Atlassian Source Item represents the same Jira ticket or Confluence Page across manual addition, Session discovery, Local Context discovery, URL aliases, and later remote resolution.
- A key-shaped string without an HTTP or HTTPS URL never creates an Item, unresolved evidence, or remote lookup.
- The same Jira key on different Source Instances or Sites remains distinct, while a confirmed URL or key change inside one remote item preserves local identity and relations.
- Separately connected old and new domains remain independent; synchronization performs no migration inference, cross-domain merge, or successor mapping.
- Existing External Resource links, Workstream and Thread mappings, checkpoint references, notes, attention, Topics, and Tags survive source-specific enrichment and refresh.
- Remote metadata, remote content, local organization, generated state, and Session or Local Context evidence have distinct ownership and cannot overwrite one another.
- Jira registered Spaces default to selected-content behavior and never bulk-index every ticket description implicitly.
- Confluence registered Spaces default to full current content for eligible regular Pages with hierarchy and labels, while excluded content types remain absent.
- Space-list retrieval and all remote resolution or refresh actions are explicit and attributable maintenance actions.
- Ordinary browse, detail, search, Topic, Tag, Workstream, and Local Context interactions cause zero remote calls and zero synchronization model calls.
- Workstream and all-known refresh present a no-remote local preview with target count, scope, selection, freshness, last check, and last content-applied time before execution.
- Thread and Workstream scopes include only their mapped Items, Workstream scope includes its Threads, and duplicate Items execute once per Run.
- All-known scope means every Atlassian resource already known to LocalBrain, not every resource accessible in Atlassian.
- Unknown, current, due, stale, and unavailable states remain distinct from content coverage and attention.
- Successful no-change checks update check evidence without rewriting unchanged content or FTS rows; changed content updates only after source identity and hash validation.
- Last-known content and local organization survive partial failure, unavailable, deleted, and not-found outcomes until an explicit destructive local action removes them.
- Synchronization returns minimal structured source fields and does not generate summaries, automatic classifications, or relationship mutations.
- Claude and Codex can satisfy one source-neutral maintenance contract, and the resulting Item identity and content do not depend on the chosen runner.
- Read-only behavior is enforced by approved tool or gateway capability, not solely by prompt wording.
- Synchronization Sessions and artifacts remain excluded from ordinary Search, workflow statistics, organization candidates, and checkpoint Session resources, while direct real-model Usage Records remain eligible for existing token and cost reporting.
- Indexed Jira descriptions and Confluence Page bodies are locally searchable without live remote search; every result resolves to the stable Item and exposes service, Site or Space, coverage, and freshness.
- Item detail visibly separates remote facts, local organization, related local evidence, and refresh state.
- Topics and Tags remain independent of Workstreams and support Items with no Workstream mapping.
- Synthetic contract, schema-upgrade, parser, adapter, query, route, UI, Run, partial-failure, responsive, accessibility, and browser evidence covers duplicate URLs, aliases, cross-Site keys, manual stubs, changed evidence, selected Jira content, full Confluence Pages, no-change refresh, stale and unavailable retention, Workstream deduplication, and all-known preview.
- Required Contract, Design, Functional, and UX Heuristic evaluations pass for their applicable child Features.

## Implemented Features

- [FEAT-0044: MCP Capability And Read-Only Policy](../feature/feat-0044-mcp-capability-and-read-only-policy.md) (`foundation`, `passed`, `Foundation Contract`): inventory independently connected Source Instances and establish an enforceable read-only capability allowlist before any synchronization call.
- [FEAT-0045: Provider-Neutral External Sync Run Contract](../feature/feat-0045-provider-neutral-external-sync-run-contract.md) (`foundation`, `passed`, `Foundation Contract`): define a generic Maintenance Run parent, one-to-one source-neutral external-sync envelope, Claude and Codex runner parity, versioned manifests, structured source results, provenance, usage, partial failure, and maintenance exclusion.
- [FEAT-0046: Atlassian Source Item Identity And Freshness Contract](../feature/feat-0046-atlassian-source-item-identity-and-freshness-contract.md) (`foundation`, `passed`, `Foundation Contract`): stable Resource binding, Source Instance/Site/remote identity, URL aliases, remote versus local ownership, coverage, freshness, retained last-known content, compatible schema evolution, and FTS projection.
- [FEAT-0047: Bounded Atlassian URL Evidence Extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md) (`foundation`, `passed`, `Foundation Contract`): changed-Session and changed-Document detection plus allowlisted MCP result-field extraction without opaque payload retention or maintenance feedback loops.
- [FEAT-0048: Atlassian Item And Space Registration](../feature/feat-0048-atlassian-item-and-space-registration.md) (`product`, `passed`, `Fullstack Product`): add manual Item URLs, direct Space URLs, explicit remote Space-list selection, Jira and Confluence default coverage, inventory states, and duplicate reuse.
- [FEAT-0049: Explicit Atlassian Refresh And Preview](../feature/feat-0049-explicit-atlassian-refresh-and-preview.md) (`product`, `passed`, `Fullstack Product`): provide Item, Space, Thread, Workstream, and all-known scopes, required previews, freshness-aware defaults, maintenance Run handoff, progress, no-change, partial-success, unavailable, and retry behavior.
- [FEAT-0050: Atlassian Browse, Search, And Local Classification](../feature/feat-0050-atlassian-browse-search-and-local-classification.md) (`product`, `passed`, `Fullstack Product`): expose source-aware inventory and detail, local indexed search, evidence links, Topics, Tags, attention, and optional Workstream or Thread organization.
- [FEAT-0051: Atlassian URL-First Connection Onboarding](../feature/feat-0051-atlassian-url-first-connection-onboarding.md) (`product`, `passed`, `Fullstack Product`): replace the configured-Site dead end with local URL preview, explicit local MCP access-path selection, atomic Source/Site/reference creation, and bounded later editing.

The owner approved PRD-0007 and authorized Feature creation on `2026-07-23`. FEAT-0044 through FEAT-0050 passed in dependency order with all required evaluators and complete regressions. Live first-use review on `2026-07-24` added approved follow-up FEAT-0051 inside the same registration boundary, and that follow-up also passed; broader adapter expansion or scale work still requires a new planned boundary.

### Recommended Dependency Order

1. Fix the MCP capability inventory and enforceable read-only policy.
2. Fix the source-neutral maintenance provider and structured-result contract.
3. Fix stable Atlassian identity, External Resource compatibility, content ownership, freshness, and local search projection.
4. Fix bounded URL evidence extraction independently of remote synchronization.
5. Add Item and Space registration against the approved foundation contracts.
6. Add explicit scoped refresh, preview, and failure recovery.
7. Complete browse, detail, Topic, Tag, Workstream relation, and local search behavior.

Only one Feature should become the active approved execution target at a time unless the human owner explicitly changes the execution policy.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human direction through `2026-07-23` | primary | Jira and Confluence scope, URL-only discovery, source-specific Source Items, coverage defaults, explicit refresh scopes and preview, local Topics and Tags, runner-neutral maintenance, and retained local identity | does not authorize external writes, key-only discovery, background refresh, opaque payload storage, or implementation before review |
| Product and privacy policies | governing | local-first behavior, Workstream and Thread responsibility, provenance, source roles, approved external access, retained local control, and read-only boundary | do not determine the new Atlassian schema or gateway capabilities |
| Approval-time External Resource and Workstream implementation | implementation truth | stable user-curated resource identity and existing Workstream, Thread, checkpoint, and retrieval relations | generic fields alone were not sufficient as the full Atlassian source model |
| Approval-time Session and Local Context ingestion | implementation truth | changed-source scanning, eligible work Session boundaries, local document authority, FTS, and opaque tool-result exclusion | bounded Atlassian URL evidence from MCP result fields required an approved extension |
| Approval-time maintenance Runner and Usage contract | implementation truth | durable Run ledger, manifests, MCP accounting, artifacts, Claude native Session linkage, exclusion from work consumers, and inclusion in cost | Claude-specific execution was not the desired provider-neutral final contract |
| Design Constitution and evaluation policies | governing | existing Atlassian browse family, shell, state, provenance, responsive, accessibility, preview, focus, and continuity constraints | do not decide exact refresh-control placement or data field allowlists |
| Roadmap and backlog | planned work | Phase 4 external read-only direction, explicit persistence modes, freshness, deep links, unavailable states, and Jira/Confluence MCP work | planning text is not implementation truth or external capability evidence |
| Connected MCP capability inspection | operational signal | separate Gateway Jira, Gateway Wiki, and official Atlassian Cloud Jira boundaries; field-selective Jira reads, metadata and hierarchy-oriented Wiki reads, write-tool exposure, and unavailable Cloud Confluence | bounded connectivity evidence only; does not establish content freshness, read-only enforcement, or migration relationships |

## Continuity Notes

- `2026-07-23`: created the initial draft from the owner's Atlassian planning decisions and reconciled it with the current External Resource, Workstream, maintenance Run, Session ingestion, privacy, roadmap, design, and search contracts.
- `2026-07-23`: fixed URLs as mandatory for manual addition and automatic evidence; key-only strings create no Item or unresolved evidence.
- `2026-07-23`: separated content coverage, attention, Workstream or Thread organization, remote facts, local classification, and source evidence.
- `2026-07-23`: fixed Jira registered Spaces to selected-content and Confluence registered Spaces to full current regular-Page content, with comments and non-Page content excluded.
- `2026-07-23`: fixed explicit Item, Space, Thread, Workstream, and all-known refresh semantics, required Workstream and all-known previews, freshness-aware selection, hash-gated persistence, and retained last-known content.
- `2026-07-23`: fixed synchronization as a provider-neutral Claude or Codex maintenance Run through approved read-only MCP capabilities; maintenance usage remains cost-visible while maintenance content remains outside ordinary work consumers.
- `2026-07-23`: retained MCP capability inventory, exact storage shape, body normalization, freshness intervals, custom fields, large-Space limits, and final control placement as child-Feature decisions rather than PRD scope ambiguity.
- `2026-07-23`: normalized reconciliation statuses to `aligned`, `conflict`, and `open`; the direct-client policy mismatch is a conflict, while stable Resource binding and bounded MCP-result extraction remain open Foundation contracts.
- `2026-07-23`: recorded the connected Gateway Jira, Gateway Wiki, and official Atlassian Cloud Jira boundaries as separate Source Instances; old/new migration detection, reconciliation, successor mapping, and automatic cross-domain merge are explicitly out of scope.
- `2026-07-23`: the owner approved the PRD boundary and authorized Feature creation; status changed to `approved` with user review `confirmed`.
- `2026-07-23`: created proposed draft FEAT-0044 through FEAT-0050, separating capability policy, provider-neutral execution, identity and freshness, bounded evidence extraction, registration, explicit refresh, and local browse or classification behavior.
- `2026-07-23`: rechecked FEAT-0044 capability evidence without retrieving ticket or Page bodies; confirmed mixed read/write Gateway catalogs, bounded Jira/Wiki read shapes, current official Jira availability, and current official Confluence unavailability.
- `2026-07-23`: the human owner approved FEAT-0044 and started RUN-20260723-49 with the `foundation-contract` profile; later Features remain draft and inactive.
- `2026-07-23`: FEAT-0044 passed Contract and Functional evaluation with complete evidence; FEAT-0045 is the next inactive boundary for human review.
- `2026-07-23`: confirmed FEAT-0045 persistence ownership as a generic `maintenance_runs` parent, one-to-one `external_sync_runs` query envelope, and detailed versioned manifest; the Feature remains draft until its complete boundary is explicitly approved.
- `2026-07-23`: the human owner approved FEAT-0045 and started RUN-20260723-50 with the `foundation-contract` profile; later Features remain draft and inactive.
- `2026-07-23`: FEAT-0045 passed Contract and Functional evaluation after one bounded metadata-coverage repair; FEAT-0046 is the next draft boundary for human review.
- `2026-07-23`: for FEAT-0046, the owner approved removing global `external_resources.url` uniqueness through a compatible ID- and relationship-preserving migration; Atlassian URL identity will instead be unique only within one Source Instance.
- `2026-07-23`: for FEAT-0046, the owner approved Jira seven-day and Confluence 30-day advisory due intervals distinct from evidence-backed stale state, plus a durable Site domain layer below Source Instance so global-company domains remain explicitly separated.
- `2026-07-23`: the owner approved the strict one-to-one `external_resources.id`/`atlassian_items.external_resource_id` extension and exact Site/Space/Item/URL/remote-state/content split, then requested RUN-20260723-51.
- `2026-07-23`: FEAT-0046 passed Contract and Functional evaluation on Attempt 1 with exact compatible Resource/link preservation, 21 focused Atlassian tests, the complete 225-test suite, and no live company or model call; FEAT-0047 is now the next draft review boundary.
- `2026-07-23`: the owner approved the recommended open decisions and sequential execution of FEAT-0047 through FEAT-0050.
- `2026-07-23`: FEAT-0047 passed on Attempt 2 after one bounded multi-file Session scan-cardinality repair, with eight focused tests, the complete 233-test suite, and zero external/model calls; FEAT-0048 is next.
- `2026-07-23`: FEAT-0048 passed all four required evaluators on Attempt 1 with local-only URL registration, one-call partial Space discovery, exact supported-width rendering, the complete 241-test suite, and zero live external/model calls; FEAT-0049 is next.
- `2026-07-23`: FEAT-0049 passed all four required evaluators on Attempt 1 with exact local previews, bounded mixed-instance maintenance execution, atomic result application, and 250 passing regressions.
- `2026-07-23`: FEAT-0050 passed all four required evaluators on Attempt 1 with local Browse/Search/detail, additive notes/Topics/Tags, role-separated FTS, existing work links, exact supported-width rendering, and 256 passing regressions. The original seven Features, FEAT-0044 through FEAT-0050, were passed.
- `2026-07-24`: live first-use review found that the configured Source Instance/Site prerequisite had no user-facing creation path. The owner approved FEAT-0051 for URL-first local parsing, explicit local MCP access-path selection, atomic Source/Site/reference creation, and later bounded editing.
- `2026-07-24`: passed FEAT-0051, replacing the configured-Site first-use dead end with local URL preview, explicit access-path selection, atomic Source/Site/reference creation, and bounded later editing. All eight PRD-0007 Features are passed.
- `2026-07-24`: the owner deferred detailed connected Atlassian first-use and end-to-end validation to draft [PRD-0008](prd-0008-connected-atlassian-validation-and-schema-erd-routing.md) so it can begin with a fresh bounded context. PRD-0007 remains passed; the follow-up distinguishes new operational evidence from its completed automated evidence.
