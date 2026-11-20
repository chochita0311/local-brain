//! User-managed Local Context registry and indexed-document readers.
mod mime;
pub mod queries;
pub mod scan;
pub mod service;
pub use queries::*;
pub use service::*;
