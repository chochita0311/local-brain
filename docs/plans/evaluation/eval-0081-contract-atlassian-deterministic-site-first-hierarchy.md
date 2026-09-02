# EVAL-0081 Contract: Atlassian Deterministic Site-First Hierarchy

## Metadata

- ID: `eval-0081-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260901-91`
- Attempt: `1`
- Feature: [FEAT-0081](../feature/feat-0081-atlassian-deterministic-site-first-hierarchy.md)
- Spec: [SPEC-0081](../spec/spec-0081-atlassian-deterministic-site-first-hierarchy.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `strict admission; Sync resolver; Site-first read model; durable owners`
- Evidence Coverage: `complete`
- Created: `2026-09-01`

## Scope

- Evaluated strict URL identity and local Site admission, source-isolated
  resolver publication, explicit-Sync currentness, canonical-URL container
  ownership, Site-first structural state, no-persisted-inference and
  zero-hidden-I/O boundaries, terminology, and durable owner parity.

## Checks And Evidence

- The strict recognizer derives service, normalized domain and URL, bounded Jira
  key or Confluence Page ID, and an optional service-qualified container
  descriptor without consulting configured access. Jira project prefixes and
  percent-decoded-once, NFKC-normalized Confluence Space segments retain the
  approved 300-code-point identity and 320-code-point structural bounds.
- Sync first honors a unique frozen service-qualified Site mapping. Only when
  that mapping is absent does it reuse one normalized-domain Site, reject a
  genuinely ambiguous domain, or register one local Site. Regression coverage
  includes a valid Jira mapping beside a second same-domain Wiki Site and the
  distinct no-mapping multi-Site ambiguity case.
- Empty-inventory Session and Document evidence creates one Site shared by Jira
  and Wiki plus exact Site-scoped links and evidence. It creates no binding,
  Source Instance, Space, or `space_id` assignment; SQL tracing confirms no
  `atlassian_spaces`, binding, or containment write.
- Each source retains one transaction. A new Site remains in a source-local
  domain/service overlay, is published to the action registry only after
  commit, and disappears with its Item, URL, evidence, and cache identity on
  rollback. Same-source duplicate and later-source reuse remain idempotent.
- The resolver bump is fixed at `localbrain.atlassian-evidence.v2`. Explicit
  Document Sync currentness compares successful status, source fingerprint,
  and this version while ignoring a registered-Site fingerprint-only change;
  the dedicated repeat trace performs zero data writes and preserves the
  diagnostic fingerprint stored by the earlier scan.
- Browse gives persisted containment precedence, otherwise derives a child only
  from the one canonical Item URL, and falls back to `소속 미확인`. A direct
  regression inserts both alias and evidence URLs containing valid-looking
  hints and confirms that neither owns or merges a hierarchy group.
- The read model groups one Site domain first under `모든 도메인`, with
  persisted Space/Project, service-qualified URL, and Site-local unassigned
  children. All keeps a Site selection service-neutral; Jira/Wiki apply their
  top filter to the same graph. Counts and selected zero states use the same
  filtered population as the adjacent list.
- Structural parsing rejects repeated, oversized, forged, stale, cross-service,
  or site-less URL scopes. A known `space_id` canonicalizes through its
  persisted owner Site, emitted Space URLs include that `site_id`, and unsafe
  return state falls back to Explorer root. Partial, detail, edit, Add, Refresh,
  and browser-history paths retain the same validated state owner.
- Product, Architecture, Privacy, Design Constitution, Atlassian Source Memory,
  Feature, and Spec own the same local-only admission, canonical grouping,
  no-Space-write, currentness, transaction, and link/document terminology
  boundaries. Sync has no Provider, model, capability, executor, Refresh, or
  network path in its imports or call graph.
- Independent verification passed the focused Atlassian/UI contract set
  `135/135`, Atlassian discovery `118/118`, and the full repository suite
  `440/440`. JavaScript syntax, repository privacy, diff, data-model, schema
  presentation, schema-cleanup, and Mermaid checks also passed.

## Findings

- None.

## Route

- Next action: `pass`
