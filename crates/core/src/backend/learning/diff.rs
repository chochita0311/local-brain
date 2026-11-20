//! The line matching and grouping policy used by Python difflib.unified_diff.
use crate::backend::unicode::splitlines_keepends;
use std::collections::HashMap;
#[derive(Clone, Copy)]
struct Opcode {
    kind: u8,
    a: usize,
    ae: usize,
    b: usize,
    be: usize,
}

fn matching(a: &[&str], b: &[&str]) -> Vec<(usize, usize, usize)> {
    let mut positions: HashMap<&str, Vec<usize>> = HashMap::new();
    for (index, line) in b.iter().enumerate() {
        positions.entry(line).or_default().push(index);
    }
    if b.len() >= 200 {
        let threshold = b.len() / 100 + 1;
        positions.retain(|_, indices| indices.len() <= threshold);
    }
    let mut queue = vec![(0, a.len(), 0, b.len())];
    let mut blocks = Vec::new();
    while let Some((alo, ahi, blo, bhi)) = queue.pop() {
        let (mut best_i, mut best_j, mut best_size) = (alo, blo, 0);
        let mut previous = HashMap::<usize, usize>::new();
        for (i, &line) in a.iter().enumerate().take(ahi).skip(alo) {
            let mut current = HashMap::new();
            if let Some(indices) = positions.get(line) {
                for j in indices.iter().copied().filter(|j| *j >= blo && *j < bhi) {
                    let size = 1 + j
                        .checked_sub(1)
                        .and_then(|j| previous.get(&j))
                        .copied()
                        .unwrap_or(0);
                    current.insert(j, size);
                    if size > best_size {
                        best_i = i + 1 - size;
                        best_j = j + 1 - size;
                        best_size = size;
                    }
                }
            }
            previous = current;
        }
        while best_i > alo && best_j > blo && a[best_i - 1] == b[best_j - 1] {
            best_i -= 1;
            best_j -= 1;
            best_size += 1;
        }
        while best_i + best_size < ahi
            && best_j + best_size < bhi
            && a[best_i + best_size] == b[best_j + best_size]
        {
            best_size += 1;
        }
        if best_size > 0 {
            blocks.push((best_i, best_j, best_size));
            if alo < best_i && blo < best_j {
                queue.push((alo, best_i, blo, best_j));
            }
            if best_i + best_size < ahi && best_j + best_size < bhi {
                queue.push((best_i + best_size, ahi, best_j + best_size, bhi));
            }
        }
    }
    blocks.sort();
    let mut merged: Vec<(usize, usize, usize)> = Vec::new();
    for (i, j, size) in blocks {
        if let Some((ai, bj, last)) = merged.last_mut() {
            if *ai + *last == i && *bj + *last == j {
                *last += size;
                continue;
            }
        }
        merged.push((i, j, size));
    }
    merged.push((a.len(), b.len(), 0));
    merged
}
fn opcodes(a: &[&str], b: &[&str]) -> Vec<Opcode> {
    let (mut i, mut j) = (0, 0);
    let mut result = Vec::new();
    for (ai, bj, size) in matching(a, b) {
        let kind = if i < ai && j < bj {
            b'r'
        } else if i < ai {
            b'd'
        } else if j < bj {
            b'i'
        } else {
            0
        };
        if kind != 0 {
            result.push(Opcode {
                kind,
                a: i,
                ae: ai,
                b: j,
                be: bj,
            });
        }
        if size > 0 {
            result.push(Opcode {
                kind: b'e',
                a: ai,
                ae: ai + size,
                b: bj,
                be: bj + size,
            });
        }
        i = ai + size;
        j = bj + size;
    }
    result
}
fn groups(mut codes: Vec<Opcode>) -> Vec<Vec<Opcode>> {
    if codes.is_empty() {
        return Vec::new();
    }
    if codes[0].kind == b'e' {
        let first = &mut codes[0];
        first.a = first.a.max(first.ae.saturating_sub(3));
        first.b = first.b.max(first.be.saturating_sub(3));
    }
    if codes.last().unwrap().kind == b'e' {
        let last = codes.last_mut().unwrap();
        last.ae = last.ae.min(last.a + 3);
        last.be = last.be.min(last.b + 3);
    }
    let mut result = Vec::new();
    let mut group = Vec::new();
    for mut code in codes {
        if code.kind == b'e' && code.ae - code.a > 6 {
            group.push(Opcode {
                ae: code.a + 3,
                be: code.b + 3,
                ..code
            });
            result.push(std::mem::take(&mut group));
            code.a = code.ae - 3;
            code.b = code.be - 3;
        }
        group.push(code);
    }
    if !(group.is_empty() || group.len() == 1 && group[0].kind == b'e') {
        result.push(group);
    }
    result
}
fn range(start: usize, end: usize) -> String {
    let count = end - start;
    match count {
        0 => format!("{start},0"),
        1 => (start + 1).to_string(),
        _ => format!("{},{}", start + 1, count),
    }
}
fn append_line(result: &mut String, prefix: char, line: &str) {
    result.push(prefix);
    result.push_str(line);
    if !line.ends_with('\n') {
        result.push_str("\n\\ No newline at end of file\n");
    }
}
pub(super) fn unified_diff(before: &str, after: &str, path: &str) -> String {
    let a = splitlines_keepends(before);
    let b = splitlines_keepends(after);
    let groups = groups(opcodes(&a, &b));
    if groups.is_empty() {
        return String::new();
    }
    let mut result = format!("--- a/{path}\n+++ b/{path}\n");
    for group in groups {
        let first = group.first().unwrap();
        let last = group.last().unwrap();
        result.push_str(&format!(
            "@@ -{} +{} @@\n",
            range(first.a, last.ae),
            range(first.b, last.be)
        ));
        for code in group {
            match code.kind {
                b'e' => {
                    for line in &a[code.a..code.ae] {
                        append_line(&mut result, ' ', line);
                    }
                }
                b'd' => {
                    for line in &a[code.a..code.ae] {
                        append_line(&mut result, '-', line);
                    }
                }
                b'i' => {
                    for line in &b[code.b..code.be] {
                        append_line(&mut result, '+', line);
                    }
                }
                b'r' => {
                    for line in &a[code.a..code.ae] {
                        append_line(&mut result, '-', line);
                    }
                    for line in &b[code.b..code.be] {
                        append_line(&mut result, '+', line);
                    }
                }
                _ => {}
            }
        }
    }
    result
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn diff_preserves_no_newline_and_line_ranges() {
        assert_eq!(unified_diff("one\ntwo","one\nthree","x.rs"),"--- a/x.rs\n+++ b/x.rs\n@@ -1,2 +1,2 @@\n one\n-two\n\\ No newline at end of file\n+three\n\\ No newline at end of file\n");
        assert_eq!(
            unified_diff("", "x\n", "x"),
            "--- a/x\n+++ b/x\n@@ -0,0 +1 @@\n+x\n"
        );
    }
}
