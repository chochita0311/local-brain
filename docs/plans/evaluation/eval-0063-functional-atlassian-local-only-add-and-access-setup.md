# EVAL-0063: Atlassian Local-Only Add And Access Setup — Functional

## Metadata

- ID: `eval-0063-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260727-68`
- Attempt: `1`
- Feature: [feat-0063-atlassian-local-only-add-and-access-setup](../feature/feat-0063-atlassian-local-only-add-and-access-setup.md)
- Spec: [spec-0063-atlassian-local-only-add-and-access-setup](../spec/spec-0063-atlassian-local-only-add-and-access-setup.md)
- Execution Profile: `fullstack-product`
- Surface Lane: no-script routes, read models, and regressions
- Evidence Coverage: `complete`
- Created: `2026-07-27`

## Checks And Evidence

- Synthetic no-script URL POST creates a local Item and redirects to its stable
  fragment without increasing Source Instance count.
- Synthetic GET after first local-only registration renders both URL and access
  forms in DOM order, contains the normalized domain, and contains no removed
  name/title inputs.
- Access POST creates one real binding and preserves the URL-derived Item title.
- Empty or invalid references fail before partial Source/binding creation.
- URL preview debounce, validation rendering, connected discovery,
  candidate confirmation, connection enablement, browse, evidence, and refresh
  regressions pass.

## Evidence Gaps

- None. Visual geometry evidence is recorded separately in the completed
  [Design evaluation](eval-0063-design-atlassian-local-only-add-and-access-setup.md).

## Findings

- The initial synthetic GET found a missing per-domain deduplication set for a
  first local-only Site. The read model was corrected and the test now passes.

## Route

- Next action: `pass`.
