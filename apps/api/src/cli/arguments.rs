use localbrain_core::backend::{BackendError, Result};
use std::collections::{BTreeMap, BTreeSet};
pub struct Arguments {
    pub positionals: Vec<String>,
    values: BTreeMap<String, String>,
    flags: BTreeSet<String>,
}
pub(super) fn negative_number(raw: &str) -> bool {
    let Some(raw) = raw.strip_prefix('-') else {
        return false;
    };
    let raw = raw.strip_suffix('\n').unwrap_or(raw);
    let decimal = localbrain_core::backend::unicode::python_decimal;
    if let Some((integer, fraction)) = raw.split_once('.') {
        integer.chars().all(decimal) && !fraction.is_empty() && fraction.chars().all(decimal)
    } else {
        !raw.is_empty() && raw.chars().all(decimal)
    }
}
impl Arguments {
    pub fn parse(args: &[String], flags: &[&str], values: &[&str]) -> Result<Self> {
        let mut result = Self {
            positionals: vec![],
            values: BTreeMap::new(),
            flags: BTreeSet::new(),
        };
        let mut args = args.iter();
        let mut positional_only = false;
        while let Some(raw) = args.next() {
            if !positional_only && raw == "--" {
                positional_only = true;
                continue;
            }
            if !positional_only && raw.starts_with('-') && !negative_number(raw) {
                let (key, inline) = raw
                    .split_once('=')
                    .map(|(key, value)| (key, Some(value)))
                    .unwrap_or((raw.as_str(), None));
                if flags.contains(&key) && inline.is_none() {
                    result.flags.insert(key.into());
                } else if values.contains(&key) {
                    let value = inline
                        .map(str::to_owned)
                        .or_else(|| args.next().cloned())
                        .ok_or_else(|| {
                            invalid(&format!("argument {key}: expected one argument"))
                        })?;
                    result.values.insert(key.into(), value);
                } else {
                    return Err(invalid(&format!("unrecognized argument: {raw}")));
                }
            } else {
                result.positionals.push(raw.clone());
            }
        }
        Ok(result)
    }
    pub fn flag(&self, key: &str) -> bool {
        self.flags.contains(key)
    }
    pub fn value(&self, key: &str) -> Option<&str> {
        self.values.get(key).map(String::as_str)
    }
    pub fn string(&self, key: &str, default: &str) -> String {
        self.value(key).unwrap_or(default).into()
    }
    pub fn number<T: std::str::FromStr>(&self, key: &str, default: T) -> Result<T> {
        self.value(key)
            .map(|value| {
                value
                    .parse()
                    .map_err(|_| invalid(&format!("argument {key}: invalid value")))
            })
            .unwrap_or(Ok(default))
    }
    pub fn positional(&self, index: usize) -> Result<&str> {
        self.positionals
            .get(index)
            .map(String::as_str)
            .ok_or_else(|| invalid("a command argument is required"))
    }
    pub fn count(&self, min: usize, max: usize) -> Result<()> {
        if (min..=max).contains(&self.positionals.len()) {
            Ok(())
        } else {
            Err(invalid("unexpected or missing command arguments"))
        }
    }
}
pub fn invalid(message: &str) -> BackendError {
    BackendError::new(400, "arguments", message)
}
