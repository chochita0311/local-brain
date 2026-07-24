# PRD-0008: Connected Atlassian Validation And Schema ERD Routing

## Metadata

- ID: `prd-0008`
- Status: `draft`
- Owner role: `human`
- Created: `2026-07-24`
- Updated: `2026-07-24`
- User review status: `pending`
- Approval mode: `strict`

## Request Summary

- Carry two explicitly deferred follow-ups into the next planning session:
  - validate the implemented Atlassian workflow against the owner's connected MCP paths and agreed first-use scenarios;
  - evaluate and, if approved, adopt Mermaid's official ELK layout path for Draw.io-like orthogonal Schema ERD routing without replacing Mermaid.
- Keep this document as an intake boundary only. The owner will add detailed scenarios, exclusions, and acceptance requirements in the next session before PRD approval or Feature decomposition.

## Workflow Scope

- Workflow root: LocalBrain repository.
- Current repository: LocalBrain.
- Related repositories: none confirmed.
- Repository aliases: none required.
- Current goal: preserve a restart-ready planning boundary without continuing implementation in the current large context.

## Source Set

| Source ID | Type | Location | Role | Freshness | Owner or update path |
| --- | --- | --- | --- | --- | --- |
| `human-20260724-follow-up` | other | current owner direction, summarized here rather than copied verbatim | planned work | current through `2026-07-24` | human review of this PRD |
| `prd-0003` | doc | [Data Model Visibility And Schema Cleanup](prd-0003-data-model-visibility-and-schema-cleanup.md) | historical note and passed product boundary | checked `2026-07-24` | PRD-0003 and its passed Features |
| `feat-0052` | doc | [Schema Diagram Zoom Navigation](../feature/feat-0052-schema-diagram-zoom-navigation.md) | historical note and passed interaction boundary | checked `2026-07-24` | FEAT-0052 |
| `schema-implementation` | repo | `package.json`, `scripts/build-mermaid-assets.mjs`, `src/localbrain/static/mermaid-adapter.js`, and Schema presentation sources | implementation truth | checked `2026-07-24` | current repository code |
| `mermaid-layout-contract` | doc | [Mermaid ER layout](https://mermaid.js.org/syntax/entityRelationshipDiagram.html#layout), [Mermaid layouts](https://mermaid.js.org/config/layouts.html), and Mermaid 11.16 package sources | authoritative library contract | checked `2026-07-24` | official Mermaid documentation and pinned package |
| `prd-0007` | doc | [Atlassian Source Memory And Explicit Refresh](prd-0007-atlassian-source-memory-and-refresh.md) | historical note and passed product boundary | checked `2026-07-24` | PRD-0007 and FEAT-0044 through FEAT-0051 |
| `atlassian-implementation` | repo | `src/localbrain/atlassian*.py`, external-access/sync modules, routes, templates, client assets, and focused tests | implementation truth | checked `2026-07-24` | current repository code |
| `connected-atlassian-runtime` | runtime | owner-connected official Atlassian MCP and company MCP Gateway paths | future operational signal | unknown until next-session test authorization | explicit owner-directed read-only checks |

## Source Relationships

- PRD-0008 follows the passed PRD-0003 Schema increment without reopening its completed data-model, presentation, or zoom contracts.
- PRD-0008 follows the passed PRD-0007 Atlassian increment without reclassifying its automated implementation evidence as live connected evidence.
- The two follow-up lanes are independent candidate execution boundaries even though the owner wants them reviewed under one next PRD.
- A connected Atlassian observation may expose a defect or missing behavior, but it does not silently modify the passed PRD-0007 contract; any resulting change must return to this draft's scope review and later Feature planning.

## Source-Of-Truth Rules

- Explicit human direction owns this draft's product scope and approval boundary.
- Current repository code owns implemented behavior.
- Approved policies own privacy, external-access, local-asset, Schema presentation, and evaluation constraints.
- A directly observed, explicitly authorized connected Atlassian result owns current remote behavior for that test; synthetic and route evidence remain regression evidence rather than a substitute for that observation.
- Official Mermaid documentation and the pinned package own supported layout capability; the current LocalBrain asset manifest owns what is actually bundled.
- This `draft` PRD is planned work only and must not trigger Feature, Spec, Run, dependency, or code changes.

## Reconciliation Notes

| Topic | Source claims | Status | Working assumption | Follow-up target |
| --- | --- | --- | --- | --- |
| ER relationship curve option | The pinned default Dagre ER renderer emits `basis` edges, while the public `curve` setting is Flowchart-specific. Official ER documentation supports selecting the ELK layout when its loader is enabled. | `aligned` | A simple `er.curve=linear` toggle is not available; ELK is the supported candidate path. | next-session PRD review |
| Mermaid replacement | Official Mermaid supports external layout loaders, and current LocalBrain already owns a pinned local Mermaid asset pipeline. | `aligned` | Mermaid does not need to be replaced; the candidate change is an official companion layout dependency plus bounded adapter/asset work. | next-session scope and candidate Feature review |
| Desired ERD routing | The owner prefers Draw.io-like orthogonal relations; current 11.16 behavior with ELK is expected to produce right-angle segments with rounded corners. | `open` | Do not assume rounded corners, sharp corners, a layout toggle, or ELK-as-default is accepted until visual comparison. | define golden comparison and acceptance envelope |
| Atlassian automated evidence | PRD-0007's child Features passed focused, migration, route, UI, schema, privacy, and full-suite checks. Several follow-up reports explicitly distinguish source-level or synthetic evidence from direct connected first-use observation. | `aligned` | Existing implementation remains passed; PRD-0008 owns additional connected validation rather than retroactively failing PRD-0007. | define next-session validation matrix |
| Connected Atlassian scope | The owner has official Atlassian MCP and company Gateway paths and wants Atlassian testing in the next PRD. Exact Sites, services, operations, test records, and allowed remote reads have not been fixed here. | `open` | Perform no additional Atlassian read in this session. | owner supplies or approves the bounded test inventory next session |
| Follow-up defects | Live validation or ELK comparison may reveal implementation, spec, or planning gaps. | `open` | Record and classify findings before creating child Features; do not fix opportunistically during discovery. | PRD-0008 review and later Feature planning |

## Product Intent

- Replace assumption-based confidence with explicit owner-reviewed evidence for the real connected Atlassian workflow while preserving the read-only, local-first, explicit-refresh, and provenance boundaries established by PRD-0007.
- Make dense Schema ERDs easier to trace with an orthogonal routing candidate familiar to Draw.io users, while preserving Mermaid source ownership, offline packaging, textual fallback, and the passed zoom interaction.

## Confirmed Scope

### Atlassian Validation Intake

- Include a next-session Atlassian validation lane using the already connected MCP paths.
- Treat connected runtime checks, rendered first-use behavior, and any agreed end-to-end workflow scenarios as distinct from existing synthetic and source-level evidence.
- Keep the integration read-only and require explicit scope before any remote request.
- Preserve the existing Source Instance, Site, Item, remote/local ownership, freshness, explicit preview/refresh, maintenance Run, search, Topic/Tag, and Workstream/Thread contracts unless an observed finding is returned to planning.
- Record findings with enough evidence to classify them as implementation bug, spec gap, planning gap, environment limitation, or no defect.

### Schema ERD Routing Intake

- Include Mermaid ELK as the preferred orthogonal-routing candidate.
- Preserve Mermaid as the diagram library; do not assume a wholesale renderer or product-surface replacement.
- Keep dependencies local and pinned, with no CDN or runtime network requirement.
- Preserve the existing generated Schema source, strict owned-node trust boundary, failure fallback, diagram zoom, ordinary scrolling, and package/privacy checks.
- Compare the current Dagre output and candidate ELK output before deciding whether ELK becomes the default, an optional control, or is rejected.

### Next-Session Planning

- Add the detailed test matrix, representative states, approved connected-source boundary, expected visual evidence, exclusions, and acceptance checks in the next session.
- Keep all candidate Features uncreated and unapproved until this draft boundary is reviewed.

## Excluded Scope

- Atlassian, Jira, Confluence, Slack, email, or other external writes.
- Credential, token, OAuth, or MCP installation changes.
- Automatic old/new Atlassian migration reconciliation, cross-domain merge, or successor inference.
- Background refresh, hidden remote reads, or broad source inventory crawling.
- Atlassian functionality changes before a validated finding returns to planning.
- Replacing Mermaid with Draw.io, a freeform editor, or another diagram product.
- Manual table positioning, drag editing, saved edge waypoints, or full diagram authoring.
- Mermaid bundle patching or post-render SVG path rewriting as the default solution.
- Feature, Spec, Run, dependency, or implementation work in the current session.

## Uncertainty And Open Questions

### Atlassian

- Which connected Source Instances, Sites, Jira tickets, Confluence Pages or Spaces, and Workstream/Thread mappings form the approved test inventory?
- Must both official Atlassian MCP and company MCP Gateway paths be exercised, and for which service on each path?
- Which scenarios require a real remote read versus local-only registration, preview, browse, search, or classification evidence?
- Which first-use, no-change, stale, unavailable, partial-failure, retry, and refresh-result states are required?
- What private runtime evidence may be observed locally, and what synthetic substitutes must be used for tracked artifacts?
- Should validation findings become multiple narrow Features or one bounded corrective Feature after classification?

### Schema ERD

- Is the acceptable target sharp orthogonal routing or Mermaid's rounded right-angle ELK routing?
- Should ELK apply to every global and subject ERD or only dense diagrams?
- Should ELK replace Dagre by default, be exposed as a visible toggle, or remain an internal evaluated choice?
- What bundle-size and render-time increase is acceptable?
- Which node placement, relation-label, cardinality-marker, determinism, fallback, and supported-width comparisons are required?
- What is the fallback if ELK degrades one or more diagrams?

## Constraints

- PRD-0008 remains `draft` and planning-only until the human owner reviews the detailed next-session boundary.
- Feature planning starts only after PRD approval.
- Connected Atlassian checks must follow the approved read-only capability policy and explicit remote-read intent.
- No private runtime content, company URL, ticket identifier, screenshot, credential, or machine-specific inventory may enter tracked artifacts.
- Mermaid and ELK assets must be pinned, locally built, license-accounted, freshness-checked, packaged offline, and consumed only through the approved adapter boundary.
- Visible changes require the Design Constitution, rendered design evidence, functional evaluation, and interaction evaluation.
- Current passed PRD-0003, PRD-0007, FEAT-0051, and FEAT-0052 behavior remain regression surfaces.

## Preliminary Acceptance Envelope

This envelope is intentionally incomplete until the next session:

- The owner has reviewed and approved a bounded Atlassian test inventory, remote-read allowance, scenario matrix, privacy boundary, and evidence plan.
- Agreed Atlassian scenarios have direct connected and rendered evidence where required, with source path, local state, remote state, maintenance execution, failure, and no-hidden-read claims checked separately.
- Every Atlassian finding is classified and routed without silently changing the passed contract.
- Current Dagre and candidate ELK results have been compared across the approved Schema diagrams and viewport/state matrix.
- If ELK is accepted, the resulting local packaged renderer provides the approved orthogonal routing without regressing labels, markers, fallback, zoom, navigation, determinism, packaging, or privacy.
- If ELK is rejected, the decision and evidence are retained without forcing a library replacement.
- Required automated, package, schema, privacy, contract, design, functional, and UX evidence passes for the later approved child Features.

## Candidate Feature Directions

No child Feature is created or approved in this session. Preliminary directions for next-session decomposition are:

- Atlassian connected first-use and end-to-end validation.
- Bounded corrective Atlassian Features derived only from classified findings.
- Schema ERD ELK asset and layout contract.
- Schema orthogonal-routing product adoption and rendered regression evidence.

These directions may be split, merged, reordered, narrowed, or rejected during PRD review.

## Drift Watchlist

- Connected official Atlassian MCP and company Gateway capability availability and tool schemas.
- Jira and Confluence remote response shapes and permissions.
- Mermaid and `@mermaid-js/layout-elk` compatible pinned versions and loader contract.
- Schema diagram count, density, labels, and relation shapes.
- Browser-control availability for connected and rendered evidence.
- Any code or policy changes made before PRD-0008 review resumes.

## Working Targets For The Next Session

Inspect these first; they are context targets, not authorized implementation tasks:

- [PRD-0007](prd-0007-atlassian-source-memory-and-refresh.md), FEAT-0044 through FEAT-0051, and their latest evaluations.
- `src/localbrain/atlassian*.py`, `external_access.py`, `external_sync.py`, Atlassian templates/assets, and focused tests.
- [PRD-0003](prd-0003-data-model-visibility-and-schema-cleanup.md), [FEAT-0052](../feature/feat-0052-schema-diagram-zoom-navigation.md), and their latest evaluations.
- `package.json`, `scripts/build-mermaid-assets.mjs`, `src/localbrain/static/mermaid-adapter.js`, `schema-explorer.js`, Schema presentation sources, and Mermaid asset tests.
- Product, privacy, Schema presentation, design, and interaction policies.

## Source Sync Status

- Sources checked this session: owner direction, PRD-0003/FEAT-0052 lineage, current Mermaid package/config/renderer evidence, official Mermaid ER/layout documentation, PRD-0007/FEAT-0051 lineage, current Atlassian implementation/test inventory, workflow rules, roadmap, and backlog.
- Source deltas: ELK is now recorded as a supported Mermaid companion-layout candidate rather than a library replacement; connected Atlassian validation is explicitly moved to the next PRD.
- External recheck needed: `yes`, but only after the owner approves the exact next-session Atlassian test boundary.

## Next Handoff Note

- Resume from PRD-0008 as the canonical next-session planning context.
- First ask the owner for the detailed Atlassian test inventory and the desired ELK visual/interaction outcome.
- Refresh only the connected capabilities required by that approved inventory; do not rediscover every external source.
- Complete confirmed scope, exclusions, open decisions, and acceptance criteria, then stop for PRD approval.
- Do not create Features, Specs, Runs, install ELK, or execute connected Atlassian tests before that review.

## Continuity Notes

- `2026-07-24`: created a minimal draft at the owner's request because the current context had grown too large. The owner explicitly deferred Atlassian testing details and ELK adoption details to the next session.
- `2026-07-24`: reconciled the earlier “basis is fixed” wording: the public Dagre ER path has no `er.curve` switch, while official Mermaid ELK is a supported companion layout and does not require replacing Mermaid.
