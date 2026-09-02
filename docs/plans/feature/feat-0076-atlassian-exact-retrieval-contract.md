# FEAT-0076: Atlassian Exact Retrieval Contract

## Metadata

- ID: `feat-0076`
- Status: `passed`
- Type: `foundation`
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Goal

- Establish one deterministic, local exact-retrieval read model that FEAT-0077
  can expose without relabeling the current token-AND FTS or guessing about
  combined Jira/Confluence eligibility.

## Acceptance Contract

- Exact retrieval trims surrounding whitespace and treats an empty query as
  unfiltered local Browse within the active structural and service scope.
- A normalized Jira issue key, Confluence Page ID, confirmed remote ID, or
  canonical/alias URL can match its complete identity case-insensitively where
  the owned field is case-insensitive.
- Non-identity text is a contiguous token phrase within one eligible indexed
  field. Tokens from separate fields or non-contiguous positions cannot be
  combined and called an exact match.
- Eligible text owners remain bounded to current local Item identity/title,
  approved remote metadata, indexed content, local note, Topic, and Tag fields;
  evidence source text, opaque payloads, and unavailable remote bodies are not
  new search owners.
- Exact identity matches order before exact title matches, which order before
  other metadata/content/local-memory phrase matches; ties use a documented
  stable local identity order.
- `All` admits both persisted Jira and Confluence Items. Jira and Wiki scopes
  filter the same read model by stored `jira` and `confluence` service values.
- Structural scope and retained advanced filters apply as deterministic `AND`
  constraints after service eligibility and cannot broaden exact results.
- Search snippets or highlights, when produced for later consumers, derive
  only from the matched eligible field and do not expose a source body that
  the Item does not own.
- The read model performs no model, embedding, provider, capability, network,
  Refresh, evidence scan, or maintenance Run.
- Current token-AND query behavior remains available only as a historical
  regression comparison and is not presented as the new exact contract.

## Scope Boundary

- In:
  - exact identity and contiguous-phrase semantics
  - eligible field ownership and safe matched-field projection
  - `All / Jira / Wiki` service eligibility
  - deterministic ordering and filter composition
  - read-model/query implementation and focused synthetic tests
  - product/data-model owner documentation for exact retrieval
- Out:
  - search input, tabs, hierarchy, filter sheet, result list, or detail UI
  - fuzzy, prefix, synonym, semantic, AI, embedding, or remote search
  - new evidence extraction or source-body persistence
  - ranking personalization or external freshness reads

## Surface Lanes

- Query contract lane:
  - path roots: `src/localbrain/queries.py`, `src/localbrain/atlassian_browse.py`,
    related query helpers and tests
  - dependencies: passed FEAT-0075
  - expected evidence: identity/phrase semantics, field ownership, service
    eligibility, stable ordering, filter composition, and zero-hidden-I/O
  - evaluator ownership: `contract`, `functional`
- Index compatibility lane:
  - path roots: Atlassian FTS projection and schema/index tests only if the
    approved query contract requires a compatible change
  - dependencies: query contract lane
  - expected evidence: fresh/compatible parity, no source-body ownership drift,
    and deterministic rebuild behavior
  - evaluator ownership: `contract`, `functional`
- Documentation lane:
  - path roots: `docs/policies/project/product.md`, Atlassian data-model and
    architecture owners
  - dependencies: fixed query behavior
  - expected evidence: consumer-ready exact semantics and explicit non-AI
    boundary
  - evaluator ownership: `contract`

## Contract Surfaces

- Exact query input normalization.
- Identity and phrase match semantics.
- Eligible indexed field ownership.
- Service/scope/filter eligibility and stable order.
- Matched-field/snippet projection when exposed.
- Zero-hidden-I/O boundary.

## Entry And Exit

- Entry point: internal Atlassian retrieval service called by focused tests and
  later FEAT-0077 consumers.
- Exit or transition behavior: return a deterministic local result set or an
  empty result without starting any other action.

## State Expectations

- Default/empty query: current structural/service population in stable order.
- Exact identity: complete owned identity match precedes phrase matches.
- Exact phrase: contiguous eligible-field matches only.
- No result: empty deterministic result with no fallback broadening.
- Invalid or over-limit query: bounded validation response; no partial hidden
  search or provider fallback.
- Error: query failure remains local and does not alter persisted Item state.

## Dependencies

- FEAT-0075 must be `passed` before this Feature enters build.
- FEAT-0077 must not enter Spec until this exact contract is approved and must
  not enter build until this Feature is `passed`.

## Likely Affected Surfaces

- `src/localbrain/queries.py`
- `src/localbrain/atlassian_browse.py`
- Atlassian query/index producers only if required by the locked contract
- focused Atlassian browse/search/query tests
- `docs/policies/project/product.md`
- `docs/policies/project/data-model/atlassian-source-memory.md`
- `docs/policies/project/architecture.md` when query ownership changes

## Pass Or Fail Checks

- Pass if a synthetic Jira key, Confluence Page ID, remote ID, and canonical or
  alias URL each follow the documented complete-identity rules.
- Pass if a multi-token phrase matches only contiguous tokens within one
  eligible field and never succeeds by combining separate fields.
- Pass if identity, title, other eligible fields, and stable-ID ties follow the
  documented deterministic order.
- Pass if `All`, Jira, Wiki, structure, and advanced filters produce the exact
  intended intersection.
- Pass if empty, no-result, invalid, and failure states remain local and
  deterministic.
- Fail on fuzzy/prefix/synonym fallback, evidence/source-text leakage, model or
  provider work, service coercion to Jira, or undocumented ranking.

## Regression Surfaces

- Existing Atlassian FTS population and rebuild behavior.
- Global Search consumers outside the Atlassian Explorer.
- Site/Space/service/filter eligibility and archived-default behavior.
- Item identity aliases, remote metadata, local notes, Topics, and Tags.
- PRD-0007 zero-model and zero-provider search boundary.

## Harness Trace

- Approved spec: [SPEC-0076](../spec/spec-0076-atlassian-exact-retrieval-contract.md)
- Completed run: [RUN-20260829-86](../run/run-20260829-86-atlassian-exact-retrieval-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract PASS](../evaluation/eval-0076-contract-atlassian-exact-retrieval-contract.md) and [functional PASS](../evaluation/eval-0076-functional-atlassian-exact-retrieval-contract.md)
- Latest fix note: none

## Resolved Review Decisions

- Accepted: `exact` means complete identity or a contiguous token phrase, not
  whole-field string equality and not token-AND behavior across values.
- Accepted order: identity, title, other metadata/content/local memory, then
  stable local identity.

## Continuity Notes

- `2026-08-29`: proposed after PRD-0014 approval to isolate exact retrieval
  semantics from both the Explorer UI and deferred AI retrieval.
- `2026-08-29`: after FEAT-0075 passed, the owner's sequential approval locked
  complete identity or contiguous in-one-field phrase semantics and the
  identity, title, other-field, stable-ID order; FEAT-0076 entered RUN-86.
- `2026-08-29`: RUN-86 passed contract and functional evaluation with complete
  evidence. FEAT-0077 may consume the exact Browse read model.
