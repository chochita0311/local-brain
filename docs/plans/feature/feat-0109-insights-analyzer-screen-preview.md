# FEAT-0109: Insights Analyzer Screen Preview

## Metadata

- ID: `feat-0109`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Created: `2026-09-28`
- Updated: `2026-09-28`

## Goal

Let the owner inspect a concrete Insights screen for the proposed personal analyzer before deciding its detailed Run and review behavior.

## Acceptance Contract

- `/sessions-dashboard/insights` presents the existing source-backed skill ranking in a compact left column and an analyzer plus Run-history preview in the wider right column. The ranking still uses real retained observations, with count and last-use values aligned to shared column headings.
- The right column shows the two proposed entry paths, asking a question and discovering opportunities without a question, with the scope and deliberate-execution intent legible before the action.
- The preview shows where the future start area will disclose the chosen latest compatible analysis model, Session scope, potentially substantial token use, and the fact that reanalysis creates another Run with additional usage.
- The right column shows a Sessions-like list of clearly synthetic analysis Runs, including a completed finding and a no-finding result. Opening the first row reveals an example observation, alternative explanation, proposed trial, follow-up check, and the intended place for source evidence and review decisions. Neither row represents a result from the owner's Sessions.
- The synthetic result shows where a completed Run's Markdown attachment can be downloaded again and where reanalysis would start a new Run. These controls remain unavailable in the preview.
- The preview's analysis controls cannot call a model, read private Session text, save a report, or alter review state. Their unavailable state is explicit in the UI. Native sample disclosure remains inspectable.
- At narrower viewports, the columns stack in reading order without horizontal page overflow or nested scrolling; the skill ranking remains readable down to the constitution's 320px floor.

## Scope Boundary

- In: Insights template structure, page-local styles using established semantic tokens, synthetic preview copy, accessible presentation states, and responsive layout.
- Out: real analyzer Run, guide execution, live model selection, Session evidence retrieval, API or database change, report persistence or download, source links for synthetic examples, review-state mutation, and proactive scheduling.

## Contract Surfaces

- Existing route and `skill_insights_data` context remain the real left-column source.
- Synthetic example is tracked UI copy, explicitly labeled as an example and disconnected from private runtime Sessions.
- Analyzer actions are visibly unavailable until a later approved product Feature supplies execution behavior.

## Pass Or Fail Checks

- The owner can identify the skill ranking, question path, discovery path, Run list, and report shape in one Insights visit. The skill table's headings and values stay aligned.
- Long skill names, ten or more ranking rows, and narrow widths remain contained.
- The preview remains clearly distinguishable from a real analysis result and contains no active Run or review action.
- Existing Usage & Cost navigation, Session Insights ranking values, and skill extraction coverage notice remain intact.
- At desktop and narrow widths, the screen follows the Design Constitution's typography, surface, spacing, focus, and content hierarchy rules.

## Dependencies

- Approved PRD-0018 upper boundary and existing FEAT-0106 skill-ranking surface.
- FEAT-0107 evidence and FEAT-0108 guide are not runtime dependencies for this visual preview.

## Regression Surfaces

- Sessions Dashboard navigation, skill ranking and last-used time display, coverage notice, shell layout, and small-viewport containment.

## Harness Trace

- Spec: [SPEC-0109](../spec/spec-0109-insights-analyzer-screen-preview.md)
- Run: [RUN-20260928-119](../run/run-20260928-119-insights-analyzer-screen-preview.md)
- Execution profile: `frontend-product`
- Initial preview evaluator reports: [design](../evaluation/eval-0109-design-insights-analyzer-screen-preview.md), [functional](../evaluation/eval-0109-functional-insights-analyzer-screen-preview.md), [UX heuristic](../evaluation/eval-0109-ux-insights-analyzer-screen-preview.md). They predate the owner-guided model, usage, attachment, column, and Run-list revisions.

## Continuity Notes

- `2026-09-28`: the owner asked to see the screen before deciding detailed functionality. This explicitly approves a reviewable visual preview, while the analysis engine and persistent Run behavior remain later decisions.
- `2026-09-28`: the owner added repeatable new Runs, a current supported model default, a token-use warning, and recurring access to each completed Markdown attachment. The preview now reserves visible places for these rules without enabling execution or download.
- `2026-09-28`: the owner requested a narrower skill rail with correctly aligned count and last-use columns and a Sessions-like list for improvement Runs. The preview now places two explicit fictional Run rows in a separate history surface; actual Run retrieval remains later work.
- `2026-09-28`: direct browser inspection of this revision at 1440px, 1140px, and emulated 320px confirmed the compact table columns, consistent stacked date/time, separate right-side Run list, and no horizontal document overflow. The fictional Run rows and disabled file controls remain preview-only; the prior evaluator reports are historical.
- `2026-09-28`: RUN-119 passed this preview boundary. FEAT-0110 later replaced its fictional content and disabled controls with live Run history and execution; this Feature remains historical evidence for the preview rather than the current screen owner.
