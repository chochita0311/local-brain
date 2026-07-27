# EVAL-0060: Session Related Context Rail — Design

## Metadata

- ID: `eval-0060-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260724-65`
- Attempt: `1`
- Feature: [feat-0060-session-related-context-rail](../feature/feat-0060-session-related-context-rail.md)
- Spec: [spec-0060-session-related-context-rail](../spec/spec-0060-session-related-context-rail.md)
- Execution Profile: `fullstack-product`
- Surface Lane: responsive detail rail
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Alignment Declaration

- Mode: `extend`.
- Target: repository Design Constitution and existing Detail/Read family.
- Affected lanes: primary Session reading grid, context rail, reason and availability states.
- Figma design-system lookup could not be meaningfully issued because the repository and approved source set own no durable Figma file key; no external Figma artifact was created.

## Checks And Evidence

- The rail reuses established panel, badge, type, provenance, border, elevation, and semantic-token vocabulary.
- At wide width, the `796px` conversation column and `340px` rail preserve the reading hierarchy without compressing the main content.
- At `920`, `700`, and `320`, the rail enters normal document flow with identity → context → conversation visual and DOM order.
- Multiple reasons remain scannable as bounded pills, while missing-state treatment combines text and tone.
- Browser review found no horizontal document or item overflow at any supported width.

## Mismatch List

- None.

## Evidence Gaps

- No external Figma comparison exists because there is no approved target file.

## Findings

- None.

## Route

- Next action: `pass`.
