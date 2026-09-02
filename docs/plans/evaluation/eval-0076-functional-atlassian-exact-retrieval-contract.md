# EVAL-0076 Functional: Atlassian Exact Retrieval Contract

## Metadata

- ID: `eval-0076-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260829-86`
- Attempt: `1`
- Feature: [FEAT-0076](../feature/feat-0076-atlassian-exact-retrieval-contract.md)
- Spec: [SPEC-0076](../spec/spec-0076-atlassian-exact-retrieval-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `query-contract -> index-compatibility`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Active feature: exact identity/phrase/filter/rank behavior and regressions.
- Active spec: SPEC-0076.
- Evaluated build: RUN-86 working-tree implementation.

## Checks

- Exercised complete Jira key, remote ID, canonical URL, normalized alias URL,
  case behavior, and partial-identity rejection.
- Exercised contiguous/noncontiguous phrases, cross-title/note and
  cross-metadata rejection, metadata/content/local owners, NFKC width folding,
  case folding, and diacritic retention.
- Exercised identity/title/other rank and ascending numeric Item-ID ties.
- Exercised combined Jira/Confluence, Space, Unclassified, archived-default,
  existing classification, and Workstream filter behavior.
- Exercised punctuation-only, over-12-token, malformed HTTP(S), empty, and
  no-result paths.
- Verified the query leaves SQLite `total_changes` unchanged and no code path
  invokes provider, model, capability, Refresh, or maintenance work.
- Re-ran existing FTS, global Search, registration, detail, classification,
  normalization, coverage, and rebuild behavior.

## Evidence

- Environments checked: isolated in-memory SQLite application schema and
  deterministic Python unit tests.
- The exact read owner was exercised through public `browse_inventory()`;
  global Search was exercised as a peer regression consumer.
- 38 Atlassian contract/registration/browse tests passed; 10 focused Browse
  tests include the new exact matrix.

## Evidence Gaps

- None. No active long-running runtime or rendered state is required by this
  backend-only Feature.

## Findings

- None.

## Regression Notes

- Global Search still uses its previous token-AND/BM25 behavior and result
  shape. Exact Browse does not require or mutate FTS projection state.

## Route

- Next action: `pass`

## Continuity Notes

- `2026-08-29`: functional evaluation passed on the complete exact/query
  matrix and named Atlassian regressions.
