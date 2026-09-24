# SPEC-0096: Auto Work Inspection

## Metadata

- ID: `spec-0096`
- Status: `approved`
- Feature: [FEAT-0096](../feature/feat-0096-auto-work-inspection.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Run: [RUN-20260916-102](../run/run-20260916-102-auto-work-inspection.md)
- Execution Profile: `fullstack-product`
- Attempt: 1
- Created: `2026-09-16`
- Updated: `2026-09-16`

## Sources And Scope

Use the Feature boundary, unchanged reconstruction/preparation contracts, and
Product/Architecture/Privacy policies. Apply Design Constitution, Design
Evaluation and Interaction Evaluation. Screen alignment mode is `extend`:
shared shell and browse/read family, no new visual language or canvas.

## Producer And Persistence Contract

- `auto_work.py` owns a versioned private preview, not Workstream identity.
  The fixed owner is `localbrain.auto-work-preview.v1`; path is
  `auto-work-preview/current.json` beneath the configured runtime directory.
- Explicit preparation samples the selected current DB through invocation UTC,
  under existing 60-Session/8-source/text/120-second/512-MiB bounds. Use only the
  latest frozen snapshot and `reconstruct(..., include_organization=False)`.
  No scoring or expectation synthesis is needed to *display* unassessed output.
- Save owner, created/expiry times, preparation counts, latest frozen manifest,
  snapshot digest, and complete extraction output. Do not copy the DB, native
  files, raw payloads, all admitted bodies, or source-native Session identity.
- A private output directory and advisory single-flight lock guard atomic
  replacement. Only a valid owned existing result may be replaced. Never
  overwrite unknown content or follow symlinks. Clean staged output on failure.
- Retain one result for seven days, not an archive. A visit discards an expired
  valid owned preview under the same lock; no retention scheduler is introduced.
  Failure retains a still-valid prior result and reports failure separately.
- CLI and server child output use fixed codes only. Browser refresh runs the
  explicit preparation command in an isolated subprocess; no app initialization
  occurs inside it. Simultaneous refresh reports busy. No browser GET starts
  analysis, source synchronization, migration, or model work.

## Consumer Contract

- GET `/auto-work`: read the fixed owner file, enforce size/version/expiry,
  revalidate the frozen source selection through the read-only adapter, and bind
  output spans/wording to the current admitted text before rendering. Changed,
  revoked, unavailable, or invalid evidence fails closed; no old private label
  or excerpt is rendered as current. No exception text is exposed.
- Local numeric Session/Document/Atlassian routes are constructed by the view
  adapter, never taken from output-provided URLs. Evidence includes role,
  observation time, source kind, span offsets, and literal escaped wording.
- Query owns `page`, `flow`, `view` (`flows` or `unassigned`), and evidence page.
  Normalize invalid values; missing selections show a bounded explanation.
  All actual results are reachable via pages, not a top-N quality disguise.
- POST `/auto-work/refresh` accepts no private path, IDs, query, model, or scope
  parameters. Require same-origin browser submission; reject cross-site or
  non-loopback requests before analysis. Return fixed notice codes through a
  303 redirect. Failure does not claim freshness or erase the preceding result.
- Responses are private/no-store. Neither browser storage nor telemetry retains
  evidence. No acceptance, promotion, naming, or manual-classification controls.

## Visual And Interaction Contract

- Add `자동 작업` immediately above Workstreams, keeping other destinations and
  shell geometry intact. Gate the new link on the matching server capability so
  an old process with newly loaded templates does not expose an unknown route.
- Heading and one clear unassessed/sampled explanation precede a scan path of
  counts, group list, selected detail and evidence. Unknown work lifecycle and
  completion remain unknown; sample counts are not correctness metrics.
- Use existing semantic tokens. Wide view shows adjacent list/detail; at 920
  and below regions become sequential, with normal document scroll. At 700 and
  320 retain readable text, touch controls and existing horizontal navigation.
- The shared narrow navigation uses the existing 40px touch-height role on
  every destination, preserving one geometry across old and new routes. Auto
  Work accounts for classic scrollbar width at the supported viewport floor.
- Corrupt or unknown owned-path content has a local-inspection recovery message;
  refresh is not allowed to overwrite it merely to remove the error state.
- Native links/forms are the primary path. Direct entry, back/forward, refresh,
  query selection, pagination and no-script use remain executable. Local JS may
  show refresh progress without hiding the old result; BFCache restores controls.
- Long Korean/English titles, identifiers and literal quotes wrap. Selected
  states have readable labels and `aria-current`; keyboard focus stays visible.

## Acceptance Mapping And Evidence

- Feature 1, 2, 3: synthetic populated/empty output, all-page reachability,
  literal/XSS-sensitive text, source links and authority labels.
- Feature 4, 5, 6: read-only DB bytes, no GET analysis, frozen hashes and
  revocation, expiry, malformed/symlink/oversize output, atomic failure,
  busy/failed refresh, same-origin rejection and no private diagnostics.
- Feature 7: full Python regression and browser shell/list/detail/source
  navigation at 1440/920/700/320, no script, reduced motion, error/empty states.
- Browser captures use synthetic data only. Actual-data handoff checks emit only
  fixed readiness codes; no private titles, excerpts, counts or images go to
  the hosted agent. UI acceptance is not semantic reconstruction acceptance.

## Open Blockers

None for this bounded inspection UI. FEAT-0095's independent quality evidence
remains unresolved and blocks production replacement, not this approved viewer.
