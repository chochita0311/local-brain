# SPEC-0089: Workflow Boundary Corrections

## Metadata

- ID: `spec-0089`
- Status: `approved`
- Run: [RUN-20260914-99](../run/run-20260914-99-workflow-boundary-corrections.md)
- Attempt: `1`
- Parent Feature: [FEAT-0089](../feature/feat-0089-workflow-boundary-corrections.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Source Set

- Human approval to execute FEAT-0085 through FEAT-0089 in dependency order.
- Passed FEAT-0087 fixed Focus/Trace interaction and FEAT-0088 append-only
  assertion contract.
- Design Constitution, Workflow Map Design Plan, Design Evaluation,
  Interaction Evaluation, Product, Architecture, Privacy, and existing local
  form/feedback conventions.
- `screen-alignment` in `extend` mode: retain the Focus hierarchy, Trace rail,
  semantic tokens, responsive breakpoints, and progressive fallback.

## Implementation Goal

- Add contextual consequence-preview forms to Episode and Relation Trace,
  commit exactly one FEAT-0088 action through a bounded local POST, and restore
  the user's map orientation after success without introducing a graph editor,
  modal workflow, Workstream mutation, or model dependency.

## Assertion API Lane

- One POST route, `/sessions/{session_id}/workflow/corrections`, accepts only
  `application/x-www-form-urlencoded` with at most 16 KiB and the exact
  single-value fields `action`, `source_episode_key`, `target_episode_key`,
  `close_reason`, `note`, `assertion_id`, `expected_active_assertion_id`, and
  `expected_revision`. Unknown, repeated, malformed, or oversized input fails
  before a database transaction.
- `action` is one FEAT-0088 assertion kind or `undo`. Episode keys and revision
  use exact versioned shapes; optional integer identities are positive and
  bounded. Only `close` accepts a reason and note from the visible product
  surface.
- Inside one outer transaction the route reconstructs the current Focus for
  the path Session and calls exactly one `apply_workflow_assertion` or
  `undo_workflow_assertion`. The domain recomputes current revision and owns
  validation/savepoint behavior; the route commits only a successful result.
- Enhanced requests identify `X-LocalBrain-Partial: workflow-correction` and
  receive bounded JSON: fixed status/code/message, same-origin reload path, and
  changed relation/lifecycle identity only. Success is `200`; stale, duplicate,
  missing-active, and chain conflict are `409`; request/domain validation is
  `422`; malformed transport is `400`; unexpected failure is a bounded `500`.
- Ordinary form success returns a `303` to the same canonical Workflow route
  with one fixed result code and fragment. Ordinary failure renders the same
  current map and form feedback with its corresponding status; it does not
  redirect, mutate optimistically, or expose an exception.
- Requests with an explicitly cross-site Fetch Metadata signal fail before
  parsing or mutation. Responses vary on the partial header and contain no
  note, source body/path, native Session ID, or opaque payload.

## Focus Interaction Lane

- Relation Trace offers only non-duplicate contextual transitions for its exact
  source/destination pair: branch becomes same-flow or merge, continuation
  becomes split or merge, and merge becomes same-flow. An active applicable
  assertion additionally offers undo.
- Episode Trace offers close only for an open/unknown current tip, close-reason
  correction for an active closed tip, reopen only for an active user closure,
  and undo for the current applicable lifecycle assertion. An active relation
  whose effective state is absent remains attached to its source Episode so its
  undo path does not disappear with the edge.
- Each action is an ordinary `<details>` disclosure containing exact affected
  Episode titles, before/after meaning, user-confirmed authority consequence,
  superseded assertion identity when present, and the confirmation form. Merely
  opening, selecting, or canceling a disclosure performs no request.
- Close reason is a required native select with the complete five-value label
  mapping. Its optional note is capped at 1,000 code points in HTML and in the
  domain. Other actions expose no note field.
- Enhanced submission disables only the owning action group. Failure leaves
  the current DOM and graph untouched, restores the controls, and places a
  local recovery message beside the form. Conflict adds one explicit reload
  action.
- On success the controller captures a bounded one-shot presentation snapshot
  in `sessionStorage`, reloads the same canonical Workflow URL, consumes and
  removes that snapshot, then restores selected Episode, expanded branches,
  scale, map pan, Trace scroll, open evidence disclosures, outer scroll, and
  meaningful boundary focus. It retains only stable Episode/relation identity,
  numeric geometry, disclosure keys, and a fixed result code; no title, note,
  evidence content, or source identity is stored.
- The changed edge or Episode receives a structural `사용자 확인` cue and the
  result status. Candidate reasons remain in the original-candidate section of
  Trace. Browser history receives no correction-only entry.
- At `700px` and below the existing text lineage and sequential Trace forms are
  the primary presentation and introduce no nested canvas scroll. No-script
  uses the same preview and POST contract. Reduced motion removes transition
  emphasis without removing labels, borders, or status.

## Presentation Adapter Contract

- `workflow_map_view` maps active assertion summaries by exact Episode or pair,
  attaches lifecycle/absent-relation history to Episode Trace, and builds all
  allowed action previews from the current effective state. Templates do not
  infer domain meanings.
- Visible assertion kinds, meanings, reasons, and authority labels use the
  executable value registry or a complete projection owned by the same
  adapter. Unknown values fail closed instead of becoming raw product copy.
- The client projection adds only assertion revision, lifecycle/authority, and
  stable boundary attributes required for restoration and structural styling.

## Regression And Exclusions

- Existing Session entry/detail, map topology, textual fallback, evidence
  destinations, Workstream/Thread/checkpoint/Resource/Suggestion behavior,
  Atlassian/Local Context actions, Search, Schema, Runner, and source
  synchronization remain unchanged.
- Correction performs no source, filesystem, Git, connector, capability,
  remote, Sync, Refresh, background, Qwen, embedding, model, or training work.
- Workstream promotion/naming, Atlas, main/supporting designation, arbitrary
  edge drawing, bulk editing, and assertion-schema changes remain outside.

## Acceptance Mapping

- Presentation tests cover exact contextual actions, consequence copy, active
  assertion attachment, retained base reasons, lifecycle and absent-edge undo,
  unknown-value failure, and no-script forms.
- Route tests cover strict form shape, all five actions, undo, transaction
  rollback, duplicate/stale/conflict/error statuses, fixed redirects, no cross-
  site mutation, and zero excluded operations.
- JavaScript tests cover bounded restoration serialization, same-path consume,
  success reload, in-place failure, owning-group busy state, cancel, and fixed
  feedback.
- Browser evaluation covers relation correction, close/reopen/undo, evidence
  and branch disclosure, focus, pan/scale, inner/outer scroll, history, stale
  recovery, keyboard operation, reduced motion, no-script, renderer failure,
  and `1440`, `920`, `700`, and `320` widths with synthetic data.

## Open Blockers

- None.

## Continuity Notes

- `2026-09-14`: approved for RUN-20260914-99 after FEAT-0088 passed. The
  Fullstack Product profile is active across Assertion API, Focus interaction,
  and regression/owner lanes.
