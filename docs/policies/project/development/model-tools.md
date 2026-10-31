# Local Model Development Tools

These are explicit source-checkout operations. They do not run as an automatic Session-processing pipeline.

These tools require a source checkout. A normal installed application uses the
packaged commands in [the installation guide](../installation-and-storage.md).
From the repository root, install the optional development runtime with
`uv sync --python 3.11 --extra local-models --frozen`.

Public model weights stay in the shared Hub cache. Model registrations belong
under `<LOCALBRAIN_DATA_DIR>/models/<model-slug>`. Put comparison reports and
checkpoints under `<LOCALBRAIN_DEVELOPMENT_DIR>/`, outside all Git repositories.
The default development archive is `~/Library/Application Support/LocalBrain-Development`.
Create the chosen private parent before invoking a script with explicit output
paths. Such scripts never create development archives during normal app startup.

Migrating an archive preserves its original files and hashes. Historical paths
inside frozen logs or diagnostic snapshots describe their original execution;
they are evidence, not live commands or dependencies on those locations.

## Operations

| Task | Guide |
| --- | --- |
| Compare search ranking and runtime | [Search comparisons](search-comparisons.md) |
| Prepare/replay full-history affinity | [Session simulation](session-simulation.md) |
| Run quoted work-context and protocol diagnostics | [Work context trials](work-context-trials.md) |
| Run source-claim extraction/binding diagnostics | [Source claim trials](source-claim-trials.md) |
| Run the bounded model-free comparator | [Work reconstruction](work-reconstruction.md) |
