# PRD-0015: Atlassian Site-First URL Organization

## Metadata

- ID: `prd-0015`
- Status: `passed`
- Boundary State: passed; FEAT-0081 passed and no active child Feature remains
- Owner role: `human`
- Created: `2026-09-01`
- Updated: `2026-09-01`
- User review status: boundary and Feature execution completed

## Request Summary

- Replace the repeated `All Sites → Jira/Wiki → domain → Unclassified` tree
  with one domain-first structure whose children are deterministic Jira
  Project or Confluence Space groups plus one honest unassigned group.
- Let an empty Atlassian inventory consume strict persisted Session and Local
  Context URLs without requiring a prior manual Site registration.
- Remove the internal `Item` term from ordinary product copy in favor of link
  or document language.

## Source Set

- Human request: domain changes define the first hierarchy boundary;
  Project/Space groups follow directly, and unresolved links remain together.
- Golden sources: the current rendered Atlassian Explorer, passed PRD-0014,
  current Product Model, Atlassian Source Memory, and Design Constitution.
- Current implementation: deterministic local evidence Sync, URL recognizer,
  browse hierarchy projection, Explorer route state, templates, and tests.

## Product Intent

- Make the Atlassian tree describe the structure visible in the user's URLs
  without repeating service hierarchy or requiring the user to pre-enter
  Project/Space information.

## Confirmed Scope

- Domain-first Site hierarchy in `All`, `Jira`, and `Wiki` views.
- Existing persisted Project/Space identity remains authoritative.
- A null-Space link may receive a read-only structural group only when its
  strict URL explicitly carries a Jira project key or Confluence Space key.
- URL-derived grouping is deterministic and never writes `space_id` or creates
  a persisted Space.
- Strict Jira Issue and Confluence Page URLs may create or reuse a local Site
  and link during persisted-only Sync even when the inventory starts empty.
- One normalized domain remains one Site when the retained evidence contains
  both Jira and Wiki URLs; service qualifies the link and child cue, not Site
  identity.
- Jira/Wiki remains available through the top scope tabs and a compact child
  cue when mixed results need disambiguation.
- Ordinary screen copy uses `link` or `document`; internal schema and code may
  retain the `Item` identity term.
- The hierarchy and list retain the same query/filter/archived denominator,
  count parity, selection, history, focus, and responsive continuity.

## Excluded Scope

- AI, model, semantic, title, or content inference.
- Provider, network, capability, connected discovery, or remote Refresh work
  during Sync or Browse.
- Persisting URL-derived Project/Space rows or changing `space_id`.
- Guessing a Space from Page title, nearby prose, Session topic, folder path,
  or cross-link frequency.
- Reworking search ranking, detail facts, local editing, Add, Connections, or
  Refresh ownership.

## Uncertainty

- None that changes the approved execution boundary. Persisted Space names may
  differ from URL keys; the read model must keep their provenance distinct
  rather than silently rewriting either owner.

## Constraints

- The same persisted sources, source locations, strict URLs, local database
  state, and resolver version produce the same logical Site/group/link graph.
- Source Session/Document edges remain evidence and never become hierarchy
  parents.
- New Site creation is local-only and bounded to URLs accepted by the strict
  Jira Issue or Confluence Page recognizer.
- Each source is atomic. A Site created while processing one source is visible
  inside that source and becomes reusable by later sources only after commit;
  rollback leaves no Site/link/evidence row or cached identity.
- The current shell, search, action separation, link list, preview, and
  full-detail fallback remain stable.
- Visible work uses the `fullstack-product` profile, `screen-alignment` in
  `extend` mode, and contract, design, functional, and UX evaluation.

## Acceptance Envelope

- From an empty Atlassian inventory, Syncing deterministic Jira and Confluence
  URLs produces domain nodes and link rows without external work.
- The left tree reads `모든 도메인 → domain → Project/Space | 소속 미확인`,
  not service first.
- URL-explicit container groups are reproducible, filterable, and clearly
  distinct from persisted containment in data ownership.
- Same-domain Jira and Wiki links stay distinguishable without an extra
  service hierarchy level.
- All prior Explorer state, Add, Connections, Sync, and Refresh contracts
  regress cleanly at `1440`, `920`, `700`, and `320`.

## Candidate Features

- [FEAT-0081: Atlassian Deterministic Site-First Hierarchy](../feature/feat-0081-atlassian-deterministic-site-first-hierarchy.md): passed [RUN-91 Attempt 1](../run/run-20260901-91-atlassian-deterministic-site-first-hierarchy.md) with contract, design, functional, and UX evaluation.

## Continuity Notes

- `2026-09-01`: created and approved from the owner's direct implementation
  instruction. This is a new follow-up boundary and does not reopen passed
  PRD-0014 or its completed FEAT-0075 through FEAT-0080 history. It supersedes
  only PRD-0014's service-first hierarchy, configured-domain-only explicit Sync
  admission, and ordinary `Unclassified` / `Item` copy. Exact retrieval,
  authority separation, action ownership, selection-reset semantics,
  responsive continuity, and every other passed PRD-0014 acceptance remain
  required regressions. PRD-0010 remains the approved incremental history for
  normalized-domain Site identity and URL-only local Add/access separation;
  PRD-0015 neither reopens its passed FEAT-0062/0063 work nor consumes its
  later-observation boundary.
- `2026-09-01`: FEAT-0081 passed RUN-91 Attempt 1 with all four required
  evaluators, focused and full regression coverage, owner-document parity, and
  Chrome evidence at `1440`, `920`, `700`, and `320`. PRD-0015 is passed and
  has no active child Feature.
