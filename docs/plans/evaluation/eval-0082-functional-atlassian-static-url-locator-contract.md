# EVAL-0082 Functional: Atlassian Static URL Locator Contract

## Metadata

- ID: `eval-0082-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260901-92`
- Attempt: `1`
- Feature: [FEAT-0082](../feature/feat-0082-atlassian-static-url-locator-contract.md)
- Spec: [SPEC-0082](../spec/spec-0082-atlassian-static-url-locator-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `descriptor; Session projection/consumer adapters; version repair`
- Evidence Coverage: `complete`
- Created: `2026-09-01`

## Checks And Evidence

- Descriptor fixtures cover the exact `item`/`structure`/`site`/`unsupported`/
  `unsafe` result contract, URL and identity bounds, normalized host and port
  handling, ASCII-only family/query authority, strict malformed percent and
  UTF-8 handling, well-formed invalid control fallback, and terminal reason
  vocabulary.
- Jira fixtures cover every Issue path, `selectedIssue`-only query identity,
  path-over-query precedence, Project and JSM families, RapidBoard and modern
  Board identity, optional Project hints, Filter, Dashboard, Site fallbacks,
  incomplete roots, query-pair overflow, and REST or unlisted exclusions.
  Confluence fixtures cover all three deployment contexts, Page path and
  `pageId` forms, normalized Space hints, exact safe locators, Space structures,
  invalid optional hints, incomplete roots, and excluded descendants.
- Semantic Session tests prove the exact compact-JSON SHA-256 target contract,
  keep RapidBoard Project hints out of identity while retaining them in safe
  navigation, group equivalent Item aliases, keep distinct identities separate,
  and remove arbitrary query, JQL, token, fragment, and unrelated filter data.
- Configured Item promotion is Site/service scoped, checks the original
  exact-normalized URL owner before one unambiguous semantic identity, and never
  reuses an Item from another domain. Independent adversarial probes confirmed
  that an explicitly added Jira alias wins over its canonical-path identity
  peer and that a configured Confluence `viewpage.action` target retains the
  canonical safe `pageId` query.
- Evidence consumers admit only exact Issue/Page Items. Structure and Site
  locators retain generic Session evidence but create no Atlassian Site, Space,
  Item, Item URL, or Item-evidence row; unsupported outcomes keep the existing
  bounded report vocabulary. Empty-registry, ambiguity, transaction isolation,
  and unchanged-repeat fixtures preserve the same DML boundary.
- Provenance fixtures preserve an authoritative Document's exact bounded
  `observed_url`, including arbitrary query, while its `normalized_url` and Item
  URL matching use the canonical safe locator. Session evidence stores the safe
  locator as both values because no original spelling is available.
- Manual Add remains descriptor-gated but preserves its original normalized
  input and alias non-merge ownership. Items plus Jira Project and Confluence
  Space remain supported; Board, Filter, Dashboard, and JSM structures remain
  rejected atomically with no partial writes.
- `localbrain.session-reference.v3` and
  `localbrain.atlassian-evidence.v3` repair stale derived state once. Current
  same-version Session and Document repeats perform no timestamp-only or
  identity writes, while failed and unavailable source paths retain prior data.
- The shared descriptor imports only Python standard-library pure helpers.
  Projection tests open no Session or Document source files, evidence Sync reads
  only its bounded persisted SQLite inputs, and no locator or adapter path calls
  Provider, capability, runner, model, Refresh, or network work.
- Independent verification passed the exact focused locator, evidence,
  registration, Session-reference, Session-Sync, refresh, and schema matrix
  `113/113`, and the full repository suite `463/463`. Repository privacy and
  `git diff --check` also passed. The only runtime warning was the existing
  Starlette `TemplateResponse` deprecation notice.

## Findings

- None.

## Route

- Next action: `pass`
