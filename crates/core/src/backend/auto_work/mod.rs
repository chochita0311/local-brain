//! Explicit experimental similarity preparation and passive local inspection.
mod common;
mod inventory;
mod store;
pub use inventory::{input_text, inventory, inventory_collect, source_texts};
pub use store::{prepare_inventory, purge, simulation_status};
pub mod graph;
mod python_rng;
mod simulation;
pub use simulation::{
    describe_groups, load_vector, simulate, vector_bytes, NativeSimulationEncoder,
    SimulationEncoder, SimulationOptions,
};
mod affinity;
mod affinity_index;
pub use affinity::{affinity_page, affinity_page_at};
pub mod reconstruction;
mod worker;
pub use worker::{
    preview_worker, run_preview_operation, NativePreviewSupervisor, PreviewSupervisor,
};
mod preview;
pub use preview::{prepare_preview, prepare_preview_with_supervisor, preview_page, PreviewOptions};
pub mod cache;
