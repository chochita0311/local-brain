//! CPython 3.11 HTMLParser data-run and html.unescape compatibility. The regex
//! grammar and public entity tables follow CPython3.11.15's PSF-licensed
//! html.parser/html.entities/html modules. See LICENSE-PSF.txt and the official
//! https://github.com/python/cpython/tree/v3.11.15/Lib/html sources.
use crate::backend::{
    unicode::{lowercase, python_space},
    BackendError, Result,
};
use fancy_regex::{Regex as Fancy, RegexBuilder};
use regex::Regex;
use std::{
    collections::{HashMap, HashSet},
    sync::LazyLock,
};
static ENTITIES: LazyLock<HashMap<String, String>> =
    LazyLock::new(|| serde_json::from_str(ENTITY_DATA).unwrap());
static INVALID_REFS: LazyLock<HashMap<u32, String>> =
    LazyLock::new(|| serde_json::from_str(INVALID_REF_DATA).unwrap());
static INVALID_POINTS: LazyLock<HashSet<u32>> =
    LazyLock::new(|| serde_json::from_str(INVALID_POINT_DATA).unwrap());
static CHARREF: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"&(#[0-9]+;?|#[xX][0-9a-fA-F]+;?|[^\t\n\f <&#;]{1,32};?)").unwrap()
});
fn compile(pattern: &str) -> Fancy {
    // Rust's verbose mode also ignores spaces inside character classes.
    // Python's verbose mode retains those class members.
    let mut normalized = String::new();
    let mut class = false;
    let mut escaped = false;
    for ch in pattern.chars() {
        if escaped {
            normalized.push(ch);
            escaped = false;
            continue;
        }
        if ch == '\\' {
            normalized.push(ch);
            escaped = true;
            continue;
        }
        if ch == '[' {
            class = true;
        } else if ch == ']' {
            class = false;
        }
        if class && ch == ' ' {
            normalized.push_str(r"\x20");
        } else {
            normalized.push(ch);
        }
    }
    RegexBuilder::new(&normalized)
        .backtrack_limit(usize::MAX)
        .build()
        .expect("frozen HTML grammar")
}
static TAG_END: LazyLock<Fancy> = LazyLock::new(|| compile(TAG_END_PATTERN));
static TAG: LazyLock<Fancy> = LazyLock::new(|| compile(TAG_PATTERN));
static ATTRIBUTE: LazyLock<Fancy> = LazyLock::new(|| compile(ATTRIBUTE_PATTERN));
fn match_at<'a>(pattern: &Fancy, text: &'a str, pos: usize) -> Option<fancy_regex::Match<'a>> {
    pattern
        .find_from_pos(text, pos)
        .expect("HTML parser matching")
        .filter(|m| m.start() == pos)
}
fn unescape(text: &str) -> Result<String> {
    if !text.contains('&') {
        return Ok(text.into());
    }
    let mut out = String::new();
    let mut pos = 0;
    for captures in CHARREF.captures_iter(text) {
        let whole = captures.get(0).unwrap();
        out.push_str(&text[pos..whole.start()]);
        let value = &captures[1];
        if let Some(digits) = value.strip_prefix('#') {
            let digits = digits.trim_end_matches(';');
            let (radix, digits) = if let Some(tail) = digits.strip_prefix(['x', 'X']) {
                (16, tail)
            } else {
                (10, digits)
            };
            if radix == 10 && digits.len() > 4300 {
                return Err(BackendError::invalid(
                    "source_scalar",
                    "HTML integer exceeds Python decimal conversion limit",
                ));
            }
            let point = u32::from_str_radix(digits, radix).ok();
            match point {
                Some(point) if INVALID_REFS.contains_key(&point) => {
                    out.push_str(&INVALID_REFS[&point])
                }
                Some(point) if (0xd800..=0xdfff).contains(&point) || point > 0x10ffff => {
                    out.push('\u{fffd}')
                }
                Some(point) if INVALID_POINTS.contains(&point) => {}
                Some(point) => out.push(char::from_u32(point).unwrap()),
                None => out.push('\u{fffd}'),
            }
        } else if let Some(value) = ENTITIES.get(value) {
            out.push_str(value);
        } else {
            let mut found = false;
            let ends = value
                .char_indices()
                .map(|(i, _)| i)
                .chain(std::iter::once(value.len()))
                .collect::<Vec<_>>();
            for end in ends.into_iter().rev().skip(1).filter(|i| *i >= 2) {
                if let Some(prefix) = ENTITIES.get(&value[..end]) {
                    out.push_str(prefix);
                    out.push_str(&value[end..]);
                    found = true;
                    break;
                }
            }
            if !found {
                out.push('&');
                out.push_str(value);
            }
        }
        pos = whole.end();
    }
    out.push_str(&text[pos..]);
    Ok(out)
}

/// `feed` leaves incomplete trailing constructs buffered; `close` finalizes
/// them using the source HTMLParser's distinct EOF behavior.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Finish {
    Feed,
    Close,
}

pub trait Visitor {
    fn start(&mut self, _tag: &str, _attributes: &[(String, Option<String>)]) -> Result<()> {
        Ok(())
    }
    fn end(&mut self, _tag: &str) -> Result<()> {
        Ok(())
    }
    fn data(&mut self, _text: &str) -> Result<()> {
        Ok(())
    }
    fn start_end(&mut self, tag: &str, attributes: &[(String, Option<String>)]) -> Result<()> {
        self.start(tag, attributes)?;
        self.end(tag)
    }
}
fn emit_data(visitor: &mut dyn Visitor, text: &str, escape: bool) -> Result<()> {
    if escape {
        visitor.data(&unescape(text)?)
    } else {
        visitor.data(text)
    }
}
fn close_raw(text: &str, start: usize, tag: &str) -> Option<usize> {
    let mut offset = start;
    while let Some(index) = text[offset..].find("</") {
        let pos = offset + index;
        let end = pos + 2 + tag.len();
        if text
            .get(pos + 2..end)
            .is_some_and(|s| s.eq_ignore_ascii_case(tag))
            && text
                .as_bytes()
                .get(end)
                .is_some_and(|c| b"\t\n\r\x0c />".contains(c))
        {
            return Some(pos);
        }
        offset = pos + 2;
    }
    None
}

/// Visit one complete input using default `HTMLParser(convert_charrefs=True,
/// scripting=False)` rules. Closing is explicit because Notes historically
/// calls feed only while normalized Atlassian HTML calls feed then close.
pub fn visit(value: &str, finish: Finish, visitor: &mut dyn Visitor) -> Result<()> {
    let close = finish == Finish::Close;
    let mut pos = 0;
    let mut raw: Option<(String, bool)> = None;
    while pos < value.len() {
        let next = if let Some((tag, _)) = &raw {
            if tag == "plaintext" {
                None
            } else {
                close_raw(value, pos, tag)
            }
        } else {
            value[pos..].find('<').map(|i| pos + i)
        };
        let Some(next) = next else {
            let tail = &value[pos..];
            if let Some((tag, escape)) = &raw {
                if close || tag == "plaintext" {
                    emit_data(visitor, tail, *escape)?;
                }
            } else {
                let last = tail
                    .char_indices()
                    .rev()
                    .take(34)
                    .find_map(|(i, c)| (c == '&').then_some(i));
                let incomplete =
                    last.is_some_and(|i| !tail[i..].chars().any(|c| "\t\n\r\u{c} ;".contains(c)));
                if close || !incomplete {
                    emit_data(visitor, tail, true)?;
                }
            }
            break;
        };
        if next > pos {
            emit_data(
                visitor,
                &value[pos..next],
                raw.as_ref().is_none_or(|(_, escape)| *escape),
            )?;
        }
        pos = next;
        let rest = &value[pos..];
        if rest.as_bytes().get(1).is_some_and(u8::is_ascii_alphabetic) {
            let start = pos + 1;
            let Some(end) = match_at(&TAG_END, value, start)
                .filter(|m| m.as_str().ends_with('>'))
                .map(|m| m.end())
            else {
                break;
            };
            let Some(tag_capture) = TAG
                .captures_from_pos(value, start)
                .expect("HTML tag grammar")
                .filter(|c| c.get(0).unwrap().start() == start)
            else {
                break;
            };
            let tag = lowercase(tag_capture.get(1).unwrap().as_str());
            let mut cursor = tag_capture.get(0).unwrap().end();
            let mut attributes = vec![];
            while cursor < end {
                let Some(attribute) = ATTRIBUTE
                    .captures_from_pos(value, cursor)
                    .expect("HTML attribute grammar")
                    .filter(|c| c.get(0).unwrap().start() == cursor)
                else {
                    break;
                };
                let next = attribute.get(0).unwrap().end();
                if next <= cursor {
                    break;
                }
                let name = lowercase(attribute.get(1).unwrap().as_str());
                let attr_value = if attribute.get(2).is_none_or(|m| m.as_str().is_empty()) {
                    None
                } else {
                    let text = attribute.get(3).unwrap().as_str();
                    let text = if text.len() >= 2
                        && ((text.starts_with('\'') && text.ends_with('\''))
                            || (text.starts_with('"') && text.ends_with('"')))
                    {
                        &text[1..text.len() - 1]
                    } else {
                        text
                    };
                    Some(if text.is_empty() {
                        String::new()
                    } else {
                        unescape(text)?
                    })
                };
                attributes.push((name, attr_value));
                cursor = next;
            }
            let suffix = value[cursor..end].trim_matches(python_space);
            if !matches!(suffix, ">" | "/>") {
                emit_data(visitor, &value[pos..end], false)?;
            } else if suffix == "/>" {
                visitor.start_end(&tag, &attributes)?;
            } else {
                visitor.start(&tag, &attributes)?;
                if RAW.contains(&tag.as_str()) || tag == "plaintext" {
                    raw = Some((tag, false));
                } else if RCDATA.contains(&tag.as_str()) {
                    raw = Some((tag, true));
                }
            }
            pos = end;
        } else if let Some(ending) = rest.strip_prefix("</") {
            let Some(gt) = ending.find('>').map(|i| pos + 2 + i + 1) else {
                if close && rest == "</" {
                    emit_data(visitor, "</", false)?;
                }
                break;
            };
            if rest.as_bytes().get(2).is_some_and(u8::is_ascii_alphabetic) {
                let Some(end) = match_at(&TAG_END, value, pos + 2)
                    .filter(|m| m.as_str().ends_with('>'))
                    .map(|m| m.end())
                else {
                    break;
                };
                let tag_capture = TAG
                    .captures_from_pos(value, pos + 2)
                    .expect("HTML end-tag grammar")
                    .filter(|c| c.get(0).unwrap().start() == pos + 2)
                    .expect("matched HTML end-tag name");
                visitor.end(&lowercase(tag_capture.get(1).unwrap().as_str()))?;
                pos = end;
                raw = None;
            } else {
                pos = gt;
            }
        } else if rest.starts_with("<!--") {
            let tail = &value[pos + 4..];
            let end = tail
                .find("-->")
                .map(|i| i + 3)
                .into_iter()
                .chain(tail.find("--!>").map(|i| i + 4))
                .min()
                .or_else(|| {
                    if tail.starts_with('>') {
                        Some(1)
                    } else if tail.starts_with("->") {
                        Some(2)
                    } else {
                        None
                    }
                });
            let Some(end) = end else {
                break;
            };
            pos += 4 + end;
        } else if let Some(data) = rest.strip_prefix("<![CDATA[") {
            let Some(end) = data.find("]]>") else {
                break;
            };
            pos += 9 + end + 3;
        } else if rest.starts_with("<!") || rest.starts_with("<?") {
            let Some(end) = rest[2..].find('>') else {
                break;
            };
            pos += 2 + end + 1;
        } else if pos + 1 < value.len() || close {
            emit_data(visitor, "<", false)?;
            pos += 1;
        } else {
            break;
        }
    }
    Ok(())
}

/// Notes' original data-run text facade, including its plain-input shortcut.
pub fn plaintext(value: &str) -> Result<String> {
    if !value.contains('<') || !value.contains('>') {
        return Ok(value.into());
    }
    struct Text(Vec<String>);
    impl Visitor for Text {
        fn data(&mut self, text: &str) -> Result<()> {
            let text = text.trim_matches(python_space);
            if !text.is_empty() {
                self.0.push(text.into());
            }
            Ok(())
        }
    }
    let mut text = Text(vec![]);
    visit(value, Finish::Feed, &mut text)?;
    Ok(text.0.join("\n"))
}

const TAG_END_PATTERN: &str = r####"(?x)
  [a-zA-Z][^\t\n\r\f />]*           # tag name
  [\t\n\r\f /]*                     # optional whitespace before attribute name
  (?:(?<=['"\t\n\r\f /])[^\t\n\r\f />][^\t\n\r\f /=>]*  # attribute name
    (?:[\t\n\r\f ]*=[\t\n\r\f ]*    # value indicator
      (?:'[^']*'                    # LITA-enclosed value
        |"[^"]*"                    # LIT-enclosed value
        |(?!['"])[^>\t\n\r\f ]*     # bare value
       )
     )?
    [\t\n\r\f /]*                   # possibly followed by a space
   )*
   >?
"####;

const TAG_PATTERN: &str = r####"(?x)([a-zA-Z][^\t\n\r\f />]*)(?:[\t\n\r\f ]|/(?!>))*"####;

const ATTRIBUTE_PATTERN: &str = r####"(?x)
  (
    (?<=['"\t\n\r\f /])[^\t\n\r\f />][^\t\n\r\f /=>]*  # attribute name
   )
  ([\t\n\r\f ]*=[\t\n\r\f ]*        # value indicator
    ('[^']*'                        # LITA-enclosed value
    |"[^"]*"                        # LIT-enclosed value
    |(?!['"])[^>\t\n\r\f ]*         # bare value
    )
   )?
  (?:[\t\n\r\f ]|/(?!>))*           # possibly followed by a space
"####;

const ENTITY_DATA: &str = r####"{"Aacute":"Á","aacute":"á","Aacute;":"Á","aacute;":"á","Abreve;":"Ă","abreve;":"ă","ac;":"∾","acd;":"∿","acE;":"∾̳","Acirc":"Â","acirc":"â","Acirc;":"Â","acirc;":"â","acute":"´","acute;":"´","Acy;":"А","acy;":"а","AElig":"Æ","aelig":"æ","AElig;":"Æ","aelig;":"æ","af;":"⁡","Afr;":"𝔄","afr;":"𝔞","Agrave":"À","agrave":"à","Agrave;":"À","agrave;":"à","alefsym;":"ℵ","aleph;":"ℵ","Alpha;":"Α","alpha;":"α","Amacr;":"Ā","amacr;":"ā","amalg;":"⨿","AMP":"&","amp":"&","AMP;":"&","amp;":"&","And;":"⩓","and;":"∧","andand;":"⩕","andd;":"⩜","andslope;":"⩘","andv;":"⩚","ang;":"∠","ange;":"⦤","angle;":"∠","angmsd;":"∡","angmsdaa;":"⦨","angmsdab;":"⦩","angmsdac;":"⦪","angmsdad;":"⦫","angmsdae;":"⦬","angmsdaf;":"⦭","angmsdag;":"⦮","angmsdah;":"⦯","angrt;":"∟","angrtvb;":"⊾","angrtvbd;":"⦝","angsph;":"∢","angst;":"Å","angzarr;":"⍼","Aogon;":"Ą","aogon;":"ą","Aopf;":"𝔸","aopf;":"𝕒","ap;":"≈","apacir;":"⩯","apE;":"⩰","ape;":"≊","apid;":"≋","apos;":"'","ApplyFunction;":"⁡","approx;":"≈","approxeq;":"≊","Aring":"Å","aring":"å","Aring;":"Å","aring;":"å","Ascr;":"𝒜","ascr;":"𝒶","Assign;":"≔","ast;":"*","asymp;":"≈","asympeq;":"≍","Atilde":"Ã","atilde":"ã","Atilde;":"Ã","atilde;":"ã","Auml":"Ä","auml":"ä","Auml;":"Ä","auml;":"ä","awconint;":"∳","awint;":"⨑","backcong;":"≌","backepsilon;":"϶","backprime;":"‵","backsim;":"∽","backsimeq;":"⋍","Backslash;":"∖","Barv;":"⫧","barvee;":"⊽","Barwed;":"⌆","barwed;":"⌅","barwedge;":"⌅","bbrk;":"⎵","bbrktbrk;":"⎶","bcong;":"≌","Bcy;":"Б","bcy;":"б","bdquo;":"„","becaus;":"∵","Because;":"∵","because;":"∵","bemptyv;":"⦰","bepsi;":"϶","bernou;":"ℬ","Bernoullis;":"ℬ","Beta;":"Β","beta;":"β","beth;":"ℶ","between;":"≬","Bfr;":"𝔅","bfr;":"𝔟","bigcap;":"⋂","bigcirc;":"◯","bigcup;":"⋃","bigodot;":"⨀","bigoplus;":"⨁","bigotimes;":"⨂","bigsqcup;":"⨆","bigstar;":"★","bigtriangledown;":"▽","bigtriangleup;":"△","biguplus;":"⨄","bigvee;":"⋁","bigwedge;":"⋀","bkarow;":"⤍","blacklozenge;":"⧫","blacksquare;":"▪","blacktriangle;":"▴","blacktriangledown;":"▾","blacktriangleleft;":"◂","blacktriangleright;":"▸","blank;":"␣","blk12;":"▒","blk14;":"░","blk34;":"▓","block;":"█","bne;":"=⃥","bnequiv;":"≡⃥","bNot;":"⫭","bnot;":"⌐","Bopf;":"𝔹","bopf;":"𝕓","bot;":"⊥","bottom;":"⊥","bowtie;":"⋈","boxbox;":"⧉","boxDL;":"╗","boxDl;":"╖","boxdL;":"╕","boxdl;":"┐","boxDR;":"╔","boxDr;":"╓","boxdR;":"╒","boxdr;":"┌","boxH;":"═","boxh;":"─","boxHD;":"╦","boxHd;":"╤","boxhD;":"╥","boxhd;":"┬","boxHU;":"╩","boxHu;":"╧","boxhU;":"╨","boxhu;":"┴","boxminus;":"⊟","boxplus;":"⊞","boxtimes;":"⊠","boxUL;":"╝","boxUl;":"╜","boxuL;":"╛","boxul;":"┘","boxUR;":"╚","boxUr;":"╙","boxuR;":"╘","boxur;":"└","boxV;":"║","boxv;":"│","boxVH;":"╬","boxVh;":"╫","boxvH;":"╪","boxvh;":"┼","boxVL;":"╣","boxVl;":"╢","boxvL;":"╡","boxvl;":"┤","boxVR;":"╠","boxVr;":"╟","boxvR;":"╞","boxvr;":"├","bprime;":"‵","Breve;":"˘","breve;":"˘","brvbar":"¦","brvbar;":"¦","Bscr;":"ℬ","bscr;":"𝒷","bsemi;":"⁏","bsim;":"∽","bsime;":"⋍","bsol;":"\\","bsolb;":"⧅","bsolhsub;":"⟈","bull;":"•","bullet;":"•","bump;":"≎","bumpE;":"⪮","bumpe;":"≏","Bumpeq;":"≎","bumpeq;":"≏","Cacute;":"Ć","cacute;":"ć","Cap;":"⋒","cap;":"∩","capand;":"⩄","capbrcup;":"⩉","capcap;":"⩋","capcup;":"⩇","capdot;":"⩀","CapitalDifferentialD;":"ⅅ","caps;":"∩︀","caret;":"⁁","caron;":"ˇ","Cayleys;":"ℭ","ccaps;":"⩍","Ccaron;":"Č","ccaron;":"č","Ccedil":"Ç","ccedil":"ç","Ccedil;":"Ç","ccedil;":"ç","Ccirc;":"Ĉ","ccirc;":"ĉ","Cconint;":"∰","ccups;":"⩌","ccupssm;":"⩐","Cdot;":"Ċ","cdot;":"ċ","cedil":"¸","cedil;":"¸","Cedilla;":"¸","cemptyv;":"⦲","cent":"¢","cent;":"¢","CenterDot;":"·","centerdot;":"·","Cfr;":"ℭ","cfr;":"𝔠","CHcy;":"Ч","chcy;":"ч","check;":"✓","checkmark;":"✓","Chi;":"Χ","chi;":"χ","cir;":"○","circ;":"ˆ","circeq;":"≗","circlearrowleft;":"↺","circlearrowright;":"↻","circledast;":"⊛","circledcirc;":"⊚","circleddash;":"⊝","CircleDot;":"⊙","circledR;":"®","circledS;":"Ⓢ","CircleMinus;":"⊖","CirclePlus;":"⊕","CircleTimes;":"⊗","cirE;":"⧃","cire;":"≗","cirfnint;":"⨐","cirmid;":"⫯","cirscir;":"⧂","ClockwiseContourIntegral;":"∲","CloseCurlyDoubleQuote;":"”","CloseCurlyQuote;":"’","clubs;":"♣","clubsuit;":"♣","Colon;":"∷","colon;":":","Colone;":"⩴","colone;":"≔","coloneq;":"≔","comma;":",","commat;":"@","comp;":"∁","compfn;":"∘","complement;":"∁","complexes;":"ℂ","cong;":"≅","congdot;":"⩭","Congruent;":"≡","Conint;":"∯","conint;":"∮","ContourIntegral;":"∮","Copf;":"ℂ","copf;":"𝕔","coprod;":"∐","Coproduct;":"∐","COPY":"©","copy":"©","COPY;":"©","copy;":"©","copysr;":"℗","CounterClockwiseContourIntegral;":"∳","crarr;":"↵","Cross;":"⨯","cross;":"✗","Cscr;":"𝒞","cscr;":"𝒸","csub;":"⫏","csube;":"⫑","csup;":"⫐","csupe;":"⫒","ctdot;":"⋯","cudarrl;":"⤸","cudarrr;":"⤵","cuepr;":"⋞","cuesc;":"⋟","cularr;":"↶","cularrp;":"⤽","Cup;":"⋓","cup;":"∪","cupbrcap;":"⩈","CupCap;":"≍","cupcap;":"⩆","cupcup;":"⩊","cupdot;":"⊍","cupor;":"⩅","cups;":"∪︀","curarr;":"↷","curarrm;":"⤼","curlyeqprec;":"⋞","curlyeqsucc;":"⋟","curlyvee;":"⋎","curlywedge;":"⋏","curren":"¤","curren;":"¤","curvearrowleft;":"↶","curvearrowright;":"↷","cuvee;":"⋎","cuwed;":"⋏","cwconint;":"∲","cwint;":"∱","cylcty;":"⌭","Dagger;":"‡","dagger;":"†","daleth;":"ℸ","Darr;":"↡","dArr;":"⇓","darr;":"↓","dash;":"‐","Dashv;":"⫤","dashv;":"⊣","dbkarow;":"⤏","dblac;":"˝","Dcaron;":"Ď","dcaron;":"ď","Dcy;":"Д","dcy;":"д","DD;":"ⅅ","dd;":"ⅆ","ddagger;":"‡","ddarr;":"⇊","DDotrahd;":"⤑","ddotseq;":"⩷","deg":"°","deg;":"°","Del;":"∇","Delta;":"Δ","delta;":"δ","demptyv;":"⦱","dfisht;":"⥿","Dfr;":"𝔇","dfr;":"𝔡","dHar;":"⥥","dharl;":"⇃","dharr;":"⇂","DiacriticalAcute;":"´","DiacriticalDot;":"˙","DiacriticalDoubleAcute;":"˝","DiacriticalGrave;":"`","DiacriticalTilde;":"˜","diam;":"⋄","Diamond;":"⋄","diamond;":"⋄","diamondsuit;":"♦","diams;":"♦","die;":"¨","DifferentialD;":"ⅆ","digamma;":"ϝ","disin;":"⋲","div;":"÷","divide":"÷","divide;":"÷","divideontimes;":"⋇","divonx;":"⋇","DJcy;":"Ђ","djcy;":"ђ","dlcorn;":"⌞","dlcrop;":"⌍","dollar;":"$","Dopf;":"𝔻","dopf;":"𝕕","Dot;":"¨","dot;":"˙","DotDot;":"⃜","doteq;":"≐","doteqdot;":"≑","DotEqual;":"≐","dotminus;":"∸","dotplus;":"∔","dotsquare;":"⊡","doublebarwedge;":"⌆","DoubleContourIntegral;":"∯","DoubleDot;":"¨","DoubleDownArrow;":"⇓","DoubleLeftArrow;":"⇐","DoubleLeftRightArrow;":"⇔","DoubleLeftTee;":"⫤","DoubleLongLeftArrow;":"⟸","DoubleLongLeftRightArrow;":"⟺","DoubleLongRightArrow;":"⟹","DoubleRightArrow;":"⇒","DoubleRightTee;":"⊨","DoubleUpArrow;":"⇑","DoubleUpDownArrow;":"⇕","DoubleVerticalBar;":"∥","DownArrow;":"↓","Downarrow;":"⇓","downarrow;":"↓","DownArrowBar;":"⤓","DownArrowUpArrow;":"⇵","DownBreve;":"̑","downdownarrows;":"⇊","downharpoonleft;":"⇃","downharpoonright;":"⇂","DownLeftRightVector;":"⥐","DownLeftTeeVector;":"⥞","DownLeftVector;":"↽","DownLeftVectorBar;":"⥖","DownRightTeeVector;":"⥟","DownRightVector;":"⇁","DownRightVectorBar;":"⥗","DownTee;":"⊤","DownTeeArrow;":"↧","drbkarow;":"⤐","drcorn;":"⌟","drcrop;":"⌌","Dscr;":"𝒟","dscr;":"𝒹","DScy;":"Ѕ","dscy;":"ѕ","dsol;":"⧶","Dstrok;":"Đ","dstrok;":"đ","dtdot;":"⋱","dtri;":"▿","dtrif;":"▾","duarr;":"⇵","duhar;":"⥯","dwangle;":"⦦","DZcy;":"Џ","dzcy;":"џ","dzigrarr;":"⟿","Eacute":"É","eacute":"é","Eacute;":"É","eacute;":"é","easter;":"⩮","Ecaron;":"Ě","ecaron;":"ě","ecir;":"≖","Ecirc":"Ê","ecirc":"ê","Ecirc;":"Ê","ecirc;":"ê","ecolon;":"≕","Ecy;":"Э","ecy;":"э","eDDot;":"⩷","Edot;":"Ė","eDot;":"≑","edot;":"ė","ee;":"ⅇ","efDot;":"≒","Efr;":"𝔈","efr;":"𝔢","eg;":"⪚","Egrave":"È","egrave":"è","Egrave;":"È","egrave;":"è","egs;":"⪖","egsdot;":"⪘","el;":"⪙","Element;":"∈","elinters;":"⏧","ell;":"ℓ","els;":"⪕","elsdot;":"⪗","Emacr;":"Ē","emacr;":"ē","empty;":"∅","emptyset;":"∅","EmptySmallSquare;":"◻","emptyv;":"∅","EmptyVerySmallSquare;":"▫","emsp13;":" ","emsp14;":" ","emsp;":" ","ENG;":"Ŋ","eng;":"ŋ","ensp;":" ","Eogon;":"Ę","eogon;":"ę","Eopf;":"𝔼","eopf;":"𝕖","epar;":"⋕","eparsl;":"⧣","eplus;":"⩱","epsi;":"ε","Epsilon;":"Ε","epsilon;":"ε","epsiv;":"ϵ","eqcirc;":"≖","eqcolon;":"≕","eqsim;":"≂","eqslantgtr;":"⪖","eqslantless;":"⪕","Equal;":"⩵","equals;":"=","EqualTilde;":"≂","equest;":"≟","Equilibrium;":"⇌","equiv;":"≡","equivDD;":"⩸","eqvparsl;":"⧥","erarr;":"⥱","erDot;":"≓","Escr;":"ℰ","escr;":"ℯ","esdot;":"≐","Esim;":"⩳","esim;":"≂","Eta;":"Η","eta;":"η","ETH":"Ð","eth":"ð","ETH;":"Ð","eth;":"ð","Euml":"Ë","euml":"ë","Euml;":"Ë","euml;":"ë","euro;":"€","excl;":"!","exist;":"∃","Exists;":"∃","expectation;":"ℰ","ExponentialE;":"ⅇ","exponentiale;":"ⅇ","fallingdotseq;":"≒","Fcy;":"Ф","fcy;":"ф","female;":"♀","ffilig;":"ﬃ","fflig;":"ﬀ","ffllig;":"ﬄ","Ffr;":"𝔉","ffr;":"𝔣","filig;":"ﬁ","FilledSmallSquare;":"◼","FilledVerySmallSquare;":"▪","fjlig;":"fj","flat;":"♭","fllig;":"ﬂ","fltns;":"▱","fnof;":"ƒ","Fopf;":"𝔽","fopf;":"𝕗","ForAll;":"∀","forall;":"∀","fork;":"⋔","forkv;":"⫙","Fouriertrf;":"ℱ","fpartint;":"⨍","frac12":"½","frac12;":"½","frac13;":"⅓","frac14":"¼","frac14;":"¼","frac15;":"⅕","frac16;":"⅙","frac18;":"⅛","frac23;":"⅔","frac25;":"⅖","frac34":"¾","frac34;":"¾","frac35;":"⅗","frac38;":"⅜","frac45;":"⅘","frac56;":"⅚","frac58;":"⅝","frac78;":"⅞","frasl;":"⁄","frown;":"⌢","Fscr;":"ℱ","fscr;":"𝒻","gacute;":"ǵ","Gamma;":"Γ","gamma;":"γ","Gammad;":"Ϝ","gammad;":"ϝ","gap;":"⪆","Gbreve;":"Ğ","gbreve;":"ğ","Gcedil;":"Ģ","Gcirc;":"Ĝ","gcirc;":"ĝ","Gcy;":"Г","gcy;":"г","Gdot;":"Ġ","gdot;":"ġ","gE;":"≧","ge;":"≥","gEl;":"⪌","gel;":"⋛","geq;":"≥","geqq;":"≧","geqslant;":"⩾","ges;":"⩾","gescc;":"⪩","gesdot;":"⪀","gesdoto;":"⪂","gesdotol;":"⪄","gesl;":"⋛︀","gesles;":"⪔","Gfr;":"𝔊","gfr;":"𝔤","Gg;":"⋙","gg;":"≫","ggg;":"⋙","gimel;":"ℷ","GJcy;":"Ѓ","gjcy;":"ѓ","gl;":"≷","gla;":"⪥","glE;":"⪒","glj;":"⪤","gnap;":"⪊","gnapprox;":"⪊","gnE;":"≩","gne;":"⪈","gneq;":"⪈","gneqq;":"≩","gnsim;":"⋧","Gopf;":"𝔾","gopf;":"𝕘","grave;":"`","GreaterEqual;":"≥","GreaterEqualLess;":"⋛","GreaterFullEqual;":"≧","GreaterGreater;":"⪢","GreaterLess;":"≷","GreaterSlantEqual;":"⩾","GreaterTilde;":"≳","Gscr;":"𝒢","gscr;":"ℊ","gsim;":"≳","gsime;":"⪎","gsiml;":"⪐","GT":">","gt":">","GT;":">","Gt;":"≫","gt;":">","gtcc;":"⪧","gtcir;":"⩺","gtdot;":"⋗","gtlPar;":"⦕","gtquest;":"⩼","gtrapprox;":"⪆","gtrarr;":"⥸","gtrdot;":"⋗","gtreqless;":"⋛","gtreqqless;":"⪌","gtrless;":"≷","gtrsim;":"≳","gvertneqq;":"≩︀","gvnE;":"≩︀","Hacek;":"ˇ","hairsp;":" ","half;":"½","hamilt;":"ℋ","HARDcy;":"Ъ","hardcy;":"ъ","hArr;":"⇔","harr;":"↔","harrcir;":"⥈","harrw;":"↭","Hat;":"^","hbar;":"ℏ","Hcirc;":"Ĥ","hcirc;":"ĥ","hearts;":"♥","heartsuit;":"♥","hellip;":"…","hercon;":"⊹","Hfr;":"ℌ","hfr;":"𝔥","HilbertSpace;":"ℋ","hksearow;":"⤥","hkswarow;":"⤦","hoarr;":"⇿","homtht;":"∻","hookleftarrow;":"↩","hookrightarrow;":"↪","Hopf;":"ℍ","hopf;":"𝕙","horbar;":"―","HorizontalLine;":"─","Hscr;":"ℋ","hscr;":"𝒽","hslash;":"ℏ","Hstrok;":"Ħ","hstrok;":"ħ","HumpDownHump;":"≎","HumpEqual;":"≏","hybull;":"⁃","hyphen;":"‐","Iacute":"Í","iacute":"í","Iacute;":"Í","iacute;":"í","ic;":"⁣","Icirc":"Î","icirc":"î","Icirc;":"Î","icirc;":"î","Icy;":"И","icy;":"и","Idot;":"İ","IEcy;":"Е","iecy;":"е","iexcl":"¡","iexcl;":"¡","iff;":"⇔","Ifr;":"ℑ","ifr;":"𝔦","Igrave":"Ì","igrave":"ì","Igrave;":"Ì","igrave;":"ì","ii;":"ⅈ","iiiint;":"⨌","iiint;":"∭","iinfin;":"⧜","iiota;":"℩","IJlig;":"Ĳ","ijlig;":"ĳ","Im;":"ℑ","Imacr;":"Ī","imacr;":"ī","image;":"ℑ","ImaginaryI;":"ⅈ","imagline;":"ℐ","imagpart;":"ℑ","imath;":"ı","imof;":"⊷","imped;":"Ƶ","Implies;":"⇒","in;":"∈","incare;":"℅","infin;":"∞","infintie;":"⧝","inodot;":"ı","Int;":"∬","int;":"∫","intcal;":"⊺","integers;":"ℤ","Integral;":"∫","intercal;":"⊺","Intersection;":"⋂","intlarhk;":"⨗","intprod;":"⨼","InvisibleComma;":"⁣","InvisibleTimes;":"⁢","IOcy;":"Ё","iocy;":"ё","Iogon;":"Į","iogon;":"į","Iopf;":"𝕀","iopf;":"𝕚","Iota;":"Ι","iota;":"ι","iprod;":"⨼","iquest":"¿","iquest;":"¿","Iscr;":"ℐ","iscr;":"𝒾","isin;":"∈","isindot;":"⋵","isinE;":"⋹","isins;":"⋴","isinsv;":"⋳","isinv;":"∈","it;":"⁢","Itilde;":"Ĩ","itilde;":"ĩ","Iukcy;":"І","iukcy;":"і","Iuml":"Ï","iuml":"ï","Iuml;":"Ï","iuml;":"ï","Jcirc;":"Ĵ","jcirc;":"ĵ","Jcy;":"Й","jcy;":"й","Jfr;":"𝔍","jfr;":"𝔧","jmath;":"ȷ","Jopf;":"𝕁","jopf;":"𝕛","Jscr;":"𝒥","jscr;":"𝒿","Jsercy;":"Ј","jsercy;":"ј","Jukcy;":"Є","jukcy;":"є","Kappa;":"Κ","kappa;":"κ","kappav;":"ϰ","Kcedil;":"Ķ","kcedil;":"ķ","Kcy;":"К","kcy;":"к","Kfr;":"𝔎","kfr;":"𝔨","kgreen;":"ĸ","KHcy;":"Х","khcy;":"х","KJcy;":"Ќ","kjcy;":"ќ","Kopf;":"𝕂","kopf;":"𝕜","Kscr;":"𝒦","kscr;":"𝓀","lAarr;":"⇚","Lacute;":"Ĺ","lacute;":"ĺ","laemptyv;":"⦴","lagran;":"ℒ","Lambda;":"Λ","lambda;":"λ","Lang;":"⟪","lang;":"⟨","langd;":"⦑","langle;":"⟨","lap;":"⪅","Laplacetrf;":"ℒ","laquo":"«","laquo;":"«","Larr;":"↞","lArr;":"⇐","larr;":"←","larrb;":"⇤","larrbfs;":"⤟","larrfs;":"⤝","larrhk;":"↩","larrlp;":"↫","larrpl;":"⤹","larrsim;":"⥳","larrtl;":"↢","lat;":"⪫","lAtail;":"⤛","latail;":"⤙","late;":"⪭","lates;":"⪭︀","lBarr;":"⤎","lbarr;":"⤌","lbbrk;":"❲","lbrace;":"{","lbrack;":"[","lbrke;":"⦋","lbrksld;":"⦏","lbrkslu;":"⦍","Lcaron;":"Ľ","lcaron;":"ľ","Lcedil;":"Ļ","lcedil;":"ļ","lceil;":"⌈","lcub;":"{","Lcy;":"Л","lcy;":"л","ldca;":"⤶","ldquo;":"“","ldquor;":"„","ldrdhar;":"⥧","ldrushar;":"⥋","ldsh;":"↲","lE;":"≦","le;":"≤","LeftAngleBracket;":"⟨","LeftArrow;":"←","Leftarrow;":"⇐","leftarrow;":"←","LeftArrowBar;":"⇤","LeftArrowRightArrow;":"⇆","leftarrowtail;":"↢","LeftCeiling;":"⌈","LeftDoubleBracket;":"⟦","LeftDownTeeVector;":"⥡","LeftDownVector;":"⇃","LeftDownVectorBar;":"⥙","LeftFloor;":"⌊","leftharpoondown;":"↽","leftharpoonup;":"↼","leftleftarrows;":"⇇","LeftRightArrow;":"↔","Leftrightarrow;":"⇔","leftrightarrow;":"↔","leftrightarrows;":"⇆","leftrightharpoons;":"⇋","leftrightsquigarrow;":"↭","LeftRightVector;":"⥎","LeftTee;":"⊣","LeftTeeArrow;":"↤","LeftTeeVector;":"⥚","leftthreetimes;":"⋋","LeftTriangle;":"⊲","LeftTriangleBar;":"⧏","LeftTriangleEqual;":"⊴","LeftUpDownVector;":"⥑","LeftUpTeeVector;":"⥠","LeftUpVector;":"↿","LeftUpVectorBar;":"⥘","LeftVector;":"↼","LeftVectorBar;":"⥒","lEg;":"⪋","leg;":"⋚","leq;":"≤","leqq;":"≦","leqslant;":"⩽","les;":"⩽","lescc;":"⪨","lesdot;":"⩿","lesdoto;":"⪁","lesdotor;":"⪃","lesg;":"⋚︀","lesges;":"⪓","lessapprox;":"⪅","lessdot;":"⋖","lesseqgtr;":"⋚","lesseqqgtr;":"⪋","LessEqualGreater;":"⋚","LessFullEqual;":"≦","LessGreater;":"≶","lessgtr;":"≶","LessLess;":"⪡","lesssim;":"≲","LessSlantEqual;":"⩽","LessTilde;":"≲","lfisht;":"⥼","lfloor;":"⌊","Lfr;":"𝔏","lfr;":"𝔩","lg;":"≶","lgE;":"⪑","lHar;":"⥢","lhard;":"↽","lharu;":"↼","lharul;":"⥪","lhblk;":"▄","LJcy;":"Љ","ljcy;":"љ","Ll;":"⋘","ll;":"≪","llarr;":"⇇","llcorner;":"⌞","Lleftarrow;":"⇚","llhard;":"⥫","lltri;":"◺","Lmidot;":"Ŀ","lmidot;":"ŀ","lmoust;":"⎰","lmoustache;":"⎰","lnap;":"⪉","lnapprox;":"⪉","lnE;":"≨","lne;":"⪇","lneq;":"⪇","lneqq;":"≨","lnsim;":"⋦","loang;":"⟬","loarr;":"⇽","lobrk;":"⟦","LongLeftArrow;":"⟵","Longleftarrow;":"⟸","longleftarrow;":"⟵","LongLeftRightArrow;":"⟷","Longleftrightarrow;":"⟺","longleftrightarrow;":"⟷","longmapsto;":"⟼","LongRightArrow;":"⟶","Longrightarrow;":"⟹","longrightarrow;":"⟶","looparrowleft;":"↫","looparrowright;":"↬","lopar;":"⦅","Lopf;":"𝕃","lopf;":"𝕝","loplus;":"⨭","lotimes;":"⨴","lowast;":"∗","lowbar;":"_","LowerLeftArrow;":"↙","LowerRightArrow;":"↘","loz;":"◊","lozenge;":"◊","lozf;":"⧫","lpar;":"(","lparlt;":"⦓","lrarr;":"⇆","lrcorner;":"⌟","lrhar;":"⇋","lrhard;":"⥭","lrm;":"‎","lrtri;":"⊿","lsaquo;":"‹","Lscr;":"ℒ","lscr;":"𝓁","Lsh;":"↰","lsh;":"↰","lsim;":"≲","lsime;":"⪍","lsimg;":"⪏","lsqb;":"[","lsquo;":"‘","lsquor;":"‚","Lstrok;":"Ł","lstrok;":"ł","LT":"<","lt":"<","LT;":"<","Lt;":"≪","lt;":"<","ltcc;":"⪦","ltcir;":"⩹","ltdot;":"⋖","lthree;":"⋋","ltimes;":"⋉","ltlarr;":"⥶","ltquest;":"⩻","ltri;":"◃","ltrie;":"⊴","ltrif;":"◂","ltrPar;":"⦖","lurdshar;":"⥊","luruhar;":"⥦","lvertneqq;":"≨︀","lvnE;":"≨︀","macr":"¯","macr;":"¯","male;":"♂","malt;":"✠","maltese;":"✠","Map;":"⤅","map;":"↦","mapsto;":"↦","mapstodown;":"↧","mapstoleft;":"↤","mapstoup;":"↥","marker;":"▮","mcomma;":"⨩","Mcy;":"М","mcy;":"м","mdash;":"—","mDDot;":"∺","measuredangle;":"∡","MediumSpace;":" ","Mellintrf;":"ℳ","Mfr;":"𝔐","mfr;":"𝔪","mho;":"℧","micro":"µ","micro;":"µ","mid;":"∣","midast;":"*","midcir;":"⫰","middot":"·","middot;":"·","minus;":"−","minusb;":"⊟","minusd;":"∸","minusdu;":"⨪","MinusPlus;":"∓","mlcp;":"⫛","mldr;":"…","mnplus;":"∓","models;":"⊧","Mopf;":"𝕄","mopf;":"𝕞","mp;":"∓","Mscr;":"ℳ","mscr;":"𝓂","mstpos;":"∾","Mu;":"Μ","mu;":"μ","multimap;":"⊸","mumap;":"⊸","nabla;":"∇","Nacute;":"Ń","nacute;":"ń","nang;":"∠⃒","nap;":"≉","napE;":"⩰̸","napid;":"≋̸","napos;":"ŉ","napprox;":"≉","natur;":"♮","natural;":"♮","naturals;":"ℕ","nbsp":" ","nbsp;":" ","nbump;":"≎̸","nbumpe;":"≏̸","ncap;":"⩃","Ncaron;":"Ň","ncaron;":"ň","Ncedil;":"Ņ","ncedil;":"ņ","ncong;":"≇","ncongdot;":"⩭̸","ncup;":"⩂","Ncy;":"Н","ncy;":"н","ndash;":"–","ne;":"≠","nearhk;":"⤤","neArr;":"⇗","nearr;":"↗","nearrow;":"↗","nedot;":"≐̸","NegativeMediumSpace;":"\u200b","NegativeThickSpace;":"\u200b","NegativeThinSpace;":"\u200b","NegativeVeryThinSpace;":"\u200b","nequiv;":"≢","nesear;":"⤨","nesim;":"≂̸","NestedGreaterGreater;":"≫","NestedLessLess;":"≪","NewLine;":"\n","nexist;":"∄","nexists;":"∄","Nfr;":"𝔑","nfr;":"𝔫","ngE;":"≧̸","nge;":"≱","ngeq;":"≱","ngeqq;":"≧̸","ngeqslant;":"⩾̸","nges;":"⩾̸","nGg;":"⋙̸","ngsim;":"≵","nGt;":"≫⃒","ngt;":"≯","ngtr;":"≯","nGtv;":"≫̸","nhArr;":"⇎","nharr;":"↮","nhpar;":"⫲","ni;":"∋","nis;":"⋼","nisd;":"⋺","niv;":"∋","NJcy;":"Њ","njcy;":"њ","nlArr;":"⇍","nlarr;":"↚","nldr;":"‥","nlE;":"≦̸","nle;":"≰","nLeftarrow;":"⇍","nleftarrow;":"↚","nLeftrightarrow;":"⇎","nleftrightarrow;":"↮","nleq;":"≰","nleqq;":"≦̸","nleqslant;":"⩽̸","nles;":"⩽̸","nless;":"≮","nLl;":"⋘̸","nlsim;":"≴","nLt;":"≪⃒","nlt;":"≮","nltri;":"⋪","nltrie;":"⋬","nLtv;":"≪̸","nmid;":"∤","NoBreak;":"\u2060","NonBreakingSpace;":" ","Nopf;":"ℕ","nopf;":"𝕟","not":"¬","Not;":"⫬","not;":"¬","NotCongruent;":"≢","NotCupCap;":"≭","NotDoubleVerticalBar;":"∦","NotElement;":"∉","NotEqual;":"≠","NotEqualTilde;":"≂̸","NotExists;":"∄","NotGreater;":"≯","NotGreaterEqual;":"≱","NotGreaterFullEqual;":"≧̸","NotGreaterGreater;":"≫̸","NotGreaterLess;":"≹","NotGreaterSlantEqual;":"⩾̸","NotGreaterTilde;":"≵","NotHumpDownHump;":"≎̸","NotHumpEqual;":"≏̸","notin;":"∉","notindot;":"⋵̸","notinE;":"⋹̸","notinva;":"∉","notinvb;":"⋷","notinvc;":"⋶","NotLeftTriangle;":"⋪","NotLeftTriangleBar;":"⧏̸","NotLeftTriangleEqual;":"⋬","NotLess;":"≮","NotLessEqual;":"≰","NotLessGreater;":"≸","NotLessLess;":"≪̸","NotLessSlantEqual;":"⩽̸","NotLessTilde;":"≴","NotNestedGreaterGreater;":"⪢̸","NotNestedLessLess;":"⪡̸","notni;":"∌","notniva;":"∌","notnivb;":"⋾","notnivc;":"⋽","NotPrecedes;":"⊀","NotPrecedesEqual;":"⪯̸","NotPrecedesSlantEqual;":"⋠","NotReverseElement;":"∌","NotRightTriangle;":"⋫","NotRightTriangleBar;":"⧐̸","NotRightTriangleEqual;":"⋭","NotSquareSubset;":"⊏̸","NotSquareSubsetEqual;":"⋢","NotSquareSuperset;":"⊐̸","NotSquareSupersetEqual;":"⋣","NotSubset;":"⊂⃒","NotSubsetEqual;":"⊈","NotSucceeds;":"⊁","NotSucceedsEqual;":"⪰̸","NotSucceedsSlantEqual;":"⋡","NotSucceedsTilde;":"≿̸","NotSuperset;":"⊃⃒","NotSupersetEqual;":"⊉","NotTilde;":"≁","NotTildeEqual;":"≄","NotTildeFullEqual;":"≇","NotTildeTilde;":"≉","NotVerticalBar;":"∤","npar;":"∦","nparallel;":"∦","nparsl;":"⫽⃥","npart;":"∂̸","npolint;":"⨔","npr;":"⊀","nprcue;":"⋠","npre;":"⪯̸","nprec;":"⊀","npreceq;":"⪯̸","nrArr;":"⇏","nrarr;":"↛","nrarrc;":"⤳̸","nrarrw;":"↝̸","nRightarrow;":"⇏","nrightarrow;":"↛","nrtri;":"⋫","nrtrie;":"⋭","nsc;":"⊁","nsccue;":"⋡","nsce;":"⪰̸","Nscr;":"𝒩","nscr;":"𝓃","nshortmid;":"∤","nshortparallel;":"∦","nsim;":"≁","nsime;":"≄","nsimeq;":"≄","nsmid;":"∤","nspar;":"∦","nsqsube;":"⋢","nsqsupe;":"⋣","nsub;":"⊄","nsubE;":"⫅̸","nsube;":"⊈","nsubset;":"⊂⃒","nsubseteq;":"⊈","nsubseteqq;":"⫅̸","nsucc;":"⊁","nsucceq;":"⪰̸","nsup;":"⊅","nsupE;":"⫆̸","nsupe;":"⊉","nsupset;":"⊃⃒","nsupseteq;":"⊉","nsupseteqq;":"⫆̸","ntgl;":"≹","Ntilde":"Ñ","ntilde":"ñ","Ntilde;":"Ñ","ntilde;":"ñ","ntlg;":"≸","ntriangleleft;":"⋪","ntrianglelefteq;":"⋬","ntriangleright;":"⋫","ntrianglerighteq;":"⋭","Nu;":"Ν","nu;":"ν","num;":"#","numero;":"№","numsp;":" ","nvap;":"≍⃒","nVDash;":"⊯","nVdash;":"⊮","nvDash;":"⊭","nvdash;":"⊬","nvge;":"≥⃒","nvgt;":">⃒","nvHarr;":"⤄","nvinfin;":"⧞","nvlArr;":"⤂","nvle;":"≤⃒","nvlt;":"<⃒","nvltrie;":"⊴⃒","nvrArr;":"⤃","nvrtrie;":"⊵⃒","nvsim;":"∼⃒","nwarhk;":"⤣","nwArr;":"⇖","nwarr;":"↖","nwarrow;":"↖","nwnear;":"⤧","Oacute":"Ó","oacute":"ó","Oacute;":"Ó","oacute;":"ó","oast;":"⊛","ocir;":"⊚","Ocirc":"Ô","ocirc":"ô","Ocirc;":"Ô","ocirc;":"ô","Ocy;":"О","ocy;":"о","odash;":"⊝","Odblac;":"Ő","odblac;":"ő","odiv;":"⨸","odot;":"⊙","odsold;":"⦼","OElig;":"Œ","oelig;":"œ","ofcir;":"⦿","Ofr;":"𝔒","ofr;":"𝔬","ogon;":"˛","Ograve":"Ò","ograve":"ò","Ograve;":"Ò","ograve;":"ò","ogt;":"⧁","ohbar;":"⦵","ohm;":"Ω","oint;":"∮","olarr;":"↺","olcir;":"⦾","olcross;":"⦻","oline;":"‾","olt;":"⧀","Omacr;":"Ō","omacr;":"ō","Omega;":"Ω","omega;":"ω","Omicron;":"Ο","omicron;":"ο","omid;":"⦶","ominus;":"⊖","Oopf;":"𝕆","oopf;":"𝕠","opar;":"⦷","OpenCurlyDoubleQuote;":"“","OpenCurlyQuote;":"‘","operp;":"⦹","oplus;":"⊕","Or;":"⩔","or;":"∨","orarr;":"↻","ord;":"⩝","order;":"ℴ","orderof;":"ℴ","ordf":"ª","ordf;":"ª","ordm":"º","ordm;":"º","origof;":"⊶","oror;":"⩖","orslope;":"⩗","orv;":"⩛","oS;":"Ⓢ","Oscr;":"𝒪","oscr;":"ℴ","Oslash":"Ø","oslash":"ø","Oslash;":"Ø","oslash;":"ø","osol;":"⊘","Otilde":"Õ","otilde":"õ","Otilde;":"Õ","otilde;":"õ","Otimes;":"⨷","otimes;":"⊗","otimesas;":"⨶","Ouml":"Ö","ouml":"ö","Ouml;":"Ö","ouml;":"ö","ovbar;":"⌽","OverBar;":"‾","OverBrace;":"⏞","OverBracket;":"⎴","OverParenthesis;":"⏜","par;":"∥","para":"¶","para;":"¶","parallel;":"∥","parsim;":"⫳","parsl;":"⫽","part;":"∂","PartialD;":"∂","Pcy;":"П","pcy;":"п","percnt;":"%","period;":".","permil;":"‰","perp;":"⊥","pertenk;":"‱","Pfr;":"𝔓","pfr;":"𝔭","Phi;":"Φ","phi;":"φ","phiv;":"ϕ","phmmat;":"ℳ","phone;":"☎","Pi;":"Π","pi;":"π","pitchfork;":"⋔","piv;":"ϖ","planck;":"ℏ","planckh;":"ℎ","plankv;":"ℏ","plus;":"+","plusacir;":"⨣","plusb;":"⊞","pluscir;":"⨢","plusdo;":"∔","plusdu;":"⨥","pluse;":"⩲","PlusMinus;":"±","plusmn":"±","plusmn;":"±","plussim;":"⨦","plustwo;":"⨧","pm;":"±","Poincareplane;":"ℌ","pointint;":"⨕","Popf;":"ℙ","popf;":"𝕡","pound":"£","pound;":"£","Pr;":"⪻","pr;":"≺","prap;":"⪷","prcue;":"≼","prE;":"⪳","pre;":"⪯","prec;":"≺","precapprox;":"⪷","preccurlyeq;":"≼","Precedes;":"≺","PrecedesEqual;":"⪯","PrecedesSlantEqual;":"≼","PrecedesTilde;":"≾","preceq;":"⪯","precnapprox;":"⪹","precneqq;":"⪵","precnsim;":"⋨","precsim;":"≾","Prime;":"″","prime;":"′","primes;":"ℙ","prnap;":"⪹","prnE;":"⪵","prnsim;":"⋨","prod;":"∏","Product;":"∏","profalar;":"⌮","profline;":"⌒","profsurf;":"⌓","prop;":"∝","Proportion;":"∷","Proportional;":"∝","propto;":"∝","prsim;":"≾","prurel;":"⊰","Pscr;":"𝒫","pscr;":"𝓅","Psi;":"Ψ","psi;":"ψ","puncsp;":" ","Qfr;":"𝔔","qfr;":"𝔮","qint;":"⨌","Qopf;":"ℚ","qopf;":"𝕢","qprime;":"⁗","Qscr;":"𝒬","qscr;":"𝓆","quaternions;":"ℍ","quatint;":"⨖","quest;":"?","questeq;":"≟","QUOT":"\"","quot":"\"","QUOT;":"\"","quot;":"\"","rAarr;":"⇛","race;":"∽̱","Racute;":"Ŕ","racute;":"ŕ","radic;":"√","raemptyv;":"⦳","Rang;":"⟫","rang;":"⟩","rangd;":"⦒","range;":"⦥","rangle;":"⟩","raquo":"»","raquo;":"»","Rarr;":"↠","rArr;":"⇒","rarr;":"→","rarrap;":"⥵","rarrb;":"⇥","rarrbfs;":"⤠","rarrc;":"⤳","rarrfs;":"⤞","rarrhk;":"↪","rarrlp;":"↬","rarrpl;":"⥅","rarrsim;":"⥴","Rarrtl;":"⤖","rarrtl;":"↣","rarrw;":"↝","rAtail;":"⤜","ratail;":"⤚","ratio;":"∶","rationals;":"ℚ","RBarr;":"⤐","rBarr;":"⤏","rbarr;":"⤍","rbbrk;":"❳","rbrace;":"}","rbrack;":"]","rbrke;":"⦌","rbrksld;":"⦎","rbrkslu;":"⦐","Rcaron;":"Ř","rcaron;":"ř","Rcedil;":"Ŗ","rcedil;":"ŗ","rceil;":"⌉","rcub;":"}","Rcy;":"Р","rcy;":"р","rdca;":"⤷","rdldhar;":"⥩","rdquo;":"”","rdquor;":"”","rdsh;":"↳","Re;":"ℜ","real;":"ℜ","realine;":"ℛ","realpart;":"ℜ","reals;":"ℝ","rect;":"▭","REG":"®","reg":"®","REG;":"®","reg;":"®","ReverseElement;":"∋","ReverseEquilibrium;":"⇋","ReverseUpEquilibrium;":"⥯","rfisht;":"⥽","rfloor;":"⌋","Rfr;":"ℜ","rfr;":"𝔯","rHar;":"⥤","rhard;":"⇁","rharu;":"⇀","rharul;":"⥬","Rho;":"Ρ","rho;":"ρ","rhov;":"ϱ","RightAngleBracket;":"⟩","RightArrow;":"→","Rightarrow;":"⇒","rightarrow;":"→","RightArrowBar;":"⇥","RightArrowLeftArrow;":"⇄","rightarrowtail;":"↣","RightCeiling;":"⌉","RightDoubleBracket;":"⟧","RightDownTeeVector;":"⥝","RightDownVector;":"⇂","RightDownVectorBar;":"⥕","RightFloor;":"⌋","rightharpoondown;":"⇁","rightharpoonup;":"⇀","rightleftarrows;":"⇄","rightleftharpoons;":"⇌","rightrightarrows;":"⇉","rightsquigarrow;":"↝","RightTee;":"⊢","RightTeeArrow;":"↦","RightTeeVector;":"⥛","rightthreetimes;":"⋌","RightTriangle;":"⊳","RightTriangleBar;":"⧐","RightTriangleEqual;":"⊵","RightUpDownVector;":"⥏","RightUpTeeVector;":"⥜","RightUpVector;":"↾","RightUpVectorBar;":"⥔","RightVector;":"⇀","RightVectorBar;":"⥓","ring;":"˚","risingdotseq;":"≓","rlarr;":"⇄","rlhar;":"⇌","rlm;":"‏","rmoust;":"⎱","rmoustache;":"⎱","rnmid;":"⫮","roang;":"⟭","roarr;":"⇾","robrk;":"⟧","ropar;":"⦆","Ropf;":"ℝ","ropf;":"𝕣","roplus;":"⨮","rotimes;":"⨵","RoundImplies;":"⥰","rpar;":")","rpargt;":"⦔","rppolint;":"⨒","rrarr;":"⇉","Rrightarrow;":"⇛","rsaquo;":"›","Rscr;":"ℛ","rscr;":"𝓇","Rsh;":"↱","rsh;":"↱","rsqb;":"]","rsquo;":"’","rsquor;":"’","rthree;":"⋌","rtimes;":"⋊","rtri;":"▹","rtrie;":"⊵","rtrif;":"▸","rtriltri;":"⧎","RuleDelayed;":"⧴","ruluhar;":"⥨","rx;":"℞","Sacute;":"Ś","sacute;":"ś","sbquo;":"‚","Sc;":"⪼","sc;":"≻","scap;":"⪸","Scaron;":"Š","scaron;":"š","sccue;":"≽","scE;":"⪴","sce;":"⪰","Scedil;":"Ş","scedil;":"ş","Scirc;":"Ŝ","scirc;":"ŝ","scnap;":"⪺","scnE;":"⪶","scnsim;":"⋩","scpolint;":"⨓","scsim;":"≿","Scy;":"С","scy;":"с","sdot;":"⋅","sdotb;":"⊡","sdote;":"⩦","searhk;":"⤥","seArr;":"⇘","searr;":"↘","searrow;":"↘","sect":"§","sect;":"§","semi;":";","seswar;":"⤩","setminus;":"∖","setmn;":"∖","sext;":"✶","Sfr;":"𝔖","sfr;":"𝔰","sfrown;":"⌢","sharp;":"♯","SHCHcy;":"Щ","shchcy;":"щ","SHcy;":"Ш","shcy;":"ш","ShortDownArrow;":"↓","ShortLeftArrow;":"←","shortmid;":"∣","shortparallel;":"∥","ShortRightArrow;":"→","ShortUpArrow;":"↑","shy":"\u00ad","shy;":"\u00ad","Sigma;":"Σ","sigma;":"σ","sigmaf;":"ς","sigmav;":"ς","sim;":"∼","simdot;":"⩪","sime;":"≃","simeq;":"≃","simg;":"⪞","simgE;":"⪠","siml;":"⪝","simlE;":"⪟","simne;":"≆","simplus;":"⨤","simrarr;":"⥲","slarr;":"←","SmallCircle;":"∘","smallsetminus;":"∖","smashp;":"⨳","smeparsl;":"⧤","smid;":"∣","smile;":"⌣","smt;":"⪪","smte;":"⪬","smtes;":"⪬︀","SOFTcy;":"Ь","softcy;":"ь","sol;":"/","solb;":"⧄","solbar;":"⌿","Sopf;":"𝕊","sopf;":"𝕤","spades;":"♠","spadesuit;":"♠","spar;":"∥","sqcap;":"⊓","sqcaps;":"⊓︀","sqcup;":"⊔","sqcups;":"⊔︀","Sqrt;":"√","sqsub;":"⊏","sqsube;":"⊑","sqsubset;":"⊏","sqsubseteq;":"⊑","sqsup;":"⊐","sqsupe;":"⊒","sqsupset;":"⊐","sqsupseteq;":"⊒","squ;":"□","Square;":"□","square;":"□","SquareIntersection;":"⊓","SquareSubset;":"⊏","SquareSubsetEqual;":"⊑","SquareSuperset;":"⊐","SquareSupersetEqual;":"⊒","SquareUnion;":"⊔","squarf;":"▪","squf;":"▪","srarr;":"→","Sscr;":"𝒮","sscr;":"𝓈","ssetmn;":"∖","ssmile;":"⌣","sstarf;":"⋆","Star;":"⋆","star;":"☆","starf;":"★","straightepsilon;":"ϵ","straightphi;":"ϕ","strns;":"¯","Sub;":"⋐","sub;":"⊂","subdot;":"⪽","subE;":"⫅","sube;":"⊆","subedot;":"⫃","submult;":"⫁","subnE;":"⫋","subne;":"⊊","subplus;":"⪿","subrarr;":"⥹","Subset;":"⋐","subset;":"⊂","subseteq;":"⊆","subseteqq;":"⫅","SubsetEqual;":"⊆","subsetneq;":"⊊","subsetneqq;":"⫋","subsim;":"⫇","subsub;":"⫕","subsup;":"⫓","succ;":"≻","succapprox;":"⪸","succcurlyeq;":"≽","Succeeds;":"≻","SucceedsEqual;":"⪰","SucceedsSlantEqual;":"≽","SucceedsTilde;":"≿","succeq;":"⪰","succnapprox;":"⪺","succneqq;":"⪶","succnsim;":"⋩","succsim;":"≿","SuchThat;":"∋","Sum;":"∑","sum;":"∑","sung;":"♪","sup1":"¹","sup1;":"¹","sup2":"²","sup2;":"²","sup3":"³","sup3;":"³","Sup;":"⋑","sup;":"⊃","supdot;":"⪾","supdsub;":"⫘","supE;":"⫆","supe;":"⊇","supedot;":"⫄","Superset;":"⊃","SupersetEqual;":"⊇","suphsol;":"⟉","suphsub;":"⫗","suplarr;":"⥻","supmult;":"⫂","supnE;":"⫌","supne;":"⊋","supplus;":"⫀","Supset;":"⋑","supset;":"⊃","supseteq;":"⊇","supseteqq;":"⫆","supsetneq;":"⊋","supsetneqq;":"⫌","supsim;":"⫈","supsub;":"⫔","supsup;":"⫖","swarhk;":"⤦","swArr;":"⇙","swarr;":"↙","swarrow;":"↙","swnwar;":"⤪","szlig":"ß","szlig;":"ß","Tab;":"\t","target;":"⌖","Tau;":"Τ","tau;":"τ","tbrk;":"⎴","Tcaron;":"Ť","tcaron;":"ť","Tcedil;":"Ţ","tcedil;":"ţ","Tcy;":"Т","tcy;":"т","tdot;":"⃛","telrec;":"⌕","Tfr;":"𝔗","tfr;":"𝔱","there4;":"∴","Therefore;":"∴","therefore;":"∴","Theta;":"Θ","theta;":"θ","thetasym;":"ϑ","thetav;":"ϑ","thickapprox;":"≈","thicksim;":"∼","ThickSpace;":"  ","thinsp;":" ","ThinSpace;":" ","thkap;":"≈","thksim;":"∼","THORN":"Þ","thorn":"þ","THORN;":"Þ","thorn;":"þ","Tilde;":"∼","tilde;":"˜","TildeEqual;":"≃","TildeFullEqual;":"≅","TildeTilde;":"≈","times":"×","times;":"×","timesb;":"⊠","timesbar;":"⨱","timesd;":"⨰","tint;":"∭","toea;":"⤨","top;":"⊤","topbot;":"⌶","topcir;":"⫱","Topf;":"𝕋","topf;":"𝕥","topfork;":"⫚","tosa;":"⤩","tprime;":"‴","TRADE;":"™","trade;":"™","triangle;":"▵","triangledown;":"▿","triangleleft;":"◃","trianglelefteq;":"⊴","triangleq;":"≜","triangleright;":"▹","trianglerighteq;":"⊵","tridot;":"◬","trie;":"≜","triminus;":"⨺","TripleDot;":"⃛","triplus;":"⨹","trisb;":"⧍","tritime;":"⨻","trpezium;":"⏢","Tscr;":"𝒯","tscr;":"𝓉","TScy;":"Ц","tscy;":"ц","TSHcy;":"Ћ","tshcy;":"ћ","Tstrok;":"Ŧ","tstrok;":"ŧ","twixt;":"≬","twoheadleftarrow;":"↞","twoheadrightarrow;":"↠","Uacute":"Ú","uacute":"ú","Uacute;":"Ú","uacute;":"ú","Uarr;":"↟","uArr;":"⇑","uarr;":"↑","Uarrocir;":"⥉","Ubrcy;":"Ў","ubrcy;":"ў","Ubreve;":"Ŭ","ubreve;":"ŭ","Ucirc":"Û","ucirc":"û","Ucirc;":"Û","ucirc;":"û","Ucy;":"У","ucy;":"у","udarr;":"⇅","Udblac;":"Ű","udblac;":"ű","udhar;":"⥮","ufisht;":"⥾","Ufr;":"𝔘","ufr;":"𝔲","Ugrave":"Ù","ugrave":"ù","Ugrave;":"Ù","ugrave;":"ù","uHar;":"⥣","uharl;":"↿","uharr;":"↾","uhblk;":"▀","ulcorn;":"⌜","ulcorner;":"⌜","ulcrop;":"⌏","ultri;":"◸","Umacr;":"Ū","umacr;":"ū","uml":"¨","uml;":"¨","UnderBar;":"_","UnderBrace;":"⏟","UnderBracket;":"⎵","UnderParenthesis;":"⏝","Union;":"⋃","UnionPlus;":"⊎","Uogon;":"Ų","uogon;":"ų","Uopf;":"𝕌","uopf;":"𝕦","UpArrow;":"↑","Uparrow;":"⇑","uparrow;":"↑","UpArrowBar;":"⤒","UpArrowDownArrow;":"⇅","UpDownArrow;":"↕","Updownarrow;":"⇕","updownarrow;":"↕","UpEquilibrium;":"⥮","upharpoonleft;":"↿","upharpoonright;":"↾","uplus;":"⊎","UpperLeftArrow;":"↖","UpperRightArrow;":"↗","Upsi;":"ϒ","upsi;":"υ","upsih;":"ϒ","Upsilon;":"Υ","upsilon;":"υ","UpTee;":"⊥","UpTeeArrow;":"↥","upuparrows;":"⇈","urcorn;":"⌝","urcorner;":"⌝","urcrop;":"⌎","Uring;":"Ů","uring;":"ů","urtri;":"◹","Uscr;":"𝒰","uscr;":"𝓊","utdot;":"⋰","Utilde;":"Ũ","utilde;":"ũ","utri;":"▵","utrif;":"▴","uuarr;":"⇈","Uuml":"Ü","uuml":"ü","Uuml;":"Ü","uuml;":"ü","uwangle;":"⦧","vangrt;":"⦜","varepsilon;":"ϵ","varkappa;":"ϰ","varnothing;":"∅","varphi;":"ϕ","varpi;":"ϖ","varpropto;":"∝","vArr;":"⇕","varr;":"↕","varrho;":"ϱ","varsigma;":"ς","varsubsetneq;":"⊊︀","varsubsetneqq;":"⫋︀","varsupsetneq;":"⊋︀","varsupsetneqq;":"⫌︀","vartheta;":"ϑ","vartriangleleft;":"⊲","vartriangleright;":"⊳","Vbar;":"⫫","vBar;":"⫨","vBarv;":"⫩","Vcy;":"В","vcy;":"в","VDash;":"⊫","Vdash;":"⊩","vDash;":"⊨","vdash;":"⊢","Vdashl;":"⫦","Vee;":"⋁","vee;":"∨","veebar;":"⊻","veeeq;":"≚","vellip;":"⋮","Verbar;":"‖","verbar;":"|","Vert;":"‖","vert;":"|","VerticalBar;":"∣","VerticalLine;":"|","VerticalSeparator;":"❘","VerticalTilde;":"≀","VeryThinSpace;":" ","Vfr;":"𝔙","vfr;":"𝔳","vltri;":"⊲","vnsub;":"⊂⃒","vnsup;":"⊃⃒","Vopf;":"𝕍","vopf;":"𝕧","vprop;":"∝","vrtri;":"⊳","Vscr;":"𝒱","vscr;":"𝓋","vsubnE;":"⫋︀","vsubne;":"⊊︀","vsupnE;":"⫌︀","vsupne;":"⊋︀","Vvdash;":"⊪","vzigzag;":"⦚","Wcirc;":"Ŵ","wcirc;":"ŵ","wedbar;":"⩟","Wedge;":"⋀","wedge;":"∧","wedgeq;":"≙","weierp;":"℘","Wfr;":"𝔚","wfr;":"𝔴","Wopf;":"𝕎","wopf;":"𝕨","wp;":"℘","wr;":"≀","wreath;":"≀","Wscr;":"𝒲","wscr;":"𝓌","xcap;":"⋂","xcirc;":"◯","xcup;":"⋃","xdtri;":"▽","Xfr;":"𝔛","xfr;":"𝔵","xhArr;":"⟺","xharr;":"⟷","Xi;":"Ξ","xi;":"ξ","xlArr;":"⟸","xlarr;":"⟵","xmap;":"⟼","xnis;":"⋻","xodot;":"⨀","Xopf;":"𝕏","xopf;":"𝕩","xoplus;":"⨁","xotime;":"⨂","xrArr;":"⟹","xrarr;":"⟶","Xscr;":"𝒳","xscr;":"𝓍","xsqcup;":"⨆","xuplus;":"⨄","xutri;":"△","xvee;":"⋁","xwedge;":"⋀","Yacute":"Ý","yacute":"ý","Yacute;":"Ý","yacute;":"ý","YAcy;":"Я","yacy;":"я","Ycirc;":"Ŷ","ycirc;":"ŷ","Ycy;":"Ы","ycy;":"ы","yen":"¥","yen;":"¥","Yfr;":"𝔜","yfr;":"𝔶","YIcy;":"Ї","yicy;":"ї","Yopf;":"𝕐","yopf;":"𝕪","Yscr;":"𝒴","yscr;":"𝓎","YUcy;":"Ю","yucy;":"ю","yuml":"ÿ","Yuml;":"Ÿ","yuml;":"ÿ","Zacute;":"Ź","zacute;":"ź","Zcaron;":"Ž","zcaron;":"ž","Zcy;":"З","zcy;":"з","Zdot;":"Ż","zdot;":"ż","zeetrf;":"ℨ","ZeroWidthSpace;":"\u200b","Zeta;":"Ζ","zeta;":"ζ","Zfr;":"ℨ","zfr;":"𝔷","ZHcy;":"Ж","zhcy;":"ж","zigrarr;":"⇝","Zopf;":"ℤ","zopf;":"𝕫","Zscr;":"𝒵","zscr;":"𝓏","zwj;":"‍","zwnj;":"‌"}"####;

const INVALID_REF_DATA: &str = r####"{"0":"�","13":"\r","128":"€","129":"","130":"‚","131":"ƒ","132":"„","133":"…","134":"†","135":"‡","136":"ˆ","137":"‰","138":"Š","139":"‹","140":"Œ","141":"","142":"Ž","143":"","144":"","145":"‘","146":"’","147":"“","148":"”","149":"•","150":"–","151":"—","152":"˜","153":"™","154":"š","155":"›","156":"œ","157":"","158":"ž","159":"Ÿ"}"####;

const INVALID_POINT_DATA: &str = r####"[1,2,3,4,5,6,7,8,11,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,786430,1114111,327679,851967,720894,917502,131070,851966,655359,131071,917503,1114110,393215,983038,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,196607,720895,458751,983039,262143,524286,1048574,64976,64977,64978,64979,64980,64981,64982,64983,64984,64985,64986,64987,64988,64989,64990,64991,64992,64993,64994,64995,64996,64997,64998,786431,524287,1048575,64999,65000,65001,65002,65003,65004,65005,65006,65007,65534,655358,196606,262142,327678,589823,393214,458750,589822,65535]"####;

const RAW: &[&str] = &["script", "style", "xmp", "iframe", "noembed", "noframes"];

const RCDATA: &[&str] = &["textarea", "title"];
