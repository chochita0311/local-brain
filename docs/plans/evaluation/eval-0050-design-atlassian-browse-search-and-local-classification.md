# EVAL-0050: Atlassian Browse, Search, And Local Classification — Design

## Metadata

- ID: `eval-0050-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260723-55`
- Attempt: `1`
- Feature: [feat-0050-atlassian-browse-search-and-local-classification](../feature/feat-0050-atlassian-browse-search-and-local-classification.md)
- Spec: [spec-0050-atlassian-browse-search-and-local-classification](../spec/spec-0050-atlassian-browse-search-and-local-classification.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Atlassian browse, Item detail, and grouped global Search
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated the new surfaces against the Design Constitution and `screen-alignment` `extend` rules, including browse/setup hierarchy, filter density, source and status legibility, remote/local/evidence/refresh separation, long content, result rows, and supported widths.

## Checks And Evidence

- Jira and Confluence remain the first service choice; Browse and Add/discover form a separate task choice. Default Browse presents local search, filters, and known Items before setup or refresh actions.
- Item rows preserve a stable reading order: remote key, coverage/freshness/attention, title, Source/Site/Space, local Topic/Tags, check time, local detail, and explicit external navigation.
- Item detail uses four semantic regions. Remote last-known facts lead, local-only memory and work relations remain visually distinct, local evidence keeps its owner identity, and maintenance history stays subordinate.
- Coverage, current/due/stale/unavailable freshness, attention, Topic, Tag, local-only, and remote-last-known meaning use text labels; color is never the only carrier.
- Search results group one Item per card and expose an Atlassian service badge, title, canonical URL, Source/Site/Space, coverage, freshness, matched roles, and excerpt without resembling a live provider result.
- Synthetic populated screens rendered at `1440`, `920`, `700`, and exact emulated `320`. Long titles, domains, metadata JSON, body text, Topic/Tag labels, URLs, notes, and evidence locations wrap inside their owners; document and body scroll widths equal the tested viewport.
- Browser QA found one pre-evaluation badge/title collision in Atlassian Search. The result grid now sizes the badge by content on wide screens and stacks badge then result body on compact screens; desktop and exact `320` rechecks show no collision or page overflow.
- The final browser pass reported no console messages and only successful local document, stylesheet, and script requests.

## Evidence Gaps

- Real company content and unusually large production inventories were intentionally not rendered. Long-content and populated-density evidence is synthetic.

## Findings

- No blocking hierarchy, containment, source-legibility, responsive, or shell-alignment issue remains.

## Route

- Next action: release Design evaluation for FEAT-0050.
