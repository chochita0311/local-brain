# EVAL-0106 Functional: First Session Insights View

## Metadata

- ID: `eval-0106-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-20260928-124](../run/run-20260928-124-first-session-insights-view.md)
- Attempt: `2`
- Feature: [FEAT-0106](../feature/feat-0106-first-session-insights-view.md)
- Spec: [SPEC-0106](../spec/spec-0106-first-session-insights-view.md)
- Execution Profile: `fullstack-product`
- Lane: `backend`, `frontend`
- Created: `2026-09-28`

## Evidence And Finding

- `.venv/bin/python -m unittest discover -s tests -p test_ui_contract.py -q`: 42 passed. The checks include reciprocal links, one ranking header, three column labels, timestamp hook, and responsive layout rule.
- `.venv/bin/python -m unittest discover -s tests -p test_skill_observations.py -v`: 8 passed. This includes all-time grouped counts, stable tie order, last-use time, Session/source disappearance, empty and partial coverage, targeted correction, and compatible ledger startup.
- Browser direct-entry, refresh, link round trip, back, and forward reached the correct Insights and Usage & Cost routes. Synthetic filled, empty, partial, 35-row, missing-time, and retained-history-without-current-file states rendered with expected labels. At 320px the 35-row table stayed within the document width.
- The first Usage & Cost route does not call the Insights query. After updating two stale expectations to the approved Cost default and removed limitation copy, `.venv/bin/python -m unittest discover -s tests -p test_usage_dashboard.py -q` passed 12 checks.

## Limit And Route

The browser used synthetic local data and did not submit an analyzer Run. Native links and server-rendered direct routes were inspected; no separate JavaScript-disabled browser profile was launched. Route `pass`.
