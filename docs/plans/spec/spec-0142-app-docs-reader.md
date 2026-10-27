# SPEC-0142: In-App Docs Reader

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](../feature/feat-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- ID: `spec-0142`
- Status: `approved`
- Run: [Run 207](../run/run-20261026-207-app-docs-reader.md)
- Attempt: 1
- Parent Feature: [FEAT-0142](../feature/feat-0142-app-docs-reader.md)
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: contract/content; shared navigation/reader/narrow-keyboard as applicable
- Required Evaluators: contract, design, functional, ux-heuristic
- Created: `2026-10-26`
- Updated: `2026-10-26`

## Source Set And Goal

The approved Feature and [In-App Documentation](../../policies/project/app-documentation.md) define the exact outcome. Existing desktop/settings/Markdown policies and design constitution remain binding. screen-alignment uses extend mode.

## In-Scope Behavior And Acceptance Mapping

- AC1: All registered /help pages render readable English and usable Docs/app/section links; unknown names and missing assets have bounded errors.
- AC2: Docs is immediately above Settings; both are keyboard-accessible and reachable at 320px and desktop widths. The existing shell/search remain intact.
- AC3: Current-guide indication, normal Back/Forward, opening/closing Settings and onboarding-to-Docs navigation preserve orientation without setup or model side effects.
- AC4: Desktop-authenticated, network-disabled reading uses bundled assets; package data includes every guide. Source-authored Markdown trust rules remain unchanged.

## Implementation And State Contract

- Canonical bodies: package `content/docs/`; registry maps seven exact names. `/help` is the home, six named articles follow; arbitrary paths never select files. Preserve FastAPI `/docs`.
- Shared Markdown renderer receives an exact `app_doc_routes` allowlist for this first-party consumer only. Default personal-source rendering is unchanged; APIs/files/executable schemes are not admitted.
- Reader reuses base shell and `.markdown-body`; English content, one contents navigation, current item, ordinary links/history and existing Settings dialog. Required local assets only. No new model/data action.
- Docs stays above Settings. Compact mode exposes both utilities without restoring unrelated status noise. At 920px the supporting Docs navigation enters normal flow; 320px content is contained, with tables scrolling locally.
- Auto-onboarding excludes Docs; Welcome links to /help without completing setup. Explicit setup requests still work.
- Known missing guide content returns bounded 503; unknown guide returns 404. No private source or local file path leaks into error output.

## Contract Surfaces

- Producer: source registry and package-owned Markdown. Consumer: shared renderer, Jinja template, authenticated /help route and local CSS.
- Source-of-truth: In-App Documentation and current behavior owners; no generated HTML persistence/indexing.
- Packaging: existing collect_data_files includes all seven bodies; verify package collection separately from a native rebuild.
- Stale assumptions: default Markdown reference tests, desktop forbidden routes, initial setup behavior and existing shell/search must remain valid.

## Evaluation Focus

Contract: route/ownership/auth/trust/package-data checks. Functional: all pages/links and read-only state, history/Settings and offline browser checks. Design/UX for FEAT-0142: native tokens, sidebar relationship, readable width, current state, keyboard/narrow reachability. A browser with desktop middleware is not a rebuilt native app; report evidence limits separately.

## Open Blockers

None for this bounded source integration. Existing release/recipient acceptance is not part of this Run.
