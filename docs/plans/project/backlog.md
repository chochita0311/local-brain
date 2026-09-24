# Project Backlog

This document tracks unresolved implementation work and decisions only. Completed history remains in its owning PRD, Feature, Spec, Run, Fix, or Evaluation artifact and in the [Artifact Catalog](../artifact-catalog.md). It intentionally excludes private source names, local absolute paths, ticket identifiers, copied conversations, and real session content.

Priority meaning:

- `P0`: required to protect private data or establish a safe source boundary
- `P1`: required for the intended Workstream workflow and reliable operation
- `P2`: important follow-up after the core workflow stabilizes

## Current Focus

The owner stopped further implementation and calculations after inspecting the
continuous map. The [design-plan handoff](../design/workflow-map-design-plan.md#handoff-to-next-track)
owns resumption; the open items below are not active jobs or newly approved work.

Inspection target: the
[relation-first inspection track](../design/workflow-map-design-plan.md#relation-first-inspection-track).
FEAT-0101's whole-history reader and FEAT-0102's map passed after real replay
verification, under the owner's continuous UI-delivery approval. The working
screen's freeform geometry was returned to planning in owner review. The current
[FEAT-0104](../feature/feat-0104-temporal-affinity-flow.md) correction now passes and makes actual
time the left-to-right axis with curved similarity strands and period inspection.
RUN-117 separates the continuous scrollable canvas from text-list pagination;
changing a list page no longer hides connections or resets the view.
FEAT-0103 remains an independent
draft relation trial, not a map prerequisite or an active job. The checkboxes
below own remaining work, not a routine classification queue.

Retained quality blocker:
[FEAT-0100's bounded extraction/binding trial](../feature/feat-0100-source-claim-extraction-and-binding-trial.md),
completed under RUN-112 with contract/replay PASS and semantic Functional FAIL.
All 28 extractions are protocol-rejected, conditioned binding fully passes 3/28,
and every end-to-end call is prerequisite-skipped. The output/evidence-interface
review produced the split above without repairing or relabeling these failures.
Original holdout stays unconsumed. Private relationship inference and replacement
still need quality evidence; affinity inspection needs its own data contract,
not a complete claim/state extractor.

Preceding foundation:
[FEAT-0099's source-claim/state-projection foundation](../feature/feat-0099-source-claims-and-work-state-projection.md)
passed under RUN-111. The owner approved its pure synthetic implementation; 50
tests and full 900-test regression pass (one optional skip). This establishes
state calculation given supplied claims/links, not the ability to extract them.
No new model trial or private processing is authorized by this PASS.

Admission boundary: [local work-context inference](../feature/feat-0098-local-work-context-inference.md),
approved on 2026-09-23 after distinguishing semantic affinity from workflow
continuity. Installation and runtime checks passed; the development quality gate
failed on goal omission and incomplete grounding. The owner approved the
same-model reasoning/staged comparison in RUN-105; it is now complete and both
candidates fail admission (3/4 and 2/4 automated cases, plus field-level semantic
errors). Holdout remains untouched and private whole-history execution is blocked.
The approved Qwen3-8B comparison in RUN-106 is now complete and admission-blocked:
thinking passes 1/4 cases and staging 2/4, with time/shape/grounding and abstention
failures. The owner approved the extraction/protocol redesign in RUN-107, retaining
the same synthetic expectations and separate semantic review. No additional model,
embedding recomputation or private job belongs to this continuation.
RUN-107 is complete and blocked on semantic extraction: its bounded variants
pass 3/4, 2/4 and 3/4 content cases, with omissions or fragmented/misassigned work.
That comparison ended without an admitted candidate or ongoing computation.
Retain the existing full-population vectors and the earlier sampled comparator;
model trial, actual corpus reconstruction and time-oriented UI are distinct gates.
The owner-requested [method review](../research/workflow-reconstruction-method-review.md)
is complete. The owner then approved its fixed-model diagnostic under
[RUN-108](../run/run-20260923-108-work-context-protocol-diagnostic.md), now passed
for diagnostic completeness only: 288 conditions plus zero-generation replay.
Order/code sensitivity and unsupported continuity both remain; switching answer
format alone does not admit an extractor. The owner-approved evidence-first
follow-up in [RUN-109](../run/run-20260923-109-evidence-first-work-context.md) is
now complete: original development passes 3/4, new composition 4/12. Field-role
confusion and false continuation survive same-model audits. Both gates fail;
failure-preserving replay passes. The next proposed decision was a matched
direct-role versus independent-property comparison on new frozen controls,
not more self-approval layers, training or another model. The owner has now
approved that diagnostic under
[RUN-110](../run/run-20260923-110-work-role-formulation-comparison.md), now complete.
Direct roles pass 15/32 order conditions versus 8/32, but only 6/16 contexts in both
orders; omissions, stale pending state and false continuity prevent admission.
Stop prompt/choice variants. The subsequent approved contract review separates
source claims from current-state reconciliation of a supported target; FEAT-0099
above owns the resulting passed pure foundation.
Production work-area grouping remains downstream. Full-history affinity
inspection has now been delivered independently through the passed boundaries above.
FEAT-0098's model admission is still blocked; RUN-112 above owns the completed
failed candidate, not an automatic private job or another trial.

This section is a priority projection only. Completion state is owned by the
single linked checkbox in the detailed backlog below.

- [Resolve the remaining work-identity and relation-quality gaps](#automatic-work-reconstruction)
  only after resumption; the full-history reader and temporal map are delivered.
  Preserve the delivered
  [Auto Work inspection UI](../feature/feat-0096-auto-work-inspection.md) as a
  labeled earlier sampled comparator. Keep the passed
  [Session Workflow Focus](#workflow-focus-real-use-review) as supporting evidence.
- [Reconcile historical paths and repository identity](#path-and-repository-identity).
- Improve [source-aware matching](#source-aware-matching) and
  [batch Suggestion review](#batch-suggestion-review) as connected source use
  expands.

## P0 - Privacy And Repository Boundary

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

- [ ] Validate the replacement's outcome-level flow and subordinate activity
  against source roles and optional user corrections; do not require the owner
  to maintain Workstream/Thread containers before value.
- [ ] Define safe treatment of existing Workstream/Thread merge, split, archive,
  move, and restore needs in the controlled transition; do not independently
  build more manual organization UI from this legacy backlog item.
- [ ] Complete [time-bounded legacy retention and retirement](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#legacy-transition-boundary)
  during replacement development: fix retention/expiry and cleanup scope,
  transfer still-needed data, verify ownership and consumers, then retire
  eligible unused/orphaned data, obsolete tables, and expired backups. Verify
  integrity and reclaimed storage; keep a minimal cleanup record, not permanent
  full copies. This is a transition-level decision, not per-record confirmation.
<a id="workflow-focus-real-use-review"></a>

- [ ] Exercise the passed
  deterministic Session Workflow Focus and boundary corrections across
  multiple real efforts and repeated context switches; record where the
  reconstructed story or correction choices are insufficient.

<a id="workstream-candidate-next-boundary"></a>
<a id="automatic-work-reconstruction"></a>

- [ ] Decide the independent [FEAT-0103 direct-context relation trial](../feature/feat-0103-direct-context-work-relation-trial.md)
  boundary: one frozen candidate with semantic gates and a stop rule. Preserve
  FEAT-0098/0100 failures and their original holdout. A PASS permits proposing
  real-context retrieval/relation validation, not automatic corpus or UI work.
- [ ] Establish full-history work-area/effort identity and supported temporal
  relationships after the relevant quality evidence, without a 60-Session cap.
  This includes recognizable purpose-based names, compatible work across long
  gaps, and justified separation or integration beyond nested similarity groups.
  Detailed lifecycle reconstruction remains deferred; a failed model gate never
  becomes a request to approve every classification. Pure supplied-input state
  projection and synthetic pair success do not establish end-to-end identity.
- [ ] Define and implement incremental product updates for newly imported or
  changed Sessions after identity/quality admission. Explicit replay and vector
  reuse already exist; automatic scheduling, stable identity reconciliation and
  product refresh do not. Browsing must remain passive and require no routine
  membership confirmation.
- [ ] Complete scoped local validation of [FEAT-0095's approved reconstruction experiment](../feature/feat-0095-bounded-work-reconstruction-experiment.md).
  The extractor/comparator, independent scorer, and read-only command have
  synthetic technical evidence in RUN-20260915-101. The owner selected current
  data through now; bounded preparation and unassessed private execution passed.
  Independent expectations/quality remain missing, so Feature/Run stay blocked.
  Prepare assessment without predicting the answer key or requiring whole-sample
  manual organization, then measure local quality under the frozen caps.
  FEAT-0091–0094 remain superseded; unrun/partial evidence is not viability or
  production/UI authority. No legacy cleanup belongs to this experiment.
- [ ] Track Resource freshness, last verification time, evidence, confidence, and review state separately.
<a id="path-and-repository-identity"></a>

- [ ] Add historical path aliases and
  repository identity reconciliation so moved folders and renamed repositories
  retain mappings; canonicalize and deduplicate current file paths and
  repository remotes alongside tickets, wiki pages, and conversation messages.
- [ ] Preserve many-to-many Session and Document mappings with relationship-specific evidence.
- [ ] Preserve shared versus activity-specific Resource meaning in the
  replacement and legacy mapping without making manual Thread ownership a
  prerequisite.
- [ ] Define checkpoint supersession and comparison semantics.
- <a id="schema-audit-timestamp-contract"></a>[ ] Define one canonical UTC timestamp storage, parsing, precision, comparison, and legacy-preservation contract before normalizing mixed source, Python ISO, and SQLite timestamp text identified by FEAT-0029.
- <a id="schema-audit-closed-vocabularies"></a>[ ] Decide and stage migration-safe physical `CHECK` constraints for the remaining bounded schema vocabularies. Preserve the passed PRD-0009 and FEAT-0057/FEAT-0061 executable value-registry contract; this item owns only the deferred physical schema changes.

## P1 - Local Contexts

- [ ] Add lazy directory expansion, pagination, and incremental scanning for large source trees.
- [ ] Show source health, last scan, changed files, extraction failures, and re-scan controls per source.
- [ ] Improve PDF extraction beyond Spotlight and support common readable document formats and attachments.
- [ ] Handle Apple Notes nested folders, duplicate titles, account changes, protected notes, attachments, and deletions.
- [ ] Add text search and filters within a selected source while preserving its tree.
- [ ] Decide how removed sources retain historical relationships while appearing unavailable.

## P1 - Sessions And Retrieval

- [ ] Validate Claude and Codex parsers against format changes and malformed or partially written JSONL.
- [ ] Decide which additional subagent metadata is useful without importing nested events.
- [ ] Decide which tool-result fields are valuable enough to index without adding opaque payload noise or excessive volume.
<a id="source-aware-matching"></a>

- [ ] Improve source-aware matching and
  explain why each Session or Document was suggested.

<a id="batch-suggestion-review"></a>

- [ ] Add batch review, filters, sorting,
  and clear pending, accepted, rejected, restored, and superseded states.
- [ ] Measure retrieval precision and missed-resource rates with synthetic local fixtures before changing ranking rules.

## P1 - External Sources

- [ ] Add conversation message and thread references with permalink, participants, location, timestamp, and bounded excerpts.
- [ ] Add Git commits, branches, pull requests, changed files, and repository identity as first-class Resources.
- [ ] Define remaining connector-specific refresh, authentication failure, caching, and content deletion behavior beyond the passed Atlassian contract.
- [ ] Add hard MCP call-count enforcement for legacy Workstream gap filling; its prompt budget remains advisory and is audited after calls occur.

## P1 - Task Runner

- [ ] Add a durable Run queue with concurrency limits, restart recovery, timeouts, and orphan-process detection.
- [ ] Make the exact prompt, manifest fingerprint, MCP budget, model, cwd, and tool policy inspectable before execution.
- [ ] Separate local retrieval, external gap filling, synthesis, and review into visible Run stages.
- [ ] Add cancellation and shutdown tests proving child processes do not survive unexpectedly.

## P2 - Reading And Context Polish

- <a id="markdown-image-and-attachment-rendering"></a>[ ] Add safe Markdown image and attachment rendering after PRD-0006's core text and Obsidian-syntax reader stabilizes, covering source-contained relative assets, missing files, root-escape rejection, remote-loading policy, responsive containment, and safe fallbacks for unsupported embeds.

## P2 - Dashboard And Workflow

- [ ] Replace generic counts with a current-work view of Thread state, recent changes, blockers, next actions, and stale checkpoints.
- [ ] Show cross-source evidence and freshness without copying full sensitive content into overview screens.
- [ ] Add editable priorities, due signals, archive state, and a daily review flow.
- [ ] Visualize how Sessions and Resources contributed to each Thread over time.
- [ ] Add a structuring inbox for unassigned Sessions, documents, and external Resources.
- [ ] Define Session-derived workflow and skill metrics that are useful without incentivizing raw activity volume.

## P2 - Quality And Distribution

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

- [ ] Whether full source text stays in SQLite, is stored only as searchable excerpts, or is read from the original source on demand.
- [ ] Which external metadata may be persisted under applicable policy and which must remain ephemeral.
- [ ] Whether AI summaries are local-only, use an approved model path, or require per-Run confirmation.
- [ ] Whether LocalBrain remains single-user local software or eventually supports encrypted sync or team sharing.
- [ ] What evidence threshold permits an automatic Suggestion instead of requiring manual search.
- [ ] Whether initial topic analysis should use deterministic rules, a local model, or an approved model.
- [ ] Which minimum checkpoint fields provide enough resume value without becoming a documentation burden.
