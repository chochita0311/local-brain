# FEAT-0141: App Docs Delivery Contract

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](feat-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- ID: `feat-0141`
- Status: `passed`
- Type: `foundation`
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Created: `2026-10-26`
- Updated: `2026-10-26`
- Authorization: The owner asked to proceed with the English in-app Docs increment following the shown PRD; this records its bounded child outcome without adding adjacent work.

## Goal

Fix the canonical content owner, product routes, packaging, privacy and shared-renderer link authority before content or reader work.

## Acceptance Contract

- AC1: Package-local Markdown bodies and a fixed registry are the only user-guide owners; no repository/personal-data publication.
- AC2: The seven /help routes, API-doc separation, desktop authentication and shared Markdown link exception are fully specified.
- AC3: Offline package delivery, first-use access, current-version alignment and bounded missing-guide behavior are fixed; no data/model side effects.

## Scope Boundary

- In: the acceptance contract and [In-App Documentation](../../policies/project/app-documentation.md).
- Out: external hosting/uploads, personal-source publication, app-wide translation, unrelated UI redesign, new source/search/sync/recovery behavior, native release distribution.

## Dependencies

None; existing desktop/settings/Markdown contracts remain authoritative.

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

- AC1: Package-local Markdown bodies and a fixed registry are the only user-guide owners; no repository/personal-data publication.
- AC2: The seven /help routes, API-doc separation, desktop authentication and shared Markdown link exception are fully specified.
- AC3: Offline package delivery, first-use access, current-version alignment and bounded missing-guide behavior are fixed; no data/model side effects.

## Harness Trace

- Active spec: [SPEC-0141](../spec/spec-0141-app-docs-delivery-contract.md)
- Active run: [Run 205](../run/run-20261026-205-app-docs-delivery-contract.md)
- Latest evaluator: [Contract evaluation](../evaluation/eval-0141-contract-app-docs-delivery.md); PASS for the original contract outcome, with execution evidence owned by the Run.
- Profile: `foundation-contract`

## Continuity Notes

- `2026-10-26`: Boundary recorded under the owner's proceed instruction. Human acceptance after execution remains separate from authorization to perform the work.
