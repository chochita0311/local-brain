//! Complete native start/end/data observations from the frozen Python HTMLParser.
use localbrain_core::backend::{
    html::{self, Finish, Visitor},
    Result,
};
use serde_json::{json, Value};
struct Events(Vec<Value>);
impl Visitor for Events {
    fn start(&mut self, tag: &str, attrs: &[(String, Option<String>)]) -> Result<()> {
        self.0.push(json!(["start", tag, attrs]));
        Ok(())
    }
    fn end(&mut self, tag: &str) -> Result<()> {
        self.0.push(json!(["end", tag]));
        Ok(())
    }
    fn data(&mut self, text: &str) -> Result<()> {
        self.0.push(json!(["data", text]));
        Ok(())
    }
}
#[test]
fn shared_html_events_match_frozen_feed_close_attributes_raw_text_and_entities() {
    let cases: Vec<Value> = serde_json::from_str(CASES).unwrap();
    assert_eq!(cases.len(), CASE_COUNT);
    for case in cases {
        let mut events = Events(vec![]);
        html::visit(
            case["source"].as_str().unwrap(),
            if case["close"] == true {
                Finish::Close
            } else {
                Finish::Feed
            },
            &mut events,
        )
        .unwrap();
        assert_eq!(
            json!(events.0),
            case["events"],
            "{} close={}",
            case["source"],
            case["close"]
        );
    }
}
const CASE_COUNT: usize = 124;
const CASES: &str = r####"[
{"source":"plain","close":false,"events":[["data","plain"]]},
{"source":"plain","close":true,"events":[["data","plain"]]},
{"source":"<p>A &amp; B</p><div>한글</div>","close":false,"events":[["start","p",[]],["data","A & B"],["end","p"],["start","div",[]],["data","한글"],["end","div"]]},
{"source":"<p>A &amp; B</p><div>한글</div>","close":true,"events":[["start","p",[]],["data","A & B"],["end","p"],["start","div",[]],["data","한글"],["end","div"]]},
{"source":"1 < 2 > 0","close":false,"events":[["data","1 "],["data","<"],["data"," 2 > 0"]]},
{"source":"1 < 2 > 0","close":true,"events":[["data","1 "],["data","<"],["data"," 2 > 0"]]},
{"source":"before<tag","close":false,"events":[["data","before"]]},
{"source":"before<tag","close":true,"events":[["data","before"]]},
{"source":"before<!--unfinished","close":false,"events":[["data","before"]]},
{"source":"before<!--unfinished","close":true,"events":[["data","before"]]},
{"source":"before&after>","close":false,"events":[]},
{"source":"before&after>","close":true,"events":[["data","before&after>"]]},
{"source":"<script>let x = a < b; &amp;</script><p>end</p>","close":false,"events":[["start","script",[]],["data","let x = a < b; &amp;"],["end","script"],["start","p",[]],["data","end"],["end","p"]]},
{"source":"<script>let x = a < b; &amp;</script><p>end</p>","close":true,"events":[["start","script",[]],["data","let x = a < b; &amp;"],["end","script"],["start","p",[]],["data","end"],["end","p"]]},
{"source":"<style>a>b &copy;</style>","close":false,"events":[["start","style",[]],["data","a>b &copy;"],["end","style"]]},
{"source":"<style>a>b &copy;</style>","close":true,"events":[["start","style",[]],["data","a>b &copy;"],["end","style"]]},
{"source":"<p>a<!--comment-->b</p>","close":false,"events":[["start","p",[]],["data","a"],["data","b"],["end","p"]]},
{"source":"<p>a<!--comment-->b</p>","close":true,"events":[["start","p",[]],["data","a"],["data","b"],["end","p"]]},
{"source":"<p>a&bogus;b</p>","close":false,"events":[["start","p",[]],["data","a&bogus;b"],["end","p"]]},
{"source":"<p>a&bogus;b</p>","close":true,"events":[["start","p",[]],["data","a&bogus;b"],["end","p"]]},
{"source":"<p>a&#0;b</p>","close":false,"events":[["start","p",[]],["data","a�b"],["end","p"]]},
{"source":"<p>a&#0;b</p>","close":true,"events":[["start","p",[]],["data","a�b"],["end","p"]]},
{"source":"<p>a&#xD800;b</p>","close":false,"events":[["start","p",[]],["data","a�b"],["end","p"]]},
{"source":"<p>a&#xD800;b</p>","close":true,"events":[["start","p",[]],["data","a�b"],["end","p"]]},
{"source":"<p>a&#128;b</p>","close":false,"events":[["start","p",[]],["data","a€b"],["end","p"]]},
{"source":"<p>a&#128;b</p>","close":true,"events":[["start","p",[]],["data","a€b"],["end","p"]]},
{"source":"<!DOCTYPE html>A","close":false,"events":[["data","A"]]},
{"source":"<!DOCTYPE html>A","close":true,"events":[["data","A"]]},
{"source":"<?xml version=\"1\"?>body","close":false,"events":[["data","body"]]},
{"source":"<?xml version=\"1\"?>body","close":true,"events":[["data","body"]]},
{"source":"<![CDATA[x < y]]>body","close":false,"events":[["data","body"]]},
{"source":"<![CDATA[x < y]]>body","close":true,"events":[["data","body"]]},
{"source":"a <<b>c","close":false,"events":[["data","a "],["data","<"],["start","b",[]],["data","c"]]},
{"source":"a <<b>c","close":true,"events":[["data","a "],["data","<"],["start","b",[]],["data","c"]]},
{"source":"<div title=\">\">x</div>","close":false,"events":[["start","div",[["title",">"]]],["data","x"],["end","div"]]},
{"source":"<div title=\">\">x</div>","close":true,"events":[["start","div",[["title",">"]]],["data","x"],["end","div"]]},
{"source":"<div title=\"<>\">x</div>","close":false,"events":[["start","div",[["title","<>"]]],["data","x"],["end","div"]]},
{"source":"<div title=\"<>\">x</div>","close":true,"events":[["start","div",[["title","<>"]]],["data","x"],["end","div"]]},
{"source":"<textarea>a<b>&amp;</textarea>","close":false,"events":[["start","textarea",[]],["data","a<b>&"],["end","textarea"]]},
{"source":"<textarea>a<b>&amp;</textarea>","close":true,"events":[["start","textarea",[]],["data","a<b>&"],["end","textarea"]]},
{"source":"<title>a<b>&amp;</title>","close":false,"events":[["start","title",[]],["data","a<b>&"],["end","title"]]},
{"source":"<title>a<b>&amp;</title>","close":true,"events":[["start","title",[]],["data","a<b>&"],["end","title"]]},
{"source":"before<","close":false,"events":[["data","before"]]},
{"source":"before<","close":true,"events":[["data","before"],["data","<"]]},
{"source":"<p> a\n b </p> c","close":false,"events":[["start","p",[]],["data"," a\n b "],["end","p"],["data"," c"]]},
{"source":"<p> a\n b </p> c","close":true,"events":[["start","p",[]],["data"," a\n b "],["end","p"],["data"," c"]]},
{"source":"<p>\u0000data</p>","close":false,"events":[["start","p",[]],["data","\u0000data"],["end","p"]]},
{"source":"<p>\u0000data</p>","close":true,"events":[["start","p",[]],["data","\u0000data"],["end","p"]]},
{"source":"<p>a</invalid b>c","close":false,"events":[["start","p",[]],["data","a"],["end","invalid"],["data","c"]]},
{"source":"<p>a</invalid b>c","close":true,"events":[["start","p",[]],["data","a"],["end","invalid"],["data","c"]]},
{"source":"x<!bogus>y","close":false,"events":[["data","x"],["data","y"]]},
{"source":"x<!bogus>y","close":true,"events":[["data","x"],["data","y"]]},
{"source":"<p>a<?pi?>b","close":false,"events":[["start","p",[]],["data","a"],["data","b"]]},
{"source":"<p>a<?pi?>b","close":true,"events":[["start","p",[]],["data","a"],["data","b"]]},
{"source":"<p>a</>b","close":false,"events":[["start","p",[]],["data","a"],["data","b"]]},
{"source":"<p>a</>b","close":true,"events":[["start","p",[]],["data","a"],["data","b"]]},
{"source":"<p>a<3>b","close":false,"events":[["start","p",[]],["data","a"],["data","<"],["data","3>b"]]},
{"source":"<p>a<3>b","close":true,"events":[["start","p",[]],["data","a"],["data","<"],["data","3>b"]]},
{"source":"<p>a &nbsp; b</p>","close":false,"events":[["start","p",[]],["data","a   b"],["end","p"]]},
{"source":"<p>a &nbsp; b</p>","close":true,"events":[["start","p",[]],["data","a   b"],["end","p"]]},
{"source":"<p>a&#13;b</p>","close":false,"events":[["start","p",[]],["data","a\rb"],["end","p"]]},
{"source":"<p>a&#13;b</p>","close":true,"events":[["start","p",[]],["data","a\rb"],["end","p"]]},
{"source":"<p>a &copy b</p>","close":false,"events":[["start","p",[]],["data","a © b"],["end","p"]]},
{"source":"<p>a &copy b</p>","close":true,"events":[["start","p",[]],["data","a © b"],["end","p"]]},
{"source":"<p>a &unknown b</p>","close":false,"events":[["start","p",[]],["data","a &unknown b"],["end","p"]]},
{"source":"<p>a &unknown b</p>","close":true,"events":[["start","p",[]],["data","a &unknown b"],["end","p"]]},
{"source":"<p>a&notit;b</p>","close":false,"events":[["start","p",[]],["data","a¬it;b"],["end","p"]]},
{"source":"<p>a&notit;b</p>","close":true,"events":[["start","p",[]],["data","a¬it;b"],["end","p"]]},
{"source":"","close":false,"events":[]},
{"source":"","close":true,"events":[]},
{"source":"one &copy","close":false,"events":[]},
{"source":"one &copy","close":true,"events":[["data","one ©"]]},
{"source":"one &","close":false,"events":[]},
{"source":"one &","close":true,"events":[["data","one &"]]},
{"source":"<p>one</p><","close":false,"events":[["start","p",[]],["data","one"],["end","p"]]},
{"source":"<p>one</p><","close":true,"events":[["start","p",[]],["data","one"],["end","p"],["data","<"]]},
{"source":"<p>one</p></","close":false,"events":[["start","p",[]],["data","one"],["end","p"]]},
{"source":"<p>one</p></","close":true,"events":[["start","p",[]],["data","one"],["end","p"],["data","</"]]},
{"source":"<p>one</p><unclosed","close":false,"events":[["start","p",[]],["data","one"],["end","p"]]},
{"source":"<p>one</p><unclosed","close":true,"events":[["start","p",[]],["data","one"],["end","p"]]},
{"source":"<script>unterminated < &amp;","close":false,"events":[["start","script",[]]]},
{"source":"<script>unterminated < &amp;","close":true,"events":[["start","script",[]],["data","unterminated < &amp;"]]},
{"source":"<textarea>unterminated &copy","close":false,"events":[["start","textarea",[]]]},
{"source":"<textarea>unterminated &copy","close":true,"events":[["start","textarea",[]],["data","unterminated ©"]]},
{"source":"<plaintext>a<b>&amp;</plaintext>","close":false,"events":[["start","plaintext",[]],["data","a<b>&amp;</plaintext>"]]},
{"source":"<plaintext>a<b>&amp;</plaintext>","close":true,"events":[["start","plaintext",[]],["data","a<b>&amp;</plaintext>"]]},
{"source":"<p a b=\"A &amp; B\" c=unquoted d='x&#13;y' disabled></p>","close":false,"events":[["start","p",[["a",null],["b","A & B"],["c","unquoted"],["d","x\ry"],["disabled",null]]],["end","p"]]},
{"source":"<p a b=\"A &amp; B\" c=unquoted d='x&#13;y' disabled></p>","close":true,"events":[["start","p",[["a",null],["b","A & B"],["c","unquoted"],["d","x\ry"],["disabled",null]]],["end","p"]]},
{"source":"<div A=\"\" A=z data-한글=\"ß\">text</div>","close":false,"events":[["start","div",[["a",""],["a","z"],["data-한글","ß"]]],["data","text"],["end","div"]]},
{"source":"<div A=\"\" A=z data-한글=\"ß\">text</div>","close":true,"events":[["start","div",[["a",""],["a","z"],["data-한글","ß"]]],["data","text"],["end","div"]]},
{"source":"<script/><p>after</p>","close":false,"events":[["start","script",[]],["end","script"],["start","p",[]],["data","after"],["end","p"]]},
{"source":"<script/><p>after</p>","close":true,"events":[["start","script",[]],["end","script"],["start","p",[]],["data","after"],["end","p"]]},
{"source":"<form><div>x</div></form><p>after</p>","close":false,"events":[["start","form",[]],["start","div",[]],["data","x"],["end","div"],["end","form"],["start","p",[]],["data","after"],["end","p"]]},
{"source":"<form><div>x</div></form><p>after</p>","close":true,"events":[["start","form",[]],["start","div",[]],["data","x"],["end","div"],["end","form"],["start","p",[]],["data","after"],["end","p"]]},
{"source":"<style/ >x</style>","close":false,"events":[["start","style",[]],["data","x"],["end","style"]]},
{"source":"<style/ >x</style>","close":true,"events":[["start","style",[]],["data","x"],["end","style"]]},
{"source":"<p a=\"unterminated>body","close":false,"events":[]},
{"source":"<p a=\"unterminated>body","close":true,"events":[]},
{"source":"<p a=abc/>tail","close":false,"events":[["start","p",[["a","abc/"]]],["data","tail"]]},
{"source":"<p a=abc/>tail","close":true,"events":[["start","p",[["a","abc/"]]],["data","tail"]]},
{"source":"<p a=abc />tail","close":false,"events":[["start","p",[["a","abc"]]],["end","p"],["data","tail"]]},
{"source":"<p a=abc />tail","close":true,"events":[["start","p",[["a","abc"]]],["end","p"],["data","tail"]]},
{"source":"</tag a=\"value\">","close":false,"events":[["end","tag"]]},
{"source":"</tag a=\"value\">","close":true,"events":[["end","tag"]]},
{"source":"<p><!--unfinished","close":false,"events":[["start","p",[]]]},
{"source":"<p><!--unfinished","close":true,"events":[["start","p",[]]]},
{"source":"<p><![CDATA[unfinished","close":false,"events":[["start","p",[]]]},
{"source":"<p><![CDATA[unfinished","close":true,"events":[["start","p",[]]]},
{"source":"<p><?unfinished","close":false,"events":[["start","p",[]]]},
{"source":"<p><?unfinished","close":true,"events":[["start","p",[]]]},
{"source":"<p><!DOCTYPE unfinished","close":false,"events":[["start","p",[]]]},
{"source":"<p><!DOCTYPE unfinished","close":true,"events":[["start","p",[]]]},
{"source":"<p><!bogus unfinished","close":false,"events":[["start","p",[]]]},
{"source":"<p><!bogus unfinished","close":true,"events":[["start","p",[]]]},
{"source":"<p></ bad>tail","close":false,"events":[["start","p",[]],["data","tail"]]},
{"source":"<p></ bad>tail","close":true,"events":[["start","p",[]],["data","tail"]]},
{"source":"<p>\u001cdata\u001f</p>","close":false,"events":[["start","p",[]],["data","\u001cdata\u001f"],["end","p"]]},
{"source":"<p>\u001cdata\u001f</p>","close":true,"events":[["start","p",[]],["data","\u001cdata\u001f"],["end","p"]]},
{"source":"<noscript><p>visible</p></noscript>","close":false,"events":[["start","noscript",[]],["start","p",[]],["data","visible"],["end","p"],["end","noscript"]]},
{"source":"<noscript><p>visible</p></noscript>","close":true,"events":[["start","noscript",[]],["start","p",[]],["data","visible"],["end","p"],["end","noscript"]]},
{"source":"<iframe>raw <p>&amp;</iframe>","close":false,"events":[["start","iframe",[]],["data","raw <p>&amp;"],["end","iframe"]]},
{"source":"<iframe>raw <p>&amp;</iframe>","close":true,"events":[["start","iframe",[]],["data","raw <p>&amp;"],["end","iframe"]]},
{"source":"<noembed>x<b>&amp;</noembed>","close":false,"events":[["start","noembed",[]],["data","x<b>&amp;"],["end","noembed"]]},
{"source":"<noembed>x<b>&amp;</noembed>","close":true,"events":[["start","noembed",[]],["data","x<b>&amp;"],["end","noembed"]]}
]"####;
