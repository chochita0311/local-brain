# EVAL-0081 Functional: Atlassian Deterministic Site-First Hierarchy

## Metadata

- ID: `eval-0081-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260901-91`
- Attempt: `1`
- Feature: [FEAT-0081](../feature/feat-0081-atlassian-deterministic-site-first-hierarchy.md)
- Spec: [SPEC-0081](../spec/spec-0081-atlassian-deterministic-site-first-hierarchy.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `empty Sync; hierarchy and route state; Add handoff; Explorer regression`
- Evidence Coverage: `complete`
- Created: `2026-09-01`

## Checks And Evidence

- Recognition fixtures cover Jira browse/issues keys, strict Confluence Page
  paths, percent-decoded Unicode normalization, dot/control/separator rejection,
  unsupported project/Space-only and REST forms, identity and URL bounds, and
  stable service-qualified descriptors.
- Empty Sync tests cover one same-domain Site for mixed Jira/Wiki evidence,
  exact link/evidence reuse, no binding or Space creation, unchanged repeat with
  zero writes, service-mapping precedence over a cross-service domain duplicate,
  honest unmapped ambiguity, and extractor-version currentness independent of
  registered-Site fingerprint changes.
- Source transaction tests cover same-source overlay reuse, later-source
  post-commit reuse, and a forced registration failure. The failed source leaves
  no Site, link, evidence, or cached identity, while the following source can
  retry and commit independently.
- Browse tests cover persisted-Space precedence, canonical-URL grouping, alias
  and evidence URL non-ownership, `소속 미확인`, equal-label provenance cues,
  one shared domain branch under All, Jira/Wiki filtering, count parity, known
  zero-count children, and bounded forged, stale, repeated, and cross-service
  structural state.
- Canonical route tests preserve query and advanced filters, clear selected
  link/document state on structural transitions, retain Sync selection and
  scroll continuity, normalize known Space-only input to its owner Site, and
  sanitize unsafe detail and action returns.
- Manual Add regression and supplied Chrome execution both confirm strict
  service-derived handoff. Jira finished with a `200` Explorer URL carrying
  `structural_scope=url:jira:REFUNDS`; Wiki finished with a `200` Explorer URL
  carrying `structural_scope=url:confluence:ORDERS`. Persisted Space, reused,
  archived, and unassigned handoffs remain covered by route tests.
- Rendered-template and controller checks cover Jira `링크`, Wiki `문서`, and
  mixed `링크/문서` copy across Explorer, Add, preview, detail, Sync,
  Connections, Refresh, global Search, notices, loading, and live status while
  preserving internal route, selector, registry, and schema names.
- Supplied Chrome evidence verified one Site-domain branch with URL and
  unassigned children and no service parent. At `1440`, `920`, `700`, and
  `320`, the hierarchy/list/detail composition retained its approved wide or
  compact form with no horizontal overflow. Lighthouse Accessibility scored
  `100`, and the final console inspection reported zero errors.
- Independent verification passed the focused Atlassian/UI contract set
  `135/135`, Atlassian discovery `118/118`, and the full repository suite
  `440/440`. JavaScript syntax, repository privacy, diff, and owner/generated
  data-model checks passed. The only runtime warning was the existing Starlette
  `TemplateResponse` deprecation notice.

## Findings

- None.

## Route

- Next action: `pass`
