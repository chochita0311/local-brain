# Personal AI-Use Improvement Playbooks — Draft

## Status And Use

- Status: historical research proposal, `2026-09-27`. The executable playbooks now live under [`personal_insight_guides/playbooks/`](../../../src/localbrain/personal_insight_guides/playbooks/task_framing-v1.md); this draft is not loaded by Runs.
- Parent direction: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md) and the [research framework](session-improvement-analysis-framework.md).
- Implemented contract owner: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md) (`passed` for the synthetic foundation contract).

These playbooks help **any person who uses AI for work or learning** decide whether a change to their own process is worth trying. They are questions for an analyzer, not diagnoses of the LocalBrain owner. Public examples explain possible methods; local Session evidence and owner feedback decide whether a suggestion applies.

## Common Reasoning Rule

1. Start with the person's question or stated goal. A faster answer, better quality, deeper learning, lower cost, and easier collaboration can call for different changes.
2. Use the first evidence manifest to choose a few candidate playbooks. It is a sample, not a full transcript audit. An `ask` search hit is only a candidate until its message text and surrounding conversation support the connection.
3. Before calling a behavior repeated, inspect at least two distinct Session contexts and one plausible counterexample. Multiple turns from one Session are one episode of work, not independent recurrence. If conversation neighbors or outcomes are missing, request bounded follow-up evidence or abstain.
4. Separate four statements: **observed** words/actions in Sessions, **inferred** friction or cause, **proposed** intervention, and **owner-confirmed** outcome after trying it. Never promote one level into the next without evidence.
5. Return at most three useful findings. Each should show a short evidence trail, benign alternative, missing coverage, smallest practical experiment, effort/tradeoff, and one way the owner can judge whether it helped. An honest no-finding result is useful.

The current normalized source records messages, timestamps, source identity, and tool names. It does not retain opaque tool inputs/results, actual off-Session outcomes, or every AI service the person may use. The first bounded manifest selects at most three messages from a Session; it may miss a correction or counterexample. The evidence cautions below describe what the **current source projection could support after enough context is retrieved**, not what the first sample automatically proves.

## 1. Goal And Task Framing

- **Candidate:** A desired result, audience, hard constraint, or definition of done appears only after an answer missed it in several distinct tasks. Message evidence can support this when the earlier request and later correction are both visible.
- **Check:** Was the person intentionally exploring or discovering the goal? Did the task change after new information? Did the assistant ignore a clear initial instruction?
- **Try:** For a known task, make a short brief with purpose, audience, source material, constraints, and what a successful result should include. For exploratory work, preserve an open question and a checkpoint instead of pretending the goal was fixed.
- **Stop:** Do not blame the user's request when the assistant disregarded a clear instruction or the work changed legitimately.
- **Follow-up:** In a comparable task, ask whether the initial brief reduced substantive rework without reducing useful exploration.

## 2. Request And Feedback Style

- **Candidate:** The same response shape, depth, tone, or evaluation criterion is repeatedly repaired across unrelated Sessions. Both original requests and the user's corrections are needed.
- **Check:** Is the common issue a missing preference, or does the assistant repeatedly fail despite an explicit preference? Are the tasks actually comparable?
- **Try:** Keep one small example or request pattern for the recurring output. For subjective work, use a draft, critique against criteria, and revision loop.
- **Stop:** Do not write a global rule from one disagreement or one model error. A task-specific preference belongs in the task brief.
- **Follow-up:** Compare the next few similar outputs for useful first-pass fit and the amount of corrective prompting.

## 3. Context Recovery And Handoff

- **Candidate:** Background, decisions, constraints, or links are reconstructed after interruptions or across Sessions. The older source and later restatement must be inspectable.
- **Check:** Was the old context current and accessible? Did the person intentionally restate it for a new audience or changed scope?
- **Try:** Create a short source-linked handoff or decision note with the current goal, established facts, unresolved points, and next step. Prefer an existing knowledge location over a new parallel store.
- **Stop:** Do not recommend copying whole conversations or preserving stale assumptions as permanent instructions.
- **Follow-up:** On the next resume, ask whether the handoff let the person start from the current decision rather than reconstruct it.

## 4. Repeatable Procedure

- **Candidate:** Similar steps recur with stable inputs, outputs, and review points in separate work episodes. Message-only evidence can suggest a candidate but often cannot prove the exact tool sequence.
- **Check:** Which steps are mechanical, which require judgment, and which vary with the task? Is an existing template, script, or tool already available?
- **Try:** Use a checklist or template when the sequence is mostly human; a script for a stable objective transform; a focused skill only when contextual judgment and tool use recur together.
- **Stop:** Do not infer a repeatable command sequence or time saving from tool names, token counts, or three isolated excerpts. Request authorized tool-action evidence if exact mechanics matter.
- **Follow-up:** Try the artifact on another real occurrence and note whether it preserved quality and review while reducing repeated setup.

## 5. Learning And Explanation

- **Candidate:** The person repeatedly asks what a term means, why a result occurred, or how a method works. Session messages can show this directly.
- **Check:** Is this healthy curiosity, a teaching goal, a poorly explained answer, or a misconception that the AI introduced? Repeated questions alone are not inefficiency.
- **Try:** Ask for a worked example, underlying mechanism, contrast with a near miss, or a brief self-check. A focused learning note may help if the same concept recurs.
- **Stop:** Do not replace genuine learning with a shortcut, or prescribe memorization from an inaccurate answer.
- **Follow-up:** Ask the person to explain or apply the concept in a new example without copying the original answer.

## 6. Verification And Rework

- **Candidate:** A claim, analysis, draft, or generated artifact is corrected late after being treated as reliable. Messages can show corrections, but current normalized events do not prove tool success or final real-world correctness.
- **Check:** Was the first answer actually wrong, or did requirements change? What was the consequence of the error, and was there an authoritative source at the time?
- **Try:** Move a small source comparison, assumption check, or review criterion earlier. For recurring objective failures, propose a focused evaluation case.
- **Stop:** Do not label an iteration as a failure solely because there was a revision. Do not claim prevented errors without later outcome evidence.
- **Follow-up:** For the next similar task, record whether the early check caught a material error before downstream work.

## 7. Information And Tool Access

- **Candidate:** The person repeatedly carries information between places, searches for the same authoritative fact, or corrects stale AI knowledge. Transcript messages can suggest the friction; exact copy steps and access rights may be unavailable.
- **Check:** Which source is authoritative and current? Is access already approved? Is the retrieval need frequent enough to justify maintaining an integration?
- **Try:** Start with a source link and retrieval note. Add a scoped read-only tool only when repeated need, maintenance cost, and access policy support it.
- **Stop:** Do not propose broad private-data access or external writes just because an assistant could use more context.
- **Follow-up:** Check whether the next task reaches the correct source faster and whether the retrieved information stays current.

## 8. Decision Memory

- **Candidate:** Comparable alternatives are debated again because the earlier rationale, constraints, or revisit trigger is hard to recover. Distinct dated conversations are needed.
- **Check:** Did circumstances change enough to justify a new decision? Was the prior choice tentative rather than settled?
- **Try:** Keep a compact decision note: choice, alternatives, why, evidence, date, and the condition that should reopen it.
- **Stop:** Do not freeze a decision that should be revisited or infer final approval from a discussion transcript.
- **Follow-up:** On the next related decision, ask whether the note clarified what still applies and what changed.

## 9. AI Task Fit And Effort

- **Candidate:** A task seems to demand repeated prompting and review while a simpler method might work. Tokens, price, or Session length can locate a case to inspect but cannot measure net value.
- **Check:** What did the person value: speed, quality, learning, creativity, or confidence? How much off-Session work was involved? Did AI enable an outcome otherwise unavailable?
- **Try:** Narrow the AI role, use a deterministic tool for a simple transform, split the task into smaller checks, or choose an appropriate model when an actual comparison supports it.
- **Stop:** Do not call a high-cost Session wasteful or a short Session successful without quality and human-effort evidence.
- **Follow-up:** Compare end-to-end effort and result quality on a comparable task, using the owner's judgment rather than a universal score.

## 10. Work Flow And Personal Value

- **Candidate:** Work is repeatedly started but the person's stated priority or desired outcome is not revisited. Sessions show only part of the work, so this is a prompt for reflection, not a productivity diagnosis.
- **Check:** Were tasks exploratory, externally blocked, or completed outside the captured Sessions? Is the goal still important to the owner?
- **Try:** Define one small next outcome, a review point, or an explicit stop decision. Ask the owner which work actually mattered before recommending a new process.
- **Stop:** Do not infer personal priorities, health, motivation, or performance from transcript volume or unfinished chats.
- **Follow-up:** Ask whether the chosen next outcome was completed or intentionally changed, and whether the process made priorities clearer.

## 11. Configurable Assistant And Harness Fit

- **Candidate:** In an environment that supports persistent instructions or tools, repeated wrong skill selection, conflicting guidance, context loss, or avoidable execution friction is visible.
- **Check:** Was the behavior required by policy, a deliberate approval boundary, or a one-off failure? Is the guidance duplicated across several locations? Model and tool behavior may have changed since a rule was written.
- **Try:** Narrow a skill trigger, remove a stale instruction, route context to the right source, improve a checkpoint, or add a focused evaluation. Use an `AGENTS.md`-style rule only for a genuinely broad stable instruction.
- **Stop:** Do not weaken a real safety boundary or install more instructions solely because a Session had many tool calls. This category is conditional and never the default for nontechnical work.
- **Follow-up:** Compare the next relevant run for the specific unwanted behavior while also checking for new selection or instruction conflicts.

## Selecting An Intervention

Prefer a change that fits the **observed friction and the person's goal**. A one-time misunderstanding may need a clearer question; repeated structure may need a template; a stable transform may need a script; domain knowledge may need a source-linked note; contextual tool work may justify a narrow skill. If several options are plausible, recommend the smallest reversible trial and say why. If evidence cannot distinguish them, return a question or no finding.

The next design review should decide which playbooks have enough current message coverage for an initial release, which require targeted expansion, and which remain unavailable until an approved additional signal exists. The guide must never convert an initial sample's missing evidence into a confident recommendation.
