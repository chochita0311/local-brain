# FEAT-0127: Code Command Reader

## Metadata
- ID: `feat-0127`
- Status: `in-loop`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, design, functional, ux-heuristic
- Parent PRD: [PRD-0023](../prd/prd-0023-code-and-command-learning.md)
- Created: `2026-10-17`
- Updated: `2026-10-27`
- Approval: owner reviewed the PRD/storyboard and authorized the first reviewed
  code/command reader increment with “확인한대로 진행해봐”.

## Goal And Acceptance Contract
Read a preserved real command or Git diff alongside one concept question,
compare a response with grounded explanation and optionally try another condition.
Dashboard shows one daily scene as a substantive work-based technical article,
with preserved code, sourced explanatory sections, application criteria and an
optional question. Desktop uses a contents/reference rail; compact screens place
references below. Selection guidance and curator reasons remain
inspectable in the library after the owner's Dashboard simplification.

## Scope Boundary
In: version-2 reviewed intake, deterministic selection/depth, scene rendering,
line references, original pre/post and source evidence, answer/reading feedback,
optional practice and tab-local unsaved draft recovery; two curator-reviewed real
work examples. Optional v2 articles share the home and individual article renderer;
article revisions preserve existing v1 lessons and actual personal records.
Out: automated scanning/generation/fetching, model runs, an editable shared source
registry, objective grading, cross-lesson mastery and new review-interval research.

## Dependencies
[FEAT-0126](feat-0126-code-learning-contract.md) document contract passed before
product spec begins. Reuse existing local storage/routes and v1 behavior.

## Surface Lanes
1. Backend/data: packet validation and selection; contract/functional ownership.
2. Frontend: Dashboard, library, article and source/question reader, scoped CSS/JS; depends on normalized
   packet contract; design/functional/UX ownership.
3. Docs: product, packet, data-model, design and generated labels; follows code.

## Entry, Exit And State Expectations
Home/article → context/code/explanatory sections/takeaway/References → optional assisted practice or an
explicit reading record. Library → reader → stored answer or reading → grounded
feedback → one self-assessment → optional practice or home. Missing scenes retain the legacy
reader. Failed validation/save keeps the question and text. Other revisions keep
their own evidence. Unknown versions/execution remain explicit. Empty data has
preparation guidance. No learning mutation occurs on GET.

## Pass Or Fail Checks And Regressions
Literal text/fingerprints, strict scene/reference validation, immutable v1 identity,
one-scene selection stability, depth predicates, feedback exposure and pending
resume, answer retry, responsive code containment, keyboard/native form fallback,
source provenance and actual runtime integration require their respective evidence.
Under the owner's 2026-10-17 execution instruction, no tests may be added/run
without the user's testing/verification request. Unobserved functional
requirements block formal pass, not authorized implementation work.
Shell/header, existing work routes, current lessons and history are regressions.

## Harness Trace
- Spec: [SPEC-0127](../spec/spec-0127-code-command-reader.md)
- Run: [RUN-165](../run/run-20261017-165-code-command-reader.md)
- Contract evidence: [partial inspection](../evaluation/eval-0127-contract-code-command-reader.md)
- Design/UX evidence: [partial rendered views](../evaluation/eval-0127-design-code-command-reader.md)

