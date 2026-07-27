# FEAT-0061: Bounded-Value Consumer Normalization

## Metadata

- ID: `feat-0061`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Created: `2026-07-24`
- Updated: `2026-07-27`

## Goal

- Make every approved ordinary-screen consumer in the FEAT-0057 inventory present each bounded value family consistently as direct, logically labeled, or internal-only without changing the physical database contract.

## Acceptance Contract

- FEAT-0057's passed machine-readable registry and exact visible-consumer inventory define the only in-scope families and screens.
- Every `direct` consumer renders the complete family's approved physical vocabulary without translating only selected values.
- Every `logical-label` consumer renders all allowed and fallback states through the approved complete mapping and never falls back to a raw token.
- Every `internal-only` family is absent from ordinary screens and remains available only in explicitly approved diagnostics or operator evidence.
- Labels use approved short copy, while consequential scope, remote-read, destructive, recovery, or coverage explanations use the registry's bounded help contract.
- Server projections, templates, client-rendered replacements, empty/error states, search/filter options, detail facts, and form redisplay use the same family mapping.
- Physical values, request payloads, persisted rows, API identity, and migration behavior remain unchanged unless a separate approved Feature owns that change.
- Unknown or unexpected values fail safely with bounded unavailable or diagnostic treatment and are caught by deterministic tests; they do not display as an unreviewed raw token.
- Current UI behavior, source provenance, state consequences, responsive containment, and accessibility remain intact.

## Scope Boundary

- In:
  - current ordinary-screen consumers enumerated by passed FEAT-0057
  - shared presentation lookup or server projection boundary
  - complete-family labels, help, fallback, and technical-only suppression
  - GET, POST redisplay, partial replacement, empty, error, and unavailable paths
  - deterministic raw-token leak and mapping-parity tests
  - affected product and subject-owner documentation
- Out:
  - changing physical database values or columns
  - translating user-authored, Session, Document, or external content
  - a general runtime localization framework
  - inventing labels outside FEAT-0057
  - Atlassian Add layout and method interaction owned by FEAT-0054
  - unrelated screen redesign

## Surface Lanes

- Consumer contract lane:
  - path roots: FEAT-0057 registry and consumer inventory, shared label projections, and contract tests
  - dependencies: passed FEAT-0057
  - expected evidence: one mapping path per family, explicit fallback, and no duplicate screen-local dictionary
  - evaluator ownership: `contract`
- Server projection lane:
  - path roots: affected query, route, and form modules identified by the inventory
  - dependencies: consumer contract lane
  - expected evidence: physical values remain behavioral inputs while approved labels/help are separate presentation fields
  - evaluator ownership: `contract`, `functional`
- Presentation lane:
  - path roots: affected templates, shared client rendering, styles only where label containment requires it, and UI tests
  - dependencies: server projection lane
  - expected evidence: complete-family consistency, technical-only suppression, bounded help, responsive containment, and accessible state
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Drift-check lane:
  - path roots: registry parity, raw-token leak checks, route/UI tests, and durable owner docs
  - dependencies: all consumer lanes
  - expected evidence: future added values or fallback leaks fail deterministically
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- FEAT-0057 family keys, presentation modes, mappings, fallback, help, and visibility.
- Shared server or presentation lookup boundary.
- Affected route/form projection fields.
- Template and client-rendered consumer inventory.
- Raw-token leak and mapping-completeness checks.

## User-Visible Outcome

- The owner sees one coherent vocabulary for each state family across ordinary LocalBrain screens and no longer encounters a mixture such as a translated state beside an unexplained storage token from the same field.

## Entry And Exit

- Entry point: open, filter, submit, or recover any ordinary screen enumerated by FEAT-0057.
- Exit or transition behavior: the screen preserves the same physical behavior while showing the approved consistent label, help, or technical suppression.

## State Expectations

- Direct: all allowed values render unchanged and consistently.
- Logical label: all allowed values and permitted fallbacks use approved labels.
- Internal only: no ordinary UI element leaks the value.
- Unknown: bounded unavailable or diagnostic behavior; no silent raw fallback.
- Error redisplay: entered physical value is preserved while visible label and help remain consistent.

## Dependencies

- PRD-0009 is `approved`.
- FEAT-0057 must be `passed` before this Feature may be approved.
- FEAT-0054 owns Atlassian Add composition and must consume the same FEAT-0057 mappings for overlapping Atlassian fields.
- If FEAT-0057's consumer inventory spans unrelated surfaces that cannot converge in one to three loops, this draft must be split before approval.

## Likely Affected Surfaces

- FEAT-0057 machine-readable registry and shared presentation helper
- server query and route projections identified by the passed consumer inventory
- ordinary templates and client-rendered replacements identified by that inventory
- focused route, form, UI, registry, and raw-token leak tests
- affected data-model subject owners and product terminology documentation

## Pass Or Fail Checks

- Pass if every in-scope consumer resolves through the approved FEAT-0057 family contract.
- Pass if direct, logical-label, and internal-only behavior is complete for the entire family.
- Pass if POST error redisplay, partial updates, empty/error states, filters, and details use the same mapping.
- Pass if unexpected values fail safely and deterministic checks detect raw-token leakage.
- Pass if physical storage, payload identity, transitions, and migrations remain unchanged.
- Fail on a screen-local partial dictionary, mixed raw/logical values, internal token exposure, arbitrary translation, or behavior coupled to display labels.

## Regression Surfaces

- All affected routes, forms, filters, detail views, and partial-render paths named by FEAT-0057.
- Physical schema and compatible migrations.
- Source provenance and state consequences.
- Design Constitution state mapping, responsive containment, and accessibility.
- PRD-0008 Atlassian Add vocabulary consumers.

## Harness Trace

- Active spec doc: [spec-0061-bounded-value-consumer-normalization](../spec/spec-0061-bounded-value-consumer-normalization.md)
- Active run: [run-20260724-66-bounded-value-consumer-normalization](../run/run-20260724-66-bounded-value-consumer-normalization.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [contract](../evaluation/eval-0061-contract-bounded-value-consumer-normalization.md) — `PASS`
  - [design](../evaluation/eval-0061-design-bounded-value-consumer-normalization.md) — `PASS`
  - [functional](../evaluation/eval-0061-functional-bounded-value-consumer-normalization.md) — `PASS`
  - [ux-heuristic](../evaluation/eval-0061-ux-bounded-value-consumer-normalization.md) — `PASS`
- Latest fix note: not created

## Open Review Decisions

- Closed on `2026-07-24`: the passed registry initially contained `40` logical-label families, `14` internal-only families, and `75` ordinary visible-consumer declarations.
- Closed on `2026-07-27`: Local Context source-list review removed three redundant normal-state consumers (`source-type`, `readable`, and `enabled`) while retaining the selected source's useful status label, leaving `72` ordinary visible-consumer declarations.
- Closed on `2026-07-24`: the inventory passed as one bounded loop with a shared helper, bidirectional path/family drift checks, focused route/UI regression, and supported-width browser evidence; no split was required.

## Continuity Notes

- `2026-07-24`: initial draft separated user-visible vocabulary migration from the dictionary and parity foundation so physical values and screen behavior cannot be changed implicitly.
- `2026-07-24`: the owner authorized automatic sequential approval and execution. SPEC-0061 and RUN-20260724-66 normalized every declared ordinary consumer without changing physical values, passed all four required evaluations, and closed the final PRD-0009 Feature.
- `2026-07-27`: owner review found the Local Context source rail over-exposed four registry labels on every row. Normal rows returned to label, path, and document count; only selected-source status remains visible.
