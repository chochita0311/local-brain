# SPEC-0163: Session Display Titles

- Status: `approved`
- Feature: [FEAT-0163](../feature/feat-0163-session-display-titles.md)
- Profile: `fullstack-product`; screen-alignment mode: `extend`.

1. `display_title TEXT` is nullable with no implicit non-null default, physically
   after `title`. Back up legacy DBs before rebuilding column order. Preserve
   every existing column, ID, FK, descendant, pin, reference and frozen Usage row.
   Repeated initialization is a no-op. Unexpected schema/data must not be lost.
2. Source ingestion owns `title`; local title updates own only `display_title`.
   Trim surrounding whitespace; blank means SQL NULL. Admit a single-line text
   override up to 500 characters. Eligibility is an existing primary work Session.
3. Local same-origin POST validates payload and returns confirmed source,
   override and effective titles. Storage failure must retain the prior title.
4. List and primary detail titles open a same-style text input on click or
   keyboard activation. Enter/blur saves; Escape cancels; composition Enter must
   not save. Pending saves prevent conflicting edits. Failed saves retain draft
   and bounded retry feedback. Blank successful save restores the source title.
5. Title controls remain outside destination anchors. Preserve row/detail
   typography, metadata geometry, pin/child controls, query/filter/page and scroll.
   Success updates matching visible titles and pinned recall without reordering.
   Native form fallback remains usable without JavaScript.
6. Session list/detail/parent/child and pinned labels use override when present;
   Chart projects the same effective title. Source title, native files and
   source-backed search content remain unchanged. Lazy unpersisted children keep
   their source title and have no editor.
7. Check actual rendered wide/narrow states, keyboard/IME, cancellation, clear,
   storage failure, refresh persistence and sync preservation. No native rebuild.
