# SPEC-0060: Session Related Context Rail

## Metadata

- ID: `spec-0060`
- Status: `approved`
- Run ID: `run-20260724-65`
- Attempt: `1`
- Parent Feature: [feat-0060-session-related-context-rail](../feature/feat-0060-session-related-context-rail.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: relationship projection → detail failure isolation → responsive rail
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Source Set

- Human approval on `2026-07-24`: execute both approved PRDs' Features automatically and sequentially.
- PRD-0009, passed FEAT-0059, PRD-0002 Session hierarchy, and PRD-0006 conversation-reading contracts.
- Existing workspace, Workstream/Thread polymorphic links, enabled Local Context Documents, Atlassian Session evidence, and owned target routes.
- Design Constitution, Design Evaluation, and Interaction Evaluation using the Fullstack Product profile.
- Screen Alignment mode: `extend`; the repository constitution is the target and no durable Figma file key is owned by the source set.

## Projection Contract

- Project only existing local relationships for persisted primary Session detail.
- Eligible reasons and precedence are:
  1. `session-reference` / `이 Session에서 참조`;
  2. `same-thread` / `같은 Thread`;
  3. `same-workstream` / `같은 Workstream`;
  4. `same-workspace` / `같은 프로젝트`.
- One target appears once and retains all applicable reasons in precedence order.
- Equal-strength targets order by case-insensitive title, target type, and stable target ID.
- Scan at most `48` candidates independently from Session evidence, shared organization membership, and enabled same-workspace Documents. Emit at most `12` targets and report bounded overflow or scan truncation.
- Global modification recency is not an eligible relationship.
- Resolved missing local paths, archived Atlassian Items, and unsafe external URLs stay visible with explicit availability; unsafe URLs are not links. Malformed or unresolved polymorphic targets are omitted with a bounded unavailable count.
- The projection loads target identity, metadata, provenance, availability, and owned destination only. It never copies content bodies or writes a new Session relationship.

## Route And Failure Contract

- The primary Session detail route loads the projection after the core Session and organization orientation.
- A local SQLite query error returns a bounded rail error while preserving identity, orientation, Subsessions, and conversation.
- Subsession detail never loads or renders the related-context projection.
- The request starts no model call, embedding request, external read, capability inspection, source scan, maintenance Run, or relationship mutation.

## Presentation Contract

- Wider than `920px`, the detail layout keeps the conversation reading column at its established maximum and places a `340px` Related Context rail at the right.
- At `920px` and below, DOM and visual order are Session identity/orientation, Related Context, then conversation.
- Each entry exposes type, title, provenance, owned destination when safe, availability, and all bounded reasons.
- Empty copy explicitly describes the local relationship basis and never substitutes recent or suggested content.
- Partial and error states remain local to the rail.

## Verification

```bash
uv run python -m unittest tests.test_session_related_context tests.test_session_inventory tests.test_session_pin_ui tests.test_ui_contract tests.test_atlassian_evidence tests.test_workstreams -v
```

- Render a temporary synthetic database at `1440`, `920`, `700`, and emulated `320`.
- Confirm readable conversation width, desktop rail, compact document order, no document/item overflow, unavailable treatment, Subsession exclusion, and local-only requests.

## Open Blockers

- None.
