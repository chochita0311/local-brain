# EVAL-0042: Context-Aware Full Document Reading — Design

## Metadata

- ID: `eval-0042-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260720-47`
- Attempt: `1`
- Feature: [feat-0042-context-aware-full-document-reading](../feature/feat-0042-context-aware-full-document-reading.md)
- Spec: [spec-0042-context-aware-full-document-reading](../spec/spec-0042-context-aware-full-document-reading.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `frontend-reading`
- Evidence Coverage: `complete`
- Created: `2026-07-20`

## Scope

- Evaluated the full Document reader against the Design Constitution, the existing detail-and-read family, and the FEAT-0041 Local Context tree and Markdown family in `screen-alignment` `extend` mode.

## Checks And Evidence

- The shell, Local Contexts location, return action, Document title and path, source/path/size metadata, memberships, and existing reading card retain the current product hierarchy and semantic-token system.
- A shared source-tree macro preserves the Explorer directory, row, selected, count, and disclosure language without introducing a second tree style.
- The FOLDERS composition adds only a fixed contextual tree beside the existing detail-and-read content. The tree owns bounded independent scrolling while the body remains within the established reading and prose measures.
- Properties, headings, paragraphs, links, references, code, tables, callouts, tasks, math, deferred images, and fallback states continue through the shared `.markdown-body` presentation.
- Non-FOLDERS Documents omit the tree and empty column entirely; source identity, return path, metadata, and bounded reading remain visually intact.
- Chrome MCP rendered the FOLDERS reader at `1440` with a `300px` tree and a contained reading column without page overflow.
- Chrome MCP rendered `920`, `700`, and emulated `320` widths. At every compact width the tree preceded the reader at full available width; the `920px` rule was corrected during evaluation and its sequential geometry was rechecked.
- Long Markdown, code, paths, headings, and tables remained contained. Narrow tables retained local overflow rather than widening the page.
- Direct visual review of FOLDERS and non-FOLDERS routes found no foreign shell, new navigation family, unsupported control, invented source state, or empty structural region.
- The complete 166-test suite, JavaScript syntax check, privacy check, and diff whitespace check passed.

## Evidence Gaps

- None.

## Findings

- The initial `920px` render retained the desktop two-column grid. Moving the existing compact reader rules from the `700px` block to the Constitution's `920px` block resolved the mismatch.
- No remaining visual drift, hierarchy conflict, containment defect, or unsupported design language was found.

## Regression Notes

- The change extends only full Document reading and reuses the Local Context tree and Markdown families. Shared navigation, source management, and unrelated detail screens retain their current contracts.

## Route

- Next action: release Design evaluation for FEAT-0042 and Run acceptance.

## Post-Pass Correction

- `2026-07-20`: [FIX-0006](../fix/fix-0006-context-reading-follow-up.md) corrected shared Markdown table fill and code tone after owner review. In the owner-reported glossary Document, the table wrapper and table occupied the full reading width and the final header cell reached the table edge; code-heavy reading retained the LocalBrain frame with a softer dedicated palette rather than Run-console semantics.
