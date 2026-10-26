import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch
from urllib.parse import urlencode, urlsplit

from localbrain import main as web
from localbrain.natural_search.index import prepare, save_settings
from localbrain.natural_search.molecules import Profile
from localbrain.natural_search.presentation import safe_return
from localbrain.natural_search.service import SearchService
from localbrain.natural_search.source import source_connection
from natural_search_fixtures import ContractEncoder, fixture


class NaturalSearchWebTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="localbrain-natural-search-web-")
        self.addCleanup(temporary.cleanup)
        self.config = fixture(temporary.name)
        self.service = SearchService(self.config, ContractEncoder)
        self.addCleanup(self.service.stop)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(web, 'settings', self.config))
        self.stack.enter_context(patch.object(web, 'connect', lambda: source_connection(self.config.database_path)))
        self.stack.enter_context(patch.object(web.app.state, 'natural_search', self.service, create=True))

    def call(self, url, *, method='GET', form=None, headers=()):
        # These cases cover the AI mode. Keyword availability has its own cases.
        if urlsplit(url).path == '/natural-search' and 'mode=' not in url:
            url += ('&' if '?' in url else '?') + 'mode=ai'
        parsed = urlsplit(url)
        body = urlencode(form or {}).encode()
        header_list = [(b'host', b'127.0.0.1'), (b'content-type', b'application/x-www-form-urlencoded')]
        header_list += [(key.encode(), value.encode()) for key, value in headers]

        async def invoke():
            received = False
            output = []

            async def receive():
                nonlocal received
                if received:
                    return {'type': 'http.disconnect'}
                received = True
                return {'type': 'http.request', 'body': body, 'more_body': False}

            async def send(message):
                output.append(message)

            await web.app({'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
                           'method': method, 'path': parsed.path, 'raw_path': parsed.path.encode(),
                           'query_string': parsed.query.encode(), 'headers': header_list,
                           'scheme': 'http', 'server': ('127.0.0.1', 8000), 'client': ('127.0.0.1', 1234)}, receive, send)
            start = next(item for item in output if item['type'] == 'http.response.start')
            return start['status'], b''.join(item.get('body', b'') for item in output).decode(), dict(start['headers'])

        return asyncio.run(invoke())

    def build(self):
        profile = Profile()
        save_settings(self.config, profile)
        return prepare(self.config, ContractEncoder(self.config, profile), profile)

    def test_disabled_get_does_not_prepare_or_claim_no_results(self):
        with patch.object(self.service, 'request_prepare', side_effect=AssertionError('GET preparation')):
            status, body, _ = self.call('/natural-search?q=test')
        self.assertEqual(status, 200)
        self.assertIn('자연어 검색을 준비해 주세요', body)
        self.assertNotIn('현재 관련도 기준에 맞는 결과가 없습니다', body)
        self.assertIn('id="global-query" name="q" type="search" maxlength="300"', body)

    def test_header_uses_one_native_form_for_search_and_enter(self):
        status, body, _ = self.call('/natural-search?' + urlencode({'q': '앱 & 문서'}))
        header = body.split('<header class="workspace-header">', 1)[1].split('</header>', 1)[0]
        self.assertEqual(status, 200)
        self.assertEqual(header.count('type="search"'), 1)
        self.assertIn('id="global-search" class="global-search" action="/natural-search" method="get"', header)
        self.assertIn('placeholder="세션, 질문, 문서 통합 검색"', header)
        self.assertIn('value="앱 &amp; 문서"', header)
        self.assertIn('<label class="sr-only" for="global-query">검색</label>', header)
        self.assertIn('type="submit" form="global-search">Search</button>', header)
        self.assertNotIn('global-natural-query', header)
        self.assertNotIn('키워드 검색', header)

    def test_keyword_route_is_deprecated_without_navigation_fallback(self):
        status, body, _ = self.call('/openapi.json')
        self.assertEqual(status, 200)
        schema = json.loads(body)
        self.assertTrue(schema['paths']['/search']['get']['deprecated'])
        self.assertNotIn('deprecated', schema['paths']['/natural-search']['get'])
        body = self.call('/natural-search')[1]
        self.assertNotIn('href="/search', body)
        self.assertNotIn('키워드 검색으로', body)

    def test_prepare_and_cancel_are_explicit_local_actions(self):
        for action, method in (('prepare', 'request_prepare'), ('cancel', 'cancel')):
            with patch.object(self.service, method) as operation:
                status, _, headers = self.call('/natural-search/' + action, method='POST', form={'q': '앱'})
                self.assertEqual(status, 303)
                self.assertIn(b'q=', headers[b'location'])
                operation.assert_called_once_with()
            status, _, _ = self.call('/natural-search/' + action, method='POST', headers=[('sec-fetch-site', 'cross-site')])
            self.assertEqual(status, 403)

    def test_bounded_queries_and_escaped_text(self):
        self.assertEqual(self.call('/natural-search?' + urlencode({'q': '가'*301}))[0],422)
        self.assertEqual(self.call('/natural-search/prepare', method='POST', form={'q':'가'*301})[0],422)
        body = self.call('/natural-search?' + urlencode({'q': '<script>alert(1)</script>'}))[1]
        self.assertNotIn('<script>alert(1)</script>', body)
        self.assertIn('&lt;script&gt;',body)

    def test_ready_results_conditions_and_session_return(self):
        self.build()
        status, body, _ = self.call('/natural-search?' + urlencode({'q':'앱 관련 세션 보여줘'}))
        self.assertEqual(status, 200)
        self.assertIn('원문 1개',body)
        self.assertIn('적용된 조건: 세션',body)
        self.assertIn('#event-synthetic-event-1',body)
        self.assertNotIn('분석 Run 출력',body)
        status, body, _ = self.call('/sessions/1?' + urlencode({'search_return':'/natural-search?q=앱&page=2#natural-result-session-1'}))
        self.assertEqual(status,200)
        self.assertIn('id="event-synthetic-event-1"',body)
        self.assertIn('검색 결과로 돌아가기',body)

    def test_document_evidence_exact_span_and_stale_recovery(self):
        self.build()
        result = self.service.search('앱 문서만')['results'][0]
        status, body, _ = self.call(result['href'])
        self.assertEqual(status,200)
        self.assertIn('오프라인에서도 입력한 기록을 저장하는',body)
        self.assertIn('전체 문서 열기',body)
        self.assertIn('검색 결과로 돌아가기', self.call('/documents/1?' + urlencode({'search_return':'/natural-search?q=앱'}))[1])
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE context_roots SET enabled=0")
        status, body, _ = self.call(result['href'])
        self.assertEqual(status,409)
        self.assertNotIn('오프라인에서도 입력한 기록을 저장하는',body)
        self.assertIn('검색 근거가 변경되었거나',body)

    def test_no_data_no_match_and_failure_are_distinct(self):
        self.build()
        body = self.call('/natural-search?' + urlencode({'q':'열역학 법칙'}))[1]
        self.assertIn('현재 관련도 기준에 맞는 결과가 없습니다',body)
        for state, phrase in [('model-missing','검색 모델 설치가 필요합니다'), ('failed','검색 준비를 마치지 못했습니다'),
                              ('preparing','검색 자료를 준비하고 있습니다'),('partial','일부 자료를 갱신하고 있습니다'),
                              ('no-data','검색할 자료가 없습니다')]:
            with patch.object(self.service,'status',return_value={'state':state}):
                self.assertIn(phrase,self.call('/natural-search')[1])

    def test_status_is_aggregate_and_no_store(self):
        self.build()
        status, body, headers = self.call('/api/natural-search/status')
        value = json.loads(body)
        self.assertEqual(status,200)
        self.assertEqual(value['state'],'ready')
        self.assertIn(b'no-store', headers[b'cache-control'])
        self.assertNotIn('Atlas',body)
        self.assertNotIn('synthetic-event',body)

    def test_query_failure_preserves_query_and_ready_index_state(self):
        self.build()
        for code, phrase in [('SEARCH_INPUT_TOO_LONG','검색어를 더 짧게'),
                             ('INVALID_SEARCH_VECTORS','검색을 완료하지 못했습니다')]:
            with patch.object(self.service,'search',side_effect=ValueError(code)):
                status, body, _ = self.call('/natural-search?' + urlencode({'q':'앱'}))
            self.assertEqual(status,200)
            self.assertIn(phrase,body)
            self.assertIn('data-state="ready"',body)
            self.assertIn('value="앱"',body)
            self.assertNotIn('현재 관련도 기준에 맞는 결과가 없습니다',body)

    def test_return_targets_cannot_escape_search(self):
        for value in ['https://example.test/','//example.test/','/sessions','/natural-search\\evil','http://[broken', '/natural-search?page=-1']:
            self.assertEqual(safe_return(value),'/natural-search')
        self.assertIn('#natural-result-document-1',safe_return('/natural-search?q=앱&page=2#natural-result-document-1'))

    def test_original_search_still_works(self):
        status, body, _ = self.call('/search?' + urlencode({'q':'앱'}))
        self.assertEqual(status,200)
        self.assertIn('Atlas 모바일 앱',body)
        self.assertIn('action="/search"',body)
        self.assertIn('id="global-query" name="q" type="search" maxlength="300"',body)


if __name__ == '__main__':
    unittest.main()
