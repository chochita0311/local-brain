# Design Document Governance

## Purpose

Define ownership, hierarchy, conflict resolution, and update rules for LocalBrain's design documents. Keep creative intent, durable law, reusable evaluation knowledge, and optional active planning separate.

## Governance Model

| Document | Role |
|---|---|
| [Design Constitution](./design-constitution.md) | durable design source of truth and implementation contract |
| [Design Evaluation](./design-evaluation.md) | reusable visual review checks derived from repeated findings |
| [DESIGN.md](../../../DESIGN.md) | creative source, visual rationale, and source interpretation |
| Design plan, only when explicitly created | active scope, sequencing, unresolved decisions, and implementation deltas |

These documents are related but are not peers. Updating one does not require mechanically rewriting the others.

## Source Hierarchy

For implementation and evaluation:

1. [Design Constitution](./design-constitution.md) governs durable visual and interaction rules.
2. [Design Evaluation](./design-evaluation.md) supplies reusable checks that are narrower than constitution law.
3. [DESIGN.md](../../../DESIGN.md) supplies creative intent and rationale.
4. An explicit design plan may govern active sequencing and unresolved work, but never overrides durable law.

For product compatibility:

- Approved product policies own product scope, terminology, privacy, and user-facing organization.
- Current code and schema are implementation truth for existing routes, entities, validation, and status values.
- The constitution reconciles those constraints into design law; it does not invent product behavior.

If sources conflict:

- The constitution wins for how an approved behavior is presented.
- Product policy wins for intended product behavior and scope.
- Code and schema win when describing what the application actually does; a contract change must be resolved explicitly rather than hidden in styling.
- `DESIGN.md` may motivate a constitution change but does not override it by itself.
- A plan wins only for active order, scope, and open questions.

## Starting-Source Reconciliation

The initial baseline is recoverable from the design outputs:

- Qoo10 Design System (AI) is the named upstream visual and token source.
- LocalBrain policies, code, templates, and existing screens provide product and implementation compatibility evidence.
- [DESIGN.md](../../../DESIGN.md) records the creative interpretation and imported/adapted boundary.
- [Design Constitution](./design-constitution.md) records the self-contained reconciled system.

Private external file keys and URLs are not documentation dependencies. A source must remain identifiable by name, date, scope, and contribution without requiring external access to interpret the constitution.

## Document Ownership

### `DESIGN.md`

Owns:

- creative north star
- tone, atmosphere, and visual rationale
- source-set interpretation
- explanation of what was imported, adapted, or rejected
- composition, color, typography, depth, and motion direction

Does not own:

- enforceable token values
- status mappings
- shell dimensions
- component implementation contracts
- rollout sequencing or screen-local exceptions

Update it when the creative direction or interpretation of a source materially changes.

### `design-constitution.md`

Owns:

- compatibility constraints that shape UI
- primitive and semantic tokens
- layout and responsive law
- status-to-UI mappings
- component and interaction contracts
- accessibility and AI guardrails
- durable screen families

Does not own:

- implementation tasks or migration notes
- unresolved experiments
- build order
- one-off visual polish

Update it before or with any durable system change. The constitution should remain usable without opening Figma, `DESIGN.md`, or a plan.

### `design-evaluation.md`

Owns:

- reusable review checks
- repeated containment, continuity, typography, alignment, and viewport cautions
- classification guidance for recurring visual failures

Does not own:

- broad design law already covered by the constitution
- one-off evaluation findings
- implementation sequence

Promote an evaluation rule into the constitution only when it becomes a product-wide constraint rather than a reusable review caution.

### Optional Design Plan

A design plan exists only when explicitly requested. It may own active scope, sequence, current implementation deltas, risks, and unresolved choices. It never duplicates token tables or changes durable rules by implication.

## Rule Promotion

When new visual input or implementation evidence appears:

1. Classify it as creative intent, durable rule, evaluation learning, active work, or product behavior.
2. Check product policy and code when the change touches entities, states, validation, navigation, privacy, or available actions.
3. Update `DESIGN.md` when the creative interpretation changes.
4. Promote a rule into the constitution only when it is reusable across more than one component, state, or fundamental screen family.
5. Add a review check to Design Evaluation when the lesson is repeatable but narrower than product-wide law.
6. Keep local polish and implementation sequence out of durable policy.
7. Record the durable change in the Version Log.

## Evaluation Rules

A constitution change passes only when:

- every rule is durable and self-contained
- source roles and reconciliation are recoverable from the files
- backend and derived UI states map to visible semantic families
- component rules use semantic roles without direct primitive or raw values
- responsive transformations preserve navigation, action access, and content containment
- several screens can be extended without inventing new color, spacing, radius, motion, or screen logic

A constitution change fails when:

- it contains tasks, sequencing, migration language, or unresolved uncertainty
- creative input is treated as implementation law
- product behavior or state values are invented without code or policy support
- source provenance disappears with the removal of private identifiers
- document ownership is ambiguous

## Drift Prevention

- Do not restyle the persistent shell as a side effect of one screen change.
- Do not add raw design values or private breakpoints in component CSS.
- Do not let a new route create a new visual family without checking the durable screen families.
- Do not silently preserve ad hoc implementation values when the constitution normalizes them into a stable scale.
- Do not weaken provenance, validation, error, or availability cues for visual simplicity.
- Do not create a design plan or production workflow as part of `init-design` unless explicitly requested.

## Version Log

| Date | Version | Durable change |
|---|---|---|
| 2026-07-15 | v1 | Established the Qoo10-derived creative direction and initial LocalBrain design baseline. |
| 2026-07-15 | v2 | Added `DESIGN.md`, corrected major entity states and shell breakpoints, removed private external identifiers, and linked the design policies from the documentation map. |
| 2026-07-16 | v3 | Reconciled source provenance, code-backed state vocabulary, current navigation and shell behavior, full semantic token roles, responsive evolution, accessibility, core component coverage, screen families, and Design Evaluation ownership. |
| 2026-07-16 | v4 | Added accessible Claude and Codex provenance roles that remain semantically separate from product status and feedback families. |
| 2026-07-16 | v5 | Added reusable micro, compact, empty-state, hidden-offset, no-border, focus, outline, active-edge, reduced-motion, and sticky-offset roles required to complete semantic-only component migration. |
| 2026-07-18 | v6 | Expanded the stable System navigation from seven to eight destinations and added the read-only Schema surface to the Explorer family without changing shell geometry or component vocabulary. |
| 2026-07-19 | v7 | Aligned the detail-and-read screen family with the source-neutral `Subsession` product term without changing its layout, tokens, or component behavior. |
| 2026-07-20 | v8 | Added dedicated Markdown reading-code surfaces, syntax-text roles, and border semantics so sustained reading does not reuse Run-console or product-state color meaning. |
| 2026-07-23 | v9 | Added External Source Instance capability and Atlassian Item freshness mappings for the Atlassian browse-and-inventory family. |
| 2026-08-02 | v10 | Added source-specific Codex Company provenance aliases and the accessible `CL`/`CX`/`CC` compact-cue contract for ordinary Session inventory cards. |
| 2026-08-02 | v11 | Restored the same compact accessible source-cue contract to Pinned Session cards without repeating configured source names visibly. |
| 2026-08-02 | v12 | Extended the stable source-key `CL`/`CX`/`CC` icon contract to Session detail headings and normalized or lazy Subsession projections while preserving their readable source labels. |
| 2026-08-03 | v13 | Removed repeated visible configured source names from Session detail headings and detail Subsession rows while preserving accessible source cues, and aligned child-row question, event, and date metadata with the Sessions inventory family. |
| 2026-08-25 | v14 | Separated Session related-material and Pinned Session content insets from their desktop scrollbar lanes, using the section spacing role for optical breathing room while preserving normal compact card insets. |
| 2026-08-29 | v15 | Reclassified Atlassian from Browse and inventory to the Explorer family; added its Site/Space/Unclassified hierarchy, one-query shell handoff, responsive list/detail composition, and distinct local Sync, Add, Connections/discovery, and remote Refresh presentation contracts. |
| 2026-09-01 | v16 | Reframed Atlassian hierarchy as top service scopes followed by domain-first Site and persisted, canonical-URL-derived, or `소속 미확인` children; added non-color-only service/provenance cues and ordinary Jira-link, Wiki-document, and mixed terminology without changing internal Item identity. |
| 2026-09-01 | v17 | Added explicit success, warning, and neutral mappings for available, unavailable, and archived Atlassian URL-derived structure references while preserving their separate URL-derived provenance cue. |
| 2026-09-02 | v18 | Added the Project-grouped Pinned Sessions hierarchy: Git-first alphabetical workspace headings, activity-ordered Session rows, optional branch metadata, and single boundary ownership within the existing browse family. |
| 2026-09-14 | v19 | Extended the Explorer family with Session Workflow Focus: fixed time and branch lanes, Episode selection/path states, adjacent evidence Trace, technical-canvas input ownership, complete narrow/no-script/render-failure lineage fallback, and contextual correction previews with persistent user-confirmed authority and stable orientation restoration. |
| 2026-09-16 | v20 | Added the owner-approved Auto Work destination immediately above Workstreams, using existing browse/read composition, shell geometry and tokens, with explicit unassessed authority and sample/availability states. Manual Workstream hierarchy is unchanged. |
| 2026-09-23 | v21 | Extended Auto Work with a full-history affinity Explorer: settled undirected constellation, selection-preserving evidence Trace, explicit expansion and complete textual navigation. Mapped freshness/availability independently from semantic quality; retained the labeled sampled comparator and unchanged shell. |
| 2026-09-24 | v22 | Corrected Auto Work to a left-to-right observed-time flow canvas: similarity strands, activity knots, explicit unobserved gaps/unknown times, period inspection and neighborhood zoom. Curves never confer work lineage; native shell, tokens, selection continuity and fallback remain. |
| 2026-09-24 | v23 | Clarified continuous Auto Work canvas ownership: text pagination cannot partition map membership/connections or camera; native bounded scrolling and visible time navigation reveal offscreen time and strands. Clarified the existing knot aggregate and capped occurrence-volume meaning without changing rendering or grouping. |
| 2026-10-06 | v24 | Added Sessions' observation-only List/Chart display: full-width time canvas, native source point/cards, collision-only vertical lanes, floating/stacked selection, timestamp activity points, explicit navigation and complete List/detail fallback. Existing Workflow Focus and Auto Work retain their contracts. |
| 2026-10-06 | v25 | Owner-approved Chart revision replaces collision rows with fixed irregular homes and smaller native source circles. Bounded point pulling, nearby geometric response, original-anchor markers and damped return remain transient; cancellation and reduced motion restore rest. Time, membership, List, Workflow Focus and Auto Work contracts are preserved. |
| 2026-10-06 | v26 | Owner review replaces scatter with recorded-folder Project bands in name/path order, stored-branch guides at first Session observation and plain tracks for missing branch records. Fixed labels, exact dense-point counts/selection and small same-track tension retain native tokens, time truth and existing frozen surfaces; guides do not assert actual Git history. |
| 2026-10-06 | v27 | Owner refinement removes Chart footer annotations and adds native checkbox Project visibility, compact reading tracks, resisted date ends and vertical overview fit. Overview withholds crowded text/preview, restores reading scale on selection, and preserves recorded-folder/branch truth and frozen List/Workflow/Auto Work surfaces. |
| 2026-10-07 | v28 | Project filtering replaces toolbar date navigation and persists after browser close. Directional/date controls are removed while drag/keys remain. Existing pins gain a static native halo/icon and exact-member status; List/Chart omits its divider and source controls adopt Dashboard separators and All. |
| 2026-10-07 | v29 | Confirmed Project visibility belongs to the private LocalBrain DB per scope, shared across browsers with contextual failure recovery. Centered native targets and balanced adaptive 64px insets define visible-date bounds; filter changes retain endpoint/time anchoring. Blank pan extends up to two control widths (80px, narrow-width capped) with the existing return, separate from point pulling. |
| 2026-10-07 | v30 | Shift-wheel accepts either wheel axis for bounded horizontal movement. Cmd/Ctrl+Shift-wheel changes time spacing alone, preserving vertical projection, camera, preview mode and independent tab state. Time-only fit and resize retain vertical orientation; existing whole-chart controls keep their meaning. |
| 2026-10-07 | v31 | Exact HEAD remains original metadata but does not create a named branch. HEAD/missing-only folders use one line without an empty baseline; mixed named-branch folders share one unassigned track for those records. Named guides and observation provenance remain unchanged without inferring repository status. |
| 2026-10-07 | v32 | Overview retains branch labels instead of dropping them below a scale threshold. Project-name typography and branch caption/height/vertical padding follow the vertical projection, with scaled heading measurement preventing occlusion. Fixed axis insets, reading tokens and native focus remain; tiny whole-fit names restore to reading scale through existing focus. |
| 2026-10-08 | v33 | Session-node hover/focus gains temporary native metadata descriptions and a stronger information surface/border. Activation holds selection; repeat/blank activation releases it without stationary-pointer reappearance. A separate temporary component preserves held description/activity and narrow layout; hover changes no camera, scale, persistence or activity. Source/pin cues and exact-member access remain. |
| 2026-10-09 | v34 | Node, temporary metadata card and the facing-edge passage share hover ownership. The card accepts pointer/focus reading and local scrolling; leaving ownership closes it after native state-duration grace with cancellation on reentry. No invisible hit overlay intercepts blank canvas input; card input does not hold selection or move the map. Pending exit callbacks clear with transient hover. |
| 2026-10-12 | v35 | Extended the existing Search/read families with a labeled two-input header, source-parent evidence/result continuity, and explicit preparation/coverage states using existing semantic tokens. |
| 2026-10-15 | v36 | Added visual-only conversation emphasis: user inputs use the existing information surface and left accent; source-marked assistant result replies use a stronger neutral perimeter. Existing speaker/time labels and ordinary commentary or unmarked replies retain their treatment, with no phase badge or task-success claim. |
| 2026-10-15 | v37 | User input cards retain the default card surface instead of an information tint. The inset left accent, stronger speaker name and neutral assistant result perimeter remain unchanged. |
| 2026-10-15 | v38 | Claude primary Sessions and Subsessions use the same visual-only result perimeter as Codex by normalizing explicit native response completion signals. Missing, interrupted, ambiguous and error responses keep their ordinary treatment. |
| 2026-10-15 | v39 | User input cards gain a very light blue surface through the conversation-input semantic role, softer than the information feedback tint. Existing input borders and speaker emphasis, assistant result frames and ordinary commentary retain their treatment. |
| 2026-10-15 | v40 | Refined the conversation-input tint to an even lighter blue; frame, type and ordinary assistant surfaces retain their treatment. |
| 2026-10-15 | v41 | Reduced the conversation-input tint to near-white blue (#fdfeff); existing frame and typography roles retain their treatment. |
| 2026-10-15 | v42 | Session detail leads its metadata strip with an abbreviated source-native Session ID and full-value copy utility. Content-sized activity time and reading-column-aware reflow preserve branch space, source cues, conversation frames and shell geometry. |
| 2026-10-15 | v43 | Session ID copying confirms success on the owning button with a check glyph and completed accessible label/tooltip, resetting on pointer exit or blur. Control geometry, metadata positions and manual-copy failure recovery remain stable. |
| 2026-10-15 | v44 | Session ID copy outcomes use a live bubble below the owning button instead of the footer toast. Copied! confirmation and local failure recovery remain unclipped, viewport-bounded and transient while preserving check feedback and control/metadata geometry. |
| 2026-10-15 | v45 | Session ID copy behavior follows the observed GitHub interaction: shared button-centered hover/result tooltip, no native title, independent two-second copied state, automatic glyph/help reset while hovered, deadline-preserving exit/reentry and repeat-copy refresh without flicker. Escape dismissal and outcome-only live announcements preserve existing geometry and failure recovery. |
| 2026-10-16 | v46 | Unified the shared header into one natural-language search field with the original placeholder, an accessible hidden label and a native Search submit action shared with Enter. Removed visible mode labels and ordinary keyword-search navigation while preserving the Atlassian local-query exception and existing shell tokens. |
| 2026-10-19 | v52 | Settings use a compact 720 by 560px maximum dialog with a 160px desktop category rail, viewport containment, a fixed header/close action and content-owned vertical scrolling. Narrow categories follow the shared 700px horizontal-row breakpoint; category changes reveal their heading without resetting unsaved inputs, and save/error feedback is brought into view. Existing type and controls remain. |
| 2026-10-25 | v53 | Owner-requested profile settings refinement separates draggable rows from a shared enclosing frame, adds an insertion line, and uses color-only tag/palette controls. Source toggles keep saved names/order without colored dots; record cues retain their profile colors and provider letters. Existing keyboard/focus, editor, removal and first-use contracts remain. |
| 2026-10-25 | v54 | Give independent settings rows quiet resting containment; extend the shared list/editor, order and named confirmation family to Local Context. |
| 2026-10-25 | v55 | Correct settings-row containment to white surfaces with a subtle edge and resting shadow; remove whole-row resting/hover/drag tints while retaining control focus and movement cues. |
| 2026-10-25 | v56 | Replace the horizontal solid-swatch palette with a vertical menu of colored tags below its trigger; define outside dismissal, bounded scrolling and keyboard/focus behavior. |
| 2026-10-26 | v57 | Session/Context ordering shows a whole-row drag preview, reserved slot, animated neighbors and edge scrolling with cancel/keyboard/reduced-motion continuity. Color choices use horizontal tags, content-sized menus and zero gap/padding; fine-pointer choices are 32×24px and coarse-pointer choices retain 40px targets. |
| 2026-10-26 | v58 | Restore diagonal profile-row tags; menu tags remain horizontal with their point/hole on the left and align to the trigger glyph's visible left edge. Selected color uses a quiet profile fill/outline instead of a check column, retaining accessible radio selection and separate keyboard focus. |
| 2026-10-26 | v59 | Match the color menu frame to both edges of its trigger background and match horizontal/diagonal painted tag widths. Remove menu color-name hover tooltips while preserving accessible names; retain compact heights and scrolling without a width-changing gutter. |
| 2026-10-26 | v60 | Run204 ties Pinned group ordering to the displayed home-abbreviated path with stable identity fallback, and distinguishes selected palette state from pointer/keyboard focus while preserving visible keyboard navigation. |

## Shared Evaluation Experience — 2026-10-26

The owner authorized generalizing this session's reusable UI/UX findings into
ai-assets. [Commit dc15bf9](https://github.com/chochita0311/ai-assets/commit/dc15bf9ad9aae2eaa6c819117a28e807cfbdb755)
updates its Design/Interaction Evaluation policies and standalone screen-alignment
procedure, with three generalized evidence records. The eight concerns are
requested-control preservation; frame/painted/hit-area geometry; sequential input
and focus; reorder feedback and commit; autosave confirmation and races; displayed
sort semantics; actual-host/native-action evidence; and hidden-content overflow.
Two documentation reviews corrected export-link portability and record subject
discovery; package, schema, links and public-fitness checks passed. This is shared
source publication, not a refresh of LocalBrain's installed harness or proof of
improved future agent behavior. Private original receipts remain at their owners;
public examples retain recorded-execution and unrun-scenario limits.

## Practical Summary

- [DESIGN.md](../../../DESIGN.md) explains why the product should feel this way.
- [Design Constitution](./design-constitution.md) defines what implementation and evaluation must obey.
- [Design Evaluation](./design-evaluation.md) preserves recurring checks that should be applied again.
- A design plan, if explicitly created, describes what is changing now.
