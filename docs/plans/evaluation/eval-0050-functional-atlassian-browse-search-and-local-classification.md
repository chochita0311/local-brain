# EVAL-0050: Atlassian Browse, Search, And Local Classification — Functional

## Metadata

- ID: `eval-0050-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260723-55`
- Attempt: `1`
- Feature: [feat-0050-atlassian-browse-search-and-local-classification](../feature/feat-0050-atlassian-browse-search-and-local-classification.md)
- Spec: [spec-0050-atlassian-browse-search-and-local-classification](../spec/spec-0050-atlassian-browse-search-and-local-classification.md)
- Execution Profile: `fullstack-product`
- Surface Lane: schema/projection → browse/search/detail → local mutation and links
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated additive startup, role-separated FTS, coverage eligibility, cross-source identity, every structured filter family, grouped global Search, detail projections, local classification mutation, Workstream/Thread links, archived recovery, no-script routes, responsive presentation, and complete regressions.

## Checks And Evidence

- Five focused Atlassian browse tests cover role-separated identity/metadata/content/local projection, grouped search, cross-domain same-key distinction, archived default/filter recovery, classification reuse, remote-failure retention, evidence/work membership/latest-Run separation, and no-script local-only routes.
- Existing schema startup applies the additive tables and classification-first index without repairing or replacing stable Items, URLs, remote state/content, evidence, or links. Fresh and compatible schema presentation paths agree.
- Local state validation bounds notes, Topic descriptions, classification names, and Tags; rejects missing Topics or unsupported attention; and saves note, Topic/Tag membership, attention, and FTS within one savepoint.
- Browse and global Search normalize GET state, apply Source/Site/Space/type/coverage/freshness/attention/Topic/Tag/Workstream filters, preserve source context, exclude archived by default, and return stable local Item detail links.
- Detail resolves exact evidence owner links and existing Workstream/Thread link IDs. Add/remove routes use the existing validated work-link service and verify Item ownership before unlinking.
- Server-rendered browse, detail, and local POST paths remain usable without JavaScript. No new route-scoped JavaScript is required for the knowledge workflow.
- Browser QA exercised populated Browse, Item detail, and grouped Search at `1440`, `920`, `700`, and exact `320`, including direct entry and long local/remote fields. All tested document widths remained contained.
- The complete suite passed 256 tests. Python compilation, JavaScript syntax, data-model ownership, nine Mermaid diagrams, schema presentation, the 512-object cleanup audit, repository privacy, and diff whitespace checks passed.

## Evidence Gaps

- No live Gateway, provider latency, or company data was used. Remote stale/unavailable durability and refresh-history projections are exercised with synthetic relational state and existing refresh tests.

## Findings

- None.

## Regression Notes

- One existing Starlette `TemplateResponse` deprecation warning remains non-blocking.

## Route

- Next action: release Functional evaluation for FEAT-0050.
