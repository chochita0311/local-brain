#!/usr/bin/env python3
"""Optional synthetic bulk embedding cost; run without another active model job."""

import argparse
import json
import time
from pathlib import Path

from localbrain.config import settings
from localbrain.natural_search.model import SearchEncoder
from localbrain.natural_search.molecules import Profile, bounded_context
from localbrain.runtime_storage import private_directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = private_directory(args.output)
    if (root / 'throughput.json').exists():
        raise SystemExit('Fresh throughput output required')
    import numpy as np
    import torch
    encoder = SearchEncoder(settings, Profile(), device='mps')
    text = '검토 기록을 바탕으로 문서의 본문과 원래 위치를 보존하고 수정된 항목만 새로 계산한다.\n' * 100
    body = bounded_context(encoder.tokenizer, text, 510)[0]
    texts = ['Title: Batch {}\n\n'.format(i)+body for i in range(64)]
    rows, reference = [], None
    for dtype in ('float32', 'float16'):
        if dtype == 'float16':
            encoder.model.half()
        for batch in (8, 16, 32, 64):
            encoder.batch_size = batch
            started = time.perf_counter()
            vectors = encoder.encode(texts)
            seconds = time.perf_counter()-started
            if reference is None:
                reference = vectors
            row = {'dtype': dtype, 'batch': batch, 'seconds': seconds,
                   'vectors_per_second': 64/seconds,
                   'min_agreement_cosine': float((vectors*reference).sum(axis=1).min()),
                   'finite': bool(np.isfinite(vectors).all()),
                   'mps_driver_bytes': torch.mps.driver_allocated_memory()}
            rows.append(row)
            print(json.dumps(row), flush=True)
    (root / 'throughput.json').write_text(json.dumps({'contract': encoder.contract,
        'rows': rows, 'memory_scope': 'Driver allocations retained across trials, not independent per-batch peaks.'}, indent=2)+'\n')


if __name__ == '__main__':
    main()
