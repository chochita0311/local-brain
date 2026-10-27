# EVAL-0142: Docs Reader Contracts

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](../feature/feat-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- Feature: [FEAT-0142](../feature/feat-0142-app-docs-reader.md)
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Active Spec: [SPEC-0142](../spec/spec-0142-app-docs-reader.md)
- Run: [Run 207](../run/run-20261026-207-app-docs-reader.md)
- Attempt: 1
- Execution Profile: `frontend-product`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`

## Checks

- All seven fixed guide names map to package files; request strings never select filesystem paths. Unknown names return 404 and missing/empty/whitespace-only registered bodies return bounded 503. `/help?slug=...` retains the Getting Started home.
- The explicit `app_doc_routes` exception activates recognized allowlisted product links only. Tests retain unresolved default source-authored links and reject API, development-only and protocol-relative destinations. Existing report-specific Session links, HTML escaping, heading anchors and table rendering remain shared behavior.
- Desktop middleware requires the per-launch credential on every guide; existing API/development routes remain excluded. The normal FastAPI API-reference route is unchanged.
- First-use Docs access does not complete onboarding, register a source or require a model. Source collection, preference mutation and model operations are absent from the reader's request path.
- Offline wheel build succeeds. The archive contains byte-identical guide bodies, module, template and CSS; a relocated-wheel run passes all six guide tests. Existing PyInstaller package-data collection is unchanged; it was inspected, not executed as a new native build.

## Regression Evidence And Limits

Guide tests: 6/6. Desktop-boundary tests: 7/7. The full suite ran 1,256 tests before the final home-query/error refinement: 1,251 passed, with five schema/value inventory failures. All five reproduce in an isolated baseline with this task's app changes removed and the pre-existing work retained. They concern learning-table ownership/counts, audit table parity, column counts and value-family counts; no Docs defect was identified in those failures. The final refinement is covered by the six guide tests and relocated-package run.

Contract evidence covers source integration and Python package delivery. A rebuilt native `.app`/ZIP and recipient-Mac execution remain unverified and are not claimed by this result.

### Reproduced Baseline Failures

| Existing check | Same failure with Docs app changes removed |
| --- | --- |
| Effective schema and owner docs | Three learning tables lack ordinary-table ownership; expected/found ordinary tables 45/48, physical FKs 58/59, fresh explicit indexes 43/44 and effective indexes 51/52. |
| Cleanup audit and ledger | Decision parity is missing `learning_attempts`, `learning_lessons` and `learning_visibility`. |
| Audit manifest boundary | Expected 46 objects; found 49. |
| Presentation manifest baseline | Expected 542 columns; found 543. |
| Value registry inventory | Expected 81 families; found 87. |
