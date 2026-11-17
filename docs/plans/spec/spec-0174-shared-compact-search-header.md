# SPEC-0174: Shared Compact Search Header

- Status: `approved`
- Feature: [FEAT0174](../feature/feat-0174-shared-compact-search-header.md)
- Profile: `frontend-product`; frontend → integration/docs.

The shared stylesheet owns header height48px and search label typography/compact
block padding. Terminal inherits these rather than overriding the same values.
Keep narrow40px controls, desktop/native titlebar offsets and each route's own
content layout. No JavaScript behavior, route, query, data or process contract changes.

Use the existing synthetic toolbar/navigation browser checks, extending geometry
observations across sidebar routes, viewport sizes and native-toolbar classes.
Check Sessions/Dashboard search and history controls, Terminal containment and
layout, final asset packaging, and reflect new CSS in the development host.
Keep earlier native IME/AX/physical acceptance limits explicit. Record current
Codex project/folder findings as research, without silently adding a new schema.
