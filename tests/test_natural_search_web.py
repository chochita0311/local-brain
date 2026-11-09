import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch
from urllib.parse import urlencode, urlsplit

from localbrain.natural_search import web
from localbrain.main import app
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
        self.stack.enter_context(patch.object(web, 'connect', lambda: source_connection(self.config.database_path)))
        self.stack.enter_context(patch('localbrain.app.templating.connect', lambda: source_connection(self.config.database_path)))
        self.stack.enter_context(patch('localbrain.app.templating.settings', self.config))
        self.stack.enter_context(patch('localbrain.search.web.connect', lambda: source_connection(self.config.database_path)))
        self.stack.enter_context(patch('localbrain.sessions.web.connect', lambda: source_connection(self.config.database_path)))
        self.stack.enter_context(patch('localbrain.local_context.web.connect', lambda: source_connection(self.config.database_path)))
        self.stack.enter_context(patch('localbrain.app.settings.settings', self.config))
        self.stack.enter_context(patch.object(app.state, 'natural_search', self.service, create=True))

    def call(self, url, *, method='GET', form=None, json_body=None, headers=()):
        parsed = urlsplit(url)
        body = json.dumps(json_body).encode() if json_body is not None else urlencode(form or {}).encode()
        content_type = b'application/json' if json_body is not None else b'application/x-www-form-urlencoded'
        header_list = [(b'host', b'127.0.0.1'), (b'content-type', content_type)]
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

            await app({'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
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
        self.assertIn('data-search-engine="keyword"', body)
        self.assertNotIn('현재 관련도 기준에 맞는 결과가 없습니다', body)
        self.assertIn('id="global-query" name="q" type="search" maxlength="300"', body)

    def test_header_uses_one_native_form_for_search_and_enter(self):
        status, body, _ = self.call('/natural-search?' + urlencode({'q': '앱 & 문서'}))
        header = body.split('<header class="workspace-header"', 1)[1].split('>', 1)[1].split('</header>', 1)[0]
        self.assertEqual(status, 200)
        self.assertEqual(header.count('type="search"'), 1)
        self.assertIn('id="global-search" class="global-search" action="/natural-search" method="get"', header)
        self.assertIn('placeholder="세션, 질문, 문서 통합 검색"', header)
        self.assertIn('value="앱 &amp; 문서"', header)
        self.assertIn('<label class="sr-only" for="global-query">검색</label>', header)
        self.assertRegex(header, r'type="submit" form="global-search"[^>]*>Search</button>')
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
        self.assertIn('data-search-engine="ai"', body)
        self.assertNotIn('aria-label="검색 방식"', body)
        self.assertNotIn('name="mode"', body)
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

    def test_ready_queries_show_results_without_repeating_the_search_landing(self):
        self.build()
        for query, expected in [('앱', '원문 2개'), ('열역학 법칙', '현재 관련도 기준에 맞는 결과가 없습니다')]:
            with self.subTest(query=query):
                status, body, _ = self.call('/natural-search?' + urlencode({'q': query}))
                main = body.split('id="main-content"', 1)[1].split('</main>', 1)[0]
                self.assertEqual(status, 200)
                self.assertIn(expected, main)
                self.assertNotIn('class="page-heading', main)
                self.assertNotIn('id="natural-page-query"', main)
                self.assertNotIn('data-search-status-count', main)
                self.assertNotIn('data-search-coverage', main)
                self.assertRegex(main, r'<section[^>]*data-natural-search-status[^>]*\shidden>')
                self.assertIn('id="global-query"', body)

    def test_queryless_search_keeps_its_intro_form_and_coverage(self):
        self.build()
        body = self.call('/natural-search?' + urlencode({'q': '   '}))[1]
        self.assertIn('자연어로 원문 찾기', body)
        self.assertIn('id="natural-page-query"', body)
        self.assertIn('data-search-status-count', body)
        self.assertIn('data-search-coverage', body)
        self.assertNotRegex(body, r'<section[^>]*data-natural-search-status[^>]*\shidden>')

    def test_keyword_results_omit_the_intro_and_model_install_prompt(self):
        from localbrain.search.keyword import keyword_search
        with patch('localbrain.search.keyword.keyword_search', lambda connection, query: keyword_search(connection, query, config=self.config)):
            status, body, _ = self.call('/natural-search?' + urlencode({'q': '앱'}))
        main = body.split('id="main-content"', 1)[1].split('</main>', 1)[0]
        self.assertEqual(status, 200)
        self.assertIn('Atlas 모바일 앱', main)
        self.assertNotIn('로컬 기록 검색', main)
        self.assertNotIn('id="keyword-query"', main)
        self.assertNotIn('모델 설치 · 검색 설정', main)
        landing = self.call('/natural-search')[1]
        self.assertIn('로컬 기록 검색', landing)
        self.assertIn('id="keyword-query"', landing)
        self.assertIn('모델 설치 · 검색 설정', landing)

    def test_keyword_fallback_excludes_the_selected_model_cache_and_keeps_documents(self):
        from localbrain.foundation.private_json import atomic_json
        from localbrain.models.catalog import EMBEDDING_SCHEMA
        from localbrain.models.installation import model_root
        from localbrain.natural_search.source import read_sources
        from localbrain.search.keyword import keyword_search

        selected = self.config.context_root / 'model-originals'
        selected.mkdir(parents=True)
        metadata = model_root('embedding', self.config.data_dir)
        metadata.mkdir(parents=True)
        atomic_json(metadata / 'model.json', {'schema': EMBEDDING_SCHEMA, 'cache_root': str(selected)})
        model_path = str(selected / 'README.md')
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("INSERT INTO context_documents (id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash) VALUES (2,2,1,?,'model-originals/README.md','Synthetic model metadata','모바일 앱',20,1791252000000000000,'synthetic-model')", (model_path,))
            connection.execute("INSERT INTO search_index SELECT 'document',cast(id AS TEXT),'context',title,body,path FROM context_documents")
        sources, coverage = read_sources(self.config)
        self.assertIn('document:1', [source.key for source in sources])
        self.assertNotIn('document:2', [source.key for source in sources])
        self.assertEqual(coverage['excluded_runtime_documents'], 1)
        for state in ('disabled', 'model-missing'):
            with self.subTest(state=state), patch.object(self.service, 'status', return_value={'state': state}), patch('localbrain.search.keyword.keyword_search', lambda connection, query: keyword_search(connection, query, config=self.config)):
                status, body, _ = self.call('/natural-search?' + urlencode({'q': '앱'}))
                self.assertEqual(status, 200)
                self.assertIn('data-search-engine="keyword"', body)
                self.assertIn('모바일 앱 설계', body)
                self.assertNotIn('Synthetic model metadata', body)
        (metadata / 'model.json').write_text('[]')
        with source_connection(self.config.database_path) as connection:
            results = keyword_search(connection, '앱', config=self.config)
        self.assertIn('모바일 앱 설계', [item['title'] for item in results])

    def test_result_preparation_and_failure_stay_visible_without_false_empty_results(self):
        for state, phrase in [('failed', '검색 준비를 마치지 못했습니다'),
                              ('preparing', '검색 자료를 준비하고 있습니다'),
                              ('partial', '일부 자료를 갱신하고 있습니다'),
                              ('no-data', '검색할 자료가 없습니다')]:
            with self.subTest(state=state), patch.object(self.service, 'status', return_value={'state': state}), patch.object(self.service, 'search', side_effect=ValueError('SEARCH_INDEX_UNAVAILABLE')):
                body = self.call('/natural-search?' + urlencode({'q': '앱'}))[1]
                main = body.split('id="main-content"', 1)[1].split('</main>', 1)[0]
                self.assertIn(phrase, main)
                self.assertNotRegex(main, r'<section[^>]*data-natural-search-status[^>]*\shidden>')
                self.assertNotIn('현재 관련도 기준에 맞는 결과가 없습니다', main)
                self.assertNotIn('data-search-coverage', main)

    def test_no_data_no_match_and_failure_are_distinct(self):
        self.build()
        body = self.call('/natural-search?' + urlencode({'q':'열역학 법칙'}))[1]
        self.assertIn('현재 관련도 기준에 맞는 결과가 없습니다',body)
        for state, phrase in [('failed','검색 준비를 마치지 못했습니다'),
                              ('preparing','검색 자료를 준비하고 있습니다'),('partial','일부 자료를 갱신하고 있습니다'),
                              ('no-data','검색할 자료가 없습니다')]:
            with patch.object(self.service,'status',return_value={'state':state}):
                self.assertIn(phrase,self.call('/natural-search')[1])

    def test_engine_follows_settings_and_legacy_mode_cannot_override_it(self):
        for state, engine in [('disabled', 'keyword'), ('model-missing', 'keyword'),
                              ('ready', 'ai'), ('failed', 'ai'), ('partial', 'ai'), ('preparing', 'ai')]:
            for legacy in ('', '&mode=ai', '&mode=keyword'):
                with self.subTest(state=state, legacy=legacy), patch.object(self.service, 'status', return_value={'state': state}), patch.object(self.service, 'search', side_effect=ValueError('SEARCH_INDEX_UNAVAILABLE')):
                    body = self.call('/natural-search?' + urlencode({'q': '앱'}) + legacy)[1]
                self.assertIn('data-search-engine="' + engine + '"', body)
                self.assertIn('value="앱"', body)
                self.assertNotIn('aria-label="검색 방식"', body)
                self.assertNotIn('name="mode"', body)

    def test_cutoff_api_validates_persists_and_rejects_stale_writes(self):
        status, body, headers = self.call('/api/settings/search')
        self.assertEqual(status, 200)
        self.assertIn(b'no-store', headers[b'cache-control'])
        current = json.loads(body)
        self.assertEqual(current['cutoff'], .45)
        value = {'cutoff': .3, 'revision': current['revision']}
        status, body, _ = self.call('/api/settings/search', method='POST', json_body=value)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['cutoff'], .3)
        status, body, _ = self.call('/api/settings/search', method='POST', json_body={**value, 'cutoff': .8})
        self.assertEqual(status, 409)
        self.assertIn('검색 설정이 변경되었습니다', body)
        for cutoff in (True, '0.4', None, -1, 1.01):
            status, body, _ = self.call('/api/settings/search', method='POST', json_body={**value, 'cutoff': cutoff})
            self.assertEqual(status, 422)
            self.assertIn('0부터 1 사이', body)

    def test_cutoff_read_and_save_failures_are_bounded_and_do_not_repair_files(self):
        path = self.config.data_dir / 'natural-search.json'
        path.write_text('{invalid')
        path.chmod(0o600)
        status, body, _ = self.call('/api/settings/search')
        self.assertEqual(status, 200)
        self.assertIsNone(json.loads(body)['cutoff'])
        self.assertIn('설정을 읽지 못했습니다', body)
        self.assertEqual(path.read_text(), '{invalid')
        path.unlink()
        current = json.loads(self.call('/api/settings/search')[1])
        with patch('localbrain.natural_search.index.atomic_json', side_effect=OSError('synthetic disk failure')):
            status, body, _ = self.call('/api/settings/search', method='POST', json_body={'cutoff': .2, 'revision': current['revision']})
        self.assertEqual(status, 503)
        self.assertIn('검색 관련도를 저장하지 못했습니다', body)
        self.assertNotIn('synthetic disk failure', body)

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
                             ('SEARCH_INDEX_UNAVAILABLE','검색할 자료를 불러오지 못했습니다'),
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
