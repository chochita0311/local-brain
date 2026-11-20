use localbrain_core::backend::references::normalize_atlassian_catalog_url;
use serde_json::{json, Value};
#[test]
fn manual_atlassian_urls_match_frozen_query_and_idna_policy() {
    let userinfo_url = format!("http://{}:{}@{}/", "user", "password", "example.test");
    let cases: Value =
        serde_json::from_str(&CASES.replace("__SYNTHETIC_USERINFO_URL__", &userinfo_url)).unwrap();
    for case in cases.as_array().unwrap() {
        let url = case["url"].as_str().unwrap();
        let result = match normalize_atlassian_catalog_url(url) {
            Ok(url) => serde_json::to_value(url).unwrap(),
            Err(error) => json!({"code":error.code,"message":error.message}),
        };
        assert_eq!(result, case["expected"], "{url:?}");
    }
}
const CASES: &str = r########"[{"url":"https://EXAMPLE.test:443/wiki/pages/?z=2&a=1&a=&space=A+B#x","expected":{"observed_url":"https://EXAMPLE.test:443/wiki/pages/?z=2&a=1&a=&space=A+B#x","normalized_url":"https://example.test/wiki/pages?a=&a=1&space=A+B&z=2","normalized_domain":"example.test","canonical_base_url":"https://example.test"}},{"url":"\u001chttps://bücher.test/a///?z=%FF&a=%zz\u001c","expected":{"observed_url":"https://bücher.test/a///?z=%FF&a=%zz","normalized_url":"https://xn--bcher-kva.test/a?a=%25zz&z=%EF%BF%BD","normalized_domain":"xn--bcher-kva.test","canonical_base_url":"https://xn--bcher-kva.test"}},{"url":"https://EXAMPLE.test.../","expected":{"observed_url":"https://EXAMPLE.test.../","normalized_url":"https://example.test/","normalized_domain":"example.test","canonical_base_url":"https://example.test"}},{"url":"http://127.1:80/","expected":{"observed_url":"http://127.1:80/","normalized_url":"http://127.1/","normalized_domain":"127.1","canonical_base_url":"http://127.1"}},{"url":"https://[::1]:443/","expected":{"observed_url":"https://[::1]:443/","normalized_url":"https://::1/","normalized_domain":"::1","canonical_base_url":"https://::1"}},{"url":"https://foo./","expected":{"observed_url":"https://foo./","normalized_url":"https://foo/","normalized_domain":"foo","canonical_base_url":"https://foo"}},{"url":"https://./","expected":{"code":"invalid-url","message":"Atlassian URL domain is empty"}},{"url":"https://example.test/a?blank&=v&&x=~*","expected":{"observed_url":"https://example.test/a?blank&=v&&x=~*","normalized_url":"https://example.test/a?=v&blank=&x=~%2A","normalized_domain":"example.test","canonical_base_url":"https://example.test"}},{"url":"https://example.test/?x=%E2%84%AA&x=K","expected":{"observed_url":"https://example.test/?x=%E2%84%AA&x=K","normalized_url":"https://example.test/?x=K&x=%E2%84%AA","normalized_domain":"example.test","canonical_base_url":"https://example.test"}},{"url":"__SYNTHETIC_USERINFO_URL__","expected":{"code":"invalid-url","message":"Atlassian URLs cannot contain credentials"}},{"url":"ftp://example.test/","expected":{"code":"invalid-url","message":"Atlassian URLs must use HTTP or HTTPS"}},{"url":"https://example.test:bad/","expected":{"code":"invalid-url","message":"URL is invalid"}},{"url":"https://[broken/","expected":{"code":"invalid-url","message":"URL is invalid"}},{"url":"https://℀.test/","expected":{"code":"invalid-url","message":"URL is invalid"}},{"url":"https://","expected":{"code":"invalid-url","message":"Atlassian URLs must use HTTP or HTTPS"}},{"url":"relative","expected":{"code":"invalid-url","message":"Atlassian URLs must use HTTP or HTTPS"}},{"url":"","expected":{"code":"invalid-input","message":"url must be a non-empty string"}},{"url":"https://x.test:0/","expected":{"observed_url":"https://x.test:0/","normalized_url":"https://x.test:0/","normalized_domain":"x.test:0","canonical_base_url":"https://x.test:0"}},{"url":"https://x.test:65536/","expected":{"code":"invalid-url","message":"URL is invalid"}},{"url":"https://İ.test/A/?a=3&b=1&a=2","expected":{"observed_url":"https://İ.test/A/?a=3&b=1&a=2","normalized_url":"https://xn--i-9bb.test/A?a=2&a=3&b=1","normalized_domain":"xn--i-9bb.test","canonical_base_url":"https://xn--i-9bb.test"}},{"url":"https://faß.test/a","expected":{"observed_url":"https://faß.test/a","normalized_url":"https://fass.test/a","normalized_domain":"fass.test","canonical_base_url":"https://fass.test"}},{"url":"https://foo。test/","expected":{"observed_url":"https://foo。test/","normalized_url":"https://foo.test/","normalized_domain":"foo.test","canonical_base_url":"https://foo.test"}}]"########;

#[test]
fn opaque_authorized_locator_admission_matches_urlsplit_without_host_or_port_access() {
    let cases: serde_json::Value = serde_json::from_str(LOCATORS).unwrap();
    for case in cases.as_array().unwrap() {
        let result = match localbrain_core::backend::references::is_http_locator(
            case["value"].as_str().unwrap(),
        ) {
            Ok(value) => serde_json::json!(value),
            Err(_) => serde_json::json!("error"),
        };
        assert_eq!(result, case["result"], "{}", case["value"]);
    }
}
const LOCATORS: &str = r########"[{"value":"http://host:99999","result":true},{"value":"http://user:pass@host/","result":true},{"value":"http://:foo/","result":true},{"value":"http://@/","result":true},{"value":"http:// ","result":true},{"value":"https://[::1]:99999/","result":true},{"value":"https://[::1]junk","result":"error"},{"value":"https://[127.0.0.1]/","result":"error"},{"value":"https://[v1.host]/","result":true},{"value":"https://[v1.]/","result":"error"},{"value":"https://[broken/","result":"error"},{"value":"//[broken","result":"error"},{"value":"//[::1]","result":false},{"value":"//host","result":false},{"value":"relative","result":false},{"value":"ftp://host","result":false},{"value":"ftp://[broken","result":"error"},{"value":"HTTPS://℀.test/","result":"error"},{"value":"https://foo。test/","result":true},{"value":"https://[::1%scope]/","result":true},{"value":"https://[::1%]/","result":"error"},{"value":"https://x@[::1]/","result":true},{"value":"https://user[xx]@host/","result":"error"},{"value":"\u0000\u001chttp://host\t/path","result":true},{"value":"http://host\u0000/","result":true},{"value":"http:////host","result":false},{"value":"https://host:bad:many","result":true},{"value":"http://[vF.x y]:bad/","result":true}]"########;
