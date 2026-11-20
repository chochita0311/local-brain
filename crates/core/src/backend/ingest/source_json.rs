//! JSONL-specific marker inventory. Scalar grammar/materialization is shared.
use super::common::open_jsonl;
use crate::backend::json::MarkerInventory;
pub(crate) use crate::backend::json::Scope as SourceJson;
use std::{
    io::{BufRead, BufReader},
    path::Path,
};
pub(super) fn for_file(path: &Path) -> SourceJson {
    let path = path.to_owned();
    SourceJson::with_marker_factory(move || {
        let mut inventory = MarkerInventory::default();
        let mut reader = BufReader::new(open_jsonl(&path)?);
        let mut line = vec![];
        loop {
            line.clear();
            if reader.read_until(b'\n', &mut line)? == 0 {
                break;
            }
            inventory.add_text(&String::from_utf8_lossy(&line));
        }
        inventory.finish()
    })
}
