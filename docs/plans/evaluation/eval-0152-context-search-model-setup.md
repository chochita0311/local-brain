# EVAL-0152: Generation Model Setup

- Feature: [FEAT-0152](../feature/feat-0152-context-search-model-setup.md)
- Run: [Run224](../run/run-20261029-224-context-search-model-setup.md)
- Result: contract, functional, design and ux-heuristic pass for Settings producer scope; same-author sequential review.

Pinned4B/8B cards extend the existing Search Model panel and use its controls, spacing and status family. Local presence discovery does not hash/load/download models. Explicit install connects shared cached assets or downloads missing public assets; dedicated child performs verification. Only embedding installation prepares its index. Canceling generation-model setup does not cancel embedding search.

Six synthetic model tests pass, covering cached reuse, registration separation, unknown-key refusal, index isolation, cancel isolation and command admission. Settings script syntax passes. Rendered source browser inspected before and after at1440×1000 and320×800: cached actions for both models wrap/read correctly, final action/footer reachable, document width equals viewport, existing modal focus/close retained. No new design family or conversation schema. Actual cached-model verification/generation and conversation selector belong to the dependent Feature0153; no live download or native-binary certification inferred here.

Integration adds a seventh test for generation-runtime independence from embedding packages. The real source browser's explicit4B cached connection completed; the final shared integration witness is [EVAL-0153](eval-0153-context-search-conversation.md).
