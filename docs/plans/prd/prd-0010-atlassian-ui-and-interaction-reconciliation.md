# PRD-0010: Atlassian UI And Interaction Reconciliation

## Metadata

- ID: `prd-0010`
- Status: `approved`
- Boundary State: open for later owner observations; FEAT-0062 and FEAT-0063 passed
- Owner role: `human`
- Created: `2026-07-27`
- Updated: `2026-08-02`
- User review status: `confirmed through implementation direction`
- Approval mode: `sequential feature execution`

## Request Summary

- Reconcile visible UI and interaction inconsistencies across the existing
  Atlassian screen family without reopening the passed read-only source,
  identity, refresh, or persistence contracts.
- Collect owner-observed problems one at a time under this approved incremental
  boundary, preserve their shared or page-local ownership, and require a
  separately approved Feature before implementation.

## Source Set

- Human request:
  - keep the upper PRD boundary limited to Atlassian;
  - add visible observations incrementally and later divide the confirmed set
    into Features;
  - observations that prove to be product-wide must move to their shared owner
    rather than remaining an Atlassian-only patch.
- Golden sources:
  - the owner's direct review of the current LocalBrain Atlassian screens.
- Supporting docs:
  - [Design Constitution](../../policies/design/design-constitution.md)
  - [Design Evaluation](../../policies/design/design-evaluation.md)
  - [Interaction Evaluation](../../policies/experience/interaction-evaluation.md)
  - [PRD-0007: Atlassian Source Memory And Explicit Refresh](prd-0007-atlassian-source-memory-and-refresh.md)
  - [PRD-0008: Connected Atlassian Validation And Schema ERD Routing](prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Current implementation references:
  - `src/localbrain/templates/atlassian.html`
  - `src/localbrain/templates/atlassian-item.html`
  - `src/localbrain/templates/atlassian-refresh.html`
  - `src/localbrain/static/styles.css`

## Product Intent

- Make Atlassian controls and workflows feel like one deliberate product
  surface instead of a collection of locally styled forms.
- Correct visible drift at the shared owning layer when evidence shows that
  several Atlassian consumers have the same problem.
- Preserve current user tasks, remote-read boundaries, local provenance, and
  existing information architecture while the presentation is reconciled.

## Plan Type

- Combination of visual consistency and interaction consistency.
- Approved incremental reconciliation plan. Durable product-wide visual law
  remains owned by the Design Constitution.

## Confirmed Scope

- Existing Atlassian product surfaces:
  - `/atlassian` browse, Add, connection, discovery, and filter controls;
  - persisted Atlassian Item detail and local organization controls;
  - explicit refresh preview and runner selection.
- Owner-observed visual or interaction inconsistencies confirmed while this
  approved PRD remains open for later observations.
- Shared-owner analysis before treating a repeated mismatch as page-local.
- Preservation of current control semantics, labels, form values, keyboard
  behavior, disabled state, validation, and no-script submission paths.
- Responsive validation at the supported `1440`, `920`, `700`, and `320`
  widths with synthetic content.

### Finding A-01: Native Select Disclosure Geometry

- Status: `moved to shared owner`
- The owner confirmed that the same disclosure-arrow clearance and text-space
  problem appears in Workstream and other native selects, not only Atlassian.
- [PRD-0011: Shared Native Select Control Geometry](prd-0011-shared-native-select-control-geometry.md)
  now owns the shared primitive, full consumer inventory, acceptance boundary,
  and candidate Feature.
- Atlassian selects remain adoption and regression surfaces under PRD-0011 but
  are no longer an Atlassian-only Feature candidate here.

### Finding A-02: Existing Connection Versus New Connection Clarity

- Status: `confirmed direction`
- Observed question:
  - the Local-only URL Add form presents `기존 MCP 연결` and a nearby
    `새 연결 설정` disclosure, but their functional difference and mutual
    exclusivity are not self-evident.
  - the owner identified that `기존 MCP 연결` actually represents a combined
    Site plus Source Instance choice and questioned why a live MCP connection
    should be mandatory for a local-only URL registration.
- Owner direction:
  - local-only URL registration must not require a Provider or functioning MCP
    connection;
  - external access configuration remains optional until the user starts a
    connected discovery or refresh task;
  - `MCP 연결 이름` is not a user-managed alias and should be removed; an
    access binding already has its Provider and actual configuration value;
  - `Site 표시 이름` is not selected or entered during local registration. It
    is derived from the normalized URL/domain;
  - `connection reference` is not collected by Local-only Add. It belongs only
    to an explicit remote-access setup or binding task;
  - Local-only registration and optional remote-access setup are separate
    actions. When presented together, the access setup region belongs to the
    right of Local-only Add rather than below it at wide and compact widths;
  - at narrow widths the two regions may stack in the same left-to-right
    reading order without making optional access look mandatory.
  - canonical Site identity is the normalized Atlassian domain, not
    `service + normalized domain`;
  - `service` means the Atlassian product family, currently Jira or
    Confluence. It belongs to the registered Space/Item and to an optional
    access binding's capability, because one Atlassian domain may expose both
    products.
- Pre-implementation behavior:
  - `기존 MCP 연결` selects an existing LocalBrain Atlassian Site backed by
    one Source Instance; the URL is registered under that existing identity and
    its provider/configuration is preserved;
  - one enabled Site matching the entered URL domain is selected
    automatically, while multiple matching Sites require an explicit choice;
  - `새 MCP 연결 만들기` activates the new-connection fields and atomically
    creates or reuses a compatible local Source Instance, Site, and URL
    registration;
  - the Provider field chooses the intended approved access path, while the
    optional connection reference binds that local identity to a remote
    configuration;
  - leaving the connection reference empty creates an unbound local-only
    Source Instance. It records the link but is not ready for remote discovery
    or refresh until it is bound later;
  - neither existing-connection reuse nor new-connection setup performs a
    remote read during URL registration;
  - new-connection form fields are ignored by the server when an existing Site
    is selected.
- Pre-implementation requirement split:
  - a stable Site and its parent Source Instance were structurally required by
    the pre-change schema;
  - `provider_kind` was also structurally required on every Source Instance,
    including an unbound local-only record;
  - the pre-change Source Instance also required one `service`, while Space and
    Item records repeated their own service. This prevented Site identity from
    standing independently of an access path and product capability;
  - an actual remote binding (`config_ref`) and a current capability
    observation were not required for local-only registration;
  - therefore the pre-change UI required an intended future access-path category,
    not a functioning MCP connection.
- Pre-implementation `MCP 연결 이름` behavior:
  - the field wrote only `external_source_instances.display_name`;
  - the value was a user-facing label shown in connection selection and
    management, Atlassian Space/Item inventory, search context, Item detail,
    and refresh targets;
  - it could affect display ordering but did not authorize access, bind a Cloud
    ID or Gateway alias, establish capability, or determine remote identity;
  - because Site already has its own display name, exposing both names during a
    local-only registration creates duplicate naming work before an MCP access
    record is needed.
- Pre-implementation `Site 표시 이름` behavior:
  - the field wrote `atlassian_sites.display_name`;
  - when omitted, the producer derived an initial value from
    the first segment of the normalized URL domain;
  - the owner does not want this initial local label to be a registration
    choice. URL/domain identity should determine the local Site automatically;
  - a later provider-confirmed Site label may remain remote/display evidence,
    but local Add does not request a custom Site alias.
- Pre-implementation presentation risk:
  - the existing selector was labeled as an MCP connection although its submitted
    identity was an Atlassian Site;
  - `새 연결 설정` remained present beside the existing choice, and a disclosure
    opened while `new` was selected did not automatically close when the user
    returned to an existing Site;
  - choosing a Provider could read like establishing a live MCP authentication
    even when the result was only an unbound local record;
  - showing `연결 reference · 나중에 설정 가능` inside Local-only Add still
    implied that remote binding was part of the local registration task.
- Approved contract:
  - one Site is identified by its normalized domain and may exist with no
    access binding;
  - a Site binding relates that Site to a Source Instance and its Provider,
    service, reference, enabled state, and capability evidence;
  - existing Site/Source ownership migrates into explicit bindings without
    deleting registered Items, Spaces, relations, refresh history, or content;
  - Local-only Add contains no Site/Source selector. It resolves or creates the
    Site from the URL;
  - optional remote access is a separate right-hand card at wide and compact
    widths and stacks after Local-only Add at narrow widths;
  - the access card selects the URL-derived Site, real Provider, and actual
    connection reference. Generated implementation labels are not editable
    aliases.

### Finding A-03: Local Display Name At Registration

- Status: `confirmed direction`
- Observed question:
  - the owner asked what the optional `로컬 표시 이름` in Local-only URL Add
    is used for.
- Pre-implementation behavior:
  - for a Jira ticket or Confluence Page, the value became
    `external_resources.title`, which is the stable local title used by
    Atlassian inventories, Item detail, local search identity, Workstream
    relations, and related local presentation;
  - when omitted for an Item, the fallback was the complete normalized
    URL rather than a compact key or Page identity;
  - a later remote refresh stored remote summary/title as remote metadata but
    did not replace this local title;
  - for a Jira project or Confluence Space URL, the value became
    `atlassian_spaces.name`; when omitted, the project/Space key was used;
  - the field changed only local presentation. It did not affect Site,
    Provider, remote identity, capability, refresh scope, or authorization.
- Owner direction:
  - the owner confirmed that initial registration does not need a user-authored
    local alias;
  - remove `로컬 표시 이름` from Local-only Add;
  - infer a deterministic compact bootstrap title from the URL identity: Jira
    Item key, Jira project key, Confluence Space key, or Confluence Page URL
    title segment with Page ID as fallback;
  - keep remotely confirmed Jira summary or Confluence title in its existing
    remote metadata ownership and let the read model prefer it where the screen
    represents remote facts;
  - do not combine title and description into a generated alias.

## Excluded Scope

- A broad LocalBrain redesign or another shell/navigation realignment.
- Further changes to Atlassian source identity, registration, freshness,
  refresh, capability, remote-read, storage, or search behavior beyond the
  approved Finding A-02 Site/access-binding correction, unless a later owner
  observation explicitly reveals another planning-level contradiction.
- New Atlassian write operations, background synchronization, or broader remote
  access.
- Product-wide native-select geometry, which is owned by PRD-0011.
- Spec, implementation, or evaluator work for a later observation before its
  Feature boundary is approved.

## Resolved Decisions And Deferred Scope

- `external_source_instances.display_name` remains as a generated compatibility
  projection for existing consumers; no product form accepts an editable
  connection alias.
- `atlassian_sites.display_name` remains nullable provider-confirmed display
  evidence; local registration derives presentation from normalized domain and
  accepts no custom Site alias.
- Local bootstrap titles are deterministic URL-derived values. Existing remote
  metadata remains the source of remotely confirmed Jira summaries and
  Confluence titles.
- Selecting among multiple same-service access bindings for one Item during
  refresh remains deferred. Existing item/space access ownership is preserved,
  and an unbound local record may use the one unambiguous compatible binding.
- Additional owner observations may add a new Feature under this open
  incremental PRD; they do not reopen the passed FEAT-0062 or FEAT-0063 runs.

## Constraints

- PRD-0007 and PRD-0008 remain passed behavioral and data-contract baselines.
- The approved incremental planning artifact records sequencing and drift; it does not
  duplicate the durable Design Constitution.
- Current implementation and durable policy contracts remain implementation
  truth; pre-implementation sections in this PRD are historical context.
- Finding A-02 requires a `Foundation Contract` Feature followed by a
  `Fullstack Product` Feature because local Site identity, optional access
  ownership, compatible migration, and URL-Add composition change together.
- Affected surface lanes for Finding A-02:
  - Site identity and optional access-binding ownership;
  - compatible migration and current registered-connection preservation;
  - Local-only URL Add;
  - separate optional remote-access setup;
  - wide right-hand composition and narrow reading-order fallback.
- Tracked screenshots and fixtures use synthetic data.

## Acceptance Envelope

- Every confirmed observation has an explicit owning layer, propagation
  boundary, user-visible outcome, and regression surface.
- Finding A-02 is satisfied only when Local-only Add can create or reuse the
  URL-derived Site and register the Item or Space without Provider, connection
  name, Site-name input, local display-name input, connection reference, or
  capability.
- Optional remote-access setup is a separate explicit action and region. It may
  collect the real Provider and connection reference, but Local-only
  registration neither depends on nor creates a placeholder access binding.
- Existing registered Sites, Items, relations, access bindings, capability
  evidence, refresh history, and retained content survive the compatible
  migration.
- Current form submission, selection, keyboard, focus, disabled, validation,
  browse, Add, Item-detail, and explicit-refresh behavior remains usable.
- Required design, functional, and UX evidence passes for each later approved
  visible Feature.
- FEAT-0062 and FEAT-0063 executed sequentially; any later child Feature must
  declare its dependency order explicitly.

## Approved Features

- [FEAT-0062: Atlassian Local Site And Access-Binding Contract](../feature/feat-0062-atlassian-local-site-and-access-binding-contract.md)
  (`foundation`, `foundation-contract`): separate stable Site identity from optional
  external access ownership so local-only registration does not require a
  Provider, make normalized domain the Site identity while Jira/Confluence
  service belongs to Items, Spaces, and optional bindings, remove the
  user-managed Source Instance alias contract, derive the initial Site
  presentation from the URL, and preserve existing identity and refresh
  evidence through compatible migration.
- [FEAT-0063: Atlassian Local-Only Add And Access Setup](../feature/feat-0063-atlassian-local-only-add-and-access-setup.md)
  (`product`, `fullstack-product`): after the Foundation contract passes, make
  Local-only URL registration independent of Provider, connection name, Site
  name, local display name, and connection reference; derive a compact title
  from URL identity, present optional remote-access setup as a distinct
  right-hand action, and state remote readiness truthfully.

## Continuity Notes

- `2026-07-27`: created the draft Atlassian reconciliation boundary and
  recorded the owner's first observation about native select disclosure-arrow
  clearance.
- `2026-07-27`: recorded the Local-only URL Add question about existing
  connection reuse versus new connection setup as Finding A-02 pending owner
  confirmation.
- `2026-07-27`: clarified that current local-only registration structurally
  requires Site, Source Instance, and Provider kind but does not require a
  remote `config_ref` or current capability; retained the access-optional
  direction as an owner decision.
- `2026-07-27`: the owner confirmed that Provider/MCP access must not be
  mandatory for local-only registration and that new setup belongs to the right
  of the existing choice rather than below it. The connection display-name
  field remains under review.
- `2026-07-27`: the owner removed the need for a user-managed MCP connection
  name and Site display-name input. Access uses its real Provider/configuration
  identity, while local Site presentation is inferred from the URL/domain.
- `2026-07-27`: the owner removed connection-reference collection from
  Local-only Add. Reference binding remains available only in the separate
  optional remote-access setup task.
- `2026-07-27`: recorded the purpose and current fallback of the optional local
  Item/Space display name as Finding A-03 pending the owner's keep-or-remove
  decision.
- `2026-07-27`: the owner removed local display-name entry from initial Add.
  Bootstrap titles derive deterministically from URL identity and remain
  separate from later remote title/description evidence.
- `2026-07-27`: clarified that `service` means Jira or Confluence and must not
  split canonical Site identity. One normalized domain owns the Site, while
  service remains on Items, Spaces, and optional access bindings.
- `2026-07-27`: moved native-select disclosure geometry to PRD-0011 after the
  owner confirmed the same issue across Workstream and other selects.
- `2026-07-27`: the owner approved implementation through the current boundary.
  Locked explicit Site bindings, URL-only local registration, generated
  compatibility labels, and separate right-hand access setup for sequential
  FEAT-0062 and FEAT-0063 execution.
- `2026-07-27`: FEAT-0063 passed rendered evaluation at `1440`, `920`, `700`,
  and `320` widths after redundant Local-only explanatory copy was removed.
  This Atlassian PRD remains approved and open for later owner observations.
- `2026-08-02`: separated pre-implementation behavior from the approved
  contract, removed stale draft/review wording, and made the open incremental
  boundary explicit without changing scope.
