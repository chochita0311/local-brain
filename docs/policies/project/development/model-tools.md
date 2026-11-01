# Local Model Development Tools

These are explicit source-checkout operations. They do not run as an automatic Session-processing pipeline.

These tools require a source checkout. A normal installed application uses the
packaged commands in [the installation guide](../installation-and-storage.md).
From the repository root, install the optional development runtime with
`uv sync --python 3.11 --extra local-models --frozen`.

Public model weights stay in the shared Hub cache. Model registrations belong
under `<LOCALBRAIN_DATA_DIR>/models/<model-slug>`. Choose a private output
directory outside Git for each invocation and create its parent before passing
an explicit output path. These source-checkout tools are not invoked by normal
application startup.

## Operations

| Task | Guide |
| --- | --- |
| Compare search ranking and runtime | [Search comparisons](search-comparisons.md) |
| Prepare/replay full-history affinity | [Session simulation](session-simulation.md) |
| Run quoted work-context and protocol diagnostics | [Work context trials](work-context-trials.md) |
| Run source-claim extraction/binding diagnostics | [Source claim trials](source-claim-trials.md) |
| Run the bounded model-free comparator | [Work reconstruction](work-reconstruction.md) |
