//! Python Random's integer seed, MT19937 bits, and rejection-sampled shuffle.
//! Louvain's deterministic contract uses this sequence across each level.
use num_bigint::BigInt;
use std::str::FromStr;
pub(super) struct PythonRandom {
    state: [u32; 624],
    position: usize,
}
impl PythonRandom {
    pub(super) fn new(seed: &str) -> Self {
        let (_, mut keys) = BigInt::from_str(seed)
            .expect("validated integer seed")
            .to_u32_digits();
        if keys.is_empty() {
            keys.push(0);
        }
        let mut result = Self {
            state: [0; 624],
            position: 624,
        };
        result.state[0] = 19650218;
        for i in 1..624 {
            result.state[i] = 1812433253u32
                .wrapping_mul(result.state[i - 1] ^ (result.state[i - 1] >> 30))
                .wrapping_add(i as u32);
        }
        let (mut i, mut j) = (1, 0);
        for _ in 0..624.max(keys.len()) {
            result.state[i] = (result.state[i]
                ^ ((result.state[i - 1] ^ (result.state[i - 1] >> 30)).wrapping_mul(1664525)))
            .wrapping_add(keys[j])
            .wrapping_add(j as u32);
            i += 1;
            j += 1;
            if i >= 624 {
                result.state[0] = result.state[623];
                i = 1;
            }
            if j >= keys.len() {
                j = 0;
            }
        }
        for _ in 0..623 {
            result.state[i] = (result.state[i]
                ^ ((result.state[i - 1] ^ (result.state[i - 1] >> 30)).wrapping_mul(1566083941)))
            .wrapping_sub(i as u32);
            i += 1;
            if i >= 624 {
                result.state[0] = result.state[623];
                i = 1;
            }
        }
        result.state[0] = 0x80000000;
        result
    }
    fn next(&mut self) -> u32 {
        if self.position >= 624 {
            for i in 0..624 {
                let y = (self.state[i] & 0x80000000) | (self.state[(i + 1) % 624] & 0x7fffffff);
                self.state[i] = self.state[(i + 397) % 624]
                    ^ (y >> 1)
                    ^ if y & 1 == 1 { 0x9908b0df } else { 0 };
            }
            self.position = 0;
        }
        let mut y = self.state[self.position];
        self.position += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c5680;
        y ^= (y << 15) & 0xefc60000;
        y ^= y >> 18;
        y
    }
    fn bits(&mut self, bits: u32) -> u64 {
        if bits <= 32 {
            u64::from(self.next() >> (32 - bits))
        } else {
            u64::from(self.next()) | (u64::from(self.next() >> (64 - bits)) << 32)
        }
    }
    fn below(&mut self, number: usize) -> usize {
        let bits = usize::BITS - number.leading_zeros();
        loop {
            let value = self.bits(bits) as usize;
            if value < number {
                return value;
            }
        }
    }
    pub(super) fn shuffle<T>(&mut self, items: &mut [T]) {
        for i in (1..items.len()).rev() {
            let j = self.below(i + 1);
            items.swap(i, j);
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn frozen_python_integer_shuffles() {
        let mut random = PythonRandom::new("0");
        let mut first = (0..20).collect::<Vec<_>>();
        random.shuffle(&mut first);
        assert_eq!(
            first,
            vec![10, 18, 16, 14, 0, 17, 11, 2, 3, 9, 5, 7, 4, 19, 6, 15, 8, 1, 13, 12]
        );
        let mut second = (0..10).collect::<Vec<_>>();
        random.shuffle(&mut second);
        assert_eq!(second, vec![7, 0, 9, 3, 2, 5, 6, 8, 1, 4]);
    }
}
