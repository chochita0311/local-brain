mod claude;
mod codex;
mod usage;
use super::{ParsedSession, ScanControl};
use crate::backend::{BackendError, Result};
use std::path::Path;
pub fn parse_session(provider: &str, path: &Path) -> Result<Option<ParsedSession>> {
    parse_with_control(provider, path, &ScanControl::default())
}

pub(super) fn parse_with_control(
    provider: &str,
    path: &Path,
    control: &ScanControl,
) -> Result<Option<ParsedSession>> {
    super::common::path_text(path)?;
    control.check()?;
    match provider {
        "claude" => claude::parse(path, control).map(Some),
        "codex" => codex::parse(path, control).map(Some),
        _ => Err(BackendError::invalid(
            "provider",
            "Unsupported Session provider",
        )),
    }
}
