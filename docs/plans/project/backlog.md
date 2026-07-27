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
- [ ] Improve source-aware matching and batch Suggestion review as connected source use expands.

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
- [x] Review and approve the revised PRD-0003 before establishing the 20-table plus FTS5 baseline, eight subject-area catalogs, local Mermaid contract, `System > Schema` explorer, incremental schema-update guide, or wider schema cleanup.
- [ ] Add Workstream and Thread merge, split, archive, move, and restore operations without losing history.
- [ ] Build a unified Workstream timeline across Sessions, documents, Git, tickets, wiki pages, and conversations.
- [ ] Track Resource freshness, last verification time, evidence, confidence, and review state separately.
- [ ] Canonicalize and deduplicate file paths, repository remotes, tickets, wiki pages, and conversation messages.
- [ ] Preserve many-to-many Session and Document mappings with relationship-specific evidence.
- [ ] Keep shared Workstream Resources distinct from Thread-specific Resources in the model and review UI.
- [ ] Define checkpoint supersession and comparison semantics.
- <a id="schema-audit-timestamp-contract"></a>[ ] Define one canonical UTC timestamp storage, parsing, precision, comparison, and legacy-preservation contract before normalizing mixed source, Python ISO, and SQLite timestamp text identified by FEAT-0029.
- <a id="schema-audit-closed-vocabularies"></a>[x] Use passed PRD-0009 and FEAT-0057/FEAT-0061 to define executable physical, logical, fallback, presentation, and consumer ownership for bounded schema vocabularies. Later physical `CHECK` additions remain separate schema changes and must preserve the registry contract.

## P1 - Local Contexts

- [x] Execute FEAT-0058 and FEAT-0059: persist row-presence Session pins and replace the Sessions `최근 Context` summary with explicit Pinned Sessions recall.
- [ ] Add lazy directory expansion, pagination, and incremental scanning for large source trees.
- [ ] Show source health, last scan, changed files, extraction failures, and re-scan controls per source.
- [ ] Improve PDF extraction beyond Spotlight and support common readable document formats and attachments.
- [ ] Handle Apple Notes nested folders, duplicate titles, account changes, protected notes, attachments, and deletions.
- [ ] Add text search and filters within a selected source while preserving its tree.
- [ ] Decide how removed sources retain historical relationships while appearing unavailable.
- [ ] Add historical path aliases so moved folders and renamed repositories keep existing mappings.

## P1 - Sessions And Retrieval

- [ ] Validate Claude and Codex parsers against format changes and malformed or partially written JSONL.
- [x] Pass FEAT-0058 and FEAT-0059 for row-presence Session pin persistence, stable inventory controls, and Pinned Sessions recall.
- [x] Pass FEAT-0060 for deterministic Session-related context based only on existing local relationships.
- [x] Expose lazy subagent exploration under the parent Session without counting it as ordinary activity.
- [ ] Decide which additional subagent metadata is useful without importing nested events.
- [ ] Decide which tool-result fields are valuable enough to index without adding opaque payload noise or excessive volume.
- [ ] Improve source-aware matching and explain why each Session or Document was suggested.
- [ ] Add batch review, filters, sorting, and clear pending, accepted, rejected, restored, and superseded states.
- [x] Keep candidate counts uncapped while avoiding repeated parsing through fingerprints, incremental indexes, and cached evidence.
- [ ] Measure retrieval precision and missed-resource rates with synthetic local fixtures before changing ranking rules.

## P1 - External Sources

- [x] Design Atlassian navigation and ownership for tickets, Pages, projects, Spaces, freshness, local Topics/Tags, and explicit refresh.
- [x] Implement local Jira and Confluence source memory, durable provenance, URL-first setup, bounded refresh preparation, and source-neutral result application.
- [x] Complete FEAT-0053's bounded connected validation: official Jira metadata read passed; official Confluence and company Gateway were classified as current host environment limitations without fabricating end-to-end evidence.
- [ ] Add conversation message and thread references with permalink, participants, location, timestamp, and bounded excerpts.
- [ ] Add Git commits, branches, pull requests, changed files, and repository identity as first-class Resources.
- [ ] Define remaining connector-specific refresh, authentication failure, caching, and content deletion behavior beyond the passed Atlassian contract.
- [x] Enforce external-sync request limits and read authorization before host dispatch; selected Atlassian refreshes are hard-capped at 20 calculated reads.
- [ ] Add hard MCP call-count enforcement for legacy Workstream gap filling; its prompt budget remains advisory and is audited after calls occur.

## P1 - Task Runner

- [ ] Add a durable Run queue with concurrency limits, restart recovery, timeouts, and orphan-process detection.
- [ ] Make the exact prompt, manifest fingerprint, MCP budget, model, cwd, and tool policy inspectable before execution.
- [ ] Separate local retrieval, external gap filling, synthesis, and review into visible Run stages.
- [x] Add retry and refresh behavior that preserves accepted and rejected decisions while replacing eligible pending Suggestions.
- [x] Verify that maintenance Runs and artifacts cannot be re-imported as ordinary Sessions or Local Context documents.
- [x] Connect every in-app Task Runner Run to the selected persisted native Claude or Codex Maintenance Session and normalize native Usage Records without work-count or retrieval leakage; existing Workstream tasks remain Claude-only, while external synchronization is runner-neutral and the Runner stream remains console/result evidence only.
- [ ] Add cancellation and shutdown tests proving child processes do not survive unexpectedly.

## P2 - Reading And Context Polish

- <a id="markdown-image-and-attachment-rendering"></a>[ ] Add safe Markdown image and attachment rendering after PRD-0006's core text and Obsidian-syntax reader stabilizes, covering source-contained relative assets, missing files, root-escape rejection, remote-loading policy, responsive containment, and safe fallbacks for unsupported embeds.

## P2 - Dashboard And Workflow

- [x] Implement PRD-0004's source-neutral Usage Records, immutable trend-cost snapshots, activity and Project attribution contracts, summary/history, and composition/trust; the later human review retired the visible current-month projection.
- [x] Complete RUN-20260718-25 as the superseded first repair: replace Codex latest-per-turn usage, align Claude's bounded cache-create fallback, version normalizer contracts, and prove automatic source-level repair without a reset button.
- [x] Complete RUN-20260718-26: prefer Codex `last_token_usage`, use cumulative subtraction only as fallback, exclude spawned or forked replay prefixes, resolve dated fallback models, add the approved `fast` trend-price snapshot, and refresh the private local Fact set idempotently.
- [x] Complete RUN-20260718-27: add immutable model-specific long-context thresholds and rates, calculate the tier per Codex Fact, repair the private Fact set, and match fixed-boundary ccusage monthly cost without a runtime dependency.
- [x] Complete RUN-20260718-28: remove the `Projected month end` presentation and dedicated styles while preserving the cost read model, selected-period metrics, and scope-switch continuity.
- [x] Complete RUN-20260718-29: retain Claude `<synthetic>` pseudo-message Facts and Session evidence in SQLite while excluding them from every Sessions Dashboard usage date, total, coverage, breakdown, and Session-count consumer.
- [ ] Replace generic counts with a current-work view of Thread state, recent changes, blockers, next actions, and stale checkpoints.
- [ ] Show cross-source evidence and freshness without copying full sensitive content into overview screens.
- [ ] Add editable priorities, due signals, archive state, and a daily review flow.
- [ ] Visualize how Sessions and Resources contributed to each Thread over time.
- [ ] Add a structuring inbox for unassigned Sessions, documents, and external Resources.
- [ ] Define Session-derived workflow and skill metrics that are useful without incentivizing raw activity volume.

## P2 - Quality And Distribution

- [x] Pass [PRD-0008](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md) child Features: FEAT-0053 connected validation, FEAT-0054 Add flow, FEAT-0055 ELK routing contract, and FEAT-0056 adoption.
- [x] Pass [PRD-0009](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md) child Features: FEAT-0057 value dictionaries, FEAT-0058 pin persistence, FEAT-0059 pinned recall, FEAT-0060 related context, and FEAT-0061 visible-consumer normalization.
- [x] Close PRD-0004's combined Sessions Dashboard rendered evidence gap at `1440`, `920`, `700`, and exact mobile-emulated `320`, covering scope controls, four-metric band, 30-day chart scrolling, long Model/Project labels, native disclosures, trust states, and in-place scroll continuity with synthetic data.
- [ ] Close FEAT-0019's direct rendered evidence gap at `1440`, `700`, and `320`, including selector geometry, same-row containment, and the Session-only source summary.
- [ ] Capture the Sessions `동기화` working, success, failure, focus, and scope-preservation states from a browser after a warm-cache revisit; versioned assets, local HTTP synchronization, and human PRD-0002 acceptance are complete, so this is non-blocking regression evidence.
- [ ] Add an official `localbrain serve` CLI subcommand with default host and port, an opt-in development reload flag, and a documented install/run-from-anywhere path so personal shell aliases are not required.
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

- [x] Use `Subsession` as the single source-neutral LocalBrain product term for child Session records; retain `subagent` only in source-native Claude/Codex formats, redirect-only legacy URLs, and agent-orchestration prompts.
- [ ] Whether full source text stays in SQLite, is stored only as searchable excerpts, or is read from the original source on demand.
- [ ] Which external metadata may be persisted under applicable policy and which must remain ephemeral.
- [ ] Whether AI summaries are local-only, use an approved model path, or require per-Run confirmation.
- [ ] Whether LocalBrain remains single-user local software or eventually supports encrypted sync or team sharing.
- [ ] What evidence threshold permits an automatic Suggestion instead of requiring manual search.
- [ ] Whether initial topic analysis should use deterministic rules, a local model, or an approved model.
- [ ] Which minimum checkpoint fields provide enough resume value without becoming a documentation burden.
