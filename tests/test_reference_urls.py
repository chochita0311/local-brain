"""Shared URL identities are independent of optional feature registration."""

import unittest

from localbrain.references.urls import parse_url


class ReferenceUrlTests(unittest.TestCase):
    def test_product_recognition_uses_url_shape_without_special_hostname(self):
        for url, service, identity in (
            ("https://example.test/browse/DEMO-123", "jira", "DEMO-123"),
            ("https://example.test/pages/viewpage.action?pageId=123", "confluence", "123"),
        ):
            with self.subTest(url=url):
                parsed = parse_url(url)
                self.assertEqual(parsed.locator.service, service)
                self.assertEqual(parsed.locator.item_identity, identity)
        for url in ("https://jira.example.test/", "https://example.test/custom/123"):
            with self.subTest(url=url):
                self.assertIsNone(parse_url(url).locator)

    def test_generic_urls_drop_query_while_known_identity_queries_survive(self):
        generic = parse_url("https://Example.Test:443/path?token=synthetic#fragment")
        page = parse_url("https://example.test/wiki/pages/viewpage.action?pageId=123&token=synthetic#fragment")
        self.assertEqual(generic.normalized_url, "https://example.test/path")
        self.assertEqual(page.normalized_url, "https://example.test/wiki/pages/viewpage.action?pageId=123")
        self.assertEqual(generic.target_key, parse_url("https://example.test/path").target_key)
        self.assertEqual(page.target_key, parse_url("https://example.test/wiki/spaces/TEAM/pages/123/title").target_key)
        self.assertNotEqual(page.target_key, parse_url("https://example.test/wiki/pages/viewpage.action?pageId=124").target_key)

    def test_unsafe_known_urls_never_fall_back_to_generic_urls(self):
        for url in (
            "https://" + "account:value" + "@example.test/browse/DEMO-123",
            "https://example.test/wiki/pages/viewpage.action?pageId=%ZZ",
            "file:///synthetic/page.md",
        ):
            with self.subTest(url=url):
                self.assertIsNone(parse_url(url))


if __name__ == "__main__":
    unittest.main()
