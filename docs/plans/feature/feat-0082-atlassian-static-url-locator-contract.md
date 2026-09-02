# FEAT-0082: Atlassian Structure Reference Locator Foundation

## Metadata

- ID: `feat-0082`
- Status: `passed`
- Type: `foundation`
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0016](../prd/prd-0016-atlassian-standard-url-recognition.md)
- Created: `2026-09-01`
- Updated: `2026-09-01`

## Goal

- Establish one privacy-safe semantic descriptor for Atlassian Items,
  structure references, and Site-only family roots so FEAT-0083 can persist and
  render a structure reference without guessing identity from a lossy URL.

## Acceptance Contract

- One pure parser returns exactly `item`, `structure`, `site`, `unsupported`, or
  `unsafe` with common service/family/domain/base/safe-locator fields for every
  recognized result.
- `item` carries exactly one Jira Issue key or Confluence Page ID.
  `structure` carries exactly one `reference_kind` and `reference_identity`
  (`1..300` code points) plus an optional non-authoritative `container_hint`.
  `site` carries no Item or structure identity.
- Supported structure kinds are `jira_project`, `jira_board`, `jira_filter`,
  `jira_dashboard`, `jira_service_portal`, `jira_service_project`, and
  `confluence_space`.
- RapidBoard identity is the canonical positive decimal `rapidView`; one valid
  `projectKey` is only a grouping hint and never part of reference identity.
- Modern Jira Board path ID, Project key, Filter ID, Dashboard ID, JSM portal
  path ID/project key, and Confluence Space key have exact family-specific
  normalization and bounds.
- Issue/Page identity wins over structure or site. Structure identity wins over
  the corresponding family root. An ambiguous/invalid query identity never
  becomes structure identity and falls back only to an otherwise valid `site`
  family result.
- A safe locator is fragment-free and keeps only the canonical allowlisted
  identity projection for its kind. RapidBoard may additionally keep the
  normalized `projectKey` hint. Raw query, JQL, and every other value are
  discarded.
- Session `target_key` derives from the semantic descriptor tuple, excluding
  locator spelling and container hint. Equivalent path/query variants group
  together; different Board/Filter/Dashboard identities never collapse.
- Existing consumers use explicit adapters: evidence/Sync accepts only `item`;
  Add retains its passed Issue/Page/Project/Space subset; structure/site remain
  generic Session URL targets. FEAT-0082 introduces no structure-reference or
  Site persistence and adds no report, screen, control, or copy; explicit Add
  keeps its already passed Project/Space mutation authority. Existing Session
  Related Context consumes the repaired generic URL projection, so its target
  may deduplicate semantically and navigate to the canonical safe locator.
- Locator, Session-reference, and Atlassian-evidence versions advance exactly
  once, cause deterministic derived repair, and then return to zero-write
  unchanged reuse.
- The shared locator and its URL-projection adapters initiate no filesystem,
  Provider, capability, runner, model, connected-discovery, Refresh, or
  external I/O; an already approved producer supplies the bounded URL.

## Scope Boundary

- In:
  - pure descriptor result and stable family/reference vocabularies
  - exact path/query/identifier normalization, bounds, and precedence
  - canonical allowlisted safe locator projection
  - semantic Session target grouping and configured-Item scope safety
  - current consumer adapters and extractor-version repair
  - foundation parity in Product, Architecture, Privacy, Session Activity, and
    Atlassian Source Memory owners
- Out:
  - durable structure-reference schema, rows, evidence, lifecycle, or DML
  - new Site creation from `structure` or `site` outside the already passed
    explicit Add Project/Space subset
  - new Sync result/receipt or Explorer/Search/Connections/Refresh behavior
  - Project/Space inference, `space_id` writes, remote confirmation, or access
  - visible UI, Design Constitution, schema/value registry, or route changes
  - arbitrary query/JQL retention or external/model work

## Surface Lanes

- Descriptor lane:
  - path roots: one shared Atlassian locator owner and normalizer
  - dependencies: passed FEAT-0046/0047/0073/0080/0081
  - expected evidence: table-driven kind/family/identity/hint/locator fixtures
  - evaluator ownership: `contract`, `functional`
- Consumer-projection lane:
  - path roots: `atlassian_evidence.py`, `atlassian_registration.py`,
    `session_references.py`, `ingest/common.py`, focused tests
  - dependencies: shared descriptor
  - expected evidence: semantic target grouping, Item-only Sync, unchanged Add,
    no structure/site DML in Session/evidence paths, unchanged explicit Add,
    version repair/idempotency
  - evaluator ownership: `contract`, `functional`
- Durable-owner lane:
  - path roots: Product, Architecture, Privacy, Workspace/Session Activity,
    Atlassian Source Memory, plans and generated artifacts
  - dependencies: approved descriptor contract
  - expected evidence: FEAT-0083 outcome recorded without claiming it is active
  - evaluator ownership: `contract`

## Contract Surfaces

- `item / structure / site / unsupported / unsafe` kind vocabulary.
- Stable common fields and Item/structure field parity.
- Reference-kind/identity/container-hint matrix and semantic target key.
- Canonical safe locator query allowlist and fixed output order.
- `localbrain.atlassian-locator.v1`,
  `localbrain.session-reference.v3`, and
  `localbrain.atlassian-evidence.v3`.
- Explicit current-consumer admission matrix and zero hidden I/O.

## Required Evaluators

- `contract`: vocabulary, bounds, precedence, privacy, identity, target grouping,
  consumer admission, versions, owners, and call graph.
- `functional`: positive/negative variants, collisions, ambiguity, repair,
  idempotency, zero DML in Session/evidence consumers, unchanged explicit Add,
  and passed-flow regression.

## User-Visible Outcome

- No new UI or structure-reference row. After normal version repair, an existing
  Session Related Context generic URL may reuse the semantic target and navigate
  to the canonical privacy-safe locator instead of the prior lossy query-free
  spelling. FEAT-0082 does not render or persist a structure reference.

## Entry And Exit

- Entry point: one bounded HTTP(S) URL in an already approved local producer.
- Exit: one deterministic descriptor and safe locator that a consumer either
  explicitly admits or leaves as a derived generic reference.

## State Expectations

- Item: exact Issue/Page identity and canonical locator.
- Structure: exact stable reference identity and optional grouping hint.
- Site: recognized service/domain/family with no selectable reference identity.
- Unsupported: safe URL outside the approved taxonomy.
- Unsafe: normalization, credentials, control, encoding, or bound failure.
- Ambiguous query: no query identity; valid family may degrade only to `site`.

## Dependencies

- PRD-0016 and both sequential Feature boundaries are owner-approved.
- Passed PRD-0015/FEAT-0081 and SPEC-0080/0081 remain historical regressions.
- FEAT-0083 dependency gate is satisfied by this passed Feature.

## Likely Affected Surfaces

- `src/localbrain/atlassian_locators.py` or one equivalent single owner
- `src/localbrain/atlassian_evidence.py`
- `src/localbrain/atlassian_registration.py`
- `src/localbrain/session_references.py`
- `src/localbrain/ingest/common.py`
- locator/evidence/registration/reference/Sync focused tests and durable owners

## Pass Or Fail Checks

- PASS when every approved Item/structure/site family and adjacent malformed,
  REST, credential, ambiguous, key-only, and generic case has an exact fixture.
- PASS when Board `rapidView=17` and `rapidView=18` never share a target key,
  while RapidBoard variants for `17` do; `projectKey` never changes that key.
- PASS when safe locators retain only canonical identity projection and allowed
  hint, and contain no fragment, JQL, or arbitrary query.
- PASS when path/query Item identity wins, invalid structure query becomes only
  a family-root `site`, and no family root becomes a structure reference.
- PASS when semantic target grouping is Site-domain/service/kind/identity scoped
  and never reuses a global Issue/Page/reference identity across domains.
- PASS when structure/site fixtures through Session/evidence consumers cause
  zero Site/Space/Item/URL/evidence DML and no current Sync report expansion,
  while explicit Add retains exactly its passed Project/Space behavior.
- PASS when one version repair converges and unchanged same-version repeats are
  read-only.
- PASS when focused and full regressions preserve current Sync, Add, Site-first
  Explorer, Connections, Refresh, and Session Related Context.

## Regression Surfaces

- FEAT-0046 Site-scoped URL/Item identity.
- FEAT-0047 configured Item evidence recognition.
- FEAT-0073 Session reference privacy, grouping, caps, and reconciliation.
- FEAT-0079 one-URL Add subset and atomicity.
- FEAT-0080 Item-only local evidence Sync.
- FEAT-0081 canonical Item grouping and no persisted Space inference.

## Harness Trace

- Approved spec doc: [SPEC-0082](../spec/spec-0082-atlassian-static-url-locator-contract.md), Attempt 1
- Completed run: [RUN-92](../run/run-20260901-92-atlassian-static-url-locator-contract.md), Attempt 1
- Execution profile: `foundation-contract`
- Latest evaluator reports:
  [contract](../evaluation/eval-0082-contract-atlassian-static-url-locator-contract.md)
  and [functional](../evaluation/eval-0082-functional-atlassian-static-url-locator-contract.md),
  both `PASS`
- Latest fix note: none

## Continuity Notes

- `2026-09-01`: owner approved FEAT-0082 as the sole in-loop Feature.
- `2026-09-01`: corrected from a lossy Site-only draft to a semantic structure
  descriptor that preserves RapidBoard and other stable reference identity for
  approved queued FEAT-0083.
- `2026-09-01`: RUN-92 Attempt 1 passed Contract and Functional evaluation.
  Independent focused verification passed `98/98`, the final functional matrix
  passed `113/113`, and the full repository suite passed `463/463`; privacy,
  compile, diff, schema-cleanup, and generated-owner checks also passed.
