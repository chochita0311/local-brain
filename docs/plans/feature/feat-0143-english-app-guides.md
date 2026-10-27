# FEAT-0143: English App Guides

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](feat-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- ID: `feat-0143`
- Status: `passed`
- Type: `product`
- Surface: `docs`
- Execution Profile: `docs-content`
- Required Evaluators: contract, functional
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Created: `2026-10-26`
- Updated: `2026-10-26`
- Authorization: The owner asked to proceed with the English in-app Docs increment following the shown PRD; this records its bounded child outcome without adding adjacent work.

## Goal

Provide seven concise English guides for setup, current settings, main screens, search and recovery using current app behavior.

## Acceptance Contract

- AC1: All seven canonical Markdown bodies cover the PRD topics without development-only content or private examples.
- AC2: Preserve all operative defaults, scope, save/apply timing, source/original preservation, optional AI, sync lifecycle and restore constraints.
- AC3: Procedures have one owner, links use the fixed product routes, and every page has a short purpose/basic flow/necessary limits/next links.

## Scope Boundary

- In: the acceptance contract and [In-App Documentation](../../policies/project/app-documentation.md).
- Out: external hosting/uploads, personal-source publication, app-wide translation, unrelated UI redesign, new source/search/sync/recovery behavior, native release distribution.

## Dependencies

FEAT-0141; reader integration is evaluated separately in FEAT-0142.

## Surface Lanes And Ownership

- Contract/content: package source ownership, guide text and renderer trust rules; primary agent.
- Reader/navigation for FEAT-0142 only: sidebar, article, Settings access, narrow and keyboard states; primary agent.
- Logical roles run sequentially in the primary agent; no delegated execution or independent-review claim.

## Entry, Exit And States

- Entry: package-owned guidance; FEAT-0142 starts from /help or the Docs link.
- Exit: app/document links and browser history; existing Settings closes back to the current guide.
- Default: Getting Started; empty personal sources/model are valid. Unknown guide is 404; missing registered content is bounded unavailable. No remote/loading placeholder is needed for static local content.

## Contract And Regression Surfaces

Fixed /help registry, shared render_markdown trust defaults, existing API docs and desktop boundary, Python/PyInstaller package data, onboarding completion, current preferences/source DB/model state. No source schema migration.

## Pass Or Fail Checks

- AC1: All seven canonical Markdown bodies cover the PRD topics without development-only content or private examples.
- AC2: Preserve all operative defaults, scope, save/apply timing, source/original preservation, optional AI, sync lifecycle and restore constraints.
- AC3: Procedures have one owner, links use the fixed product routes, and every page has a short purpose/basic flow/necessary limits/next links.

## Harness Trace

- Active spec: `writing-contract-0143` — [Writing Contract](#writing-contract)
- Active run: [Run 206](../run/run-20261026-206-english-app-guides.md)
- Latest evaluator: [Evaluation](../evaluation/eval-0143-english-app-guides.md); results and evidence limits are owned by the Run.
- Profile: `docs-content`

## Continuity Notes

- `2026-10-26`: Boundary recorded under the owner's proceed instruction. Human acceptance after execution remains separate from authorization to perform the work.

## Writing Contract

- ID: `writing-contract-0143`; designated by Run 206 as its active spec.
- Authority: PRD-0024 and In-App Documentation; desktop-app-and-settings and the existing app guide provide factual source behavior. Source/developer-only mechanics outside the PRD are not copied.
- Owners: exactly seven bodies in `src/localbrain/content/docs/`; fixed names in the delivery contract. Titles/routes remain owned by the registry.
- Permitted change: new English user prose and links, synthetic examples only; no product-behavior change or additional pages.
- Preservation: complete settings category/scope/save/apply distinctions; default 10/30 completion schedules and Off behavior; source unregister vs original deletion; model-free keyword/explicit AI; usage estimate/Project limits; readable-format and PDF/Notes constraints; backup inclusions/exclusions, same-Mac/schema/restart/recovery copy; close versus quit and data-preserving app replacement.
- Presentation: short orientation, basic steps, necessary conditions, related links; no forced word limit or omission of qualifying facts. Existing UI labels remain recognizable.
- Evaluation owners: Contract checks factual scope and exclusions; Functional checks readable shared-renderer output and product links; final browser integration belongs to FEAT-0142.

- `2026-10-26`: Bounded source/content outcome passed its checks. Final human review and native-binary release acceptance remain separate.
