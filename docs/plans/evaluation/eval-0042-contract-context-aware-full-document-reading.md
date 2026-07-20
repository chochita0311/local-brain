# EVAL-0042: Context-Aware Full Document Reading — Contract

## Metadata

- ID: `eval-0042-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260720-47`
- Attempt: `1`
- Feature: [feat-0042-context-aware-full-document-reading](../feature/feat-0042-context-aware-full-document-reading.md)
- Spec: [spec-0042-context-aware-full-document-reading](../spec/spec-0042-context-aware-full-document-reading.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `backend-context`
- Evidence Coverage: `complete`
- Created: `2026-07-20`

## Scope

- Evaluated authoritative Document ownership, exact enabled-root eligibility, FOLDERS-only tree production, selected-branch materialization, shared renderer consumption, non-FOLDERS fallback, disabled-root fallback, return identity, and unchanged persistence and 404 boundaries.

## Producer And Consumer Evidence

- `context_document_reader` copies the authoritative Document into the existing shared render path and never writes or replaces `body`.
- `get_context_root` accepts only the Document's stored `context_root_id` and an enabled root; the reader does not search by path, title, source name, or another candidate root.
- Tree production requires `source_type = folder`. File, Apple Notes, missing-root, and disabled-root Documents cannot receive a tree or a source-local reference context through this lane.
- The selected Document ID flows into `context_source_tree`, and each materialized directory derives `contains_selected` only from its descendants. Direct-entry disclosure is therefore tied to the exact tree identity rather than a guessed path.
- The same `context_document_preview` and FEAT-0038/0039 renderer/reference context produces derived HTML, properties, and state for full reading.
- The route retains the existing Document lookup and `404 Document not found` branch, then hands the derived reader context and unchanged membership query to the template.
- Return identity is `/context?root={stored root}&document={selected id}` only when that exact root is enabled; otherwise it safely falls back to `/context`.
- No database schema, source registration, scanning, membership, search, or stored Document contract changed.

## Verification

- `uv run --no-sync python -m unittest tests.test_context_roots -v` — 3 tests passed.
- Synthetic tests cover a selected nested FOLDERS branch, local reference rendering, file-source no-tree behavior, enabled source counts and return identity, disabled-root no-tree behavior, and source/body preservation.
- Post-contract verification passed all 166 repository tests after the frontend consumer was complete.

## Evidence Gaps

- None for the backend-context producer contract. Frontend composition and interaction remain owned by the downstream Design, Functional, and UX evaluators.

## Findings

- No implementation bug, spec gap, planning gap, ambiguous ownership, or stale persistence assumption was found.

## Route

- Next action: `pass`; release the frontend-reading lane.
