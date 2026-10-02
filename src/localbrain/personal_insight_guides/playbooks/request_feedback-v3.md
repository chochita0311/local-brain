# Request and feedback · v3 (`request_feedback`)

- **Trigger:** A response shape, depth, tone, or review criterion is repaired across distinct comparable Sessions; or the single-episode evidence below establishes a concrete goal/output mismatch with burden.
- **Exclude:** A disagreement without an explicit goal or burden, changed requirements, healthy exploration, or a corrected output already accepted with no remaining friction. An assistant ignoring a clear request does not establish poor user wording, recurrence, or a need for persistent configuration.
- **Evidence questions:** Which goal/output relationship is directly visible, and when was the goal made explicit? What correction or review method has already been supplied or accepted? For a recurring preference, are distinct comparable Sessions present? For a single episode, what specific comparison would add value in the next similar response without making the owner restate the goal? If proposing to fix the current task, is its unresolved state actually established?
- **Benign alternative:** Iteration may be intended exploration. A one-off assistant error may never recur; a subsequent correction may have resolved the issue.
- **Intervention:** Choose the smallest applicable trial: check one output against the existing explicit result criterion, request a focused correction, compare a draft with a short example, or retain a reusable request pattern only when comparable recurring evidence supports it. Do not make the owner rewrite an already clear request as the default remedy.
- **Output sketch:** Name the goal/output relationship and visible burden, who missed the instruction when observable, the competing explanation, and one bounded reversible trial. Explain the action's value beyond the supplied correction and whether it concerns the current task or a future response. A single episode remains `single_observation`; do not diagnose a persistent skill, configuration, or user deficit from it.
- **Follow-up:** Check whether the next response meets the evidenced result criterion with less corrective work. Preserve whether that criterion was visible initially or established by a later correction. Benefits remain hypotheses until the owner checks them.
- **Current-source limit:** Inventory the supplied request, response, corrections, and outcome first. Ask only for a specific omitted message or fact that could reverse the interpretation; never request a supplied complete turn again. Missing future benefit alone does not block a reversible trial.

## Single-episode evidence

Require a concrete owner goal, a visible response that fails that goal, and a visible correction or other burden. Establish them through one of these routes:

1. The initial goal, assistant response, and owner's reaction are directly supplied.
2. A later owner correction explicitly names the intended result, the preceding response is supplied, and the assistant specifically acknowledges the corresponding mismatch. This route supports only a bounded output-review trial. It does not establish how clearly the absent original request was worded or that the goal was explicit before the response. Cite the correction and admission, state the missing original request in `coverage_limit`, and consider changed requirements.

A vague complaint plus an assistant apology does not establish the concrete goal. An explicit change of requirements is not an assistant failure. A corrected output already accepted with no further friction remains excluded. When the goal is established through the second route, do not request the original wording merely to prove it was clear; request it only if the proposed action actually depends on the earlier wording or sequence.

After the evidence threshold is met, use the core's outcome decision. A future trial must specify an added behavior, such as comparing the requested object with the object actually changed before reporting completion. Merely repeating the corrected answer, adding a generic checklist, or promising to be more careful does not establish added value.
