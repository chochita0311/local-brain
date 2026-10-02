# EVAL-0108 Contract: Guide Behavior

## Metadata

- ID: `eval-0108-contract-guide-behavior`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete` for the bounded output-limit correction and version integration
- Run: [RUN-20260928-126](../run/run-20260928-126-personal-insight-guide-behavior.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`, `docs-content`
- Created: `2026-09-28`

## Observed Failure And Correction

One of three baseline subagent outputs requested additional evidence with six admitted, distinct references. The product rejected it because the existing local limit is five. The frozen JSON schema and core v2 instructions did not expose that limit. This was an output-contract omission, not an invalid source citation or an unsupported interpretation.

Core v3 adds the existing acceptance limits within the Result section: request references and question length, finding count, finding and handoff text lengths, citation bounds, and conditional empty values. The loader selects the new version. Core v2, all selected playbooks, the report version, JSON schema, and validator behavior remain unchanged. A lossless comparison confirmed preservation of all earlier core rules, apart from the version label and added subsection.

All three fresh core v3 outputs passed the unchanged validator. The original six-reference output remains rejected; acceptance was not obtained by relaxing the contract or editing a producer's answer. A synthetic boundary check confirms that five references are accepted, six are rejected, and the active guide exposes the limit.

## Documentation Ownership And Preservation

- `docs-structuring`: incremental. Executable instructions remain beside their package. SPEC-0108 owns the guide contract; SPEC-0110 now points to it instead of identifying the historical standalone v1 guide as the current owner.
- `docs-shaping`: reshape, minimal. The added output-bounds subsection addresses the concrete inability to discover local acceptance limits. It does not reorder the guide or compress its evidence, trust, abstention, or intervention rules.
- The Developer Guide identifies the private evaluation archive and distinguishes it from product Run history. A local heading separates Session source configuration from personal analysis configuration; the configuration content is preserved.
- Content review covered the core, four selected playbooks, affected specification passages, and the relevant Developer Guide sections. The selected playbooks needed no change because the observed failure belongs to the shared output contract. Other playbooks were inventoried and covered by existing resource checks, not behaviorally evaluated across all categories. Historical research and prior evaluation records remain historical.

## Checks And Limits

- The focused personal-insight suite passes 25 tests, including the added citation-limit regression case.
- Both positive and negative synthetic behavior controls preserve their prior outcome after the guide update.
- The correction discloses limits through the trusted guide. The JSON schema alone still does not express every local validation condition; the validator remains authoritative. Future changes must keep these surfaces aligned.
- This evaluation does not establish product CLI execution, provider billing, general model reliability, or improvement in the owner's work. Private evidence, output text, and detailed reviewer citations remain outside Git.
