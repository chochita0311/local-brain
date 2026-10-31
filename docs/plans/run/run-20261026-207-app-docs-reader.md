# Run 207: In-App Docs Reader

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](../feature/feat-0144-canonical-product-docs.md) and [Run 208](run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- ID: `run-20261026-207`
- Status: `passed`
- Feature: [FEAT-0142](../feature/feat-0142-app-docs-reader.md)
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Active Spec: [SPEC-0142](../spec/spec-0142-app-docs-reader.md)
- Attempt: 1
- Execution Profile: `frontend-product`
- Surface: frontend
- Required Evaluators: contract, design, functional, ux-heuristic
- Created: `2026-10-26`
- Updated: `2026-10-26`

## Selected Loop

- Sequential primary-agent execution: foundation contract passed, content authored, then reader built. No delegated roles or independent-review claim.
- Current phase: original reader evaluation complete; its outcome is recorded in Evaluation Exit below.
- Source of truth: approved Feature and active spec above; In-App Documentation fixes routes, packaging and shared-renderer authority.
- Run record persisted after the corresponding first build pass; this is recorded as delayed stage bookkeeping, not an invented earlier timestamp. All work was sequential; content evaluation closes before final reader evaluation.

## Contract Surfaces

Seven package bodies, fixed /help registry, shared Markdown opt-in links, desktop authentication, app navigation/Settings/setup, offline local assets and package data. No personal-source or model operation.

## Evaluation Coverage

The original evaluation is complete; Evaluation Exit below distinguishes source/content/browser/package checks from unverified native release execution.

## Human Review Outcome

Pending final review of the completed increment; no external publication or native distribution.

## Evaluation Exit

- [Owning evaluation](../evaluation/eval-0142-functional-app-docs-reader.md): PASS; partial overall coverage; source/browser/package checks complete and native binary unverified.
- Targeted guide tests 6/6 and desktop boundary 7/7 pass; all seven guides render at 1440px/320px with external networking blocked, cache disabled and local assets available.
- Relocated wheel passes six guide tests without checkout-content dependency. Full suite: 1,251/1,256; five pre-existing schema/value inventory failures reproduced with this task's app changes removed.
- Post-contract regression: default source-authored Markdown links, desktop API/development exclusions and onboarding state remain intact.
- Next route: human review of the authored English Docs and source integration. No new shared design/interaction promotion candidate; existing rules were applied. Native app rebuild/recipient acceptance remains open; no external release.

## Current Artifacts

- [Contract](../evaluation/eval-0142-contract-app-docs-reader.md)
- [Design and interaction / heuristic inspection](../evaluation/eval-0142-design-app-docs-reader.md)
- [Functional](../evaluation/eval-0142-functional-app-docs-reader.md)

## Fixes Within Attempt 1

Fixed home-query selection so /help stays Getting Started and treated whitespace-only packaged content as unavailable. The final six guide tests and relocated-wheel checks cover these fixes. No source feature or data behavior was added.
