# EVAL-0153: Transient Context Search

## Metadata

- ID: `eval-0153`
- Status: `complete`
- Result: `PASS` for the bounded first delivery; final human acceptance remains open.
- Feature: [FEAT-0153](../feature/feat-0153-context-search-conversation.md)
- Run: [Run225](../run/run-20261029-225-context-search-conversation.md)
- Spec: [SPEC-0153](../spec/spec-0153-context-search-conversation.md)
- Profile: `fullstack-product`; contract, functional, design, ux-heuristic.
- Review: primary performed logical roles sequentially; same-author evidence, not independent certification.

## Evaluator Results

| Evaluator | Result | Evidence and limit |
| --- | --- | --- |
| Contract | PASS | Separate shared Hub originals, app manifests and private kernel caches; server-admitted sources; read-only native tools; no answer schema, transcript file or browser persistence. Native route/token/origin and worker entry preserve existing boundaries. |
| Functional | PASS |35focused tests, actual4B/8B synthetic inference and a real browser→HTTP→worker answer/cancel flow. Existing full-suite failures remain separate below. |
| Design | PASS | Screen-alignment extend: existing shell, prose/control tokens, Settings cards and evidence disclosures. Rendered1440×1000 and320×800, normal and long unbroken path/text, no outer overflow and final actions reachable. |
| UX heuristic | PASS | Empty/source-missing/model-missing, selection, same-screen follow-up, busy, error/retry, stop, Settings clearing and navigation/Back reset exercised. Status and evidence retain their own roles. Visibility reset branch exercised with a browser fixture; actual native/host visibility events remain unverified. |

## Implementation And Checks

- Models use the pinned native Qwen tool template, with validated source/file listing, literal search and partial reads. Search excerpts include nearby lines, explicit result/loop/input budgets and inaccessible/changed-file coverage. Unknown writes, source/path escape, symlinks, incomplete receive staging and changed selected-file type are refused. One unavailable source does not hide other readable sources. Notes use current enabled/readable collected bodies; no new embedding/index is prepared.
- Generation runs in one owned child at a time. Model switch, abort and shutdown terminate the owned worker; owner EOF terminates even during loading. Python network blocking stays in that child. Requests/results travel only over pipes and RAM; per-turn buffers/evidence are released while public weights may stay resident. Missing public assets require explicit Settings installation. Generation does not require embedding packages.
- Source browser: cached4B connection through Settings completed without redownloading; first real question returned the correct operator and daily06schedule with actual excerpt. An in-flight follow-up was canceled; server busy became false within the observed1.2second wait. The local user server and Drive jobs were not restarted or replayed.
- Browser protocol fixtures checked two successful turns with `user,assistant,user` follow-up history, selecting8B for the second response, retryable409, stop, limited coverage, safe formatted body and long relative evidence paths. Settings opening and navigation away/Back clear messages/input; refresh begins empty. localStorage/sessionStorage remained empty. Model-missing and no-source states keep Settings actions reachable. Native controls remain subject to recipient verification.
-35focused tests cover tools, native protocol/evidence, request admission, shared discovery/setup, process reuse/switch/cancel/EOF, cache separation, safe rendering and origin/no-store stream cleanup. JavaScript syntax, app-guide destinations, desktop boundary tests and Python3.9 grammar checks pass; grammar checks do not certify optional-model runtime on3.9.
- The final full-suite result and package/privacy checks are recorded in the Run closeout. Five pre-existing Learning/schema/audit/presentation/value-registry failures remain; all nine baseline schema/registry/builder/test fingerprints match work start. No conversation schema change was made.

## Actual Model Witness

Both pinned models used the same single synthetic Markdown file and Korean question, without embedding or network downloads:

```text
# Demo pipeline
Airflow 운영 담당자는 Demo operator입니다.
Airflow 배치는 매일 오전 06시에 실행합니다.
장애 대응 절차는 운영 가이드에서 확인합니다.
```

The question asked who operates Airflow and when it runs. Both answers named the operator and daily06time and cited the actual file excerpt. Observed first-question totals, including verification/loading and tool rounds, were29.53seconds for4B and51.51seconds for8B on a64GiB Mac using MPS, PyTorch2.8.0, Transformers4.57.6 and huggingface-hub0.36.2. Public revisions are pinned by the model catalog/spec. Initial trials exposed missing neighboring facts when a search returned only one line; surrounding excerpts and a tool-use reminder corrected this witness. These are single-fixture observations, not latency targets, broad Korean/contact-ranking accuracy, corpus completeness or all-device memory evidence. Real negative/conflict/multifolder quality and native recipient-host certification remain outside this bounded witness.

## Remaining Boundary At Run225 Closeout

Implementation is available in the source and wheel. The installed native application was not rebuilt or replaced, and the existing user development server was left running. Restart the development server to load new backend routes; installed-app delivery requires its normal rebuild/replacement. Saved history, embeddings, quantization/new inference engines and broader model-quality work require their separate design. No live private corpus, external AI or Drive publication was used in these checks.

Later [Run226 native/publication evidence](eval-0153-native-publication-closeout.md) adds an actual native build and isolated frozen-model/SDK checks. It preserves the original Run225 witness and remaining provider/recipient/quality limits; the existing installed user app/server still has not been replaced or restarted by this work.
