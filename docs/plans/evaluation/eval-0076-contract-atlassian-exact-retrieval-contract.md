# EVAL-0076 Contract: Atlassian Exact Retrieval Contract

## Metadata

- ID: `eval-0076-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260829-86`
- Attempt: `1`
- Feature: [FEAT-0076](../feature/feat-0076-atlassian-exact-retrieval-contract.md)
- Spec: [SPEC-0076](../spec/spec-0076-atlassian-exact-retrieval-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `query-contract -> index-compatibility -> docs`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Active feature: deterministic local Atlassian exact read model.
- Active spec: SPEC-0076.
- Evaluated build: query/read-model, focused synthetic tests, and owner-policy
  changes for RUN-86.

## Checks

- Verified complete key/remote-ID and normalized canonical/alias URL ownership.
- Verified NFKC plus casefold token normalization with retained diacritics.
- Verified phrases cannot cross title, metadata scalar, content, note, Topic,
  or Tag values.
- Verified excluded evidence/source text, opaque payload, Site/Space labels, and
  Workstream names never entered the exact field set.
- Verified rank, role, bounded excerpt, stable-ID order, filter intersection,
  and `structural_scope=unclassified` contracts.
- Verified no schema, projection, migration, FTS rebuild, global Search score,
  provider, model, or external-I/O contract changed.
- Verified Product Model and Atlassian Source Memory describe the implemented
  owner boundary without relabeling global Search as exact.

## Evidence

- Environments checked: source inspection, in-memory SQLite synthetic tests,
  existing role-projection/global Search tests, and policy parity review.
- Shared owner: `browse_inventory()` queried read model. Representative
  consumers checked: current Atlassian Browse, historical
  `atlassian_search_results()`, and `queries.search()`.
- Commands:
  - `.venv/bin/python -m unittest tests.test_atlassian_browse -v` — 10 passed
  - `.venv/bin/python -m unittest tests.test_atlassian tests.test_atlassian_registration tests.test_atlassian_browse -v` — 38 passed
  - `PYTHONPYCACHEPREFIX=/tmp/localbrain-feat0076-pyc .venv/bin/python -m compileall -q src/localbrain/atlassian_browse.py tests/test_atlassian_browse.py` — passed
  - `git diff --check` — passed

## Evidence Gaps

- None for the approved backend contract. Browser evidence is not required
  because RUN-86 changes no presentation contract.

## Contract Evidence

- Producer surfaces: Atlassian Item, URL, remote metadata/content, local note,
  and classification relational owners.
- Consumer surfaces: `browse_inventory()` and later FEAT-0077; global Search
  remains a regression-only FTS consumer.
- Schemas, payloads, generated artifacts, commands, routes, config, or policy
  docs checked: `schema.sql` existing fields/FTS table, projection producers,
  Browse/global adapters, Product Model, and Atlassian Source Memory.
- Stale-assumption check: Explorer exact is no longer token-AND; global Search
  is intentionally unchanged and unlabeled; no schema/rebuild assumption was
  introduced.

## Findings

- None.

## Regression Notes

- Existing FTS row generation/rebuild, global mixed-source search, Add,
  registration, classification, and local detail tests passed.

## Route

- Next action: `pass`

## Continuity Notes

- `2026-08-29`: contract evaluation passed after locking global Search,
  Unclassified input, Unicode normalization, malformed URL, and excerpt rules.
