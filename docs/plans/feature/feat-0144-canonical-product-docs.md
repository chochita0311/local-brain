# FEAT-0144: Canonical Product Docs

## Metadata

- ID: `feat-0144`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: contract, design, functional, ux-heuristic
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Created: `2026-10-27`
- Updated: `2026-10-27`
- Authorization: The owner explicitly requested generalized product-user Docs, removing Troubleshooting, Open settings and the version badge; the follow-up requires preserving necessary information in its feature guides.

## Goal And Scope

Read six canonical English product guides without development-environment framing or unnecessary reader controls. Keep Docs above Settings and the existing product/navigation behavior.

- In: retire the Troubleshooting guide; move required facts into Settings/Storage, Search, Sessions, Local Contexts and Getting Started; remove the Docs header action/version badge and now-unused registry/style fields; update current owners and links.
- Out: app-wide translation, settings/source/search/backup behavior changes, platform-support expansion, external publication and native release distribution.

## Acceptance Contract

- AC1: Exactly six guide topics remain; Troubleshooting is absent from contents and guide links, and its old route is unavailable rather than a shipped orphan body.
- AC2: Reader has no per-guide Open settings action or For LocalBrain version label; ordinary app Settings stays available.
- AC3: Necessary former Troubleshooting facts survive in their feature guides, especially explicit registration/readability, search readiness, backup inclusion/exclusion, same installation/computer/schema restore eligibility, explicit replacement/restart/recovery and original/model preservation.
- AC4: Prose describes ordinary download/install/use and completed functionality; no developer tooling, personal-machine framing, test-release caveats or unfinished-feature lists. Actual user-facing conditions and limits remain accurate.
- AC5: Surviving guide/section/app links, current topic, history, first-use access, desktop authentication and narrow layout remain functional.

## Dependencies, State And Regression

Uses the passed delivery/reader/content contract in FEAT-0141–0143, amended by this explicit owner correction. The six canonical routes and source-body list remain fixed; unknown/missing guide behavior and Markdown trust defaults remain unchanged. No schema or data migration.

## Surface Lanes

- Content: six English guide bodies and assertion-level migration; primary agent; Contract/Functional evaluation.
- Reader: registry/template/style and allowed routes; primary agent; Design/Functional/UX evaluation.
- Initial implementation and evaluation execute sequentially in the primary agent; separately tasked content/structure and closeout reviews are recorded below. They do not establish independent runtime certification.

## Harness Trace

- Active Spec: [SPEC-0144](../spec/spec-0144-canonical-product-docs.md)
- Active Run: [Run 208](../run/run-20261027-208-canonical-product-docs.md)
- Latest evaluator: [Evaluation](../evaluation/eval-0144-canonical-product-docs.md); PASS for the bounded correction. Run outcome and human acceptance remain separate.

## Continuity

- `2026-10-27`: Owner-directed correction; older seven-guide Run evidence remains historical. This is a content/reader correction, not a product capability change.
- `2026-10-27`: Six-guide content, reader and package checks pass under Run 208. Ready for owner review; final human acceptance and the parent release boundary remain open.
- `2026-10-27`: Subsequent owner-selected prose trim removes About and path-label explanations from Settings Docs, including the category row and jump link. This changes documentation coverage only; Run 208's earlier browser/package evidence remains scoped to its evaluated content.
- `2026-10-27`: Owner clarified that useful path-abbreviation guidance should remain in a suitable place. Sessions now explains `~`, descendant paths and full paths outside home alongside conversation metadata, preserving saved locations and historical Project attribution. About remains omitted.
- `2026-10-27`: After two read-only subagent reviews, the owner authorized the reported corrections. Search now describes automatic preparation after a successful download, manual preparation/retry when needed and the subsession exclusion. Settings and Local Contexts explain unregister confirmation, search-entry cleanup and retained source details/documents/originals in plain English. Guide tests 6/6 and desktop boundary tests 7/7 pass after the edits. This is a source-content follow-up; earlier browser/package evidence is not expanded to the revised text.
- `2026-10-27`: Owner-authorized closeout completed the bounded source outcome after two independent documentation reviews and corrections. The session-only snapshot passes all 1,257 tests, current desktop/narrow browser checks and relocated-wheel guide tests. Run 208 and its evaluation own results and limits. This Feature passes for its source/content scope; the parent PRD retains native/recipient release acceptance, and source commit/push is separately authorized by the closeout request.
