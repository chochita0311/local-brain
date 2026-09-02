# EVAL-0079 Functional: Atlassian Manual Add And Connections Separation

## Metadata

- ID: `eval-0079-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260829-89`
- Attempt: `1`
- Feature: [FEAT-0079](../feature/feat-0079-atlassian-manual-add-and-connections-separation.md)
- Spec: [SPEC-0079](../spec/spec-0079-atlassian-manual-add-and-connections-separation.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `registration; structural handoff; Connections routes`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- Focused registration tests cover Jira issue/project and Confluence
  Page/Space inference from every origin, exact normalized-URL reuse, alias
  conflict, savepoint rollback, invalid and REST rejection, and zero optional
  access during Add.
- An encoded 8,000-code-point multibyte Confluence URL passes the bounded form
  parser and registers successfully with its stored bootstrap title capped at
  500 characters. Oversized structure, return, form, and connection path IDs
  produce bounded normalization or `422` responses rather than SQLite errors.
- New and reused Items redirect to selected Jira/Wiki Explorer state with
  actual Site, Space or Unclassified containment and archived visibility.
  New and reused persisted Spaces redirect to the owner Site and retain their
  eligible-zero active branch across reload and direct entry without creating
  an Item.
- The direct Add GET renders the same one-field form and ordinary POST action,
  providing the no-script and failed-enhancement path. Enhanced `422` replaces
  only Add content, retains the URL and safe return, and performs no partial
  identity write.
- Connections normalizes omitted, `all`, and invalid view state to Jira and
  `confluence` to Wiki. Add and Connections contexts do not render each
  other's forms or data.
- Connections SQL tracing proves one grouped Item-count query and no Item,
  content, evidence, external-resource, Workstream, Thread, Session, or
  Document row materialization.
- Discovery rejects Site/binding mismatch before executor or Run work, derives
  authority from the selected binding, keeps the one-call bounded candidate
  contract, and requires explicit confirmation. Tampered or deleted Run-owned
  candidate identity returns `422` and creates no Space.
- Chrome confirmed a neutral busy/disabled Add state, `422` input retention,
  successful full navigation, and focus on the selected Item preview. The 91
  focused Atlassian/UI-contract checks and the full 403-test suite passed;
  JavaScript syntax, privacy, generated docs, schema checks, artifact catalog,
  and `git diff --check` also passed.

## Findings

- None.

## Route

- Next action: `pass`
