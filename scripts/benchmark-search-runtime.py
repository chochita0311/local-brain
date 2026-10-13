#!/usr/bin/env python3
"""Frozen default on new authored topics, plus real-model refresh contention."""

import argparse
import json
import resource
import sqlite3
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))

from natural_search_benchmark import aggregate, metrics
from natural_search_holdout import seed
from localbrain.config import settings
from localbrain.natural_search.index import folder, prepare
from localbrain.natural_search.model import SearchEncoder
from localbrain.natural_search.molecules import Profile
from localbrain.natural_search.retrieval import Retriever
from localbrain.natural_search.source import digest, source_connection
from localbrain.queries import search as keyword_search
from localbrain.runtime_storage import private_directory


def percentiles(values):
    import numpy as np
    return {name: round(float(np.percentile(values, quantile)), 2)
            for name, quantile in [('p50', 50), ('p95', 95)]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = private_directory(args.output)
    if (root / 'corpus').exists():
        raise SystemExit('Fresh runtime comparison output required')
    config, queries, relevance = seed(root / 'corpus')
    profile = Profile(target=512, dimension=512, overlap=0, cutoff=0.45)
    encoder = SearchEncoder(settings, profile, device='mps', batch_size=8)
    tick = time.perf_counter()
    built = prepare(config, encoder, profile)
    report = {'fixture': 'authored-holdout-v1', 'parents': len(relevance), 'queries': len(queries),
              'fixture_sha256': digest([queries, relevance, (ROOT / 'tests/natural_search_holdout.py').read_text()]),
              'profile': dict(target=512, dimension=512, overlap=0, cutoff=0.45),
              'contract': encoder.contract, 'preparation_seconds': round(time.perf_counter()-tick, 3),
              'build': built, 'query_cache': False}
    reader = Retriever(config, profile, encoder)
    try:
        old, selected, samples = [], [], []
        for query in queries:
            with source_connection(config.database_path) as connection:
                rows = keyword_search(connection, query['query'], limit=100)
            old.append(metrics([row['entity_type']+':'+str(row['entity_id']) for row in rows], query['expected']))
            result = reader.search(query['query'])
            selected.append(metrics([row['key'] for row in result['results']], query['expected']))
            samples.append({'id': query['id'], 'metrics': selected[-1], 'timing': result['timing']})
        report.update(old_keyword=aggregate(old), selected=aggregate(selected), cases=samples)
        idle = [reader.search(query['query'])['timing']['total_ms'] for query in queries for _ in range(2)]
        report['idle_ms'] = percentiles(idle)
        before = time.perf_counter()
        unchanged = prepare(config, encoder, profile)
        report['unchanged_refresh'] = {**unchanged, 'observed_seconds': round(time.perf_counter()-before, 3)}

        # Change only one synthetic parent. Its old evidence must immediately disappear.
        with sqlite3.connect(config.database_path) as connection:
            text = '\n\n'.join('추가 관측 {}. 녹음한 소리의 품질을 확인하고 결정을 기록했다.'.format(i)
                               for i in range(800))
            connection.execute('UPDATE activity_events SET text=text || ? WHERE session_id=1', (text,))
        query = next(query for query in queries if query['id'] == 'audio')['query']
        assert reader.search(query)['partial']
        assert all(item['key'] != 'session:1' for item in reader.search('종이 영수증')['results'])
        started, finished = threading.Event(), threading.Event()
        errors, refreshed, concurrent = [], [], []

        def rebuild():
            try:
                refreshed.append(prepare(config, encoder, profile, progress=lambda value: started.set()))
            except Exception as error:
                errors.append(error)
            finally:
                finished.set()

        worker = threading.Thread(target=rebuild)
        worker.start()
        try:
            assert started.wait(10)
            while not finished.is_set():
                concurrent.append(reader.search(query)['timing']['total_ms'])
                finished.wait(0.05)
        finally:
            worker.join()
        if errors:
            raise errors[0]
        assert concurrent and refreshed[0]['encoded'] > 0 and refreshed[0]['reused'] > 0
        assert not reader.search(query)['partial']
        report['concurrent_refresh'] = {'queries': len(concurrent), 'query_ms': percentiles(concurrent),
                                        'build': refreshed[0], 'changed_source_hidden': True}
        files = [path.stat() for path in folder(config).iterdir() if path.is_file()]
        report['final_cache_bytes'] = {'logical': sum(stat.st_size for stat in files),
                                       'allocated': sum(stat.st_blocks * 512 for stat in files)}
        report['peak_process_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (root / 'runtime.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({key: report[key] for key in ('selected', 'old_keyword', 'idle_ms', 'concurrent_refresh', 'peak_process_rss_bytes')}))
    finally:
        reader.close()


if __name__ == '__main__':
    main()
