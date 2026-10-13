#!/usr/bin/env python3
"""Frozen offline ranking comparison; synthetic inputs, private output receipts."""

import argparse
import hashlib
import json
import platform
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))

from natural_search_benchmark import aggregate, metrics, seed as selection_seed
from natural_search_holdout import seed as previous_holdout_seed
from natural_search_precision import seed as precision_seed
from localbrain.config import settings
from localbrain.natural_search.index import lexical_tokens, prepare
from localbrain.natural_search.model import SearchEncoder
from localbrain.natural_search.molecules import Profile
from localbrain.natural_search.retrieval import RANKING_VERSION, Retriever
from localbrain.runtime_storage import private_directory


def ranking_keys(reader, query, response, memo):
    """Historical RRF and a fixed bonus grid on identical admitted fragments.

    These fixtures use only kind filters. Refuse a new fixture condition rather
    than silently omit its date/exclusion semantics from this comparator.
    """
    import numpy as np
    conditions = response['conditions']
    if conditions['start'] or conditions['end'] or conditions['exclude']:
        raise ValueError('PRECISION_FIXTURE_CONDITION_UNSUPPORTED')
    kind = conditions['kind']
    indices = [i for i, key in enumerate(reader._parent_keys)
               if not kind or reader._parents[key][1]['kind'] == kind]
    vector = memo.encode([query], query=True)[0]
    scores = reader._matrix @ (vector / np.linalg.norm(vector))
    dense_order = sorted(indices, key=lambda i: (-float(scores[i]), reader._ids[i]))
    dense_ranks = {reader._ids[i]: rank + 1 for rank, i in enumerate(dense_order)}
    words = list(dict.fromkeys(lexical_tokens(query)))
    expression = ' OR '.join('"'+word.replace('"', '""')+'"' for word in words)
    lexical = reader._connection.execute('''SELECT rowid, bm25(terms) AS score
        FROM terms WHERE terms MATCH ? ORDER BY score, rowid LIMIT 500''',
        (expression,)).fetchall() if expression else []
    valid_ids = {reader._ids[i] for i in indices}
    ranks = {row['rowid']: rank + 1 for rank, row in enumerate(lexical) if row['rowid'] in valid_ids}
    exact = query.strip().casefold() if re.fullmatch(r'[a-zA-Z0-9_./:+-]+', query.strip()) and re.search(r'[a-zA-Z]', query) else ''
    candidates = []
    for i in indices:
        ident, score = reader._ids[i], float(scores[i])
        lexical_rank = ranks.get(ident)
        if score < reader.profile.cutoff:
            if not exact or not lexical_rank:
                continue
            fragment = reader._connection.execute('SELECT text,context FROM fragments WHERE id=?', (ident,)).fetchone()
            if not re.search(r'(?<![\w])'+re.escape(exact)+r'(?![\w])',
                             (fragment['context']+'\n'+fragment['text']).casefold()):
                continue
        candidates.append((i, score, dense_ranks[ident], lexical_rank))
    output = {}
    for mode, bonus in (('legacy', None), ('cosine', 0), ('bonus003', .03), ('bonus005', .05), ('bonus008', .08)):
        ranked = []
        for i, score, dense_rank, lexical_rank in candidates:
            if bonus is None:
                rank = 1/(60+dense_rank) + (1/(60+lexical_rank) if lexical_rank else 0)
            else:
                rank = score + (bonus*60/(60+lexical_rank) if lexical_rank else 0)
            ranked.append((rank, i))
        ranked.sort(key=lambda value: (-value[0], reader._parent_keys[value[1]], reader._ids[value[1]]))
        output[mode] = list(dict.fromkeys(reader._parent_keys[i] for _, i in ranked))
    return output


def quality(keys, expected):
    result = metrics(keys, expected)
    result['hit1'] = int(bool(keys) and keys[0] in expected) if expected else None
    result['hit3'] = int(any(key in expected for key in keys[:3])) if expected else None
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', choices=('mps', 'cpu'), default='mps')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('A fresh private output directory is required.')
    output = private_directory(args.output)
    import numpy as np
    profile = Profile()
    encoder = SearchEncoder(settings, profile, device=args.device)
    encoder._load()

    class Memo:
        # Quality comparisons reuse query vectors, never reported as latency.
        def __init__(self):
            self.contract, self.tokenizer = encoder.contract, encoder.tokenizer
            self.batch_size, self.cache = encoder.batch_size, {}

        def encode(self, texts, query=False):
            if not query:
                return encoder.encode(texts, query=False)
            for text in texts:
                if text not in self.cache:
                    self.cache[text] = encoder.encode([text], query=True)[0]
            return np.stack([self.cache[text] for text in texts])

    memo = Memo()
    report = {'selected_policy': 'semantic-cosine-exact-v2', 'current_engine': RANKING_VERSION,
              'selection_frozen_before_holdout': True,
              'selected_bonus': 0, 'cutoff': profile.cutoff, 'device': args.device,
              'runtime': encoder.contract, 'python': platform.python_version(),
              'query_cache_for_quality_only': True,
              'fixture_sha256': {name: hashlib.sha256((ROOT/'tests'/name).read_bytes()).hexdigest()
                                 for name in ('natural_search_precision.py', 'natural_search_benchmark.py', 'natural_search_holdout.py')},
              'sets': {}}
    with tempfile.TemporaryDirectory(prefix='localbrain-ranking-') as scratch:
        sets = [('development', precision_seed), ('previous_selection', selection_seed),
                ('previous_observed_holdout', previous_holdout_seed),
                ('new_frozen_holdout', lambda root: precision_seed(root, held_out=True))]
        for name, seed in sets:
            config, queries, relevance = seed(Path(scratch)/name)
            built = prepare(config, memo, profile)
            reader = Retriever(config, profile, memo)
            modes = ('legacy', 'cosine', 'bonus003', 'bonus005', 'bonus008') if name in {'development', 'previous_selection'} else ('legacy', 'cosine')
            details = {mode: [] for mode in modes}
            try:
                for query in queries:
                    # Keep this historical v2 comparison reproducible after v3
                    # adds a second view in hybrid mode. Exact identifiers have
                    # no removable framing and retain hybrid lexical admission.
                    exact = bool(re.fullmatch(r'[a-zA-Z0-9_./:+-]+', query['query'].strip())
                                 and re.search(r'[a-zA-Z]', query['query']))
                    response = reader.search(query['query'], mode='hybrid' if exact else 'dense', page_size=100)
                    variants = ranking_keys(reader, query['query'], response, memo)
                    current = [item['key'] for item in response['results']]
                    if current != variants['cosine']:
                        raise ValueError('CURRENT_AND_COMPARATOR_ORDER_DIFFER')
                    for mode in modes:
                        keys = variants[mode]
                        details[mode].append({'id': query['id'], 'query': query['query'],
                                              'expected': query['expected'], 'keys': keys,
                                              'metrics': quality(keys, query['expected'])})
            finally:
                reader.close()
            report['sets'][name] = {'parents': len(relevance), 'queries': len(queries),
                                   'answerable': sum(bool(q['expected']) for q in queries),
                                   'fragments': built['fragments'],
                                   'modes': {mode: {'metrics': aggregate([row['metrics'] for row in rows]),
                                                    'queries': rows} for mode, rows in details.items()}}
            (output/'quality.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
            print(json.dumps({'set': name, 'metrics': {mode: row['metrics'] for mode, row in report['sets'][name]['modes'].items()}}), flush=True)


if __name__ == '__main__':
    main()
