# FEAT-0009: Document And Resource Details

## Metadata

- ID: `feat-0009`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Make local Document and Resource detail routes calm, readable evidence surfaces with visible provenance, availability, relationships, technical paths, and reliable return navigation.

## Acceptance Contract

- Document detail prioritizes title, source type, path, metadata, Workstream memberships, and readable body content.
- Local Resource detail prioritizes title, resource type, path, availability, note content, and connected Workstreams.
- Available and missing Resources use correct semantic treatment and retain historical path visibility.
- Long paths, bodies, notes, membership labels, and mixed scripts remain contained at every supported width.

## Scope Boundary

- In:
  - `/documents/{document_id}` and `/local-resources/{resource_id}`
  - headings, metadata, provenance, availability, membership, reading body, note, return link, empty, and responsive presentation
- Out:
  - document extraction or rendering semantics
  - Resource creation, editing, deletion, or relationship behavior
  - Local Context explorer preview owned by `feat-0011`
  - Markdown or rich-text feature expansion

## Contract Surfaces

- Document and local Resource GET route parameters and template contexts
- current availability and membership values
- back and Workstream membership destinations

## Required Evaluators

- `design`: reading width, provenance, path treatment, availability, membership, and responsive containment.
- `functional`: return links, membership links, route behavior, missing state, and content rendering regression.
- `ux-heuristic`: reading clarity, metadata priority, and distinction between evidence content and navigation.

## User-Visible Outcome

- The user can read local evidence, understand where it came from and whether it remains available, and follow its existing Workstream relationships without losing context.

## Entry And Exit

- Entry point: Local Context explorer, Search result, Workstream Resource, or direct detail URL.
- Exit or transition behavior: return and membership links open the current owning surfaces with shell orientation intact.

## State Expectations

- Default: provenance, path, metadata, body or note, and relationships follow one reading order.
- Loading: no new client loading contract is introduced.
- Empty: absent note content or memberships is explicit and neutral.
- Error: missing route records retain current error behavior.
- Success: available and missing Resource states remain distinguishable with labels and structural treatment.

## Dependencies

- `feat-0002` and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/document.html`
- `src/localbrain/templates/local_resource.html`
- Document, Resource, metadata, membership, availability, reading-body, path, and responsive selectors in `src/localbrain/static/styles.css`

## Pass Or Fail Checks

- Pass if long body text and paths remain within the reading surface.
- Pass if available and missing Resources follow success and warning semantics with text labels.
- Pass if return and membership links retain correct destinations.
- Pass if absent notes or relationships do not look like failures.
- Fail if missing evidence is hidden to simplify the page.
- Fail if body rendering creates malformed links or horizontal page overflow.

## Regression Surfaces

- Document and Resource detail routes and 404 behavior
- Workstream membership destinations
- Local Context and Workstream entry links
- content rendering and path visibility

## Harness Trace

- Active spec doc: [spec-0009-document-resource-details](../spec/spec-0009-document-resource-details.md)
- Active run: [run-20260716-09-document-resource-details](../run/run-20260716-09-document-resource-details.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0009-ux-evidence-details](../evaluation/eval-0009-ux-evidence-details.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft paired Document and local Resource details as local evidence reading surfaces with different availability contracts.
- `2026-07-16`: executed and passed in `run-20260716-09`.
