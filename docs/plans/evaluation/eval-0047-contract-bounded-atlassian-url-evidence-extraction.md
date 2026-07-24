# EVAL-0047: Bounded Atlassian URL Evidence Extraction — Contract

## Metadata

- ID: `eval-0047-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260723-52`
- Attempt: `2`
- Feature: [feat-0047-bounded-atlassian-url-evidence-extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md)
- Spec: [spec-0047-bounded-atlassian-url-evidence-extraction](../spec/spec-0047-bounded-atlassian-url-evidence-extraction.md)
- Execution Profile: `foundation-contract`
- Surface Lane: bounded parsing → source-backed reconciliation → durable ownership
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated eligible source boundaries, parser/result allowlists, Item URL recognition, configured Site mapping, source location/cardinality, fingerprints, derived lifecycle, stable Item retention, privacy, and downstream readiness.

## Checks And Evidence

- Only primary work Sessions and enabled registered Context Documents can own evidence. Maintenance Sessions, subsessions, disabled roots, repository paths, and arbitrary files are excluded.
- Visible text extraction requires an HTTP(S) URL. Key-only strings, Space-only links, unknown domains, API URLs, and ambiguous configured Source mappings create no Item, evidence, unresolved placeholder, or lookup.
- Tool-result extraction requires an approved FEAT-0044 read call and walks only bounded structural containers plus URL, remote-ID, and title field names. Depth, node, candidate, and string-size limits prevent broad retention; opaque result bodies and unrelated fields are never persisted.
- `atlassian_item_evidence` references the stable FEAT-0046 Item plus exactly one Session/source-path or Document owner. It stores no excerpt or generic payload column.
- `atlassian_evidence_scans` separates source, extractor, and enabled-Site fingerprints. Session scan identity is `(session_id, source_path)` so multi-file Sessions remain independently current; Document identity is one-to-one.
- Recognition maps a Jira issue or Confluence Page URL to exactly one enabled configured Site/service before creating or reusing a reference stub. Observed remote IDs/titles remain unconfirmed evidence and never bind remote identity or overwrite local Resource fields.
- Successful changed scans upsert current evidence and remove only obsolete sightings from that source. Errors retain prior sightings; disappearing evidence, source disablement, and source deletion do not delete the stable Item or remote/local state.
- Parser/scanner code contains no Gateway dispatch, network, model, freshness, classification, or organization mutation.
- Durable schema owners and generated artifacts agree on 31 ordinary tables, one FTS5 object, 36 physical relations, 32 explicit indexes, 365 columns, 24 application relations, and nine subjects.

## Evidence Gaps

- None for the approved local foundation boundary.
- No company data, live connector, model invocation, or visible UI was exercised.

## Findings

- None remaining after FIX-0047.

## Route

- Next action: `pass` and run final Functional evaluation.
