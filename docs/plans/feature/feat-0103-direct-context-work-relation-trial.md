# FEAT-0103: Direct-Context Work Relation Trial

## Metadata

- ID: `feat-0103`
- Status: `draft`
- Type: `foundation`
- Surface: `mixed` (`data`, `infra`)
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-23`
- Updated: `2026-09-23`
- User review status: planning requested; this single-trial boundary awaits approval.

## Goal And Evidence

Test one narrower question: can the installed local model distinguish supported
work continuation from topic similarity, separate work and insufficient context
when given original ordered context directly? This is not another goal/role
extractor, state projector, JSON-format comparison or model-size comparison.

RUN-107 already tested host-owned source selections; RUN-108 tested answer forms;
RUN-109/110 used selected goals and same-model relation checks; RUN-112 failed
both protocol and semantic extraction/binding. Exact citations and structurally
valid choices alone did not make those judgments correct. The new distinction is
removing mandatory role/goal inventories from the relation input, not claiming
constrained output is a newly discovered solution.

## Acceptance Contract

### Direct Context, Narrow Judgment

- Supply two bounded, source-ordered context windows and the focal passages to
  compare, with original speaker and time metadata. Preserve antecedents,
  negation and relevant preceding/following context. No reference goals, roles,
  target roster, expected relation or previous extractor output enters the model.
- Host-provided windows define the question's scope, not discovered work identity.
  A mixed-goal Session is not one effort; ambiguous focal scope must remain
  uncertain. Synthetic supplied-window quality does not measure corpus retrieval.
- The model selects `continues`, `related`, `independent` or `uncertain`:
  - `continues`: compatible outcome-level work and explicit evidence that the
    later focal work resumes/advances the earlier work, including long gaps.
  - `related`: supported shared subject/context without a supported same-effort
    continuation. Topic/file/repository/time overlap alone cannot imply continuity.
  - `independent`: positive evidence of distinct work or an explicit boundary,
    not simply a missing continuation phrase.
  - `uncertain`: insufficient, contradictory or ambiguously scoped evidence.
- Resolve label overlap explicitly: positive distinct-work/boundary evidence
  takes precedence over shared-topic `related`; the latter means supported
  affinity without a supported identity decision. Missing antecedents or an
  ambiguous focal target require `uncertain`, not a topic-word shortcut to
  `related`. Freeze these distinctions in the reference cases before generation.
- Cite both sides and, for continuation, the later backward-link evidence.
  For uncertainty, identify the ambiguous/insufficient supplied context; never
  invent a missing fact to produce a more confident label.
- The host owns source IDs, revisions, coordinates, chronology and serialization.
  The model selects bounded host span aliases; it does not generate quotes, IDs,
  a goal inventory or long JSON. Selected spans must support the judgment in
  context, not merely exist in the source. No fuzzy citation repair.
- At most four calls per pair: relation, left evidence, right evidence, and a
  backward-link selection only for continuation. Invalid prerequisites remain
  failed/skipped; no reference substitution, repair loop or same-model approval.
- Host span boundaries are citation mechanics, not semantic episode boundaries.
  Allow bounded multi-span evidence so antecedents and compound passages are
  not forced into an unsupported single-sentence quote.

### Freeze One Comparison And Its Stop Rule

Freeze cases, reference judgments, prompts, span options, protocol, scorer,
producer/configuration fingerprints and limits in the approved Spec **before**
generation. All labels are synthetic engineering judgments, not real-work truth.

- One installed, verified Qwen3-8B candidate; reuse the admitted offline runtime
  configuration, non-thinking greedy generation and existing asset verification.
  No download, hosted service, training, alternate model or parameter sweep.
- Development: 24 new histories, six for each relation. Cover explicit long-gap
  resumption, new work on the same topic, shared files/repository with different
  outcomes, mixed goals, missing antecedents, ambiguous chronology, negation and
  insufficient evidence. Include matched contrasts but report their dependence.
- Regression: all original four development and twelve composition histories,
  assessing their unchanged relation expectations and supporting evidence only.
  Report this as a narrower relation projection, not a pass of their omitted
  extraction/lifecycle requirements. Do not modify any original fixture or scorer.
- Assessment: eight new histories, two per relation, authored and frozen before
  the candidate is run and kept out of prompt selection. Separate scenario
  families from development where possible. They are author-known synthetic
  assessment, not an independently blinded or population-representative holdout.
  The original ten-case extractor holdout remains untouched.
- Run assessment at most once and only after development and regression gates
  pass. Maximum 48 history blocks / 192 actual generation calls; conditional
  skips remain visible. At most 8,192 combined input/output tokens and 32 output
  tokens per call, a 60-second soft call limit and a 90-minute cumulative launch
  budget including loading/validation. No silent input truncation; an over-budget
  case fails/refuses explicitly. Time limits are not hard process-kill guarantees.
- Record actual calls/tokens/time and refusals. Resume cannot reset budgets or
  regenerate completed failures. No prompt, span, threshold, code-order, seed or
  model variant is tried after observing answers in this trial.

### Judge Support, Not Just Labels

- Within each cohort, all non-continuation cases must pass the exact expected
  relation and relevant evidence checks; at least 80% of continuation cases,
  rounded up, must pass. Invalid/omitted/runtime-failed cases stay in denominators.
- Any unsupported continuation or fabricated source attribution blocks admission,
  even inside an otherwise positive case or an intermediate emitted decision.
  Primary semantic review checks scope, outcome compatibility and actual support.
- Report per-label counts, answered coverage, abstention, false joins, missed
  continuations and evidence errors. Include all-uncertain and all-continues
  controls; neither uniform strategy can pass. Cases, not tokens, spans or
  correlated calls, are the units. Do not infer corpus accuracy or significance.
- Structural/transport PASS is distinct from semantic Functional PASS. Replay
  raw successful and failed observations with identical hashes, judgments and
  counters and zero new generation; failure preservation is required.

## Exit And Failure Route

- Failure ends this candidate and the current automatic 8B prompt-variant track
  for this task. Report the narrower capability gap, not a universal claim that
  an 8B model cannot work. No automatic rerun, corpus job or owner-labeling queue.
- A protocol/infrastructure repair may revalidate stored responses only when
  semantic inputs/configuration remain identical and no generation is added.
  Otherwise stop and return the changed boundary for review.
- PASS permits proposing a separately bounded real-context relationship study.
  Candidate retrieval/recall, long-history coverage, cost and false joins must
  then be evaluated; a supplied pair trial cannot establish those properties.
- Neither result gates FEAT-0101/0102 affinity inspection. Pair edges do not
  define top-level groups, transitive work identity, branching/merging or state.
  FEAT-0098/0100 remain blocked; no broad extractor admission is inherited.

## Scope Boundary

- In: one source-native synthetic relationship trial, evidence/abstention scoring,
  finite runtime observations, failure-preserving replay and semantic review.
- Out: private data, all-corpus pair generation, embeddings, cluster assignment,
  UI/overlay, role/claim/goal extraction, lifecycle, production identity, source
  rescan, organization writes, Foundry changes and legacy cleanup.

## Surface Lanes And Contract Surfaces

- Data: versioned source-window/span and relation-evidence packet, frozen
  synthetic cases and independent reference scoring; Contract/Functional owners.
- Infra: verified generator, bounded orchestration and existing out-of-repository
  evaluation-store lifecycle with 30-day inactive expiry; no second permanent
  corpus or raw-response store. Contract/replay and runtime-budget evidence.

Source text is untrusted evidence, not executable instructions. The model has
no tools or external access. Only synthetic fixtures/aggregate evidence enter Git.

## Dependencies And Likely Affected Surfaces

Existing verified model/runtime and choice/evaluation utilities may be reused.
Implement a distinct relation protocol and tests; do not alter frozen historical
prompts, scorers, results or holdout. No dependence on FEAT-0101/0102 or FEAT-0099's
state projector. Exact module/command placement follows the approved Spec.

## Pass Or Fail Checks

Contract: source authority, unchanged old behavior, bounded calls, no hidden
generation, frozen fingerprints, fail-closed evidence validation and exact replay.
Functional: all cohort gates plus primary semantic review. A fully completed
failed trial is reported as quality-blocked, not Feature PASS.

## Harness Trace

- Spec, Run and evaluations: not created; boundary review pending.

## Continuity Notes

- `2026-09-23`: drafted a direct-context relation boundary with a single-candidate
  stop rule. No new case, prompt, code, model call, private read or holdout
  consumption occurred during planning.
