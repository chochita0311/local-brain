# EVAL-0110 Functional: Scope And Requests

## Metadata

- ID: `eval-0110-functional-scope-and-requests`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `partial`
- Run: [RUN-129](../run/run-20260929-129-personal-insight-scope-and-requests.md)
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `data, backend, frontend`
- Created: `2026-09-29`

## Checks And Evidence

Commands completed successfully:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_personal_insight*.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_ui_contract.py' -v
```

There are 30 personal-insight tests and 42 shared UI contract tests. New cases exercise scoped positions versus raw sequence, truncation, complete/missing message requests, selection/type fields, schema freeze, legacy validation/rendering, and candidate/request reference rechecks. Existing usage tests cover emitted usage retained after invalid results and cancellation, idempotent recovery, and exclusion from ordinary work Sessions.

An isolated local server with synthetic records exercised six states at both 1440px and 320px: historical report, finding, no actionable finding, missing evidence, running, and failed. All 12 loads returned 200 with no horizontal document overflow or page errors. Native disclosures worked by keyboard. Unselected entry, history navigation, report download, and an admitted Session link worked. Observed browser requests were GET only; no product provider Run was started.

## Gaps And Route

This is real rendering and route execution with synthetic records, not a live paid CLI run or test of the owner's long-running server. The [foundation functional report](eval-0108-functional-selection-contract.md) separately records repeated model-surrogate outputs. Live CLI behavior and owner benefit are outside this correction's acceptance boundary and remain non-blocking gaps. Route: `pass`.
