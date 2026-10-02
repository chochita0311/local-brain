# PRD-0018: Personal AI-Use Improvement Insights

## Metadata

- ID: `prd-0018`
- Status: `approved`
- Owner role: `human`
- Created: `2026-09-27`
- Updated: `2026-10-02`

## Request Summary

- Extend Sessions Dashboard → Insights from an observed skill ranking into a personal AI-use improvement workspace. The owner can ask about their own AI-assisted work or request discovery, receive one evidence-backed report per analysis Run, and review practical changes that may improve how they use AI and work.
- Use broad writing, research, analysis, planning, learning, coordination, and development examples. Codex harness, skills, and `AGENTS.md` are possible interventions, not the product's exclusive purpose.

## Source Set

### Human Direction

- Keep the observed skill ranking on the left at a narrower width and put an improvement analyzer on the right within Insights; preserve a readable stacked layout at narrow widths.
- Support both a question-led Run and suggestions that can arise without the owner first asking a specific question. A Run may find nothing useful and should still return an honest result.
- Let one deliberate Run produce a report that can inform later work. Use a skill-like, versioned guide for what to look for, how to weigh evidence, and what to recommend.
- Analyze the owner's local Sessions for repeated friction, habits, learning needs, missed opportunities, and suitable interventions. The goal is personal AI use and work improvement for anyone, not a developer-only or harness-only audit.
- Existing Dashboard and Workstream concepts may be replaced later. Reuse only general execution and evidence primitives where they fit; avoid making new insight identity depend on Workstreams or their maintenance schema.

### Supporting Sources

- [Personal AI-Use Improvement research and guide proposal](../research/session-improvement-analysis-framework.md): primary-source review, provisional improvement taxonomy, core analysis guide, and evidence limits.
- [Personal AI-Use Improvement playbook drafts](../research/session-improvement-playbook-drafts.md): type-specific triggers, benign alternatives, intervention choices, and owner follow-up checks for later guide review.
- [PRD-0005: Workflow And Skill Intelligence](prd-0005-workflow-and-skill-intelligence.md): sibling approved first Insights increment and source-backed skill-use contract; its deferred pattern work overlaps this destination but does not approve the new analyzer.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): private Session content, runtime artifacts, and external-model boundaries.
- [Product Model](../../policies/project/product.md), [Project Architecture](../../policies/project/architecture.md), and [Maintenance Task Runner](../../policies/operations/claude-task-runner.md): current Session authority, retrieval, execution, and review behavior.
- [Design Constitution](../../policies/design/design-constitution.md), [Design Evaluation](../../policies/design/design-evaluation.md), and [Interaction Evaluation](../../policies/experience/interaction-evaluation.md): visible evidence, hierarchy, containment, state, and responsive behavior.

### Current Implementation References

- `/sessions-dashboard/insights` and `src/localbrain/templates/session_insights.html` show the source-backed skill ranking beside executable question and discovery analysis controls, retained Run history, and real report detail. The earlier fictional preview has been removed.
- `src/localbrain/skill_observations.py` and `skill_observations` retain counted explicit skill loads after ordinary source disappearance. Invocation count does not prove quality or impact.
- `sessions` and `activity_events` retain source-backed work Session messages and tool names; opaque tool inputs and result payloads are intentionally absent from the normalized activity projection. `personal_insight_guidance.py` and its versioned package playbooks now own the executable guide; research drafts are historical rationale rather than Run input.
- The existing Task Runner already supports bounded local retrieval, background process status, artifacts, cancellation, and maintenance-Session exclusion. Its Workstream-oriented Run/result schema is not a suitable semantic owner for personal insights.

## Product Intent

- Help one person see patterns in how they use AI, identify concrete improvements worth trying, and judge whether an accepted change helped their own goals.
- Treat outside best practices as hypotheses to test against local evidence. Distinguish an observed Session pattern from an inferred cause, the proposed action, and an outcome confirmed by the owner.
- Make asking, discovery, evidence inspection, review, and later follow-up feel like one coherent Insights workflow without slowing the Usage & Cost opening route.

## Confirmed Scope

### Insights Experience

- Keep the current skill ranking accessible as a compact left column in Insights and give the analyzer and its Run history the primary remaining desktop width. Align the ranking's skill, count, and last-use columns across every row. On narrow screens, preserve both in a clear reading order without a nested-scroll trap.
- Offer a free-form question path and a `Discover` path. Each deliberate analysis Run produces one report; the report may contain several bounded findings or say no actionable finding was supported.
- One Run identity is one execution attempt. The owner may repeat a question or discovery request, but each repeat creates a new Run and preserves the previous Run's status, inputs, model, evidence, and report. Opening or downloading an old result never reruns analysis; duplicate start actions must not create accidental concurrent Runs.
- A completed analysis Run produces a readable Markdown report in its private local Run artifacts. Insights displays it and offers a repeatable Markdown download from that Run's history. Any additional user-facing output files belong to the same Run and remain downloadable there; internal prompts, evidence, and traces are not automatically presented as attachments. There is no automatic output expiry. Originals remain available until the owner explicitly deletes the Run or local runtime data. A later Run never overwrites earlier outputs. The owner may save a downloaded copy to a chosen local work location for use in a separate ordinary work Session. The analysis Run does not resume as a work Session or execute the proposed change.
- Show Run progress, completion, failure, cancellation, and partial-evidence state with a recovery path. Reopening Insights or changing unrelated dashboard controls does not start or repeat analysis.
- Show analysis Runs as a browsable list alongside the analyzer, using the familiar Sessions-list pattern while keeping analysis Runs out of ordinary work Sessions. Each real row identifies its question or discovery purpose, status, execution time, and output attachment availability; opening a row reveals its report and download. Keep a small number of recent reports and reviewed findings on the Insights overview, with a complete retained Run history for older reports and their downloads. A finding can be accepted for consideration, revised, deferred, dismissed, or marked inapplicable without changing source Sessions or other product organization.
- Allow a future owner-enabled proactive discovery cadence after new evidence arrives, so the product can suggest improvements without a question. The first increment does not silently start a model Run on page load or every synchronization.

### Analysis And Recommendations

- Use a short core guide with bounded versioned category playbooks. The approved goal-led selection correction makes all eleven types available to each Run; the model chooses a type from the owner's goal and observed friction. Cover request quality, context, repetition, learning, verification, information access, decisions, task fit, personal value, and configurable-assistant behavior when applicable.
- Recommendations can be a better way to ask or review AI, a template, checklist, learning resource, document, script, focused skill, assistant setting, tool, or no change. They must not default to creating a skill or adding an `AGENTS.md` rule.
- Every finding states the person's relevant goal, observation, representative Session evidence, alternative explanation or counterexample, source-coverage limit, proposed action, expected benefit, effort or tradeoff, and a follow-up check. Claims about productivity or causality require evidence beyond volume or duration.
- Every personal-improvement analysis Run, its generated explanation and suggestions, and resolved child activity are excluded from future personal-improvement evidence. The analysis execution is not an ordinary work Session; direct real-model usage/cost remains attributable under the existing contract.
- The Markdown report is analysis output, not an independent observation of the owner's work. A later ordinary work Session may use it as a reference, while any claim that the proposed change helped must be supported by that later work or owner feedback.
- Preserve the guide version, selected scope, evidence manifest, status, and result for each Run. A changed source or guide may make a result stale; it must not silently rewrite a reviewed finding.
- Default each new Run to the latest available, compatible high-capability analysis model for the selected runner/provider. Resolve and show its chosen model identifier and analysis settings before execution, then record them with the Run. Record the provider-reported effective snapshot when available; otherwise label the underlying version unverified. A new release may change the default for future Runs only. If the default is unavailable, do not silently switch model or provider; require an explicit user choice or show that execution is unavailable.
- The first analysis increment may reason from eligible Session messages, timestamps, source identity, and tool names already available. It must label other categories unavailable when they require tool input, tool results, actual task outcomes, or off-Session context that the approved evidence contract does not provide.

### Source And Ownership Boundary

- Current evidence comes from directly collected Claude and Codex Sessions. The guide is occupation-neutral, but reports must not imply coverage of offline work, other AI tools, or actual outcomes that these sources do not show.
- Distinguish currently inspectable evidence from a retained historical observation whose source Session has disappeared. Skill-use retention does not automatically authorize or prove retention of every other kind of Session-derived content.
- Give analysis Runs and findings independent identity and review state. Reuse generic runner, source retrieval, status, and artifact primitives where suitable; Workstream links are optional context, not ownership.
- Keep private prompts, evidence, traces, and the original Markdown report in local runtime storage outside Git. A user-requested copy in a selected work location is a separate handoff artifact. Any external-model path must have an explicit user choice before private Session content is sent.
- Before every analysis Run, show the selected model and Session evidence scope beside a concise notice that token use can be substantial and a repeat creates additional usage. Show a reliable pre-Run estimate only if the selected runner supports one; after completion, show observed usage and an attributable cost estimate when available, with its pricing basis visible.

## User-Visible Flows

### Ask About A Work Pattern

- The owner enters a question, reviews the selected Session scope and analysis path, and starts one Run.
- The owner sees the exact model selected at that moment and the token-use notice before starting. Repeating the same question later creates a new Run whose result can be compared with the earlier one.
- The report responds to that question with source-backed findings or explains that the available Sessions do not support a useful conclusion.

### Discover Improvement Opportunities

- The owner starts a deliberate discovery Run without supplying a question. The guide selects relevant types and returns a small, reviewable set of opportunities, including a no-finding result when warranted.
- A later owner-enabled proactive path may bring new candidates into this view without making a page visit or every source sync an implicit model execution.

### Review And Revisit

- The owner opens a finding's representative Session evidence and counterexample, decides whether the suggestion is useful, and can later record whether the chosen change helped.
- The owner can repeatedly download any retained completed Run's Markdown report and supply a saved copy to a separate local work Session when ready to implement an idea. Downloading the report never starts or continues a model Session by itself.
- If a source disappears or changes, the report retains its historical decision while showing which evidence can no longer be verified. A failed or cancelled Run does not erase an earlier valid report.

## Excluded Scope

- Automatic edits to skills, `AGENTS.md`, project files, external systems, or Workstream organization from a generated finding.
- Continuing the analyzer conversation as an ordinary work Session, or automatically starting one when a report is completed or exported.
- Employee ranking, surveillance, a universal productivity score, or treating prompt count, tokens, spend, Session length, and tool use as value measures.
- Broad copying of raw source files or opaque tool payloads into an insight database or tracked artifact.
- Assuming all work or all AI usage is visible in Claude/Codex Sessions.
- Automatic provider transmission from viewing Insights, synchronizing Sessions, or opening a saved report.
- Replacing the current Usage & Cost route, skill-observation ledger, or approved first ranking increment as part of the analyzer's initial build.

## Uncertainty And Decisions Needed Before Dependent Features

- The exact Markdown handoff presentation and destination choice: the original stays in the private Run artifact location; define the explicit copy/save flow and whether the first release needs a file-open or path-copy shortcut. No work-location copy is written merely by running analysis.
- Future analysis-engine expansion beyond the owner-selected Codex CLI path, including any local-only alternative and its separate private-content boundary.
- Future model resolver refresh and pricing: the first executable increment freezes the displayed Astra model and selected Codex home per Run; automatic discovery of new model availability, alternative choice, and precise pre-Run estimates remain separate work. Observed analysis usage and supported estimated cost follow the existing Usage & Cost contract.
- Future evidence-quality review: the first executable release freezes at most 100 Sessions, 300 excerpts, and three messages per Session, with source/month spread. A real-model review must assess which claims those sampled messages can actually support.
- Targeted expansion remains a future option for conversation neighbors and disconfirming examples. The first executable release instead narrows, asks for bounded additional evidence, or abstains when its frozen sample is insufficient.
- The first proactive mechanism: when the owner enables it, what change triggers candidate discovery, and whether model analysis requires a separate scheduled or explicit action.
- The exact review states and freshness rules for a finding whose underlying Session disappears or changes, plus explicit deletion controls for retained Run artifacts. Completed Markdown reports do not expire automatically.
- How to provide a precise pre-Run cost estimate if a future runner exposes one; the first increment shows a token-use warning and observed CLI usage after execution.

## Constraints

- Use the `fullstack-product` profile for a visible analyzer Feature, with `backend` and `frontend` lanes; separate foundation Features own evidence and result contracts before a product Feature consumes them.
- Scope all analysis to eligible primary work Sessions unless an approved source-neutral contract defines safe child attribution. Maintenance and provider-internal records remain excluded as evidence.
- Preserve privacy and source authority. An external model cannot receive private Session text merely because a public research source recommended a method.
- Show observed, inferred, unavailable, stale, reviewed, and failed states without color alone. Maintain keyboard access and containment down to the Design Constitution's viewport floor.
- Keep the existing Usage & Cost first-load query independent of insight analysis.

## Acceptance Envelope

- The owner can reach Insights, see the skill ranking and analyzer, ask a question or request discovery, and inspect a completed or honest no-finding report without losing source context.
- A completed Run preserves its Markdown report and any other user-facing output attachments in private local Run artifacts without automatic expiry. The owner can download them again from Run history and save a copy for a separate work Session; neither completion nor downloading starts implementation work.
- Repeating an analysis creates a separately identifiable Run and never replaces an earlier result. The exact chosen model, settings, evidence scope, and observed usage remain inspectable for each Run.
- Every claim in a finding can be traced to admitted local evidence or is clearly labeled as interpretation; competing explanations and missing coverage are visible.
- Runs are deliberate, bounded, cancellable, and recoverable. A page visit, refresh, report download, or source sync does not silently trigger a paid model Run or a private-content transfer. The start area warns that analysis can consume substantial tokens and a repeat adds usage.
- A reviewed recommendation persists as a review decision, does not automatically edit local or external resources, and can be revisited after new evidence or owner feedback.
- The system can add a later user-enabled proactive suggestion path without replacing the question-led report identity or creating a feedback loop from its own Sessions.
- The guide and result are versioned so a user can understand why a prior report differed from a later one.
- The existing skill ranking, Sessions route, and Usage & Cost opening performance remain intact.

## Delivered And Candidate Features

- [Insights Analyzer Screen Preview](../feature/feat-0109-insights-analyzer-screen-preview.md) (`passed`, historical preview): its fictional report example and disabled controls were replaced by FEAT-0110.
- [Executable Personal Insight Runs](../feature/feat-0110-executable-personal-insight-runs.md) (`passed`, bounded live-provider evidence): explicit Codex CLI question/discovery Runs, private Markdown reports, status, and history. RUN-125 restores analysis usage accounting; RUN-135 fixes the observed CLI startup failure. Subsequent owner-started question Runs produced a no-finding report and a core-v8 finding report. The [closeout review](../feature/feat-0110-executable-personal-insight-runs.md#first-increment-closeout-review) records current residual gaps.
- [Insight Evidence Eligibility And Manifest](../feature/feat-0107-personal-insight-evidence-manifest.md) (`passed`, synthetic foundation): source-neutral eligible Session scope, bounded evidence references, coverage, and maintenance exclusion.
- `Targeted Evidence Expansion` (`foundation`, `data`, future option): bounded follow-up reads around candidate conversations and counterexamples when the initial sample cannot support a claim; the current first release abstains or asks instead.
- Discovery quality follow-up: [RUN-127](../run/run-20260929-127-personal-insight-context-comparison.md) compares bounded neighboring context and records a repeated evidence request plus a category-coverage limitation. The owner subsequently approved visible scope and candidate-selection reasons, duplicate-request prevention, and goal-led type selection through [RUN-128](../run/run-20260929-128-personal-insight-selection-contract.md) and [RUN-129](../run/run-20260929-129-personal-insight-scope-and-requests.md). Project balancing, automatic expansion, and model/reasoning options remain future choices.
- [Personal Improvement Guide And Finding Contract](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md) (`passed`, foundation and bounded behavior evidence): versioned routing/playbooks, finding/result shape, abstention, counterevidence, and concrete application handoffs. RUN-136 establishes core v8's existing-proposal follow-through, followed by one owner-started product finding with usable application detail. Stable recommendation quality and actual owner benefit remain unverified. Owner review persistence and detailed staleness semantics remain future product work.
- `Personal Analysis Run Contract` (absorbed into FEAT-0110): independent Run identity, privacy boundary, runner selection, persistence, cancellation, and usage attribution.
- `Question And Discovery Analyzer` (absorbed into FEAT-0110): two deliberate entry paths, progress, one report, and source-backed viewing in the Insights layout; owner review decisions remain future work.
- `Markdown Report Handoff` (partly delivered by FEAT-0110): durable private report, readable Insights view, and repeatable download. An explicit save-to-workspace action remains future work.
- `Owner-Enabled Proactive Suggestions` (`product`, `fullstack`, later): incremental candidate discovery and controlled cadence based on changed evidence and review history.
- `Intervention Follow-Up` (`product`, `fullstack`, later): owner feedback and outcome review without a productivity score.

## First Increment And Next Use

As of 2026-10-02, the deliberate analysis → retained report → download → separate work-session path is usable. New Runs use core v8, request-feedback v4 and report v3. Analysis usage is included once under its selected Source while its metadata-only accounting Session remains excluded from ordinary work and retrieval. Successful question executions now supplement the earlier synthetic and subagent evidence; discovery quality in the live provider remains less directly observed.

The first increment does not complete every destination in this PRD. The next owner-use step is one real work task using a report's bounded handoff, then judging whether it helped. Review/adoption state persistence, model/reasoning controls, project/source/date selection, automatic evidence expansion, proactive scheduling and a direct work-location save action remain later choices. Repeated runs do not promise novel candidates, and no actual benefit follows merely from producing a finding.

The [2026-10-02 closeout review](../feature/feat-0110-executable-personal-insight-runs.md#first-increment-closeout-review) initially found Run-specific estimated-cost visibility, shared-shell overflow at the 320px floor with a classic scrollbar, and eight pre-existing pricing/schema test failures. The owner-approved [RUN-137](../run/run-20261002-137-insight-closeout-corrections.md) resolves those findings and adds missing GPT-6.1 Sol pricing with scoped retained-usage repair. The [backlog](../project/backlog.md#personal-improvement-insights) now owns the remaining intervention trial and later product choices. No additional paid analysis was used for these corrections.

## Continuity Notes

- `2026-09-27`: drafted after the owner expanded the Session Insights direction from a skill ranking into an interactive, personally useful AI-work improvement analyzer. The owner explicitly clarified that it must be useful beyond developer or Codex-harness work. PRD-0005's first skill-ranking increment remains a sibling boundary; the new analysis Run and review domain are proposed here.
- `2026-09-27`: the owner directed work to start after reviewing the research and guide proposal. This accepts the upper product boundary for feature planning. The model/privacy path remains an explicit open item and must be resolved before an analysis-Run Feature can be approved for implementation. The first evidence-contract Feature can be planned independently of that choice.
- `2026-09-27`: implementation planning showed that a three-excerpt-per-Session first sample may miss corrections and counterexamples inside long conversations. Before a first analyzer claims recurrence, planning must decide whether to admit a bounded targeted expansion inside that same Run or require abstention for unsupported types.
- `2026-09-28`: the owner asked to see the actual Insights screen before deciding detailed analyzer behavior. FEAT-0109 adds a non-executing visual preview with real skill counts and fictional analysis content. The choice of model path, Run persistence, and finding review behavior remains open for later Features.
- `2026-09-28`: after seeing the preview, the owner questioned whether an analyzer Run should be hidden from ordinary Sessions like maintenance or become an extensible main Session. The existing exclusion remains the approved baseline; follow-up and explicit promotion into ordinary work are now a decision for the analysis-Run Feature.
- `2026-09-28`: the owner further proposed finding and continuing improvement work from a normal Sessions entry. The planning question now separates Sessions visibility and conversation continuity from eligibility for future personal analysis; no implementation boundary has been changed yet.
- `2026-09-28`: the owner confirmed that a conversation created to analyze their work must not be fed back into later improvement analysis as if it were the work being studied. This fixes the evidence boundary regardless of whether that conversation is later made visible or continuable in Sessions; the latter presentation and transition choices remain open.
- `2026-09-28`: the owner chose an analysis-only boundary. Rather than continuing the analyzer's model conversation into work, a Run will produce a Markdown improvement design/report that the owner can use in a separate local work Session. The original report stays in private runtime artifacts; Sessions visibility and same-conversation continuation are no longer requirements for the initial analyzer.
- `2026-09-28`: the owner asked for repeatable analysis, a current model by default, a visible token-use warning, and persistent access to report attachments. Each retry/reanalysis is a new Run; a completed Run's Markdown can be downloaded repeatedly while its local runtime data is retained. Model/provider resolution and precise usage limits remain implementation decisions for the Run contract.
- `2026-09-28`: the owner asked to align the skill-count and last-use columns, narrow the skill area further, and browse improvement Runs as a list like ordinary Sessions when Markdown attachments accumulate. The Insights preview now treats Run history as a separate right-side browse surface with synthetic list rows; it does not add real Run records.
- `2026-09-28`: the owner directed removal of preview wording and fictional examples and asked for executable analysis through the complete UI. The owner chose the current Codex CLI with its Codex Company home as the first model path. FEAT-0110 implements explicit analysis-only Runs with frozen evidence, Codex profile/model, private Markdown reports, and retained history; further review actions and proactive scheduling remain future work.
- `2026-09-28`: after documentation and RUN-120 review, the owner chose to complete FEAT-0108's detailed guide before a real analysis Run. The evidence and guide foundations passed synthetic checks, and RUN-122 integrated the versioned selected guide with new executable Runs. No actual model report or owner-confirmed improvement has been reviewed yet.
- `2026-09-28`: the owner confirmed that analysis Runs must count toward estimated cost while remaining outside ordinary Sessions. The review found that FEAT-0110 had excluded Usage projection despite this PRD requirement. [RUN-125](../run/run-20260928-125-personal-insight-usage-accounting.md) corrects that planning gap and records the private Run execution directory and unassigned Project attribution.
- `2026-09-28`: the owner requested a skill-like behavior evaluation with independent analysis subagents and reviewers, guide refinement, and comparable reruns. [RUN-126](../run/run-20260928-126-personal-insight-guide-behavior.md) completed that bounded comparison and disclosed a previously hidden output limit in core v3. The observed requests for missing context support investigating the existing Targeted Evidence Expansion option; they do not approve or implement that future scope.

- `2026-09-29`: approved proceeding with the three bounded corrections identified after RUN-127; foundation guide/request validation precedes the fullstack report and scope display. Evaluate repeated fresh subagent outputs and synthetic browser behavior without claiming an actual CLI or owner-benefit result.

- `2026-09-29`: [RUN-130](../run/run-20260929-130-personal-insight-requested-context.md) completes the owner-requested comparison after supplying three precisely requested messages, with unchanged core v5 and fresh contexts for all six analyses and their reviewer. The added context informs candidate interpretation without duplicate requests, but disposition varies among a trial, further evidence, and abstention. This supports a bounded follow-up on the evidence threshold; it does not approve automatic expansion, establish stable usefulness, or replace the outstanding actual-product and owner-benefit checks.

- `2026-10-01`: [RUN-131](../run/run-20261001-131-personal-insight-decision-threshold.md) completes the threshold clarification and one targeted output-review scope correction. The final three fresh answers stay within the admitted trial, with a passing independent review and one narrow attribution suggestion. Earlier raw failures and four controls remain distinct evidence. Current guides are core v6/request-feedback v4/report v3. This bounded result does not establish discovery generalization, example independence, actual product execution, or owner benefit, and does not approve new sampling or automatic expansion.

- `2026-10-01`: the owner switches to clarification-and-correction questions. [RUN-132](../run/run-20261001-132-personal-insight-explanation-question.md) completes three real-input analyses, four controls and fresh independent review with the current guide and production ask selector unchanged. The bounded audit passes with precision suggestions; ordinary learning and unsupported apologies are distinguished from substantive corrections. A small future response-review trial is supported, while retrieval quality, generalization and owner benefit remain unverified. No guide change or automatic expansion is introduced.

- `2026-10-01`: the owner selects a previous execution-basis question for the proposed response-review comparison. [RUN-133](../run/run-20261001-133-personal-insight-explanation-trial.md) preserves two fresh current-code answers and a condition-hidden independent review. Both answers are adequate, with a small precision suggestion in the additional-instruction condition. Incremental benefit is not established; the comparison introduces no permanent instruction or product change.
