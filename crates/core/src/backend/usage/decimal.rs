//! Decimal coefficients with Python's default 28-significant-digit context.
//!
//! Frozen Usage amounts are decimal text, and percentage/projection division
//! can require more than 28 fractional places. A fixed-scale decimal changes
//! those values. Each arithmetic operation here rounds half even; formatting
//! and the history labels request their own explicit quantization.
use num_bigint::{BigInt, Sign};
use rust_decimal::RoundingStrategy;
use std::{cmp::Ordering, fmt, str::FromStr};

#[derive(Clone, Debug, Eq)]
pub(crate) struct Decimal {
    coefficient: BigInt,
    exponent: i32,
}
const PRECISION: usize = 28;
const MAX_EXPONENT: i32 = 999_999;
fn power(exponent: u32) -> BigInt {
    BigInt::from(10).pow(exponent)
}
fn digits(value: &BigInt) -> usize {
    value.to_str_radix(10).trim_start_matches('-').len()
}
fn absolute(value: &BigInt) -> BigInt {
    if value.sign() == Sign::Minus {
        -value
    } else {
        value.clone()
    }
}
fn quotient(numerator: BigInt, denominator: BigInt, strategy: RoundingStrategy) -> BigInt {
    let negative = (numerator.sign() == Sign::Minus) != (denominator.sign() == Sign::Minus);
    let numerator = absolute(&numerator);
    let denominator = absolute(&denominator);
    let mut result = &numerator / &denominator;
    let remainder = numerator % &denominator;
    let compare = (&remainder * 2u8).cmp(&denominator);
    let odd = (&result % 2u8) != BigInt::from(0);
    if compare == Ordering::Greater
        || (compare == Ordering::Equal
            && (strategy == RoundingStrategy::MidpointAwayFromZero || odd))
    {
        result += 1;
    }
    if negative {
        -result
    } else {
        result
    }
}
impl Default for Decimal {
    fn default() -> Self {
        Self::zero()
    }
}
impl Decimal {
    pub(crate) fn zero() -> Self {
        Self::from(0)
    }
    pub(super) fn one() -> Self {
        Self::from(1)
    }
    pub(super) fn ten() -> Self {
        Self::from(10)
    }
    pub(crate) fn new(coefficient: i64, scale: u32) -> Self {
        Self {
            coefficient: coefficient.into(),
            exponent: -(scale as i32),
        }
    }
    pub(crate) fn is_zero(&self) -> bool {
        self.coefficient == BigInt::from(0)
    }
    fn checked(coefficient: BigInt, exponent: i32) -> Option<Self> {
        (-MAX_EXPONENT..=MAX_EXPONENT)
            .contains(&exponent)
            .then_some(Self {
                coefficient,
                exponent,
            })
    }
    fn context(coefficient: BigInt, exponent: i32) -> Option<Self> {
        // Every magnitude representable in 93 bits fits in 28 decimal digits.
        if coefficient.bits() <= 93 {
            return Self::checked(coefficient, exponent);
        }
        let length = digits(&coefficient);
        if length <= PRECISION {
            return Self::checked(coefficient, exponent);
        }
        let shift = (length - PRECISION) as u32;
        let coefficient = quotient(
            coefficient,
            power(shift),
            RoundingStrategy::MidpointNearestEven,
        );
        // Rounding a row of nines carries a new digit into the exponent.
        if digits(&coefficient) > PRECISION {
            Self::checked(coefficient / 10, exponent.checked_add(shift as i32 + 1)?)
        } else {
            Self::checked(coefficient, exponent.checked_add(shift as i32)?)
        }
    }
    pub(crate) fn checked_add(self, other: Self) -> Option<Self> {
        let exponent = self.exponent.min(other.exponent);
        let coefficient = match self.exponent.cmp(&other.exponent) {
            Ordering::Less => {
                self.coefficient + other.coefficient * power((other.exponent - exponent) as u32)
            }
            Ordering::Equal => self.coefficient + other.coefficient,
            Ordering::Greater => {
                self.coefficient * power((self.exponent - exponent) as u32) + other.coefficient
            }
        };
        Self::context(coefficient, exponent)
    }
    pub(super) fn checked_mul(self, other: Self) -> Option<Self> {
        Self::context(
            self.coefficient * other.coefficient,
            self.exponent.checked_add(other.exponent)?,
        )
    }
    pub(super) fn checked_div(self, other: Self) -> Option<Self> {
        if other.is_zero() {
            return None;
        }
        if self.is_zero() {
            return Some(Self::zero());
        }
        let numerator = absolute(&self.coefficient);
        let denominator = absolute(&other.coefficient);
        let difference = digits(&numerator) as i32 - digits(&denominator) as i32;
        let less = if difference >= 0 {
            numerator < denominator * power(difference as u32)
        } else {
            numerator * power((-difference) as u32) < denominator
        };
        let magnitude = difference - i32::from(less);
        let shift = magnitude - (PRECISION as i32 - 1);
        let (numerator, denominator) = if shift >= 0 {
            (self.coefficient, other.coefficient * power(shift as u32))
        } else {
            (self.coefficient * power((-shift) as u32), other.coefficient)
        };
        let coefficient = quotient(
            numerator,
            denominator,
            RoundingStrategy::MidpointNearestEven,
        );
        Self::context(
            coefficient,
            self.exponent
                .checked_sub(other.exponent)?
                .checked_add(shift)?,
        )
    }
    fn quantized(&self, exponent: i32, strategy: RoundingStrategy) -> Self {
        let difference = self.exponent - exponent;
        let coefficient = if difference >= 0 {
            &self.coefficient * power(difference as u32)
        } else {
            quotient(
                self.coefficient.clone(),
                power((-difference) as u32),
                strategy,
            )
        };
        Self {
            coefficient,
            exponent,
        }
    }
    pub(super) fn round_dp_with_strategy(&self, places: u32, strategy: RoundingStrategy) -> Self {
        self.quantized(-(places as i32), strategy)
    }
    pub(super) fn trunc(&self) -> Self {
        if self.exponent >= 0 {
            return self.clone();
        }
        Self {
            coefficient: &self.coefficient / power((-self.exponent) as u32),
            exponent: 0,
        }
    }
    fn plain(&self) -> String {
        let negative = self.coefficient.sign() == Sign::Minus;
        let digits = absolute(&self.coefficient).to_string();
        let mut result = if self.exponent >= 0 {
            format!("{digits}{}", "0".repeat(self.exponent as usize))
        } else {
            let point = digits.len() as i32 + self.exponent;
            if point > 0 {
                format!(
                    "{}.{}",
                    &digits[..point as usize],
                    &digits[point as usize..]
                )
            } else {
                format!("0.{}{digits}", "0".repeat((-point) as usize))
            }
        };
        if negative {
            result.insert(0, '-');
        }
        result
    }
}
impl From<i32> for Decimal {
    fn from(value: i32) -> Self {
        Self {
            coefficient: value.into(),
            exponent: 0,
        }
    }
}
impl From<i64> for Decimal {
    fn from(value: i64) -> Self {
        Self {
            coefficient: value.into(),
            exponent: 0,
        }
    }
}
impl FromStr for Decimal {
    type Err = ();
    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let value = value.trim();
        let (mantissa, exponent) = if let Some(index) = value.find(['e', 'E']) {
            (
                &value[..index],
                value[index + 1..].parse::<i32>().map_err(|_| ())?,
            )
        } else {
            (value, 0)
        };
        let negative = mantissa.starts_with('-');
        let mantissa = mantissa.strip_prefix(['+', '-']).unwrap_or(mantissa);
        let (whole, fraction) = mantissa.split_once('.').unwrap_or((mantissa, ""));
        if (whole.is_empty() && fraction.is_empty())
            || !whole
                .bytes()
                .chain(fraction.bytes())
                .all(|v| v.is_ascii_digit())
        {
            return Err(());
        }
        let mut coefficient = BigInt::from_str(&format!("{whole}{fraction}")).map_err(|_| ())?;
        if negative {
            coefficient = -coefficient;
        }
        Self::checked(
            coefficient,
            exponent
                .checked_sub(fraction.len().try_into().map_err(|_| ())?)
                .ok_or(())?,
        )
        .ok_or(())
    }
}
impl fmt::Display for Decimal {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let text = if let Some(precision) = formatter.precision() {
            self.quantized(-(precision as i32), RoundingStrategy::MidpointNearestEven)
                .plain()
        } else {
            self.plain()
        };
        formatter.write_str(&text)
    }
}
impl PartialEq for Decimal {
    fn eq(&self, other: &Self) -> bool {
        self.cmp(other) == Ordering::Equal
    }
}
impl PartialOrd for Decimal {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for Decimal {
    fn cmp(&self, other: &Self) -> Ordering {
        let exponent = self.exponent.min(other.exponent);
        (&self.coefficient * power((self.exponent - exponent) as u32))
            .cmp(&(&other.coefficient * power((other.exponent - exponent) as u32)))
    }
}
