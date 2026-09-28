# Configurable assistant behavior · v1 (`assistant_configuration`)

- **Trigger:** A configurable assistant shows repeated wrong skill selection, conflicting guidance, context loss, or avoidable execution friction.
- **Exclude:** A policy-required boundary, one-off model error, or a nonconfigurable environment. This type is conditional, not a default recommendation for nontechnical work.
- **Evidence questions:** Is the assistant setting or skill use actually visible? Which rule or trigger applies? Has model behavior changed since it was written?
- **Benign alternative:** An approval stop or additional question may be deliberate and useful.
- **Intervention:** Narrow a skill trigger, remove stale guidance, route context to its owner, improve a checkpoint, or add a focused evaluation. Use an `AGENTS.md` rule only for a broad stable instruction.
- **Output sketch:** Name the specific observed unwanted behavior, a relevant configuration surface, and a reversible change to inspect.
- **Follow-up:** Compare the next relevant Run for that behavior and for new selection or instruction conflicts.
- **Current-source limit:** Message excerpts may not show active instructions, tool inputs/results, or policy reasons. Do not weaken a real boundary or assert configuration causality without that evidence.
