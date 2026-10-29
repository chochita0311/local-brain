# FEAT-0125: Reviewed Learning Home

## Metadata
- ID: `feat-0125`
- Status: `superseded`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, design, functional, ux-heuristic
- Parent PRD: [PRD-0022](../prd/prd-0022-work-grounded-learning-dashboard.md)
- Created: `2026-10-17`
- Updated: `2026-10-17`
- Approval: owner requested the PRD and continued implementation of the bounded pilot.

## Goal And Acceptance Contract

2026-10-17: the owner's approved code/command redesign supersedes the active
reader boundary. Existing implementation and records remain; missing functional
evidence is not a pass. PRD-0023 owns the successor contract and reader work.

A user can open a finite daily learning home, answer a work-related question or
read its explanation, compare with source-backed feedback, record a self-assessment
and return later. Reviewed content and learning history persist locally.

- Strict atomic local packet intake preserves immutable revisions and snapshots.
- Answer/confidence precede feedback; reading and self-reported recall remain distinct.
- Daily selection, question rotation, review dates and reversible visibility follow
  [FEAT-0124's policy](../../policies/project/work-grounded-learning.md).
- Home, library and reader show source dates, version uncertainty and actual state;
  empty/error states and save retry are available without a model.
- Existing work/session/search routes and native shell remain accessible.
- Owner's widget follow-up: compose today's lesson, reviews, recent work and
  selected-lesson evidence as native panels; expose the manual preparation method
  and reviewer/source metadata in the library. This frontend increment adds no
  drag/resize preferences or automated source collection.

## Surface Lanes

1. Data/backend: `schema.sql`, learning module, CLI, generated Schema presentation.
   Depends on FEAT-0124; contract/functional evidence owns identity, persistence,
   strict input, local mutations, scheduling and recovery semantics.
2. Frontend: Dashboard, learning library/reader, shared route wiring, scoped CSS.
   Depends on lane 1; design/functional/UX evidence owns actual content, forms,
   feedback, navigation, source disclosure, narrow containment and keyboard access.

## Scope Boundary

In: manually reviewed import, three durable tables, local learning flow, finite
daily selection in a fixed widget composition and recent-session entry.
Out: automatic candidate generation,
source fetching, Qwen execution, semantic grading, gamification and model claims.

## Entry, Exit And States

`/` → `/learning/<id>` → stored answer/reading → feedback → self-assessment → home.
`/learning` exposes all current lessons and restores hidden/snoozed choices.
No lessons gives an honest preparation explanation. Validation retains typed
answer and confidence. Missing revisions return a navigable not-found view.
Save errors stay on the owning surface and do not claim persistence.

## Dependencies And Regression Surfaces

FEAT-0124 contract; existing private DB and local app shell. Sessions Dashboard,
Workstreams, Session reading, Local Context and natural search retain their scopes.

## Harness Trace

- Spec: [SPEC-0125](../spec/spec-0125-reviewed-learning-home.md)
- Run: [RUN-163](../run/run-20261017-163-reviewed-learning-home.md)
- Contract review: [EVAL-0125 contract](../evaluation/eval-0125-contract-reviewed-learning-home.md)
  PASS with partial evidence.
- Design/UX review: [EVAL-0125 design](../evaluation/eval-0125-design-reviewed-learning-home.md)
  PASS WITH SUGGESTIONS with partial evidence.
- Implementation is available locally; required functional transitions remain
  untested, so the Feature is not marked passed. Automatic generation and actual
  learning benefit are outside this implementation result.
