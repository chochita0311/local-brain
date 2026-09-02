# SPEC-0082: Atlassian Structure Reference Locator Foundation

## Metadata

- ID: `spec-0082`
- Status: `approved`
- Run ID: `run-20260901-92`
- Attempt: `1`
- Parent Feature: [FEAT-0082](../feature/feat-0082-atlassian-static-url-locator-contract.md)
- Parent PRD: [PRD-0016](../prd/prd-0016-atlassian-standard-url-recognition.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Surface Lane: `descriptor → Session projection/consumer adapters → owners`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-01`
- Updated: `2026-09-01`

## Source Set

- Human approval: preserve a semantic structure reference descriptor and
  allowlisted safe locator before approved queued FEAT-0083 persists anything.
- Parent PRD/Feature: PRD-0016 and FEAT-0082.
- Golden sources: passed FEAT-0046/0047/0073/0079/0080/0081, Product,
  Architecture, Privacy, Workspace/Session Activity, Atlassian Source Memory.
- Primary URL examples: Atlassian's
  [RapidBoard `projectKey`/`rapidView` link](https://developer.atlassian.com/server/jira/platform/developing-for-the-jira-project-centric-view/),
  [saved-filter `?filter=ID` example](https://support.atlassian.com/jira/kb/how-to-validate-all-filters-in-jira/),
  [Dashboard `view` with `selectPageId`](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-dashboards/),
  [Confluence `/wiki/spaces/{SPACE_KEY}/pages/{PAGE_ID}` examples](https://developer.atlassian.com/cloud/confluence/extension-point-locations/),
  [Confluence `viewpage.action?pageId=` example](https://support.atlassian.com/jira/kb/how-to-link-a-confluence-page-on-a-jira-cloud-issue-via-rest-api/),
  and [Confluence `/spaces/:spaceKey/...` module paths](https://developer.atlassian.com/platform/forge/manifest-reference/modules/confluence-space-page/).
  The exact matrix below is a reviewed static allowlist, not a claim of complete
  Atlassian URL coverage.
- Current code: `normalize_atlassian_url`, duplicate evidence/registration
  patterns, all-query-stripping Session projection, and Item-only Sync.

## Implementation Goal

- Implement one pure, exhaustive semantic locator descriptor and make the
  retained Session projection preserve only the safe identity needed by
  FEAT-0083, with no structure-reference DML or visible behavior.

## In-Scope Behavior

### Result Shape And Bounds

- Add one shared pure owner with `ATLASSIAN_LOCATOR_VERSION =
  "localbrain.atlassian-locator.v1"`. Its result contract is:
  - `kind`: `item`, `structure`, `site`, `unsupported`, or `unsafe`;
  - common recognized fields for `item`/`structure`/`site`: `service`
    (`jira|confluence`), stable `family`, `normalized_domain`,
    `canonical_base_url`, and `safe_locator_url`;
  - `item_identity_kind` and `item_identity` required only for `item`;
  - `reference_kind` and `reference_identity` required only for `structure`;
  - optional `container_hint` allowed only for `structure`;
  - no Item/reference identity or hint for `site`;
  - `reason` absent for recognized results, exactly `unsupported-url` for
    `unsupported`, and exactly `unsafe-url` for `unsafe`; no raw input, query,
    fragment, exception, or opaque value enters the result.
- Strip input once; maximum 8,000 Unicode code points. Accept only HTTP(S),
  reject credentials, invalid/empty host or port, IDNA failure, path controls,
  and an output over 8,000. Lowercase scheme and IDNA host, drop terminal host
  dot/default port, retain non-default port, use `/` for empty path, and discard
  fragment. Malformed percent escapes or invalid UTF-8 after percent decoding
  in an approved identity or hint path segment/query value are `unsafe` rather
  than a lossy decode.
- Path family tokens and approved query names are ASCII-case-insensitive;
  emitted query names have fixed canonical casing. Inspect at most 64 query
  pairs. Query parsing is ephemeral and never logs or returns raw values.
- Jira Project key: uppercase `[A-Z][A-Z0-9_]*`, `1..300`. Jira Issue key:
  uppercase `[A-Z][A-Z0-9_]*-[1-9][0-9]*`, total at most 300. Numeric identity:
  `1..300` ASCII digits with at least one nonzero, leading zeros removed.
- Confluence Space key is percent-decoded exactly once as strict UTF-8,
  NFKC-normalized, `1..300` code points, nonblank, not `.`/`..`, and contains no
  control, `/`, or `\`. Safe locator path output percent-encodes the normalized
  value exactly once.

### Precedence

- Precedence is: unsafe normalization → complete `/rest/` segment rejection →
  exact path Item → unambiguous allowlisted query Item → exact structure
  identity → valid Site-family root → unsupported.
- Path Item identity wins over every query. Query Item identity wins over Board,
  Filter, Dashboard, Project, JSM, or Space context. For example,
  `RapidBoard.jspa?rapidView=17&selectedIssue=PAY-4` is Item `PAY-4` and emits
  the canonical Issue locator.
- A present allowlisted identity/hint value with malformed percent or decoded
  UTF-8 is `unsafe` even beside an exact path Item; malformed non-allowlisted
  query material is neither inspected nor retained and does not defeat the path.
- Jira query Item identity uses only `selectedIssue`: exactly one occurrence
  with one valid Issue key on a path that independently matches an exact Jira
  Item/structure/site family in this matrix, or on the exact `/browse` root.
  Generic `issueKey` and `key` query names are not identity authority.
  Confluence query Page identity requires one exact `pageId` on an approved
  `viewpage.action` path.
- Repeated/conflicting/invalid identity parameters do not become identity. A
  path with its own valid Item/structure identity still wins; otherwise a valid
  recognized family may return only `site`.
- A missing, invalid, repeated, or conflicting but well-formed identity degrades
  to `site` only for a fallback explicitly listed below. Malformed percent or
  UTF-8 encoding is always `unsafe`, and an unlisted incomplete path is
  `unsupported`.

### Item Families

- `jira_issue` Item:
  - `/browse/{ISSUE_KEY}`; `/issues/{ISSUE_KEY}`;
  - `/jira/core/projects/{PROJECT}/issues/{ISSUE_KEY}`;
  - `/jira/software/c/projects/{PROJECT}/issues/{ISSUE_KEY}`;
  - `/jira/software/projects/{PROJECT}/issues/{ISSUE_KEY}`;
  - `/jira/servicedesk/projects/{PROJECT}/issues/{ISSUE_KEY}`;
  - `/servicedesk/customer/portal/{PORTAL_ID}/{ISSUE_KEY}`;
  - or the one approved query Item identity above.
  Emit `{base}/browse/{ISSUE_KEY}` and Item identity `jira_issue`/Issue key.
- For Confluence, `{context}` is the normalized input prefix `""`, `/wiki`, or
  `/confluence`; safe locators preserve that prefix rather than assuming one
  deployment context.
- `confluence_page` Item: with context prefix empty, `/wiki`, or
  `/confluence`, accept `/spaces/{SPACE}/pages/{PAGE_ID}` with optional title
  suffix, `/pages/{PAGE_ID}` with optional title suffix, and
  `/viewpage.action` or `/pages/viewpage.action` with the one valid `pageId`.
  A valid Space path emits
  `{base}{context}/spaces/{encoded-SPACE}/pages/{PAGE_ID}`. Otherwise emit
  `{base}{context}/pages/viewpage.action?pageId={PAGE_ID}`. Item identity is
  always `confluence_page`/canonical Page ID. A well-formed but invalid optional
  Space removes only the existing Item-container grouping adapter, not valid
  Page identity; malformed percent/UTF-8 encoding remains `unsafe`.

### Structure And Site Families

- `jira_project` structure:
  - `/projects/{PROJECT}`;
  - `/jira/core/projects/{PROJECT}`;
  - `/jira/software/c/projects/{PROJECT}`;
  - `/jira/software/projects/{PROJECT}`;
  - `/plugins/servlet/project-config/{PROJECT}`;
  - safe descendants not classified as a more specific Item/Board family.
  Identity and hint are the uppercase Project key. Emit
  `{base}/projects/{PROJECT}` with no query.
- `jira_board` structure:
  - `/secure/RapidBoard.jspa` requires exactly one positive decimal
    `rapidView`; identity is that canonical decimal. One exact valid
    `projectKey` may be retained only as `container_hint`;
  - `/jira/software/projects/{PROJECT}/boards/{BOARD_ID}` and
    `/jira/software/c/projects/{PROJECT}/boards/{BOARD_ID}` use canonical Board
    ID identity and Project hint.
  RapidBoard emits `{base}/secure/RapidBoard.jspa?rapidView={ID}` plus
  `&projectKey={PROJECT}` only when the hint is valid, in that fixed order.
  Modern Board emits `{base}/jira/software/projects/{PROJECT}/boards/{ID}`.
  RapidBoard without one valid `rapidView`, and a modern
  `/jira/software[/c]/projects/{valid-PROJECT}/boards` root with a missing or
  well-formed invalid Board ID, are `site`/`jira_board`, not structure.
- `jira_filter` structure: on `/issues`, `/secure/IssueNavigator.jspa`, or
  `/secure/ManageFilters.jspa`, exactly one positive decimal `filter`,
  `requestId`, or `filterId` yields identity ID and canonical
  `{base}/issues?filter={ID}`. A family root without it is `site`/`jira_filter`.
- `jira_dashboard` structure: `/secure/Dashboard.jspa` with exactly one positive
  decimal `selectPageId` yields identity ID and canonical
  `{base}/secure/Dashboard.jspa?selectPageId={ID}`. Without it, the result is
  `site`/`jira_dashboard`.
- `jira_service_portal` structure:
  `/servicedesk/customer/portal/{PORTAL_ID}` and descendants not classified as
  an Issue use canonical positive portal ID and no container hint. Portal roots
  without an ID are `site`/`jira_service_portal`.
- `jira_service_project` structure:
  `/jira/servicedesk/projects/{PROJECT}` and non-Item descendants use uppercase
  Project identity/hint and canonical
  `{base}/jira/servicedesk/projects/{PROJECT}`.
- `confluence_space` structure: with context prefix empty, `/wiki`, or
  `/confluence`, `/spaces/{SPACE}` and `/display/{SPACE}` plus non-Page
  descendants use the same normalized Space identity/hint and canonical
  `{base}{context}/spaces/{encoded-SPACE}`. A display title never becomes Page
  identity; it only provides evidence of that Space reference.
- A listed `site` fallback emits one exact query-free family root and no result
  identity or hint:
  - RapidBoard: `{base}/secure/RapidBoard.jspa`;
  - modern Board with a valid Project path segment:
    `{base}/jira/software/projects/{PROJECT}/boards`;
  - Filter: `{base}/issues`;
  - Dashboard: `{base}/secure/Dashboard.jspa`;
  - JSM portal: `{base}/servicedesk/customer/portal`.
  This covers only the missing, invalid, repeated, or conflicting but
  well-formed identity cases explicitly admitted above. Incomplete Jira
  `/projects`, JSM `/jira/servicedesk/projects`, Confluence `{context}/spaces`,
  `{context}/display`, or `{context}/pages` paths are `unsupported`, as are
  attachment, blog, whiteboard, database, embed, short/tiny, and arbitrary
  plugin families.
- Generic Jira/Confluence home, arbitrary plugin, attachment, blog, whiteboard,
  database, embed, short/tiny, REST/API, key-only, and generic HTTP(S) forms are
  unsupported unless one exact rule above applies.

### Safe Query And Semantic Session Projection

- Safe locator query is empty except:
  - RapidBoard: canonical `rapidView`, then optional validated `projectKey` hint;
  - Filter: canonical `filter`;
  - Dashboard: canonical `selectPageId`;
  - Confluence Page without a valid Space path: canonical `pageId` on
    `{context}/pages/viewpage.action`.
  Jira `selectedIssue` canonicalizes to query-free `/browse/{ISSUE_KEY}`; a
  Confluence Page with a valid Space path remains query-free. Drop JQL, mode,
  view, selected tab, filter text, comments, tokens, and all other query.
- The semantic descriptor identity tuple is one exact JSON array:
  - Item: `[locator_version, normalized_domain, service, "item",
    item_identity_kind, item_identity]`;
  - Structure: `[locator_version, normalized_domain, service, "structure",
    reference_kind, reference_identity]`;
  - Site: `[locator_version, normalized_domain, service, "site", family]`.
  `safe_locator_url` and `container_hint` do not enter the tuple.
- Serialize that array as UTF-8 JSON with non-ASCII characters unescaped and
  compact separators `,`/`:`. For retained Session `target_kind=url`,
  `target_key` is `url:` plus the lowercase hexadecimal SHA-256 of those exact
  bytes, not a hash of the whole URL. Generic unsupported safe URLs keep their
  existing whole-safe-URL hash.
- Recognized structure/site Session rows retain `safe_locator_url` in
  `normalized_url` and a bounded safe family/identity display in
  `observed_identity`; they create no Atlassian FK. Equivalent reference URL
  variants group under one target key while distinct identity values remain
  separate. RapidBoard's canonical locator preserves the optional Project hint
  so FEAT-0083 can reparse it without making the hint identity.
- Recognized unconfigured Item rows use the semantic Item key and canonical
  locator. Configured Item promotion resolves normalized-domain Site/service,
  then exact Site-scoped URL owner, then one unambiguous Item identity within
  that Site/service. Never reuse a global key/ID from another domain.

### Consumer Admission, Versioning, And I/O

- `atlassian_evidence.py` consumes only `item`; `structure`/`site` return its
  existing unsupported-locator outcome and cause no Sync DML/report change.
- Safe-query minimization governs the descriptor result, Session projection,
  and evidence-Sync `normalized_url`/Item URL authority; it does not erase
  source provenance. An authoritative Local Context Document sighting keeps its
  exact bounded source spelling, including arbitrary query, in
  `atlassian_item_evidence.observed_url`, while evidence Sync uses the
  descriptor's canonical safe locator for normalization and Item URL matching.
  A Session-derived sighting has only the retained safe locator and stores that
  same value as `observed_url` without claiming that it is the unavailable
  original spelling. Explicit manual Add is excluded from this minimization:
  it uses the descriptor only for admission and preserves FEAT-0079's original
  exact-normalized-input URL/alias non-merge semantics.
- `atlassian_registration.py` delegates parsing but retains the passed Add
  subset: Items plus direct `jira_project` and `confluence_space` registration.
  Board/Filter/Dashboard/JSM references remain unsupported by Add. Existing
  atomicity, original normalized input URL/alias ownership, non-merge, and
  return behavior remain.
- FEAT-0081 Item container grouping remains an Item adapter derived from exact
  Issue key or Page `/spaces/{SPACE}/pages/{ID}` context. It does not consume a
  structure-reference descriptor or change `space_id`.
- Set `REFERENCE_EXTRACTOR_VERSION` to
  `localbrain.session-reference.v3` and `EVIDENCE_EXTRACTOR_VERSION` to
  `localbrain.atlassian-evidence.v3`. Normal Session reconciliation and explicit
  Document Item-evidence Sync re-evaluate stale versions once; existing caps,
  partial/error retention, source transactions, and cleanup owners remain.
- Same-version unchanged repeats perform no timestamp-only or identity writes.
  No startup sweep, route, action, schema, value, report, receipt, or screen is
  added.
- The shared descriptor imports no SQLite/filesystem/external owner. Adapters
  use only their passed bounded local SQLite paths and never call Provider,
  capability, runner, model, connected discovery, Refresh, or network code.

## Out-Of-Scope Behavior

- Durable structure-reference schema/rows/evidence/lifecycle or new Site
  creation outside the already passed explicit Add Project/Space subset;
  approved queued FEAT-0083 owns the new product authority after this Feature
  passes.
- Sync report/receipt, Explorer/Search/Connections/Refresh, route, template,
  Design Constitution, or visible-copy changes.
- Persisting `container_hint` as containment, creating Space/Project/Item, or
  assigning `space_id` from a structure descriptor.
- Arbitrary query/JQL retention, Provider inference, remote/model work, or
  generic URL classification as Atlassian.

## Affected Surfaces

- shared static Atlassian locator module
- `src/localbrain/atlassian_evidence.py`
- `src/localbrain/atlassian_registration.py`
- `src/localbrain/session_references.py`
- `src/localbrain/ingest/common.py`
- focused locator/evidence/registration/reference/Sync tests
- Product, Architecture, Privacy, Workspace/Session Activity, Atlassian Source
  Memory, plans and generated artifacts

## Surface Lanes

- Descriptor first: result shape, taxonomy, precedence, safe query and version.
- Consumer projection second: semantic Session key, Item-only evidence,
  unchanged explicit Add subset, versions, and zero-DML proof for Session and
  evidence consumers.
- Durable owners with final contract: foundation law plus approved queued
  FEAT-0083 direction, never a claim of current product implementation.

## State And Interaction Contract

- No new screen, route, request, redirect, form, focus, history, scroll, copy,
  report, or receipt contract. Existing Session Related Context continues to
  render its generic URL row, but after version repair that row may deduplicate
  by semantic target and use the canonical safe locator as its destination.
- Existing Sync/Add states keep passed consequences. Structure/site descriptors
  remain generic Session evidence rather than Atlassian structure-reference UI
  until FEAT-0083.

## Data And Contract Assumptions

- Semantic locator descriptor and Session target key are derived/rebuildable,
  not durable Atlassian structure-reference identity.
- Container hint is excluded from identity and never confirms containment.
- Safe locator is a privacy-minimized navigation/reparse projection, not raw
  observed spelling or remote confirmation.
- FEAT-0083 will own stable structure-reference persistence/evidence separately
  from Session/Document text, Item, Space, access, and remote state.

## Contract Surfaces

- Producer: one pure bounded semantic descriptor and safe locator.
- Consumers: explicit adapter allowlists, semantic Session grouping, no
  structure/site persistence.
- Generated artifacts: plan catalog and data-model audit digest only when owner
  sources change; no schema/value artifact.
- Source-of-truth owners: Product, Architecture, Privacy, Workspace/Session
  Activity, Atlassian Source Memory, and this approved Attempt.
- Stale-assumption check: Site-only collapse, whole-URL target identity, all-
  query stripping, global Item-key reuse, parser-as-persistence authority.

## Required Evaluators

- Contract: taxonomy, identity, precedence, safe query, target grouping,
  versions, adapters, owner parity, zero hidden I/O.
- Design: not required; no visible surface.
- Functional: exhaustive fixtures, DML absence, repair/idempotency, focused/full
  regressions.
- UX heuristic: not required.

## Acceptance Mapping

- Exact descriptor → pure result module plus family matrix tests.
- RapidBoard preservation → `rapidView`/`projectKey` canonical locator, identity
  and target-key fixtures.
- Privacy → per-family query allowlist and no raw query/JQL assertions.
- Identity precedence → path/query Item versus structure/site conflict fixtures.
- Session preservation → semantic target-key and safe-locator reconciliation.
- Consumer separation → Item-only evidence/Sync and unchanged Add DML tests.
- Version repair → literal versions, one stale repair, zero-write repeat.
- Zero hidden I/O → imports/call graph and fail-fast external-path mocks.

## Evaluation Focus

- Look for Board/filter/dashboard collapse, hint entering identity, arbitrary
  query leakage, invalid query becoming structure, cross-domain reuse,
  unexpected structure/site DML outside the passed explicit Add subset, or
  parser-triggered external/model work.

## Open Blockers

- None. FEAT-0083 is approved but intentionally dependency-queued.

## Continuity Notes

- `2026-09-01`: approved Attempt 1.
- `2026-09-01`: corrected to preserve semantic structure identity and canonical
  allowlisted query after owner rejected the lossy Site-only projection.
