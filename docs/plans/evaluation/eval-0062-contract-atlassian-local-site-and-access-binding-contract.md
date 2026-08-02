# EVAL-0062: Atlassian Local Site And Access-Binding Contract — Contract

## Metadata

- ID: `eval-0062-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260727-67`
- Attempt: `1`
- Feature: [feat-0062-atlassian-local-site-and-access-binding-contract](../feature/feat-0062-atlassian-local-site-and-access-binding-contract.md)
- Spec: [spec-0062-atlassian-local-site-and-access-binding-contract](../spec/spec-0062-atlassian-local-site-and-access-binding-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: schema → migration → identity/access consumers → durable owners
- Evidence Coverage: `complete`
- Created: `2026-07-27`

## Scope

- Evaluated the fresh and compatible Site/access contract, domain-first
  registration, explicit binding, nullable Item/Space access ownership, and
  every current evidence, browse, discovery, and refresh consumer.

## Checks And Evidence

- Fresh SQLite has optional Site access, explicit Site bindings, and nullable
  Item/Space Source Instance references.
- File-backed legacy upgrade created a non-overwriting valid backup, retained
  exact Site and local-note rows, backfilled one binding plus Item/Space access,
  remained idempotent, and passed `foreign_key_check`.
- Source Instance deletion cascaded only the binding and set Site, Item, and
  Space access references null without deleting local identity or notes.
- One normalized-domain Site is reused across Jira/Confluence services and
  multiple access paths in current producers.
- Local evidence recognizes an explicitly registered local-only Site without
  inventing an access owner; multiple compatible bindings leave that owner
  unassigned.
- Data Model counts, hashes, ownership, Schema Presentation, and cleanup audit
  match 36 ordinary tables, 44 physical foreign keys, and 34 named indexes.

## Contract Evidence

- Producer surfaces: `atlassian.py`, `atlassian_registration.py`, compatible
  startup in `db.py`.
- Consumer surfaces: Atlassian evidence, browse, refresh, discovery, inventory,
  and generated Schema Explorer data.
- Stale-assumption check: old direct Site→Source ownership queries and
  first-URL placeholder Source creation were removed from active producers and
  current owner docs.

## Evidence Gaps

- None.

## Findings

- None.

## Regression Notes

- Existing remote state/content, local classification, evidence, search, and
  Workstream/Thread identity tests remain passing.

## Route

- Next action: `pass`.
