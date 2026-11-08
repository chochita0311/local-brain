# SPEC-0165: Reading Query Efficiency And Title Caret

- Status: `approved`
- Feature: [FEAT-0165](../feature/feat-0165-reading-query-efficiency-and-title-caret.md)
- Profile: `fullstack-product`; lanes: contract/backend, frontend, docs.

1. Title pointer activation maps the rendered text position to a collapsed input
   caret. Keyboard activation remains usable without selecting the full title.
   Hover and editing use existing semantic surface/focus roles without changing
   row geometry. Preserve save/clear/cancel/error/pending/IME behavior and links.
2. Keyword FTS admission, root identity, private-runtime exclusions, snippet,
   score/order and post-admission limit remain exact. Read Session owners in
   bounded batches rather than per result; never limit away allowed later hits.
3. Chart uses metadata when either timestamp parses. Only when both fail, fetch
   retained event timestamps in batches; parse in Python with existing UTC rules,
   preserve min/max and source labels, and read no bodies.
4. Visible Usage candidates retain ordinary raw-date windows plus all exceptional
   timestamps outside them. Preserve lexical row order and ID tie order, UTC
   filtering, untimed counts, Decimal addition order/precision, maintenance and
   synthetic exclusions, frozen attribution and every public result field.
   Use existing indexes and bounded processing; no persisted cache or schema change.
5. Atlassian detail reads only the requested item's joined body/metadata before
   applying the same projection, classifications, evidence and memberships.
6. Prove parity with frozen baseline functions on synthetic and read-only local
   snapshots; query counts/plans and elapsed times support bounded improvements.
   Verify actual title pointer and keyboard interactions, wide/narrow geometry,
   failures and first state. Real Notion inspection is separate from inference;
   if permissions remain absent, report that limit without claiming observation.
7. Update owning policies/app instructions and required generated artifacts; run
   appropriate focused checks, required full suite/privacy and browser checks.
