//! Reviewed local lessons and private self-reported practice. No model/network calls.
mod diff;
pub mod presentation;
mod service;
mod validation;
pub use service::*;
pub use validation::{validate_packet, MAX_PACKET_BYTES};
