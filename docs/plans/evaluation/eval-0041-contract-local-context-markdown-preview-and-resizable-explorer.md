# EVAL-0041: Local Context Markdown Preview And Resizable Explorer — Contract

## Metadata

- ID: `eval-0041-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-46`
- Attempt: `1`
- Feature: [feat-0041-local-context-markdown-preview-and-resizable-explorer](../feature/feat-0041-local-context-markdown-preview-and-resizable-explorer.md)
- Spec: [spec-0041-local-context-markdown-preview-and-resizable-explorer](../spec/spec-0041-local-context-markdown-preview-and-resizable-explorer.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `backend-integration`
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated the authoritative Document to shared renderer to Local Context preview handoff, owning-source resolver eligibility, selected-source guard, and consumer-ready result shape before the frontend lane.

## Checks And Evidence

- `context_document_preview` copies the selected row, preserves `body`, and adds only trusted `rendered_body`, explicit `render_state`, and immutable `render_properties` derived fields.
- The helper calls the shared renderer exactly once and supplies `build_markdown_reference_context` without adding route-local parsing, sanitization, math, or wikilink behavior.
- The reference adapter returns a context only for an enabled `source_type='folder'` root and selects every resolver Document by that same `context_root_id`.
- Direct file and Apple Notes source types cannot receive a FOLDERS resolver and therefore keep source-relative references readable with `no-source` state.
- The route retains its existing cross-root rejection before invoking the preview helper.
- Synthetic scanned FOLDERS documents resolved an alias and heading to a LocalBrain Document route while the copied source body remained byte-equal; a standalone file produced explicit no-source output.
- No template `safe` filter, source `Markup` conversion, rendered-output persistence, URL fetch, or schema change entered the backend lane.

## Contract Evidence

- Producer surfaces: `contexts.py` resolver adapter and preview helper; `main.py` selected Document route.
- Consumer surfaces: `context.html` receives `rendered_body`, `render_state`, and `render_properties`; frontend implementation may only compose those values.
- Artifacts checked: folder and file scanner fixtures, Document detail rows, source identity guard, renderer result, and route context.
- Stale-assumption check: no second parser, sanitizer, or global title lookup exists in the route.

## Evidence Gaps

- None for the backend handoff. Frontend markup, lifetime, and interaction contracts remain assigned to their own evaluators after the dependent lane is built.

## Findings

- None.

## Regression Notes

- Existing resolver and renderer suites plus three Context Root tests passed.

## Route

- Next action: `pass`; release the frontend-explorer lane.
