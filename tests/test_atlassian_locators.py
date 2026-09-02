import ast
import dataclasses
import hashlib
import inspect
import json
import unittest

import localbrain.atlassian_locators as locator_module
from localbrain.atlassian_locators import (
    ATLASSIAN_LOCATOR_VERSION,
    atlassian_item_container_hint,
    atlassian_locator_identity,
    describe_atlassian_url,
)


class AtlassianLocatorTests(unittest.TestCase):
    def assert_result(self, url, **expected):
        result = describe_atlassian_url(url)
        for key, value in expected.items():
            self.assertEqual(getattr(result, key), value, (url, result))
        return result

    def test_result_shape_version_and_terminal_reasons(self):
        self.assertEqual(
            ATLASSIAN_LOCATOR_VERSION,
            "localbrain.atlassian-locator.v1",
        )
        item = self.assert_result(
            "https://JIRA.Example.Test.:443/browse/pay-7?theme=compact#comment",
            kind="item",
            service="jira",
            family="jira_issue",
            normalized_domain="jira.example.test",
            canonical_base_url="https://jira.example.test",
            safe_locator_url="https://jira.example.test/browse/PAY-7",
            item_identity_kind="jira_issue",
            item_identity="PAY-7",
            reason=None,
        )
        self.assertIsNone(item.reference_kind)
        self.assertIsNone(item.reference_identity)
        self.assertIsNone(item.container_hint)

        unsupported = self.assert_result(
            "https://jira.example.test/unknown?theme=compact",
            kind="unsupported",
            reason="unsupported-url",
        )
        unsafe = self.assert_result(
            "file:///tmp/a", kind="unsafe", reason="unsafe-url"
        )
        for result in (unsupported, unsafe):
            values = dataclasses.asdict(result)
            self.assertTrue(
                all(
                    value is None
                    for key, value in values.items()
                    if key not in {"kind", "reason"}
                )
            )

    def test_shared_locator_is_pure_and_semantic_kinds_do_not_collide(self):
        source = inspect.getsource(locator_module)
        imported_modules = []
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")
        for forbidden in (
            "sqlite3",
            "pathlib",
            "requests",
            "localbrain.",
        ):
            self.assertFalse(
                any(module.startswith(forbidden) for module in imported_modules)
            )

        locators = (
            describe_atlassian_url(
                "https://jira.example.test/secure/RapidBoard.jspa?rapidView=17"
            ),
            describe_atlassian_url(
                "https://jira.example.test/secure/RapidBoard.jspa"
            ),
            describe_atlassian_url(
                "https://other.example.test/secure/RapidBoard.jspa?rapidView=17"
            ),
            describe_atlassian_url(
                "https://wiki.example.test/wiki/pages/17"
            ),
        )
        identities = [atlassian_locator_identity(locator) for locator in locators]
        self.assertEqual(len(set(identities)), len(identities))

    def test_host_url_and_control_safety(self):
        unsafe_urls = (
            "https://" + "account:value" + "@jira.example.test/browse/PAY-1",
            "https://jira.example.test:99999/browse/PAY-1",
            "https://exa%mple.test/browse/PAY-1",
            "https://bad_host.test/browse/PAY-1",
            "https://bad host.test/browse/PAY-1",
            "https://999.999.999.999/browse/PAY-1",
            "https://wiki.example.test/wiki/spaces/%FF/pages/7",
            "https://jira.example.test/browse/PAY-1\nnext",
            "https://jira.example.test/browse/PAY-1" + ("x" * 8_000),
        )
        for url in unsafe_urls:
            with self.subTest(url=url):
                self.assert_result(url, kind="unsafe", reason="unsafe-url")
        for url in (
            "https://jira.example.test/projects/%0A",
            "https://jira.example.test/projects/%00",
            "https://jira.example.test/browse/PAY%0A-1",
        ):
            self.assert_result(url, kind="unsupported", reason="unsupported-url")

    def test_jira_issue_path_matrix_and_ascii_only_tokens(self):
        paths = (
            "/browse/pay-1",
            "/issues/pay-2",
            "/jira/core/projects/pay/issues/pay-3",
            "/jira/software/projects/pay/issues/pay-4",
            "/jira/software/c/projects/pay/issues/pay-5",
            "/jira/servicedesk/projects/pay/issues/pay-6",
            "/servicedesk/customer/portal/0007/pay-7",
        )
        for number, path in enumerate(paths, 1):
            with self.subTest(path=path):
                result = self.assert_result(
                    "https://jira.example.test" + path,
                    kind="item",
                    item_identity="PAY-{}".format(number),
                    safe_locator_url=(
                        "https://jira.example.test/browse/PAY-{}".format(number)
                    ),
                )
                self.assertEqual(
                    atlassian_item_container_hint(
                        "https://jira.example.test" + path
                    ),
                    "PAY",
                )
                self.assertIsNone(result.container_hint)

        self.assert_result(
            "https://jira.example.test/JIRA/SOFTWARE/C/PROJECTS/pay/ISSUES/pay-9",
            kind="item",
            item_identity="PAY-9",
        )
        self.assert_result(
            "https://wiki.example.test/wiki/ſpaces/TEAM/pages/7",
            kind="unsupported",
        )
        self.assert_result(
            "https://jira.example.test/browse?ſelectedIssue=PAY-1",
            kind="unsupported",
        )

    def test_selected_issue_is_the_only_query_item_authority(self):
        for path in (
            "/browse",
            "/projects/PAY",
            "/secure/RapidBoard.jspa?rapidView=17&",
            "/issues?filter=9&",
            "/secure/Dashboard.jspa?selectPageId=4&",
            "/servicedesk/customer/portal/2?",
        ):
            separator = "&" if "?" in path else "?"
            if path.endswith(("&", "?")):
                separator = ""
            result = self.assert_result(
                "https://jira.example.test{}{}selectedIssue=pay-8".format(
                    path, separator
                ),
                kind="item",
                item_identity="PAY-8",
                safe_locator_url="https://jira.example.test/browse/PAY-8",
            )
            self.assertIsNone(result.reference_identity)

        for name in ("issueKey", "key"):
            self.assert_result(
                "https://jira.example.test/browse?{}=PAY-8".format(name),
                kind="unsupported",
            )
        self.assert_result(
            "https://jira.example.test/arbitrary?selectedIssue=PAY-8",
            kind="unsupported",
        )
        self.assert_result(
            "https://jira.example.test/secure/RapidBoard.jspa"
            "?rapidView=17&selectedIssue=BAD",
            kind="structure",
            reference_identity="17",
        )
        self.assert_result(
            "https://jira.example.test/secure/RapidBoard.jspa"
            "?rapidView=17&selectedIssue=%ZZ",
            kind="unsafe",
            reason="unsafe-url",
        )

    def test_path_item_precedes_query_item(self):
        self.assert_result(
            "https://jira.example.test/browse/PAY-1?selectedIssue=OPS-2",
            kind="item",
            item_identity="PAY-1",
        )
        self.assert_result(
            "https://jira.example.test/browse/PAY-1?selectedIssue=%ZZ",
            kind="unsafe",
            reason="unsafe-url",
        )
        self.assert_result(
            "https://jira.example.test/browse/PAY-1?arbitrary=%ZZ",
            kind="item",
            item_identity="PAY-1",
        )

    def test_confluence_page_matrix_preserves_context(self):
        fixtures = (
            (
                "https://wiki.example.test/spaces/Team/pages/0007/A+title",
                "https://wiki.example.test/spaces/Team/pages/7",
                "Team",
            ),
            (
                "https://wiki.example.test/wiki/spaces/Team/pages/7",
                "https://wiki.example.test/wiki/spaces/Team/pages/7",
                "Team",
            ),
            (
                "https://wiki.example.test/confluence/pages/7/A-title",
                "https://wiki.example.test/confluence/pages/viewpage.action?pageId=7",
                None,
            ),
            (
                "https://wiki.example.test/wiki/viewpage.action?pageId=0007",
                "https://wiki.example.test/wiki/pages/viewpage.action?pageId=7",
                None,
            ),
            (
                "https://wiki.example.test/pages/viewpage.action?pageId=7",
                "https://wiki.example.test/pages/viewpage.action?pageId=7",
                None,
            ),
        )
        for url, safe_url, hint in fixtures:
            with self.subTest(url=url):
                self.assert_result(
                    url,
                    kind="item",
                    service="confluence",
                    item_identity="7",
                    safe_locator_url=safe_url,
                )
                self.assertEqual(atlassian_item_container_hint(url), hint)

        invalid_hint = (
            "https://wiki.example.test/wiki/spaces/A%2FB/pages/7"
        )
        self.assert_result(
            invalid_hint,
            kind="item",
            item_identity="7",
            safe_locator_url=(
                "https://wiki.example.test/wiki/pages/viewpage.action?pageId=7"
            ),
        )
        self.assertIsNone(atlassian_item_container_hint(invalid_hint))
        control_hint = "https://wiki.example.test/wiki/spaces/%00/pages/7"
        self.assert_result(
            control_hint,
            kind="item",
            item_identity="7",
            safe_locator_url=(
                "https://wiki.example.test/wiki/pages/viewpage.action?pageId=7"
            ),
        )
        self.assertIsNone(atlassian_item_container_hint(control_hint))
        self.assert_result(
            "https://wiki.example.test/wiki/spaces/%ZZ/pages/7",
            kind="unsafe",
            reason="unsafe-url",
        )

    def test_page_id_is_only_valid_on_viewpage_family(self):
        for url in (
            "https://wiki.example.test/wiki/viewpage.action?pageId=8",
            "https://wiki.example.test/confluence/pages/viewpage.action?pageId=8",
        ):
            self.assert_result(url, kind="item", item_identity="8")
        self.assert_result(
            "https://wiki.example.test/wiki/spaces/TEAM?pageId=8",
            kind="structure",
            reference_kind="confluence_space",
            reference_identity="TEAM",
        )
        self.assert_result(
            "https://wiki.example.test/wiki/pages?pageId=8",
            kind="unsupported",
        )
        self.assert_result(
            "https://wiki.example.test/wiki/viewpage.action?pageId=8&pageId=9",
            kind="unsupported",
        )

    def test_jira_project_and_service_project_structures(self):
        paths = (
            "/projects/pay/settings",
            "/jira/core/projects/pay/summary",
            "/jira/software/projects/pay/backlog",
            "/jira/software/c/projects/pay/list",
            "/plugins/servlet/project-config/pay/details",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assert_result(
                    "https://jira.example.test" + path,
                    kind="structure",
                    reference_kind="jira_project",
                    reference_identity="PAY",
                    container_hint="PAY",
                    safe_locator_url="https://jira.example.test/projects/PAY",
                )
        self.assert_result(
            "https://jira.example.test/jira/servicedesk/projects/pay/queues",
            kind="structure",
            reference_kind="jira_service_project",
            reference_identity="PAY",
            safe_locator_url=(
                "https://jira.example.test/jira/servicedesk/projects/PAY"
            ),
        )
        for path in (
            "/projects",
            "/jira/servicedesk/projects",
            "/projects/invalid-key",
        ):
            self.assert_result(
                "https://jira.example.test" + path,
                kind="unsupported",
            )

    def test_board_structures_hints_and_site_fallbacks(self):
        board = self.assert_result(
            "https://jira.example.test/secure/RapidBoard.jspa"
            "?mode=plan&projectKey=pay&rapidView=00017&theme=compact",
            kind="structure",
            reference_kind="jira_board",
            reference_identity="17",
            container_hint="PAY",
            safe_locator_url=(
                "https://jira.example.test/secure/RapidBoard.jspa"
                "?rapidView=17&projectKey=PAY"
            ),
        )
        expected_identity = (
            ATLASSIAN_LOCATOR_VERSION,
            "jira.example.test",
            "jira",
            "structure",
            "jira_board",
            "17",
        )
        self.assertEqual(atlassian_locator_identity(board), expected_identity)
        for query in (
            "rapidView=17&projectKey=bad-key",
            "rapidView=17&projectKey=PAY&projectKey=OPS",
        ):
            result = self.assert_result(
                "https://jira.example.test/secure/RapidBoard.jspa?" + query,
                kind="structure",
                reference_identity="17",
                container_hint=None,
                safe_locator_url=(
                    "https://jira.example.test/secure/RapidBoard.jspa?rapidView=17"
                ),
            )
            self.assertEqual(atlassian_locator_identity(result), expected_identity)
        self.assert_result(
            "https://jira.example.test/secure/RapidBoard.jspa"
            "?rapidView=17&projectKey=%ZZ",
            kind="unsafe",
        )
        self.assert_result(
            "https://jira.example.test/secure/RapidBoard.jspa?rapidView=bad",
            kind="site",
            family="jira_board",
            safe_locator_url=(
                "https://jira.example.test/secure/RapidBoard.jspa"
            ),
        )
        self.assert_result(
            "https://jira.example.test/secure/RapidBoard.jspa?rapidView=%00",
            kind="site",
            family="jira_board",
            safe_locator_url=(
                "https://jira.example.test/secure/RapidBoard.jspa"
            ),
        )

        for path in (
            "/jira/software/projects/pay/boards/00018/backlog",
            "/jira/software/c/projects/pay/boards/18",
        ):
            self.assert_result(
                "https://jira.example.test" + path,
                kind="structure",
                reference_identity="18",
                container_hint="PAY",
                safe_locator_url=(
                    "https://jira.example.test/jira/software/projects/PAY/boards/18"
                ),
            )
        self.assert_result(
            "https://jira.example.test/jira/software/c/projects/pay/boards",
            kind="site",
            family="jira_board",
            safe_locator_url=(
                "https://jira.example.test/jira/software/projects/PAY/boards"
            ),
        )
        self.assert_result(
            "https://jira.example.test/jira/software/projects/pay/boards/%00",
            kind="site",
            family="jira_board",
            safe_locator_url=(
                "https://jira.example.test/jira/software/projects/PAY/boards"
            ),
        )

    def test_filter_dashboard_and_jsm_families(self):
        for path in (
            "/issues?filter=0009",
            "/secure/IssueNavigator.jspa?requestId=9&jql=project%3DPAY",
            "/secure/ManageFilters.jspa?filterId=9",
        ):
            self.assert_result(
                "https://jira.example.test" + path,
                kind="structure",
                reference_kind="jira_filter",
                reference_identity="9",
                safe_locator_url="https://jira.example.test/issues?filter=9",
            )
        self.assert_result(
            "https://jira.example.test/issues?filter=9&requestId=9",
            kind="site",
            family="jira_filter",
            safe_locator_url="https://jira.example.test/issues",
        )
        self.assert_result(
            "https://jira.example.test/secure/Dashboard.jspa?selectPageId=004",
            kind="structure",
            reference_kind="jira_dashboard",
            reference_identity="4",
            safe_locator_url=(
                "https://jira.example.test/secure/Dashboard.jspa?selectPageId=4"
            ),
        )
        self.assert_result(
            "https://jira.example.test/servicedesk/customer/portal",
            kind="site",
            family="jira_service_portal",
        )
        self.assert_result(
            "https://jira.example.test/servicedesk/customer/portal/0003/queues",
            kind="structure",
            reference_kind="jira_service_portal",
            reference_identity="3",
            safe_locator_url=(
                "https://jira.example.test/servicedesk/customer/portal/3"
            ),
        )

    def test_confluence_space_context_and_excluded_descendants(self):
        fixtures = (
            (
                "https://wiki.example.test/spaces/%EF%BC%B4%EF%BC%A5%EF%BC%A1%EF%BC%AD/overview",
                "https://wiki.example.test/spaces/TEAM",
            ),
            (
                "https://wiki.example.test/wiki/display/TEAM/A-title",
                "https://wiki.example.test/wiki/spaces/TEAM",
            ),
            (
                "https://wiki.example.test/confluence/spaces/TEAM/settings",
                "https://wiki.example.test/confluence/spaces/TEAM",
            ),
        )
        for url, safe_url in fixtures:
            self.assert_result(
                url,
                kind="structure",
                reference_kind="confluence_space",
                reference_identity="TEAM",
                container_hint="TEAM",
                safe_locator_url=safe_url,
            )
        for path in (
            "/wiki/spaces",
            "/wiki/display",
            "/wiki/pages",
            "/wiki/spaces/TEAM/attachments/7",
            "/wiki/spaces/TEAM/blog/7",
            "/wiki/spaces/TEAM/whiteboards/7",
            "/wiki/spaces/TEAM/databases/7",
            "/wiki/spaces/TEAM/embed/7",
        ):
            self.assert_result(
                "https://wiki.example.test" + path,
                kind="unsupported",
            )

    def test_rest_and_unlisted_families_are_unsupported(self):
        for path in (
            "/rest/api/3/issue/PAY-1",
            "/wiki/rest/api/content/7",
            "/plugins/servlet/other",
            "/wiki/blog/7",
            "/wiki/short/abc",
            "/wiki/x/abc",
            "/",
        ):
            self.assert_result(
                "https://example.test" + path,
                kind="unsupported",
                reason="unsupported-url",
            )

    def test_query_pair_cap_never_trusts_an_inspected_prefix(self):
        noise_63 = "&".join("x{}=1".format(index) for index in range(63))
        within_cap = (
            "https://jira.example.test/secure/RapidBoard.jspa?"
            + noise_63
            + "&rapidView=17"
        )
        self.assert_result(
            within_cap,
            kind="structure",
            reference_identity="17",
        )

        noise_64 = "&".join("x{}=1".format(index) for index in range(64))
        over_cap = (
            "https://jira.example.test/secure/RapidBoard.jspa?rapidView=17&"
            + noise_64
        )
        self.assert_result(
            over_cap,
            kind="site",
            family="jira_board",
            safe_locator_url=(
                "https://jira.example.test/secure/RapidBoard.jspa"
            ),
        )

    def test_semantic_identity_serialization_is_exact_and_hint_free(self):
        first = describe_atlassian_url(
            "https://jira.example.test/secure/RapidBoard.jspa"
            "?rapidView=17&projectKey=PAY"
        )
        second = describe_atlassian_url(
            "https://jira.example.test/secure/RapidBoard.jspa"
            "?rapidView=17&projectKey=OPS"
        )
        identity = atlassian_locator_identity(first)
        self.assertEqual(identity, atlassian_locator_identity(second))
        serialized = json.dumps(
            identity,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        self.assertEqual(
            hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            "214198462a821b2b3517ebeb9b668e22b14764fa330b05113bb58af2a41efacc",
        )


if __name__ == "__main__":
    unittest.main()
