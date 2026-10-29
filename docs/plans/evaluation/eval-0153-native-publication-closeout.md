# EVAL-0153: Native Integration And Public Candidate Closeout

## Metadata

- Result: `PASS` for the local build and bounded integration described below.
- Evidence coverage: complete for these checks; provider, recipient and broad model quality limits remain separate.
- Feature: [Context Search](../feature/feat-0153-context-search-conversation.md), with [Drive](../feature/feat-0150-drive-operation-guides.md) and the pending Learning/schema integration.
- Run: [Run226](../run/run-20261029-226-publication-and-native-integration.md).
- Evaluators: primary owns integration, contract, functional and final semantic review. User-requested read-only subagents supply privacy, docs-structuring and docs-shaping evidence; their findings do not grant publication approval.

## Build And Packaging

The ordinary desktop builder completed an Apple Silicon app and ZIP with Python3.11.15 on macOS26.5.1. The app remains version0.0.1, ad-hoc signed, with macOS14 declared as its minimum; notarization and other Mac execution are not established here. Public model weights are separate downloads/reused shared assets.

The first native build was correctly rejected because its Rust executable contained a builder path. The builder now passes Cargo encoded path-remapping flags for home, checkout and temporary roots while preserving existing compiler flags, including spaces. Seven build-support tests pass. Rebuild, deep/strict code-signature verification and raw/compressed Python/native private-path inspection pass; the check remains fail-closed.

Final deliverables are `dist/LocalBrain-apple-silicon/LocalBrain.app`, its portable `READ-ME.md`, dependency notices, build metadata, ZIP and matching SHA-256 file. The ZIP contains no database, Session JSONL or safetensors model files. Source-relative links added to the distribution guide were replaced with in-app navigation so the copied README remains usable outside a checkout. No runtime fixture or user data enters the app archive.

## Packaged Runtime And Interaction Witness

The new frozen backend ran with isolated data/cache/source roots and a synthetic desktop token. It admitted one local Context and one saved received-copy folder, including a stopped copy. Cached public4B/8B originals were reused; app registrations were created separately. Both models read the synthetic received Markdown file and answered the operator/daily06schedule question with a real excerpt. A broader8B query returned insufficient evidence; naming the file succeeded. This is execution evidence, not a claim that a larger model always retrieves better or that broad contact questions are reliable.

The packaged desktop edition was inspected in Chrome at1440×1000 and320×800. Model cards, selector, source distinction, evidence, Settings/Drive tab, controls and final actions remained reachable without outer overflow. Settings opening cleared conversation and input; localStorage/sessionStorage stayed empty. An arbitrary client root was rejected with422. Immediate resubmission during asynchronous cancellation produced a retryable busy response and retained input; retry after release worked. The test question did not occur in the isolated app-data files afterward.

An external synthetic `gcloud` fixture was invoked through the frozen adapter with the pinned synthetic account. Python/loader variables were absent in that SDK process. Its reauthentication failure produced a sanitized422 message, preserved jobs/account state and did not echo raw stderr. This failed before a Google API call; no actual Google credential or live Drive content was used. Cached status and the native route were available in the packaged process.

An existing native app instance was detected and preserved. The new Tauri window was not launched over it; genuine WKWebView/window-hide/recipient interactions remain unverified. These checks validate the frozen backend and packaged-browser surface, not every native-host interaction. Existing user servers, installed app, sources and sync jobs were not restarted or replayed.

## Schema And Regression Reconciliation

The source schema was retained. Its current semantic owners/checkers now agree on48ordinary tables plus1FTS object,543columns,52explicit indexes,59physical relations,29application relations and11subjects. All12global/focused Mermaid diagrams are checked, including the previously omitted Atlassian and Learning diagrams. The value registry has87families and all11generated dictionaries pass their exact check.

The current cleanup ledger has732objects:620keep and112defer. Existing decision defaults,118column overrides, defer groups and prior table decisions are preserved. Three explicit Learning table decisions and evidence were added. Five synthetic Learning tests cover immutable revisions, invalid-batch atomicity, idempotent submissions, one-way self-assessment, reading records, RESTRICT ownership and reversible visibility. This does not establish learning benefit or the full learning-reader workflow.

The full suite passes **1,421tests**. This resolves the five previously reported stale checker/audit/count failures without weakening their contracts. Schema/presentation/value/audit/Mermaid checks and JavaScript syntax also pass. Older Runs retain the counts and failures observed at their own execution times.

## Documentation And Publication Boundary

The initial privacy inventory covered all1,579publishable files mechanically, with contextual review of suspicious matches. Findings were an authenticated corporate design-source name and three obsolete local evidence locators. Public aliases now preserve authenticated provenance, date, scope and contribution; temporary locators are generalized without claiming their captures are public or retained. No known credential, real Drive destination or private corpus excerpt was found in the reviewed matches. This is a current-candidate check, not a Git-history rewrite or universal secret-detection guarantee.

The documentation reviewers accounted for all106initial selected documents: authored prose was read, while exact generated catalogs/dictionaries were checked mechanically. Necessary changes preserve source authority, force and history: current model/format choices and approval gates are reconciled, historical OAuth attempts point to their gcloud successors, auth consumers inherit the producer contract, intact Drive/persistence blocks move to their owning sections, and resolved schema debt moves from backlog to this Run's history. Broad chronology compression and optional reorganization were withheld. New/delta documents and the final candidate receive another frozen review before commit/push.

Source publication is authorized by the owner's current request. Binary delivery/upload, installed-app replacement, real two-account My Drive/Shared Drive operations, broad model quality and signed/notarized public release remain separate. The source commit and verified remote update are reported by the final execution receipt; this artifact does not claim they occurred before the publication action.
