# EVAL-0018: Conversation-Focused Session Details Design

## Metadata

- ID: `eval-0018-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260717-18`
- Attempt: `1`
- Feature: [feat-0018-conversation-focused-session-details](../feature/feat-0018-conversation-focused-session-details.md)
- Spec: [spec-0018-conversation-focused-session-details](../spec/spec-0018-conversation-focused-session-details.md)
- Execution Profile: `fullstack-product`
- Surface Lane: primary and child conversation reading
- Created: `2026-07-17`

## Scope And Mode

- Applied screen-alignment in `extend` mode. Existing detail width, source provenance, metadata strip, timeline rail, cards, semantic colors, and responsive shell remained authoritative.

## Rendered Evidence

- The detail strip now labels the stored value as `원본 이벤트`, while the conversation heading explains that tool activity remains in source events but is hidden from this reading surface.
- Parent details retain the established Subagents section above the conversation and use the same valid normalized child destinations as the inventory.
- Child details retain the same detail family while adding a bounded parent notice, parent backlink, and source-specific child role labels.
- Tool-only details keep the complete heading and metadata context and use a bordered empty state instead of a broken blank timeline.
- Long Korean, English, unbroken identifiers, and file paths wrapped inside message cards.
- Synthetic 1440, 920, 700, and 320px renders showed no horizontal document, message-card, or Subagents-row overflow. At 320px each measured message and child row had equal client and scroll widths.
- A mobile Lighthouse snapshot scored Accessibility `100` and Best Practices `100`; the remaining SEO finding is unrelated to this detail Feature.

## Findings And Regression

- No blocking visual finding.
- The legacy Claude fallback retains the established lazy-view notice without creating a second design family.

## Route

- Next action: `pass`
