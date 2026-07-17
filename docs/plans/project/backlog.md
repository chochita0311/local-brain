# Project Backlog

This document tracks unresolved implementation work and decisions. It intentionally excludes private source names, local absolute paths, ticket identifiers, copied conversations, and real session content.

Priority meaning:

- `P0`: required to protect private data or establish a safe source boundary
- `P1`: required for the intended Workstream workflow and reliable operation
- `P2`: important follow-up after the core workflow stabilizes

## Current Focus

- [ ] Exercise multiple real Workstreams through repeated context switches and record model gaps locally.
- [ ] Build the unified cross-source Workstream timeline.
- [ ] Add historical path aliases and repository identity reconciliation.
- [ ] Improve source-aware matching and batch Suggestion review before external ingestion.

## P0 - Privacy And Repository Boundary

- [x] Store the SQLite database and Run artifacts outside the source repository by default.
- [x] Ignore databases, JSONL histories, exports, logs, environment files, and local workflow context as a fallback guard.
- [x] Add a repository privacy scanner and pre-commit gate for local paths, common secrets, work URLs, runtime files, and unreviewed media.
- [ ] Run the repository privacy scanner in CI before connecting or publishing to an external remote.
- [ ] Define an export workflow with destination confirmation, content preview, and redaction options.
- [ ] Add per-source delete, purge, and re-index operations that distinguish index removal from original-source deletion.
- [ ] Decide whether database encryption at rest is required and, if so, keep keys in macOS Keychain.
- [ ] Define backup, restore, schema migration, and database corruption recovery procedures.
- [ ] Ensure logs and error pages omit note bodies, Session excerpts, credentials, and full prompts by default.
- [ ] Replace private data in tracked test fixtures and screenshots with generated examples.

## P0 - Source Safety And Consent

- [ ] Make every source opt-in and show exactly which paths, note accounts, or external scopes are indexed.
- [ ] Add source-level exclusions for directories, file patterns, note folders, and individual documents.
- [ ] Surface macOS Automation permission state for Apple Notes and explain how to revoke it.
- [ ] Define retention and freshness rules independently for source metadata, extracted text, matches, and Run evidence.
- [ ] Record field-level provenance where needed so summaries and relationships can be traced to source evidence.

## P1 - Information Model

- [ ] Validate the boundary between Workstream, Thread, Project, Context Source, Document, Session, and external Resource through daily use.
- [ ] Add Workstream and Thread merge, split, archive, move, and restore operations without losing history.
- [ ] Build a unified Workstream timeline across Sessions, documents, Git, tickets, wiki pages, and conversations.
- [ ] Track Resource freshness, last verification time, evidence, confidence, and review state separately.
- [ ] Canonicalize and deduplicate file paths, repository remotes, tickets, wiki pages, and conversation messages.
- [ ] Preserve many-to-many Session and Document mappings with relationship-specific evidence.
- [ ] Keep shared Workstream Resources distinct from Thread-specific Resources in the model and review UI.
- [ ] Define checkpoint supersession and comparison semantics.

## P1 - Local Contexts

- [ ] Add lazy directory expansion, pagination, and incremental scanning for large source trees.
- [ ] Show source health, last scan, changed files, extraction failures, and re-scan controls per source.
- [ ] Improve PDF extraction beyond Spotlight and support common readable document formats and attachments.
- [ ] Handle Apple Notes nested folders, duplicate titles, account changes, protected notes, attachments, and deletions.
- [ ] Add text search and filters within a selected source while preserving its tree.
- [ ] Decide how removed sources retain historical relationships while appearing unavailable.
- [ ] Add historical path aliases so moved folders and renamed repositories keep existing mappings.

## P1 - Sessions And Retrieval

- [ ] Validate Claude and Codex parsers against format changes and malformed or partially written JSONL.
- [x] Expose lazy subagent exploration under the parent Session without counting it as ordinary activity.
- [ ] Decide which additional subagent metadata is useful without importing nested events.
- [ ] Decide which tool-result fields are valuable enough to index without adding opaque payload noise or excessive volume.
- [ ] Improve source-aware matching and explain why each Session or Document was suggested.
- [ ] Add batch review, filters, sorting, and clear pending, accepted, rejected, restored, and superseded states.
- [x] Keep candidate counts uncapped while avoiding repeated parsing through fingerprints, incremental indexes, and cached evidence.
- [ ] Measure retrieval precision and missed-resource rates with synthetic local fixtures before changing ranking rules.

## P1 - External Sources

- [ ] Design Atlassian navigation and ownership for tickets, watched work, pages, spaces, and topic grouping.
- [ ] Implement read-only Jira and Confluence ingestion through the approved MCP Gateway with durable provenance.
- [ ] Add conversation message and thread references with permalink, participants, location, timestamp, and bounded excerpts.
- [ ] Add Git commits, branches, pull requests, changed files, and repository identity as first-class Resources.
- [ ] Define connector refresh, authentication failure, caching, and content deletion behavior.
- [ ] Enforce MCP call limits through a gateway or broker; the current prompt budget is advisory and audited after calls occur.

## P1 - Task Runner

- [ ] Add a durable Run queue with concurrency limits, restart recovery, timeouts, and orphan-process detection.
- [ ] Make the exact prompt, manifest fingerprint, MCP budget, model, cwd, and tool policy inspectable before execution.
- [ ] Separate local retrieval, external gap filling, synthesis, and review into visible Run stages.
- [x] Add retry and refresh behavior that preserves accepted and rejected decisions while replacing eligible pending Suggestions.
- [x] Verify that maintenance Runs and artifacts cannot be re-imported as ordinary Sessions or Local Context documents.
- [ ] Add cancellation and shutdown tests proving child processes do not survive unexpectedly.

## P2 - Dashboard And Workflow

- [ ] Replace generic counts with a current-work view of Thread state, recent changes, blockers, next actions, and stale checkpoints.
- [ ] Show cross-source evidence and freshness without copying full sensitive content into overview screens.
- [ ] Add editable priorities, due signals, archive state, and a daily review flow.
- [ ] Visualize how Sessions and Resources contributed to each Thread over time.
- [ ] Add a structuring inbox for unassigned Sessions, documents, and external Resources.
- [ ] Define cavemem-style metrics that are useful without incentivizing raw activity volume.

## P2 - Quality And Distribution

- [ ] Add browser-level tests for Workstream, Thread, source browsing, Suggestion review, and Run workflows.
- [ ] Build a synthetic graphical regression matrix for the current screen families at `1440`, `920`, `700`, and `320`, covering representative long-content, empty, unavailable, error, and active-interaction states without tracking private runtime content.
- [ ] Add performance tests using large synthetic Session and document sets.
- [ ] Audit keyboard navigation, focus, contrast, empty states, long text, and narrow viewports.
- [ ] Add a default `<meta name="description">` to the shared server-rendered shell and recheck Lighthouse SEO.
- [ ] Add structured migrations and release compatibility checks before distributing builds.
- [ ] Decide between Tauri, Electron, or a signed launcher after the localhost MVP stabilizes.
- [ ] Package, sign, notarize, and document macOS permissions without broad filesystem entitlements.
- [ ] Add controlled startup and reliable shutdown for an app-icon launch experience.

## Open Decisions

- [ ] Whether full source text stays in SQLite, is stored only as searchable excerpts, or is read from the original source on demand.
- [ ] Which external metadata may be persisted under applicable policy and which must remain ephemeral.
- [ ] Whether AI summaries are local-only, use an approved model path, or require per-Run confirmation.
- [ ] Whether LocalBrain remains single-user local software or eventually supports encrypted sync or team sharing.
- [ ] What evidence threshold permits an automatic Suggestion instead of requiring manual search.
- [ ] Which parts of cavemem's schema or behavior should remain compatible.
- [ ] Whether initial topic analysis should use deterministic rules, a local model, or an approved model.
- [ ] Which minimum checkpoint fields provide enough resume value without becoming a documentation burden.
