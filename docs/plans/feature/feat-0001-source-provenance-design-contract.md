# FEAT-0001: Source Provenance Design Contract

## Metadata

- ID: `feat-0001`
- Status: `passed`
- Type: `foundation`
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Fix how Claude and Codex source identity is represented in the design system so downstream UI Features do not confuse provenance with status semantics or invent component-local colors.

## Acceptance Contract

- The Design Constitution defines reusable semantic provenance roles for supported AI-session sources.
- Provenance roles remain separate from neutral, info, brand, success, warning, and danger status families.
- Source identity always has a readable label or equivalent non-color cue.
- Any required primitive or semantic addition follows Design Document Governance and records a version entry.
- Downstream specs can use the contract without choosing new raw values or redefining source meaning.

## Scope Boundary

- In:
  - Claude and Codex visual provenance roles
  - source-label fallback when a dedicated source role is unavailable
  - contrast and non-color identification constraints
  - constitution and governance ownership updates
- Out:
  - runtime CSS migration
  - template or route changes
  - new source types
  - source health or domain-status remapping

## Contract Surfaces

- [Design Constitution](../../policies/design/design-constitution.md)
- [Design Document Governance](../../policies/design/design-document-governance.md)
- semantic distinction between source provenance and product status

## Required Evaluators

- `contract`: confirm ownership, semantic completeness, contrast constraints, and downstream readiness.

## User-Visible Outcome

- No direct runtime change. Later renewed screens identify Claude and Codex consistently without implying success, failure, or action priority.

## Entry And Exit

- Entry point: approved `prd-0001` and the unresolved source-identity item in its Uncertainty section.
- Exit behavior: the durable contract is versioned and `feat-0002` can implement the roles without guessing.

## State Expectations

- Default: source identity remains legible with label and semantic provenance treatment.
- Loading: not applicable.
- Empty: unknown or absent source identity uses a documented neutral fallback.
- Error: source errors continue to use danger semantics independently of source identity.
- Success: source identity and source health can coexist without semantic collision.

## Dependencies

- `prd-0001` is `approved`.

## Likely Affected Surfaces

- `docs/policies/design/design-constitution.md`
- `docs/policies/design/design-document-governance.md`

## Pass Or Fail Checks

- Pass if every supported AI-session source has a reusable role or explicit neutral fallback.
- Pass if source identity cannot be mistaken for status through color alone.
- Pass if no downstream component must invent a raw source color.
- Fail if source identity reuses a feedback family as its meaning.
- Fail if the change is undocumented, unversioned, or dependent on external Figma access.

## Regression Surfaces

- existing semantic status families and state-to-UI mappings
- Design Brief, Constitution, Evaluation, and Governance ownership hierarchy

## Harness Trace

- Active spec doc: [spec-0001-source-provenance-design-contract](../spec/spec-0001-source-provenance-design-contract.md)
- Active run: [run-20260716-01-source-provenance-design-contract](../run/run-20260716-01-source-provenance-design-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [eval-0001-contract-source-provenance](../evaluation/eval-0001-contract-source-provenance.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft proposed a dedicated provenance contract rather than treating Claude and Codex identity as status.
- `2026-07-16`: approved and passed in `run-20260716-01`; runtime adoption is delegated to dependent Features.
