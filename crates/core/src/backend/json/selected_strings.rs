//! Validate the selected serialization view without rebuilding JSON. In
//! particular, serde_json's Value serializer would reinterpret literal private
//! number-tag objects and reject our deliberately retained nonfinite numbers.
use crate::backend::{BackendError, Result};
use serde::{ser, Serialize};
use std::fmt;

#[derive(Debug)]
pub(super) enum Error {
    Surrogate,
    Serialization(String),
}
impl fmt::Display for Error {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Surrogate => {
                out.write_str("Selected source text contains an unpaired Unicode surrogate")
            }
            Self::Serialization(message) => out.write_str(message),
        }
    }
}
impl std::error::Error for Error {}
impl ser::Error for Error {
    fn custom<T: fmt::Display>(message: T) -> Self {
        Self::Serialization(message.to_string())
    }
}
pub(super) fn validate(value: &impl Serialize, marker: char) -> Result<()> {
    let escaped = if marker as u32 <= 0xffff {
        format!("\\u{:04x}", marker as u32)
    } else {
        format!("\\U{:08x}", marker as u32)
    };
    // Python repr uses \x for byte-sized nonprintable characters; a selected
    // container must not turn an opaque surrogate marker into visible text.
    let repr_escaped = if marker as u32 <= 255 {
        format!("\\x{:02x}", marker as u32)
    } else {
        escaped.clone()
    };
    value
        .serialize(Strings {
            marker,
            escaped: &escaped,
            repr_escaped: &repr_escaped,
        })
        .map_err(|error| {
            BackendError::invalid(
                match error {
                    Error::Surrogate => "source_unicode",
                    _ => "json",
                },
                error.to_string(),
            )
        })
}
#[derive(Clone, Copy)]
struct Strings<'a> {
    marker: char,
    escaped: &'a str,
    repr_escaped: &'a str,
}
type Checked = std::result::Result<(), Error>;
macro_rules! scalar {
    ($($method:ident($ty:ty)),* $(,)?) => {$(
        fn $method(self, _: $ty) -> Checked { Ok(()) }
    )*};
}
impl<'a> ser::Serializer for Strings<'a> {
    type Ok = ();
    type Error = Error;
    type SerializeSeq = Self;
    type SerializeTuple = Self;
    type SerializeTupleStruct = Self;
    type SerializeTupleVariant = Self;
    type SerializeMap = Self;
    type SerializeStruct = Self;
    type SerializeStructVariant = Self;
    scalar!(
        serialize_bool(bool),
        serialize_i8(i8),
        serialize_i16(i16),
        serialize_i32(i32),
        serialize_i64(i64),
        serialize_i128(i128),
        serialize_u8(u8),
        serialize_u16(u16),
        serialize_u32(u32),
        serialize_u64(u64),
        serialize_u128(u128),
        serialize_f32(f32),
        serialize_f64(f64),
        serialize_bytes(&[u8])
    );
    fn serialize_char(self, value: char) -> Checked {
        self.serialize_str(value.encode_utf8(&mut [0; 4]))
    }
    fn serialize_str(self, value: &str) -> Checked {
        if value.contains(self.marker)
            || value.contains(self.escaped)
            || value.contains(self.repr_escaped)
        {
            Err(Error::Surrogate)
        } else {
            Ok(())
        }
    }
    fn serialize_none(self) -> Checked {
        Ok(())
    }
    fn serialize_some<T: ?Sized + Serialize>(self, value: &T) -> Checked {
        value.serialize(self)
    }
    fn serialize_unit(self) -> Checked {
        Ok(())
    }
    fn serialize_unit_struct(self, _: &'static str) -> Checked {
        Ok(())
    }
    fn serialize_unit_variant(self, _: &'static str, _: u32, variant: &'static str) -> Checked {
        self.serialize_str(variant)
    }
    fn serialize_newtype_struct<T: ?Sized + Serialize>(
        self,
        _: &'static str,
        value: &T,
    ) -> Checked {
        value.serialize(self)
    }
    fn serialize_newtype_variant<T: ?Sized + Serialize>(
        self,
        _: &'static str,
        _: u32,
        variant: &'static str,
        value: &T,
    ) -> Checked {
        self.serialize_str(variant)?;
        value.serialize(self)
    }
    fn serialize_seq(self, _: Option<usize>) -> std::result::Result<Self, Error> {
        Ok(self)
    }
    fn serialize_tuple(self, _: usize) -> std::result::Result<Self, Error> {
        Ok(self)
    }
    fn serialize_tuple_struct(self, _: &'static str, _: usize) -> std::result::Result<Self, Error> {
        Ok(self)
    }
    fn serialize_tuple_variant(
        self,
        _: &'static str,
        _: u32,
        variant: &'static str,
        _: usize,
    ) -> std::result::Result<Self, Error> {
        self.serialize_str(variant)?;
        Ok(self)
    }
    fn serialize_map(self, _: Option<usize>) -> std::result::Result<Self, Error> {
        Ok(self)
    }
    fn serialize_struct(self, _: &'static str, _: usize) -> std::result::Result<Self, Error> {
        Ok(self)
    }
    fn serialize_struct_variant(
        self,
        _: &'static str,
        _: u32,
        variant: &'static str,
        _: usize,
    ) -> std::result::Result<Self, Error> {
        self.serialize_str(variant)?;
        Ok(self)
    }
}
macro_rules! sequence {
    ($($kind:ident::$method:ident),* $(,)?) => {$(
        impl ser::$kind for Strings<'_> {
            type Ok = (); type Error = Error;
            fn $method<T: ?Sized + Serialize>(&mut self, value: &T) -> Checked { value.serialize(*self) }
            fn end(self) -> Checked { Ok(()) }
        }
    )*};
}
sequence!(
    SerializeSeq::serialize_element,
    SerializeTuple::serialize_element,
    SerializeTupleStruct::serialize_field,
    SerializeTupleVariant::serialize_field
);
impl ser::SerializeMap for Strings<'_> {
    type Ok = ();
    type Error = Error;
    fn serialize_key<T: ?Sized + Serialize>(&mut self, value: &T) -> Checked {
        value.serialize(*self)
    }
    fn serialize_value<T: ?Sized + Serialize>(&mut self, value: &T) -> Checked {
        value.serialize(*self)
    }
    fn end(self) -> Checked {
        Ok(())
    }
}
macro_rules! structure {
    ($($kind:ident),* $(,)?) => {$(
        impl ser::$kind for Strings<'_> {
            type Ok = (); type Error = Error;
            fn serialize_field<T: ?Sized + Serialize>(&mut self, key: &'static str, value: &T) -> Checked {
                ser::Serializer::serialize_str(*self, key)?; value.serialize(*self)
            }
            fn end(self) -> Checked { Ok(()) }
        }
    )*};
}
structure!(SerializeStruct, SerializeStructVariant);
