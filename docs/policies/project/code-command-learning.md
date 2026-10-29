# Code And Command Learning

## Purpose And Current Boundary

This policy defines reviewed code/command scenes, substantive articles and the
deterministic daily selection/depth policy. [Work-Grounded Learning](work-grounded-learning.md)
owns common lesson/source contracts, private storage, atomic intake, immutable
revisions, attempts, intervals and visibility.

The current producer is a curator using the reviewed JSON import. Capturing the
selected original material is explicit authoring work. No repository watcher,
terminal recorder, official-document crawler, Qwen generator or semantic grader
runs from the Dashboard or reader. Metadata validation verifies structure and
internal consistency, not whether a curator's claims are true.

## Learning Concepts

| Concept | Meaning |
| --- | --- |
| Scene | Preserved command material or complete selected-file before/after snapshots, with work context, conditions and explicit real/synthetic provenance. |
| Reviewed article | A separately authored and reviewed teaching narrative connecting the work, mechanism, explanation and reusable takeaway. Its one central concept governs the article's composition. |
| Question concept | A stable grouping within one lesson for question-depth progression. A lesson may offer multiple concepts; the same concept in another lesson is not automatically a proven equivalence or a transferred skill. |

### Question Depth

Depth describes the requested reasoning:

1. understand: role, relationships and what a line does, with background available;
2. predict: behavior or failure under explicit conditions, with a reason;
3. transfer: change a condition/call path/input and apply the same principle.

## Packet Version 2

The integer packet version may be 1 or 2. Version 1 retains its exact normalized
shape and revision hashes. Version 2 retains all version-1 lesson/source/question
fields and requires scene, selection and authorship on each lesson. The normalized
version-2 lesson stores packet_version=2. No new SQL table is needed: the immutable
packet_json owns these bounded objects. Old answers keep their old revision.

Version-2 source snapshots preserve their literal text, including indentation and
terminal newline. The source fingerprint identifies precisely that stored text,
not an unread whole document. Existing URL, source-kind and date checks still apply.
Both versions retain the 2 MiB packet cap and atomic validation-before-write rule.

### Scene

Every scene requires:

- kind: command or diff;
- source_id: an existing work source in the same lesson;
- origin: source (real preserved material) or synthetic (invented teaching example);
- title (240 characters), language (80), context and conditions (8,000 each);
- captured_at: timezone-aware ISO timestamp, not after the validation date;
- occurred_on: nonfuture ISO date or null when the work time is unknown.

Command scenes additionally require code (literal, at most 48,000 characters),
execution (suggested, reported, executed or observed), and output (literal,
at most 48,000 characters, empty allowed except for observed).

- suggested: instructions exist; execution is not evidenced;
- reported: a work note reports execution, without claiming original terminal proof;
- executed: original execution evidence exists; completion/effect is not inferred;
- observed: recorded output/state supports the stated result, within conditions.

A synthetic command must use suggested and empty output. Context carries needed
alias/function/variable definitions, namespace, ownership and result limits.
Missing definitions must remain unknown and narrow or prevent the question; no
current shell execution or environment substitution repairs historical evidence.

Diff scenes additionally require repo, path, before_ref, after_ref (bounded text),
git_state (committed, staged, unstaged or mixed), and literal before/after snapshots
(up to 96,000 characters each; either may be empty, but they must differ).
These are complete snapshots of the selected file. Capture the actual fixed commit
IDs, or explicitly identify worktree state and capture time. Branch alone is not
a sufficient ref. A worktree/index ref uses `sha256:` plus its matching content
fingerprint. For a real uncommitted scene at least one side must use that form;
the other may be a fixed commit. The importer computes before_sha256, after_sha256 and a unified display
diff from the snapshots; it does not trust a separately authored diff body.
A synthetic diff uses synthetic refs/repo and stays explicitly labeled.

The importer computes code_sha256 for the command or generated diff. Context and
conditions participate in the enclosing lesson revision hash. Original paths/refs
are text, never shell instructions or browser file links. The rendered display
numbers excerpt lines, not original file lines; the diff hunk headers retain
before/after locations. Around-code, settings and dependency/version evidence must
be included in context or cited source snapshots before relevant claims are taught.

### Reviewed Article

Version 2 may carry `article` as a separate teaching narrative. Its absence adds
no default to normalization, preserving existing v2 hashes; version 1 rejects it.
The article is authored/reviewed under the lesson's existing authorship fields
and participates in its immutable revision. It is not a generated question answer.

- `intro`: nonempty Markdown, at most 1,600 characters, connecting the actual work
  to the concept and naming material observation limits;
- `code_range`: exactly two integer display-line numbers (booleans rejected),
  `1 <= start <= end <= scene line count` and `end - start < 24`; these select
  actual preserved code independently of the daily question;
- `source_ids`: 1–12 unique resolving IDs, including the scene's work source and
  at least one official source; these cover the introduction and takeaway too;
- `sections`: 2–5 objects with unique ASCII-key `id`, nonempty `title` (160),
  Markdown `body` (6,000) and 1–12 unique resolving `source_ids`, including an
  official source and contained in the article's overall source set;
- `takeaway`: nonempty Markdown, at most 800 characters, carrying the reusable
  judgment and its conditions. The existing 2 MiB packet cap still applies.

The article should connect work → mechanism → a consequential distinction or
worked example → application to the work. Define unfamiliar terms when introduced,
label invented examples, distinguish recorded facts from inference, and retain
conditions/version limits at the claims they qualify. A question's brief answer
does not substitute for this narrative. Source IDs validate references, not truth
or educational quality; those remain manual review responsibilities.

Home and `/learning/{id}/note` render the same article through the shared safe
Markdown renderer, without resolving local files, embedding images or fetching
links. Code comes only from the retained scene range. Section navigation and
numbered official References derive from those fields. Source snapshots remain
in the reader. Older lessons show their complete explanation without an invented
article. The library opens an article when present and retains legacy readers.
Updating the article requires a new reviewed import, retains earlier revisions
and their answers, and starts the existing schedule for that new revision.

### Questions And Authorship

Every version-2 question adds:

- concept_id: stable ASCII key within the lesson;
- depth: understand, predict or transfer;
- focus_lines: unique positive integer display-line numbers, 1–24 entries;
- rationale: why this question matters (up to 2,000 characters);
- rubric: 1–8 required points/conditions (up to 2,000 characters each).

All questions reference the scene's work source and at least one official source.
Every concept offered by a lesson has an understand question; additional depths
are optional and have no invented fallback. Question IDs remain immutable within
their revision. The same concept in another lesson is not automatically a proven
equivalence or a transferred skill.

Authorship requires author (owner or assistant), method (manual),
reviewer (owner or assistant, equal to reviewed_by), and authored_on (nonfuture).
Future generated content needs a new admitted contract with model/prompt/source
identity and quality evidence; setting reviewed_by does not admit model output.

Selection requires signal (requested, recurring, recent or general) and reason
(up to 2,000 characters). These are curator-declared reasons, not automatic
discovery or a diagnosis of the user's knowledge. Requested must refer to an
explicit user topic/request; recurrence must be supported by the cited work.

## Daily Eligibility And Selection

Home proposes at most one scene total, including review, for a local calendar day.
Version-1 lessons stay accessible and participate using their legacy questions.
Eligibility excludes hidden and snoozed stable keys and uses only current revisions.
A completed lesson stays today's selection rather than immediately replenishing it.

Use history strictly before today:

1. Continue an answer that was unfinished at the start of today, oldest first;
   finalizing it today keeps that same daily selection.
2. Due reviews: read/again/partial or hinted latest assessment first, then other
   due reviews; within each group oldest due date then revision ID.
3. New lessons: requested, recurring, recent, general; then most recent known work
   date; then import ID. Legacy lessons use general with unknown work date.

A newer revision, import, explicit hide/snooze or timezone change may alter the
eligible set. Completing today's selected lesson alone does not refill it.
The library explains scheduling rules and each curator-declared work reason.
Dashboard shows the daily scene as an explanation-first note with inline official
references. Selection guidance and complete evidence remain in library/reader.
Other lessons remain deliberately accessible in the library.

This deterministic policy is not a learned recommender or a research-proven optimal
schedule. Due-first may postpone new content; the library provides explicit choice.
Future recommendation quality and interval changes require their own evidence.

## Question Depth And Review Evidence

Start each concept at understand. For each available depth, require two distinct
earlier local response dates, completed before today, whose latest relevant self-assessment is unhinted recalled
before recommending the next available depth. Read/again/partial or hinted work
at that depth resets the count. Any earlier feedback-bearing attempt for the same
concept on that date makes a later answer assisted for progression, even when its
hint checkbox is clear. Submitted answers expose feedback; this records feedback
availability, not proof that the user read it. Same-day repetitions do not promote.

Choose the concept with the fewest earlier completed dates, then declared order;
within its eligible depth choose the least recently completed question, then order.
An unresolved pending attempt takes precedence. Version-1 question rotation and
legacy interval calculations remain readable and unchanged.
After a version-2 completion today, default reopening returns its feedback;
explicit other-question practice remains available without replacing that record.

The rule is transparent scheduling from self-report, not objective grading or a
mastery percentage. General review intervals remain the existing pilot 1/3/7/21-day
defaults. For version-2 interval decisions, same-day feedback-assisted recalled
also has the conservative one-day effect; stored hint_used remains the submitted
help report (including opened hint/additional-code disclosures) and is not
overwritten to encode feedback availability.

## Article Reading And Optional Practice

Home presents a work-based article: context, preserved code, sourced explanation
sections, reusable takeaway and optional practice. The article keeps one central
concept with enough reasoning to understand its mechanism; it never silently
clips prose or conditions. The code preview labels whether it is partial and its
display-line range. Diff previews preserve literal +/− markers; command
highlighting uses an explicit shell label, with escaped text for unknown labels.

Home GET creates no attempt or durable exposure record. **읽은 내용 기록** is an
explicit `read` POST; it has no recall credit and returns to home or the individual
article through fixed local redirects.
Optional questions entered through the note carry `from_note=1`; submission forces
`hint_used=1` even without JavaScript. This is an assisted explanation exercise and
cannot promote depth or earn an independent-recall interval. Failed saves retain
that context. Prior saved answers are not retroactively changed by opening home.
The app does not monitor reading in other tabs or later independent navigation;
those entry paths still depend on the learner's help report and stored-attempt
history. A page view is neither proof of reading nor a completed lesson.

The reader permits an explicit other-question link for optional practice. This
does not count as a new daily requirement. Background-first records read; comparison
feedback includes the preserved rubric and official references. Unsaved answer/
confidence/hint state may persist in this browser tab's sessionStorage, keyed by
immutable revision and question; storage failure retains normal forms and says
draft recovery is unavailable. This temporary browser draft is not a saved attempt,
does not sync or train a model, and is cleared after a successful answer or read.

## Qwen And Official Documents

### Current Embedding Role

Current natural search uses Qwen3-Embedding-0.6B to encode queries/documents.
Embedding/reranking and text generation are separate roles
([Qwen Embedding](https://qwenlm.github.io/blog/qwen3-embedding/)).

### For Later Generation

For later generation, use retrieval-augmented generation: preserve versioned
official passages, retrieve the relevant material, and supply it alongside the
actual code/command and question objective in the local model's input. The
weights are not updated by this process. Public-document updates refresh stored
evidence/indexes and flag dependent questions for review; they do not automatically
rewrite history or require retraining the model.

Official ownership, section, actual software version, document version, fetch/
review times and content identity remain distinct. Latest documentation alone
does not establish applicability to old work. A generator must cite supplied
evidence, keep exceptions and abstain when it is insufficient. Formatting checks,
self-critique and retrieval similarity do not certify technical correctness.

### Admission And Evidence Limits

Qwen's [RAG integration guide](https://qwen.readthedocs.io/en/latest/framework/LlamaIndex.html)
illustrates retrieval plus a generator using Qwen2.5; it is conceptual evidence,
not a tested Qwen3 integration or a new dependency recommendation.

No private query or code is sent to public document search. Model selection,
resource budget and automatic exposure remain the later generation gate.
