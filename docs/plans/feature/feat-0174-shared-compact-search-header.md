# FEAT-0174: Shared Compact Search Header

- ID: `feat-0174`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Parent PRD: [PRD0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Authority: the user explicitly clarified that reducing the upper search/header height applies to every sidebar destination, including Sessions and Sessions Dashboard.

All shared routes use the compact48px desktop header and32px search controls.
Keep40px narrow touch input, query/action/shortcut semantics, Back/Forward,
sidebar state, page content/scroll and the existing Terminal viewport contract.
Remove the redundant Terminal-only overrides. This does not add a project-folder
registry; Codex project research is a separate read-only comparison.

- Spec: [SPEC0174](../spec/spec-0174-shared-compact-search-header.md)
- Run: [Run255](../run/run-20261113-255-shared-compact-search-header.md)
- Evaluation: [Eval0171](../evaluation/eval-0171-shared-compact-search-header.md)

All11 sidebar routes share the compact header; browser121, actual native12 and
319-file final package checks pass. Existing40px narrow controls and all6 user
terminal executions remain. Codex's attached-folder registry remains a researched
follow-up proposal. Prior native physical/IME/accessibility limits are preserved.
