//! Bounded source-backed sample preparation and goal extraction.
mod contract;
mod input;
mod preparation;
pub use contract::{reconstruct, validate_snapshot, VERSION};
pub use input::{load_snapshots, validate_manifest};
pub use preparation::prepare_current;
mod sql;
