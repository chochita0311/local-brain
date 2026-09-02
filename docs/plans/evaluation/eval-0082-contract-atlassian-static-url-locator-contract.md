# EVAL-0082 Contract: Atlassian Structure Reference Locator Foundation

## Metadata

- ID: `eval-0082-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260901-92`
- Attempt: `1`
- Feature: [FEAT-0082](../feature/feat-0082-atlassian-static-url-locator-contract.md)
- Spec: [SPEC-0082](../spec/spec-0082-atlassian-static-url-locator-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `pure locator; safe Session projection; Item-only adapters; durable owners`
- Evidence Coverage: `complete`
- Created: `2026-09-01`
- Updated: `2026-09-01`

## Scope

- Evaluated locator taxonomy, family and identity precedence, encoding and query
  bounds, canonical safe-locator privacy, semantic Session grouping, configured
  Item resolution, Add and evidence-Sync authority separation, version repair,
  zero-hidden-I/O, and durable owner parity.

## Checks And Evidence

- The shared pure owner returns exactly `item`, `structure`, `site`,
  `unsupported`, or `unsafe` and fixes its version at
  `localbrain.atlassian-locator.v1`. Recognized results expose only their allowed
  common and kind-specific fields; terminal results retain only the fixed
  reason vocabulary.
- The approved Jira Issue/Project/Board/Filter/Dashboard/JSM and Confluence
  Page/Space matrix is deterministic and bounded. Item identity wins over
  structure and Site context, malformed approved identity encoding is unsafe,
  and a well-formed invalid identity degrades only through an explicitly listed
  Site fallback. Invalid optional Confluence Space context preserves a valid
  Page identity without creating a container hint.
- Safe locators discard fragments, JQL, tokens, and arbitrary query values.
  They retain only the canonical identity projection: RapidBoard positive
  `rapidView` plus an optional validated `projectKey` hint, Filter and Dashboard
  IDs, or Confluence `pageId` when no valid Space/Page path exists. Query
  inspection is capped at 64 pairs and an overflow cannot authorize identity.
- Semantic Session keys hash the exact UTF-8 compact JSON descriptor tuple and
  exclude locator spelling and container hint. Equivalent Board aliases group
  together while domain, service, kind, family, and identity boundaries remain
  distinct; the retained row keeps a reparsable canonical safe locator.
- Configured Item promotion is normalized-domain and service scoped, checks the
  exact Site-owned normalized URL before one unambiguous Item identity, and
  never reuses a global Issue/Page key. Regression coverage proves that a
  query-bearing manual-Add alias selects its exact owner rather than a sibling
  semantic owner, while a configured Confluence Page retains its canonical
  `pageId` locator.
- Current evidence and explicit Sync adapters admit only `item`. Structure and
  Site descriptors remain generic Session URL evidence and produce no Site,
  Space, Item, Atlassian Item-URL, binding, Atlassian sighting, `space_id`,
  report, receipt, route, or UI expansion. Document provenance keeps its exact
  bounded observed spelling, while Session evidence and normalized Item URL
  authority use only the safe locator.
- Manual Add delegates admission to the descriptor but preserves FEAT-0079's
  original exact-normalized-input URL ownership, alias non-merge behavior,
  atomicity, and existing Issue/Page/Project/Space subset. Board, Filter,
  Dashboard, and JSM structure references remain unsupported Add inputs.
- `localbrain.session-reference.v3` and
  `localbrain.atlassian-evidence.v3` each repair stale derived state once.
  Scanner and explicit-Sync regressions prove the subsequent same-version,
  unchanged pass performs no owned identity or timestamp write.
- The locator imports no SQLite, filesystem, LocalBrain service, Provider,
  capability, runner, model, connected-discovery, Refresh, or network owner.
  Consumer paths use only bounded passed input and local SQLite state. Product,
  Architecture, Privacy, Workspace/Session Activity, and Atlassian Source
  Memory own the same parser-versus-admission, safe-query, provenance, no-new-
  persistence, version, and queued-FEAT-0083 boundaries.
- Independent contract verification passed `98/98` focused locator, evidence,
  registration, Session reference/Sync, and Atlassian evidence-Sync tests. The
  final repository regression receipt passed `463/463`; compile, repository
  privacy, diff, schema-cleanup, and generated-owner checks also passed.

## Findings

- None.

## Route

- Next action: `pass`
