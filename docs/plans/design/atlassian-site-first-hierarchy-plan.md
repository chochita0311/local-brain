# Atlassian Site-First Hierarchy Design Plan

## Metadata

- Status: `complete`
- Parent boundary: [PRD-0015](../prd/prd-0015-atlassian-site-first-url-organization.md)
- Completed Feature: [FEAT-0081](../feature/feat-0081-atlassian-deterministic-site-first-hierarchy.md)
- Completed Run: [RUN-91](../run/run-20260901-91-atlassian-deterministic-site-first-hierarchy.md)
- Created: `2026-09-01`
- Updated: `2026-09-01`
- Screen alignment: `extend`

## Purpose

- Record the completed reconciliation of the Atlassian Explorer with the
  owner's domain-first mental model while preserving the LocalBrain family.

## Plan Type

- Information-hierarchy and interaction consistency.

## Baseline

- Passed PRD-0014 baseline: service-first hierarchy with
  Site/Space/Unclassified; PRD-0015 intentionally replaces only that hierarchy,
  strict-Sync admission, and ordinary terminology.
- Durable family: hierarchy/list/preview Explorer with responsive disclosures.
- User target: `모든 도메인 → domain → Project/Space | 소속 미확인`.

## Scope

- Remove the repeated service parent from the left hierarchy.
- Use Site domain as the first node and native compact cues for mixed services.
- Keep Project/Space and deterministic URL groups at one child depth.
- Keep `All` Site and `소속 미확인` selection mixed-service while persisted
  and URL children retain their service-qualified identity.
- Replace ordinary Item copy with link/document language.
- Preserve search, filters, list, preview, actions, scroll, focus, and fallback.

## Non-Goals

- New visual language, tokens, shell, cards, search mode, or action family.
- Persisted containment inference or remote data.

## Invariants

- One primary Add action and distinct Sync/Connections/Refresh consequences.
- Hierarchy and list counts share one denominator.
- Service tabs remain reversible and visible.
- URL hints come from the canonical URL only, never persist Space identity, and
  remain visibly distinct from persisted containment.
- Empty local Sync may create Site/link identity from strict Issue/Page URLs but
  performs no external/model work and publishes source-local resolver state only
  after commit.
- Compact/narrow list remains primary and selected detail remains reachable.
- Type/provenance differences never depend on color alone.

## Resolved Findings

- The repeated service tree layer was removed while All/Jira/Wiki remained as
  reversible top scopes.
- Site domain now leads directly to persisted, URL-derived, or honestly
  unassigned children.
- Ordinary `Unclassified` and `Item` copy was replaced with `소속 미확인` and
  link/document language without changing internal identity owners.

## Completed Work

### Batch 1: Read Model And State

- Outcome: emitted Site-first nodes, stable canonical-URL child descriptors, and the
  approved empty-Sync local identity handoff.
- Guardrails: no Space writes, binding, remote/model work, or rolled-back cache
  publication; preserve query/filter/selection URLs.
- Evidence: count parity, mixed-service Site/unknown state, source transaction
  rollback, invalid state, and direct/back-forward tests passed.

### Batch 2: Native Explorer Presentation

- Outcome: rendered one Site depth, child labels/cues, and ordinary terminology.
- Guardrails: reuse current hierarchy links, counts, focus, tokens, breakpoints.
- Evidence: source review, UI contract, and the Chrome four-width matrix passed.

### Batch 3: Regression And Durable Parity

- Outcome: closed owner docs and all four evaluators with focused/full, privacy,
  generated-owner, and browser evidence.
- Guardrails: no change to search/list/detail/action behavior outside scope.
- Evidence: focused `135/135`, Atlassian discovery `118/118`, full `440/440`,
  and required generated checks passed.

## Validation Results

- `1440` retained contained hierarchy/list/detail columns; `920` retained the
  compact hierarchy and detail drawer order.
- `700` and `320` retained bounded disclosures, rows, type cues, touch targets,
  and zero horizontal overflow.
- Mixed Jira/Wiki labels remained distinguishable in All through non-color
  service and URL-basis cues.
- Empty, shared-domain, persisted Space, URL group, unassigned, selected,
  long-label, and invalid-state fixtures passed automated or browser review.

## Risks / Open Questions

- None. URL grouping remains derived and does not claim persisted containment.

## Exit Outcome

- Achieved: the left hierarchy reads as `모든 도메인`, domain, then
  Project/Space or `소속 미확인`, while the rest of the Explorer remains
  visibly unchanged.

## Handoff To Next Track

- Stable hierarchy law is owned by Product, Source Memory, and the Design
  Constitution. FEAT-0081 and RUN-91 retain the completed implementation and
  evaluation trace. At this plan's closure no successor design track was
  active; the later completed [PRD-0016 structure-reference track](atlassian-structure-reference-plan.md)
  owns standard-URL structure references without rewriting this Site-first
  baseline.
