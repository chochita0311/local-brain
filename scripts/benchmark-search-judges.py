#!/usr/bin/env python3
"""Offline candidate judges in an isolated runtime; no product dependency."""

import argparse
import hashlib
import json
import os
import platform
import resource
import shutil
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

for name in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','HF_HUB_DISABLE_IMPLICIT_TOKEN'):
    os.environ[name]='1'
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from natural_search_benchmark import aggregate, metrics


class Judge:
    def __init__(self, role, assets, output, device='mps', laya_fp32=False):
        import torch
        self.torch, self.role, self.device=torch,role,device
        self.budget=4096
        asset=assets[role]
        snapshot=Path(asset['path'])
        for relative, expected in asset['hashes'].items():
            h=hashlib.sha256()
            with (snapshot/relative).open('rb') as stream:
                for block in iter(lambda:stream.read(1048576),b''):h.update(block)
            if h.hexdigest()!=expected:raise ValueError('MODEL_ASSET_CHANGED')
        started=time.perf_counter()
        if role=='laya':
            import laya
            # The upstream loader patches tokenizer metadata. Keep its adaptation
            # private while sharing immutable weights with the public Hub cache.
            runtime=output/'laya-compatible-metadata'
            runtime.mkdir(parents=True,exist_ok=True)
            for relative in asset['hashes']:
                original=snapshot/relative; target=runtime/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():continue
                if original.suffix=='.safetensors':target.symlink_to(original.resolve())
                else:shutil.copyfile(original,target)
            self.model=laya.load(str(runtime),device=device,token=False,backend='eager')
            if str(self.model.device)!=device:raise ValueError('UNEXPECTED_DEVICE_FALLBACK')
            if laya_fp32:
                self.model.amp_enabled=False
            self.dtype={'weights':str(next(self.model.model.parameters()).dtype),
                        'batch_compute':'torch.float32' if not self.model.amp_enabled else str(self.model.dtype),
                        'amp_min_rows':self.model.mps_amp_min_rows}
        else:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False,padding_side='left')
            self.model=AutoModelForCausalLM.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False,
                    dtype=torch.float32,attn_implementation='eager').to(device).eval()
            self.no=self.tokenizer.convert_tokens_to_ids('no'); self.yes=self.tokenizer.convert_tokens_to_ids('yes')
            self.prefix=self.tokenizer.encode('<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be "yes" or "no".<|im_end|>\n<|im_start|>user\n',add_special_tokens=False)
            self.suffix=self.tokenizer.encode('<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n',add_special_tokens=False)
            self.dtype={'weights':str(next(self.model.parameters()).dtype),'batch_compute':'torch.float32','attention':'eager'}
        if device=='mps':torch.mps.synchronize()
        self.load_seconds=time.perf_counter()-started

    def score(self, query, candidates):
        if not candidates:return [],0
        started=time.perf_counter(); scores=[]
        if self.role=='laya':
            states=['Query: '+query+'\nDocument title: '+item['title']+'\nDocument: '+item['text'] for item in candidates]
            questions={'relevant':{'type':'noul','instructions':'Does the document contain relevant evidence for the search query? Judge topic relevance, not whether it literally repeats the query.'}}
            rows=self.model.predict_batch(states,questions,batch_size=8,lang='ko',max_len=self.budget,head_max_len=256)
            for row in rows:
                if row.get('usage',{}).get('truncated') or row.get('usage',{}).get('state_tokens_dropped',0):
                    raise ValueError('JUDGE_INPUT_TRUNCATED')
                scores.append(row['answers']['relevant']['noul'])
        else:
            encoded=[]
            for item in candidates:
                text='<Instruct>: Given a search query, retrieve relevant passages from work sessions and documents.\n<Query>: '+query+'\n<Document>: '+item['title']+'\n'+item['text']
                ids=self.prefix+self.tokenizer.encode(text,add_special_tokens=False)+self.suffix
                if len(ids)>self.budget:raise ValueError('JUDGE_INPUT_TOO_LONG')
                encoded.append(ids)
            with self.torch.inference_mode():
                for start in range(0,len(encoded),8):
                    batch=self.tokenizer.pad({'input_ids':encoded[start:start+8]},padding=True,return_tensors='pt').to(self.device)
                    logits=self.model(**batch,logits_to_keep=1).logits[:,-1,[self.no,self.yes]].float()
                    scores.extend(self.torch.softmax(logits,dim=-1)[:,1].cpu().tolist())
        if self.device=='mps':self.torch.mps.synchronize()
        if not all(self.torch.isfinite(self.torch.tensor(scores))):raise ValueError('INVALID_JUDGE_SCORES')
        return scores,round((time.perf_counter()-started)*1000,3)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--candidates',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--role',choices=('laya','reranker'),required=True)
    parser.add_argument('--device',choices=('mps','cpu'),default='mps')
    parser.add_argument('--serve',action='store_true')
    parser.add_argument('--laya-fp32',action='store_true',help='Explicitly disable Laya autocast for a separately recorded precision trial')
    args=parser.parse_args()
    from localbrain.foundation.files import private_directory
    output=private_directory(args.output)
    assets=json.loads(args.assets.read_text())
    started=time.perf_counter()
    with redirect_stdout(sys.stderr):
        judge=Judge(args.role,assets,output,args.device,args.laya_fp32)
    import numpy as np
    import torch,transformers
    report={'role':args.role,'asset':{k:v for k,v in assets[args.role].items() if k!='path'},
            'device':args.device,'dtype':judge.dtype,'budget':judge.budget,'batch_size':8,
            'cold_load_seconds':round(judge.load_seconds,3),'torch':torch.__version__,
            'transformers':transformers.__version__,'python':platform.python_version(),'threads':torch.get_num_threads(),
            'truncated_inputs':0,'configurations':[]}
    if args.serve:
        print(json.dumps({'ready':True,'load_seconds':judge.load_seconds}),flush=True)
        for line in sys.stdin:
            request=json.loads(line)
            with redirect_stdout(sys.stderr):
                scores,ms=judge.score(request['query'],request['candidates'])
            print(json.dumps({'scores':scores,'judge_ms':ms}),flush=True)
        return
    if not args.candidates:parser.error('--candidates required outside serve mode')
    cases=json.loads(args.candidates.read_text())
    report['candidate_manifest_sha256']=hashlib.sha256(args.candidates.read_bytes()).hexdigest()
    # Warmup is explicitly excluded from warm latency samples.
    sample=next(case for case in cases if case['candidates'])
    judge.score(sample['query'],sample['candidates'][:2])
    for mode in ('hybrid','lexical'):
        selected=[case for case in cases if case['candidate_mode']==mode]
        for count in (10,20,50):
            timings=[];runs=[]
            for case in selected:
                candidates=case['candidates'][:count]
                scores,ms=judge.score(case['query'],candidates)
                timings.append(ms)
                ranked=sorted(zip(candidates,scores),key=lambda value:-value[1])
                runs.append({'id':case['id'],'candidate_recall':sum(x['key'] in case['expected'] for x in candidates)/len(case['expected']) if case['expected'] else None,
                             'judge_ms':ms,'scores':[{**item,'judge_score':score} for item,score in ranked],
                             'metrics':{str(cutoff):metrics([item['key'] for item,score in ranked if score>=cutoff],case['expected']) for cutoff in (0,0.5,0.7)}})
            entry={'candidate_mode':mode,'candidate_limit':count,
                   'judge_ms':{'p50':round(float(np.percentile(timings,50)),2),'p95':round(float(np.percentile(timings,95)),2)},
                   'metrics':{str(cutoff):aggregate([row['metrics'][str(cutoff)] for row in runs]) for cutoff in (0,0.5,0.7)},'queries':runs}
            report['configurations'].append(entry)
            (output/'judgment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({key:entry[key] for key in ('candidate_mode','candidate_limit','judge_ms','metrics')}),flush=True)
    report.update(total_seconds=round(time.perf_counter()-started,3),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  mps_allocated_bytes=torch.mps.current_allocated_memory() if args.device=='mps' else None,
                  mps_driver_bytes=torch.mps.driver_allocated_memory() if args.device=='mps' else None)
    (output/'judgment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
