# EVAL-0107 Functional: Personal Insight Evidence Manifest

## Metadata

- ID: `eval-0107-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `complete` for the synthetic evidence-only contract
- Run: [RUN-20260927-118](../run/run-20260927-118-personal-insight-evidence-manifest.md)
- Attempt: `2`
- Feature: [FEAT-0107](../feature/feat-0107-personal-insight-evidence-manifest.md)
- Spec: [SPEC-0107](../spec/spec-0107-personal-insight-evidence-manifest.md)
- Execution Profile: `foundation-contract`
- Lane: `data`
- Created: `2026-09-28`

## Evidence And Finding

- Eight in-memory SQLite tests using synthetic Claude and Codex Sessions passed with `.venv/bin/python -m unittest discover -s tests -p test_personal_insight_evidence.py -v`.
- The cases cover input validation, empty scope, primary work and message eligibility, source filtering, local date boundaries, unknown and future event times, FTS-ranked `ask` selection and honest fallback, source/month spread, all hard caps, deterministic output, and stale or unavailable references after source changes.
- The tests compare `connection.total_changes` across manifest production. The producer reads normalized Session tables only; Usage & Cost route ownership has no call into this producer. No private Session, native JSONL, model, network, or browser state was used.
- The first functional pass found that casefold expansion could place a lexical excerpt beyond the original text. Attempt 2 maps the folded match position back to an original-text character offset; the synthetic regression now passes.

## Scope And Route

- The required evidence-only behavior in SPEC-0107 is covered. This result does not assess the later analysis guide, CLI execution, real-model response, or whether a generated recommendation is useful.
- The earlier [contract evaluation](eval-0107-contract-personal-insight-evidence-manifest.md) remains a partial source-inspection result. This functional pass supplies its missing synthetic behavior evidence, so the foundation Run can close without claiming a real analysis Run.
