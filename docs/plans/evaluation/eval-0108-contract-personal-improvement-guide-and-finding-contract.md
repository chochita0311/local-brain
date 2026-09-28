# EVAL-0108 Contract: Personal Improvement Guide And Finding Contract

## Metadata

- ID: `eval-0108-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete` for the product-neutral guide contract
- Run: [RUN-20260928-121](../run/run-20260928-121-personal-improvement-guide-and-finding-contract.md)
- Attempt: `1`
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Lane: `data`
- Created: `2026-09-28`

## Evidence And Finding

- `personal_insight_guidance.py` owns deterministic, bounded selection and strict result validation. Its only input is a versioned FEAT-0107 manifest; it has no database, source-file, model, or network read. `core-v2.md` and eleven `*-v1.md` playbooks are package-owned resources; the earlier v1 guide remains historical.
- Ask questions have strict routing priority over excerpt cues. At most four detailed playbooks travel with a Run. The core always supplies the complete category index and warns that selection is a routing aid, not evidence of a pattern.
- The result schema and local validator separate findings, no actionable finding, and bounded additional-evidence request. Findings cite admitted IDs, identify a selected category, distinguish a single observation from recurrence, state a disconfirming check and its status, retain a benign alternative and missing coverage, and carry a structured handoff for a separate work Session. Recurrence requires at least two distinct Sessions; supporting and counterexample references cannot overlap. The validator rejects an owner-confirmed outcome.
- The guide instructs the model to exclude analysis and maintenance material, treat source excerpts as untrusted, abstain when sampled turns cannot support a claim, and avoid a skill or persistent instruction as a default remedy. The evidence producer separately enforces primary-work admission.
- Core and selected playbook versions and SHA-256 digests are exposed for a consumer to freeze. A locally assigned finding ID is deterministic for the exact validated finding value. This Feature has no provider call, Run storage, Markdown writer, UI, or owner-review persistence.

## Limits And Route

- Source-level checks establish the value contract, not the accuracy or usefulness of an actual model recommendation. Lexical routing can omit a relevant detailed category when the question and sample lack its cues; the core requires a narrowed conclusion or another scoped Run in that case.
- The FEAT-0110 product consumer already existed with a v1 guide. Its adoption of this contract is a separately recorded post-Run correction; this PASS alone does not claim a live analysis Run.
