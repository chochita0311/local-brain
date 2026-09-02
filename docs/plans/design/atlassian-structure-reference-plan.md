# Atlassian Structure Reference Design Plan

## Metadata

- Status: `complete`
- Parent boundary: [PRD-0016](../prd/prd-0016-atlassian-standard-url-recognition.md), `passed`
- Completed foundation: [FEAT-0082](../feature/feat-0082-atlassian-static-url-locator-contract.md), `passed`
- Foundation execution: [SPEC-0082](../spec/spec-0082-atlassian-static-url-locator-contract.md) / [RUN-92](../run/run-20260901-92-atlassian-static-url-locator-contract.md), Attempt 1, Contract and Functional `PASS`
- Completed product: [FEAT-0083](../feature/feat-0083-atlassian-structure-reference-sync-and-explorer.md), `passed`
- Product execution: [SPEC-0083 Attempt 1](../spec/spec-0083-atlassian-structure-reference-sync-and-explorer.md) / [RUN-93](../run/run-20260901-93-atlassian-structure-reference-sync-and-explorer.md), Contract, Design, Functional, and UX `PASS`
- Prior completed track: [Atlassian Site-First Hierarchy Design Plan](atlassian-site-first-hierarchy-plan.md)
- Created: `2026-09-01`
- Updated: `2026-09-01`
- Screen alignment: `extend`

## Purpose

- Reconcile Jira Project/Board/Filter/Dashboard/JSM and Confluence Space URLs
  observed by local evidence Sync with the completed Site-first Explorer
  without presenting an observed URL as an Item or confirmed/persisted
  Project/Space containment.
- Sequence the pure locator/privacy foundation before any product identity or
  presentation work so the hierarchy, list, preview, counts, action
  consequences, and responsive states consume one approved contract.

## Plan Type

- Information-hierarchy consistency.
- Interaction and responsive consistency.
- Provenance and terminology reconciliation.

## Baseline

### Audited Sources

- [Completed Site-first plan](atlassian-site-first-hierarchy-plan.md) and its
  passed FEAT-0081/RUN-91 hierarchy, state, and four-width evidence.
- [PRD-0016](../prd/prd-0016-atlassian-standard-url-recognition.md), the
  passed sequential foundation/product boundary.
- [FEAT-0082](../feature/feat-0082-atlassian-static-url-locator-contract.md),
  [SPEC-0082](../spec/spec-0082-atlassian-static-url-locator-contract.md), and
  [RUN-92](../run/run-20260901-92-atlassian-static-url-locator-contract.md):
  pure locator taxonomy, privacy-safe Session projection, and explicit
  consumer admission with no schema, persistence, report, or visible change.
- [FEAT-0083](../feature/feat-0083-atlassian-structure-reference-sync-and-explorer.md),
  [SPEC-0083](../spec/spec-0083-atlassian-structure-reference-sync-and-explorer.md),
  and [RUN-93](../run/run-20260901-93-atlassian-structure-reference-sync-and-explorer.md):
  the completed product loop after the FEAT-0082 dependency gate passed.
- Current Site-first Explorer hierarchy, list, preview, Sync report, Add,
  Connections, Refresh, and shared Search consumers.
- Pre-FEAT-0083 strict Sync baseline, which admitted Jira Issue and Confluence
  Page URLs but reported structure families as unsupported locators.
- Current one-URL Add boundary, which can explicitly register a Jira Project or
  Confluence Space as persisted local containment.

### Constitution And Owner References

- [Design Constitution](../../policies/design/design-constitution.md)
- [Design Evaluation](../../policies/design/design-evaluation.md)
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md)
- [Product](../../policies/project/product.md)
- [Atlassian Source Memory](../../policies/project/data-model/atlassian-source-memory.md)

### Target Direction For This Track

- The target composition is `domain → URL-derived group → 구조 참조 row →
  구조 참조 preview`.
- A structure reference is locally observed URL evidence, not a persisted
  Space, confirmed remote identity, access binding, or Refresh result.
- FEAT-0082 supplies only the deterministic `item`/`structure`/`site`
  descriptor and privacy-minimized Session projection. It creates no durable
  structure reference and changes no screen or Sync report.
- FEAT-0083 owns durable structure-reference identity, evidence, schema, Sync
  result, Search, and Explorer projection. SPEC-0083/RUN-93 completed that
  approved boundary after the FEAT-0082 foundation passed.

## Scope

- Plan the approved FEAT-0083 structure-reference identity and read model for
  Jira Project, Board, Filter, Dashboard, service portal/project, and
  Confluence Space descriptors classified by FEAT-0082.
- Preserve deterministic service, locator family, normalized domain,
  privacy-minimized safe locator URL, stable reference kind/identity, optional
  non-authoritative Project/Space container hint, and source evidence.
- Project structure references beneath the existing normalized-domain Site and
  existing URL-derived or honestly unassigned child kinds.
- Render each admitted structure reference as one eligible center-list row with
  one read-first preview and ordinary full-detail/no-script destination.
- Keep service and URL-basis provenance visible in hierarchy, row, preview,
  direct detail, Search, Sync result, and live feedback where those consumers
  are owned by FEAT-0083.
- Keep link/document and structure-reference counts separate in aggregate,
  source-level, hierarchy/list, empty, and announcement copy.
- Define deterministic repeat, collision, source-removal, direct-entry,
  archived, filtered, missing, and unsupported states.
- Reconcile the boundary with Add, Sync, Refresh, and Connections without
  merging their prerequisites, progress, outcomes, or recovery.
- Validate the native Explorer composition at `1440`, `920`, `700`, and `320`.
- Implementation completed through SPEC-0083/RUN-93; the passed FEAT-0082
  dependency remains closed and is not reopened.

## Non-Goals

- Automatically creating or mutating `atlassian_spaces`, writing `space_id`,
  or claiming remote Project/Space confirmation from source evidence.
- Treating a `site` descriptor or hierarchy-only zero-count node as successful
  URL preservation.
- Adding Service as a hierarchy parent, adding Board as another hierarchy
  depth, or nesting Jira issues or Confluence Pages under a structure reference.
- Remote reads, capability inspection, access setup, connected discovery,
  Refresh execution, model work, title inference, or content inference during
  local Sync or Browse.
- New shell, query mode, action family, dialog family, design tokens, or private
  breakpoint.
- Rewriting the completed Site-first design plan or its historical evidence.
- Implementing code, schema, owner-policy, or constitution changes in this
  design-plan task.
- Expanding FEAT-0082 beyond its approved pure parser, Session projection,
  versioning, and existing-consumer adapter boundary.

## Invariants

- `All`, `Jira`, and `Wiki` remain reversible peer scopes above the hierarchy;
  normalized Site domain remains the first hierarchy node.
- A visible structure-reference group is backed by at least one eligible list
  row. Site, group, and list counts use the same population; newly invented
  zero-count branches are not allowed.
- URL-derived grouping stays one child depth and keeps the existing non-color
  cue: `Jira · URL 기준` or `Wiki · URL 기준` in All and `URL 기준` in a
  service-only scope.
- Durable identity is Site domain + service + `reference_kind` +
  `reference_identity`. Locator spelling, URL alias, and `container_hint` do not
  enter that identity; conflicting hints place the stable reference under
  `소속 미확인` rather than choosing a Project/Space label.
- Jira Project, Board, Filter, Dashboard, service portal/project, and Wiki Space
  references remain distinguishable in row and detail copy without representing
  any of them as a Jira Issue or Wiki document.
- A standard RapidBoard reference uses one bounded, canonical `rapidView`
  identity for reference deduplication. An allowlisted `projectKey` is only a
  non-authoritative URL-derived grouping hint; it never becomes persisted
  Project/Space containment. Raw query text and unrelated parameters are never
  retained or rendered.
- Persisted Project/Space and structure reference remain separate authorities.
  Equal labels remain visibly separate; FEAT-0083 does not convert or merge
  them.
- Structure references do not inherit remote freshness, content coverage,
  Refresh eligibility, or connected readiness merely because current Item rows
  expose those axes.
- Under passed FEAT-0083, a `site` descriptor may be counted only in bounded
  Sync reporting; it never produces a hierarchy child, list row, preview,
  Search result, or detail route.
- Sync remains local persisted-evidence reconciliation. Add remains the
  explicit one-URL local registration path. Connections remains optional access
  and discovery. Refresh remains explicit remote maintenance.
- Existing query, filter, selection, focus, history, scroll, modal ownership,
  named Sync fragments, and no-script fallbacks remain stable while FEAT-0083
  adds the approved reference states.
- Wide, compact, and narrow layouts retain current semantic tokens, reading
  order, focus order, touch geometry, containment, and zero horizontal overflow.

## Resolved Findings And Guardrails

### F-01: Pre-Implementation Sync Preserved No Navigable Structure Reference — Resolved

- Structure-family candidates were reported as unsupported, so a user could see
  that Sync skipped a URL but could not revisit that exact reference from the
  Explorer.
- FEAT-0083 resolved the gap with a real selectable reference identity rather
  than a presentation-only node.

### F-02: Site And Group-Only States Break Explorer Count Meaning — Resolved

- The completed family makes hierarchy counts equal adjacent list membership.
  A new Site or URL-derived group with count zero would advertise a destination
  while preserving no selectable URL.
- Existing selected-zero states are bounded exceptions for already known
  persisted or canonical structures after filtering, not admission patterns for
  a newly observed candidate.

### F-03: Automatic Persisted Space Would Cross Authority — Resolved

- One-URL Add may register persisted Project/Space containment because the user
  explicitly chose that task. Sync evidence only proves that a URL was observed.
- Reusing the Add mutation silently would make source evidence appear to own
  containment and could imply Connections or Refresh scope that never ran.

### F-04: Pre-Implementation Item Presentation Could Not Name The New Meaning Honestly — Resolved

- Prior rows and counts assumed Jira link, Wiki document, or mixed
  link/document identity. A Jira Project/Board/Filter/Dashboard/JSM or Wiki
  Space reference is not a Jira Issue or Confluence Page and must not borrow
  their detail or freshness semantics.
- Aggregate copy, row subtype, preview authority, Search result context, and
  live Sync feedback now use one explicit structure-reference vocabulary.

### F-05: Add And Existing-Space Collision Requires Product Ownership — Resolved

- The design can keep equal persisted and URL-derived labels visually distinct,
  but identity reuse, later Add coexistence, evidence retention, and source
  removal cannot be implemented safely in templates.
- FEAT-0083 locked those lifecycle and deduplication rules in its executable
  contract before rendering a selectable row. FEAT-0082 remains the URL-only
  classifier and does not own this product authority.

### F-06: The Product Feature Was Approved Behind A Foundation Gate — Resolved

- FEAT-0083 already selects durable, selectable structure references instead of
  report-only Site recognition or a zero-count Site branch.
- FEAT-0082 passed first. FEAT-0083's executable schema, evidence lifecycle,
  route/read model, and interaction details then passed SPEC-0083/RUN-93 and
  all four independent evaluators.

## Target Composition

### Wide Wireframe

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ Atlassian                                          [Sync] [Add] [More] │
│ Local evidence Sync status                                             │
│ [All] [Jira] [Wiki]                             링크/문서 · 구조 참조 │
│ [키, 제목, 문장 또는 Atlassian URL ____________________] [Search] │
├──────────────────┬──────────────────────────┬─────────────────────────────┤
│ 모든 도메인   1 │ PAYMENTS                 │ STRUCTURE REFERENCE         │
│  jira.test     1 │ Jira Project 참조        │ PAYMENTS                    │
│   PAYMENTS     1 │ jira.test · PAYMENTS     │ Jira Project 참조           │
│   Jira · URL 기준│ URL 기준 · 구조 참조    │ jira.test · URL 기준         │
│                  │                          │ safe locator URL            │
│                  │                          │ Session/Local Context evidence│
│                  │                          │ 원격 조회·Project/Space 미등록│
└──────────────────┴──────────────────────────┴─────────────────────────────┘
```

- Jira Project URL: child label uses the deterministic Project key; row label
  is `Jira Project 참조`.
- Jira Board URL: row label is `Jira 보드 참조`. A deterministic Project key
  in the approved URL shape owns the URL-derived child; a board locator without
  one remains under `소속 미확인` rather than inferring a Project or board name.
- Confluence Space URL: child label uses the deterministic Space key; row label
  is `Wiki Space 참조`.
- Jira RapidBoard URL: one valid derived `rapidView` value distinguishes the
  reference. A valid derived `projectKey` may select the `PAYMENTS` URL-derived
  group but is not part of the remote-confirmation claim; absent or ambiguous
  board identity is not admitted as a selectable structure reference.
- Jira Filter, Dashboard, and service portal references without a deterministic
  Project hint remain under `소속 미확인`; they do not create an extra
  hierarchy depth. A Jira service Project reference may use its explicit
  Project key as the URL-derived grouping hint.
- The preview leads with the observed family and privacy-minimized safe locator
  URL, then local source evidence. It does not show remote facts, remote
  freshness, Space coverage, or Refresh readiness as if they had been checked.

### Copy And Count Contract

| Surface | Target copy |
| --- | --- |
| Hierarchy child | `PAYMENTS` plus `Jira · URL 기준`; `TEAM` plus `Wiki · URL 기준` |
| List row type | `Jira Project 참조`, `Jira 보드 참조`, `Jira 필터 참조`, `Jira 대시보드 참조`, `Jira 서비스 포털 참조`, `Jira 서비스 Project 참조`, or `Wiki Space 참조` |
| Row kind and provenance | `구조 참조` plus `URL 기준 · Local evidence`; do not reuse Item freshness as a status |
| Only-reference result count | `구조 참조 1` |
| Mixed result count | `링크/문서 2 · 구조 참조 1` |
| Mixed hierarchy count | the same scoped split, such as `링크 2 · 구조 참조 1`; omit a zero category and allow the pair to wrap rather than collapsing to an unlabeled total |
| Sync aggregate | `새 구조 참조 1` and `기존 구조 참조 0`, separate from link/document counts |
| `site` report | `도메인/서비스만 확인 1`; no success row or hierarchy count |
| Preview authority | `Session/Local Context에서 URL 구조만 확인했습니다. Jira 링크/Wiki 문서·등록된 Project/Space·원격 조회 결과가 아닙니다.` |
| Unsupported locator | `지원하지 않는 Atlassian URL`; no hierarchy or list mutation |

### Action Consequence Contract

| Entry point | Preserved meaning | Structure-reference consequence |
| --- | --- | --- |
| `Sync` | zero-input reconciliation of already persisted eligible Session/Local Context evidence; local only | FEAT-0083 creates/reuses evidence-owned references and reports them separately; it never performs Add, Refresh, or connection setup |
| `Add` | explicit one-URL local registration | retains its approved Issue/Page/Project/Space admission and persisted-containment semantics; it does not become the automatic path for Sync evidence |
| `Refresh` | explicit remote maintenance for already eligible configured inventory | excludes an evidence-only structure reference until a separate approved authority makes it remotely refreshable |
| `Connections` | optional access and connected-discovery setup | does not appear complete or required merely because a structure URL was recognized |

- Action order remains `Sync → Add → More`, with `Refresh preview` and
  `Connections` in the existing overflow. No fifth primary action is added.
- Busy, complete, repeat, partial, failed, and patch-failure feedback remains in
  the existing stable Sync region; structure-reference counts are additive and
  do not rename or absorb link/document counts.
- Enhanced completion patches only the established named Sync/Explorer
  fragments and preserves exact query, selection, history, focus, list/detail
  scroll, and any open Add/detail modal. No-script Sync keeps the existing
  POST→303 bounded receipt and reaches the same server-authored row/detail.

### Responsive Composition

| Width | Hierarchy | List | Detail | Actions and containment |
| --- | --- | --- | --- | --- |
| `1440` | existing persistent Site-first rail | existing bounded center list with a structure-reference row | existing adjacent read-first preview | no new action, rail, or modal; long key and count copy wrap inside owners |
| `920` | existing compact hierarchy disclosure before results | primary in-flow list | existing right drawer when selected | current equal Sync/Add/More row and one modal owner remain |
| `700` | compact disclosure before list | list-first document flow | existing full-width sheet below the current sticky header | current two-action row plus More, 40-pixel targets, no outer overflow |
| `320` | same compact disclosure; long child labels and cues wrap | one-column rows; subtype and provenance wrap before statuses | full-width sheet or full-detail fallback | no horizontal overflow, 40-pixel targets, safe locator URL wraps anywhere |

- Page DOM and keyboard order remains heading/actions → Sync status →
  All/Jira/Wiki → exact search/filters → hierarchy → list → selected
  preview. Within the three-region family, visual and reading order remains
  hierarchy → list → preview at `1440`. The existing server-authored tree
  projection may appear in wide rail and compact disclosure owners, but exactly
  one copy is visible and focusable at each breakpoint.
- Selecting a reference uses the existing history/focus/scroll lifecycle and
  normal server-authored destination. Closing a compact preview restores its
  initiating row when present and otherwise the results heading; no-script
  navigation reaches the full detail directly.

## State Matrix

| State | Required presentation |
| --- | --- |
| FEAT-0082 only | existing Sync and Explorer remain unchanged; `structure`/`site` descriptors create no Site, group, row, report category, or preview |
| only one supported structure URL | one Site, one derived or unassigned child, one list row, optional selected preview; every count is `1` |
| mixed Issue/Page and structure references | one shared Site where domains match; ordinary and structure-reference counts remain separate |
| repeat Sync | stable row identity, `기존 구조 참조`, no duplicate Site/group/row/evidence |
| same label as persisted Space | two distinguishable children; never silent conversion or merge |
| supported board without Project key | `소속 미확인` plus `Jira 보드 참조`; no inferred Project |
| two RapidBoard URLs with distinct `rapidView` values | two stable board-reference rows even if `projectKey` and display group match; only the canonical allowlisted query projection is retained, never raw spelling or arbitrary parameters |
| repeated, missing, or invalid `rapidView` identity | bounded recognized-`site` report when the RapidBoard family remains valid; no reference, group, or selectable zero-count row |
| Jira Filter/Dashboard/JSM reference | explicit family label; deterministic Project hint group when allowed, otherwise `소속 미확인`; no false Item or Project |
| recognized `site` family root | separately bounded Sync count/reason only; no durable reference or Explorer branch |
| unsupported or ambiguous locator | bounded Sync reason and no hierarchy/list mutation |
| source unavailable or failed | retain the last-known reference with honest unavailable state; do not fabricate freshness or destructively clean identity |
| last supporting evidence removed | stable identity and safe URL remain, while zero retained evidence derives `archived`; no template-side cleanup or silent Space merge |
| filtered or archived reference | Item-only filters exclude references; a known filtered reference is bounded out-of-scope, while archived identity remains direct-only and reusable |
| missing direct reference | bounded missing preview/full detail without changing the current scope or widening the result population |

## Planned Work

### Batch 1: FEAT-0082 Pure Locator Foundation

- Goal: complete the one pure, versioned static locator taxonomy and query-safe
  Session projection that FEAT-0083 can consume without duplicating URL rules.
- Why this grouping: deterministic service, family, normalized domain, safe
  locator, optional container hint, privacy, and identity precedence must be
  settled before the product Spec implements persistence or visibility.
- Guardrails: no schema/value change; no Site, Space, Item, structure-reference,
  evidence, report, receipt, hierarchy, Search, Connections, or Explorer
  consequence beyond passed behavior; no external/model work. `structure` and
  `site` descriptors are derived classification, not persistence authority.
- Targets: [FEAT-0082](../feature/feat-0082-atlassian-static-url-locator-contract.md),
  [SPEC-0082](../spec/spec-0082-atlassian-static-url-locator-contract.md), and
  [RUN-92](../run/run-20260901-92-atlassian-static-url-locator-contract.md);
  shared parser, current consumer adapters, canonical allowlisted Session
  reference projection, semantic target grouping, extractor versions, and
  their approved durable owners.
- Validation: exact positive/negative family matrix, unsafe and ambiguous-query
  handling, path/query identity precedence, normalized bounds, query/fragment
  minimization, bounded canonical RapidBoard `rapidView` identity and optional
  `projectKey` hint, Site-scoped configured-Item reuse, version
  repair/idempotency, zero structure/site DML, zero hidden I/O, and unchanged
  Sync/Add/Explorer UI regressions.
- Exit gate: complete. FEAT-0082 passed Contract and Functional evaluation with
  a stable derived locator contract and no product consequence before
  FEAT-0083 entered SPEC-0083/RUN-93.

### Batch 2: FEAT-0083 Executable Contract And Identity

- Goal: translate the approved product Feature into an executable Spec and one
  durable structure-reference identity/evidence/schema and Sync contract.
- Why this grouping: admission allowlist, stable identity, evidence ownership,
  source cleanup, deduplication, Add collision, report units, list eligibility,
  and direct-detail identity must agree before visible implementation starts.
- Guardrails: the prerequisite was enforced: SPEC-0083/RUN-93 were created only
  after FEAT-0082 passed. FEAT-0082 stays unchanged; `site` results receive
  report-only treatment and never a durable reference or zero-count Explorer
  branch. Structure identity stays separate from Item, Space, container hint,
  locator alias, and source evidence.
- Targets: [FEAT-0083](../feature/feat-0083-atlassian-structure-reference-sync-and-explorer.md),
  [SPEC-0083](../spec/spec-0083-atlassian-structure-reference-sync-and-explorer.md),
  [RUN-93](../run/run-20260901-93-atlassian-structure-reference-sync-and-explorer.md),
  stable reference/alias/evidence owners, fresh/compatible schema and value
  contracts, local Sync candidate/report/receipt units, Browse/detail/Search
  read models, and explicit filter eligibility.
- Validation: empty-database admission; same-source and later-source reuse;
  source rollback/removal; equal-label Site/Space collision; optional-container-
  hint versus persisted containment; strict Add coexistence without conversion;
  distinct/repeated/ambiguous RapidBoard identities; unsupported family
  handling; no `space_id`; no external/model work; and deterministic
  fresh/repeat graphs.
- Exit gate: complete. The FEAT-0083 contract produces one stable durable
  reference and separate evidence/report outcomes without calling it an Item,
  persisted Project/Space, freshness target, connection, or remotely confirmed
  object.

### Batch 3: FEAT-0083 Sync And Explorer Presentation

- Goal: expose approved structure references through separate Sync feedback and
  the existing Site-first hierarchy, center list, read-first preview/full
  detail, and shared exact Search surface.
- Why this grouping: hierarchy group, row eligibility, selection, preview,
  aggregate/source counts, terminology, responsive behavior, and no-script
  fallback form one visible Explorer lifecycle.
- Guardrails: reuse current Explorer, action, status, focus, history, scroll,
  drawer/sheet, and no-script families; no new modal or hierarchy depth; do not
  imply persisted Space, remote facts, Refresh readiness, or connected access.
- Targets: approved SPEC-0083/RUN-93; Sync aggregate/source/live copy and named
  fragments; approved Browse/Search read-model consumers; Explorer hierarchy,
  list, preview, and full-detail templates; only shared semantic CSS/controller
  changes required by approved states.
- Validation: the State Matrix above; keyboard and no-script direct entry; deep
  and rapid selection; back/forward; exact list/detail scroll preservation;
  Sync fragment replacement; modal-open completion deferral; long and equal
  labels; only-reference and mixed counts; missing/error/unsupported states;
  Add/Sync/Refresh/Connections separation; Chrome at `1440`, `920`, `700`, and
  `320`; accessibility tree, contrast, touch geometry, console, and zero
  horizontal overflow.
- Exit gate: complete. A supported structure-only Sync produces one honest
  navigable reference row and preview at every supported width without changing
  the meaning or behavior of persisted Project/Space, ordinary link/document,
  or remote actions.

### Batch 4: Durable Owner And Plan Closure

- Goal: promote only proven stable structure-reference rules to their durable
  owners and close this design track.
- Why this grouping: the Design Constitution and Product/Source Memory should
  record validated law, not speculative presentation or unverified
  implementation choices.
- Guardrails: preserve the completed Site-first plan as history; do not rewrite
  passed FEAT-0081 evidence; update generated indexes only through their owning
  workflow.
- Targets: Product, Architecture, Privacy, Source Memory, Design Constitution
  and governance entry, plan lifecycle owners, and generated catalog after
  FEAT-0082/0083 pass.
- Validation: contract/design/functional/UX evaluator parity, owner-doc checks,
  generated artifact checks, privacy check, focused/full regression, and final
  four-width browser evidence.
- Exit gate: complete. PRD-0016 owns the durable outcome, FEAT-0082 and
  FEAT-0083 retain their execution evidence, and no unresolved design-law drift
  remains.

## Completion Evidence

- Contract focused verification passed `162/162`, the final Atlassian/UI
  functional matrix passed `193/193`, UI contracts passed `41/41`, and the full
  repository suite passed `480/480`.
- Chrome verified the reference-only and mixed Explorer at `1440`, `920`,
  `700`, and `320`, including exact breakpoint crossings, no-script Sync and
  direct detail, focus/history/modal continuity, 40-pixel targets, long-identity
  containment, zero console errors, and Lighthouse Accessibility `100`.
- Contract, Design, Functional, and UX evaluations passed with complete evidence
  coverage. Privacy, schema/data-model, generated-owner, Mermaid, catalog, and
  diff checks passed.

## Validation Gates

- PRD-0016 approval and FEAT-0082 foundation completion precede FEAT-0083
  product implementation.
- One supported structure URL from an otherwise empty inventory produces one
  domain, one derived or unassigned group, one row, and one preview—not a
  `site` or group-only zero state.
- SQL and graph evidence prove that Sync creates no persisted Space, writes no
  `space_id`, and performs no access, capability, Refresh, provider, or model
  work.
- Hierarchy counts equal adjacent eligible rows under All/Jira/Wiki, exact
  query, advanced filters, archived state, direct entry, and selected scope.
- Persisted and URL-derived equal labels remain distinguishable without color;
  Jira and Wiki structure references remain distinguishable in All.
- Aggregate, source-level, empty, recovery, and live feedback never count a
  structure reference as a Jira Issue or Wiki document.
- Add of the same URL retains its explicit persisted Project/Space consequence;
  an equal-label structure reference remains distinct and Sync never silently
  converts or merges it.
- RapidBoard evidence with distinct canonical `rapidView` identities remains
  distinct under one URL-derived `projectKey` group; invalid, missing, or
  ambiguous identity cannot collapse into a generic zero-count board node.
- Refresh and Connections exclude a structure reference unless a later,
  separately approved authority changes that boundary.
- Browser evidence covers only-reference, mixed, repeated, equal-label,
  unassigned-board, long-label, selected, missing, unsupported, and error states
  at effective `1440`, `920`, `700`, and `320` viewports.
- The wide three-region composition, compact list-first disclosure/drawer, and
  narrow sheet/fallback preserve focus, scroll, history, touch targets, reduced
  motion, semantic tokens, and zero horizontal overflow.

## Resolved Contract Decisions

- SPEC-0083 owns three additive, independently identified reference, safe-URL,
  and evidence tables; no `external_resources`, Item, Space, or access owner is
  reused.
- Last-evidence cleanup retains stable identity and safe URLs while deriving an
  archived direct-only state. Any retained eligible source makes a non-archived
  reference available; otherwise it is honestly unavailable.
- Explicit Add and an equal-label structure reference coexist without merge or
  conversion. Add, Connections, Refresh, Item local edits/classification, and
  Workstream/Thread organization do not gain reference authority.
- Explorer and global Search admit only reference identity, generated family
  label, and safe URL under shared Site/service/query state. Item-only filters
  exclude references, and known filtered selection is out-of-scope without
  widening.
- Aggregate and source copy keep link/document and `구조 참조` units separate;
  narrow wrapping may compact layout but cannot collapse the semantic counts.

## Risks / Open Questions

- None within this completed track. Repeated real-use observation remains a
  roadmap activity, not unfinished FEAT-0083 design work.

## Exit Goal

- Syncing a supported Jira Project/Board/Filter/Dashboard/JSM or Confluence
  Space URL yields a deterministic local structure reference under the correct
  Site and honest URL-derived or unassigned group, with one selectable row and
  read-first preview, separate counts, and no false persisted Space or remote
  state.
- The result remains usable and contained across `1440`, `920`, `700`, and
  `320`, while Add, Sync, Refresh, and Connections retain distinct visible and
  executable consequences.

## Handoff To Next Track

- FEAT-0082 owns only the pure locator and safe Session projection foundation;
  FEAT-0083 consumes that contract and owns structure-reference identity,
  evidence, schema, Sync, Search, and Explorer product behavior through
  completed SPEC-0083/RUN-93 after FEAT-0082 passed.
- Stable visual and interaction law is owned by the Design Constitution;
  FEAT-0082, FEAT-0083, RUN-92, RUN-93, and their evaluations retain the
  completed execution trace. No successor design track is active.
- The completed Site-first plan remains unchanged and linked as the inherited
  baseline rather than being reopened.
