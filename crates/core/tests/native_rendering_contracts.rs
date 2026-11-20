use localbrain_core::backend::{
    rendering::{highlight_code, references::*, render_markdown, MarkdownOptions},
    yaml::{safe_load, SafeYaml},
};
use serde_json::{json, Value};

fn document(id: i64, path: &str, title: &str, body: &str) -> MarkdownDocumentReference {
    MarkdownDocumentReference {
        id,
        context_root_id: 7,
        relative_path: path.into(),
        title: title.into(),
        body: body.into(),
        content_type: "text/markdown".into(),
    }
}
fn render(source: &str) -> String {
    render_markdown(source, &MarkdownOptions::default()).html
}
fn html_tree(html: &str) -> Value {
    fn shape(node: roxmltree::Node<'_, '_>) -> Value {
        if node.is_text() {
            return json!({"text": node.text().unwrap()});
        }
        json!({
            "tag": node.tag_name().name(),
            "attributes": node.attributes().map(|attr| (attr.name(), attr.value()))
                .collect::<std::collections::BTreeMap<_, _>>(),
            "children": node.children().filter(|node| node.is_text() || node.is_element())
                .map(shape).collect::<Vec<_>>(),
        })
    }
    let source = format!("<root>{html}</root>");
    shape(roxmltree::Document::parse(&source).unwrap().root_element())
}
#[test]
fn baseline_blocks_html_safety_and_nonfetching_images() {
    let source="# Heading\n\nFirst line\nsecond **strong**, *emphasis*, `inline`.\n\n- parent\n  - child\n\n1. first\n2. second\n\n> quoted\n\n| Name | Value |\n| --- | --- |\n| one | two |\n\n---\n\n[safe](https://example.test/path)";
    let html = render(source);
    for expected in [
        "<h1 id=\"heading-heading\">Heading</h1>",
        "First line<br />",
        "<strong>strong</strong>",
        "<em>emphasis</em>",
        "<code>inline</code>",
        "<ol>",
        "<blockquote>",
        "<div class=\"markdown-table-scroll\"><table>",
        "</table></div>",
        "<hr />",
        "href=\"https://example.test/path\"",
    ] {
        assert!(html.contains(expected), "missing {expected}: {html}");
    }
    assert!(html.matches("<ul>").count() >= 2);
    let hostile=render("<script>alert(\"x\")</script>\n\n<a href=\"https://example.test\" onclick=\"steal()\">raw</a>\n\n[script](javascript:alert(1)) [file](file:///tmp/private)");
    for forbidden in [
        "<script>",
        "href=\"javascript:",
        "href=\"file:",
        "<a href=\"https://example.test\" onclick=",
    ] {
        assert!(!hostile.contains(forbidden), "{hostile}");
    }
    assert!(hostile.contains("&lt;script&gt;"));
    assert!(hostile.contains("onclick=&quot;steal()&quot;"));
    assert!(hostile.contains("[script]"));
    let images=render("![Architecture **diagram**](https://example.test/private.png \"title\") ![Local](images/local.png)");
    assert_eq!(
        images
            .matches("data-markdown-image-deferred=\"true\"")
            .count(),
        2
    );
    assert!(images.contains("Architecture diagram"));
    for forbidden in ["<img", "src=", "private.png"] {
        assert!(!images.contains(forbidden));
    }
}
#[test]
fn explicit_route_admission_and_external_links() {
    let source="[admitted](/sessions/12) [other](/sessions/13) [escape](/sessions/../admin) [docs](/help/search)";
    assert!(!render(source).contains("href=\"/sessions/12\""));
    let options = MarkdownOptions {
        trusted_session_routes: ["/sessions/12".into(), "/admin".into()].into(),
        app_doc_routes: ["/help/search".into()].into(),
        app_doc_language: Some("ko"),
        ..Default::default()
    };
    let html = render_markdown(source, &options).html;
    assert!(html.contains("href=\"/sessions/12\""));
    assert!(!html.contains("href=\"/sessions/13\""));
    assert!(!html.contains("href=\"/admin\""));
    assert!(html.contains("href=\"/help/search?lang=ko\""));
    let external = render("[external](https://example.test/read)");
    assert!(external.contains("rel=\"noopener noreferrer external\""));
    assert!(!external.contains("prefetch"));
}
#[test]
fn code_uses_existing_css_roles_and_escaped_complete_fallback() {
    let html = render("```python\nprint(\"hello\")\n```");
    for expected in [
        "data-language=\"python\"",
        "Python</figcaption>",
        "class=\"language-python\"",
        "<span class=\"nb\">print</span>",
    ] {
        assert!(html.contains(expected), "missing {expected}: {html}");
    }
    assert!(!html.contains("style="));
    let unknown = render("```unknown<script>\n<a>& value\n```");
    assert!(unknown.contains("unknown&lt;script&gt;"));
    assert!(unknown.contains("&lt;a&gt;&amp; value"));
    assert!(!unknown.contains("<span class="));
    assert_eq!(highlight_code("\n<a>&\n", "unknown"), "\n&lt;a&gt;&amp;\n");
    let typescript = highlight_code("const amount: number = 42;\n", "typescript");
    assert!(typescript.contains("class=\"k\""), "{typescript}");
    assert!(typescript.contains("class=\"m\""), "{typescript}");
}

#[test]
fn code_literals_match_frozen_renderer() {
    let fixtures: Value =
        serde_json::from_str(include_str!("native_rendering_fixtures/code_literals.json")).unwrap();
    let mut differences = Vec::new();
    for case in fixtures["cases"].as_array().unwrap() {
        let name = case["name"].as_str().unwrap();
        let actual = render_markdown(case["source"].as_str().unwrap(), &Default::default());
        assert_eq!(actual.state, case["state"].as_str().unwrap(), "{name}");
        assert_eq!(
            serde_json::to_value(&actual.properties).unwrap(),
            case["properties"],
            "{name}"
        );
        // These two cases differ only in an existing quote-entity spelling or
        // anchor attribute order. Check every decoded text node and attribute.
        if matches!(
            name,
            "raw_html_in_generic_fence_info_and_code" | "inline_note_reference_context"
        ) {
            assert_eq!(
                html_tree(&actual.html),
                html_tree(case["html"].as_str().unwrap()),
                "{name}"
            );
            continue;
        }
        // Preserve the existing loose-list <li> newline serialization choice.
        let expected = case["html"]
            .as_str()
            .unwrap()
            .replace("<li>\n<p>", "<li><p>");
        if actual.html != expected {
            differences.push(format!(
                "{name}\nnative: {:?}\nbaseline: {:?}",
                actual.html, case["html"]
            ));
        }
    }
    assert!(differences.is_empty(), "{}", differences.join("\n\n"));
}

#[test]
fn html_disabled_parsing_preserves_autolinks_and_angle_destinations() {
    let fixtures: Value =
        serde_json::from_str(include_str!("native_rendering_fixtures/code_literals.json")).unwrap();
    for case in fixtures["html_links"].as_array().unwrap() {
        let html = render(case["source"].as_str().unwrap());
        // Attribute order already differs between the renderers. Compare every
        // tag, attribute and text node while retaining exact text whitespace.
        assert_eq!(
            html_tree(&html),
            html_tree(case["html"].as_str().unwrap()),
            "{}: {html}",
            case["name"]
        );
    }
}

#[test]
fn inline_footnotes_use_the_shared_local_inline_math_contract() {
    let fixtures: Value =
        serde_json::from_str(include_str!("native_rendering_fixtures/code_literals.json")).unwrap();
    for case in fixtures["math_cases"].as_array().unwrap() {
        let actual = render_markdown(case["source"].as_str().unwrap(), &Default::default());
        assert_eq!(actual.state, "ready");
        assert_eq!(actual.html.matches("class=\"markdown-math\"").count(), 1);
        assert!(actual.html.contains("<p>$<span class=\"markdown-math\">"));
        assert!(actual.html.contains("</span>$ <a href=\"#fnref1\""));
        let source = format!("<root>{}</root>", actual.html);
        let tree = roxmltree::Document::parse(&source).unwrap();
        let math = tree
            .descendants()
            .find(|node| node.has_tag_name(("http://www.w3.org/1998/Math/MathML", "math")))
            .unwrap();
        assert_eq!(math.attribute("display"), Some("inline"));
        assert!(math
            .descendants()
            .any(|node| node.tag_name().name() == "mi" && node.text() == Some("x")));
        assert!(!actual.html.contains("LOCALBRAINMARKER"));
        assert!(!actual.html.contains("<script"));
    }
}

#[test]
fn excessive_inline_note_depth_returns_complete_fallback_in_an_isolated_process() {
    let (status, output) = localbrain_core::process::run_status(
        std::process::Command::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "inline_note_depth_child",
                "--ignored",
                "--nocapture",
                "--test-threads=1",
            ])
            .env("LOCALBRAIN_NATIVE_INLINE_NOTE_DEPTH_CHILD", "1"),
        std::time::Duration::from_secs(20),
        16 * 1024,
    )
    .expect("isolated note-depth child must finish within twenty seconds and bounded output");
    assert!(
        status.success(),
        "child status={status}: {}",
        String::from_utf8_lossy(&output)
    );
    assert!(
        String::from_utf8_lossy(&output).contains("INLINE_NOTE_DEPTH_CHILD_COMPLETED"),
        "child did not execute its complete regression: {}",
        String::from_utf8_lossy(&output)
    );
}

#[test]
#[ignore = "invoked by the isolated twenty-second note-depth regression"]
fn inline_note_depth_child() {
    if std::env::var("LOCALBRAIN_NATIVE_INLINE_NOTE_DEPTH_CHILD").as_deref() != Ok("1") {
        return;
    }
    let ordinary = "Control ^[a **bold** note].\n";
    let before = render_markdown(ordinary, &Default::default());
    assert_eq!(before.state, "ready");
    assert!(before.html.contains("<strong>bold</strong>"));
    assert!(before.html.contains("class=\"footnotes\""));
    for depth in [16, 64, 65, 4096] {
        let source = format!("{}x{}", "^[".repeat(depth), "]".repeat(depth));
        assert_eq!(source.len(), 3 * depth + 1);
        let actual = render_markdown(&source, &Default::default());
        if depth <= 64 {
            assert_eq!(actual.state, "ready", "depth={depth}");
            assert!(actual.html.contains("class=\"footnotes\""), "depth={depth}");
        } else {
            assert_eq!(actual.state, "fallback", "depth={depth}");
            // This complete ASCII source needs no escaping. Compare the whole
            // response so a prefix-only or truncated fallback cannot pass.
            assert_eq!(
                actual.html,
                format!("<pre class=\"markdown-render-fallback\">{source}</pre>"),
                "depth={depth}"
            );
            assert!(actual.properties.is_empty());
        }
    }
    assert_eq!(render_markdown(ordinary, &Default::default()), before);
    assert_eq!(
        render("After **alive**."),
        "<p>After <strong>alive</strong>.</p>\n"
    );
    println!("INLINE_NOTE_DEPTH_CHILD_COMPLETED");
}

#[test]
fn inline_backtick_matching_stops_at_container_boundaries() {
    // The frozen renderer treats both backticks in each container as unmatched.
    // The first backtick belongs to the highlight's literal payload.
    for (name, source) in [
        (
            "nested_list",
            "- ==`literal== `[[Guide]]\n  - ==active== #outside/tag `\n",
        ),
        (
            "table_cells",
            "| ==`literal== `[[Guide]] | ==active== #outside/tag ` |\n| --- | --- |\n",
        ),
        (
            "footnote",
            "One[^n]\n\n[^n]: ==`literal== `[[Guide]]\n\n==active== #outside/tag `\n",
        ),
    ] {
        let html = render(source);
        assert!(!html.contains("LOCALBRAINMARKER"), "{name}: {html}");
        assert!(!html.contains("<code>"), "{name}: {html}");
        assert_eq!(html.matches("<mark>").count(), 2, "{name}: {html}");
        assert_eq!(
            html.matches("class=\"markdown-tag\"").count(),
            1,
            "{name}: {html}"
        );
        assert_eq!(
            html.matches("data-reference-state=\"no-source\"").count(),
            1,
            "{name}: {html}"
        );
    }
}

#[test]
fn repeated_consumed_backtick_openers_match_exact_runs_at_the_cursor() {
    // This whole expected HTML was also checked against the frozen renderer.
    // Varying lengths exercise exact matching rather than a backtick toggle.
    let mut source = Vec::new();
    let mut expected = Vec::new();
    for _ in 0..8 {
        for length in 1..=16 {
            let ticks = "`".repeat(length);
            source.push(format!(
                "=={ticks}literal== {ticks}[[Guide]] ==literal== #inside/tag{ticks} ==active=="
            ));
            expected.push(format!(
                "<mark>{ticks}literal</mark> <code>[[Guide]] ==literal== #inside/tag</code> <mark>active</mark>"
            ));
        }
    }
    assert_eq!(
        render(&(source.join("\n") + "\n")),
        format!("<p>{}</p>\n", expected.join("<br />\n"))
    );
}

#[test]
fn literal_code_does_not_expand_extensions_or_hide_following_prose() {
    let literal = "[[Guide]] ![[Guide]] ==literal== $x^2$ $$x$$ #local/tag <b>&";
    let escaped = "[[Guide]] ![[Guide]] ==literal== $x^2$ $$x$$ #local/tag &lt;b&gt;&amp;";
    let blocks = [
        format!("    {literal}\n"),
        format!("\t{literal}\n"),
        format!(">     {literal}\n"),
        format!("- item\n\n      {literal}\n"),
        format!("> ```\n> {literal}\n> ```\n"),
        format!("- item\n\n  ```\n  {literal}\n  ```\n"),
        format!("> - item\n>\n>   ```\n>   {literal}\n>   ```\n"),
        format!("````\n```\n{literal}\n```\n````\n"),
        format!("~~~~\n~~~\n{literal}\n```\n~~~~\n"),
        format!("`{literal}`\n"),
        format!("`` ` {literal} ` ``\n"),
    ];
    let context = MarkdownReferenceContext::from_documents(
        vec![
            document(1, "root.md", "Root", ""),
            document(2, "guide.md", "Guide", "Guide body"),
        ],
        1,
    )
    .unwrap();
    let options = MarkdownOptions {
        reference_context: Some(&context),
        ..Default::default()
    };
    for block in blocks {
        let source = format!(
            "---\ntitle: Code\n---\n%% hidden %%\n{block}\n[[Guide]] ==active== $x^2$ #outside/tag\n\n![[Guide]]\n"
        );
        let actual = render_markdown(&source, &options);
        assert_eq!(actual.state, "ready");
        assert_eq!(actual.properties[0].value, "Code");
        let html = actual.html;
        assert!(html.contains(escaped), "{block:?}: {html}");
        assert!(!html.contains("LOCALBRAINMARKER"), "{block:?}: {html}");
        assert!(!html.contains("hidden"), "{block:?}: {html}");
        assert_eq!(html.matches("<mark>").count(), 1, "{block:?}: {html}");
        assert!(html.contains("<mark>active</mark>"), "{block:?}: {html}");
        assert_eq!(
            html.matches("class=\"markdown-math\"").count(),
            1,
            "{block:?}: {html}"
        );
        assert_eq!(
            html.matches("class=\"markdown-tag\"").count(),
            1,
            "{block:?}: {html}"
        );
        assert!(
            html.contains("data-tag=\"outside/tag\""),
            "{block:?}: {html}"
        );
        assert_eq!(
            html.matches("class=\"markdown-note-embed\"").count(),
            1,
            "{block:?}: {html}"
        );
        assert!(
            html.contains("href=\"/documents/2\">Guide</a>"),
            "{block:?}: {html}"
        );
        assert!(html.contains("Guide body"), "{block:?}: {html}");
    }
}

#[test]
fn aligned_tables_and_reused_footnotes_keep_structure() {
    let table = render("| Center | Right |\n| :---: | ---: |\n| one | two |\n");
    assert_eq!(table.matches("style=\"text-align:center\"").count(), 2);
    assert_eq!(table.matches("style=\"text-align:right\"").count(), 2);
    let footnotes = render("One[^a] and two[^a].\n\n[^a]: A note\n");
    assert!(footnotes.contains("id=\"fnref1\""));
    assert!(footnotes.contains("id=\"fnref1:1\""));
    assert!(footnotes.contains("href=\"#fnref1:1\""));
    assert!(footnotes.contains("[1:1]"));
}
#[test]
fn obsidian_authoring_is_read_only_and_safe() {
    let source="- [ ] open\n  - [x] done\n\n~~removed~~ ==important== #local/tag [^note]\n\n%% hidden text %%visible and `%%code%%`\n\n> [!warning] Read first\n> Callout **body**\n\n[^note]: Footnote\n";
    let html = render(source);
    assert_eq!(html.matches("type=\"checkbox\"").count(), 2);
    assert_eq!(html.matches("disabled=\"disabled\"").count(), 2);
    for expected in [
        "<s>removed</s>",
        "<mark>important</mark>",
        "data-tag=\"local/tag\"",
        "class=\"markdown-callout markdown-callout-warning\"",
        "class=\"markdown-callout-title\">Read first",
        "class=\"footnotes\"",
        "%%code%%",
    ] {
        assert!(html.contains(expected), "missing {expected}: {html}");
    }
    assert!(!html.contains("hidden text"));
    assert!(render("==**literal**==").contains("<mark>**literal**</mark>"));
}
#[test]
fn frontmatter_properties_are_ordered_and_bad_yaml_stays_readable() {
    let valid = render_markdown(
        "---\ntitle: Demo\ntags: [one, two]\npublished: true\n---\n# Body",
        &Default::default(),
    );
    assert_eq!(
        valid
            .properties
            .iter()
            .map(|item| (item.name.as_str(), item.value.as_str()))
            .collect::<Vec<_>>(),
        vec![
            ("title", "Demo"),
            ("tags", "[one, two]"),
            ("published", "true")
        ]
    );
    assert!(!valid.html.contains("title: Demo"));
    let invalid = render_markdown("---\ntitle: [broken\n---\nBody", &Default::default());
    assert!(invalid.properties.is_empty());
    assert!(invalid.html.contains("title: [broken"));
    assert!(invalid.html.contains("Body"));
    let nonstring = render_markdown("---\nyes: value\n---\nBody", &Default::default());
    assert!(nonstring.properties.is_empty());
    assert!(nonstring.html.contains("yes: value"));
    let empty = render_markdown("", &Default::default());
    assert_eq!((empty.state.as_str(), empty.html.as_str()), ("empty", ""));
}
#[test]
fn math_is_local_validated_and_has_same_line_delimiters() {
    let html = render("Inline $x^2$ and block:\n\n$$\\frac{1}{2}$$");
    assert!(html.contains("<math"), "{html}");
    assert!(html.contains("display=\"inline\""));
    assert!(html.contains("display=\"block\""));
    assert!(!html.contains("script"));
    let multiline = render("Inline $x^2$ remains math.\nBroken $x +\ny$ stays text.");
    assert_eq!(multiline.matches("markdown-math").count(), 1);
    assert!(multiline.contains("Broken $x +"));
    assert!(multiline.contains("y$ stays text."));
    let stack="at io.grpc.ClientCallImpl$ClientStreamListenerImpl$1StreamClosed.runInternal(ClientCallImpl.java:744)\nat io.grpc.ClientCallImpl$ClientStreamListenerImpl$1StreamClosed.runInContext(ClientCallImpl.java:723)";
    let html = render(stack);
    assert!(!html.contains("markdown-math"));
    assert_eq!(html.matches("<br />").count(), 1);
    let hostile = render(r"$\text{<script>alert(1)</script>}$");
    assert!(hostile.contains("markdown-math-fallback"), "{hostile}");
    assert!(!hostile.contains("<script>"));
    assert!(hostile.contains("&lt;script&gt;"));
    let nested = render("> $$\n> x^2\n> $$\n");
    assert!(nested.contains("display=\"block\""), "{nested}");
    assert!(!nested.contains("markdown-math-fallback"), "{nested}");
}
#[test]
fn document_references_resolve_only_inside_one_root() {
    let context = MarkdownReferenceContext::from_documents(
        vec![
            document(1, "notes/current.md", "Current", "# Current\n\nText ^here"),
            document(
                2,
                "guide.md",
                "Guide",
                "# Guide\n\n## Part\n\nDetails ^detail",
            ),
            document(3, "one/shared.md", "Shared One", ""),
            document(4, "two/shared.md", "Shared Two", ""),
        ],
        1,
    )
    .unwrap();
    assert_eq!(
        context
            .resolve("../guide.md#Part", "markdown")
            .href
            .as_deref(),
        Some("/documents/2#heading-part")
    );
    assert_eq!(
        context.resolve("guide#^detail", "wiki").href.as_deref(),
        Some("/documents/2#block-detail")
    );
    for (target, kind, state) in [
        ("shared", "wiki", "ambiguous"),
        ("guide#Absent", "wiki", "missing"),
        ("../../secret.md", "markdown", "unsafe"),
        ("%2e%2e/%2e%2e/secret.md", "markdown", "unsafe"),
        ("%252e%252e/%252e%252e/secret.md", "markdown", "unsafe"),
        ("file:///tmp/private", "wiki", "unsafe"),
    ] {
        assert_eq!(context.resolve(target, kind).state, state);
    }
    let html=render_markdown("[[guide#Part|Guide part]] [[shared]] [[missing]] [relative](../guide.md#Part) [outside](../../private.md)",&MarkdownOptions{reference_context:Some(&context),..Default::default()}).html;
    for expected in [
        "href=\"/documents/2#heading-part\">Guide part",
        "data-reference-state=\"ambiguous\">shared",
        "data-reference-state=\"missing\">missing",
        "data-reference-state=\"unsafe\">outside",
    ] {
        assert!(html.contains(expected), "missing {expected}: {html}");
    }
    assert_eq!(
        render("[[guide]] [relative](guide.md)")
            .matches("data-reference-state=\"no-source\"")
            .count(),
        2
    );
}
#[test]
fn stable_anchors_keep_python_unicode_word_semantics() {
    assert_eq!(heading_slug("  Ａ Café_ΟΣ!  "), "a-café-ος");
    assert_eq!(heading_slug("a\u{0301} x\u{0345} ² Ⅷ"), "á-x-2-viii");
    let source = "# Same\n\n# Same\n\nParagraph ^piece\n\n[[#Same|wiki]] [markdown](#^piece)";
    let html = render(source);
    for expected in [
        "id=\"heading-same\"",
        "id=\"heading-same-2\"",
        "id=\"block-piece\"",
        "href=\"#heading-same\">wiki</a>",
        "href=\"#block-piece\"",
    ] {
        assert!(html.contains(expected), "missing {expected}: {html}");
    }
    assert!(!html.contains("^piece"));
    let indexed = "# Same\n\nFirst\n\n# Same\n\n## Part\n\nBody ^piece\n\n# Next";
    assert_eq!(
        extract_document_fragment(indexed, Some("Part")).as_deref(),
        Some("## Part\n\nBody ^piece")
    );
    assert_eq!(
        extract_document_fragment(indexed, Some("^piece")).as_deref(),
        Some("Body")
    );
    let context = MarkdownReferenceContext::from_documents(
        vec![
            document(1, "root.md", "Root", ""),
            document(2, "Straße.md", "Straße", ""),
        ],
        1,
    )
    .unwrap();
    assert_eq!(context.resolve("STRASSE", "wiki").state, "resolved");
}
#[test]
fn note_embeds_select_fragments_and_bound_cycles_depth_and_attachments() {
    let context = MarkdownReferenceContext::from_documents(
        vec![
            document(1, "root.md", "Root", "# Root"),
            document(
                2,
                "target.md",
                "Target",
                "# Target\n\n## Part\n\nSelected ^piece\n\n## Other\n\nNot selected",
            ),
            document(3, "cycle-a.md", "Cycle A", "![[Cycle B]]"),
            document(4, "cycle-b.md", "Cycle B", "![[Cycle A]]"),
            document(5, "depth-a.md", "Depth A", "![[Depth B]]"),
            document(6, "depth-b.md", "Depth B", "![[Depth C]]"),
            document(7, "depth-c.md", "Depth C", "![[Depth D]]"),
            document(8, "depth-d.md", "Depth D", "![[Target]]"),
        ],
        1,
    )
    .unwrap();
    let options = MarkdownOptions {
        reference_context: Some(&context),
        ..Default::default()
    };
    let selected = render_markdown("![[Target#Part]]", &options).html;
    assert!(selected.contains("class=\"markdown-note-embed\""));
    assert!(selected.contains("Selected"));
    assert!(!selected.contains("Not selected"));
    let block = render_markdown("![[Target#^piece]]", &options).html;
    assert!(block.contains("Selected"));
    assert!(!block.contains("## Part"));
    assert!(render_markdown("![[Cycle A]]", &options)
        .html
        .contains("data-reference-state=\"cycle\""));
    assert!(render_markdown("![[Depth A]]", &options)
        .html
        .contains("data-reference-state=\"depth-limit\""));
    let attachment = render_markdown("![[assets/photo.png]]", &options).html;
    assert!(attachment.contains("Attachment deferred"));
    assert!(!attachment.contains("<img"));
    assert!(!attachment.contains("src="));
}

fn descriptor(value: &SafeYaml) -> Value {
    match value {
        SafeYaml::Null => json!(["null"]),
        SafeYaml::Boolean(value) => json!(["bool", value]),
        SafeYaml::Integer(value) => json!(["int", value]),
        SafeYaml::Real(_) => json!(["float", value.property_value()]),
        SafeYaml::String(value) => json!(["str", value]),
        SafeYaml::Date(value) => json!(["date", value]),
        SafeYaml::Timestamp(value) => json!(["timestamp", value]),
        SafeYaml::Sequence(values) => {
            json!(["seq", values.iter().map(descriptor).collect::<Vec<_>>()])
        }
        SafeYaml::Mapping(values) => json!([
            "map",
            values
                .iter()
                .map(|(key, value)| json!([descriptor(key), descriptor(value)]))
                .collect::<Vec<_>>()
        ]),
        _ => panic!("not in these scalar fixtures"),
    }
}
#[test]
fn yaml_matches_frozen_pyyaml_603_safe_loader_fixtures() {
    // Generated from the repository's Python3.11/PyYAML6.0.3 SafeLoader using
    // synthetic source only. Expected types preserve quote/date distinctions.
    let fixtures = [
        (
            "plain: yes\nquoted: \"yes\"\nupper: ON\nword: y\nlist: [no, \"off\", true, null]\n",
            json!([
                "map",
                [
                    [["str", "plain"], ["bool", true]],
                    [["str", "quoted"], ["str", "yes"]],
                    [["str", "upper"], ["bool", true]],
                    [["str", "word"], ["str", "y"]],
                    [
                        ["str", "list"],
                        [
                            "seq",
                            [["bool", false], ["str", "off"], ["bool", true], ["null"]]
                        ]
                    ]
                ]
            ]),
            "{plain: true, quoted: yes, upper: true, word: y, list: [false, off, true, null]}",
        ),
        (
            "day: 2020-01-02\nquoted: \"2020-01-02\"\nwhen: 2020-1-2 3:04:05.12 +9:00\n",
            json!([
                "map",
                [
                    [["str", "day"], ["date", "2020-01-02"]],
                    [["str", "quoted"], ["str", "2020-01-02"]],
                    [
                        ["str", "when"],
                        ["timestamp", "2020-01-02T03:04:05.120000+09:00"]
                    ]
                ]
            ]),
            "{day: 2020-01-02, quoted: 2020-01-02, when: 2020-01-02T03:04:05.120000+09:00}",
        ),
        (
            "octal: 012\nhex: 0xA\nsexagesimal: 1:20\nexponent: 1e3\nfloat: 1.0e+3\n",
            json!([
                "map",
                [
                    [["str", "octal"], ["int", "10"]],
                    [["str", "hex"], ["int", "10"]],
                    [["str", "sexagesimal"], ["int", "80"]],
                    [["str", "exponent"], ["str", "1e3"]],
                    [["str", "float"], ["float", "1000.0"]]
                ]
            ]),
            "{octal: 10, hex: 10, sexagesimal: 80, exponent: 1e3, float: 1000.0}",
        ),
        (
            "yes: first\ntrue: second\n1: third\n\"yes\": text\n",
            json!([
                "map",
                [
                    [["bool", true], ["str", "third"]],
                    [["str", "yes"], ["str", "text"]]
                ]
            ]),
            "{True: third, yes: text}",
        ),
        (
            "forced: !!str yes\nboolean: !!bool YEs\n",
            json!([
                "map",
                [
                    [["str", "forced"], ["str", "yes"]],
                    [["str", "boolean"], ["bool", true]]
                ]
            ]),
            "{forced: yes, boolean: true}",
        ),
    ];
    for (source, expected, display) in fixtures {
        let native = safe_load(source).unwrap();
        assert_eq!(descriptor(&native), expected, "{source}");
        assert_eq!(native.property_value(), display);
    }
    let aliased =
        safe_load("base: &b {x: yes, label: \"yes\"}\nmerged: {<<: *b, x: no}\ncopy: *b\n")
            .unwrap();
    assert_eq!(aliased.property_value(),"{base: {x: true, label: yes}, merged: {x: false, label: yes}, copy: {x: true, label: yes}}");
    let blocks = safe_load("literal: |\n  yes\n  2020-01-01\nfolded: >\n  one\n  two\n").unwrap();
    assert_eq!(
        blocks.property_value(),
        "{literal: yes\n2020-01-01\n, folded: one two\n}"
    );
    for source in [
        "!!python/object/apply:os.system [echo unsafe]",
        "!unknown value",
        "---\na: 1\n---\nb: 2\n",
    ] {
        assert!(safe_load(source).is_err());
    }
    // SafeLoader permits recursive collections. Unrelated scalar selection
    // still works; finite Markdown properties leave a cyclic source readable.
    let recursive = safe_load("name: safe-name\nrecursive: &self [*self]\n").unwrap();
    assert_eq!(
        recursive.get("name").and_then(SafeYaml::as_str),
        Some("safe-name")
    );
    assert!(recursive.has_recursive_alias());
    let cyclic = render_markdown(
        "---\nname: safe-name\nrecursive: &self [*self]\n---\nBody",
        &Default::default(),
    );
    assert!(cyclic.properties.is_empty());
    assert!(cyclic.html.contains("safe-name"));
    assert_eq!(safe_load("! yes").unwrap(), SafeYaml::Boolean(true));
    assert_eq!(
        safe_load("!!timestamp 2020-1-2").unwrap(),
        SafeYaml::Date("2020-01-02".into())
    );
    assert_eq!(
        safe_load("2020-1-2").unwrap(),
        SafeYaml::String("2020-1-2".into())
    );
    assert_eq!(
        safe_load("=: value")
            .unwrap()
            .get("=")
            .and_then(SafeYaml::as_str),
        Some("value")
    );
    for source in ["name: =", "name: ok\nother: <<", "[=]", "<<"] {
        assert!(safe_load(source).is_err(), "{source}");
    }
}
