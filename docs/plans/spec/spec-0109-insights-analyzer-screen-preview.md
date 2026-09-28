# SPEC-0109: Insights Analyzer Screen Preview

## Metadata

- ID: `spec-0109`
- Status: `approved`
- Parent Feature: [FEAT-0109](../feature/feat-0109-insights-analyzer-screen-preview.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Created: `2026-09-28`
- Updated: `2026-09-28`

## Implementation Goal

Extend the current Insights route in the existing LocalBrain design language so the owner can judge the analyzer's layout, entry paths, and result explanation from the rendered screen.

## Screen Contract

- Keep the page shell, heading, Usage & Cost link, and existing extraction-coverage notice. Change the heading copy to describe both the real skill ranking and the analyzer preview.
- Place a compact skill leader and ranking in a left column narrower than one third of the content width where space allows. Keep real skill names, counts, and local last-used times. Use one semantic three-column table so skill, count, and last-use headings align with every row; no ordinal column. Stack local date and time consistently within the last-use cell, and let long skill names wrap rather than widening the rail.
- Place one principal analyzer panel in the right column. Show a clear preview label, one question entry composition, and one no-question discovery composition. Their action controls are disabled and explained at the point of action. Do not accept or save text in this Feature.
- Add a concise execution notice below the two entry paths: the eventual model and Session scope are shown before a Run, token use may be substantial, and repeating an analysis creates a new Run with additional usage. Do not display a fabricated current model identifier or cost estimate in this preview.
- Below the analyzer, show a separate Run-history panel that resembles the Sessions browse list. Two synthetic Run rows demonstrate completed finding and honest no-finding outcomes, with the first initially expanded through native disclosure. The expanded finding demonstrates an observation, alternate explanation, practical trial, follow-up check, evidence position, and proposed review states. All example material is labeled synthetic and has no Session URL or invented execution timestamp.
- Show a clearly disabled Markdown-download action and new-Run reanalysis action beside the synthetic report attachment explanation. They convey that completed reports stay available per Run without implying an existing file or working analyzer.
- Use existing `analysis-panel`, heading, control, text, surface, and status tokens. Avoid foreign illustrations, gradients, or a second design language. Stack columns at a width where the compact list ceases to fit; move the Run attachment cue below its title at narrow widths and preserve the skill table without horizontal scrolling at the viewport floor.

## Behavior And Accessibility

- Each sample Run row uses native `<details>` and `<summary>` so it works without JavaScript, is keyboard reachable, and does not imply backend analysis.
- Preview action buttons, reanalysis, Markdown download, and text entry are disabled and have adjacent explanatory copy. No fake success state, model call, Session text read, network write, file download, or stored review decision occurs.
- The visual preview remains honest when there are no skill observations: the left existing empty/partial state still renders beside the right analyzer preview.
- Long names and example prose wrap within the column. Text labels, not color alone, distinguish the preview from real source-backed data.

## Ownership

- `src/localbrain/templates/session_insights.html`: structural view and synthetic copy.
- `src/localbrain/static/styles.css`: Insights page layout and responsive component styling.
- No route, schema, query, or JavaScript change is required.
- Update `README.md` only if a user-visible usage instruction changes. This Feature creates a visual review surface, not a working analysis action.

## Evaluation Focus

- Design: compare the rendered Insights screen with its current shell and family panels at wide and narrow viewports; inspect type hierarchy, card weight, spacing, and overflow.
- Functional: confirm real ranking values/coverage remain visible, disclosure opens and closes, disabled controls do not initiate work, and Usage & Cost navigation remains available.
- UX heuristic: check whether the owner can tell real ranking data from synthetic example and understand the two entry paths before implementation decisions.

## Open Blockers

- None for the visual preview. Model and result persistence remain outside this Feature.
