# EVAL-0069-R5: Session Detail Metadata And Subsession Stats — Functional

## Metadata

- ID: `eval-0069-r5-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260803-81`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-r5-session-detail-metadata-and-subsession-stats](../spec/spec-0069-r5-session-detail-metadata-and-subsession-stats.md)
- Execution Profile: `frontend-product`
- Surface Lane: primary, normalized child, and lazy child detail rendering
- Evidence Coverage: `complete`
- Created: `2026-08-03`

## Checks

- A synthetic Codex Company primary detail renders no visible source eyebrow,
  keeps `CC`, and renders its direct child as external ID, question 3, event 8,
  then activity date.
- The normalized company child detail renders the source-neutral `SUBSESSION`
  eyebrow and keeps its company cue and parent/list navigation.
- A lazy Claude child summary derives question count from user-message events,
  and its detail template renders `SUBSESSION · LAZY VIEW` without a visible
  configured source prefix.
- Conversation ordering, tool-row suppression, parent/child eligibility,
  source-scoped return links, pin controls, ingestion, Usage, and count behavior
  remain unchanged.

## Evidence

- Focused Session/UI suite: 50 tests passed.
- Final full repository suite: 327 tests passed.
- Privacy and diff checks passed.

## Findings

- None after the bounded accessibility-fallback fix recorded by Contract.

## Route

- Next action: `pass`.
