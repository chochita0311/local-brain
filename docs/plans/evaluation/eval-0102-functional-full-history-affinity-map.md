# EVAL-0102: Full-History Affinity Map — Functional

- ID: `eval-0102-functional`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`
- Feature: [FEAT-0102](../feature/feat-0102-full-history-affinity-map.md)
- Spec: [SPEC-0102](../spec/spec-0102-full-history-affinity-map.md)
- Run: [RUN-115](../run/run-20260923-115-full-history-affinity-map.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `backend`, `frontend`
- Attempt: `1`
- Created: `2026-09-23`

Historical RUN-115 evidence, not acceptance of the later time-axis or continuous
canvas contract. [EVAL-0104 Functional](eval-0104-functional-temporal-affinity-flow.md)
owns the replacement checks; the original test counts and scoped PASS remain below.

All 18 consumer/route tests, 20 old-sample tests and full 963-test regression pass
(three optional semantic checks run separately in the semantic environment).
Browser QA passes at 1440/920/700/320: stable coordinates and transform across
selection, three-level expansion, exact source and return, latest-request ownership,
history, keyboard pan/zoom, fit/reset, ordinary versus modifier wheel, complete
paging, no-script and injected SVG-render failure. Browser emits zero mutation
requests. Separate sampled QA preserves refresh/source/history at all four widths.
Running synthetic probes cover missing/busy/expired/invalid/stale/empty states;
unit tests cover unavailable and concurrently invalidated anchors. Actual app
readiness/exact source and loaded client rendering are checked via non-content
booleans. No private screenshot or source text is part of this evidence.
