# PRD-0016: Atlassian Standard URL Structure References

## Metadata

- ID: `prd-0016`
- Status: `passed`
- Boundary State: passed; FEAT-0082 and FEAT-0083 passed, and no active child
  Feature remains
- Owner role: `human`
- Created: `2026-09-01`
- Updated: `2026-09-01`
- User review status: sequential foundation and durable product outcome completed

## Request Summary

- Statically recognize standard Jira and Confluence URL families found in
  persisted Session and Local Context evidence.
- Preserve an exact, privacy-safe structure identity for Project, Board, Filter,
  Dashboard, JSM portal/project, and Confluence Space references, then expose
  those references durably through explicit Sync and the Site-first Explorer.

## Source Set

- Human approval: a pure descriptor foundation first, followed by a durable
  structure-reference Sync/Explorer product Feature.
- Golden sources: passed PRD-0014 and PRD-0015, FEAT-0047, FEAT-0073,
  FEAT-0080, FEAT-0081, current Product, Architecture, Privacy, and Atlassian
  Source Memory.
- Official supporting examples: Atlassian's
  [project-centric RapidBoard link](https://developer.atlassian.com/server/jira/platform/developing-for-the-jira-project-centric-view/),
  [saved-filter URL example](https://support.atlassian.com/jira/kb/how-to-validate-all-filters-in-jira/),
  [Dashboard REST `view` URL](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-dashboards/),
  [Confluence Page path examples](https://developer.atlassian.com/cloud/confluence/extension-point-locations/),
  [Confluence `viewpage.action?pageId=` example](https://support.atlassian.com/jira/kb/how-to-link-a-confluence-page-on-a-jira-cloud-issue-via-rest-api/),
  and [Confluence Space path contract](https://developer.atlassian.com/platform/forge/manifest-reference/modules/confluence-space-page/).
  These support the locked fixture shapes; they are not an exhaustive promise
  to recognize every Atlassian URL variant.
- Pre-PRD-0016 implementation baseline: duplicate evidence/registration URL
  regex, generic Session query stripping, strict Issue/Page-only Sync admission,
  and the passed Site-first Explorer. The completed chain replaces that URL
  parsing baseline without rewriting its historical evidence.

## Product Intent

- Make a locally observed Atlassian structure URL reconnectable without
  pretending that it is a Jira Issue, Confluence Page, persisted Project/Space,
  access binding, Refresh result, or remotely confirmed object.

## Confirmed Scope

- One shared, pure, versioned static descriptor with exact `item`, `structure`,
  `site`, `unsupported`, and `unsafe` kinds.
- Common recognized fields: service, URL family, normalized domain/base, and a
  privacy-minimized safe locator.
- Exact Item identity for Jira Issue and Confluence Page forms.
- Exact structure-reference kind and identity, each identity at most 300 code
  points, for Jira Project, Board, Filter, Dashboard, JSM portal/project, and
  Confluence Space forms; an optional Project/Space container hint never becomes
  containment authority.
- A `site` result recognizes a standard service/domain landing family but has
  no structure identity. Sync reports it as a truthful bounded Site-only
  outcome, but it never creates an Explorer structure-reference row.
- Path Item identity wins over query-derived Item identity; exact Item identity
  wins over structure/site classification. Within a structure family, only one
  allowlisted unambiguous identity value can create structure identity.
- Safe locators discard fragments, JQL, and arbitrary query. They retain only
  canonical allowlisted identity projection needed to preserve the reference;
  RapidBoard keeps canonical `rapidView`, and may keep one validated
  `projectKey` only as a non-authoritative grouping hint.
- Session reference grouping derives from the semantic Item/structure/site
  descriptor, not the whole URL, so equivalent standard variants do not split
  or collapse identity accidentally.
- FEAT-0082 owns the parser, safe Session projection, identity precedence,
  consumer adapters, and extractor versions. It creates no durable structure
  reference and adds no Atlassian screen or Sync report; ordinary Session
  projection repair may correct generic URL deduplication and destination.
- FEAT-0083 owns durable structure-reference persistence/evidence, explicit
  Sync reconciliation/reporting, Site-first hierarchy/list/detail/Search
  projection, responsive interaction, and action separation.

## Excluded Scope

- Creating or inferring an Atlassian Item or persisted Project/Space from a
  structure reference; writing `space_id`; or treating a container hint as
  remote confirmation.
- Provider inference, Source Instance/binding creation, capability inspection,
  remote reads, connected discovery, Refresh, model work, embeddings, or
  external writes during parsing, Sync, or Browse.
- Persisting credentials, fragments, raw query, JQL, arbitrary query values,
  copied source text, or opaque tool payloads.
- Treating a family root with no stable reference identity as a selectable
  zero-count hierarchy node.
- Rewriting passed PRD-0015/FEAT-0081/SPEC-0080/SPEC-0081 history as though it
  had accepted structure references.

## Uncertainty

- No product-boundary uncertainty remains: passed FEAT-0083 produces a durable,
  visibly selectable structure reference rather than report-only Site
  recognition or a zero-count Site branch.
- FEAT-0083's executable schema, evidence lifecycle, route/read-model, and
  interaction details are locked by SPEC-0083 after FEAT-0082 passed; that
  sequencing does not reopen the approved product outcome.

## Constraints

- Parsing is deterministic, bounded, local, configured-domain independent, and
  performs no SQLite, filesystem, Provider, model, capability, or network work.
- Descriptor kind is not persistence authority. Every consumer admits an exact
  subset and preserves passed Site/service/URL ownership.
- Structure identity is scoped by normalized Site domain, service,
  `reference_kind`, and `reference_identity`; `container_hint` and locator
  spelling do not enter that identity.
- A RapidBoard URL without one valid positive `rapidView` cannot become a Board
  structure reference. It remains only a `site` family result.
- Query projection is fixed per family and canonical. The application never
  preserves arbitrary query to keep a URL navigable.
- Derived Session evidence remains rebuildable and versioned. Durable FEAT-0083
  structure identity and evidence must remain separate from Session/Document
  source content and from persisted Space/Item authority.

## Acceptance Envelope

- FEAT-0082 passes with exhaustive family/precedence/privacy fixtures, semantic
  Session target grouping, stable safe locators, version repair, explicit
  consumer admission, and zero structure-reference DML or hidden I/O.
- `RapidBoard.jspa?rapidView=17&projectKey=PAY` yields one Jira Board structure
  identity `17`, hint `PAY`, and a safe locator that drops all non-allowlisted
  query without collapsing Board `17` into another Board.
- Jira/Confluence Issue/Page forms remain Items and win over structural URL
  context. Family roots without an exact structure identity remain `site`, not
  selectable references.
- FEAT-0083 passes when one durable Site-scoped reference per semantic identity
  reconciles source evidence, reports it separately, and renders one honest
  Explorer row/detail with count parity.

## Candidate Features

- [FEAT-0082: Atlassian Structure Reference Locator Foundation](../feature/feat-0082-atlassian-static-url-locator-contract.md): passed [RUN-92 Attempt 1](../run/run-20260901-92-atlassian-static-url-locator-contract.md) with Contract and Functional `PASS`.
- [FEAT-0083: Atlassian Structure Reference Sync And Explorer](../feature/feat-0083-atlassian-structure-reference-sync-and-explorer.md): passed [RUN-93 Attempt 1](../run/run-20260901-93-atlassian-structure-reference-sync-and-explorer.md) with Contract, Design, Functional, and UX `PASS` after its FEAT-0082 dependency gate passed.

## Continuity Notes

- `2026-09-01`: created as a new approved follow-up rather than widening passed
  PRD-0015. PRD-0015 and FEAT-0081 remain the historical baseline for strict
  Issue/Page empty-Sync admission and Site-first Item hierarchy.
- `2026-09-01`: owner corrected the initial weak Site-only draft. The approved
  result preserves semantic structure identity in FEAT-0082 and makes durable
  visible structure references the fixed FEAT-0083 product outcome.
- `2026-09-01`: FEAT-0082 passed RUN-92 Attempt 1 with both required evaluators
  at `PASS`; the sequential dependency gate for FEAT-0083 is satisfied.
- `2026-09-01`: SPEC-0083 and RUN-93 were approved after the dependency close;
  FEAT-0083 became the sole in-loop Atlassian Feature with no unresolved
  product-boundary blocker.
- `2026-09-01`: FEAT-0083 passed RUN-93 Attempt 1 with all four required
  evaluators, full `480/480` regression coverage, owner/generated parity, and
  Chrome evidence at `1440`, `920`, `700`, and `320`. PRD-0016 is passed and
  has no active child Feature.
