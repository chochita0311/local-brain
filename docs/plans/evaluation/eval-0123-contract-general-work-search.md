# Contract Evaluation: General Work Search

## Metadata

- ID: `eval-0123-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-160](../run/run-20261013-160-general-work-search.md)
- Feature: [FEAT-0123](../feature/feat-0123-general-work-search.md)
- Spec: [SPEC-0123](../spec/spec-0123-general-work-search.md)
- Execution Profile: `backend-product`
- Created: `2026-10-13`

## Checked Contracts

- The original query controls source conditions, displayed input and return URLs.
  A second view removes common request framing without topic-specific dictionaries
  or generated text. Quotes, negative wording and condition notices prevent it.
  Empty and unchanged views add no encoding. Single-syllable topics remain valid.
- One foreground batch encodes at most two texts. Each vector must have the
  configured shape and finite values with a finite positive norm. Either cosine
  can admit evidence at0.45; their mean orders it. The original view retains its
  admitted evidence. Exact identifiers retain lexical admission and its reason.
- Dense comparison remains original-query cosine. Hybrid's API/CLI name, result
  fields and URL shapes stay compatible; ranking identifies `semantic-dual-view-v3`.
  `score` identifies the strongest view for selected evidence; `rank_score` its mean.
- Source policy, current revisions, exclusions, original offsets, generation
  checks and parent grouping remain enforced. Repeated spans do not add score.
  Rank/count all parents; retrieve at most three distinct excerpt texts per parent
  on the requested page. Pagination is not source sampling.
- No model, dependency, document-input identity, storage path or index migration.
  Actual private comparison loaded the existing index, performed zero document
  encodings and observed unchanged source DB and index stamps.

## Evidence And Limits

The 39 natural-search unit/HTTP checks pass, including five new tests for framing,
dual-view admission and ranking, one-view guards, invalid vectors and page-bounded
excerpt reads. Existing checks retain identifier boundaries, source changes,
generation freshness, deduplication, pagination, conditions and return navigation.
All 135 authored quality queries also pass comparator/current-engine agreement.
These are contract checks; model usefulness and regressions belong to the
[functional evaluation](eval-0123-functional-general-work-search.md).

No new screen, interaction policy, remote connector or publication boundary.
