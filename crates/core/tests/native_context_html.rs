//! Frozen HTMLParser data-run behavior; this never opens Apple Notes.
use localbrain_core::backend::contexts::scan::plain_text;
#[test]
fn native_notes_plaintext_matches_frozen_html_data_runs() {
    let fixtures: Vec<(String, String)> = serde_json::from_str(FIXTURES).unwrap();
    for (source, expected) in fixtures {
        assert_eq!(plain_text(&source).unwrap(), expected, "{source:?}");
    }
}
const FIXTURES: &str = r####"[["plain","plain"],["<p>A &amp; B</p><div>한글</div>","A & B\n한글"],["1 < 2 > 0","1\n<\n2 > 0"],["before<tag","before<tag"],["before<!--unfinished","before<!--unfinished"],["before&after>","before&after>"],["<script>let x = a < b; &amp;</script><p>end</p>","let x = a < b; &amp;\nend"],["<style>a>b &copy;</style>","a>b &copy;"],["<p>a<!--comment-->b</p>","a\nb"],["<p>a&bogus;b</p>","a&bogus;b"],["<p>a&#0;b</p>","a�b"],["<p>a&#xD800;b</p>","a�b"],["<p>a&#128;b</p>","a€b"],["<!DOCTYPE html>A","A"],["<?xml version=\"1\"?>body","body"],["<![CDATA[x < y]]>body","body"],["a <<b>c","a\n<\nc"],["<div title=\">\">x</div>","x"],["<div title=\"<>\">x</div>","x"],["<textarea>a<b>&amp;</textarea>","a<b>&"],["<title>a<b>&amp;</title>","a<b>&"],["before<","before<"],["<p> a\n b </p> c","a\n b\nc"],["<p>\u0000data</p>","\u0000data"],["<p>a</invalid b>c","a\nc"],["x<!bogus>y","x\ny"],["<p>a<?pi?>b","a\nb"],["<p>a</>b","a\nb"],["<p>a<3>b","a\n<\n3>b"],["<p>a &nbsp; b</p>","a   b"],["<p>a&#13;b</p>","a\rb"],["<p>a &copy b</p>","a © b"],["<p>a &unknown b</p>","a &unknown b"],["<p>a&notit;b</p>","a¬it;b"]]"####;
