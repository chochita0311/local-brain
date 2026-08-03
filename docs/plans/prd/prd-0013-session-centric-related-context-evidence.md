# PRD-0013: Session-Centric Related Context Evidence

## Metadata

- ID: `prd-0013`
- Status: `passed`
- Owner role: `human`
- Created: `2026-08-03`
- Updated: `2026-08-03`
- User review status: `implemented and accepted`
- Approval mode: `completed`
- Canonical passed boundary: this PRD

## Request Summary

- Reframe primary Session `Related Context` as a deterministic account of what
  that Session explicitly mentioned, read through an approved tool, or shares
  through an explicit user-managed Thread or Workstream relationship.
- Present Session evidence before explicit organization context, use Session-observed identity
  instead of a shared Resource title as the primary display authority, and
  reduce the current flat rail's repeated labels and equal visual weight.
- Extend bounded local extraction to explicit Markdown references, safe HTTP(S)
  URLs, and approved resource-read tool evidence without parsing large
  conversations on detail-page requests or retaining opaque tool payloads.

## Source Set

### Human Direction

- The current deterministic behavior is desirable; the product should not add
  semantic relevance, LLM ranking, or hidden recommendation logic.
- Related Context should explain the viewed Session's perspective: what was
  mentioned, what was actually read through MCP, and what is explicitly linked
  through user-managed organization.
- Mentioned Markdown files and URLs should be organized without the current
  visually noisy sequence of equally weighted entries and repeated reason
  badges.
- Session presentation must not use `external_resources.title` as though it
  were the title observed by that Session. Shared Resource identity and
  Session-specific evidence have different owners.

### Existing Product Boundaries

- [PRD-0009: Data Model Value Dictionaries And Pinned Session Recall](prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
  and [FEAT-0060: Session Related Context Rail](../feature/feat-0060-session-related-context-rail.md)
  own the passed deterministic Related Context rail, its existing reason order,
  bounded projection, primary-Session-only placement, and zero-hidden-I/O
  contract.
- [PRD-0007: Atlassian Source Memory And Refresh](prd-0007-atlassian-source-memory-and-refresh.md)
  and [FEAT-0047: Bounded Atlassian URL Evidence Extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md)
  own the current configured-Atlassian URL evidence, bounded approved-tool
  result fields, source fingerprints, and derived reconciliation behavior.

### Durable Policies

- [Product Model](../../policies/project/product.md): Session source authority,
  evidence provenance, current Related Context projection, and detail/read
  ownership.
- [Project Architecture](../../policies/project/architecture.md): Claude and
  Codex parsing, normalized Activity Events, source reconciliation, Local
  Context ingestion, and no-hidden-external-work boundaries.
- [Workspace And Session Activity](../../policies/project/data-model/workspace-and-session-activity.md):
  source-derived Session, workspace, Activity Event, and evidence-consumer
  contracts.
- [Atlassian Source Memory](../../policies/project/data-model/atlassian-source-memory.md):
  stable External Resource identity, shared title ownership, bounded evidence,
  remote state, and content separation.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): local
  source content, derived-data minimization, private runtime storage, and
  synthetic tracked evidence.
- [Design Constitution](../../policies/design/design-constitution.md): detail/read
  hierarchy, calm evidence-rich density, contextual rail width, semantic-token
  use, and responsive simplification before typography reduction.
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md):
  truthful destination affordances, disclosure behavior, navigation
  continuity, focus, and responsive reading order.

### Current Implementation Evidence

- `src/localbrain/session_context.py` builds a request-time projection from
  Session-backed Atlassian evidence, shared Thread and Workstream links, and
  enabled same-workspace Documents.
- `src/localbrain/templates/_session_related_context.html` presents every target
  with repeated type, provenance, detail, availability, and reason rows inside
  one flat rail.
- `src/localbrain/atlassian_evidence.py` stores Session evidence separately from
  shared Resource and remote-content ownership, but the current visible
  projection reads `external_resources.title` as the target title.
- `src/localbrain/ingest/common.py`, `ingest/claude.py`, and `ingest/codex.py`
  already identify bounded visible URL evidence and approved tool-result
  evidence, but do not expose a general Session reference model for Markdown,
  generic URLs, or successful resource-read calls.
- Current local inspection confirmed that successful Jira MCP reads can exist in
  authoritative Session JSONL while Related Context knows only that the URL was
  visible. A short Jira-key title versus a full-URL title currently reflects
  shared Resource bootstrap history, not whether the viewed Session performed a
  remote read.

## Product Intent

- Turn Related Context into a compact Session evidence index: direct references
  first and explicit user-managed organization context second.
- Let the user distinguish `mentioned`, `read through an approved tool`,
  and `shared explicit organization` without implying semantic relevance or
  remote freshness.
- Keep stable Resource identity and destination ownership reusable across the
  product while allowing each Session detail to describe only what that Session
  actually observed.
- Preserve enough bounded provenance to explain and reconcile the display
  without copying complete messages, tool inputs, tool results, or remote
  content into a new evidence owner.

## Confirmed Scope

### Session-Centric Evidence Ownership

- Define one source-neutral Session reference evidence contract for eligible
  primary work Sessions.
- Separate these facts explicitly:
  - stable target identity and destination;
  - Session-observed display identity;
  - evidence channel and bounded source location;
  - occurrence or completed-read state;
  - shared Resource metadata and remote state.
- `external_resources.title` remains the shared Resource title and may serve as
  a bounded fallback or destination description. It is not the primary
  presentation authority for a Session reference when the Session supplies a
  deterministic identity.
- One target may retain several Session evidence kinds without appearing more
  than once in the visible direct-reference group.
- Evidence remains source-derived and rebuildable. It never becomes a
  user-curated Resource relation merely because the Session detail displays it.

### Explicit Reference Families

- Support explicit safe HTTP(S) URLs observed in visible user or assistant
  messages.
- Support explicit Markdown reference forms that identify a `*.md` target,
  including a bounded absolute path, relative path, Markdown link destination,
  or bare Markdown filename when it resolves exactly and unambiguously inside
  the Session's eligible local workspace/context boundary.
- Support an initial approved tool-read evidence family for configured
  Atlassian Item reads recorded in authoritative Claude or Codex Session data.
  A visible `MCP로 조회` state requires a matching completed non-error read,
  not a tool name, attempted call, URL mention, or shared Resource refresh.
- Preserve supported failed read attempts when their target identity is
  deterministic. If any matching read succeeds, the target presents successful
  `MCP 조회` evidence; when every matching attempt fails, it presents bounded
  `MCP 조회 실패` evidence and never implies that remote content was read.
- Preserve the distinction between:
  - user-message mention;
  - assistant-message mention;
  - approved tool-result observation;
  - successful approved resource read.
- Initial tool-call interpretation is adapter- and operation-allowlist based.
  Unknown MCP tools and opaque arguments do not become references by heuristic.
- Jira Session display identity prefers a deterministically observed issue key;
  Markdown prefers the observed file name or relative path; a generic URL
  prefers a safe bounded host/path representation. Confirmed remote titles and
  shared local titles remain secondary metadata or fallback.

### Extraction And Reconciliation

- Extract and reconcile reference evidence during Session synchronization under
  a versioned bounded contract. Session detail requests do not reparse the
  source JSONL or normalized multi-megabyte message bodies.
- Repeated synchronization is idempotent and deduplicates the same target while
  retaining bounded distinct evidence locations and evidence kinds.
- When the authoritative JSONL changes, a reference disappears, or a Session is
  removed through the existing source-reconciliation lifecycle, its derived
  Session reference evidence is reconciled or deleted without deleting shared
  user-managed Resource state.
- A source or parser failure retains prior valid evidence with a bounded stale
  or partial state rather than reporting an empty successful result.
- Extraction remains bounded by eligible Session class, role, source policy,
  candidate count, per-field size, parser depth, and total retained evidence.
- Existing Claude, personal Codex, and Codex Company source instances share
  provider-appropriate parser rules while retaining independent source
  provenance.

### Related Context Information Architecture

- Replace the flat equal-weight list with two relationship-strength groups:
  1. direct evidence from the viewed Session;
  2. explicit shared Thread or Workstream organization.
- Direct Session evidence is visually primary and expanded by default.
- Group headings explain the relationship once. Repeated per-item relationship
  pills, source labels, and identical provenance text are removed when the group
  already carries that meaning.
- Each target appears once under its strongest group and may expose multiple
  bounded Session evidence labels such as `MCP로 조회` and `대화에서 URL 언급`.
- Normal rows show only the identity, destination context, and Session evidence
  needed to understand the relationship. Missing, archived, unsafe, ambiguous,
  stale, or partial states retain explicit text and may use the existing status
  vocabulary.
- The main conversation retains its established readable width. The contextual
  rail remains secondary, enters document flow before the conversation at the
  compact breakpoint, and simplifies disclosure before reducing text size.
- Empty and error states continue to avoid recent-document, inferred-relevance,
  or global-catalog fallback.

### Read And Navigation Boundaries

- Opening Session detail remains a local SQLite read. It performs no external
  call, MCP request, model call, embedding request, source scan, capability
  inspection, maintenance Run, or relationship mutation.
- A related target keeps its existing owned destination: Local Context document,
  Atlassian Item, local Resource, or safe external URL.
- Evidence location must be sufficient for later Session-conversation navigation
  without requiring retained message excerpts.

## Excluded Scope

- Semantic relevance, embeddings, LLM ranking, topic similarity, fuzzy filename
  matching, inferred Jira keys, or recommendation scoring.
- Treating every same-workspace Document as mentioned or every remote Resource as
  read.
- Showing Local Context Documents merely because their `workspace_id`, parent
  directory, repository, or work path matches the Session. A shared path without
  direct Session evidence or an explicit Thread/Workstream link is not Related
  Context in this boundary.
- Replacing stable External Resource identity, remote metadata ownership, local
  notes, classifications, or Workstream/Thread relations.
- Updating a shared Resource title merely to make one Session display read more
  naturally.
- Copying full messages, tool arguments, tool results, command output, Jira
  descriptions/comments, Local Context bodies, or remote content into reference
  evidence.
- Scanning arbitrary repository files, Git history, disabled Context roots,
  unregistered filesystem roots, Maintenance Sessions, or unsupported opaque
  tool payloads.
- Implicit remote refresh, Site registration, access setup, capability checks,
  or External Resource creation from key-only text.
- User-curated Session-to-context membership, manual rail ordering, accepted
  inferred relevance, global recent Context, or native Claude/Codex resume.
- Exact `대화에서 보기` anchors, in-conversation scrolling or highlighting,
  and multi-occurrence navigation in the initial Feature sequence. The evidence
  contract remains navigation-ready for a separately approved follow-up.
- Related Context on Subsession detail and parent aggregation of child evidence
  in the initial Feature sequence. Primary Session evidence remains isolated;
  explicitly attributed direct-child roll-up requires a separately approved
  follow-up.
- Spec, implementation, migration, tracked schema output, or evaluator work
  while this PRD remains `draft`.

## Resolved Decisions And Deferred Scope

- Each visible group initially presents at most `10` unique targets and always
  exposes its total count. Additional retained targets remain available through
  an explicit `N개 더 보기` disclosure; collapsing the disclosure restores the
  initial list. Direct references and explicit Thread/Workstream targets use
  independent counts and limits, so organization candidates cannot displace
  direct Session evidence.
- Each Session reference family retains at most `100` unique targets under the
  initial safety boundary. If more unique targets are observed, the projection
  reports the observed total and explicit partial state such as `총 143개 중
  100개까지 확인했습니다`; it never reports the retained subset as complete.
- One target occupies one row. The evidence summary may show both distinct
  completed MCP read calls and distinct normalized message/tool-result
  locations. Repeated text within one event, replayed prefixes, compaction
  copies, and repeated normalization of the same source location do not inflate
  counts. A single occurrence may omit the numeral.
- Markdown resolution follows deterministic containment:
  1. an absolute path resolves only by exact eligible path;
  2. a relative path resolves exactly against the Session `cwd`;
  3. a bare Markdown filename resolves only when exactly one eligible Document
     in the Session workspace matches;
  4. ambiguous or missing targets remain unresolved and are never guessed;
  5. workspace is a resolution boundary for an explicit mention, never a source
     of automatic context candidates.
- The rail title is `관련 자료`. The direct-evidence group is `이 세션의 참조`
  and the explicit Thread/Workstream group is `연결된 작업`.
- Initial evidence labels are `MCP 조회`, `MCP 조회 실패`, `사용자 메시지에서
  언급`, `Agent 응답에서 언급`, and `도구 결과에서 확인`.
- Exact `대화에서 보기` scrolling, highlighting, and occurrence selection is
  deferred to a later Feature. The initial evidence shape remains
  navigation-ready without exposing that interaction.
- Subsession evidence remains isolated and does not roll up to a primary Session
  in the initial sequence. A later boundary may add direct-child evidence only
  with explicit child provenance.

## Constraints

- Original Claude and Codex JSONL remains authoritative for Session messages,
  tool calls, results, order, and source location. Normalized reference evidence
  is a derived local projection.
- The evidence owner must preserve Session ID, source instance, provider/parser
  identity, source event or line location, evidence kind, and reconciliation
  version without retaining excessive payloads.
- Generic URL persistence and display must avoid leaking credentials or opaque
  query material. Query and fragment data is excluded unless an approved
  identity adapter requires a bounded allowlist.
- The current meaningful-primary, Maintenance exclusion, source-file deletion,
  parser-version repair, and multi-source synchronization contracts remain
  authoritative.
- Evidence reconciliation may delete source-derived rows when their owning
  source evidence disappears, but it cannot delete shared user-managed Resource,
  note, classification, Workstream, Thread, or confirmed remote-content state.
- Tracked tests, examples, screenshots, PRDs, Features, Specs, and evaluations
  use synthetic Session IDs, paths, URLs, issue keys, and Markdown names.
- Visible work uses the `fullstack-product` profile with Contract, Design,
  Functional, and UX Heuristic evaluation. Foundation work uses the
  `foundation-contract` profile with Contract and Functional evaluation where
  runtime reconciliation changes.
- [FEAT-0060](../feature/feat-0060-session-related-context-rail.md) and
  [FEAT-0047](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md)
  remain regression surfaces rather than being rewritten as though the earlier
  contracts never existed.

## Acceptance Envelope

- A Session detail can explain whether each direct target was mentioned by the
  user, mentioned by the assistant, observed in an approved tool result, or read
  successfully through an approved resource tool.
- Supported failed reads remain visible as failure evidence when no matching
  attempt succeeds; success and failure are never collapsed into a false read
  confirmation.
- Shared Resource title/bootstrap history cannot make two equivalent Session
  references appear to have different evidence strength or resource type.
- Jira issue keys, resolved Markdown references, and safe generic URL identities
  use deterministic Session-observed presentation with explicit fallback rules.
- Mentioned or read targets appear before explicit organization material, and
  one target is deduplicated across every applicable evidence and relationship
  reason.
- Same-workspace Documents with no direct evidence or explicit organization link
  do not enter candidate counts, display limits, empty states, or the visible
  rail.
- Primary Session reference evidence excludes Subsession evidence in the initial
  Feature sequence.
- Changed, removed, duplicated, malformed, ambiguous, unsupported, stale,
  partial, and failed source states have deterministic reconciliation and visible
  behavior.
- A large Session does not require source or message-body reparsing on detail
  load; request-time work remains a bounded local projection.
- The detail request performs zero external/model work and does not mutate
  Resource identity, remote state, organization, or source files.
- Every new persisted fact has an explicit owner, rebuildability, deletion,
  recovery, producer, consumer, and privacy contract before the product surface
  depends on it.
- Synthetic Contract, parser, reconciliation, route, UI, responsive, keyboard,
  and browser evidence covers every supported reference family and group state.

## Candidate Features

The completed PRD is decomposed into the following passed Feature boundaries.

### [FEAT-0072: Session Reference Evidence Contract](../feature/feat-0072-session-reference-evidence-contract.md)

- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Likely execution profile: `foundation-contract`
- Required evaluators: `contract`
- Goal: fix the source-of-truth boundary, evidence vocabulary, minimal value
  shape, display-authority order, lifecycle, and privacy rules so downstream
  extraction and presentation do not guess.
- Contract surfaces: Session reference identity, evidence kinds, source
  location, successful-read semantics, shared Resource relation, Markdown and
  URL resolution boundary, reconciliation/version ownership, and fallback
  presentation.
- Dependency: passed FEAT-0047 and FEAT-0060 behavior as inspected regression
  sources.
- Pass seed: downstream parser, storage, query, and UI Specs can proceed without
  unresolved ownership or display-authority decisions.

### [FEAT-0073: Deterministic Session Reference Capture And Reconciliation](../feature/feat-0073-deterministic-session-reference-capture-and-reconciliation.md)

- Status: `passed`
- Type: `foundation`
- Surface: `backend`
- Likely execution profile: `foundation-contract`
- Required evaluators: `contract`, `functional`
- Goal: produce the approved bounded reference evidence from current local AI
  source adapters during synchronization and reconcile it with authoritative
  Session changes without opaque-payload retention or remote work.
- Surface lanes:
  - provider-aware visible mention and approved read extraction;
  - exact Markdown and safe URL resolution;
  - fingerprinted persistence, deduplication, stale handling, and deletion;
  - bounded read projection for later presentation.
- Dependency: FEAT-0072 must pass before build.
- Pass seed: supported synthetic Claude, personal Codex, and Codex Company
  Sessions produce equivalent evidence semantics; repeated, changed, missing,
  malformed, unsupported, successful-read, failed-read, maintenance,
  Subsession, and large-source cases reconcile deterministically.

### [FEAT-0074: Session-Centric Related Materials Rail](../feature/feat-0074-session-centric-related-materials-rail.md)

- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Likely execution profile: `fullstack-product`
- Required evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Goal: replace the flat Related Context list with a calm, grouped Session
  evidence index that shows direct references first and keeps explicit
  organization context truthful but subordinate.
- Surface lanes:
  - grouped read model, strongest-group deduplication, count/disclosure, and
    fallback state;
  - detail rail markup, semantic-token presentation, responsive order, and
    accessibility;
- Dependencies: FEAT-0072 and FEAT-0073 must pass before build.
- Pass seed: equivalent Jira references display consistently regardless of
  shared title history; direct evidence kinds remain visible; same-workspace-only
  Documents remain absent; desktop and compact layouts preserve the conversation
  reading hierarchy with no hidden I/O.

## Recommended Feature Order

1. `FEAT-0072`: Session Reference Evidence Contract.
2. `FEAT-0073`: Deterministic Session Reference Capture And Reconciliation.
3. `FEAT-0074`: Session-Centric Related Materials Rail.

All three Features passed in the approved dependency order. Exact conversation
navigation and Subsession evidence roll-up remain deferred and require a new
planning boundary.

## Continuity Notes

- `2026-08-03`: initial draft created from the owner's review of a populated
  primary Session Related Context rail, the distinction between Session evidence
  and shared `external_resources.title`, and the request to organize explicitly
  mentioned Markdown, URL, and MCP-read references from the Session's
  perspective.
- `2026-08-03`: planning stopped at PRD review. Candidate FEAT-0072 through
  FEAT-0074 remain proposals and have no Feature, Spec, Run, evaluation, schema,
  or implementation authority until the owner approves the PRD boundary.
- `2026-08-03`: owner deferred exact `대화에서 보기` scrolling, highlighting,
  and occurrence navigation to a later Feature while retaining bounded source
  location evidence for future use.
- `2026-08-03`: owner removed same-workspace/work-path Documents from Related
  Context because path-only candidates make the Session-focused rail too large.
  Only direct Session evidence and explicit user-managed Thread/Workstream
  relations remain eligible in this PRD boundary.
- `2026-08-03`: owner required failed approved MCP reads to remain visible. Any
  matching success presents successful read evidence; failure-only attempts
  present bounded failure evidence without remote-read implication.
- `2026-08-03`: owner accepted the primary-only recommendation for the initial
  sequence. Subsession evidence does not roll up to its parent until a later
  separately approved boundary adds explicit child provenance.
- `2026-08-03`: owner approved all remaining PRD decisions with `10` targets as
  each group's initial display limit. Distinct read and source-location counts,
  exact Markdown resolution, the `관련 자료` / `이 세션의 참조` / `연결된 작업`
  vocabulary, explicit `N개 더 보기`, and a transparent `100`-target safety
  boundary are fixed. PRD-0013 moved to `approved` and entered Feature planning.
- `2026-08-03`: FEAT-0072 through FEAT-0074 and RUN-20260803-82 through
  RUN-20260803-84 passed every required evaluator and repository check. Human
  post-run review accepted the completed evidence contract, deterministic
  reconciliation, and related-material presentation and closed this PRD as
  `passed`.
