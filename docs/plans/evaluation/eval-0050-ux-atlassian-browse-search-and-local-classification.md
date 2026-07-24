# EVAL-0050: Atlassian Browse, Search, And Local Classification — UX Heuristic

## Metadata

- ID: `eval-0050-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260723-55`
- Attempt: `1`
- Feature: [feat-0050-atlassian-browse-search-and-local-classification](../feature/feat-0050-atlassian-browse-search-and-local-classification.md)
- Spec: [spec-0050-atlassian-browse-search-and-local-classification](../spec/spec-0050-atlassian-browse-search-and-local-classification.md)
- Execution Profile: `fullstack-product`
- Surface Lane: find → judge source/freshness → remember/classify → optionally organize
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated local-search trust, Source/Site distinction, knowledge-base use without Workstreams, classification clarity, archived recovery, remote/local comprehension, evidence orientation, explicit external navigation, filter burden, and responsive reachability.

## Checks And Evidence

- The screen states that browse and filters use stored local state and do not start remote or maintenance work. Refresh remains a separately named preview action.
- Source Instance, Site domain, Space, coverage, freshness, and matched search roles let the user judge what a result represents before opening it. Identical keys from different domains remain distinguishable.
- Topic, Tag, attention, and Workstream are presented as independent choices. An Item can carry notes and classifications with no Workstream mapping, so knowledge retention is not forced into active work organization.
- The detail boundary uses “remote facts · last known,” “local only,” “local evidence,” and “refresh state” language. Provider metadata/body cannot be mistaken for the user's note or a Session/Document sighting.
- Canonical Atlassian URLs are explicit user-activated actions. Evidence links return to LocalBrain owners, and the screen does not prefetch or imply that opening detail refreshes remote content.
- Archived Items disappear from default browse/search but remain directly reachable and are recoverable through the explicit attention filter. The distinction is visible rather than destructive.
- Dense filters remain one ordinary form with reset/search actions; compact widths stack controls and results in document order without hiding required fields or causing horizontal overflow.
- Search service badges, titles, paths, source context, and excerpts remain separate after the compact-layout correction, improving scanability without adding another control family.

## Evidence Gaps

- Very large real-world Topic/Tag vocabularies and inventory pagination are outside this Feature's demonstrated synthetic dataset. The current local query and wrapping contracts remain bounded, but later scale evidence may justify a separate usability Feature.

## Findings

- No blocking ambiguity, forced organization, hidden remote action, archived dead end, or responsive reachability issue remains.
- No optional heuristic backlog item is required for the approved first scope.

## Route

- Next action: release UX Heuristic evaluation and Run acceptance.
