# SPEC-0125: Reviewed Learning Home

## Metadata
- ID: `spec-0125`
- Status: `approved`
- Run: [RUN-163](../run/run-20261017-163-reviewed-learning-home.md)
- Attempt: `1`
- Parent Feature: [FEAT-0125](../feature/feat-0125-reviewed-learning-home.md)
- Parent PRD: [PRD-0022](../prd/prd-0022-work-grounded-learning-dashboard.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: data/backend → home/library/reader
- Required Evaluators: contract, design, functional, ux-heuristic
- Created: `2026-10-17`
- Updated: `2026-10-27`

## Execution Continuity

This Spec preserves the original approved input for FEAT-0125. The Feature is
now `superseded` and [RUN-163](../run/run-20261017-163-reviewed-learning-home.md)
is `returned-to-planning`, following the recorded 2026-10-17 owner redesign.
[PRD-0023](../prd/prd-0023-code-and-command-learning.md),
[FEAT-0127](../feature/feat-0127-code-command-reader.md) and
[SPEC-0127](spec-0127-code-command-reader.md) own the successor reader. Historical
selection/widget rules below do not define that successor; retained records and
missing functional/learning-benefit evidence keep their existing limits.

## Implementation Goal And Contracts

Implement [the learning policy](../../policies/project/work-grounded-learning.md)
using `learning_lessons`, `learning_attempts`, `learning_visibility` in the existing
private DB. Import validates all content before insertion and hashes canonical
normalized content. Attempts reference immutable revision IDs; visibility uses
stable lesson keys. Apply additive DDL through normal startup, preserving all data.

CLI: `localbrain learning import PATH --reviewed`, no network/model, no private
payload in errors. Document a synthetic packet. The import is the initial content
producer; no unimplemented “generate” action appears in the product.

Routes: GET `/` and `/learning`, GET `/learning/{id}`, POST
`/learning/{id}/attempts`, POST `/learning/{id}/assess`, POST
`/learning/{id}/visibility`. Require local hostname, same-origin browser mutation,
URL-encoded bounded forms and strict actions. POST/303/GET supports native browser
operation. Duplicate tokens replay the same stored result; conflicting payloads
fail. Errors retain answer/confidence on the reader and allow a safe retry.

Feedback uses autoescaped plain text with preserved line breaks; the source links
are separately admitted and show title, locator, snapshot, version, fingerprint
and checked date. No remote images, raw HTML or arbitrary file loading. The source
section is below the question; feedback is not in the initial page response.

Daily selection uses pre-day history, with one new and at most two due lessons.
The reader chooses the day's question and resumes pending attempts; completed
answers remain linked to their original questions. One completed date advances
question rotation once. The library remains an explicit extra-study route.

## Design And Interaction Contract

Screen-alignment mode: `adapt` for the owner's 2026-10-17 widget direction,
following the initial `extend` implementation. The active Feature remains
Fullstack Product; this increment owns the frontend Dashboard/library/reader
navigation lane and changes no persistence or learning transitions.

The owner selected [Refero's Qatchup reference](https://styles.refero.design/style/1b010453-80df-406a-8b1a-72630c4a5165)
for independent content panels while explicitly retaining LocalBrain's tone.
Borrow grouped cards and breathing room; resolve color, type, radius, border and
spacing through native tokens. The rendered current home establishes dark left
navigation, a neutral content surface and one warm primary action.

Concrete differences to address: the initial home is a single reading column;
review and recent work lack independent panel boundaries; reviewer information
and source dates require opening a lesson. Use a responsive two-column widget
composition for today's lesson, reviews, recent work and the selected lesson's
evidence. The evidence widget derives from the first new/due lesson and links to
its existing source section; with no selected lesson it offers the library.
Keep the finite daily selection and existing content intact. The library exposes
reviewer/version labels, source titles/dates and the current manual preparation
method. Source excerpts/answers stay behind the existing reading/answer choice.

This is a fixed initial composition. No drag handles, resize controls, widget
preferences or automated source-management actions are implied. Shared navigation
and search stay intact. Library/reader retain their native reading width.
At 320px, forms wrap, reader text/locators break, and no essential action depends
on hover or a horizontal multi-column layout. Native labels, details, radio
controls and focus states support keyboard use. No required JavaScript.

## Acceptance Mapping And Evidence Boundary

Data contract maps to import/revision/state code and schema owner documentation.
Learning transitions map to reader forms and local POST handlers. Finite selection
maps to deterministic date helpers. Source trust maps to reader metadata and
immutable packet snapshots. Navigation maps to the existing base template.
Required evaluators report their actual coverage separately; source inspection
does not establish runtime behavior or learning benefit. The 2026-10-17 execution
instruction permits no tests to be added or run without the user's explicit
testing/verification request; RUN-163 records the resulting evidence gap.

## Open Blockers

None for implementation. Runtime/design validation and the two-week learning
trial remain evidence to obtain; automatic source/model admission is later work.
