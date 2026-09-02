# FEAT-0081: Atlassian Deterministic Site-First Hierarchy

## Metadata

- ID: `feat-0081`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0015](../prd/prd-0015-atlassian-site-first-url-organization.md)
- Created: `2026-09-01`
- Updated: `2026-09-01`

## Goal

- Make deterministic local URL evidence immediately useful in a domain-first
  Atlassian Explorer without repeating service layers or exposing internal
  Item terminology.

## Acceptance Contract

- Persisted-only Sync accepts strict Jira Issue and Confluence Page URLs with
  no pre-existing Site, creates or reuses one normalized local Site across Jira
  and Wiki on that domain, and performs no external/model/capability work.
- One link identity is still deduplicated by Site and normalized URL; repeated
  Sync is idempotent and preserves all local/remote/history owners. Explicit
  Sync Document currentness depends on persisted content/source fingerprint,
  successful status, and extractor/resolver version rather than registered
  Site/service fingerprint.
- Each source owns one transaction. A new Site is reusable through a
  source-local overlay, enters the action-wide resolver only after commit, and
  disappears with that overlay on rollback.
- The hierarchy groups the eligible population by Site first. Its children are
  persisted Spaces/Projects, deterministic URL-explicit container groups, and
  one Site-local `소속 미확인` group.
- Jira Issue keys contribute only their exact project-key prefix. Confluence
  contributes only a decoded `/spaces/{key}/pages/{page-id}` key. Other URL
  forms remain unassigned.
- URL grouping is a read-only projection. It creates no Space, changes no
  `space_id`, and is never represented as remote confirmation. Exactly one
  canonical URL owns the hint; alias and evidence URLs never choose grouping.
- `All` keeps mixed Jira/Wiki links under one Site and uses a compact type cue;
  Jira/Wiki tabs filter the same hierarchy without adding a service parent.
- Site, child, and unassigned selections preserve view, query, advanced
  filters, and reachable hierarchy orientation; as with the existing Explorer
  structure transition, they reset selected link/document state and
  result-local scroll. Node count stays equal to list membership.
- Ordinary visible copy replaces `Item` with `링크` for Jira-only context,
  `문서` for Wiki-only context, and `링크/문서` for mixed context. This covers
  Explorer, Add, preview, full detail, Sync, Connections, Refresh, global
  Search, and browser-authored live copy without renaming physical schema,
  internal APIs/routes/selectors, value-registry keys, or historical artifacts.

## Scope Boundary

- In:
  - deterministic zero-configuration local Site admission in Sync
  - deterministic URL container descriptor
  - Site-first hierarchy/filter/active-state URLs
  - Korean unassigned label and link/document terminology
  - responsive, focus, history, and regression evidence
  - durable Product, Design Constitution, Source Memory, and Privacy parity
- Out:
  - persisted Space inference or migration
  - remote discovery/Refresh, AI, or content-based grouping
  - search ranking, preview fact, Add, Connections, or classification redesign

## Surface Lanes

- Contract/backend lane:
  - path roots: `atlassian_evidence.py`, `atlassian_evidence_sync.py`,
    `atlassian_browse.py`, route-state helpers, focused tests
  - dependencies: passed FEAT-0080 deterministic Sync and PRD-0015
  - expected evidence: strict admission, deterministic descriptor, no Space
    mutation, idempotency, count/filter parity, zero hidden I/O
  - evaluator ownership: `contract`, `functional`
- Explorer presentation lane:
  - path roots: Atlassian templates, shared semantic styles, local controller,
    UI-contract and browser tests
  - dependencies: backend read model
  - expected evidence: domain-first reading order, compact service cue,
    terminology, focus/history/scroll continuity at four widths
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable owner lane:
  - path roots: Product, Architecture/Privacy when needed, Source Memory,
    Design Constitution, plan indexes
  - dependencies: completed contract
  - expected evidence: no stale service-first or configured-domain-only owner
  - evaluator ownership: `contract`

## Contract Surfaces

- strict URL recognition and normalized Site creation
- deterministic URL container descriptor and version
- Explorer structural request fields, canonical URLs, active-node counts
- hierarchy read model and template terminology
- owner documents and generated artifact catalog

## User-Visible Outcome

- The user presses Sync from an empty inventory and then browses links through
  a simple `모든 도메인 → domain → Project/Space | 소속 미확인` tree.

## Entry And Exit

- Entry point: local Sync or ordinary Atlassian Explorer navigation.
- Exit: inspect a filtered link or selected document without losing compatible
  query, filter, hierarchy-orientation, or browser-history context; structural
  transitions retain the existing selected-detail reset contract.

## State Expectations

- Default: `모든 도메인` is the hierarchy root, domains lead beneath it, and no
  service parent is rendered.
- Empty: no retained strict URL produces the existing bounded empty state.
- Success: domain and deterministic child counts equal the adjacent list.
- Unknown containment: one `소속 미확인` child remains reachable.
- Mixed service: a compact Jira/Wiki cue disambiguates equal child labels.
- Error: invalid or stale structural state is bounded and cannot mutate data.
- Narrow: hierarchy remains a bounded disclosure and the list stays primary.

## Dependencies

- PRD-0014, FEAT-0077, FEAT-0078, FEAT-0079, and FEAT-0080 are passed
  regression baselines.

## Likely Affected Surfaces

- `src/localbrain/atlassian_evidence.py`
- `src/localbrain/atlassian_evidence_sync.py`
- `src/localbrain/atlassian_browse.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/templates/_atlassian-item-preview.html`
- `src/localbrain/static/atlassian.js` and `styles.css` only as needed
- focused Sync/Browse/UI tests and durable owner docs

## Pass Or Fail Checks

- PASS when a fresh database plus fixed synthetic URLs produces the same
  logical Site/link/container graph on repeated fresh runs and zero duplicate
  state on same-database repeat.
- PASS when source locations change only evidence edges, not link/container
  identity.
- PASS when one empty-database source containing same-domain Jira and Wiki URLs
  creates one Site, and when a forced late source failure publishes no partial
  Site/link/evidence row or action-cache identity to the following source.
- PASS when persisted Space, URL group, and unassigned counts equal selected
  lists under All/Jira/Wiki and retained advanced filters.
- PASS when no URL-derived grouping writes `atlassian_spaces` or `space_id`.
- PASS when ordinary product copy contains no user-facing Item terminology.
- PASS when Chrome at four widths preserves search, list/detail, selection,
  focus, scroll, back/forward, Add, Sync, Connections, and Refresh behavior.

## Regression Surfaces

- exact retrieval ordering and all advanced filters
- selected preview and safe full-detail return
- manual Add and persisted Space handoff
- local Sync report/receipt/single-flight and source evidence ownership
- Connections and explicit Refresh
- global Search diagnostic filters

## Harness Trace

- Approved spec: [SPEC-0081](../spec/spec-0081-atlassian-deterministic-site-first-hierarchy.md), Attempt 1
- Completed run: [RUN-91](../run/run-20260901-91-atlassian-deterministic-site-first-hierarchy.md), Attempt 1
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  [contract](../evaluation/eval-0081-contract-atlassian-deterministic-site-first-hierarchy.md),
  [design](../evaluation/eval-0081-design-atlassian-deterministic-site-first-hierarchy.md),
  [functional](../evaluation/eval-0081-functional-atlassian-deterministic-site-first-hierarchy.md),
  and [UX](../evaluation/eval-0081-ux-atlassian-deterministic-site-first-hierarchy.md), all `PASS`
- Latest fix note: none

## Continuity Notes

- `2026-09-01`: boundary locked by direct owner instruction after reviewing
  empty Sync, domain-first grouping, Jira/Wiki URL identity, and Item
  terminology.
- `2026-09-01`: RUN-91 Attempt 1 passed contract, design, functional, and UX
  evaluation. Focused Atlassian/UI, Atlassian discovery, full regression,
  privacy, owner/generated checks, and Chrome evidence passed; FEAT-0081 is
  passed.
