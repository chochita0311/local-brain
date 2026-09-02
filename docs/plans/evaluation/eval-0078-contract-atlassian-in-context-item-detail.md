# EVAL-0078 Contract: Atlassian In-Context Item Detail

## Metadata

- ID: `eval-0078-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260829-88`
- Attempt: `2`
- Feature: [FEAT-0078](../feature/feat-0078-atlassian-in-context-item-detail.md)
- Spec: [SPEC-0078](../spec/spec-0078-atlassian-in-context-item-detail.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `preview read model; selection/history; documentation`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Evaluated the selected-Item URL and eligibility boundary, bounded preview
  projection, authority ownership, progressive-enhancement contract, safe
  return paths, and durable owner-document parity.

## Checks And Evidence

- `/atlassian` owns optional positive local `item` state. Malformed,
  non-positive, and oversized values are local `400` responses; a positive
  unknown ID produces the bounded missing state, and Setup rejects selection.
- Complete and partial requests use the same server-authored preview. The
  partial header returns only the stable preview fragment and calls neither the
  broad inventory/hierarchy projection nor editing-option loaders.
- Full and partial routes share targeted Site/Space/service normalization.
  Known Space ownership is canonicalized and cross-service structural input
  remains a bounded `400` instead of becoming a false out-of-scope Item.
- The preview reads one selected Item and applies the approved metadata,
  content, local-note, classification, evidence, organization, and recent-Run
  caps. Remote, local, evidence, organization, and maintenance fields retain
  separate owners; unavailable and out-of-scope states do not fabricate facts.
- Exact eligibility projects only boolean target predicates for full persisted
  content/note and reads display text through capped `SUBSTR` projections.
  Unavailable retained remote bodies are not query owners, while local memory
  remains eligible. Supported Source Instance and Item-type diagnostics survive
  select, clear, partial, detail-return, and Refresh URLs.
- Row selection, full detail, local edit redirects, and Item Refresh all carry
  one canonical same-origin Explorer `return_to`. Every server boundary
  revalidates syntax and structural meaning before emitting a back link.
- Product Model, Design Constitution, Interaction Evaluation, and Atlassian
  Source Memory own the same read-first, bounded, progressive Explorer
  behavior as the implementation. Selection performs no provider, model,
  capability, scan, Refresh, or maintenance work.
- The focused 72-test preview/Browse/Refresh/UI-contract set, JavaScript syntax
  check, and `git diff --check` passed.

## Findings

- None.

## Route

- Next action: `pass`
