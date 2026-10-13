# SPEC-0123: General Work Search

## Metadata

- ID: `spec-0123`
- Status: `approved`
- Feature: [FEAT-0123](../feature/feat-0123-general-work-search.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Run: [RUN-160](../run/run-20261013-160-general-work-search.md)
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Created: `2026-10-13`

## Comparison Contract

The baseline is `semantic-cosine-exact-v2`, cutoff0.45 and the installed pinned
Qwen embedding model. Compare original-only queries with a bounded second view
that removes unambiguous retrieval-request framing, retaining the topic and action.
Evaluate a small fixed pooling grid (maximum, equal blend, original-heavy blend)
on development and prior regression sets. Also compare the existing query
instruction, Qwen's official retrieval example, a general past-work instruction
and unprompted encoding before selecting a method. Query instructions describe
the retrieval task without supplying topic answers. No guessed synonyms.
Quoted, negative, conflicting or uncertain conditions must not lose meaning.
Scope interpretation, URLs and displayed input always use the original query.

Keep original semantic admission and exact single-identifier behavior. A second
view may admit additional relevant evidence at the same cosine cutoff; report
that effect rather than describe its score as a probability. Parent aggregation
uses strongest distinct evidence, never a sum rewarding many fragments.
Encode at most two distinct query texts in one foreground batch. Original-only
queries incur no extra model pass. Document/input identity stays compatible.

## Acceptance And Verification

Choose a common method only if development ordering or broad-topic coverage
improves, with aggregate Recall@10 and Hit@10 on existing regression queries no
more than two percentage points below baseline. Check family-level results and
individual regressions, not only averages. Freeze the candidate before observing
the new holdout and report its results without relabeling or retuning on it.

Measure uncached warm search in alternating baseline/new order on the existing
private index. A modest batching cost is acceptable when usefulness improves;
report milliseconds and runtime conditions. Reject changes requiring seconds of
extra inference for this increment. Preserve all evidence and source restrictions.

Add deterministic tests for framing removal, retained semantic actions,
quotes/negation/identifiers, unchanged condition filtering, dual-vector validation,
stable grouping/pagination and document-encoding count. Run relevant existing
unit/HTTP checks and the full suite after integration. Verify the running route.
All test corpora and public examples are authored synthetic material; private
observations and machine-specific receipts remain outside Git.

## Selected Method And Integration

Freeze `semantic-dual-view-v3`: equal mean of original and conservative focused
query cosines, with admission from either at0.45. An unchanged view is encoded
once. Keep `dense` as original-only comparison and exact single-identifier lexical
admission in hybrid. Quotes, negation and condition notices use one original view.
One-syllable topics remain valid. The instruction and document identity stay fixed.
Load excerpt text after parent ranking and pagination; count all eligible parents.

Original-only instruction replacements lose useful recall on some development
sets. Fixed instruction mixtures do not provide a better broad-query tradeoff
than the selected framing view. They are rejected experiments, not runtime paths.
Selection precedes the new holdout observation; its fixture hash is preserved in
the functional report. The selected change improves first-result usefulness on
the authored broad development queries while retaining prior-set recall. Some
per-query recall/order regressions remain explicitly reported.
