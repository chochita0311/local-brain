# EVAL-0050: Atlassian Browse, Search, And Local Classification — Contract

## Metadata

- ID: `eval-0050-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260723-55`
- Attempt: `1`
- Feature: [feat-0050-atlassian-browse-search-and-local-classification](../feature/feat-0050-atlassian-browse-search-and-local-classification.md)
- Spec: [spec-0050-atlassian-browse-search-and-local-classification](../spec/spec-0050-atlassian-browse-search-and-local-classification.md)
- Execution Profile: `fullstack-product`
- Surface Lane: stable Item → role-separated local projection → grouped search/detail
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated additive local-memory ownership, stable cross-source Item identity, coverage-gated search roles, conjunctive filters, archived recovery, local mutation boundaries, existing Workstream/Thread relations, evidence/Run separation, and zero-remote browse/search behavior.

## Checks And Evidence

- `atlassian_item_local_state`, `atlassian_classifications`, and `atlassian_item_classifications` are additive owners. The stable `external_resources.id` remains the only Item identity used by URLs, remote state/content, evidence, classifications, Workstream/Thread links, and FTS.
- Topic and Tag identity is unique by kind plus case-folded normalized name. Topic descriptions are Topic-only; membership is many-to-many and deleting a membership never deletes an Item or remote state.
- Every Item owns a deterministic identity FTS role. Eligible bounded metadata, indexed body, and local note/Topic/Tag text occupy separate roles. Reference never exposes remote metadata/body, metadata never exposes body, and downgrade rebuilds only eligible rows.
- Global Search groups all matching roles back to one stable Item, then resolves current Source Instance, Site/Space, coverage, freshness, attention, classifications, and canonical local detail link.
- Jira and Confluence inventories keep identical remote keys on different Site domains distinct. Filters are conjunctive and local; archived is excluded by default but direct detail plus explicit `archived` or `all` scope recovers it.
- Item detail keeps remote facts/content, local memory and existing work relations, Session/Local Context evidence, and latest explicit refresh Run evidence in separate relational and presentation regions.
- Browse, search, detail, local note/Topic/Tag/attention changes, and Workstream/Thread link changes contain no executor, provider, capability-inspection, maintenance-Run preparation, or model-call path.
- Product, Architecture, Privacy, Work Organization, Atlassian Source Memory, and Derived Retrieval Index owners match implementation. The generated baseline contains 34 ordinary tables, one FTS5 object, 381 columns, 33 explicit indexes, 39 physical relations, 24 application relations, and nine subjects. The 512-object schema cleanup audit is current.

## Evidence Gaps

- No company Atlassian content was retrieved. Contract paths used synthetic local Source Instances, domains, Items, content, evidence, and classifications only.

## Findings

- None.

## Route

- Next action: `pass` and release Design, Functional, and UX Heuristic evaluation.
