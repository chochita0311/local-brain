# EVAL-0079 Contract: Atlassian Manual Add And Connections Separation

## Metadata

- ID: `eval-0079-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260829-89`
- Attempt: `1`
- Feature: [FEAT-0079](../feature/feat-0079-atlassian-manual-add-and-connections-separation.md)
- Spec: [SPEC-0079](../spec/spec-0079-atlassian-manual-add-and-connections-separation.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `registration contract; structural handoff; Connections; documentation`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Evaluated one-URL registration authority, transaction and identity rules,
  canonical Explorer handoff, Add/Connections separation, bounded local and
  remote-read ownership, and Product/Source Memory parity.

## Checks And Evidence

- Add and preview accept one URL authority. Jira/Confluence service, Site,
  Item, and Space identity are derived locally from that URL; a legacy
  `service` value cannot constrain or override the inferred service.
- Recognition preserves the approved HTTP(S), credential, route-family, and
  8,000-code-point bounds. The 160-KiB form envelope admits the worst-case
  encoded supported URL while retaining the 128-field parser ceiling, and
  URL-derived bootstrap titles are deterministically capped at 500 code
  points.
- Registration uses exact normalized-URL reuse inside a savepoint. Validation,
  alias conflict, or late failure leaves no partial Site, Space, Item, or
  external-resource rows; supported URL aliases are not silently merged.
- Success redirects are derived from committed persisted owners. Items carry
  their actual service, Site, Space or Unclassified scope, selected identity,
  and archived visibility when required. An explicit selected persisted Space
  may project one truthful zero-count active branch while roots and siblings
  remain Item-backed.
- Safe return and structural IDs are revalidated at every server boundary and
  bounded to SQLite integer range. External, setup, malformed, oversized, and
  cross-service destinations fall back or fail with the approved bounded
  response instead of entering SQLite or emitting a broken Back link.
- `/atlassian` owns Explorer only, `/atlassian/add` owns the server-executable
  one-field Add, and `/atlassian/connections` owns optional access and bounded
  discovery. Legacy setup routes normalize by `303`; no hidden parallel setup
  state remains.
- Connections GET reads persisted Site/Space and connection facts plus one
  aggregate Item count grouped by Site. It does not materialize Item, content,
  evidence, Session, or Document rows. Add performs no provider, model,
  capability, executor, Run, or remote work.
- Discovery resolves Site and binding authority before any Run work. Candidate
  confirmation re-resolves Run-owned Site, Source Instance, service, and
  candidate identity; deleted or mismatched owners return a Connections-scoped
  error without creating a Space.
- Product Model, Atlassian Source Memory, Design Constitution, Feature, Spec,
  routes, and generated value dictionaries own the same behavior. Independent
  contract audit and the full 403-test suite passed.

## Findings

- None.

## Route

- Next action: `pass`
