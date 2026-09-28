# Personal AI-Use Improvement: Session-Grounded Research And Guide Proposal

## Status And Ownership

- Reviewed: `2026-09-27`
- Status: supporting research and historical proposal. The executable guide now lives in [`personal_insight_guides/`](../../../src/localbrain/personal_insight_guides/core-v2.md), under [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md); this research is not loaded by a Run.
- Proposed analyzer owner: [PRD-0018: Personal AI-Use Improvement Insights](../prd/prd-0018-personal-ai-use-improvement-insights.md) (`approved` for feature planning).
- Related first increment: [PRD-0005: Workflow And Skill Intelligence](../prd/prd-0005-workflow-and-skill-intelligence.md).
- Existing first view: [FEAT-0106: First Session Insights View](../feature/feat-0106-first-session-insights-view.md) owns only the observed skill ranking.
- Surface under discussion: the future personal AI-use improvement analyzer beside the skill ranking in Sessions Dashboard → Insights.

This is a design hypothesis, not a diagnosis of the owner's work. No private
Sessions were analyzed for this research review. Public sources are examples and candidate
methods; only admitted local evidence and owner feedback can establish whether a
recommendation applies here. The proposed side-by-side layout and analyzer expanded
beyond PRD-0005's first increment. PRD-0018 owns that upper boundary; its
executed Features and remaining decisions are tracked there. This document does
not change their status.

## Audience And Aim

The intended beneficiary is **any individual who uses AI to get work done**:
for example, writing, research, analysis, planning, learning, coordination, or
software development. The question is how that person can use AI more
effectively for their own goals and improve the surrounding work process. Agent
skills, `AGENTS.md`, and the Codex harness are possible interventions for some
people and tasks; they are one branch of this guide, not its organizing goal.

The source boundary is narrower than the audience. LocalBrain currently
observes Claude and Codex Sessions, so a future analyzer may describe only
behaviors visible there. It must not claim to know the person's entire job,
offline work, other AI tools, or actual outcomes solely from those Sessions.
The same analysis guide could later accept other approved sources through a
source-neutral evidence contract. Personal goals may differ: saving time,
improving quality, learning deeply, reducing cost, or gaining confidence can
lead to different recommendations for the same apparent pattern.

## Research: What Transfers And What Does Not

| Evidence | Transferable lesson | Limit |
| --- | --- | --- |
| [Professional writing experiment by Noy and Zhang](https://www.science.org/doi/10.1126/science.adh2586) | AI can help with drafting and editing bounded writing tasks; the useful division of work may change. | Short, self-contained tasks do not establish gains for long, context-heavy work. |
| [Cross-industry knowledge-work field experiment](https://www.microsoft.com/en-us/research/publication/shifting-work-patterns-with-generative-ai/) | AI can reduce time on independently changeable tasks such as email, while coordination-heavy work may remain largely unchanged. | Access to a tool does not imply every surrounding workflow changes. |
| [Consulting-task field experiment](https://www.hbs.edu/ris/Publication%20Files/dell-acqua-et-al-2026-navigating-the-jagged-technological-frontier_5c589c8c-fbb5-458f-b285-c944746cd717.pdf) | AI may improve work inside its task capability and degrade work outside it; people need to judge task fit and verify. | The experiments used then-current GPT-4 and selected consultant tasks; capability boundaries move. |
| [Knowledge-worker critical-thinking study](https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/) | Verification, integrating responses, and retaining ownership of decisions are part of effective AI use. | This is a survey of self-reported examples; it does not prove AI caused a loss of critical-thinking skill. |
| [Official OpenAI Codex harness account](https://developers.openai.com/blog/codex-as-a-platform) | An effective agent needs scoped context, tools, state, progress, recovery, and approval boundaries around the model. | This describes a platform architecture, not proof that LocalBrain needs the Agents API or a second general-purpose chat app. |
| [Official OpenAI skill and prompt guidance for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | Short, precise skill routing and selective reference loading can avoid irrelevant context and conflicting instructions. Revisit old `AGENTS.md` rules as models change. | Adding a skill or rule is not automatically helpful; broad skill descriptions can worsen selection. |
| [OpenAI Agents SDK maintenance practice](https://developers.openai.com/blog/skills-agents-sdk) and [OpenAI Runme case](https://developers.openai.com/blog/automating-repetitive-work-at-openai-with-codex) | Put repeatable mechanics in scripts; keep interpretation with the model; capture plans, commands, decisions, and dead ends for later runs. | These are practitioner case studies, not controlled causal estimates. |
| [Official OpenAI skill evaluation guide](https://developers.openai.com/blog/eval-skills) and [Anthropic agent evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Define outcome, process, and efficiency checks; test representative success and failure cases before promoting a guide. | A synthetic passing case does not establish improvement in the owner's real workflow. |
| [DORA 2025 report](https://dora.dev/research/2025/dora-report/), [small-batch capability](https://dora.dev/capabilities/working-in-small-batches/), and [user-centric capability](https://dora.dev/capabilities/user-centric-focus/) | AI amplifies the surrounding workflow. Smaller work units, feedback, and user outcomes matter more than generation volume. | DORA is largely organizational and observational; personal Session patterns are only hypotheses about cause. |
| [Generative AI at Work, published paper](https://danielle.li/assets/docs/GenerativeAIatWork.pdf) | AI can transfer tacit practices and help people learn in a setting with repeated, observable tasks. | This is a customer-support field study, not a direct estimate for another person's work. |
| [GitHub Copilot controlled task study](https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/) and [METR early-2025 randomized study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) | AI can accelerate a bounded coding task and slow experienced maintainers in a different, mature-codebase setting. Measure task fit and end-to-end result. | Neither result generalizes to all current models or workflows. [METR's 2026 update](https://metr.org/blog/2026-02-24-uplift-update/) reports possible later gains but says selection and time-measurement problems limit the estimate. |
| [Anthropic's effective-agent patterns](https://www.anthropic.com/engineering/building-effective-agents) | Begin with the simplest useful workflow; use routing or additional agent steps when distinct tasks and measured benefit justify them. | This 2024 engineering account notes that the tooling landscape has changed; it is a design pattern, not a current product contract. |

The practical principle is to treat outside best practices as a **catalog of
testable interventions**, not a fixed ideal that all people and Sessions must
match. The analysis should identify a local friction or missed opportunity,
show why it might matter to this person's goal, propose the smallest useful
intervention, and later ask whether it helped. More prompts, tokens, tool
calls, skills, or agent Runs are not outcomes by themselves.

## Improvement Taxonomy

An observation may fit more than one type. The analyzer must use a type to choose
questions and evidence checks, not force every Session into one class. Counts alone
never establish a problem or its cause.

| Type | Candidate local Session evidence | Possible recommendation | Required countercheck |
| --- | --- | --- | --- |
| 1. Goal and task framing | The desired result or constraints emerge only after several AI responses, or the output solves a different problem. | A compact brief with purpose, audience, examples, constraints, and a useful definition of done. | Was the conversation intentionally exploring possibilities rather than executing a known task? |
| 2. AI request and feedback | The person repeatedly repairs the same response shape, tone, level of detail, or evaluation criteria across Sessions. | A reusable request pattern, example of a good answer, or a deliberate draft → critique → revision loop. | Is the task genuinely different each time? Is the issue inaccurate AI output rather than the person's request? |
| 3. Context recovery | Background, prior decisions, source material, or audience are repeatedly reconstructed after an interruption. | A short handoff, source-linked note, or better retrieval entry point. | Was the context actually available and current? Avoid duplicating stale notes. |
| 4. Repeatable procedure | Similar steps, prompts, or tool actions recur across distinct Sessions with stable inputs and outputs. | A checklist, template, script, runbook, or narrowly triggered skill, depending on the amount of judgment. | Does the sequence vary materially? Would automation hide necessary review or human contact? |
| 5. Learning and explanation | The person asks for underlying reasons or repeatedly returns to a concept while using AI. | An explanation-first interaction, worked example, comparison, or focused learning resource. | Is the follow-up healthy exploration or caused by an incorrect answer? Do not label curiosity as inefficiency. |
| 6. Verification and rework | An AI-produced claim, analysis, document, or artifact is repeatedly corrected late or used without checking a consequential assumption. | Earlier fact checks, source comparison, a review checklist, or a focused evaluation case. | Did requirements change? Is the apparent correction actually a new preference? |
| 7. Tool and information access | The person repeatedly copies between systems, re-searches authoritative facts, or corrects stale AI knowledge. | A source-of-truth link, scoped retrieval tool, or authorized read-only integration. | Is the source authorized, reliable, and worth maintaining? |
| 8. Decision memory | The same alternatives are debated because earlier reasoning and results are hard to recover. | A concise decision note with rationale, evidence, date, and revisit trigger. | Was reconsideration appropriate because circumstances changed? |
| 9. AI task fit and cost | AI is repeatedly used for a task it handles poorly, or a simple task causes disproportionate prompting and review effort. | Change the human–AI division of work; use a simpler tool or method, a narrower call, or a different model when warranted. | Session time and token count do not reveal net effort or quality. Ask for outcome evidence. |
| 10. Work flow and personal value | Many activities start without completion, or AI accelerates output that does not advance the person's stated goal. | Smaller steps, explicit priority, an outcome check, or a deliberate pause. | A transcript rarely contains all outside commitments or values; the person must confirm what matters. |
| 11. Assistant configuration and harness fit | Repeated unwanted skill loads, conflicting instructions, lost task context, or avoidable execution friction are visible. | Review assistant settings, skill metadata, `AGENTS.md`, context routing, approval boundaries, or checkpoint state when this environment supports them. | Was the behavior required by policy or appropriate caution? Never weaken a real safety boundary to improve a metric. |

Types 1–10 apply across many kinds of AI-assisted work. Type 11 examines the
agent's own configuration and runtime when the person uses a configurable
assistant such as Codex. These types are adapted from the sources above; the
table is a proposed LocalBrain taxonomy, not a published external
classification.

Current normalized activity retains messages and tool names but intentionally
omits opaque tool inputs and results. It therefore cannot yet substantiate
touched files, command sequences, error equivalence, or tool success from that
projection alone. In particular, types 4, 6, and 7 must show partial or
unavailable coverage until a bounded, approved source-neutral signal contract
provides the needed evidence. The retained explicit skill-use ledger proves
invocation counts only, not skill quality or workflow success.

## Proposed Analysis Guide

### Core Rules For Every Run

1. Interpret the person's question or `Discover` request and the outcome they
   value for this work (for example speed, quality, learning, or confidence).
   State the selected Session scope, source coverage, time range, and
   analysis-guide version. Ask about the goal only when it changes the advice.
2. Retrieve a bounded, representative set of eligible primary work evidence.
   Keep source references; distinguish direct observations from interpretation.
   Exclude the analyzer's own runs and other maintenance activity from the
   behavioral evidence pool so recommendations do not feed themselves.
3. Route only to relevant taxonomy playbooks. For each candidate, look for
   confirming and disconfirming examples, including a successful case. Do not
   turn repeated words, large token use, long Sessions, or repeated questions
   into an inefficiency claim by themselves.
4. Compare candidate interventions against what already exists. Prefer the
   least complex remedy that advances the person's goal. An acceptable
   result is `no actionable finding` or a clarifying question.
5. Return at most a small number of findings, each with: observation, evidence
   links, alternative explanation, affected scope, suggested change, expected
   benefit, effort/risk, and one observable follow-up check. Mark inference
   and missing coverage explicitly. Do not present a personal productivity
   score or claim a causal gain from Session traces alone.
6. Leave generated edits and external actions in a reviewable proposal state.
   The owner may accept, revise, defer, reject, or mark a finding inapplicable.
   Record that feedback for future deduplication and guide evaluation.

### Playbook Contract

Each type-specific playbook should define:

- **Trigger and exclusions:** which admissible signals justify inspection and
  which common lookalikes do not.
- **Evidence questions:** what to inspect across Sessions, what counts as a
  distinct recurrence, and what coverage is missing.
- **Intervention chooser:** when the best output is a different way of asking
  or reviewing AI, a template, learning resource, checklist, skill, script,
  document, tool, task brief, assistant setting, or no change.
- **Output sketch:** one short finding and a concrete, reviewable artifact
  proposal, not a generic best-practice lecture.
- **Evaluation:** one before/after observation or user-reported outcome and at
  least one negative example that should suppress a recommendation.
- **Version and source references:** public rationale, last review date, and
  changes to the guide so later Runs can be explained.

Keep a small core router and load only selected playbooks and references for a
Run. The guide belongs to the analyzer; it should not be appended wholesale to
every Session or to the repository-wide `AGENTS.md`. [Official OpenAI guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
specifically warns that broad skills and accumulated instructions can crowd or
conflict in context.

### Intervention Choice

| If the repeated need is… | Prefer… |
| --- | --- |
| Better alignment between a request and the answer | A clearer purpose, audience, constraints, example, or feedback pattern. |
| Deeper understanding rather than faster output | An explanation mode, worked example, self-check, or learning resource. |
| More reliable claims or decisions | Source comparison, a review checklist, or an explicit human judgment step. |
| A repeated communication or analysis format | A lightweight template or reusable example. |
| A stable command or transform with objective results | Script or existing automation. |
| A recurring task needing contextual judgment and tools | Focused skill with a narrow trigger and reviewable output. |
| A rule applicable to nearly every task in one configurable assistant environment | A short persistent instruction such as `AGENTS.md`, after checking for duplication and conflict. |
| Domain knowledge, rationale, or an answer the agent should retrieve when relevant | Source-linked document or decision note. |
| A recurring error pattern with clear expected behavior | Focused validation or evaluation case. |
| Missing access to authoritative information | Scoped tool or retrieval integration after authorization review. |
| One-off ambiguity or changing priorities | Better task brief or human decision, with no persistent rule. |

## Product And Data Shape For A Later Feature

- **Insights layout:** retain the existing skill ranking in a narrower left
  region; place a right-side analyzer with a question field, a `Discover`
  action, recent analysis results, and source-backed finding cards. On smaller
  screens, stack these regions in reading order. The layout is proposed; it is
  not part of FEAT-0106's approved first view.
- **Run modes:** `Ask` follows the owner's question; `Discover` scans for
  worthwhile candidates without a question. Both use the same evidence and
  guide contract. A later owner-enabled cadence may generate proactive
  findings after new Sessions arrive; merely opening Insights should not start
  a costly model run.
- **Candidate and Run separation:** cheap, incremental source-backed signals
  may identify what to inspect. A bounded analysis Run performs interpretation
  and produces a report. Reading a report or changing dashboard dates should
  not repeat model analysis. Changed source evidence should mark a finding
  stale or eligible for refresh, not silently rewrite a reviewed conclusion.
- **Independent domain:** an analysis Run owns its question, scope, guide
  version, evidence manifest, status, cost/usage, and report. A finding owns its
  type, evidence references, uncertainty, recommendation, review state, and
  follow-up outcome. Reuse generic runner/process and Session retrieval
  primitives where appropriate; do not make Workstream or its maintenance-run
  schema the semantic owner of this feature.
- **Retention and privacy:** all private prompts, retrieved excerpts, traces,
  and reports remain in local runtime storage outside Git. If a source Session
  disappears, an evidence pointer may become unavailable; do not treat it as
  still verified merely because the skill-use counter retains an observation.
  Use a local model or another explicitly approved path for private content;
  public best-practice research does not authorize sending Sessions outside.

## Evaluation And Review Boundary

Before implementing any category, define synthetic positive, negative, and
ambiguous cases. Review groundedness, false positives, usefulness, coverage,
and the artifact choice, then compare the accepted intervention with an
owner-confirmed outcome after use. An outcome can be clearer writing, better
decisions, stronger understanding, fewer repeated clarifications, shorter
reorientation, fewer verification failures, or an easier handoff; no single
quantity becomes a universal productivity score. The
[official OpenAI evaluation guide](https://developers.openai.com/blog/eval-skills)
and [Anthropic evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
support trace and rubric checks, while the [METR studies](https://metr.org/blog/2026-02-24-uplift-update/)
show why perceived speed and raw Session time are weak substitutes for measured
benefit.

At the time of this research, the next planning step was one bounded Feature at
a time for evidence coverage, guide/run contract, and the Insights interaction.
The current implementation and approval status are recorded in PRD-0018 and its
Features. This research itself does not authorize a private Session analysis,
external model call, or automatic changes to skills, `AGENTS.md`, tools, or
Workstreams.
