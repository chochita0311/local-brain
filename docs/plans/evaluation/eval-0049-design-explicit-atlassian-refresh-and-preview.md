# EVAL-0049: Explicit Atlassian Refresh And Preview — Design

## Metadata

- ID: `eval-0049-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260723-54`
- Attempt: `1`
- Feature: [feat-0049-explicit-atlassian-refresh-and-preview](../feature/feat-0049-explicit-atlassian-refresh-and-preview.md)
- Spec: [spec-0049-explicit-atlassian-refresh-and-preview](../spec/spec-0049-explicit-atlassian-refresh-and-preview.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `atlassian-refresh-preview`
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated the explicit refresh preview against the Design Constitution and `screen-alignment` `extend` rules, including hierarchy, consequence, dense target rows, freshness, unavailable execution, contextual entry, and supported widths.

## Checks And Evidence

- The screen reuses the LocalBrain shell, heading, card, semantic badge, form, button, and metadata families. It introduces no foreign dashboard, modal, or raw color system.
- The top summary exposes known count, default selection, expected remote reads against 20, and the one-Run consequence before the target checklist.
- Each target preserves a stable reading order: selection, Item identity, coverage, freshness, Source/Site/Space, canonical URL, read count, last check, and content time.
- Current, due, stale, unavailable, reference, metadata, and indexed states use textual semantic labels; color is never the only carrier.
- The maintenance handoff is visually subordinate to scope selection and truthfully disables execution when no host-side executor is available.
- Synthetic populated states rendered at `1440`, `920`, `700`, and exact emulated `320`. Long mixed-language titles, domains, URLs, labels, and timestamps wrap within their rows. Document and body scroll widths equal every tested viewport.
- Contextual links on Atlassian, Space, Item, Workstream, and Thread surfaces state the target scope instead of multiplying unlabeled global buttons.

## Evidence Gaps

- A live terminal partial-result screen was not browser-rendered because the development server intentionally had no external executor. Terminal projection and retry markup are covered by synthetic functional and UI contract tests.

## Findings

- No blocking hierarchy, containment, semantic-state, or shell-alignment issue remains.

## Route

- Next action: release Design evaluation for FEAT-0049.
