# FEAT-0096: Auto Work Inspection

## Metadata

- ID: `feat-0096`
- Status: `passed`
- Type: `product`
- Surface: `mixed` (`backend`, `frontend`)
- Execution Profile: `fullstack-product`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-16`
- Updated: `2026-09-16`
- User review status: the owner accepted the proposed actual-data, read-only
  inspection UI and specified sidebar placement immediately above Workstreams.
  This is approval of the bounded inspection increment, not replacement quality.

## Goal And Acceptance

Provide one clickable `자동 작업` destination at `/auto-work` where the owner
can inspect actual inferred groups, their stated goals, source contributions,
unassigned material, and the sample boundary without creating or approving work.

1. Sidebar placement, active state, direct entry, list/detail selection,
   pagination, source links, and no-script access work within the existing shell.
2. Render actual rule-based output. Do not invent group names, examples, quality
   percentages, lifecycle, or a fixed total. All groups and unassigned statements
   remain reachable through bounded pages; partial sampling stays explicit.
3. Source/span reasons and observed wording remain distinguishable from inferred
   membership. Unknown completion and assistant claims never become confirmation.
4. Browse only reads the bounded local preview and eligible indexed evidence.
   An explicit local refresh uses existing chronological preparation and the
   unchanged extractor, without expected labels or manual organization input.
5. One purpose-owned preview under the configured data directory is bounded to
   10 MiB and seven days. Atomic replacement retains the previous valid result
   on failure, excludes repository paths/symlinks, and creates no history archive.
6. Missing, expired, changed-source, empty, invalid, busy, and failed states are
   readable. Refresh recovers ordinary missing/stale/failed results; an unknown
   or corrupt owner file requires local inspection, not blind overwrite or an
   endless retry instruction. No raw error or private result is logged or sent
   to a hosted service.
7. Existing Workstream/Thread, Session reading, and source data remain unchanged.
   Verify 1440/920/700/320 widths, keyboard, back/forward, no script, long text,
   source revocation, and source database byte preservation on synthetic data.

## Boundary And Dependencies

In: local preview preparation, retention, GET presentation, one explicit local
refresh POST, sidebar entry, responsive browse/read composition, tests and
local browser verification. Prepare the owner's already-selected current DB
through now for a usable handoff; private output stays on the local machine.

Out: background refresh, full-history body enumeration, extraction tuning,
model/connector/source sync, persistent flow or correction tables, approval or
promotion actions, Workstream/Thread replacement, migration, or legacy cleanup.

Dependency: FEAT-0095's implemented and technically verified *experimental*
admission/extraction shape, not its still-missing semantic quality verdict.
The PRD's explicit inspection exception permits this narrow consumer. It does
not absorb or waive the unresolved production foundation or quality contract.

## Surface Lanes

- Backend: local preview module and main routes; Contract + Functional own
  bounded input, source checks, atomic output, failure and refresh behavior.
- Frontend: shared sidebar plus Auto Work template/assets; depends on backend
  view contract; Design + Functional + UX own rendering and interaction.
- Regression: existing sidebar destinations, Workstreams, Session reading,
  reconstruction experiment, privacy scanner and source schema audit.

## Harness Trace

- Spec: [SPEC-0096](../spec/spec-0096-auto-work-inspection.md)
- Run: [RUN-20260916-102](../run/run-20260916-102-auto-work-inspection.md)
- Result: narrow UI/transport acceptance passed; `20` focused and `665` full
  tests, synthetic browser verification, and private local readiness. Post-run
  owner review can use the actual screen; reconstruction quality is unassessed.
