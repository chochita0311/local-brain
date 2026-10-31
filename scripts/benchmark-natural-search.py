#!/usr/bin/env python3
"""Offline, synthetic Qwen retrieval comparison; outputs stay outside Git."""

import argparse
import json
import platform
import resource
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))

from natural_search_benchmark import aggregate, metrics, seed
from localbrain.foundation.config import settings
from localbrain.natural_search.index import prepare
from localbrain.natural_search.model import SearchEncoder
from localbrain.natural_search.molecules import Profile
from localbrain.natural_search.retrieval import Retriever
from localbrain.natural_search.source import digest, source_connection
from localbrain.search.legacy import search as keyword_search
from localbrain.foundation.files import private_directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', default='mps', choices=('mps','cpu'))
    parser.add_argument('--dtype', default='float32', choices=('float32','float16'))
    parser.add_argument('--batch-size', type=int, default=16)
    args = parser.parse_args()
    root = private_directory(args.output)
    if (root/'corpus').exists():
        raise SystemExit('Use a fresh owned output directory for a frozen comparison.')
    config, queries, relevance = seed(root/'corpus')
    import numpy as np
    import torch
    started = time.perf_counter()
    encoder = SearchEncoder(settings, Profile(dimension=1024), device=args.device, batch_size=args.batch_size)
    encoder._load()
    if args.dtype == 'float16':
        encoder.model.half()
    if args.device == 'mps':
        torch.mps.synchronize()
    loaded = time.perf_counter()
    encoder.contract['dtype'] = str(next(encoder.model.parameters()).dtype)
    document_cache, query_cache = {}, {}
    encode_seconds = [0.0]

    class ProjectionEncoder:
        def __init__(self, profile):
            self.profile = profile
            self.contract = {**encoder.contract, 'dimension':profile.dimension,
                             'benchmark_projection':'matryoshka-prefix-renormalized-v1'}
            self.batch_size = encoder.batch_size
            self.tokenizer = encoder.tokenizer
            self.cache_queries = True

        def encode(self, texts, query=False):
            cache = query_cache if query else document_cache
            keys = [digest(text) for text in texts]
            missing = list(dict.fromkeys(key for key in keys if key not in cache))
            if query and not self.cache_queries:
                values = encoder.encode(texts, query=True)
            else:
                if missing:
                    by_key = dict(zip(keys,texts))
                    tick = time.perf_counter()
                    values = encoder.encode([by_key[key] for key in missing], query=query)
                    encode_seconds[0] += time.perf_counter()-tick
                    cache.update(zip(missing,values))
                values = np.stack([cache[key] for key in keys])
            values = np.asarray(values)[:, :self.profile.dimension]
            return values / np.linalg.norm(values,axis=1,keepdims=True)

    report = {'fixture_version':'authored-korean-search-v2','parents':len(relevance),'queries':len(queries),
              'fixture_sha256':digest([queries,relevance, (ROOT/'tests/natural_search_benchmark.py').read_text()]),
              'device':args.device,'runtime':encoder.contract,'dtype':encoder.contract['dtype'],
              'batch_size':args.batch_size,'threads':torch.get_num_threads(),'python':platform.python_version(),
              'cold_model_load_seconds':round(loaded-started,3),'profiles':[]}
    old_rows=[]
    for query in queries:
        with source_connection(config.database_path) as connection:
            found=keyword_search(connection,query['query'],limit=100)
        old_rows.append(metrics([item['entity_type']+':'+str(item['entity_id']) for item in found],query['expected']))
    report['old_keyword']=aggregate(old_rows)
    candidates=[]
    for target in (256,512,768):
        for dimension in (1024,512):
            profile = Profile(target=target,dimension=dimension)
            current = replace(config,cache_dir=root/f'index-{target}-{dimension}')
            projected = ProjectionEncoder(profile)
            tick=time.perf_counter()
            built=prepare(current,projected,profile)
            reader=Retriever(current,profile,projected)
            entry={'target':target,'dimension':dimension,'fragments':built['fragments'],
                   'index_bytes':(current.cache_dir/'natural-search/index.sqlite3').stat().st_size,
                   'prepare_seconds_with_cross_profile_reuse':round(time.perf_counter()-tick,3),'modes':{}}
            try:
                for mode in ('lexical','dense','hybrid'):
                    for cutoff in ([0] if mode=='lexical' else [0,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8]):
                        rows=[]; per_query=[]
                        for query in queries:
                            result=reader.search(query['query'],mode=mode,cutoff=cutoff,page_size=100)
                            keys=[item['key'] for item in result['results']]
                            row=metrics(keys,query['expected']);rows.append(row)
                            per_query.append({'id':query['id'],'keys':keys[:10],
                                              'top_score':result['results'][0]['score'] if keys else None,**row})
                            if target==512 and dimension==512 and cutoff==0 and mode in {'hybrid','lexical'}:
                                # Export identical parent candidates for separate local judges.
                                candidates.append({**query,'candidate_mode':mode,'candidates':[
                                    {'key':item['key'],'title':item['title'],'score':item['score'],
                                     'text':item['evidence'][0]['text']} for item in result['results'][:50]]})
                        entry['modes'][f'{mode}:{cutoff}']={'metrics':aggregate(rows),'queries':per_query}
                if target==512 and dimension==512:
                    projected.cache_queries=False
                    timings=[]
                    for _ in range(3):
                        for query in queries[:12]:
                            timings.append(reader.search(query['query'],cutoff=0.55)['timing'])
                    entry['warm_uncached_query_ms']={field:{'p50':round(float(np.percentile([r[field] for r in timings],50)),2),
                         'p95':round(float(np.percentile([r[field] for r in timings],95)),2)} for field in timings[0]}
                report['profiles'].append(entry)
                print(json.dumps({'target':target,'dimension':dimension,'fragments':built['fragments'],
                                  'hybrid07':entry['modes']['hybrid:0.7']['metrics']}),flush=True)
                (root/'retrieval.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            finally:
                reader.close()
    report.update(total_seconds=round(time.perf_counter()-started,3),actual_encoding_seconds=round(encode_seconds[0],3),
                  peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  mps_allocated_bytes=torch.mps.current_allocated_memory() if args.device=='mps' else None,
                  mps_driver_bytes=torch.mps.driver_allocated_memory() if args.device=='mps' else None,
                  projection_reuse='Documents/queries embedded once at 1024; prefix512 re-normalized. Accuracy-loop query cache excluded from latency.')
    (root/'retrieval.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (root/'candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'complete':True,'seconds':report['total_seconds'],'peak_rss_bytes':report['peak_rss_bytes']}),flush=True)


if __name__=='__main__':
    main()
