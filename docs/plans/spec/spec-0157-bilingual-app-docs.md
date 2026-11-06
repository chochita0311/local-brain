# SPEC-0157: Bilingual App Docs

## Metadata

- ID: `spec-0157`
- Status: `approved`
- Run: [Run233](../run/run-20261105-233-bilingual-app-docs.md)
- Attempt: `1`
- Parent Feature: [FEAT-0157](../feature/feat-0157-bilingual-app-docs.md)
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, design, functional, ux-heuristic
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Writing And Reader Contract

Six existing app guides only. Bare help entries default to Korean; `lang=ko|en`
selects a fixed bundled locale. Invalid language falls back to Korean, never a file
path. Language selection retains the topic; contents, adjacent and authored guide
links retain language and ordinary browser history. Other source Markdown keeps
its existing link authority. No network or preference migration is needed.

Preserve each existing guide's facts, linked conditions, eligibility/stop rules,
backup scope and original/data/cache distinctions in both languages. Use task
steps, concise tables and short paragraphs. Source installation points to README;
no developer-only or suspended screens enter Docs. Missing/empty body yields a
bounded localized unavailable state. Use existing shell, typography and tokens.

## Acceptance

Check all twelve bodies, internal links/fragments, fixed-path/error and shared
renderer authority tests; browser language/topic/history/keyboard and 320px
containment; actual package inclusion and offline reading at final rebuild.

## Shared Language Option — 2026-11-06

The owner requested a website-style language option for the documentation area,
rather than per-article toggles. Place one current-language disclosure in the
shared Docs contents header. Keep the article heading/body free of language
controls. Preserve fixed `lang=ko|en` routes, Korean default, same-topic switching,
selected language across guide links/history, and the surrounding app's language.
Use native disclosure/link semantics; pointer/keyboard, Escape focus return,
outside dismissal and 320px containment are required. No stored preference, new
API, body rewrite or global application-language setting. Frontend refinement,
owned by [Run236](../run/run-20261106-236-docs-language-option.md).
