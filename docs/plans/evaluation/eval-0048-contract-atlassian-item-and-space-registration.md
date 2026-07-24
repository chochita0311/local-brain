# EVAL-0048: Atlassian Item And Space Registration — Contract

## Metadata

- ID: `eval-0048-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260723-53`
- Attempt: `1`
- Feature: [feat-0048-atlassian-item-and-space-registration](../feature/feat-0048-atlassian-item-and-space-registration.md)
- Spec: [spec-0048-atlassian-item-and-space-registration](../spec/spec-0048-atlassian-item-and-space-registration.md)
- Execution Profile: `fullstack-product`
- Surface Lane: registration contract → partial catalog maintenance → durable ownership
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated URL recognition, Source Instance/Site resolution, stable Item and Space identity, duplicate behavior, coverage defaults, Space-candidate Run composition, remote-call boundaries, schema compatibility, privacy, and owner documentation.

## Checks And Evidence

- Registration accepts only an HTTP(S) Jira issue/project or Confluence Page/Space URL. Key-only text, REST endpoints, service mismatch, unsupported URL shapes, and unconfigured domains fail before mutation and do not create unresolved evidence or a lookup.
- A direct URL selects a Site automatically only when service and normalized domain identify exactly one enabled configured Site. Multiple matching Source Instances require explicit selection and cannot cross-merge Items with the same key.
- Item registration reuses the FEAT-0046 `external_resources.id` identity and Site-scoped canonical URL. Duplicate input does not overwrite coverage, attention, local title/summary, Workstream relations, or remote state.
- Space registration stores a normalized canonical navigation URL and an explicit coverage axis. Jira defaults to `selected-content`; Confluence defaults to regular-Page `full-content`; duplicate registration preserves an existing explicit coverage value.
- Page load, service switching, form entry, local registration, and inventory reads contain no external dispatch. The application exposes no hidden browse-time capability inspection.
- Space discovery requires a current FEAT-0044 capability, an injected host-side executor, and an explicit FEAT-0045 maintenance Run. Its manifest contains one Source Instance/Site-scoped target, one allowlisted metadata operation, and a call budget of one.
- Current provider catalogs expose no complete project/Space-list operation. The bounded Jira or Confluence search projection is therefore always labeled partial, deduplicates no more than 200 candidates, registers nothing automatically, and requires a separate confirmation form.
- Older databases receive additive `atlassian_spaces.canonical_url` and `coverage` columns with service-specific backfills; retained Space IDs and Item relations are unchanged.
- Durable data-model, architecture, privacy, product, and design-state owners match the implementation. The generated baseline contains 31 ordinary tables, one FTS5 object, 36 physical relations, 32 explicit indexes, 367 columns, 24 application relations, and nine subjects.

## Evidence Gaps

- No company Atlassian content or live Space catalog was fetched. Provider capability shape was inspected only to establish the approved partial-catalog boundary.

## Findings

- None.

## Route

- Next action: `pass` and release Design, Functional, and UX Heuristic evaluation.
