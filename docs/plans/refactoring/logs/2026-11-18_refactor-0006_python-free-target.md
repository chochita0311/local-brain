# Python-Free Backend Goal And Application Boundaries

## Log Type

- Type: `Handoff`
- Date: `2026-11-18`
- Related track: [REFACTOR-0006](../refactor-0006-rust-core-transition.md)
- Scope: reconcile the user's final backend goal and recommended application layout; planning only

## Outcome

The user clarified that completion means removing Python from the backend,
following questions about the incomplete migration and settings regression.
The subsequent directory question proposes separating API and web applications.
The [current target](../../project/python-free-backend-target.md) records Python-free
runtime/delivery acceptance and recommended `apps/api`, `apps/web`,
`apps/desktop` plus shared Rust `crates/` organization. The parent PRD, active
refactor plan, inventory entrance and Plans Index now reflect that final goal.

Earlier Terminal/settings results remain partial increments. HTTP/CLI/template,
TOML/zone and optional Python model execution are remaining work, not permanent
exceptions. The backend/runtime goal does not require deleting build/test tools,
legacy reference fixtures or the independent Node PTY/VT engine. Compatibility,
data preservation and existing feature admission remain binding.

## Actual Architecture Evidence

Current `desktop/src-tauri/src/main.rs` opens the native window, manages backend
startup/readiness/termination and provides OS commands. `desktop/ui` contains
startup/failure and window-specific assets. Actual product templates/static
assets live under `src/localbrain/`. PyInstaller entry/spec/build support still
packages the Python backend and models. These are current facts; the new layout
has not been physically applied and no native Rust API server is claimed.

Current common preferences code spawns one Rust child per operation. General
save calls preflight, save and readback as three operations with retained syntax
callbacks; source validation recomputes its input fingerprint. Eval0176 measured
11.208/41.029ms read/save medians versus Python0.036/0.485ms. The target calls
Rust core directly in a persistent Rust backend, retaining lock, durability and
readback/error stages. No per-component profile, speed fix or new benchmark is
claimed by this source/plan reconciliation.

## Verification And Handoff

Initial HEAD remains `e6958df0813b8652074c68a73ac61a8b551e59a8`; the prior
1,971-file dirty candidate is preserved. This update changes planning owners
only. Catalog checks/tests, local links, privacy, whitespace and exact input
hash comparison establish document scope; no runtime/build/native suite is
needed or claimed for these prose changes. Final counts are retained in the
existing configured private stage receipt. No code, directory, live process,
installed app, data or Git publication changes.

Next boundary is native host/rendering/codec and delivery under the final
Python-free goal, followed by coherent persistence/ingestion/read/retrieval and
native model execution. Adopt directory moves with their actual scripts,
resources and consumers. Whole-backend completion, model numerical/index
compatibility and declared minimum compiler/OS evidence remain due. This handoff
does not turn a proposed layout into an implemented or evaluated backend.
