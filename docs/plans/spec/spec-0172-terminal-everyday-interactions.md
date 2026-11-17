# SPEC-0172: Terminal Everyday Interactions

- Status: `approved`
- Feature: [FEAT0172](../feature/feat-0172-terminal-everyday-interactions.md)
- Run: [Run253](../run/run-20261113-253-terminal-everyday-interactions.md)
- Profile: `fullstack-product`; host contract/frontend/integration/docs.

Use existing manager operations for hide/show/rename/scoped termination. Do not
alter Node or Rust protocol/manifest/build identity. GUI retirement applies only
to confirmed exited records without cleanup/input errors, independent of exit code, through the single-ID
stop API with an optional observed generation forwarded to Rust. Retain genuine
failure records. Observational HTTP reads never retire a process or create files.

Add a private presentation order cache beside the terminal scope, containing
only schema, generation and ordered tab IDs. Host code owns this UI preference,
separate from execution state and generic settings. Validate the supplied generation
and exact ID membership against the observed manager snapshot before atomic publication; last committed write
wins. Reads append new IDs and ignore stale generations. Manager metadata and this
presentation cache do not share a transaction; later manager changes reconcile
through generation tags and current membership, without executing any process action. Invalid/unavailable
presentation state must not disable unrelated terminal controls. Respect private
owner/mode/no-link/bounds checks; never accept a browser-supplied filesystem path.

Extend the existing compact frame with stable per-task menus and inline title
editing. Preserve editor draft/menu/focus through periodic state updates, close
peer menus on outside click/Escape and use reachable keyboard actions. Reorder
only within the folder, preserve hidden tab positions, rollback unconfirmed
order on save failure and keep existing terminal views alive while dragging.
Use shared component tokens and existing Sessions editor interaction conventions.

Actual browser tests must exercise zero/nonzero shell exit, background/reopen,
task menus, inline edit/IME cancellation/failure, actual mouse reorder/reload,
keyboard reorder and individual close with no dialog. Retain bulk confirmation,
generation safety, plain-shell unknown state and background process continuity.
Build the app with the same runtime payload and record native evidence limits.
