# EVAL-0055: Mermaid ELK Routing Contract — Design

## Metadata

- ID: `eval-0055-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260724-59`
- Attempt: `1`
- Feature: [feat-0055-mermaid-elk-routing-contract](../feature/feat-0055-mermaid-elk-routing-contract.md)
- Spec: [spec-0055-mermaid-elk-routing-contract](../spec/spec-0055-mermaid-elk-routing-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: global, sparse, and dense ERD visual comparison
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Checks And Evidence

- Like-for-like local captures were reviewed at `1440`, `920`, `700`, and `320`.
- Global ELK output replaces the very wide Dagre arc field with clearer vertical layers and mostly right-angle route segments.
- Dense-subject ELK output forms a readable trunk and aligned child rows; labels are easier to associate with their lines than in the Dagre fan.
- Sparse-subject ELK output preserves whitespace, entity hierarchy, labels, cardinality marks, and physical/application distinction without becoming needlessly dense.
- Rounded corners are consistent with the requested Draw.io-like direction and do not require a sharp-corner renderer patch.
- Narrow comparison cards stack and retain diagram-local horizontal scroll without page-level overflow.
- A selector would add state and control noise without a demonstrated need; one Schema-only default is the clearer composition.

## Evidence Gaps

- None for the synthetic adoption comparison. FEAT-0056 must repeat rendered evaluation inside the actual Schema shell.

## Findings

- None.

## Route

- Next action: `pass`.
