# PRD-0005: Workflow And Skill Intelligence

## Metadata

- ID: `prd-0005`
- Status: `draft`
- Owner role: `human`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Request Summary

- Turn LocalBrain's directly collected Claude and Codex Session history into evidence-backed personal workflow insights, repeated-error and repeated-process detection, explicit skill-usage visibility, and reviewable suggestions for workflows that may be worth packaging as skills.
- Use cavemem's automatic capture, local health reporting, and behavior-report examples as reference material only. LocalBrain must not treat cavemem as a source, connector, compatibility target, database import, or runtime dependency.

## Source Set

### Human Request

- Analyze Claude Code and Codex Session history to understand what work occurred, which tools and file types were used, when activity was concentrated, which topics or errors repeated, and which processes could become reusable skills.
- Show frequently used skills separately from inferred skill candidates.
- Keep the insight experience understandable rather than turning raw activity volume into a productivity score.
- Treat cavemem as a reference implementation, not a LocalBrain connector or data source.
- Remove architecture and roadmap language that made cavemem appear to be an intended LocalBrain source; that durable boundary was aligned on 2026-07-18.

### Golden Sources

- Owner-supplied cavemem overview and example behavior report: automatic local Session capture, Session and observation counts, monthly activity, question activity by hour, tool frequency, file-extension frequency, topic distribution, repeated-error analysis, personal retrospective, context optimization, and knowledge-transfer use cases.
- Inspected cavemem reference behavior: local SQLite Sessions and observations, lifecycle hooks, capture-versus-query capability labeling, worker, database, and embedding-backfill health, progressive retrieval, and a read-only local viewer. These are reference patterns only.
- Current LocalBrain Claude and Codex source adapters and source-backed Session contract.
- [Design Constitution](../../policies/design/design-constitution.md): evidence-rich dashboard, provenance, reviewable Suggestions, hierarchy, density, state, responsive, and accessibility contract.

### Supporting Documents

- [Project Architecture](../../policies/project/architecture.md): direct Claude and Codex ingestion, normalized activity, source authority, and adapter ownership.
- [Product Model](../../policies/project/product.md): Session, Project, Workstream, Thread, checkpoint, Resource, and Suggestion responsibilities.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): local Session content, tracked evidence, export, and external-access boundaries.
- [Project Roadmap](../project/roadmap.md): Activity Insights And Workflow Intelligence phase and cavemem reference-only boundary.
- [Project Backlog](../project/backlog.md): Session-derived workflow and skill metrics, topic-analysis mechanism, evidence thresholds, and dashboard work.
- [Design Evaluation](../../policies/design/design-evaluation.md): dashboard hierarchy, readability, containment, source-use discipline, and rendered evidence.
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md): scope transitions, browse-to-evidence continuity, selection, disclosure, and feedback.
- [PRD-0004](prd-0004-session-usage-and-cost-dashboard.md): sibling draft for token usage and monetary observability.

### Current Implementation References

- `src/localbrain/ingest/claude.py` and `src/localbrain/ingest/codex.py`: current normalization of messages and tool names from authoritative local Session JSONL.
- `src/localbrain/ingest/common.py`: Parsed Session and Activity Event contracts, maintenance classification, and deterministic identity.
- `src/localbrain/schema.sql`: Sessions, Activity Events, Workstreams, Threads, Suggestions, checkpoints, and source provenance.
- `src/localbrain/queries.py`: current Session activity, Project activity, source mix, tool-call frequency, and context-switch metrics.
- `src/localbrain/templates/sessions_dashboard.html`: current activity and attention presentation that may provide an entry point but does not yet own Workflow Intelligence.
- `src/localbrain/workstreams.py` and related routes: current reviewable Suggestion and evidence-link behavior.
- `tests/`: synthetic Session parsing, parentage, maintenance exclusion, retrieval, query, route, and UI contract evidence.

## Current Findings

- LocalBrain already collects Claude and Codex Sessions directly and preserves authoritative source identity, timestamps, messages, tool names, Project relations, primary or subsession roles, and maintenance classification.
- The current parser intentionally omits opaque tool inputs and result payloads. As a result, current normalized data cannot yet reproduce touched-file, file-extension, error, stack-trace, attempted-solution, or command-sequence reports without a new bounded signal contract.
- Current `dashboard_stats`, `top_tools`, Project activity, and context-switch queries provide early descriptive signals but do not define active work duration, repeated workflow identity, topic classification, error equivalence, skill invocation, or evidence thresholds.
- Cavemem's useful reference contribution is its low-friction capture model, explicit capture coverage, database and worker health, and behavior-report categories. Its database, JSONL export, worker, embedding pipeline, and viewer are not LocalBrain product dependencies.
- Source session start and end timestamps can include idle time or incomplete lifecycle coverage. Raw wall-clock duration must not be presented as focused work time without an inactivity rule and source caveat.
- Tool frequency, prompt count, token count, file access, and active hours are activity indicators rather than outcome or productivity scores.
- LocalBrain is a single-user local product. Team ranking, employee evaluation, shared personnel reporting, and multi-user skill matrices are outside the current product boundary.

## Product Intent

- Help the user understand recurring work patterns they would not reliably document by hand, reconnect them to the underlying Session evidence, and decide which repeated processes deserve documentation, remediation, or a reusable skill.
- Convert raw activity into reviewable personal insight without equating volume with value or presenting inference as confirmed fact.
- Preserve useful tacit knowledge such as recurring errors, repeated questions, file relationships, solution paths, and workflow sequences while keeping source evidence and uncertainty visible.

## Confirmed Scope

### Direct Source And Signal Contract

- Derive Workflow Intelligence from LocalBrain's directly collected Claude and Codex source records and normalized LocalBrain data only.
- Keep cavemem reference-only:
  - no cavemem database or JSONL import
  - no cavemem source adapter or connector
  - no cavemem schema-compatibility requirement
  - no cavemem worker, embedding, viewer, or installation dependency
- Define a bounded source-neutral signal contract capable of representing, when supported:
  - Session identity, source, role, parent relation, Project, and time scope
  - activity segments and inactive gaps
  - user question or request events
  - tool name, normalized operation class, order, and bounded success or failure state
  - touched file or resource identity, extension or type, and read, edit, create, or execute relation
  - error signature, category, occurrence, and bounded local evidence
  - attempted or applied solution relation without claiming success solely because it appeared later in the transcript
  - explicit skill identity and invocation evidence
  - topic classification with classifier version, confidence, and evidence
  - repeated workflow fingerprint and the distinct Sessions, days, Projects, or Workstreams supporting it
- Prefer derived, minimal, rebuildable facts over copying full opaque tool inputs and outputs into new durable fields.
- Preserve source line, event, Session, and Project provenance so an insight can lead back to inspectable evidence.

### Personal Workflow Report

- Provide period-scoped personal activity insights including:
  - Session count and completion or lifecycle coverage where the source supports it
  - active-time estimate and inactive-gap caveat
  - monthly, weekly, daily, and time-of-day activity distribution
  - tool usage and common tool sequences
  - file or resource types and operation mix
  - Project or Workstream activity distribution
  - question or request topic distribution
  - context switching and Session fragmentation
- Use neutral wording such as `activity concentrated between` rather than claiming a productive or optimal time without outcome evidence.
- Keep raw counts visually subordinate to actionable patterns and comparisons.
- Allow period and source scope without mixing incompatible denominators silently.

### Repeated Error, Question, And Workflow Insight

- Detect recurring error signatures across distinct Sessions and show occurrence count, recency, affected Projects or Workstreams, and representative evidence.
- Detect repeated questions or semantically equivalent requests conservatively and distinguish exact matches from inferred topic similarity.
- Detect repeated tool and file-operation sequences only after a reproducible normalization and fingerprint contract exists.
- Surface candidate repeated workflows with:
  - concise pattern description
  - distinct Session, day, Project, or Workstream evidence counts
  - most recent occurrence
  - representative source-backed evidence links
  - confidence and source limitations
  - a bounded user action such as review, defer, dismiss, or inspect
- Treat undocumented file or stored-procedure relationships, decision context, and applied solution paths as evidence-backed knowledge candidates, not automatically confirmed architecture facts.

### Explicit Skill Usage

- Record a skill as used only when LocalBrain can identify an explicit invocation or another approved source-backed usage signal.
- Show frequently used skills separately from inferred skill candidates.
- For explicit skill usage, show at minimum:
  - stable skill identity and readable name
  - invocation count
  - distinct Session count
  - Project or Workstream distribution when known
  - last-used time
  - source coverage or missing-signal caveat
  - evidence links
- Do not infer skill success, quality, or impact from invocation count alone.
- Keep model, source, status, and skill identity as separate visual and semantic roles.

### Reviewable Skill Suggestions

- Generate a skill candidate only from a repeated, evidence-backed workflow that clears an approved threshold across distinct Sessions or dates.
- Check candidate overlap against the locally available skill inventory when that inventory can be read through an approved local boundary.
- Each candidate must explain:
  - what repeated workflow was observed
  - how often and across how many distinct Sessions, dates, Projects, or Workstreams it occurred
  - which steps, tools, file types, or errors support the pattern
  - why a reusable skill may reduce repetition or improve consistency
  - which evidence can be inspected
  - what uncertainty or source coverage limits the suggestion
- Present generated candidates as reviewable Suggestions with explicit inferred provenance.
- Support inspect, defer, dismiss or reject, and restore semantics consistent with LocalBrain's reversible review model.
- Skill-file creation, installation, publication, or external sharing requires a separately approved action and is not implied by accepting an insight.

### Information Architecture

- Keep Workflow Intelligence separate from the PRD-0004 Usage and Cost Overview, either as a clearly labeled local view or another bounded surface chosen during Feature review.
- The primary reading order is:
  - period, source, Project, or Workstream scope
  - concise personal workflow summary
  - repeated errors and repeated workflows
  - explicit skill usage
  - inferred skill candidates
  - source coverage and analysis freshness
- Link metrics and suggestions to filtered Session, Project, or Workstream evidence without losing the persistent shell.
- Keep data-health and classifier freshness visible but subordinate to the insight itself unless coverage is too weak for a trustworthy result.

### Privacy, Provenance, And Analysis Health

- Keep analysis local by default and do not transmit prompts, code, paths, error text, skill evidence, or derived profiles to an external model or service without explicit approval.
- Record analysis version, input scope, last successful analysis time, and source limitations for derived topics, signatures, patterns, and suggestions.
- Distinguish observed, normalized, inferred, user-confirmed, deferred, rejected, unavailable, and stale information without relying on color alone.
- Preserve previously valid insights with a stale label when recalculation fails; do not replace them with empty success.
- Use synthetic content in tracked tests, examples, screenshots, and evaluation artifacts.

## Excluded Scope

- cavemem installation, execution, worker control, SQLite or JSONL import, schema compatibility, viewer embedding, or connector behavior.
- Treating cavemem as a LocalBrain source or presenting it among supported or planned connectors.
- Team member comparison, employee productivity scoring, performance evaluation, managerial surveillance, bus-factor scoring from personal activity, or multi-user team dashboards.
- Claiming that tool count, file count, prompt count, tokens, Session duration, active hours, or topic share measures productivity, quality, or business value.
- Automatic publication to a Wiki, repository, ticket, team system, or external service.
- Automatic modification of Claude memory, Codex instructions, project instructions, or local skill directories.
- Automatic creation or installation of a skill merely because a candidate was generated or accepted.
- Full opaque tool payload duplication, broad command-output storage, credential capture, or unbounded stack-trace retention solely for insight generation.
- Mandatory external embeddings, external AI analysis, or network enrichment.
- A new multi-user identity, authorization, synchronization, or cloud architecture.
- Token and monetary reporting already owned by PRD-0004.
- Feature, Spec, schema, parser, query, template, or implementation work before this draft boundary is approved.

## Uncertainty

- Define the active-time idle threshold, minimum segment length, overlapping Session behavior, and source-specific fallback when no reliable Session end exists.
- Confirm whether the first product release covers both Claude and Codex or begins with a Claude-first evidence set while retaining a source-neutral contract; source rollout must follow actual file, error, and skill-signal coverage rather than assuming parity.
- Determine which Claude and Codex records provide reliable file-operation, tool-result, error, and explicit skill-invocation evidence without retaining excessive raw payloads.
- Decide whether error evidence stores only a deterministic signature and bounded excerpt or also a local pointer that rereads the authoritative source on demand.
- Define when a later action qualifies as an applied solution and when an error can be considered resolved rather than merely followed by different activity.
- Choose initial topic analysis between deterministic rules, a local model, or an explicitly approved model path. General external analysis is not authorized.
- Define minimum distinct Session, date, Project, and confidence thresholds for repeated workflow and skill Suggestions.
- Decide how to compare a candidate against installed skills when skill installations may come from several local Codex or plugin locations.
- Decide whether analysis uses primary work Sessions only, attributes direct subsession activity to its parent, or exposes separately scoped child activity. Maintenance activity should not silently affect personal workflow interpretation.
- Decide whether Project and Workstream distribution uses only source-time relations or later user-confirmed organization as an additional view.
- Decide whether a reviewed insight may be exported as a personal retrospective or Wiki draft in a later Feature; no external destination or write behavior is currently approved.
- Choose the final entry interaction: a local `Workflow Insights` view under Sessions Dashboard, a separate route, or another bounded dashboard-family surface.

These items may remain open while the PRD is `draft`, but each must be resolved before a dependent Feature is approved for Spec handoff.

## User-Visible Flows And Interaction Expectations

### Review Personal Patterns

- The user selects a period and optional source, Project, or Workstream scope and sees activity concentration, tool and file-type mix, topics, context switching, and analysis coverage.
- The report describes observed activity and limitations without assigning a productivity score.

### Inspect A Repeated Error Or Workflow

- The user opens a repeated pattern, understands its normalized signature or sequence, and follows representative evidence into existing Session, Project, or Workstream surfaces.
- Exact observations, inferred grouping, and user-confirmed interpretation remain distinguishable.

### Review Explicit Skill Usage

- The user sees which skills have source-backed invocation evidence, how often and where they were used, and which Sessions support the count.
- Missing source coverage does not appear as zero usage without a caveat.

### Review A Skill Candidate

- The user sees why a repeated workflow became a skill candidate, inspects its evidence and overlap with existing skills, and chooses to defer, dismiss, restore, or continue to a separately approved creation flow.
- Rejecting or deferring the candidate does not delete source activity or rewrite Workstream organization.

### Recover From Partial Analysis

- When a parser, classifier, or analysis pass fails, prior valid results remain visible with a stale or partial label and a bounded recovery path.
- No result state exposes raw implementation traces, internal storage paths, or excessive source payload by default.

## Constraints

- Explicit human direction and the approved PRD boundary govern scope.
- Claude and Codex source files remain authoritative. Workflow signals, clusters, topics, signatures, and skill candidates are derived and rebuildable.
- LocalBrain remains local-first and single-user; analysis runs without requiring cavemem or an external service.
- Captured and derived facts preserve source identity, Session identity, time, and evidence references.
- Generated insight never becomes user-confirmed fact or a created skill without an explicit review and later approved action.
- Analysis must avoid false precision, productivity scoring, volume incentives, and unsupported causal claims.
- Raw tool inputs and outputs remain bounded by the minimum signal needed for the approved analysis and by [Privacy And Data Handling](../../policies/project/privacy-and-data.md).
- The likely execution model begins with one or more `foundation-contract` Features for signal, duration, error, topic, workflow, and skill identity, followed by `fullstack-product` Features for insight and review surfaces.
- Visible Features require Contract, Design, Functional, and UX Heuristic evaluation as applicable, including evidence navigation, long content, empty, partial, stale, and responsive states at representative `1440`, `920`, `700`, and `320` widths.
- This PRD remains planning-only while `draft`. Feature creation, Spec work, parser or schema changes, and implementation require the repository's human approval gates.

## Acceptance Envelope

- Every workflow metric and insight has a reproducible definition, input scope, analysis version, freshness state, and source limitation.
- Active-time and Session-duration views distinguish wall-clock duration, inactive gaps, incomplete lifecycle coverage, and source-specific fallbacks.
- Tool, file type, topic, Project, Workstream, error, and workflow summaries derive from bounded normalized signals rather than unreviewed full-payload duplication.
- Raw activity volume is never labeled or ranked as productivity, performance, quality, or business value.
- Repeated errors, questions, workflows, and knowledge candidates link to representative source-backed evidence and distinguish observation from inference.
- Explicit skill use and inferred skill candidates remain separate in data, wording, status, and presentation.
- Every skill candidate states recurrence evidence, confidence, source limitations, likely benefit, and overlap with existing skills when available.
- Skill candidates are reversible and reviewable and cannot create, install, publish, or modify a skill without a separately approved action.
- The insight surface remains usable without cavemem installed and contains no cavemem source, import, connector, or compatibility behavior.
- Partial, stale, unavailable, empty, and failed analysis states remain visible and do not erase prior valid results.
- Synthetic parser, normalization, analysis, query, route, UI, and browser evidence covers representative repeated and non-repeated patterns without committing private Session content.
- PRD-0004 Usage and Cost behavior remains a separate information hierarchy and is not duplicated as Workflow Intelligence.

## Candidate Features

- `Session Insight Signal Contract` (`foundation`, `data`): define active segments, tool operations, file facts, error signatures, solution relations, topic facts, explicit skill events, provenance, and analysis freshness.
- `Personal Workflow Report` (`product`, `fullstack`): present period-scoped activity concentration, tools, file types, topics, Projects or Workstreams, and context-switching signals without productivity scoring.
- `Repeated Pattern Contract` (`foundation`, `data`): define error, question, workflow, recurrence, confidence, and evidence-link semantics independently of presentation.
- `Repeated Error And Workflow Insights` (`product`, `fullstack`): consume the approved pattern contract and expose evidence-backed review surfaces.
- `Skill Usage Insights` (`product`, `fullstack`): present explicit source-backed skill usage, Session and Project distribution, freshness, and evidence.
- `Reviewable Skill Suggestions` (`product`, `fullstack`): compare repeated workflows with existing skills and provide reversible, evidence-backed candidates without creating skill files.
- `Reviewed Insight Export` (`product`, deferred candidate): export a user-reviewed retrospective or documentation draft through a separately approved local or external boundary.

Feature documents are not created from this draft PRD until the human owner accepts its boundary. Signal contracts must be approved before product Features rely on duration, topic, error, workflow, or skill facts.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human request | primary | personal workflow analysis, repeated errors and processes, explicit skill usage, skill candidates, and cavemem reference-only direction | does not authorize team surveillance, external analysis, connector import, or automatic skill creation |
| Owner-supplied cavemem report | primary reference | automatic capture concept, health visibility, behavior-report categories, repeated-error use cases, retrospective, and knowledge-capture motivation | example counts, paths, identities, team use cases, and claims are not LocalBrain requirements or tracked data |
| Inspected cavemem behavior | supporting reference | lifecycle coverage, capture-versus-query status, local health, observations, and progressive disclosure | no source, connector, import, compatibility, worker, viewer, embedding, or runtime dependency |
| Current Claude and Codex source records | source authority | Sessions, messages, tool calls, timestamps, source identity, Project context, parentage, and available metadata | capabilities differ and require explicit fallback rules |
| Current LocalBrain code and schema | implementation truth | existing normalized facts, provenance, maintenance exclusion, primary/subsession contract, queries, evidence destinations, and review model | current omissions are foundation gaps, not permission to infer unsupported facts |
| Product, architecture, privacy, design, and interaction policies | durable contract | local-first scope, single-user boundary, evidence, Suggestions, provenance, state, responsive, and review behavior | do not decide analysis thresholds or classifier mechanism |
| PRD-0004 | sibling planning boundary | token usage, price basis, cost, source/model/Project composition, and usage history | monetary observability must not become a proxy for workflow productivity |

## Continuity Notes

- `2026-07-18`: created the initial draft from the owner's Workflow And Skill Intelligence direction, supplied cavemem reference report, inspected reference behavior, current Claude and Codex ingestion, and durable LocalBrain contracts.
- `2026-07-18`: fixed cavemem's role as reference-only and excluded database or JSONL import, source adapter, connector, compatibility, worker, viewer, embedding, and runtime dependency behavior.
- `2026-07-18`: separated observed activity, normalized facts, inferred patterns, user-confirmed interpretation, explicit skill use, and inferred skill candidates to preserve provenance and reviewability.
- `2026-07-18`: kept active-time rules, source evidence coverage, topic mechanism, error-resolution semantics, suggestion thresholds, subsession scope, installed-skill lookup, and export behavior open for human review.
