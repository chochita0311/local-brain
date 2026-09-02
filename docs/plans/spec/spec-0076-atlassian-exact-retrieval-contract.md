# SPEC-0076: Atlassian Exact Retrieval Contract

## Metadata

- ID: `spec-0076`
- Status: `approved`
- Run ID: `run-20260829-86`
- Attempt: `1`
- Parent Feature: [FEAT-0076](../feature/feat-0076-atlassian-exact-retrieval-contract.md)
- Parent PRD: [PRD-0014](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Surface Lane: `query-contract -> index-compatibility -> docs`
- Required Evaluators: `contract`, `functional`
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Source Set

- Human decision: approve the proposed Features sequentially; the FEAT-0076
  exact definition and order are accepted as proposed.
- Parent Feature and PRD: FEAT-0076 and PRD-0014.
- Golden sources: current Atlassian role-separated projection, Browse read
  model, global Search adapter, synthetic Atlassian tests, and passed FEAT-0075.
- Relevant policies: Product Model, Atlassian Source Memory, Privacy And Data
  Handling, and execution governance.

## Implementation Goal

- Replace Atlassian token-AND matching with one deterministic local exact read
  model whose matches and order are explainable and safe for FEAT-0077.

## In-Scope Behavior

- Trim the query; empty query means unfiltered Browse.
- Reject a non-empty query with no searchable tokens or more than 12 tokens as
  a bounded local validation error; the route-level 300-character maximum
  remains authoritative.
- Match complete Jira key, stored remote/Page ID, or normalized canonical/alias
  URL as identity. Key/ID comparison is Unicode-casefolded; URL comparison uses
  exact normalized URL identity after normalizing the submitted HTTP(S) URL.
- For non-identity text, normalize each Unicode word token with NFKC plus
  casefold on both query and eligible owned values, retain diacritics, and
  require the complete token sequence contiguously inside exactly one value.
- Title values are local title and approved remote title/summary. Other values
  are individual approved remote-metadata scalar values, indexed normalized
  content, local note, individual Topic name/description, and individual Tag
  name. Separate values never combine into one match.
- Exclude evidence text, observed source text, opaque payloads, Workstream
  names, Site/Space labels, and unavailable remote bodies.
- Rank identity `0`, title `1`, other eligible field `2`, then stable local Item
  ID ascending. Empty Browse retains its existing stable inventory order.
- Project one excerpt of at most 240 characters from only the matched owned
  value, with up to 72 characters of leading context when truncation is
  needed, and a match role of `identity`, `title`, `metadata`, `content`, or
  `local`.
- Compose service, structure, attention, coverage, freshness, Topic, Tag, and
  Workstream filters as AND constraints after matching.
- Represent null-Space structural scope internally as
  `structural_scope=unclassified`; it cannot combine with `space_id`.
- Preserve the role-separated FTS projection and the existing global Search
  adapter, including its historical unlabeled token-AND Atlassian behavior;
  no schema migration or rebuild is required for the Explorer exact read
  model. Cross-source score merging is not changed by this Feature.

## Out-Of-Scope Behavior

- Explorer UI, query input, tabs, hierarchy, filters disclosure, or detail.
- Prefix, fuzzy, token-AND, synonym, semantic, model, embedding, provider, or
  remote fallback.
- New persistence, source-body ownership, or search-index schema.

## Affected Surfaces

- `src/localbrain/atlassian_browse.py`
- focused tests in `tests/test_atlassian_browse.py`
- `docs/policies/project/product.md`
- `docs/policies/project/data-model/atlassian-source-memory.md`
- global Search regression tests through `localbrain.queries.search`, without
  changing its cross-source score contract

## Surface Lanes

- Query contract:
  - path roots: `src/localbrain/atlassian_browse.py`, focused tests
  - dependency order: first
  - implementation responsibility: tokens, identity normalization, per-value
    phrase matching, projection, ranking, and filter composition
  - validation evidence: exact-match matrix and no-result/error tests
- Index compatibility:
  - path roots: existing Atlassian FTS producer and global Search consumer
  - dependency order: after query contract
  - implementation responsibility: retain schema/projection behavior and prove
    exact reads do not need a rebuild
  - validation evidence: projection/rebuild and global Search regressions
- Documentation:
  - path roots: Product Model and Atlassian Source Memory
  - dependency order: after behavior is fixed
  - implementation responsibility: record semantics, ownership, ordering, and
    zero-I/O boundary
  - validation evidence: code/policy parity review

## State And Interaction Contract

- Empty: Browse returns its scoped inventory; the global search adapter still
  returns no results for an empty query.
- Identity: complete identity only; partial identifiers do not match merely
  because their tokens occur inside an identity value.
- Phrase: contiguous tokens inside one owned value; noncontiguous or
  cross-value tokens return no match.
- Filters: exact candidate set intersects with every supplied filter and the
  archived-default rule.
- Invalid/over-limit: raise a bounded `AtlassianBrowseError` and write nothing.
  A query beginning with HTTP(S) but failing URL normalization is invalid
  rather than being reinterpreted as an ordinary phrase.
- Failure: local query errors alter no Item, index, evidence, or remote state.

## Data And Contract Assumptions

- `external_resource_id` is stable tie-break identity.
- `atlassian_items.remote_key`, `remote_id`, and `atlassian_item_urls` own
  identity matching.
- Remote metadata JSON, normalized indexed content, local note, and
  classification rows own individual eligible non-identity values.
- Existing FTS rows remain a rebuildable global/index compatibility surface;
  exact semantics are enforced against current owner values to prevent matches
  across flattened metadata or local fields.

## Contract Surfaces

- Producer expectations: Atlassian persistence owners expose current identity,
  metadata, content, and local fields without adding evidence/source bodies.
- Consumer expectations: Atlassian Browse, and later FEAT-0077, receive ordered
  Item results with `exact_match.rank`, `.role`, and `.excerpt` when queried.
  Global Search remains an explicitly unlabeled historical consumer in this
  Feature and is checked only for regression.
- Generated artifacts: none beyond the normal planning catalog.
- Source-of-truth owner: `atlassian_browse.py` exact read model plus Product
  Model/Atlassian Source Memory durable behavior.
- Stale-assumption check: no exact-mode consumer may describe the new path as
  token-AND, fuzzy, model-backed, or remote; global Search remains unlabeled
  until a separately approved cross-source retrieval contract changes it.

## Required Evaluators

- Contract: identity/field ownership, filter intersection, projection shape,
  zero hidden I/O, global consumer, and stale assumptions.
- Design: not required; no visible surface changes.
- Functional: match/no-match/rank/error/filter/idempotent read behavior and
  existing Atlassian/global regressions.
- UX heuristic: not required; no visible interaction changes.

## Acceptance Mapping

- Identity matrix tests cover key, remote/Page ID, canonical URL, alias URL,
  case normalization, and partial rejection.
- Phrase tests cover contiguous, noncontiguous, cross-field, metadata, content,
  note, Topic, Tag, and no-result behavior.
- Ranking tests cover identity/title/other and stable-ID ties.
- Combined Jira/Confluence, Site/Space/Unclassified, and every retained filter
  proves AND composition.
- Mock/inspection and no-write assertions prove zero external/model work.
- Existing projection/global tests prove compatibility.

## Evaluation Focus

- Treat the current flattened FTS rows as candidates/compatibility only, not
  proof that tokens came from one logical owner value.
- Ensure excerpts never come from evidence/source bodies.
- Ensure query ranking is not overwritten by the inventory's empty-query
  pinned/updated order.
- Ensure `All` is represented by no service constraint, not Jira coercion.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-29`: approved for RUN-86 after RUN-85 passed and the owner accepted
  the proposed exact definition and order.
