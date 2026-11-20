//! Private local storage, writer leases and same-installation recovery.
pub mod accounting;
pub mod files;
pub mod layout;
pub(crate) mod migrations;
mod operations;
pub mod recovery;
pub use accounting::{aggregate_status, maintain_migration_backups, storage_status};
pub use layout::migrate_storage;
pub(crate) use operations::OPERATION_BUSY;
pub use operations::{operation_active, operation_lock, OperationGuard};
pub use recovery::{backend_storage_lease, create_backup, validate_backup, BackendStorageLease};
