# RUN-20260929-127: Personal Insight Context Comparison

## Metadata

- ID: `run-20260929-127`
- Status: `returned-to-spec`
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Evidence owner: [FEAT-0107](../feature/feat-0107-personal-insight-evidence-manifest.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Surface: `data`, analysis evaluation only
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-29`
- Updated: `2026-09-29`
- Current Phase: owner-approved contract correction

## Goal And Authorization

The owner requested continuation of the bounded evidence comparison proposed after [RUN-126](run-20260928-126-personal-insight-guide-behavior.md), and an explanation of discovery selection and possible recency or project concentration. Evaluate whether neighboring conversation changes the analysis appropriately before proposing production evidence expansion.

## Frozen Comparison

- Arm A reuses the prior frozen manifest with core v3, the same four selected playbooks, and the same result schema.
- Arm B preserves A and adds at most two preceding and two following eligible messages around each of two previously cited question anchors. Select by sequence before inspecting their content, clip each new message at 2,000 characters, and admit only messages before the original cutoff. Require matching source, eligibility, role, and full-text revision for the original anchors.
- This is an experimental evidence extension, including its higher per-message and excerpt limits; it does not change the production manifest contract. Freeze the playbooks to isolate evidence effects from category routing.
- Run two fresh answer-isolated subagent producers per arm. Add one single-episode opportunity control without a supplied solution, and one benign clarification control whose context is required to interpret it. Withhold expectations and previous answers from producers.
- Use the unchanged product result validator and a separate content reviewer. The primary agent owns final interpretation and persistence. Model binding is inherited; the interface does not expose the resolved model, seed, or sampling configuration.

## Success And Stop Conditions

- Claims must match admitted evidence, distinguish ordinary inquiry from friction, consider successful or benign context, and avoid requesting evidence already supplied.
- A supported single episode may justify a small reversible trial without a confirmed future benefit. A benign or resolved case must not be turned into a recurring defect.
- An unchanged uncertain result can be valid when the added context does not establish a current owner outcome. More findings are not a success criterion.
- Stop after the four real-sample outputs, two controls, and independent review. Do not expand the sample or alter guidance merely to obtain findings.
- Keep production behavior unchanged during this comparison. Product CLI execution, actual user benefit, feedback persistence, and a new sampling policy require their own evidence and implementation boundary.

## Evidence And Retention

Private inputs, outputs, provenance checks, distribution diagnostics, and review belong under the existing private evaluation archive owner. Tracked documents contain sanitized conclusions only. Remove task-owned staging after verified durable preservation.

The private archive contains 65 files, including the hash manifest. All copies were verified before the exact task-owned staging directory was removed. No completed output depends on the temporary location.

## Execution Result

- Four real-sample analyses and two synthetic analyses completed in fresh contexts. Thread-capacity limits delayed scheduling; no produced answer was retried or repaired. All six pass the unchanged product validator.
- Both real-sample arms returned two bounded evidence requests. The added messages support a more specific distinction between an assistant's scope substitution and a potentially ordinary follow-up question. They do not establish whether friction remains after the reported process changes.
- One expanded-input output requests four neighboring messages already supplied in full. This fails a declared functional check; structural acceptance does not close it.
- The intended positive control has unsuitable selected categories and cannot establish positive discovery capability. An input-only reviewer identified that limitation before output inspection. The benign control correctly treats repeated explanation as ordinary completed editing.
- The guide and production selector remain unchanged. Documentation now explains deterministic sampling, recency within source/month groups, the absence of project balancing, and the limits of interpreting a candidate as an overall priority.

## Evaluation And Review

- [Contract](../evaluation/eval-0108-contract-context-comparison.md): `PASS` for preservation and six structurally valid outputs.
- [Functional](../evaluation/eval-0108-functional-context-comparison.md): `FAIL` for requesting supplied evidence, with `partial` coverage of useful discovery. This bounded evaluation is complete; it is not a product-quality pass.
- Recommended disposition: review the evidence-request decision in the guide/spec, and treat candidate/category coverage and visible discovery scope as separate product planning concerns. The failed functional check remains open; no automated execution or technical recovery is pending.
- On 2026-09-29 the owner approved proceeding with visible scope/selection reasons, duplicate-request prevention, and goal-led type selection. [RUN-128](run-20260929-128-personal-insight-selection-contract.md) owns the contract correction; the separate consumer Run follows it. This diagnostic Run remains a functional failure, not a successful refinement.
