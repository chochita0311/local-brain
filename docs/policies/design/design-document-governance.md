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

## Practical Summary

- [DESIGN.md](../../../DESIGN.md) explains why the product should feel this way.
- [Design Constitution](./design-constitution.md) defines what implementation and evaluation must obey.
- [Design Evaluation](./design-evaluation.md) preserves recurring checks that should be applied again.
- A design plan, if explicitly created, describes what is changing now.
