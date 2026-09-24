# EVAL-0101: Full-History Affinity Inspection — Functional

- ID: `eval-0101-functional`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`
- Feature: [FEAT-0101](../feature/feat-0101-full-history-affinity-inspection-contract.md)
- Spec: [SPEC-0101](../spec/spec-0101-full-history-affinity-inspection-contract.md)
- Run: [RUN-114](../run/run-20260923-114-full-history-affinity-inspection.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Attempt: `1`
- Created: `2026-09-23`

`test_session_affinity.py`: 13/13 pass in the ordinary app runtime. Tests enumerate
every synthetic group, occurrence and all 96 source Sessions; traverse three
scales; retain duplicate inputs, overlaps, unknown dates and empty/excluded
records; and exercise query normalization, stale/config selection, changed/
removed/appended/revoked sources, cached-anchor invalidation, source races,
shared/exclusive locking, expiry, malformed/oversize/symlink content, empty and
missing/unavailable stores. Source and owned-store bytes remain unchanged by
browsing. Actual full-history readiness and exact evidence pass locally in 2.85
seconds, without private content in tool output. No UI claim in this foundation.
