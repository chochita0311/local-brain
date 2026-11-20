//! Ordered, arbitrary-scalar TOML values without recursive JSON.
use super::{Fault, Result};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashSet;

#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Node {
    pub kind: String,
    pub value: Value,
}

#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Arena {
    root: usize,
    nodes: Vec<Node>,
}

impl Arena {
    /// Fixed transport metadata only; raw TOML/application values use import.
    pub fn from_json(value: Value) -> Result<Self> {
        let mut result = Self {
            root: 0,
            nodes: vec![],
        };
        let mut pending = vec![(None, String::new(), value)];
        while let Some((parent, key, value)) = pending.pop() {
            let id = result.nodes.len();
            if let Some(parent) = parent {
                if result.kind(parent) == "table" {
                    result.nodes[parent]
                        .value
                        .as_array_mut()
                        .unwrap()
                        .push(json!([key, id]));
                } else {
                    result.nodes[parent]
                        .value
                        .as_array_mut()
                        .unwrap()
                        .push(json!(id));
                }
            }
            let (kind, encoded) = match value {
                Value::Object(values) => {
                    pending.extend(
                        values
                            .into_iter()
                            .rev()
                            .map(|(key, value)| (Some(id), key, value)),
                    );
                    ("table", json!([]))
                }
                Value::Array(values) => {
                    pending.extend(
                        values
                            .into_iter()
                            .rev()
                            .map(|value| (Some(id), String::new(), value)),
                    );
                    ("array", json!([]))
                }
                Value::String(value) => ("string", json!(value)),
                Value::Bool(value) => ("boolean", json!(value)),
                Value::Number(value) if value.is_i64() || value.is_u64() => {
                    ("integer", json!(value.to_string()))
                }
                Value::Number(value) => (
                    "float",
                    json!(super::native::float_hex(
                        value.as_f64().ok_or_else(Fault::protocol)?
                    )),
                ),
                Value::Null => ("null", Value::Null),
            };
            result.add(kind, encoded);
        }
        Ok(result)
    }
    pub fn has_nonfinite(&self, id: usize) -> Result<bool> {
        let subtree = self.subtree(id)?;
        Ok(subtree.nodes.iter().any(|node| {
            node.kind == "float"
                && node
                    .value
                    .as_str()
                    .is_some_and(|s| ["nan", "-nan", "inf", "-inf"].contains(&s))
        }))
    }

    pub fn parse(value: Value) -> Result<Self> {
        let arena: Self = serde_json::from_value(value).map_err(|_| Fault::protocol())?;
        if arena.root != 0 || arena.nodes.is_empty() {
            return Err(Fault::protocol());
        }
        let mut parents = vec![0usize; arena.nodes.len()];
        for (index, node) in arena.nodes.iter().enumerate() {
            match node.kind.as_str() {
                "table" | "array" => {
                    for child in arena.children(index)? {
                        if child <= index || child >= parents.len() {
                            return Err(Fault::protocol());
                        }
                        parents[child] += 1;
                    }
                }
                "string" | "integer" | "float" | "date" | "time" | "datetime" => {
                    let value = node.value.as_str().ok_or_else(Fault::protocol)?;
                    if node.kind == "integer" {
                        let digits = value.strip_prefix('-').unwrap_or(value);
                        if digits.is_empty()
                            || !digits.bytes().all(|c| c.is_ascii_digit())
                            || (digits.len() > 1 && digits.starts_with('0'))
                            || value == "-0"
                        {
                            return Err(Fault::protocol());
                        }
                    }
                }
                "boolean" if node.value.is_boolean() => {}
                "null" | "unsupported" if node.value.is_null() => {}
                "surrogate-string" => {
                    let points = node.value.as_array().ok_or_else(Fault::protocol)?;
                    if !points
                        .iter()
                        .all(|p| p.as_u64().is_some_and(|p| p <= 0x10ffff))
                    {
                        return Err(Fault::protocol());
                    }
                }
                _ => return Err(Fault::protocol()),
            }
        }
        if parents[0] != 0 || parents[1..].iter().any(|count| *count != 1) {
            return Err(Fault::protocol());
        }
        Ok(arena)
    }

    pub fn table() -> Self {
        Self {
            root: 0,
            nodes: vec![Node {
                kind: "table".into(),
                value: json!([]),
            }],
        }
    }

    pub fn kind(&self, id: usize) -> &str {
        &self.nodes[id].kind
    }
    pub(super) fn value(&self, id: usize) -> &Value {
        &self.nodes[id].value
    }
    pub(super) fn append(&mut self, id: usize, child: usize) -> Result<()> {
        if self.kind(id) != "array" {
            return Err(Fault::protocol());
        }
        self.nodes[id]
            .value
            .as_array_mut()
            .ok_or_else(Fault::protocol)?
            .push(json!(child));
        Ok(())
    }
    pub fn text(&self, id: usize) -> Option<&str> {
        (self.kind(id) == "string")
            .then(|| self.nodes[id].value.as_str())
            .flatten()
    }
    pub fn scalar(&self, id: usize) -> Value {
        match self.kind(id) {
            "string" | "boolean" => self.nodes[id].value.clone(),
            "integer" => self.nodes[id]
                .value
                .as_str()
                .and_then(|s| s.parse::<i64>().ok())
                .map(Value::from)
                .unwrap_or(Value::Null),
            _ => Value::Null,
        }
    }
    pub fn entries(&self, id: usize) -> Result<Vec<(String, usize)>> {
        if self.kind(id) != "table" {
            return Err(Fault::protocol());
        }
        let mut keys = HashSet::new();
        self.nodes[id]
            .value
            .as_array()
            .ok_or_else(Fault::protocol)?
            .iter()
            .map(|entry| {
                let pair = entry
                    .as_array()
                    .filter(|p| p.len() == 2)
                    .ok_or_else(Fault::protocol)?;
                let key = pair[0].as_str().ok_or_else(Fault::protocol)?.to_owned();
                if !keys.insert(key.clone()) {
                    return Err(Fault::protocol());
                }
                let child = pair[1]
                    .as_u64()
                    .and_then(|n| usize::try_from(n).ok())
                    .ok_or_else(Fault::protocol)?;
                Ok((key, child))
            })
            .collect()
    }
    pub(super) fn children(&self, id: usize) -> Result<Vec<usize>> {
        match self.kind(id) {
            "table" => Ok(self.entries(id)?.into_iter().map(|(_, n)| n).collect()),
            "array" => self.nodes[id]
                .value
                .as_array()
                .ok_or_else(Fault::protocol)?
                .iter()
                .map(|v| {
                    v.as_u64()
                        .and_then(|n| usize::try_from(n).ok())
                        .ok_or_else(Fault::protocol)
                })
                .collect(),
            _ => Ok(vec![]),
        }
    }
    pub fn get(&self, id: usize, key: &str) -> Option<usize> {
        self.entries(id)
            .ok()?
            .into_iter()
            .find(|(k, _)| k == key)
            .map(|(_, n)| n)
    }
    pub fn require(&self, key: &str) -> Result<usize> {
        self.get(0, key).ok_or_else(Fault::protocol)
    }
    pub fn keys(&self, allowed: &[&str], required: &[&str]) -> Result<()> {
        let entries = self.entries(0)?;
        if entries.iter().any(|(k, _)| !allowed.contains(&k.as_str()))
            || required
                .iter()
                .any(|k| !entries.iter().any(|(name, _)| name == k))
        {
            return Err(Fault::protocol());
        }
        Ok(())
    }
    pub fn add(&mut self, kind: &str, value: Value) -> usize {
        self.nodes.push(Node {
            kind: kind.into(),
            value,
        });
        self.nodes.len() - 1
    }
    pub fn set(&mut self, table: usize, key: &str, child: usize) -> Result<()> {
        let mut entries = self.entries(table)?;
        if let Some((_, n)) = entries.iter_mut().find(|(k, _)| k == key) {
            *n = child;
        } else {
            entries.push((key.into(), child));
        }
        self.nodes[table].value = json!(entries);
        Ok(())
    }
    pub fn reorder(&mut self, table: usize, first: &[&str]) -> Result<()> {
        let entries = self.entries(table)?;
        let mut result = vec![];
        for key in first {
            if let Some(entry) = entries.iter().find(|(name, _)| name == key) {
                result.push(entry.clone());
            }
        }
        result.extend(
            entries
                .into_iter()
                .filter(|(name, _)| !first.contains(&name.as_str())),
        );
        self.nodes[table].value = json!(result);
        Ok(())
    }
    pub fn import(&mut self, source: &Self, root: usize) -> Result<usize> {
        let imported = source.subtree(root)?;
        let offset = self.nodes.len();
        for mut node in imported.nodes {
            match node.kind.as_str() {
                "table" => {
                    for pair in node.value.as_array_mut().ok_or_else(Fault::protocol)? {
                        let pair = pair.as_array_mut().ok_or_else(Fault::protocol)?;
                        pair[1] =
                            json!(pair[1].as_u64().ok_or_else(Fault::protocol)? + offset as u64);
                    }
                }
                "array" => {
                    for child in node.value.as_array_mut().ok_or_else(Fault::protocol)? {
                        *child = json!(child.as_u64().ok_or_else(Fault::protocol)? + offset as u64);
                    }
                }
                _ => {}
            }
            self.nodes.push(node);
        }
        Ok(offset)
    }
    pub fn subtree(&self, root: usize) -> Result<Self> {
        let mut nodes = vec![];
        let mut pending = vec![(None, 0, root)];
        while let Some((parent, slot, old)) = pending.pop() {
            let id = nodes.len();
            if let Some((parent_id, table)) = parent {
                let parent_node: &mut Node = &mut nodes[parent_id];
                if table {
                    parent_node.value[slot][1] = json!(id);
                } else {
                    parent_node.value[slot] = json!(id);
                }
            }
            let node = self.nodes.get(old).ok_or_else(Fault::protocol)?.clone();
            let table = node.kind == "table";
            let children = self.children(old)?;
            nodes.push(node);
            for (slot, child) in children.into_iter().enumerate().rev() {
                pending.push((Some((id, table)), slot, child));
            }
        }
        Ok(Self { root: 0, nodes })
    }
    pub fn exchange(&self, root: usize) -> Result<Value> {
        serde_json::to_value(self.subtree(root)?).map_err(|_| Fault::protocol())
    }
}
