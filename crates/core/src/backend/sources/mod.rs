//! User-managed Session source identities and explicit registrations.
pub mod profiles;
pub mod registry;
pub mod settings;
pub use registry::{
    load_and_reconcile_session_sources, load_session_source_settings, registered_session_roots,
};
pub use settings::{
    candidates, migrate_source_settings, recover_source_reconnect, source_inventory, update_source,
};
