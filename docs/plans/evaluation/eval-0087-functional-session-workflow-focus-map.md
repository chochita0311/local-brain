# EVAL-0087 Functional: Session Workflow Focus Map

## Metadata

- ID: `eval-0087-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run: [RUN-20260914-97](../run/run-20260914-97-session-workflow-focus-map.md)
- Attempt: `1`
- Feature: [FEAT-0087](../feature/feat-0087-session-workflow-focus-map.md)
- Spec: [SPEC-0087](../spec/spec-0087-session-workflow-focus-map.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Session entry → fixed map interaction → source return`
- Evidence Coverage: `complete`
- Created: `2026-09-14`

## Checks And Evidence

- Route fixtures prove exact eligibility, one projection call, zero writes,
  typed `404`/`422`/`500` states, honest unconnected success, safe evidence
  destinations, and failure isolation on the existing Session detail.
- Pure adapter fixtures prove that all FEAT-0086 Episodes, relations, reasons,
  evidence groups, totals, partial indicators, and availability states survive
  presentation while native IDs and sensitive paths remain absent.
- JavaScript tests prove repeatable wide and compact coordinates, stable branch
  lanes, ancestry/descendant illumination without sibling contamination,
  bounded pointer-anchored zoom, ordinary-wheel pass-through, and malformed
  input failure.
- Synthetic browser QA starts from the real Session detail, opens Focus, renders
  `1440`/`920`/`700`/`320`, expands a branch from three visible Episodes to all
  four retained Episodes, selects another Episode, and restores both directions
  with browser back/forward.
- Keyboard edge activation opens Relation Trace with its complete reason list.
  Zoom changes from `100%` and resets, Ctrl-wheel is owned while ordinary wheel
  is not, the selected card keeps its transform, and opening a Session source
  then returning restores the canonical focused Workflow route.
- No-script and forced renderer-failure paths retain the textual lineage, Trace,
  Session destination, and disabled controls. Existing conversation reading is
  present both before entry and after following a Session destination.
- Focused Python checks passed `39/39`, Node checks passed `5/5`, and the full
  Python suite passed `521/521`. The only suite output was the pre-existing
  Starlette `TemplateResponse` deprecation warning.

## Findings

- None.

## Route

- Next action: `pass`.
