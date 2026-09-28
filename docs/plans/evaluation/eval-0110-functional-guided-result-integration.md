# EVAL-0110 Functional: Guided Result Integration

## Metadata

- ID: `eval-0110-functional-guided-result`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `complete` for synthetic and local-renderer behavior; `partial` for provider execution
- Run: [RUN-20260928-122](../run/run-20260928-122-guided-personal-insight-result-integration.md)
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `fullstack-product`
- Lane: `backend`, rendered report
- Created: `2026-09-28`

## Evidence And Finding

- `.venv/bin/python -m unittest discover -s tests -p 'test_personal_insight*.py' -v` passed 17 synthetic evidence, guide, and consumer cases. `.venv/bin/python -m unittest discover -s tests -p test_markdown_rendering.py -v` passed 11 renderer cases, including the exact Session-route allowlist and default unresolved behavior.
- Synthetic consumer preparation froze v2 core/playbook provenance and selected JSON schema. Validation and Markdown generation accepted finding and additional-evidence results without invoking Codex CLI. Invalid values, unsupported citations, and recurrence from only one Session are rejected by the focused cases.
- A temporary local server backed by a synthetic fixture served a completed report. Chrome showed two active `/sessions/{id}` evidence links after the renderer correction, compared with zero before it; both routes came from the frozen synthetic manifest. No source or model call was triggered by opening the page.

## Limit

- The CLI path, real provider response, cancellation during a paid analysis, and semantic quality of a real report remain untested. This pass is bounded to the local guide/consumer correction.
