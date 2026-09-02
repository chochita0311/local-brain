# EVAL-0081 Design: Atlassian Deterministic Site-First Hierarchy

## Metadata

- ID: `eval-0081-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260901-91`
- Attempt: `1`
- Feature: [FEAT-0081](../feature/feat-0081-atlassian-deterministic-site-first-hierarchy.md)
- Spec: [SPEC-0081](../spec/spec-0081-atlassian-deterministic-site-first-hierarchy.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Explorer presentation; domain-first hierarchy and terminology`
- Evidence Coverage: `complete`
- Created: `2026-09-01`

## Checks And Evidence

- `screen-alignment` was applied in `extend` mode. The change reuses the
  existing Explorer hierarchy rail, compact disclosure, segmented scope,
  list/detail, action, semantic-status, focus, and responsive families without
  introducing a private shell, token set, or breakpoint.
- The read model projects `hierarchy.sites[]` with Site-local `containers[]`.
  The template renders `모든 도메인 → domain → Project/Space | URL group |
  소속 미확인` and contains no service-parent branch. The supplied All-view DOM
  inspection found the shared domain once in the inspected hierarchy and no
  repeated Jira/Wiki parent.
- All, Jira, and Wiki remain peer top filters. In All, URL-derived children use
  the non-color cues `Jira · URL 기준` and `Wiki · URL 기준`; in the supplied
  Jira view they reduce to `URL 기준`. Persisted Project/Space children retain
  their service cue in All, while URL-derived rows, preview, and detail keep
  `URL 기준` or `로컬 파생` so a derived grouping does not claim confirmed
  Space authority.
- Ordinary product presentation uses Jira `링크`, Wiki `문서`, and mixed
  `링크/문서`. UI-contract coverage checks the Explorer, Add, preview, detail,
  Sync, Connections, Refresh, Search, and browser-authored live copy while
  leaving internal selectors, routes, and schema vocabulary unchanged.
- At `1440`, the supplied Chrome measurement retained the native three-region
  composition with 260/454/387-pixel hierarchy, list, and preview columns. At
  `920`, hierarchy moved into the compact list disclosure and the three actions
  measured 212 by 37 pixels.
- At `700`, Sync and Add measured 325 pixels each, More measured 657 pixels, and
  all narrow action targets measured 40 pixels high. At an emulated `320`
  viewport, document and viewport widths both measured 320 pixels, Sync/Add
  measured 142 pixels each, More measured 292 pixels, and all action targets
  remained 40 pixels high. Open compact labels wrapped inside their owner with
  no horizontal overflow.
- The hierarchy and containment styles consume existing semantic spacing,
  type, surface, border, focus, and information tokens. The desktop rail keeps
  the established 260-pixel role; the `920` compact transition and `700` touch
  geometry use the existing product breakpoints.
- The current source audit covered the Browse projection and route URL helper,
  Explorer/preview/detail templates, `atlassian.js`, `styles.css`, and UI
  contracts. The evaluator reran the complete suite with `436/436` passing and
  JavaScript syntax also passed.
- Supplied mobile Lighthouse evidence reported Accessibility `100`, Best
  Practices `100`, and Agentic `100`. Final supplied browser console inspection
  reported zero errors and zero warnings.

## Findings

- None.

## Route

- Next action: `pass`
