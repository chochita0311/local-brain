# SPEC-0141: App Docs Delivery Contract

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](../feature/feat-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- ID: `spec-0141`
- Status: `approved`
- Run: [Run 205](../run/run-20261026-205-app-docs-delivery-contract.md)
- Attempt: 1
- Parent Feature: [FEAT-0141](../feature/feat-0141-app-docs-delivery-contract.md)
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Surface Lane: contract/content; shared navigation/reader/narrow-keyboard as applicable
- Required Evaluators: contract
- Created: `2026-10-26`
- Updated: `2026-10-26`

## Source Set And Goal

The approved Feature and [In-App Documentation](../../policies/project/app-documentation.md) define the exact outcome. Existing desktop/settings/Markdown policies and design constitution remain binding. screen-alignment uses extend mode.

## In-Scope Behavior And Acceptance Mapping

- AC1: Package-local Markdown bodies and a fixed registry are the only user-guide owners; no repository/personal-data publication.
- AC2: The seven /help routes, API-doc separation, desktop authentication and shared Markdown link exception are fully specified.
- AC3: Offline package delivery, first-use access, current-version alignment and bounded missing-guide behavior are fixed; no data/model side effects.

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
