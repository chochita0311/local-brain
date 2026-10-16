# RUN-161: Session Parsing And Search Closeout

## Metadata

- ID: `run-20261016-161`
- Status: `passed`
- Related Features: [FEAT-0018](../feature/feat-0018-conversation-focused-session-details.md), [FEAT-0070](../feature/feat-0070-usage-source-scope-and-composition.md), [FEAT-0120](../feature/feat-0120-parallel-natural-search.md)
- Reference Specs: [SPEC-0015](../spec/spec-0015-session-subsession-source-contract.md), [SPEC-0018](../spec/spec-0018-conversation-focused-session-details.md), [SPEC-0070](../spec/spec-0070-usage-source-scope-and-composition.md), [SPEC-0120](../spec/spec-0120-parallel-natural-search.md)
- Current Contract: owner-approved corrections recorded below; the [2026-10-16 PRD decision](../prd/prd-0020-local-natural-language-search.md#current-search-entry--2026-10-16) and [search policy](../../policies/project/natural-language-search.md#product-surface) supersede only the reference specs' parallel-header and ordinary keyword-navigation clauses. Other reference contracts and historical evidence limits remain applicable within the recorded correction scope.
- Parent PRD: [PRD-0002](../prd/prd-0002-session-browsing-and-subsession-organization.md), [PRD-0004](../prd/prd-0004-session-usage-and-cost-dashboard.md), [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Execution Profile: `fullstack-product`, `docs-content`
- Required Evaluators: contract, functional, design; independent docs-structuring and docs-shaping review
- Created: `2026-10-16`

## Authorized Scope And Publication Boundary

The owner requested the current session's corrections, an overall reconciliation,
independent subagent reviews using docs-structuring and docs-shaping, verification,
commit and push. This Run records that cross-feature closeout and the owner's
bounded follow-up decisions; it opens no new product increment.

Publish common implementation, durable contracts, synthetic regression fixtures
and this bounded receipt. Native conversations, restored rollouts, model/index
files, local configuration, real Session IDs, machine inventories and raw private
observations remain outside Git. Source recovery and duplicate-file removal were
separately authorized local operations.

## Changes And Evidence Owners

| Area | Established behavior | Owner |
| --- | --- | --- |
| Codex conversation repair | Preserve all authored inputs in a turn, including the initial question and later replies; filter recognized generated context by content block, preserve malformed/quoted examples, and retain distinct user-counterpart and assistant-turn precedence rules. Confirmed-empty siblings cannot retire a shared meaningful owner, including skill-only sources. | [Session lifecycle](../../policies/project/data-model/workspace-and-session-activity.md#sessions), parser and Sync regression fixtures |
| Question-reply transport | Read recognized question/answer batches as quoted questions and authored answers in order; keep transport IDs in source JSONL and retain unknown/malformed payloads without lossy interpretation. | Same Session lifecycle and Codex parser |
| Completion framing | Retain explicit Codex phases and Claude end_turn/tool_use evidence. Share Claude signals only within the same native message ID; absent, ambiguous, conflicting, malformed and error signals remain unmarked. Additive nullable migration and versioned Session reparse preserve stable identities and unchanged Usage snapshots. | [Activity Events](../../policies/project/data-model/workspace-and-session-activity.md#activity_events), value dictionary and schema manifest |
| Conversation presentation | User inputs have a very pale information tint, stronger speaker name and left accent; completed assistant responses have a neutral perimeter without an added completion label or task-success claim. Commentary retains its ordinary treatment for Claude and both Codex source profiles. | [Design Constitution](../../policies/design/design-constitution.md#detail-and-read), shared conversation template |
| Session identity and copy | Lead the metadata strip with Session ID, abbreviate from eight characters and extend on distinct-ID collisions. Copy the complete ID with button-anchored hover/result feedback, independent two-second copied state, bounded placement, stale-attempt protection and selectable failure recovery. | [Architecture](../../policies/project/architecture.md), design rules and shared browser assets |
| Usage history and disclosure | Use the first/last positive selected-metric buckets when present for every source and Daily/Weekly/Monthly/Cumulative view; retain internal zero periods and selected-range totals, and keep requested bounds when no positive bucket exists. Expanded composition places Show less after the additional rows. | [Architecture](../../policies/project/architecture.md), usage read model and responsive CSS |
| Unified search entry | Preserve the original header placeholder in one accessible input. Search and Enter submit the same native form to natural search; remove keyword fallback links. Keep the legacy keyword route and FTS implementation deprecated for existing URLs. | [PRD decision](../prd/prd-0020-local-natural-language-search.md#current-search-entry--2026-10-16), [search policy](../../policies/project/natural-language-search.md#product-surface) |
| Local source recovery | Recovery and duplicate retirement were performed locally with complete decoding, matching SHA-256/byte counts, no-overwrite publication and unchanged-file checks. LocalBrain ingests the restored native Session JSONL under its existing contract. | [Storage recovery](../../policies/project/installation-and-storage.md#native-session-compression-and-recovery) |

## Clarifications And Deferred Decisions

- Natural-search activation is explicit. Once enabled, the running app observes
  normalized Sync changes and refreshes in the background, reusing compatible
  embedding inputs. Sync completion is distinct from index completion; first
  preparation, cache loss, incompatible model/profile changes and explicit rebuild
  can require complete encoding. This is the natural-search index, not automatic
  preparation of the separate affinity map.
- Model composition uses normalized model IDs for both providers while preserving
  raw identity. A date suffix can be part of a published Claude model ID.
  This is not blanket alias or model-family aggregation, and it establishes no
  equivalence of model capability. This inspection changed no pricing.
- A Project label of `.` reflects the stored base-relative display name.
  General settings, configurable base paths and historical attribution/display
  policy remain a tracked decision in the [backlog](../project/backlog.md#project-root-and-path-display-settings).
- Native compression startup gating and an explicit compression RPC are distinct.
  A current disabled flag cannot identify the actor behind a previous compression
  pass. Keep the version scope and evidence limit in the storage owner.
- Scope correction: the owner clarified that LocalBrain reads local native
  Sessions; the compressed files in this incident required a separately authorized
  local recovery operation. The agent-added direct compressed-ingestion backlog
  item was withdrawn. It was not an approved follow-up requirement, and compressed
  ingestion is outside this Session ingestion contract.
- Portable conversation, identity, analytical-range and utility-feedback review
  criteria were separately published in [ai-assets](https://github.com/chochita0311/ai-assets/commit/b1adc91f4d90e57f5766b7cb78d674c689572960).
  That separate upstream result does not replace LocalBrain's owned policies.

## Documentation Reconciliation

Mode: incremental ownership cleanup and minimal/bounded reshaping. A broad tree
reorganization or document-wide rewrite was unnecessary and was not performed.

- Before: the Session lifecycle still described retaining only the last user
  input in a turn. After: its owned contract matches authored-input preservation,
  exact wrapper handling and counterpart deduplication.
- Before: current navigation still described two shared-header search inputs.
  After: the Plans Index and backlog point to the approved single-input decision;
  the PRD preserves the initial comparison phase as historical evidence.
- Before: native compressed rollout recovery had no current storage owner.
  After: the storage policy owns the version-scoped upstream distinction and
  safeguards for separately authorized local recovery.
- Before: detailed conversation normalization and phase provenance were split
  between Architecture and the declared data-model owner. After: the Session and
  Activity Event owner sections contain the complete predicates and exceptions;
  Architecture links to them while retaining integration and presentation rules.
  Generated semantic summaries remain self-contained, and the independent personal
  insight evidence-manifest contract keeps its own subsection.
- The receipt distinguishes historical reference specs from the owner's current
  corrections. Missing-file reconciliation and parsed-empty cleanup retain
  separate predicates and deletion effects.
- Existing entrance, policy, generated data-model and execution-history layers
  retain their ownership. No private recovery inventory is copied into them.

## Verification And Review

### Contract And Regression Evidence

- Baseline full regression: 1,144 tests passed before closeout additions.
  Seven focused Session ID collision/source/literal-ID, unified search and
  positive/empty history-bound checks increased that result to 1,151 passing tests.
- A subsequent semantic code review exposed an uncovered shared skill-only owner
  deletion case. Its eighth synthetic regression failed before the owner guard was
  corrected and passed afterward. The final full suite passed **1,152 tests in
  19.958 seconds** after the code and document-review corrections.
- Configured data-model checks match 45 ordinary tables, one FTS5 object,
  57 physical foreign keys, 51 explicit indexes and 10 subject owners. Schema
  presentation, 10 generated value dictionaries, the 704-object cleanup audit
  (592 keep, 112 defer) and the plan catalog are current.
- The repository privacy check passed for 1,292 candidate files. Both affected
  JavaScript assets passed Node syntax checks; the complete diff passed whitespace
  checks. These checks establish their recorded scopes, not complete product
  behavior or retrieval relevance.

### Local Browser Evidence

- A real browser Search click and Enter both reached natural search and retained
  the submitted query through the single native form. The original placeholder,
  accessible label and external submit-button association remain present.
  Atlassian retains its page-owned query and links Search to natural search.
- The composing-Enter guard was exercised with a synthetic keyboard event;
  physical operating-system IME behavior remains outside this evidence.
- Session pages reported in this session render authored user content without a
  standalone raw question-reply envelope. Representative Claude, personal Codex
  and Codex Company pages all expose user/final response frames and Session ID
  copy controls without an added completion label.
- Copy behavior was exercised with a temporary clipboard stub, restored afterward:
  complete-ID writes, button-centered feedback, independent two-second copied
  state, leave/re-entry, timeout, stale rejection after newer success, and local
  selectable failure recovery behaved as intended. This does not establish real
  operating-system clipboard permission behavior.
- Dashboard source changes and Daily/Weekly/Monthly changes retain selected dates
  while beginning and ending at positive selected-metric buckets. Expanded
  composition places Show less after its additional rows; collapsing restores
  Show more. Empty and cumulative range cases are covered by regression fixtures.
- Computed layout checks at 320, 920 and 1,440 CSS pixels found no outer-document
  overflow on search, Session detail and dashboard, kept header/copy controls
  contained, and retained the bottom Show less position. This is local DOM and
  interaction evidence, not an independent screenshot or human visual review.
- The idle loopback server was restarted with the current code; affected pages
  reloaded successfully and the existing natural-search index returned ready.

### Independent Documentation Reviews

Both requested subagents applied docs-structuring and docs-shaping independently.
Their content review covered changed document deltas, affected owner sections,
entrances and relevant linked contracts. The structural pass also inventoried the
978-file documentation tree; that inventory is not a semantic audit of all
unrelated historical prose.

Review findings corrected authored/generated subject direction, stale active-spec
authority, the no-positive-history exception, split normalization ownership,
deletion-branch predicate scope, generated summaries with invalid local links, and
an unrelated evidence-manifest paragraph captured by a new phase heading.
Focused follow-up reviews reported no remaining findings in those passages.
The final structural follow-up checked 733 relative links/anchors in three
affected documents, all 13 manifest source digests, the audit digest and the
ledger's manifest digest successfully. Reviewers performed read-only checks;
implementation and final verification remain the primary agent's responsibility.

## Remaining Boundary

Project display settings and recurring search-quality follow-ups remain
separately owned work. Physical operating-system IME behavior
and full distribution installation are not established by unit tests or this
closeout's local browser observations. Publication covers this repository's
reviewed changes; private source recovery is not a reusable product feature.
