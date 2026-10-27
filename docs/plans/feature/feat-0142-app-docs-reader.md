# FEAT-0142: In-App Docs Reader

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](feat-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- ID: `feat-0142`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: contract, design, functional, ux-heuristic
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Created: `2026-10-26`
- Updated: `2026-10-26`
- Authorization: The owner asked to proceed with the English in-app Docs increment following the shown PRD; this records its bounded child outcome without adding adjacent work.

## Goal

Read the seven English guides inside the existing app shell from Docs immediately above Settings.

## Acceptance Contract

- AC1: All registered /help pages render readable English and usable Docs/app/section links; unknown names and missing assets have bounded errors.
- AC2: Docs is immediately above Settings; both are keyboard-accessible and reachable at 320px and desktop widths. The existing shell/search remain intact.
- AC3: Current-guide indication, normal Back/Forward, opening/closing Settings and onboarding-to-Docs navigation preserve orientation without setup or model side effects.
- AC4: Desktop-authenticated, network-disabled reading uses bundled assets; package data includes every guide. Source-authored Markdown trust rules remain unchanged.

## Scope Boundary

- In: the acceptance contract and [In-App Documentation](../../policies/project/app-documentation.md).
- Out: external hosting/uploads, personal-source publication, app-wide translation, unrelated UI redesign, new source/search/sync/recovery behavior, native release distribution.

## Dependencies

FEAT-0141 contract must pass; FEAT-0143 content must be available before the final reader evaluation.

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

- AC1: All registered /help pages render readable English and usable Docs/app/section links; unknown names and missing assets have bounded errors.
- AC2: Docs is immediately above Settings; both are keyboard-accessible and reachable at 320px and desktop widths. The existing shell/search remain intact.
- AC3: Current-guide indication, normal Back/Forward, opening/closing Settings and onboarding-to-Docs navigation preserve orientation without setup or model side effects.
- AC4: Desktop-authenticated, network-disabled reading uses bundled assets; package data includes every guide. Source-authored Markdown trust rules remain unchanged.

## Harness Trace

- Active spec: [SPEC-0142](../spec/spec-0142-app-docs-reader.md)
- Active run: [Run 207](../run/run-20261026-207-app-docs-reader.md)
- Latest evaluator: [Evaluation](../evaluation/eval-0142-functional-app-docs-reader.md); results and evidence limits are owned by the Run.
- Profile: `frontend-product`

## Continuity Notes

- `2026-10-26`: Boundary recorded under the owner's proceed instruction. Human acceptance after execution remains separate from authorization to perform the work.

- `2026-10-26`: Bounded source/content outcome passed its checks. Final human review and native-binary release acceptance remain separate.
