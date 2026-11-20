//! In-process syntax and OS adapters. They never select, merge or publish settings.
use super::{execute, native_toml, values::Arena, Codec, Fault, Result, Scope};
use crate::{files, Context};
use serde_json::{json, Value};
use std::fs;
use std::os::fd::{AsRawFd, BorrowedFd};
use std::path::{Component, Path, PathBuf};

/// Trusted host inputs, supplied when assembling a host rather than by a browser.
/// OS directories are deliberately used instead of a bundled timezone catalogue.
#[derive(Clone, Debug)]
pub struct NativeOptions {
    pub package_root: Option<PathBuf>,
    pub original_data_dir: Option<PathBuf>,
    pub timezone_roots: Vec<PathBuf>,
}
impl Default for NativeOptions {
    fn default() -> Self {
        Self {
            package_root: std::env::current_exe()
                .ok()
                .and_then(|path| fs::canonicalize(path).ok())
                .and_then(|path| path.parent().map(ToOwned::to_owned)),
            original_data_dir: None,
            timezone_roots: [
                "/usr/share/zoneinfo",
                "/usr/lib/zoneinfo",
                "/usr/share/lib/zoneinfo",
                "/etc/zoneinfo",
            ]
            .into_iter()
            .map(PathBuf::from)
            .collect(),
        }
    }
}

/// Execute with ordinary JSON arguments, retaining all settings transaction rules.
/// The caller owns the operations lock through the returned acknowledgement and
/// performs common-save readback after releasing it; terminal save reads back here.
pub fn native_call(
    operation: &str,
    context: &Context,
    default_zone: &str,
    arguments: Value,
    lease: Option<BorrowedFd<'_>>,
) -> Result<Value> {
    native_call_with_options(
        operation,
        context,
        default_zone,
        arguments,
        lease,
        &NativeOptions::default(),
    )
}

pub fn native_call_with_options(
    operation: &str,
    context: &Context,
    default_zone: &str,
    arguments: Value,
    lease: Option<BorrowedFd<'_>>,
    options: &NativeOptions,
) -> Result<Value> {
    native_call_tagged(
        operation,
        context,
        default_zone,
        Arena::from_json(arguments)?.exchange(0)?,
        lease,
        options,
    )
}

/// Lossless entrypoint for internal callers carrying values JSON cannot express,
/// including nonfinite floats and invalid surrogate application input.
pub fn native_call_tagged(
    operation: &str,
    context: &Context,
    default_zone: &str,
    arguments: Value,
    lease: Option<BorrowedFd<'_>>,
    options: &NativeOptions,
) -> Result<Value> {
    context.validate().map_err(Fault::from)?;
    let invalid_absolute =
        |path: &Path| !path.is_absolute() || path.as_os_str().as_encoded_bytes().contains(&0);
    for path in options.package_root.iter().chain(&options.timezone_roots) {
        if invalid_absolute(path) || path.components().any(|p| matches!(p, Component::ParentDir)) {
            return Err(Fault::protocol());
        }
    }
    // The host path retains the caller's spelling for the final symlink check.
    // Context validation above still requires the resolved data directory.
    if options
        .original_data_dir
        .as_deref()
        .is_some_and(invalid_absolute)
    {
        return Err(Fault::protocol());
    }
    let scope = Scope {
        context: context.clone(),
        default_zone: Arena::from_json(json!(default_zone))?,
        host_package_root: options.package_root.clone(),
        host_data_dir: Some(
            options
                .original_data_dir
                .as_deref()
                .map(|path| path.components().collect())
                .unwrap_or_else(|| context.data_dir.clone()),
        ),
    };
    let id = if operation.ends_with(".save") {
        files::random_id().map_err(Fault::from)?
    } else {
        "native-read".into()
    };
    let mut codec = NativeCodec { options };
    execute(
        &scope,
        operation,
        arguments,
        lease.map(|fd| fd.as_raw_fd()),
        &id,
        &mut codec,
    )
    .map(|(value, _)| value)
}

/// For schema-constrained JSON stores. Unsupported scalar conversions fail
/// explicitly; common settings uses the lossless Arena instead of this helper.
pub fn decode_toml_document(text: &str) -> Result<Value> {
    json_document(&native_toml::decode(text)?, Err)
}

/// Keep invalid scalar positions for schema checks. TOML has no null value,
/// so a present null marks a value that the caller must reject before writing.
pub(crate) fn decode_toml_for_validation(text: &str) -> Result<Value> {
    json_document(&native_toml::decode(text)?, |_| Ok(Value::Null))
}

/// Lossless syntax-only decode for selecting fields in external TOML documents
/// whose unrelated values can include dates or arbitrary-precision integers.
pub fn decode_toml_exchange(text: &str) -> Result<Value> {
    native_toml::decode(text)?.exchange(0)
}

/// Validate the document's TOML syntax while reading only its integer version.
pub(crate) fn toml_schema_version(text: &str) -> Result<Option<i64>> {
    let arena = native_toml::decode(text)?;
    Ok(arena
        .get(0, "schema_version")
        .and_then(|id| arena.scalar(id).as_i64()))
}

pub fn encode_toml_document(document: Value) -> Result<String> {
    native_toml::encode(&Arena::from_json(document)?)
}

fn json_document(arena: &Arena, unsupported: fn(Fault) -> Result<Value>) -> Result<Value> {
    let exchange = arena.exchange(0)?;
    let nodes = exchange["nodes"].as_array().ok_or_else(Fault::protocol)?;
    let mut values = vec![Value::Null; nodes.len()];
    for id in (0..nodes.len()).rev() {
        values[id] = match arena.kind(id) {
            "table" => {
                let mut table = serde_json::Map::new();
                for (key, child) in arena.entries(id)? {
                    table.insert(key, std::mem::take(&mut values[child]));
                }
                Value::Object(table)
            }
            "array" => Value::Array(
                arena
                    .children(id)?
                    .into_iter()
                    .map(|child| std::mem::take(&mut values[child]))
                    .collect(),
            ),
            "string" | "boolean" => arena.value(id).clone(),
            "integer" => {
                let text = arena.value(id).as_str().ok_or_else(Fault::protocol)?;
                text.parse::<i64>()
                    .map(Value::from)
                    .or_else(|_| text.parse::<u64>().map(Value::from))
                    .or_else(|_| unsupported(syntax_fault("value")))?
            }
            "float" => serde_json::Number::from_f64(float_value(
                arena.value(id).as_str().ok_or_else(Fault::protocol)?,
            )?)
            .map(Value::Number)
            .map_or_else(|| unsupported(syntax_fault("value")), Ok)?,
            _ => unsupported(syntax_fault("type"))?,
        };
    }
    Ok(std::mem::take(&mut values[0]))
}

struct NativeCodec<'a> {
    options: &'a NativeOptions,
}
impl Codec for NativeCodec<'_> {
    fn call(&mut self, operation: &str, value: Value) -> Result<Value> {
        match operation {
            "toml.decode" => {
                let text = value.as_str().ok_or_else(Fault::protocol)?;
                let arena = if text.is_empty() {
                    Arena::from_json(json!({"schema_version":1}))?
                } else {
                    native_toml::decode(text)?
                };
                arena.exchange(0)
            }
            "toml.encode" => Ok(json!(native_toml::encode(&Arena::parse(value)?)?)),
            "timezone.valid" => {
                let arena = Arena::parse(value)?;
                let name = input_string(&arena, 0)?;
                Ok(json!(name
                    .as_deref()
                    .is_some_and(|name| self.zone_valid(name))))
            }
            "json.measure" => Ok(json!(json_size(&Arena::parse(value)?)?)),
            _ => Err(Fault::protocol()),
        }
    }
    fn cancelled(&self) -> bool {
        false
    }
}
impl NativeCodec<'_> {
    fn zone_valid(&self, name: &str) -> bool {
        // Match ZoneInfo's normalized relative-key checks, including aliases.
        if name.is_empty()
            || name.starts_with('/')
            || name.contains('\0')
            || name
                .split('/')
                .any(|part| part.is_empty() || part == "." || part == "..")
        {
            return false;
        }
        for root in &self.options.timezone_roots {
            if let Ok(bytes) = fs::read(root.join(name)) {
                return jiff::tz::TimeZone::tzif(name, &bytes).is_ok();
            }
        }
        false
    }
}

pub(super) fn syntax_fault(code: &str) -> Fault {
    let mut fault = Fault::new("io", code, "설정 문법 변환을 완료하지 못했습니다.");
    fault.commit = "not-published".into();
    fault
}

/// CPython float.hex(), including the sign bit of zero and NaN.
pub(super) fn float_hex(value: f64) -> String {
    let sign = if value.is_sign_negative() { "-" } else { "" };
    if value.is_nan() {
        return format!("{sign}nan");
    }
    if value.is_infinite() {
        return format!("{sign}inf");
    }
    if value == 0.0 {
        return format!("{sign}0x0.0p+0");
    }
    let bits = value.to_bits();
    let exponent = ((bits >> 52) & 0x7ff) as i32;
    let fraction = bits & ((1u64 << 52) - 1);
    let (leading, power) = if exponent == 0 {
        (0, -1022)
    } else {
        (1, exponent - 1023)
    };
    format!("{sign}0x{leading}.{fraction:013x}p{power:+}")
}

pub(super) fn float_value(text: &str) -> Result<f64> {
    match text {
        "inf" => return Ok(f64::INFINITY),
        "-inf" => return Ok(f64::NEG_INFINITY),
        "nan" => return Ok(f64::NAN.copysign(1.0)),
        "-nan" => return Ok(f64::NAN.copysign(-1.0)),
        _ => {}
    }
    let (negative, text) = text.strip_prefix('-').map_or((false, text), |v| (true, v));
    let text = text.strip_prefix("0x").ok_or_else(Fault::protocol)?;
    let (mantissa, exponent) = text.split_once('p').ok_or_else(Fault::protocol)?;
    let exponent: i32 = exponent.parse().map_err(|_| Fault::protocol())?;
    let (leading, fraction) = mantissa.split_once('.').ok_or_else(Fault::protocol)?;
    let sign = (negative as u64) << 63;
    if leading == "0" && fraction == "0" && exponent == 0 {
        return Ok(f64::from_bits(sign));
    }
    if fraction.len() != 13 {
        return Err(Fault::protocol());
    }
    let fraction = u64::from_str_radix(fraction, 16).map_err(|_| Fault::protocol())?;
    let bits = match leading {
        "0" if exponent == -1022 => fraction,
        "1" if (-1022..=1023).contains(&exponent) => (((exponent + 1023) as u64) << 52) | fraction,
        _ => return Err(Fault::protocol()),
    };
    Ok(f64::from_bits(sign | bits))
}

/// Python repr uses the same shortest round-trip digits, with signed, padded
/// scientific exponents. Debug formatting also keeps integral floats as floats.
pub(super) fn float_text(value: f64) -> String {
    if value.is_nan() {
        return "nan".into();
    }
    if value.is_infinite() {
        return if value.is_sign_negative() {
            "-inf"
        } else {
            "inf"
        }
        .into();
    }
    let text = format!("{value:?}");
    match text.split_once('e') {
        Some((mantissa, exponent)) => {
            let exponent: i32 = exponent.parse().expect("Rust float exponent");
            format!("{mantissa}e{exponent:+03}")
        }
        None => text,
    }
}

pub(super) fn quote(text: &str) -> Result<String> {
    serde_json::to_string(text).map_err(|_| Fault::protocol())
}

fn input_string(arena: &Arena, id: usize) -> Result<Option<String>> {
    match arena.kind(id) {
        "string" => Ok(arena.text(id).map(ToOwned::to_owned)),
        "surrogate-string" => {
            let mut text = String::new();
            for point in arena.value(id).as_array().ok_or_else(Fault::protocol)? {
                let point = point.as_u64().ok_or_else(Fault::protocol)? as u32;
                let Some(ch) = char::from_u32(point) else {
                    return Ok(None);
                };
                text.push(ch);
            }
            Ok(Some(text))
        }
        _ => Ok(None),
    }
}

fn json_size(arena: &Arena) -> Result<usize> {
    let mut count = 0usize;
    let mut pending = vec![0];
    let mut invalid_unicode = false;
    while let Some(id) = pending.pop() {
        count += match arena.kind(id) {
            "table" => {
                let entries = arena.entries(id)?;
                let mut bytes = 2 + entries.len().saturating_sub(1);
                for (key, child) in entries.into_iter().rev() {
                    bytes += quote(&key)?.len() + 1;
                    pending.push(child);
                }
                bytes
            }
            "array" => {
                let children = arena.children(id)?;
                let bytes = 2 + children.len().saturating_sub(1);
                pending.extend(children.into_iter().rev());
                bytes
            }
            "string" => quote(arena.text(id).unwrap())?.len(),
            "boolean" => {
                if arena.value(id) == true {
                    4
                } else {
                    5
                }
            }
            "integer" => {
                let text = arena.value(id).as_str().ok_or_else(Fault::protocol)?;
                decimal_limit(text)?;
                text.len()
            }
            "float" => {
                let value = float_value(arena.value(id).as_str().ok_or_else(Fault::protocol)?)?;
                if value.is_nan() {
                    3
                } else if value.is_infinite() {
                    if value.is_sign_negative() {
                        9
                    } else {
                        8
                    }
                } else {
                    float_text(value).len()
                }
            }
            "null" => 4,
            "surrogate-string" => {
                if let Some(text) = input_string(arena, id)? {
                    quote(&text)?.len()
                } else {
                    // json.dumps first constructs a Python string; UTF-8
                    // encoding happens only after every value serialized.
                    // A later unsupported value therefore still fails first.
                    invalid_unicode = true;
                    0
                }
            }
            _ => return Err(syntax_fault("type")),
        };
    }
    if invalid_unicode {
        Err(syntax_fault("unicode"))
    } else {
        Ok(count)
    }
}

pub(super) fn decimal_limit(text: &str) -> Result<()> {
    // The frozen Python 3.11 baseline's decimal conversion safety limit. Hex,
    // octal and binary reads remain arbitrary precision; refusal is at encode.
    if text.trim_start_matches('-').len() > 4300 {
        Err(syntax_fault("value"))
    } else {
        Ok(())
    }
}
