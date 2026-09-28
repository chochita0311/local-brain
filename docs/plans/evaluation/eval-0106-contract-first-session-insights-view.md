# EVAL-0106 Contract: First Session Insights View

## Metadata

- ID: `eval-0106-contract`
- Status: `complete`
- Evaluator Type: `contract`
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

- The Insights route reads the FEAT-0105 ledger and its source-file extraction coverage; the Usage & Cost route calls its usage query only. The new ranking has no date, metric, or breakdown dependency and does not require live Session joins.
- The query groups observed rows by normalized name across source keys, counts retained rows, orders by count then stable name, and projects the latest parsable event time. The view omits Session/source row disclosure and separate rank numbers as the owner later requested.
- Both heading actions are native server links. Direct route and browser-history navigation worked. Initial, partial, current, and retained-without-current-file states have distinct copy.
- The active Feature and Spec now match the implemented three-column row and the FEAT-0105 dependency's actual acceptance sequence. No route or data-contract mismatch remains.

## Limit And Route

No JavaScript-disabled browser profile was launched; the no-script conclusion rests on native `href` links and directly rendered server routes. This does not block the bounded route contract. Route `pass`.
