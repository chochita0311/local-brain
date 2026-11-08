# FEAT-0163: Session Display Titles

- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md#session-titles-and-collection-efficiency--2026-11-07)
- Authorization: the owner explicitly requested implementation of discussed item 1.
- Spec: [SPEC-0163](../spec/spec-0163-session-display-titles.md)

Persist a nullable user override immediately after `sessions.title` in fresh and
upgraded schemas. Clicking a primary work Session title edits it in place;
clearing restores the source title. Retain the original title and preserve the
override across synchronization and retained-history updates. Session list,
detail, pinned recall and Chart present the effective title consistently.

Contract/data precedes backend, frontend and docs lanes. Validate migration
rollback/identity/FKs/order/idempotence, title validation and source ownership,
keyboard/pointer/IME/clear/error states, filter/page/scroll continuity, pin and
navigation isolation, narrow/wide layouts, and existing source/provider behavior.
Required evaluators: primary contract, functional, design and interaction review;
same-author evidence is distinct from independent review and human acceptance.
No new search-index content policy, provider writes or native distribution.

Source/browser/wheel evaluation passed in [EVAL-0156](../evaluation/eval-0156-session-titles-and-collection-efficiency.md).
Installed-native and human acceptance are separate.
