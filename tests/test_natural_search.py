import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from localbrain.natural_search.conditions import interpret
from localbrain.natural_search.index import folder, meta, open_index, prepare, read_settings, save_settings, writer
from localbrain.natural_search.molecules import Profile, molecularize, split_spans
from localbrain.natural_search.model import SearchEncoder
from localbrain.natural_search.query import focus_query
from localbrain.natural_search.retrieval import Retriever
from localbrain.natural_search.source import read_sources
from localbrain.natural_search.service import SearchService
from natural_search_fixtures import CharacterTokenizer, ContractEncoder, fixture


class NaturalSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="localbrain-natural-search-test-")
        self.addCleanup(self.temp.cleanup)
        self.config = fixture(self.temp.name)
        self.profile = Profile()
        self.encoder = ContractEncoder(self.config, self.profile)

    def build(self):
        result = prepare(self.config, self.encoder, self.profile)
        reader = Retriever(self.config, self.profile, self.encoder)
        self.addCleanup(reader.close)
        return result, reader

    def test_source_policy_and_read_only_ingestion(self):
        sources, coverage = read_sources(self.config)
        self.assertEqual({s.key for s in sources}, {'session:1', 'session:2', 'session:3', 'document:1'})
        self.assertEqual(coverage['excluded_sessions'], 2)
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute('UPDATE context_roots SET enabled=0')
        self.assertEqual(len(read_sources(self.config)[0]), 3)

    def test_coverage_distinguishes_empty_unreadable_and_runtime_sources(self):
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE activity_events SET text='' WHERE session_id=1")
            connection.execute("UPDATE context_documents SET body='' WHERE id=1")
        _, coverage = read_sources(self.config)
        self.assertEqual(coverage['empty_sessions'], 1)
        self.assertEqual(coverage['empty_documents'], 1)
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE context_documents SET path=?,body='app cache'", (str(self.config.cache_dir/'search.txt'),))
        self.assertEqual(read_sources(self.config)[1]['excluded_runtime_documents'], 1)
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute('UPDATE context_roots SET readable=0')
        self.assertEqual(read_sources(self.config)[1]['unreadable_context_roots'], 1)

    def test_full_body_unicode_and_tail_coverage(self):
        text = ('첫 요청.\n\n조건은 유지하고 취소하지 않는다. 👨‍💻\n' * 120) + '마지막 고유 근거'
        spans = list(split_spans(text, CharacterTokenizer(), self.profile))
        self.assertEqual(''.join(text[a:b] for a, b in spans), text)
        self.assertTrue(all(0 < b-a <= 768 for a,b in spans))
        self.assertTrue(all(spans[i][1] == spans[i+1][0] for i in range(len(spans)-1)))

    def test_context_is_bounded_and_provenance_preserved(self):
        source = read_sources(self.config)[0][0]
        source.blocks.append({'id':'answer','text':'그 조건을 유지한다.','role':'assistant','sequence':1,'source_line':2})
        values = list(molecularize(source, self.encoder.tokenizer, self.profile))
        self.assertEqual(values[-1]['locator']['context_event'], source.blocks[0]['id'])
        self.assertTrue(all(len(v['input']) + 1 <= 1024 for v in values))

    def test_splitter_tokenizer_does_not_share_query_mutation_state(self):
        encoder = object.__new__(SearchEncoder)
        encoder._condition = threading.Condition()
        encoder._busy, encoder._queries, encoder._splitter_tokenizer = False, 0, None
        encoder.model = SimpleNamespace(tokenizer=CharacterTokenizer())
        encoder.model.tokenizer.mutable_settings = {'padding': False}
        encoder._load = lambda: None
        tokenizer = encoder.tokenizer
        encoder.model.tokenizer.mutable_settings['padding'] = True
        self.assertIs(tokenizer, encoder.tokenizer)
        self.assertIsNot(tokenizer, encoder.model.tokenizer)
        self.assertFalse(tokenizer.mutable_settings['padding'])

    def test_index_binary_vectors_reuse_and_parent_ranking(self):
        first, reader = self.build()
        self.assertEqual(first['parents'], 4)
        self.assertEqual(first['encoded'], 4)
        response = reader.search('만들던 앱 관련 세션 보여줘')
        self.assertEqual([r['key'] for r in response['results']], ['session:1'])
        self.assertIn('#event-synthetic-event-1', response['results'][0]['href'])
        self.assertFalse(response['partial'])
        second = prepare(self.config, self.encoder, self.profile)
        self.assertEqual(second['encoded'], 0)
        self.assertEqual(second['reused'], 4)
        with open_index(folder(self.config)/'index.sqlite3') as connection:
            self.assertTrue(meta(connection)['complete'])
            self.assertEqual(connection.execute('SELECT length(value) FROM vectors LIMIT 1').fetchone()[0],512*4)

    def test_changed_deleted_and_disabled_sources_never_leak_old_evidence(self):
        _, reader = self.build()
        old = reader.search('앱')['results'][0]['evidence'][0]
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE activity_events SET text='정원' WHERE session_id=1")
            connection.execute('UPDATE context_roots SET enabled=0')
        response = reader.search('앱')
        self.assertEqual(response['results'], [])
        self.assertTrue(response['partial'])
        with self.assertRaisesRegex(ValueError, 'CHANGED'):
            reader.evidence(old['id'], old['generation'])

    def test_interrupted_generation_keeps_active_and_resumes_vectors(self):
        _, reader = self.build()
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE context_documents SET body=? WHERE id=1", ('앱 내용. '*350,))
        initial_calls = len(self.encoder.calls)
        with self.assertRaises(InterruptedError):
            prepare(self.config, self.encoder, self.profile,
                    stopped=lambda: len(self.encoder.calls)>initial_calls)
        self.assertTrue((folder(self.config)/'index.sqlite3').is_file())
        resumed = prepare(self.config, self.encoder, self.profile)
        self.assertGreater(resumed['reused'], 0)
        self.assertFalse((folder(self.config)/'building.sqlite3').exists())
        self.assertFalse(reader.search('앱')['partial'])

    def test_lexical_and_threshold_are_separate(self):
        _, reader = self.build()
        self.assertGreater(reader.search('atlas', mode='lexical')['total'],0)
        self.assertEqual(reader.search('찾을 수 없는 독특한 질문', mode='dense')['total'],0)
        self.assertGreater(reader.search('찾을 수 없는 독특한 질문', mode='dense',cutoff=0)['total'],0)

    def test_weak_lexical_match_cannot_displace_stronger_semantic_evidence(self):
        import numpy as np
        _, reader = self.build()
        # Only the weaker document matches the lexical query. Its hundreds of
        # repeated terms must not overcome the stronger Session's cosine score.
        with sqlite3.connect(folder(self.config)/'index.sqlite3') as connection:
            connection.execute("UPDATE terms SET tokens='unrelated'")
            connection.execute("UPDATE terms SET tokens=? WHERE rowid IN (SELECT id FROM fragments WHERE parent_key='document:1')",
                               ('앱 ' * 600,))
        reader._load()
        reader._matrix[:] = 0
        for i, key in enumerate(reader._parent_keys):
            score = .8 if key == 'session:1' else .55 if key == 'document:1' else .2
            reader._matrix[i, :2] = [score, np.sqrt(1-score*score)]
        result = reader.search('앱')
        self.assertEqual([row['key'] for row in result['results']], ['session:1', 'document:1'])
        self.assertEqual(result['ranking'], 'semantic-dual-view-v3')
        self.assertEqual(result['results'][0]['score'], .8)
        self.assertAlmostEqual(result['results'][0]['rank_score'], .8)
        self.assertEqual(reader.search('앱', mode='lexical')['results'][0]['key'], 'document:1')

    def test_exact_identifier_still_enters_below_semantic_cutoff(self):
        _, reader = self.build()
        reader._load()
        # ContractEncoder encodes atlas on axis0, while every stored vector is
        # deliberately orthogonal. Only actual literal evidence may enter.
        reader._matrix[:] = 0
        reader._matrix[:, 3] = 1
        result = reader.search('atlas')
        self.assertEqual([row['key'] for row in result['results']], ['session:1'])
        self.assertEqual(result['results'][0]['match_reason'], 'exact')
        self.assertEqual(result['results'][0]['score'], 0)
        self.assertEqual(reader.search('atlas', mode='dense')['total'], 0)
        vector = self.encoder.encode(['atlas'], query=True)
        with patch.object(self.encoder, 'encode', return_value=vector):
            self.assertEqual(reader.search('atla')['total'], 0)

    def test_focus_query_preserves_topic_actions_and_uncertain_language(self):
        for query, focused in [
            ('내가 작업하던 응답 속도 개선 관련 세션을 찾아줘', '응답 속도 개선'),
            ('화면 배치를 조정한 문서만', '화면 배치를 조정한'),
            ('배포 자동화와 빌드 과정을 고쳤던 세션 찾아줘', '배포 자동화와 빌드 과정을 고쳤던'),
            ('처음 온 동료가 프로젝트를 실행하도록 안내한 기록 찾아줘', '처음 온 동료가 프로젝트를 실행하도록 안내한'),
            ('Find work about reducing query latency', 'reducing query latency'),
        ]:
            self.assertEqual(focus_query(query), focused)
        for query in ('"화면 배치" 관련 세션 찾아줘', '화면 배치 말고 야간 배치 찾아줘',
                      '로그가 남지 않게 고친 기록 찾아줘', '네트워크 없이 쓰던 앱 찾아줘',
                      'Find work about uploads without a network',
                      'atlas', 'redirect_uri', '문서만', '찾아줘'):
            self.assertEqual(focus_query(query), query)

    def test_dual_query_retrieves_both_views_and_keeps_original_scope_and_links(self):
        import numpy as np
        _, reader = self.build()
        reader._load()
        # Original and focused views attend to different sources. Admission is
        # their union; ordering is their mean and ignores fragment multiplicity.
        query = '앱 관련 세션 찾아줘'
        reader._matrix[:] = 0
        for i, key in enumerate(reader._parent_keys):
            reader._matrix[i, :3] = ([.7, .1, np.sqrt(.5)] if key == 'session:1' else
                                    [.2, .8, np.sqrt(.32)] if key == 'session:2' else
                                    [.1, .1, np.sqrt(.98)])
        original = self.encoder.encode
        def encode(texts, query=False):
            if not query:
                return original(texts, query=False)
            self.assertEqual(texts, ['앱 관련 세션 찾아줘', '앱'])
            vectors = np.zeros((2, 512), dtype=np.float32)
            vectors[0, 0] = vectors[1, 1] = 1
            return vectors
        with patch.object(self.encoder, 'encode', side_effect=encode):
            response = reader.search(query, cutoff=.6)
        self.assertEqual([r['key'] for r in response['results']], ['session:2', 'session:1'])
        self.assertAlmostEqual(response['results'][0]['rank_score'], .5)
        self.assertEqual(response['results'][0]['score'], .8)
        self.assertEqual(response['conditions']['kind'], 'session')
        self.assertEqual(response['timing']['query_views'], 2)
        from urllib.parse import parse_qs, urlsplit
        return_url = parse_qs(urlsplit(response['results'][0]['href']).query)['search_return'][0]
        self.assertEqual(parse_qs(urlsplit(return_url).query)['q'], [query])

    def test_single_view_for_identifiers_quotes_notices_dense_and_empty_queries(self):
        _, reader = self.build()
        for query in ('atlas', '"앱" 관련 세션 찾아줘', '세션 말고 문서 찾아줘',
                      '지난주 이후 앱 세션 찾아줘'):
            response = reader.search(query)
            self.assertEqual(response['timing']['query_views'], 1)
            self.assertEqual(self.encoder.calls[-1], (True, [query]))
        response = reader.search('앱 관련 세션 찾아줘', mode='dense')
        self.assertEqual(response['timing']['query_views'], 1)
        before = len(self.encoder.calls)
        for mode in ('hybrid', 'lexical'):
            self.assertEqual(reader.search('', mode=mode)['timing']['query_views'], 0)
        self.assertEqual(len(self.encoder.calls), before)

    def test_dual_query_rejects_wrong_shape_zero_and_nonfinite_vectors(self):
        import numpy as np
        _, reader = self.build()
        for vectors in (np.ones((1, 512)), np.ones((2, 511)), np.zeros((2, 512)),
                        np.full((2, 512), np.nan), np.full((2, 512), np.inf)):
            with self.subTest(shape=vectors.shape), patch.object(self.encoder, 'encode', return_value=vectors):
                with self.assertRaisesRegex(ValueError, 'INVALID_SEARCH_VECTORS'):
                    reader.search('앱 관련 세션 찾아줘')

    def test_broad_search_fetches_text_only_for_the_current_page(self):
        _, reader = self.build()
        reader._load()
        statements = []
        reader._connection.set_trace_callback(statements.append)
        all_results = reader.search('앱', cutoff=0, page_size=100)
        statements.clear()
        page = reader.search('앱', cutoff=0, page=2, page_size=1)
        self.assertEqual(page['total'], all_results['total'])
        self.assertEqual(page['results'][0]['key'], all_results['results'][1]['key'])
        fetches = [s for s in statements if s.startswith('SELECT * FROM fragments WHERE id=')]
        self.assertEqual(len(fetches), len(page['results'][0]['evidence']))
        self.assertLessEqual(len(fetches), 3)

    def test_repeated_fragments_do_not_change_parent_scores_or_pagination(self):
        _, reader = self.build()
        before = reader.search('앱')['results']
        with sqlite3.connect(folder(self.config)/'index.sqlite3') as connection:
            template = connection.execute("SELECT input_hash,body_hash,text,context,locator,id FROM fragments WHERE parent_key='document:1'").fetchone()
            terms = connection.execute('SELECT tokens FROM terms WHERE rowid=?', (template[5],)).fetchone()[0]
            for ordinal in range(1, 30):
                cursor = connection.execute("INSERT INTO fragments(parent_key,ordinal,input_hash,body_hash,text,context,locator) VALUES ('document:1',?,?,?,?,?,?)",
                                            (ordinal, *template[:5]))
                connection.execute('INSERT INTO terms(rowid,tokens) VALUES (?,?)', (cursor.lastrowid, terms))
        after = reader.search('앱')['results']
        self.assertEqual([(r['key'], r['score'], r['rank_score']) for r in before],
                         [(r['key'], r['score'], r['rank_score']) for r in after])
        self.assertEqual(len(next(r for r in after if r['key']=='document:1')['evidence']), 1)
        paged = [reader.search('앱', page=i+1, page_size=1)['results'][0]['key'] for i in range(len(after))]
        self.assertEqual(paged, [r['key'] for r in after])

    def test_lexical_scope_is_applied_before_the_candidate_cap(self):
        _, reader = self.build()
        with sqlite3.connect(folder(self.config)/'index.sqlite3') as connection:
            connection.execute("UPDATE terms SET tokens='unrelated'")
            connection.execute("UPDATE terms SET tokens='앱 filler filler filler filler' WHERE rowid IN (SELECT id FROM fragments WHERE parent_key='document:1')")
            template = connection.execute("SELECT input_hash,body_hash,context,locator FROM fragments WHERE parent_key='session:1'").fetchone()
            for ordinal in range(1, 510):
                cursor = connection.execute("INSERT INTO fragments(parent_key,ordinal,input_hash,body_hash,text,context,locator) VALUES ('session:1',?,?,?,?,?,?)",
                                            (ordinal, template[0], template[1], '앱', template[2], template[3]))
                connection.execute('INSERT INTO terms(rowid,tokens) VALUES (?,?)', (cursor.lastrowid, '앱'))
        result = reader.search('앱 문서만', mode='lexical')
        self.assertEqual([row['key'] for row in result['results']], ['document:1'])
        # Current permission/revision also precedes the cap, even without an
        # explicit kind filter: all the high-ranked Session hits are now stale.
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE activity_events SET text='수정된 본문' WHERE session_id=1")
        result = reader.search('앱', mode='lexical')
        self.assertEqual([row['key'] for row in result['results']], ['document:1'])
        self.assertTrue(result['partial'])

    def test_unchanged_refresh_preserves_generation_without_splitting(self):
        _, reader = self.build()
        before = reader.search('앱')['results'][0]['evidence'][0]['generation']
        with patch('localbrain.natural_search.index.molecularize', side_effect=AssertionError('unchanged splitting')):
            result = prepare(self.config, self.encoder, self.profile)
        self.assertTrue(result['unchanged'])
        self.assertEqual(result['encoded'],0)
        self.assertEqual(reader.search('앱')['results'][0]['evidence'][0]['generation'],before)

    def test_incremental_refresh_only_splits_changed_parents(self):
        self.build()
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE context_documents SET body=body || ' 앱 변경 사항.' WHERE id=1")
        seen=[]
        original=molecularize
        def capture(source, tokenizer, profile):
            seen.append(source.key)
            return original(source,tokenizer,profile)
        with patch('localbrain.natural_search.index.molecularize',side_effect=capture):
            prepare(self.config,self.encoder,self.profile)
        self.assertEqual(seen,['document:1'])

    def test_cached_generation_replay_still_commits_bounded_batches(self):
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute('UPDATE activity_events SET text=? WHERE session_id=1', ('앱 작업 내용.\n\n'*250,))
        self.build()
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE sessions SET last_event_at='2026-10-07T00:00:00Z' WHERE id=1")
        counts = []
        result = prepare(self.config, self.encoder, self.profile, progress=lambda value: counts.append(value['fragments']))
        self.assertEqual(result['encoded'], 0)
        self.assertLessEqual(max(b-a for a,b in zip(counts, counts[1:])), self.encoder.batch_size)

    def test_explicit_rebuild_recomputes_and_duplicate_evidence_is_collapsed(self):
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,source_line) SELECT 'duplicate',session_id,10,event_type,role,text,10 FROM activity_events WHERE session_id=1")
        _, reader = self.build()
        item = next(item for item in reader.search('앱')['results'] if item['key']=='session:1')
        self.assertEqual(len(item['evidence']),1)
        self.assertGreater(prepare(self.config,self.encoder,self.profile,force=True)['encoded'],0)

    def test_calendar_type_and_ambiguous_exclusion(self):
        now = datetime(2026,10,12,12,tzinfo=ZoneInfo('Asia/Seoul'))
        value = interpret('지난주 앱 관련 세션 보여줘','Asia/Seoul',now)
        self.assertEqual(value.kind, 'session')
        self.assertTrue(value.start.startswith('2026-10-05'))
        self.assertTrue(value.end.startswith('2026-10-12'))
        broad = interpret('지난주 말고 이번주 배포 작업은 제외','Asia/Seoul',now)
        self.assertFalse(broad.start)
        self.assertTrue(broad.notices)
        literal = interpret('앱 “staging” 문구는 제외')
        self.assertEqual(literal.exclude,['staging'])
        combined = interpret('지난주 문서만 앱 “staging” 문구는 제외','Asia/Seoul',now)
        self.assertEqual(combined.kind, 'document')
        self.assertTrue(combined.start)
        self.assertEqual(combined.exclude, ['staging'])
        scoped = interpret('지난주 문서만 배포 작업은 제외', 'Asia/Seoul', now)
        self.assertEqual(scoped.kind, 'document')
        self.assertTrue(scoped.start)
        self.assertTrue(scoped.notices)
        for query in ['지난주 이후 앱 작업', '오늘의집 앱 작업', '지난주말 앱 작업', '지난주 작업은 제외']:
            self.assertFalse(interpret(query, 'Asia/Seoul', now).start, query)
        quoted = interpret('"지난주 계획" 문서만', 'Asia/Seoul', now)
        self.assertFalse(quoted.start)
        self.assertEqual(quoted.kind, 'document')
        mixed = interpret('"staging" 제외 배포 작업은 제외')
        self.assertEqual(mixed.exclude, ['staging'])
        self.assertTrue(mixed.notices)

    def test_cache_and_durable_settings_are_separate(self):
        save_settings(self.config, self.profile)
        self.build()
        self.assertTrue((self.config.data_dir/'natural-search.json').is_file())
        self.assertTrue((self.config.cache_dir/'natural-search/index.sqlite3').is_file())
        self.assertFalse((self.config.data_dir/'natural-search').exists())

    def test_invalid_settings_are_a_bounded_error(self):
        save_settings(self.config, self.profile)
        path = self.config.data_dir/'natural-search.json'
        for text in ('[]', '{"version":1,"enabled":true}',
                     '{"version":1,"enabled":true,"profile":{"cutoff":"invalid"}}'):
            path.write_text(text)
            with self.assertRaisesRegex(ValueError, '^INVALID_SEARCH_SETTINGS$'):
                read_settings(self.config)

    def test_external_writer_and_stale_progress_are_distinct(self):
        save_settings(self.config, self.profile)
        service = SearchService(self.config, ContractEncoder)
        with writer(self.config):
            self.assertEqual(service.status()['state'], 'preparing')
            self.assertFalse(service.status()['can_cancel'])
        self.assertEqual(service.status()['state'], 'partial')

    def test_corrupt_vectors_are_rejected_and_rebuild_recovers(self):
        import numpy as np
        _, reader = self.build()
        for value in (b'bad', np.full(512, np.nan, dtype='<f4').tobytes(),
                      np.zeros(512, dtype='<f4').tobytes()):
            with sqlite3.connect(folder(self.config)/'index.sqlite3') as connection:
                connection.execute('UPDATE vectors SET value=?', (value,))
            with self.assertRaisesRegex(ValueError, '^INVALID_SEARCH_VECTORS$'):
                reader.search('앱')
        prepare(self.config, self.encoder, self.profile, force=True)
        self.assertGreater(reader.search('앱')['total'],0)

    def test_empty_corpus_is_not_model_failure(self):
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE sessions SET index_policy='metadata_only'")
            connection.execute('UPDATE context_roots SET enabled=0')
        class EmptyEncoder:
            contract = self.encoder.contract
            @property
            def tokenizer(self):
                raise AssertionError('An empty corpus must not load the model')
        result = prepare(self.config, EmptyEncoder(), self.profile)
        reader = Retriever(self.config, self.profile, self.encoder)
        self.addCleanup(reader.close)
        self.assertEqual(result['state'],'no-data')
        self.assertEqual(reader.search('앱')['total'],0)

    def test_worker_activation_sync_refresh_and_cache_loss(self):
        service = SearchService(self.config, ContractEncoder)
        self.addCleanup(service.stop)
        service.start()
        self.assertEqual(service.status()['state'], 'disabled')
        self.assertFalse(folder(self.config).exists())
        service.request_prepare()

        def wait_for(predicate):
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if predicate():
                    return
                time.sleep(0.02)
            self.fail('Search worker did not reach the expected state')

        wait_for(lambda: service.status()['state']=='ready')
        self.assertGreater(service.search('앱')['total'], 0)
        with sqlite3.connect(self.config.database_path) as connection:
            connection.execute("UPDATE activity_events SET text='정원 작업' WHERE session_id=1")
        service._wake.set()
        wait_for(lambda: not service._running and not service.search('앱')['partial'])
        (folder(self.config)/'index.sqlite3').unlink()
        service._wake.set()
        wait_for(lambda: (folder(self.config)/'index.sqlite3').is_file() and service.status()['state']=='ready')


if __name__ == '__main__':
    unittest.main()
