#!/usr/bin/env python3
"""Actual retrieval + local judge process round trips on authored synthetic data."""

import argparse
import json
import selectors
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from natural_search_benchmark import aggregate, metrics, seed
from localbrain.foundation.config import settings
from localbrain.natural_search.index import prepare
from localbrain.natural_search.model import SearchEncoder
from localbrain.natural_search.molecules import Profile
from localbrain.natural_search.retrieval import Retriever
from localbrain.natural_search.source import digest
from localbrain.foundation.files import private_directory


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--judge-python',required=True)
    parser.add_argument('--role',choices=('laya','reranker'),required=True)
    args=parser.parse_args()
    root=private_directory(args.output)
    if (root/'corpus').exists():raise SystemExit('Fresh comparison output required')
    config,queries,relevance=seed(root/'corpus')
    profile=Profile()
    encoder=SearchEncoder(settings,profile,device='mps',batch_size=16)
    prepare(config,encoder,profile)
    reader=Retriever(config,profile,encoder)
    command=[args.judge_python,'-B',str(ROOT/'scripts/benchmark-search-judges.py'),
             '--assets',str(args.assets),'--output',str(root/'judge'),'--role',args.role,'--device','mps','--serve']
    if args.role=='laya':command.append('--laya-fp32')
    server=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    selector=selectors.DefaultSelector()
    selector.register(server.stdout,selectors.EVENT_READ)

    def receive():
        if not selector.select(90):raise RuntimeError('Judge response timed out')
        line=server.stdout.readline()
        if not line:raise RuntimeError('Judge process exited')
        return json.loads(line)

    try:
        ready=receive()
        if not ready.get('ready'):raise RuntimeError('Judge did not become ready')
        report={'role':args.role,'candidate_limit':20,'judge_threshold':0.5,'transport':'local stdin/stdout; no network',
                'fixture_version':'authored-korean-search-v2',
                'fixture_sha256':digest([queries,relevance,(ROOT/'tests/natural_search_benchmark.py').read_text()]),
                'retrieval_contract':encoder.contract,'candidate_cutoff':0,
                'cold_judge_load_seconds':ready['load_seconds'],'query_cache':False,'modes':[]}
        import numpy as np
        for mode in ('hybrid','lexical'):
            rows=[]
            for repeat in range(2):
                for query in queries:
                    tick=time.perf_counter()
                    result=reader.search(query['query'],mode=mode,cutoff=0,page_size=20)
                    candidates=[{'key':item['key'],'title':item['title'],'text':item['evidence'][0]['text']} for item in result['results']]
                    server.stdin.write(json.dumps({'query':query['query'],'candidates':candidates},ensure_ascii=False)+'\n')
                    server.stdin.flush()
                    judged=receive()
                    ranked=sorted(zip(candidates,judged['scores']),key=lambda value:-value[1])
                    keys=[item['key'] for item,score in ranked if score>=0.5]
                    rows.append({'id':query['id'],'repeat':repeat,'total_ms':round((time.perf_counter()-tick)*1000,3),
                                 'retrieval_ms':result['timing']['total_ms'],'judge_ms':judged['judge_ms'],
                                 'metrics':metrics(keys,query['expected'])})
            entry={'mode':mode,'samples':len(rows),'metrics':aggregate([row['metrics'] for row in rows]),
                   'timing':{field:{'p50':round(float(np.percentile([row[field] for row in rows],50)),2),
                                    'p95':round(float(np.percentile([row[field] for row in rows],95)),2)}
                             for field in ('total_ms','retrieval_ms','judge_ms')},'queries':rows}
            report['modes'].append(entry)
            print(json.dumps({k:entry[k] for k in ('mode','samples','metrics','timing')}),flush=True)
            (root/'pipeline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    finally:
        reader.close()
        selector.close()
        server.stdin.close()
        try:server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.terminate();server.wait(timeout=15)
        server.stdout.close()


if __name__=='__main__':main()
