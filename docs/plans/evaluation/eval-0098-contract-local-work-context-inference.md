# EVAL-0098: Local Work Context Inference — Contract

## Metadata

- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Run: [RUN-20260923-110](../run/run-20260923-110-work-role-formulation-comparison.md)
- Attempt: `1`
- Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, `data`
- Evaluator: `contract`
- Date: `2026-09-23`

## Current Scope — RUN-110

PASS covers the separately approved matched formulation diagnostic, not an
extraction admission or a semantic guarantee. Earlier admission failures remain.

- PASS — matched source/definitions: sixteen new role contexts share the same
  original messages, content-derived focus and four facet definitions. Property
  canonical order uses the unchanged evidence-first questions/options. Direct
  selection admits every role subset plus uncertainty. Canonical/reversed order
  affects presentation only; expectations and case IDs do not enter prompts.
- PASS — scoring: 160 role choices yield 64 assembled case/method/order results;
  full-set matches, extra/missing roles, per-field confusion and matched changes
  remain separate. Six unchanged-pipeline relation controls retain quote/locator/
  speaker validation. No compound role is forced into one label, no missing answer
  becomes none, and no relation score is presented as extractor admission.
- PASS — runtime: existing verified 8B/MPS/eager/bfloat16/non-thinking/greedy only.
  All 31 label strings preflight exactly, at most four tokens, before weights load.
  Runtime prompt/template/token audits match actual generation in all 198 calls.
  The underlying decoder, historical strategies and identities are unchanged.
- PASS — accounting/storage: the existing owned private/locked/atomic/expiring
  evaluation store is reused. Each actual choice, including nested relation
  choices, reserves cumulative accounting. Incomplete observations have at most
  two attempts; unclean in-flight state refuses. Completed errors and wrong answers
  are hashed and reused. Actual replay preserves all 166 observations, aggregate
  scores, 198-call total, spent time and one-attempt counters without generation.
  Config changes, corruption, quote tampering and budget/crash paths have tests.
- PASS — consumers/scope: the CLI accepts only the frozen synthetic suite and
  explicit model/output locations, plus no-model description. No private source,
  holdout/tuning switch, new model/dependency, training, UI, schema or organization
  mutation is introduced. The report cannot return an admission PASS; the current
  owner docs/projections preserve FEAT-0098's blocked admission.

Verification: 23 new comparison tests and 142 existing work-context tests pass in
the model runtime; 850 application regression tests run with no failures and one
optional graph skip. Live coverage is the installed MPS runtime, token preflight,
complete comparison and replay. CPU/CUDA, maximum context, corpus throughput and
product quality are not established. The report is finite-owned evaluation
evidence outside Git, not scratch; no task scratch or active model job remains.
Final checks pass: privacy scanning on 979 candidate files, generated catalog,
912 local links across fourteen task-touched documents and diff whitespace.

## Evidence-First Scope — RUN-109

RUN-109's PASS covers implementation, provenance, bounded execution and replay, not the
candidate's semantic interpretation. Functional FAIL blocks model admission.

- PASS — opt-in runtime: existing verified 8B, offline MPS/eager/bfloat16,
  non-thinking/greedy only. One pre-generation integration defect was corrected:
  explicit versioned 32-character labels, with the legacy eight-character default
  and eight-token/code/EOS constraints preserved. Real-adapter and tokenizer
  preflight checks cover both paths; no semantic prompt/expectation changed.
- PASS — evidence assembly: bounded uniquely located source spans and original
  context/speakers precede grouping. Fields and pair evidence are model-selected;
  code supplies exact quotes/locators, not missing semantic support. Inconsistent
  or multiply matching membership, recognized audit conflicts and bounds refuse
  without partial units or repaired output. Actual mixed-work and example refusals
  are observed. Unrecognized semantic errors remain visible, not claimed solved.
- PASS — evaluation: original fixtures are unchanged; twelve new compositional
  cases were frozen before inference and scored separately. Field coverage and
  purity prevent extra wrong-role facts from hiding behind expected keywords.
  Model, prompts, semantic labels, contracts, cases, expectations and runtime
  participate in identity. No post-output prompt/label/expectation adjustment.
- PASS — persistence: completed valid, wrong and refused observations are hashed
  and reused. Corruption or a changed unexpired configuration refuses instead of
  silently regenerating; clean incomplete attempts are limited to two, and an
  unclean in-flight crash refuses automatic resume. Actual replay reuses all 16
  cases with matching hashes, unchanged one-attempt counts and cumulative calls.
  Synthetic tests cover corruption, bounds and interruption, not actual crashes.
- PASS — admission: the evidence CLI forbids blended splits and requires an
  owned, unexpired, identity-matched development report re-scored against both
  cohorts before holdout. Primary semantic review remains a separate operator
  requirement, not an invented machine proof. Both cohorts fail; holdout is unused.
- PASS — scope: no private input/DB path, training, dependency install, source
  schema, production identity, UI or legacy mutation was introduced. Historical
  strategies/defaults/identities remain unchanged. Owner docs and projections
  distinguish this completed implementation from blocked Feature admission.

Verification: 142 work-context tests pass in the model runtime; 827 full
application tests pass with one optional graph skip. Actual offline generation,
label preflight and failure-preserving replay are observed. CPU/CUDA, maximum
context, private corpus and user-facing quality remain unobserved. Final catalog
and diff checks pass, as do privacy scanning on 974 candidate files and 903 local
links in fourteen task-touched documents. The initial adapter
failure report and corrected semantic report are explicit finite-lived evaluation
evidence outside Git, not task scratch. No active generation or scratch remains.

## Protocol Diagnostic Scope — RUN-108

PASS applies to the approved synthetic protocol diagnostic, not model-quality
admission. Feature coverage remains partial; prior extraction failures below
are historical evidence, not erased by this result.

- PASS — input and identity: the CLI accepts no private DB/Session or holdout
  input. Twelve new frozen cases generate an ordered, independently crossed
  numeric order/code matrix plus label/text controls. Expected decisions never
  enter prompts. Suite/configuration identities include cases, expectations,
  prompts, protocol/parser version, runtime and bounds; actual template/prompt
  hashes and answer tokenization are recorded for every condition.
- PASS — scoring boundary: recognized meaning, strict format and literal quote
  grounding remain independent. Ambiguous or failed cells stay in denominators;
  neither numeric nor label selection claims generated citations. Text decoration
  and missing-source failures were retained, not repaired into passes. All 46
  distinct case/answer texts received primary semantic review.
- PASS — persistence: the diagnostic reuses the evaluation owner, exclusive
  lock, atomic files and finite expiry outside Git. Wrong/invalid/refused completed
  observations are hashed and reused. Changed unexpired configurations and corrupt
  observations refuse without silent regeneration; an unclean in-flight crash
  cannot reset cumulative budgets. A clean-resume stale-error metadata bug was
  corrected and regression-tested without changing frozen inference/scoring.
- PASS — runtime/defaults: existing verified 8B assets and installed Foundry
  dependencies only, offline non-training MPS/eager/bfloat16. Diagnostic limits
  are opt-in; historical generation defaults and extraction strategies remain
  unchanged. Actual replay reuses 288/288 observations with matching digests and
  unchanged attempted-call/time totals; its asset verification passes again.
- PASS — consumers and projections: module/CLI/tests, README, privacy and
  architecture contracts, active Spec/Feature/Run and planning projections agree
  on diagnostic-only scope. No source schema or product/UI consumer is changed.

Verification: 108 work-context tests pass in both application and installed
model runtimes; 793 full regression tests pass with one optional dependency skip.
Privacy scanning passes 970 candidate files. Catalog, touched local links and
diff-whitespace checks pass. Real coverage is complete execution/replay on this
MPS environment; refusal, corruption, interruption and bound paths have injected
test coverage, not claims of all those failures occurring in this actual run.
No private-corpus or maximum-context readiness is established. The owned report
has finite retention; no task scratch or active generation process remains.

## Established Boundaries

- Official pinned public safetensors were installed and hash-verified. Only
  installation can use the network; it accepts no source/DB argument or token.
  The existing Foundry runtime was reused without package/model-state changes.
- Generation uses verified local files, eval/inference mode, remote-code denial,
  offline/telemetry settings and the tested outbound Python socket guard.
- Output is an inferred work unit or inferred pair judgment. Exact quotes,
  unique local locators and original speaker attribution are validated; scalar
  fields, missing paired evidence, unknown quotes and fabricated IDs fail closed.
- The actual trial demonstrated invalid model output being rejected, not repaired
  into apparent success. Quote validity is explicitly separate from entailment.
- Model/prompt/decoding/input identities govern per-case reuse. Tests cover
  interruption, changed identities, corrupt attribution, expiry, unknown owner,
  symlinks and exclusive writers. Private source/organization schemas are untouched.
- Model assets are durable installation state. Synthetic evaluation state has an
  explicit owner and 30-day inactivity expiry. No durable reference depends on
  a task scratch path; the known task-created public transfer log was removed.

## Evidence And Gaps

- The initial RUN-104 established 28 boundary tests and a 713-test regression,
  including separate optional simulation coverage. RUN-105 adds 19 boundary tests;
  all 47 passed in both runtimes and its full application regression passed 732
  tests with one optional graph-dependency skip. RUN-106 adds ten two-model and
  transfer tests: all 57 work-context tests pass in the optional model runtime;
  the application regression passes 742 tests with one optional graph skip.
- Actual MPS/bfloat16 inference and a real 8B generation time-limit refusal are
  observed. CPU/CUDA execution, a maximum-context request and whole-corpus
  integration remain unobserved. Other size/shape and interrupt behavior is
  tested with synthetic injections.
- The frozen holdout set was not executed: the development gate already failed.
  No private corpus was admitted and no semantic-quality PASS is claimed.

## Same-Model Comparison Boundaries

- Thinking protocol requires EOS and one closing delimiter. Tests exercise
  actual adapter decoding to prove reasoning, malformed and truncated outputs
  are never decoded into the final answer or stale diagnostics. Only final text
  and token counts persist. Greedy thinking and oversized budgets are rejected.
- Staged inventory accepts exact, unique source anchors, not one unit per message.
  Each detail keeps its anchor and reuses original messages. Pair evidence is
  side-scoped; a verdict's missing citation is not automatically filled in.
  Intermediate failure terminates the case and records its stage metrics.
- Stage prompts, strategy, thinking settings, budgets and attention backend
  participate in cache identity. Actual repeated staged evaluation reused all
  four validated results while preserving semantic failures. Synthetic tests
  verify changed identities and interrupted stages cannot reuse partial units.
- Each split's gate is computed separately, including `--split all`, so aggregate
  success cannot hide a failed development or holdout split. Fixed expectations
  and source contracts were not weakened to improve scores.
- The fused MPS numerical failure was isolated from semantic evaluation. The
  existing library's eager path completed the corrected comparison without
  changing dependencies/weights; rehash verification passes. Exact kernel cause
  remains unproven, not silently described as established. Other devices and
  actual maximum-size/time-stopped model runs were unobserved in RUN-105.
- No source schema, product consumer, UI, Foundry state, legacy organization,
  training or private-corpus path was added. Owned model/evaluation storage and
  finite evaluation retention remain unchanged; diagnostics created no scratch.

## Model-Size Comparison Boundaries — RUN-106

- The installer admits exactly two pinned public models, with separate owned
  directories, asset inventories and hashes. Unknown models fail before directory
  creation; explicit mismatch preserves the existing model. Manifest and owner
  must agree, and inference identity uses the verified model rather than the 4B
  default. Synthetic tampering/mismatch tests and real installation verify this.
- All 13 admitted 8B assets were verified (16,397,443,036 logical bytes). Snapshot
  links reuse owned content-addressed blobs rather than duplicate the weights.
  The 4B baseline remains intact and verifies; 8B rehash verification passes after
  inference. Neither installation is trained or quantized by this trial.
- Slow HTTP transfer was resumed through the already-installed official Xet
  client after verifying and stopping only the task's locked installer process.
  A new empty private transfer directory was configured before client import;
  chunk/shard caches were disabled. Exact task-owned diagnostics and empty
  directories were removed after successful installer exit. No shared cache,
  dependency or durable model asset was removed or changed by that cleanup.
- Both frozen strategies ran all development cases once. The 180-second thinking
  generation stop was rejected without decoding or retaining truncated reasoning.
  Single-sided evidence and wrong field shapes also failed closed. No invalid
  result was repaired, rerun with a new seed or counted as a semantic success.
- Neither candidate qualified for holdout. No private-source producer, new model
  beyond the two approved candidates, training, dependency update or UI work was
  introduced. Earlier replay evidence remains historical; no new claim of actual
  8B replay is made because invalid cases would regenerate on a repeated command.

## Routing

No observed contract-boundary defect remains. The failing semantic admission
gate is reported by Functional evaluation and blocks downstream corpus use.
Contract PASS is not acceptance of the model as a workflow reconstruction engine.

## Source-Choice Boundaries — RUN-107

- Both new strategies are opt-in; historical single/staged prompts and default
  routing remain unchanged. Classification/selection use existing verified local
  weights, offline controls and MPS eager. No dependency or model was installed.
- The existing runtime's prefix callback admits only finite answer-code token
  sequences and EOS. Tests exercise the actual adapter, overlapping prefixes,
  code collisions, malformed/oversized choices and incomplete/unknown output.
  Per-choice configuration is recorded separately from free-generation defaults.
- Source spans retain exact original text and are not automatically work units.
  Full messages remain in every decision. Excess spans/units/items, uncertain
  classification/membership and ambiguous grounded quotes refuse without silent
  truncation. Case time/call limits are explicit, not hard OS cancellation.
- Only model-selected fields, membership and citations are projected. Tests show
  deliberately wrong semantic selections remain visible rather than repaired.
  A non-uncertain pair requires explicit left/right evidence; continuation needs
  a separately selected right-side link. Missing evidence fails closed.
- Goal-first selection preserves its selected anchor in each unit. The actual
  mixed case violated that invariant and was rejected without publishing partial
  units as success. Field-level semantic errors are still a Functional concern.
- Stage metrics and content-free decisions survive a failed case. Strategy,
  prompt/projection version, choice protocol and bounds separate cache identities.
  An interrupted case cannot reuse partial work. Actual classified v2 replay
  reused all four validated cases and retained its failed semantic gate.
- 87 work-context tests pass in both runtimes; full regression runs 772 tests
  with no failures and one optional graph skip. Post-inference 8B rehash passes.
  CPU/float32 execution was observed only for one diagnostic choice, not the
  complete benchmark or whole-corpus throughput. Holdout was never executed.
- All diagnostic inputs were synthetic. No private source, embeddings, product
  consumer, UI, training or organization changed. No task scratch or active model
  process remains; owned synthetic evaluation reports retain their finite expiry.

## Continuity Notes

2026-09-23: RUN-104's installation/evidence boundaries remain valid historical
evidence. RUN-105 extends verified boundaries for thinking and staged inference;
its separate Functional FAIL still blocks private application. Runtime, CLI,
tests, package ownership, README and planning projections were checked for stale
single-pass/non-thinking assumptions.

2026-09-23: RUN-106 extends the installation catalog to the separately approved
8B model and verifies transport lifecycle and model-specific identity. Actual
time-limit refusal is now observed. Contract PASS remains narrower than the
Functional FAIL; model size did not establish readiness for private application.

2026-09-23: RUN-107 verifies bounded source-choice protocols and unchanged output
grounding, but none of its semantic gates passes. Contract PASS is partial and
does not promote the experimental strategies to private workflow reconstruction.

2026-09-23: RUN-108 completes the separately approved diagnostic contract and
observes failure-preserving real replay. No new extraction strategy is admitted;
the next approach remains a bounded planning decision, not private execution.

2026-09-23: RUN-109 implements the approved evidence-first candidate, fixes its
pre-generation label-length adapter defect, and verifies failure-preserving replay.
Its literal-grounding and lifecycle contracts pass; field/relationship semantics
fail. No independent semantic guarantee follows from the same-model audit.

2026-09-23: RUN-110 completes the matched role comparison without changing legacy
inference or expectations. Direct choices reduce excess roles but omit others;
order agreement and five correct relationship controls still do not admit the
model. Current PASS applies only to diagnostic implementation and preservation.
