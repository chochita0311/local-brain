# EVAL-0069: Session Source Scope And Provenance — UX Heuristic

## Metadata

- ID: `eval-0069-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS WITH SUGGESTIONS`
- Run ID: `run-20260802-74`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-session-source-scope-and-provenance](../spec/spec-0069-session-source-scope-and-provenance.md)
- Execution Profile: `fullstack-product`
- Surface Lane: scope selection, provenance recognition, recovery, and continuity
- Evidence Coverage: `partial`
- Created: `2026-08-02`

## Scope

- Evaluated source distinction, filter visibility, URL predictability, empty and
  invalid recovery, direct-entry orientation, and narrow-control reachability.

## Checks And Evidence

- `전체`, Claude, Codex, and Codex Company are peers; no combined-Codex label
  makes the company boundary ambiguous.
- Selected Source updates the headline and empty-state wording together with the
  list, avoiding an apparently global count over a filtered inventory.
- Every visible Session projection names its source, so repeated `CX` cues remain
  understandable for scanning and assistive technology.
- Source transitions reset pagination and preserve only a valid Project filter;
  malformed URLs recover to a canonical, useful state instead of a phantom tab.
- Detail and parent/Subsession routes retain list orientation without implying
  that the Session itself changed source.
- Horizontal control overflow keeps future or owner-customized source options
  reachable without introducing a hidden secondary selector.

## Evidence Gaps

- Direct focus-ring, horizontal-scroll, browser history, and 320px observation was
  unavailable because the Browser skill's required in-app control capability was
  not exposed. Route normalization, selected-state semantics, link contracts,
  DOM order, accessible labels, and overflow rules are directly inspected.

## Findings

- No indistinguishable Codex scopes, misleading count, or invalid-filter dead end
  remains.
- Suggestion: observe horizontal source-control discoverability with more than
  four configured sources before adding any overflow affordance.

## Route

- Next action: `pass` with rendered-interaction evidence follow-up retained.
