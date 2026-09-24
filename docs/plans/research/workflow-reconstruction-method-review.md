# Workflow Reconstruction: Evidence And Method Review

## Status And Ownership

- Reviewed: `2026-09-23`
- Status: literature review, protocol diagnostic, evidence-first trial, matched
  role comparison, source-claim/current-state and extraction/binding reviews complete;
  no extractor is admitted. Remaining method changes are **proposed**, not admitted
  extraction or permission for private processing.
- Parent: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Current admission owner: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Pure contract owner: [FEAT-0099](../feature/feat-0099-source-claims-and-work-state-projection.md)
  (`passed` under RUN-111 after separate implementation approval; no model admission)
- Adapter/trial owner: [FEAT-0100](../feature/feat-0100-source-claim-extraction-and-binding-trial.md)
  (subsequently approved and completed under RUN-112; contract/replay PASS,
  semantic Functional FAIL, no admitted candidate)
- Local evidence: [RUN-109 evidence-first trial](../run/run-20260923-109-evidence-first-work-context.md),
  [RUN-110 formulation comparison](../run/run-20260923-110-work-role-formulation-comparison.md),
  [RUN-108 diagnostic](../run/run-20260923-108-work-context-protocol-diagnostic.md),
  following [RUN-107 extraction](../run/run-20260923-107-source-selected-work-extraction.md)
- Surface: supporting research/planning; execution belongs to RUN-108/109/110, with no
  product consumer or UI change.

The owner requested research into classification, statistical foundations, AI
methods and relevant systems before another extraction revision. This is a
targeted primary-source review, not an exhaustive systematic review or a claim
about the latest state of the art. Publication dates below are not search-index
dates. Public research queries contained no private Session content. No model,
private corpus, training, download or embedding recomputation ran for the original
literature review. The subsequent approved synthetic diagnostic is separate
execution evidence summarized below, not an effect established by a cited paper.

This document owns supporting evidence and proposed experiments. It does not
override approved Feature/Spec gates, make previous failed candidates pass, or
change production organization. Existing vectors, sources, holdout results
(not yet generated), UI and legacy records remain unchanged.

## Recommendation

Separate four questions that a single clustering/extraction score cannot answer:

1. Which enduring **work area** helps the owner find this material?
2. Which **outcome-oriented effort** does the evidence contribute to?
3. Does it **continue, branch from, or converge with** earlier work?
4. At this zoom level, what should the interface **reveal or summarize**?

Reuse embeddings for candidate retrieval. Evaluate evidence-backed work
relationships separately from area clustering and optional descriptive fields.
The completed RUN-108 isolates answer-protocol sensitivity using the installed
model and new frozen diagnostic cases. Its evidence-first follow-up, RUN-109,
also fails admission: extra same-model support/audit decisions do not establish
correct semantic roles or continuity. The matched RUN-110 improves exact role
sets but introduces omissions and still fails temporal reconciliation. Stop the
prompt/choice-variant sequence. The separate source-claim/current-state contract
now passes with supplied synthetic judgments. The subsequent adapter review below
proposed one bounded model-aware trial; its separately approved RUN-112 execution
is complete and failed admission, as recorded in [Review Boundary](#review-boundary).
Preserve strict provenance
and abstention requirements; do not silently bypass FEAT-0098 by calling a
different producer a graph experiment.

The destination remains all admitted Sessions, minimal routine confirmation,
an inspectable time-oriented map, recomputable derived state, and a finite
legacy transition. Neither a sentence nor a Session should automatically become
a top-level work area.

## What The Research Supports — And What It Does Not

### Task Context: Resources Support Work, But Do Not Define Its Identity

Dragunov, Dietterich and colleagues' **TaskTracer** (IUI 2005) connects activity,
resources and task context to interruption recovery. Importantly, that paper's
implementation still asks users to indicate task switches and explicitly
recognizes the burden and noisy labels. It is precedent for combining evidence,
not proof that automatic work discovery was solved.
[Author paper, especially Sections 2 and 7](https://web.engr.oregonstate.edu/~tgd/publications/iui2005-tasktracer.pdf).

Kersten and Murphy's **Mylar**, the task-context work behind Mylyn (FSE 2006),
uses interaction-derived interest to focus relevant artifacts. Its field study
analyzed 16 qualifying participants from 99 initial participants, with edit ratio
as a productivity proxy. Selection, attrition and changing tasks limit the
inference; it did not establish automatic cross-Session goal discovery.
[Author paper, Sections 5–6](https://www.cs.ubc.ca/~murphy/papers/mylar/2006-11-mylar-fse.pdf).

Local implication: combine scoped goals, artifacts, interactions and source
history, but do not restore a mandatory task-activation or labeling workflow.
Sharing a handbook or repository is useful retrieval evidence, not work identity.

### Classification: Broader, Related And Same Work Are Different Relations

**SKOS** distinguishes broader/narrower concept organization from associative
relationships; it represents knowledge-organization schemes, not every fact
about the world. **Flamenco**, from Marti Hearst's group, demonstrates navigation
through multiple hierarchical facets rather than one compulsory classification
axis. Neither source supplies an automatic classifier for this corpus.
[W3C SKOS Reference, Section 8](https://www.w3.org/TR/skos-reference/#semantic-relations),
[Flamenco research and interaction principles](https://flamenco.ischool.berkeley.edu/index.html).

Local implication: work area, project, artifact, lifecycle and time can be
different lenses. An effort may contribute to multiple areas without duplicating
its source evidence. Do not interpret an area hierarchy as temporal lineage.
Adopt this distinction, not RDF infrastructure merely because SKOS uses it.

### Segmentation And Conversation Disentanglement

Hearst's **TextTiling** (1997) identifies contiguous subtopic passages, a useful
counterexample to treating every fixed character window as a meaningful unit.
Its lexical document setting does not directly solve Korean chat, interleaved
goals or noncontiguous work resumed months later.
[Original paper](https://aclanthology.org/J97-1003/).

Zhu, Lau and Qi's **Findings on Conversation Disentanglement** (ALTA 2021)
examines reply-to links, thread context and additional features; it also studies
alternatives to independently choosing each utterance's top candidate. Its Ubuntu
IRC setting and learned models are not a ready-made work-reconstruction model.
[Paper and benchmark scope](https://aclanthology.org/2021.alta-1.1/).

Local implication: retain conversational context around evidence spans and test
relationship candidates, rather than independently turning each sentence into
work. Reply-to is still not the same as contributing to the same outcome.

### Object-Centric Process Mining: Do Not Flatten Many-to-Many Evidence

Wil van der Aalst's **Object-Centric Process Mining** (2019) explains how forcing
events into one case notion can duplicate events or introduce misleading order.
Its object-centric event model accommodates multiple objects per event.
It assumes structured event evidence; it does not extract reliable events from
arbitrary conversation. Its convergence/divergence terminology is not itself
proof of user-level workflow merges or branches.
[Author paper, Sections 1, 4 and 6](https://www.vdaalst.com/publications/p1056.pdf).

Local implication: one Session can contain several efforts, one effort can span
Sessions, and a resource can support several efforts. Keep evidence references
and typed relationships rather than copying or exclusively assigning whole
Sessions. Chronological adjacency must not manufacture causality.

### Clustering: Hierarchy And Noise Help, But Do Not Decide Meaning

**HDBSCAN** offers density-based clusters and noise without requiring a fixed
number of clusters. However, minimum cluster size, conservatism and cluster
selection parameters materially affect fragmentation and unassigned points.
It does not guarantee a small or meaningful work-area inventory.
[Official parameter-selection documentation](https://hdbscan.readthedocs.io/en/latest/parameter_selection.html).

Traag, Waltman and van Eck's **Leiden** (2019) addresses Louvain's potentially
disconnected communities and provides connectivity guarantees. Resolution still
affects community granularity; a well-connected graph community is not proof of
a shared goal. Changing the optimizer cannot fix unsupported input edges.
[Original paper](https://www.nature.com/articles/s41598-019-41695-z).

Local implication: retain the current Louvain result as a baseline. Prefer one
bounded Leiden graph comparison first because existing affinity graphs are
reusable; consider HDBSCAN only as a separately justified density alternative.
This is an engineering recommendation, not an empirical winner. Independent
resolution runs are not automatically a nested hierarchy; parent-child membership
needs its own validated aggregation rule. Do not cluster screen coordinates.

### Time: Stability Must Compete With New Evidence

Chakrabarti, Kumar and Tomkins' **Evolutionary Clustering** (KDD 2006) separates
fit to current data from the cost of changing earlier groupings. The study
includes a 68-week image-tag dataset; it is not a benchmark of dormant work
resumption. Temporal smoothness can preserve a mistaken grouping too.
[Author paper](https://faculty.mccombs.utexas.edu/deepayan.chakrabarti/mywww/papers/kdd06-evolutionary.pdf).

Local implication: measure identity/membership churn alongside grouping quality.
Search old work beyond a short recency window. Inactivity may lower visual
prominence but cannot alone close work, sever its identity or delete evidence.
Distinguish a real work branch/merge from an algorithm revising its clusters.

### Language-Model Evaluation: Answer Codes Can Be A Confounder

Zheng and colleagues' **Large Language Models Are Not Robust Multiple Choice
Selectors** (ICLR 2024) finds option-ID/position bias and studies inference-time
prior debiasing. Its assumptions and benchmark results do not establish the cause
of LocalBrain's failures or validate a specific correction here.
[Original paper](https://arxiv.org/abs/2309.03882).

Wang and colleagues' **Look at the Text** (2024) provides an important qualification:
instruction-tuned models' generated text answers can be more robust than answers
inferred from initial token probabilities. Their tested families include Llama2,
Mistral and Gemma, not our Qwen3 configuration. Our finite-sequence decoder is
not identical to their evaluation procedure, so this motivates a comparison,
not a diagnosis by analogy.
[Paper, experimental setup and results](https://arxiv.org/abs/2404.08382).

Zhao and colleagues' **Calibrate Before Use** (ICML 2021) studies prompt-induced
label bias and content-free calibration. This is another diagnostic precedent,
not evidence that a corrected score becomes a calibrated probability of truth.
[Primary paper](https://proceedings.mlr.press/v139/zhao21c.html).

Local implication: independently vary option position, code mapping and response
format before declaring a model incapable. Score meaning, protocol validity and
evidence grounding separately, without repairing a wrong answer into a pass.

### Graph Summaries And Zoom: Relevant, But Not Workflow Ground Truth

Microsoft's **GraphRAG** (2024) uses graph communities and summaries for corpus-wide
question answering. This supports investigating multilevel derived views, not
equating entity co-occurrence with workflow continuation. Its global QA evaluation
does not validate our task grouping, local model budget or privacy boundary.
[Research paper](https://arxiv.org/abs/2404.16130).

Suh and colleagues' **Sensecape** (UIST 2023) explores abstraction levels and
semantic zoom. Its 12-participant, short-task study reports benefits for exploring
concepts and structuring information, but also learning-curve and navigation
costs. It does not prove a constellation is universally better than a list or
timeline, nor that generated information is accurate.
[Paper, Sections 4–6](https://arxiv.org/abs/2305.11483).

Local implication: test a stable overview → effort → evidence interaction with
a synchronized timeline and an accessible non-spatial route. Zoom should reveal
existing source-backed detail, not invent extra tasks or require manual node
arrangement. This is a research input to the existing
[design plan](../design/workflow-map-design-plan.md), not new visual law.

## Reinterpretation Of The Local Failures

The results still mean that none of the tested recipes passes admission. They
do **not** establish a general Qwen3 capacity limit or a model-size ranking.

- The source-choice strategies encode none/done and evidence choices using
  enumerated codes. Omission and exhaustive anchor selection can reflect a mix
  of task framing, answer-protocol bias and genuine semantic failure.
- One unconstrained generation using the same code-oriented prompt still chose
  none. That does not isolate code semantics or ordering from the prompt.
- One CPU/float32 check agreed with MPS on an omission. This is evidence against
  a solely GPU-specific explanation for that observation, not a control for
  option bias, segmentation or field definitions.
- Mixed-goal fragmentation and request-as-progress errors remain substantive,
  whatever their cause. Quoting real text does not make its field assignment true.
- The four repeatedly used development cases are regression/development checks.
  The ten holdout cases have not been consumed by model evaluation, but their
  definitions exist in the repository; this is not an independently blinded
  real-world test set.

These hypotheses require a controlled diagnostic. No new causal conclusion is
claimed from literature alone.

## Proposed Reconstruction Structure

The following is LocalBrain's proposed synthesis, not a method proven by any one
paper. Terminology here does not add or rename persisted schema objects.

| Level | Meaning | What must not be inferred automatically |
| --- | --- | --- |
| Work area | Enduring responsibility or purpose under which multiple outcomes make sense | One area per Session, file or embedding chunk |
| Effort | A compatible desired change and outcome, potentially spanning months | Same effort solely because the topic or repository matches |
| Activity episode | Contextual evidence of investigation, implementation, verification or resumption | A completed action merely because the user requested it |
| Source evidence | Original spans, roles, times and admitted resource references | Model inference as an owner-confirmed fact |

Allow scoped many-to-many contribution while keeping each evidence record's
identity. Project/topic/time facets complement these levels rather than becoming
competing top-level workstreams.

### Candidate Retrieval And Relationship Decisions

1. Preserve source coordinates and conversational context. Existing 1,800-character
   embedding chunks remain retrieval units, not gold episode boundaries. Map
   retrieved chunks back to contextual messages; keep mixed goals separable.
2. Retrieve a bounded candidate union from semantic affinity, scoped references
   and lexical signals across **all admitted history**. Missing a close neighbor
   or an old goal must be measurable before blaming the relation model.
3. Judge compatible outcomes and supporting evidence on that candidate set.
   Shared utilities and generic boilerplate are weak signals; explicit
   incompatibility prevents joining efforts. Do not promote a mixed Session's
   transitive bridge into proof that all its neighbors are one effort.
4. Keep topic affinity, contribution and temporal relations distinct. FEAT-0098's
   explicit-link requirement for continuation remains in force. Any future
   inferred implicit continuity needs an approved, separately evaluated contract.
   Branches and merges need relational evidence, not a change in community labels.
5. Aggregate supported efforts into areas at a coarser level. Generate labels
   from representative evidence with uncertainty visible. Preserve provenance,
   correction scope and identity lineage when source/configuration changes.

Rich goal/progress/result extraction need not be assumed the sole way to discover
useful relationships. A narrower relationship-first experiment is worth proposing;
it is **not** authorization to relax the current extraction gate or publish
ungrounded relationships. Optional descriptive fields must remain unknown when
unsupported, including in any future graph consumer.

### Controlling Proliferation Without Concealing Bad Grouping

Prefer the simplest area organization that preserves recognizable responsibilities
and separately resumable outcomes. Evaluate area granularity and effort
fragmentation separately; a legitimate collection of many small efforts does not
require as many peer work areas.

A prototype may target roughly 6–10 visible areas initially, but that is an
adjustable presentation hypothesis, not a scientifically derived optimum or an
approved fixed cluster count. Report the complete area/effort totals and all
unassigned evidence before folding or filtering. If the algorithm fragments a
few responsibilities into dozens of areas, showing only six is a failure, not a
solution. Conversely, genuine distinct responsibilities must remain accessible
without false merges to satisfy a display budget.

Changing k or resolution alone does not settle semantic granularity. Coarser
candidates must be compared using same-area and different-goal evidence, coverage
and stability. The owner should not have to specify k or name every area.

## Evaluation: Statistical Evidence And Product Usefulness

Ulrike von Luxburg's **Clustering Stability: An Overview** explains why stability
is informative but not a universal selector of the correct number of clusters.
A stable, overly coarse result can still be wrong. Treat stability as one axis,
not semantic ground truth.
[Author review](https://www.tml.cs.uni-tuebingen.de/team/luxburg/publications/Luxburg_Stability_2010.pdf).

The four handcrafted development cases cannot estimate population accuracy.
For perspective only: even if four cases were independent random trials and all
four passed, the exact two-sided 95% binomial lower confidence limit would be
`0.025^(1/4) ≈ 39.8%`. Under a different, one-sided 95% calculation, zero errors
in 59 independent representative trials gives an upper error bound of
`1 - 0.05^(1/59) ≈ 4.95%`. These are calculations illustrating sample uncertainty,
**not** confidence intervals for our existing cases or a prescribed sample size.
[NIST exact binomial limits and small-sample guidance](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm).

Proposed measurement changes:

- Freeze expectations before output review. Preserve the current cases as
  regressions and use additional contrastive cases for development. Reserve a
  separate locked assessment set and consume it only after the candidate is
  frozen; do not repeatedly tune on it or pick whichever seed passes.
- Split by underlying effort/history, not by chunks from the same conversation.
  Keep near-duplicates and paraphrase families together. For later private
  assessment, sample across time, areas, sparse evidence and long-gap resumptions;
  report the sampling frame, unknown labels and coverage.
- Do not count correlated chunks, option permutations or pairs sharing the same
  effort as independent observations. If uncertainty intervals are justified,
  resample at the effort/history-block level and state the dependence assumptions;
  a naive binomial interval over all edges is not appropriate.
- Distinguish a deliberately difficult challenge set from a representative sample.
  Challenge failures are diagnostic, not an unweighted population error estimate.
  Automatically derived labels from explicit references are weak supervision
  unless their identity semantics have been independently established.
- Use synthetic exact expectations and source-based checks before asking the
  owner anything. If real expectations remain genuinely ambiguous, request at
  most a small consequential batch, not routine Session classification. Without
  independent expectations, report descriptive quality as unassessed; do not let
  the producing model certify its own accuracy.

| Axis | Proposed observation |
| --- | --- |
| Retrieval | Fraction of expected related histories present in the candidate set, including long gaps |
| Wrong joins | Evidence/effort assignments and supported pairs that join incompatible outcomes |
| Fragmentation | One expected effort split across groups; area over-splitting scored separately |
| Coverage | Recovered expected work, abstentions, excluded and unexamined sources, with denominators |
| Relationships | Precision/recall by relation type; unsupported continuity, branches and merges |
| Field meaning | Requests versus performed/reported actions, speaker attribution and unsupported results |
| Stability | Identical replay, unrelated append, changed/deleted evidence and correction survival |
| Usefulness | Time/actions to find an old effort and inspect why evidence belongs; consequential correction burden |
| Cost | Calls, tokens, elapsed time, peak resources and cache reuse at the intended scale |

Report complete counts, worst cases and class-specific failures, not only an
aggregate pass fraction. All-abstain and all-one-cluster baselines make degenerate
success visible. Numerical tolerances must be locked before a follow-up trial;
existing Feature acceptance criteria are not changed by this research.

**All-Session processing and sampled quality assessment are different.** Sampling
expectations for evaluation must not silently reduce the processing destination
back to 60 Sessions. Full-population coverage itself does not prove correctness.

## Next Bounded Follow-Up Proposal

### First: Separate Semantic Failure From Protocol Sensitivity — Completed

The owner approved this first step under RUN-108. Its frozen twelve-case/288-cell
matrix and real zero-generation replay completed. The
[Functional evaluation](../evaluation/eval-0098-functional-local-work-context-inference.md#protocol-diagnostic--run-108)
owns detailed counts and review. Numeric order/code changes alter meaning in
seven cases; label choices improve aggregate counts but do not fix contextless
continuation. Brief explanations sometimes disagree with their selected label.
Formatting/citation failures are reported separately from these semantic errors.
Thus the result supports a **mixed** diagnosis, not a pure answer-code explanation
or a claim that a larger model is required. No extraction recipe is admitted.

The original frozen-comparison rationale follows; it is not a request to repeat
this completed matrix or tune against its answers.

Use only the installed 8B baseline, with fixed weights/runtime and no training.
Before generation, freeze a small diagnostic set covering goals versus requests,
reported progress, two interleaved outcomes, gratitude, incompatible goals and
long-gap continuation. Keep original cases and expectations unchanged.

Compare three response forms on the same meaning: existing numeric choices,
explicit semantic-label choices, and a short text answer with source evidence.
Counterbalance choice order and code mapping independently where applicable;
record the actual serialized order and tokenization, not just intended order.
Record semantic answer changes, invalid output and evidence errors separately.
Text answers are diagnostic evidence, not a bypass around the structured-output
contract. Freeze the test matrix, parser, call/time budget and stopping rule
before execution; report every prescribed condition, not only the best one.

If the content answer is right but the code/protocol changes it, fix that boundary
and revalidate. If grounded semantic answers fail across the controlled forms,
revisit work-unit/context definition before further model-size comparisons.
If results are mixed, report that uncertainty. Do not keep retrying these cases
or install another model automatically.

### Then: Validate Work Relationships Before Whole-History Publication

Subject to approval of a new bounded contract, compare retrieval-only affinity
against retrieval plus evidence-backed relationship decisions. Include the hard
cases above, transitive mixed-Session bridges and real replay invariants. A graph
optimizer comparison is secondary to edge quality; richer progress summaries
are a separately scored consumer, not proof of correct grouping.

Only after the required admission boundary is satisfied should the all-Session
producer run with explicit coverage, cache/config identities and interruption
recovery. Existing embedding reuse is preferred; re-embedding is justified only
by a measured retrieval defect or an approved representation change.

At this diagnostic's planning checkpoint, `/auto-work` was still the older
sampled inspection surface; this review did not connect full-history results or
implement the intended map. The subsequent separately delivered temporal-affinity
surface is tracked in the [design plan](../design/workflow-map-design-plan.md#handoff-to-next-track),
not evidence that this model candidate passed. Production replacement and finite
legacy retirement remain separate approved outcomes.

### Evidence-First Follow-Up — Completed, Not Admitted

The owner approved RUN-109 after the diagnostic. Its single semantic candidate
uses source-selected fields, goal grouping, scoped links and same-model audits.
One label-length adapter defect was corrected before any model generation;
prompts, labels, cases and expectations stayed frozen. Original development passes
3/4 and new composition 4/12. Both gates fail, with extraction passing 1/8 overall
(only no-work abstention) and relations 6/8. No holdout/private run follows.

The primary review finds requests and plans in performed-work fields, completed
work left pending, and topic-only similarity promoted to continuation. Exact
quotes and speaker attribution are retained, while same-model audits approve
these false interpretations. Ambiguous mixed-work grouping and one example case
refuse without publishing partial output; refusal is not correct reconstruction.
Actual replay reuses all sixteen completed outcomes, including errors, unchanged.
The [Functional evaluation](../evaluation/eval-0098-functional-local-work-context-inference.md#evidence-first-candidate--run-109)
owns complete counts and review; these are local observations, not paper results.

Proposed next comparison: use fresh frozen matched contexts to compare direct
semantic-role classification with independent property judgments, keeping false
continuity controls separately visible. RUN-108's focused role results motivate
this hypothesis but are not causally comparable to RUN-109's compositional set.
Do not presume wording/token bias explains everything or add more same-model
audits as independent verification. No new candidate is selected by this note.
The owner has subsequently approved that matched diagnostic under RUN-110. It
permits all role combinations (not a forced single label), canonical/reversed
orders and separate unchanged-pipeline relationship controls. Inference and
scoring are frozen before observations; no model or extraction admission follows
merely from completing the comparison.

### Matched Role Formulation — Completed, Not Admission

RUN-110 completes all 166 observations and failure-preserving replay. Direct
role sets are correct in 15/32 order conditions versus 8/32 for independent
questions, with unsupported role assignments reduced from 42 to 16 but missing
assignments increased from zero to nine. Only 6/16 direct cases pass both orders.
Three of nine stable recognized direct cases are wrong, so consistency is not
truth. These are matched synthetic contexts with correlated conditions, not a
population accuracy estimate or an isolated causal test of option length/wording.

Both formulations mishandle a historical pending assertion followed by same-work
completion. Direct choices also omit actions from compound statements. Unchanged
relationship controls pass 5/6 final labels but still falsely continue topic-only
activity. The [current Functional evaluation](../evaluation/eval-0098-functional-local-work-context-inference.md#role-formulation-comparison--run-110)
owns primary review and counts. No old score is repaired or expectation changed.

The next proposed contract review should distinguish what a source asserted at
its event time from the current state of a supported effort. Preserve an earlier
pending assertion and a later completion separately, then resolve state only
when work/target identity is supported; retain compound-claim coverage and
unresolved identity. This is an engineering hypothesis from the local failures,
not a result proven by the cited literature or permission to redefine the frozen
tests. The owner subsequently approved reviewing that structure; the resulting
proposal and later separately approved pure implementation follow. No new
inference implementation is approved by that foundation.

### Source-Claim/Current-State Review — Completed, Planning Only

The approved review examined the failed comparison, current extraction prompts
and validators, and the existing user-correction ledger. It proposes
[FEAT-0099: Source Claims And Work State Projection](../feature/feat-0099-source-claims-and-work-state-projection.md),
a separate foundation, `draft` at review completion, not another FEAT-0098
inference strategy or an implicit rewrite of its acceptance criteria.

What the repository establishes:

- `work_context_evidence.py` asks progress/results about the focus's report,
  but asks remaining work about the end of the conversation. Extraction and
  later-state reconciliation are combined in the model's role decision. This
  design fact does not establish the sole cause of the measured failures.
- `work_context.py` verifies literal quote location and attribution, not truth
  of a status or semantic equality of work. Its unit ID hashes mutable output;
  it is not a persistent effort identity.
- `workflow_assertions` stores user-initiated, user-confirmed Episode corrections.
  It must not receive model-derived source claims. Existing Session Episode
  identity likewise cannot become an outcome identity just by renaming it.

The proposed separation is source anchors → attributed claims → supported
target bindings → reported-state projection. The Feature owns the exact
boundary and acceptance checks; this review owns the rationale:

1. **History and state answer different questions.** Keep “not done yet” as
   historical evidence and add a later completion claim. Change current remaining
   work only when supported identity, scope and chronology connect the two.
2. **Clause coverage and grouping are different problems.** An edit and an
   outstanding test in one sentence need two claims, not two top-level flows.
   An outcome-level effort may contain both. Unknown identity stays unresolved.
3. **State must be scoped and qualified.** Completing a test does not complete
   the whole effort; cancellation is not completion; failed outcomes do not
   invent repair requests. Contradictory reports, retrospective dates and
   unsupported reopening cannot be settled by ingestion order or latest-wins.
   Source reports remain reports, never verified completion or owner correction.
4. **A deterministic consumer isolates only one responsibility.** Start with
   supplied synthetic claims/bindings and test state/replay invariants without
   a model or DB. It cannot infer a missing clause, validate an arbitrary semantic
   link or rescue the rejected models. A later extractor/binding adapter needs
   separate approval and quality assessment before private processing.

Do not append more prompts to the completed matrix, load all private Sessions
before admission, reuse the durable correction ledger, or rescore RUN-110's
historical-pending cases under the new claim meaning. Those would respectively
confound diagnosis, bypass admission, mix authority or change the answer key.
The new representation needs its own version; any later current-field adapter
must still exclude fulfilled pending items and preserve original attribution.

This proposal keeps the whole-history work-area/effort/map destination and zero
routine classification burden. It adds no production cap, confirmation queue,
permanent storage, cleanup/migration or UI. It is an engineering hypothesis
motivated by local evidence, not a literature-proven fix or statistical quality
claim. No code, test expectations, model weights, source data or policy semantics
changed during this review.

Planning-document validation: catalog generation/check and its two existing
tests pass; all 865 local links across eight changed documents resolve; privacy
scan passes for 980 candidate files and whitespace checks pass. These are document
checks, not execution/evaluation of the draft Feature. No task scratch was created.

### Pure Contract Implementation — Completed After Separate Approval

The owner then approved FEAT-0099's implementation under
[RUN-111](../run/run-20260923-111-source-claims-and-work-state-projection.md).
Its pure projector now validates supplied source claims, target bindings and
reported-state transitions, including cutoff, partial-order disputes, source
revision and replay. Fifty tests and full 900-test regression pass (one optional
graph skip). There is no model, source reader, DB, persistent ledger or UI consumer.
The new [policy](../../policies/project/source-claims-and-work-state.md) owns that
implementation contract; historical extraction tests/results are unchanged.

This validates state calculation given supplied semantic judgments, not automatic
extraction, target identity or real-corpus quality. It isolates downstream state
logic so a future producer can be assessed without confusing its errors with
temporal projection. That producer still requires a bounded adapter and frozen
assessment review before any new model trial; FEAT-0098 remains blocked.

### Extraction/Binding Adapter Review — Completed, Planning Only

The owner requested this review after RUN-111. Its output is the separate draft
[FEAT-0100](../feature/feat-0100-source-claim-extraction-and-binding-trial.md), which
owns the proposed contract, cohorts, numerical limits and conditional holdout gate.
Repository inspection establishes two important integration constraints:

- `work_state.py` currently stamps all claims as `synthetic-supplied.v1`; a model
  adapter cannot use that contract unchanged and merely relabel its outer report.
  Preserve the passed baseline while adding actual producer/version lineage.
- Only scoped state claims change projected status. An action/result cannot
  silently become completion. A supported obligation-fulfillment inference needs
  its own model-attributed evidence and quality check, distinct from a literal
  source statement and from deterministic state reduction.

The proposal separates raw-source claim extraction from target/occurrence binding
and lifecycle judgments. Code retains source identity, attribution and exact
locators, then applies the passed state semantics. Supplied-reference diagnostics
isolate conditional capabilities; the end-to-end path receives neither reference
claims nor a correct target roster. Correct status with wrong premises still fails.
No same-model audit grants authority, and no all-unknown result passes by avoiding
false joins while missing the work.

This is an engineering hypothesis motivated by the existing local failures, not
new literature evidence or a demonstrated model improvement. The proposed bounded
trial reuses installed assets and original quality requirements. The original
holdout is unconsumed, not independently blinded; private all-history processing,
area grouping and the map remain later boundaries. No model inference ran and no
application code changed for this planning review.

## Review Boundary

The diagnostic, evidence-first trial, matched formulation comparison and approved
structure review and subsequently approved pure foundation are complete. No model
candidate is admitted or waiting for further calculation or owner classification.
The extraction/binding adapter review is also complete. The owner subsequently
approved FEAT-0100's implementation and frozen synthetic trial under
[RUN-112](../run/run-20260923-112-source-claim-extraction-and-binding-trial.md).
That Run now owns the completed failed trial: all 28 extractions are rejected by
protocol/source validation, conditioned binding fully passes 3/28, and every
end-to-end call is prerequisite-skipped. These are engineering-control counts,
not real-corpus accuracy or an isolated model-capacity diagnosis. Contract and
failure-preserving replay pass; original holdout/private/UI remain untouched.
The subsequent owner-requested output/evidence-interface review is now complete.
Its [relation-first inspection plan](../design/workflow-map-design-plan.md#relation-first-inspection-track)
separated then-draft full-history read/map Features from one direct-context
relation trial. The reader and temporal map subsequently passed under
FEAT-0101/0104; FEAT-0102's earlier freeform geometry is superseded, and FEAT-0103
remains draft/unexecuted. Removing mandatory role/goal inventories from that trial is a new bounded
engineering hypothesis, not a literature-proven fix or a relaxation of prior
extraction requirements. Compatible outcomes, source identity, actual relation
support and automatic withholding remain requirements.
No additional prompt variant, individual membership review, model installation
or training is authorized by this result.

Preserve original checks and untouched holdout; do not retune the completed cases,
weaken field-purity checks or treat relationship success as full extraction
admission. New execution/private processing still needs its normal bounded
Feature review. The delivered affinity inspection uses its own passed
data contract without claiming causal work identity; detailed state extraction
does not gate that narrower surface. The rejected trial and this planning
review change no source data, vectors, UI or legacy state. No new research search,
model inference or empirical quality result was produced by the planning review.
