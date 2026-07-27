# PRD-0008: Connected Atlassian Validation And Schema ERD Routing

## Metadata

- ID: `prd-0008`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-24`
- Updated: `2026-07-27`
- User review status: `confirmed`
- Approval mode: `strict`
- Canonical passed boundary: this PRD

## Request Summary

- Carry two explicitly deferred follow-ups into the next planning session:
  - validate the implemented Atlassian workflow against the owner's connected MCP paths and agreed first-use scenarios;
  - evaluate and, if approved, adopt Mermaid's official ELK layout path for Draw.io-like orthogonal Schema ERD routing without replacing Mermaid.
- Include the owner's first connected-workflow review findings in the Atlassian lane:
  - keep only the local-browse and add top-level intents and rename `Add / discover` to `Add`;
  - treat direct URL registration and connected candidate discovery as two paths inside one Add intent rather than two competing side-by-side cards;
  - keep Source Instance as the internal access and policy boundary, but replace the user-facing compound `Source Instance / Site` choice with separate target-Site and MCP-connection choices.
- Keep exact connected fixtures, final control composition, and the ELK adoption choice for later bounded Feature review. The owner approved this PRD as the product boundary whose user outcomes, access constraints, and evaluation decisions those Features must preserve.

## Workflow Scope

- Workflow root: LocalBrain repository.
- Current repository: LocalBrain.
- Related repositories: none confirmed.
- Repository aliases: none required.
- Completed goal: validate the bounded connected Atlassian paths, correct the Add information architecture, evaluate official Mermaid ELK routing, and adopt the accepted local Schema path through approved child Features.

## Source Set

| Source ID | Type | Location | Role | Freshness | Owner or update path |
| --- | --- | --- | --- | --- | --- |
| `human-20260724-follow-up` | other | current owner direction, summarized here rather than copied verbatim | approved scope and acceptance boundary | confirmed through `2026-07-27` | human review and closure confirmation |
| `prd-0003` | doc | [Data Model Visibility And Schema Cleanup](prd-0003-data-model-visibility-and-schema-cleanup.md) | historical note and passed product boundary | checked `2026-07-24` | PRD-0003 and its passed Features |
| `feat-0052` | doc | [Schema Diagram Zoom Navigation](../feature/feat-0052-schema-diagram-zoom-navigation.md) | historical note and passed interaction boundary | checked `2026-07-24` | FEAT-0052 |
| `schema-implementation` | repo | `package.json`, `scripts/build-mermaid-assets.mjs`, `src/localbrain/static/mermaid-adapter.js`, and Schema presentation sources | implementation truth | checked `2026-07-24` | current repository code |
| `mermaid-layout-contract` | doc | [Mermaid ER layout](https://mermaid.js.org/syntax/entityRelationshipDiagram.html#layout), [Mermaid layouts](https://mermaid.js.org/config/layouts.html), and Mermaid 11.16 package sources | authoritative library contract | checked `2026-07-24` | official Mermaid documentation and pinned package |
| `prd-0007` | doc | [Atlassian Source Memory And Explicit Refresh](prd-0007-atlassian-source-memory-and-refresh.md) | historical note and passed product boundary | checked `2026-07-24` | PRD-0007 and FEAT-0044 through FEAT-0051 |
| `prd-0009` | doc | [Data Model Value Dictionaries And Pinned Session Recall](prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md) | passed owner of cross-subject bounded-value definitions and presentation policy | checked `2026-07-27` | PRD-0009 and passed FEAT-0057/0061 |
| `atlassian-implementation` | repo | `src/localbrain/atlassian*.py`, external-access/sync modules, routes, templates, client assets, and focused tests | implementation truth | checked `2026-07-24` | current repository code |
| `connected-atlassian-runtime` | runtime | owner-connected official Atlassian MCP and company MCP Gateway paths | closure operational signal | official Jira checked `2026-07-24`; official Confluence and Gateway remain conditional | explicit owner-directed read-only checks under a newly approved inventory |

## Source Relationships

- PRD-0008 follows the passed PRD-0003 Schema increment without reopening its completed data-model, presentation, or zoom contracts.
- PRD-0008 follows the passed PRD-0007 Atlassian increment without reclassifying its automated implementation evidence as live connected evidence.
- PRD-0009 owns the cross-subject physical/logical/UI value dictionaries. PRD-0008 only requires later Atlassian consumers to follow the approved whole-family presentation policy; it does not define or audit the nine subject dictionaries.
- The two follow-up lanes became independent execution boundaries under one PRD and passed through separate child Features.
- A connected Atlassian observation may expose a defect or missing behavior, but it does not silently modify the passed PRD-0007 contract; any resulting change outside an approved child Feature must return to PRD-0008 review and later Feature planning.

## Source-Of-Truth Rules

- Explicit human direction owns this approved product scope and approval boundary.
- Current repository code owns implemented behavior.
- Approved policies own privacy, external-access, local-asset, Schema presentation, and evaluation constraints.
- A directly observed, explicitly authorized connected Atlassian result owns current remote behavior for that test; synthetic and route evidence remain regression evidence rather than a substitute for that observation.
- Official Mermaid documentation and the pinned package own supported layout capability; the current LocalBrain asset manifest owns what is actually bundled.
- At approval, this PRD authorized child Feature planning only; no draft Feature could trigger Spec, Run, dependency, or code changes. Its current `passed` status records completion through FEAT-0053 to FEAT-0056 without weakening that gate.

## Reconciliation Notes

The table records both planning-time uncertainties and their final disposition. Rows marked `resolved` were closed by the passed child Features and closure evidence below.

| Topic | Source claims | Status | Working assumption | Follow-up target |
| --- | --- | --- | --- | --- |
| ER relationship curve option | The pinned default Dagre ER renderer emits `basis` edges, while the public `curve` setting is Flowchart-specific. Official ER documentation supports selecting the ELK layout when its loader is enabled. | `aligned` | A simple `er.curve=linear` toggle is not available; ELK is the supported candidate path. | post-approval Feature review |
| Mermaid replacement | Official Mermaid supports external layout loaders, and current LocalBrain already owns a pinned local Mermaid asset pipeline. | `aligned` | Mermaid does not need to be replaced; the candidate change is an official companion layout dependency plus bounded adapter/asset work. | post-approval scope and candidate Feature review |
| Desired ERD routing | The owner prefers Draw.io-like orthogonal relations; current 11.16 behavior with ELK produces right-angle segments with rounded corners. | `resolved` | FEAT-0055 accepted the rounded ELK result after like-for-like comparison, and FEAT-0056 adopted it as the Schema-only default without a selector. | Mermaid/ELK drift watchlist |
| Atlassian automated evidence | PRD-0007's child Features passed focused, migration, route, UI, schema, privacy, and full-suite checks. Several follow-up reports explicitly distinguish source-level or synthetic evidence from direct connected first-use observation. | `aligned` | Existing implementation remains passed; PRD-0008 owns additional connected validation rather than retroactively failing PRD-0007. | define the validation Feature matrix |
| Connected Atlassian scope | The owner has official Atlassian MCP and company Gateway paths and wants bounded first-use validation. Exact Sites, services, operations, and test records are fixture choices rather than new product scope. | `aligned` | A later approved Feature must enumerate its enabled connection/Site fixtures and read-only operations before any request. Broad discovery and unlisted remote reads remain excluded. | validation Feature intake |
| Atlassian Add information architecture | The current setup view combines `Source Instance / Site`, presents direct URL registration and Space-candidate discovery as equal left/right cards, and labels the top-level intent `Add / discover`. The owner identifies these as comprehension problems. | `aligned` | Keep one Add intent, remove `discover` from its top-level label, and make each addition path legible without exposing the internal Source Instance term as the primary user concept. | detailed Add flow and later Feature review |
| Site and MCP selection | Source Instance remains necessary to distinguish official Atlassian MCP from company MCP Gateway access, capability, and provenance even for the same domain. The owner still needs the target and access method to be chosen separately. | `aligned` | Present one target Site/domain choice followed by one MCP connection choice. Resolve the pair to the existing Source Instance/Site identity internally rather than presenting one compound selector or duplicating the Site into connection-specific tabs. | connected scenario matrix and later interaction contract |
| Add orientation content | The current full-width `MCP CONNECTIONS / Source Instance와 Site` panel leads with connection administration and a `0 connections` count. The owner finds Sites and Spaces/projects already registered in the LocalBrain database more useful as the Add-screen orientation. | `aligned` | Lead with the persisted Atlassian scope LocalBrain already owns, independent of whether registration came from the Atlassian UI, an approved AI-assisted flow, or another supported producer. Keep MCP binding and capability details subordinate. | persisted-scope projection and later Add Feature review |
| Add-overview inclusion boundary | Search and discovery results may expose candidates before they are added, while supported URL, candidate-confirmation, and AI-assisted flows can persist Site, Space/project, and Item records. | `aligned` | The overview reads current registered database records, not producer provenance. Unregistered candidates and URL-only inference that has not created the owning record remain absent. | later Add Feature contract |
| Physical enum versus product vocabulary | Current Atlassian copy exposes storage values such as `selected-content` directly to the user, while PRD-0009 now owns cross-subject value definitions and presentation modes. | `split` | Atlassian screens consume the approved PRD-0009 mapping for each complete column or bounded value family. PRD-0008 does not create a competing Atlassian-only dictionary. | FEAT-0057 baseline and FEAT-0054 consumer lane |
| Evolving Atlassian composition | The owner expects the Atlassian screen composition and detailed copy to continue changing as connected behavior is exercised. | `aligned` | PRD approval fixes user outcomes, identity, inclusion, provenance, external-access, and interaction-order boundaries rather than one final card or control composition. Feature and Spec review may choose and refine the exact controls and layout within those boundaries. | later Feature and Spec review |
| Follow-up defects | Live validation or ELK comparison may reveal implementation, spec, or planning gaps. | `resolved` | FEAT-0053 classified the connected evidence and environment limits; no corrective Feature was required outside the approved FEAT-0054 Add boundary. | future changes require a new approved boundary |

## Product Intent

- Replace assumption-based confidence with explicit owner-reviewed evidence for the real connected Atlassian workflow while preserving the read-only, local-first, explicit-refresh, and provenance boundaries established by PRD-0007.
- Make the Atlassian Add flow speak in user goals—what to add and which MCP connection to use—while keeping the stricter Source Instance identity and provenance contract underneath.
- Make dense Schema ERDs easier to trace with an orthogonal routing candidate familiar to Draw.io users, while preserving Mermaid source ownership, offline packaging, textual fallback, and the passed zoom interaction.

## Confirmed Scope

### Atlassian Validation Intake

- Include a bounded Atlassian validation lane using the already connected MCP paths after PRD and Feature approval.
- Treat connected runtime checks, rendered first-use behavior, and any agreed end-to-end workflow scenarios as distinct from existing synthetic and source-level evidence.
- Keep the integration read-only and require explicit scope before any remote request.
- Preserve the existing Source Instance, Site, Item, remote/local ownership, freshness, explicit preview/refresh, maintenance Run, search, Topic/Tag, and Workstream/Thread contracts unless an observed finding is returned to planning.
- Record findings with enough evidence to classify them as implementation bug, spec gap, planning gap, environment limitation, or no defect.

### Atlassian Add And Connection Selection

- Keep two top-level Atlassian work intents: local browsing and adding. Rename the current `Add / discover` action to `Add`; exact final copy for the browse-side label remains a small copy-review item.
- Treat URL registration and connected Space/project candidate discovery as ways to add Atlassian knowledge, not as separate top-level product modes.
- Replace the equal left/right URL-registration and candidate-discovery cards with one comprehensible Add flow. The exact in-flow switch or disclosure control remains for detailed interaction review.
- Do not expose `Source Instance / Site` as one compound user choice.
- In connected candidate discovery, present the choices in this order:
  1. `조회 대상`: the Atlassian Site/domain whose Space or project candidates the user wants to inspect;
  2. `MCP 연결`: the official Atlassian MCP or company MCP Gateway path to use for that target.
- Keep both selections separately legible even when LocalBrain already stores or resolves them as one Source Instance/Site pair.
- Keep `실행 주체` separate from both: Claude or Codex selects which maintenance runner executes the bounded Run, not which Atlassian target or MCP connection owns the remote identity.
- When the same Site/domain is reachable through more than one MCP connection, show the Site once as the target and expose the eligible connections as access-method choices. Do not create separate Site tabs solely because the connection differs.
- Keep the selected MCP connection visible as provenance on the bounded discovery Run and its results.
- Retain `Source Instance` as an internal data, capability, isolation, and policy term. Ordinary Add copy uses `MCP 연결`; technical diagnostics may retain the internal term only where it is necessary to explain identity or recovery.
- Replace the dominant `MCP CONNECTIONS / Source Instance와 Site` orientation panel with a local-knowledge overview organized by recognizable Site/domain.
- Populate the overview from persisted LocalBrain Atlassian records: registered Sites, their registered Spaces/projects, and useful counts or labels derived from current registered Items.
- Apply no inclusion filter based on how a record was registered. A URL submitted in the Atlassian UI, a candidate explicitly added after connected search, and an approved AI-assisted registration are equivalent once they have produced the same durable database record.
- Exclude search/discovery candidates that have not been added and do not infer a new Site or Space/project solely for presentation from a raw Session, Local Context, or URL occurrence.
- Connection count alone is not the primary summary.
- Keep MCP connection availability as subordinate operational context for actions that need a remote read. Detailed binding, enabled state, and capability management move behind a secondary `연결 관리` disclosure or destination.
- An empty overview explains that no Atlassian Site or Space/project has been registered yet and points to URL addition or connected search. It does not lead with `0 connections`.
- Make ordinary Atlassian copy consume the approved PRD-0009 presentation policy for each complete column or bounded value family. This PRD does not author cross-subject dictionaries; it preserves their physical values and requires any later Atlassian consumer to avoid an unapproved raw-token fallback.

### Schema ERD Routing Intake

- Include Mermaid ELK as the preferred orthogonal-routing candidate.
- Preserve Mermaid as the diagram library; do not assume a wholesale renderer or product-surface replacement.
- Keep dependencies local and pinned, with no CDN or runtime network requirement.
- Preserve the existing generated Schema source, strict owned-node trust boundary, failure fallback, diagram zoom, ordinary scrolling, and package/privacy checks.
- Compare the current Dagre output and candidate ELK output before deciding whether ELK becomes the default, an optional control, or is rejected.

### Original Planning Handoff

These requirements governed the transition from approved PRD to child Feature work and are retained as historical gate evidence.

- Fix the exact connected test inventory, representative fixtures, evidence capture, and ELK comparison matrix before approving the corresponding validation or implementation Feature.
- Keep all candidate Features uncreated and unapproved until the owner approves this PRD boundary.

## Excluded Scope

- Atlassian, Jira, Confluence, Slack, email, or other external writes.
- Credential, token, OAuth, or MCP installation changes.
- Automatic old/new Atlassian migration reconciliation, cross-domain merge, or successor inference.
- Collapsing official Atlassian MCP and company MCP Gateway into one indistinguishable access path or removing Source Instance isolation from the persistence and read-policy contracts.
- Automatically merging or deduplicating remote Items discovered through different Source Instances.
- Background refresh, hidden remote reads, or broad source inventory crawling.
- Connected-behavior corrections outside the confirmed Add and selection scope before a classified finding returns to planning.
- Authoring or auditing the nine subject-oriented value dictionaries, Session pinning, or Session-related context; PRD-0009 owns those boundaries.
- Replacing Mermaid with Draw.io, a freeform editor, or another diagram product.
- Manual table positioning, drag editing, saved edge waypoints, or full diagram authoring.
- Mermaid bundle patching or post-render SVG path rewriting as the default solution.
- Spec, Run, dependency installation, connected execution, or implementation before an individual child Feature is approved.

## Resolved Feature-Planning Decisions

The planning questions were resolved inside the approved identity, inclusion, external-access, provenance, and persistence boundary. They are no longer open PRD items.

### Atlassian

- FEAT-0053 used a bounded approved inventory and recorded direct official Jira evidence separately from unavailable official Confluence and company Gateway capabilities. Those unavailable host paths remain conditional future rechecks, not failed product behavior.
- FEAT-0054 kept one Add surface with reversible URL and connected-search methods, led with registered Site and Space/project scope, moved connection administration into a subordinate disclosure, and retained ordinary `Browser` and `Add` labels.
- Connected search selects Site, MCP connection, and Claude/Codex runner in that order. Local URL registration, preview, browsing, search, classification, and method switching remain local-only; only an explicit bounded discovery or refresh submission may read remotely.
- Private connected observations stayed local. Tracked route, test, and rendered evidence used synthetic fixtures, and no validation finding required a corrective Feature outside FEAT-0054.

### Schema ERD

- FEAT-0055 accepted Mermaid's rounded right-angle ELK output after global, sparse, dense, fallback, and supported-width comparison.
- FEAT-0056 applies ELK to every global and subject ERD as one Schema-only default without a user selector. The locally pinned bundle, license, freshness, determinism, labels, markers, zoom behavior, and document containment remain verified contracts.
- Rendering retries once with Dagre and then leaves the textual catalog authoritative if both diagram attempts fail.

## Constraints

- PRD-0008 and all four child Features are `passed`; later changes require their own approved boundary.
- Feature planning starts only after PRD approval.
- Connected Atlassian checks must follow the approved read-only capability policy and explicit remote-read intent.
- No private runtime content, company URL, ticket identifier, screenshot, credential, or machine-specific inventory may enter tracked artifacts.
- Mermaid and ELK assets must be pinned, locally built, license-accounted, freshness-checked, packaged offline, and consumed only through the approved adapter boundary.
- Visible changes require the Design Constitution, rendered design evidence, functional evaluation, and interaction evaluation.
- The later Atlassian Add correction is provisionally a `Fullstack Product` surface because the separated selectors require coordinated server read-model, route/form, template, and interaction behavior. Its expected lanes are Add information architecture, Site/MCP selection and provenance, connection-management disclosure, and responsive/error states; no schema change is currently confirmed.
- PRD approval does not freeze one Atlassian card, tab, segmented-control, disclosure, or copy composition. Feature and Spec review may refine those details while preserving the approved user outcomes, target/MCP/runner distinction, registered-database inclusion, Source Instance isolation, provenance, explicit remote-read consequence, and responsive/accessibility contracts.
- A proposed UI refinement that changes persistence identity, registration inclusion, remote-call scope, access-path selection semantics, or user-visible consequence returns to PRD review rather than being absorbed as visual iteration.
- Current passed PRD-0003, PRD-0007, FEAT-0051, and FEAT-0052 behavior remain regression surfaces.

## Acceptance Envelope

- The owner has reviewed and approved a bounded Atlassian test inventory, remote-read allowance, scenario matrix, privacy boundary, and evidence plan.
- Atlassian navigation exposes only the local-browse and Add intents, and discovery remains clearly a way to add rather than a peer top-level mode.
- Direct URL registration and connected candidate discovery no longer compete as unexplained side-by-side cards inside Add.
- Add orientation leads with recognizable Sites and Spaces/projects already persisted in the LocalBrain database, not an internal Source Instance explanation or connection count.
- Persisted scope records appear regardless of whether the supported registration producer was the Atlassian UI or an approved AI-assisted flow; unregistered candidates and presentation-only URL inference remain absent.
- Connection state appears only where it affects an available action or recovery.
- Ordinary Atlassian copy follows the approved PRD-0009 per-column or value-family presentation policy without changing the underlying persistence contract or falling back to an unapproved raw token.
- Connected candidate discovery asks for the target Site/domain and MCP connection separately, in that order, without requiring the user to understand a compound `Source Instance / Site` identifier.
- Target Site, MCP connection, and Claude/Codex maintenance runner remain three distinguishable choices: what to read, which access path to use, and which runner executes the bounded action.
- A Site reachable through both company MCP Gateway and official Atlassian MCP remains one recognizable target choice while the access path remains an explicit, provenance-preserving second choice.
- Agreed Atlassian scenarios have direct connected and rendered evidence where required, with source path, local state, remote state, maintenance execution, failure, and no-hidden-read claims checked separately.
- Every Atlassian finding is classified and routed without silently changing the passed contract.
- Current Dagre and candidate ELK results have been compared across the approved Schema diagrams and viewport/state matrix.
- If ELK is accepted, the resulting local packaged renderer provides the approved orthogonal routing without regressing labels, markers, fallback, zoom, navigation, determinism, packaging, or privacy.
- If ELK is rejected, the decision and evidence are retained without forcing a library replacement.
- Required automated, package, schema, privacy, contract, design, functional, and UX evidence passes for the later approved child Features.

## Implemented Features

The approved PRD was executed through these passed child Features:

1. [FEAT-0053: Connected Atlassian First-Use Validation](../feature/feat-0053-connected-atlassian-first-use-validation.md) (`passed`) — classified bounded direct official Jira evidence, explicit official Confluence and Gateway environment limitations, and local synthetic substitutes without silently changing passed behavior.
2. [FEAT-0054: Atlassian Add And Registered Scope Flow](../feature/feat-0054-atlassian-add-and-registered-scope-flow.md) (`passed`) — implemented the registered-scope-led Add information architecture and separate target/MCP/runner choices.
3. [FEAT-0055: Mermaid ELK Routing Contract](../feature/feat-0055-mermaid-elk-routing-contract.md) (`passed`) — accepted the official ELK loader as the Schema-only default after bounded comparison.
4. [FEAT-0056: Schema ERD Orthogonal Routing](../feature/feat-0056-schema-erd-orthogonal-routing.md) (`passed`) — packaged the accepted ELK path locally with one Dagre retry and textual fallback.

No defect finding required a corrective Feature outside FEAT-0054. All four child Features passed with their required evaluators and final repository closure checks.

## Closure Evidence

- RUN-20260724-58, RUN-20260724-62, RUN-20260724-59, and RUN-20260724-63 passed in dependency order.
- Direct official Jira metadata access passed within the approved bounded inventory. Official Confluence and company Gateway absence were retained as environment limitations; no fabricated read or private payload entered tracked evidence.
- The registered-scope-led Atlassian Add flow passed route, contract, and rendered checks at `1440`, `920`, `700`, and `320` without hidden remote reads.
- Official ELK was accepted, packaged locally, license-accounted, byte-freshness checked, and applied to all nine Schema subject diagrams with one Dagre retry and textual fallback.
- The final `288`-test repository suite, Mermaid asset checks, Schema/Data Model checks, and repository privacy inspection passed on `2026-07-27`.

## Drift Watchlist

- Connected official Atlassian MCP and company Gateway capability availability and tool schemas.
- Jira and Confluence remote response shapes and permissions.
- Mermaid and `@mermaid-js/layout-elk` compatible pinned versions and loader contract.
- Schema diagram count, density, labels, and relation shapes.
- Browser-control availability for connected and rendered evidence.
- Any code or policy changes made before the relevant child Feature is approved.

## Regression Targets

Inspect these before a later approved change; they are regression context, not standing authorization:

- [PRD-0007](prd-0007-atlassian-source-memory-and-refresh.md), FEAT-0044 through FEAT-0051, and their latest evaluations.
- `src/localbrain/atlassian*.py`, `external_access.py`, `external_sync.py`, Atlassian templates/assets, and focused tests.
- [PRD-0003](prd-0003-data-model-visibility-and-schema-cleanup.md), [FEAT-0052](../feature/feat-0052-schema-diagram-zoom-navigation.md), and their latest evaluations.
- `package.json`, `scripts/build-mermaid-assets.mjs`, `src/localbrain/static/mermaid-adapter.js`, `schema-explorer.js`, Schema presentation sources, and Mermaid asset tests.
- Product, privacy, Schema presentation, design, and interaction policies.

## Source Sync Status

- Sources checked this session: owner direction, PRD-0003/FEAT-0052 lineage, current Mermaid package/config/renderer evidence, official Mermaid ER/layout documentation, PRD-0007/FEAT-0051 lineage, current Atlassian implementation/test inventory, PRD-0009, workflow rules, roadmap, and backlog.
- Source deltas: ELK was accepted as a supported Mermaid companion layout and adopted locally rather than replacing the library; connected Atlassian validation and the Add correction completed under this PRD; owner review fixed one Add intent, separate target/MCP choices, and internal-only Source Instance terminology for ordinary Add interaction; cross-subject value-dictionary ownership remains with passed PRD-0009.
- External recheck needed: `conditional`. Official Confluence and company Gateway remain environment-limited; recheck only when those host capabilities become available or their contracts change.

## Closure Handoff

- No child Feature remains active.
- Future official Confluence or company Gateway validation must use a newly approved bounded inventory; environment availability is not a failed product contract.
- Future Mermaid or ELK updates must retain exact local packaging, license, freshness, attempt-order, and fallback checks.
- Later Atlassian composition refinements may continue within the passed identity, inclusion, access, provenance, and explicit-remote-read boundaries.

## Continuity Notes

- `2026-07-24`: created a minimal draft at the owner's request because the current context had grown too large. The owner explicitly deferred Atlassian testing details and ELK adoption details to the next session.
- `2026-07-24`: reconciled the earlier “basis is fixed” wording: the public Dagre ER path has no `er.curve` switch, while official Mermaid ELK is a supported companion layout and does not require replacing Mermaid.
- `2026-07-24`: owner review renamed the Atlassian top-level add intent from `Add / discover` to `Add`, rejected the side-by-side URL/discovery composition, retained Source Instance as the internal connection boundary, and required connected discovery to separate the target Site/domain choice from the MCP access-path choice.
- `2026-07-24`: owner review replaced the connection-centric Add orientation with a Site-and-Space database overview. Inclusion follows current persisted registration, not whether the producer was the Atlassian UI or an approved AI-assisted flow; unregistered candidates and presentation-only link inference remain excluded.
- `2026-07-24`: owner review identified raw database enum copy such as `selected-content` as a physical/logical presentation leak and requested subject-oriented value definitions under the data-model documentation before broad UI terminology normalization. The owner clarified that presentation policy belongs to the whole enum column or bounded value family: every value renders directly, every value receives a logical label, or the whole family remains internal-only. Mixed translated/raw values in one family are forbidden.
- `2026-07-24`: owner review clarified that PRD approval should not freeze the changing Atlassian screen composition. Exact controls, layout, and copy may converge during Feature and Spec review, while identity, inclusion, access, provenance, remote-read consequence, and interaction-order changes remain PRD-level.
- `2026-07-24`: split the nine-subject value-dictionary definition and audit boundary to PRD-0009. PRD-0008 now owns only Atlassian consumption of an approved mapping and is structured as an approval candidate rather than a next-session placeholder.
- `2026-07-24`: the owner approved PRD-0008 and requested Feature decomposition. FEAT-0053 through FEAT-0056 were created as draft validation, Atlassian Add, ELK contract, and conditional routing-adoption boundaries.
- `2026-07-27`: FEAT-0053 through FEAT-0056 and repository-wide closure verification passed. PRD-0008 is the canonical completed boundary; unavailable official Confluence and company Gateway host capabilities remain conditional future recheck signals rather than open implementation work.
