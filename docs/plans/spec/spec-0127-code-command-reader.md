# SPEC-0127: Code Command Reader

## Metadata
- ID: `spec-0127`
- Status: `approved`
- Run: [RUN-165](../run/run-20261017-165-code-command-reader.md)
- Attempt: 1
- Parent Feature: [FEAT-0127](../feature/feat-0127-code-command-reader.md)
- Parent PRD: [PRD-0023](../prd/prd-0023-code-and-command-learning.md)
- Surface: fullstack
- Execution Profile: fullstack-product
- Surface Lanes: backend/data → frontend → docs
- Required Evaluators: contract, design, functional, ux-heuristic
- Created: `2026-10-17`
- Updated: `2026-10-27`

## Source Set And Contract
The [scene policy](../../policies/project/code-command-learning.md) owns exact
field shapes/predicates. Current learning modules/templates and the
[approved design plan](../design/code-and-command-learning-design-plan.md) are the
implementation inputs. The constitution wins over storyboard-specific styling.

## Implementation And Acceptance Mapping
1. Normalize v2 with strict typed/size/date/source/line/rubric checks. Generate
   unified diffs from before/after; preserve literal bytes. Persist via existing
   atomic reviewed import and immutable JSON revision; no SQL migration.
2. Centralize next-question and conservative v2 schedule behavior in learning.py.
   Home is one selected item; the owner's subsequent instructions remove the
   reason/evidence/recent-work widgets. The latest owner return replaces the
   short-answer composition with an independently authored article: work context,
   labeled/numbered code, sourced explanatory sections and takeaway precede a
   collapsed optional question. A desktop contents/reference rail stacks below
   the article at the compact breakpoint. Selection
   guidance and curator reasons remain in the library, complete evidence in the reader. Legacy
   packets keep their own question rotation and interval semantics.
3. Reader accepts optional question ID; an explicit attempt selects its saved
   question. Explicit practice does not silently replace a pending answer. Invalid
   selection yields a recoverable missing view. Submission retains selected
   question on error. GET does not record answers or explanation exposure, even
   though the home/article displays an explanation. Note-origin practice carries `from_note=1`
   through retry and forces `hint_used=1` on POST, including without JavaScript.
   Other navigation relies on the existing help report and attempt history;
   page views are not monitored across tabs. An explicit home/article read POST
   uses the existing `read` outcome and a fixed home or same-article redirect,
   never an arbitrary URL.
4. Scene and question stay adjacent above 1139px; stack at the shared compact
   breakpoint. A short reference panel may be sticky below the topbar, while long
   technical content uses document flow. All literal code has one local horizontal
   scroller and non-color line/diff markings. Sources and before/after remain
   available; feedback/rubric follow the stored answer or explicit reading.
5. Tab-local draft keys contain revision/question. Restore only absent server
   error values; retain edits on request failure. Clear after saved answer/read.
   Storage errors keep native forms and honest draft notice. Hint opening records
   help in the submission; no-script self-report remains usable.
6. Show depth as a question task, explain scheduling/self-report limits and
   provide explicit other-question practice links after feedback.
7. Prepare one real recorded command and one fixed Git diff with reviewed official
   evidence, no original code in Git. Import real content without artificial user
   answers, hidden settings or assessments. Do not execute source commands.
8. Update label registry/generated dictionaries, data-model ownership, learning
   policy/README, and design constitution for native scene presentation.

## Owner-Directed Article Revision

The owner rejected the short-answer composition and requested substantive
technical-blog-like learning reconstructed from actual work. Add optional
`article` on v2 packets; absent articles and v1 normalized payloads stay unchanged.
The article contains intro (1,600 characters), code_range (two positive display-line
integers, ordered, within the scene and at most 24 lines), 2–5 sections (unique id,
title 160, Markdown body 6,000 and resolving source_ids), takeaway (800) and overall
source_ids. Overall sources include the scene's work source and an official source;
each section cites an official source and stays within the overall source set.
The existing packet cap still applies. The scene policy owns the exact predicates.

Render article prose through shared safe Markdown. Slice code only from the
preserved scene, independently of today's question. Home and `/learning/{id}/note`
share the article component; the library opens it when available. Older lessons
retain their reader and complete explanation, without a fabricated article.
Note-origin practice and explicit read semantics continue; GET writes no history.

Reauthor two examples as private immutable revisions after source review. Preserve
historical uncertainty and label hypothetical examples. No model or automatic
content pipeline is added; the active Run remains open for owner/functional review.

## Scope And Open Blockers
Automatic collection/generation/source registry and efficacy are outside this Run.
No model selection is required. The curator captures only explicitly selected
local work; refs and versions are checked or marked unknown. No unresolved decision
blocks implementation. Runtime behavior tests were not run during the
2026-10-17 execution and remain pending; the user's testing/verification request
is required before adding or running them.

## Evaluation Focus
Contract: v1 identity, fields, source refs and producers/consumers.
Design: actual desktop/narrow scene presentation and native shell/header.
Functional: selection, progression, same-day exposure, mutation/retry/drafts,
historical records and no-script; unobserved paths must remain evidence gaps.
UX: one focused daily article, code kept in context, explanation-first reading,
optional question and finite exit. Reference article: the owner's Chochita Archive
note 43; native tokens/shell remain authoritative. Owner-authorized reauthoring
creates reviewed immutable revisions; layout does not truncate article conditions
or automatically summarize answers.

