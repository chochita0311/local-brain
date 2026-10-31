#!/usr/bin/env python3
"""Offline authored general-work comparison. Outputs are private, never in Git."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))

from natural_search_benchmark import aggregate, metrics, seed as selection_seed
from natural_search_holdout import seed as prior_seed
from natural_search_precision import seed as precision_seed
from natural_search_general import seed as general_seed
from localbrain.foundation.config import settings
from localbrain.natural_search.index import prepare
from localbrain.natural_search.model import SearchEncoder
from localbrain.natural_search.molecules import Profile
from localbrain.natural_search.query import focus_query
from localbrain.natural_search.retrieval import Retriever
from localbrain.foundation.files import private_directory


def quality(keys, expected, relevance):
    result = metrics(keys, expected)
    result['hit1'] = int(bool(keys) and keys[0] in expected) if expected else None
    result['hit3'] = int(any(key in expected for key in keys[:3])) if expected else None
    def topic(key):
        return relevance[key]['topic'] if isinstance(relevance[key], dict) else relevance[key]
    topics = {topic(key) for key in expected}
    found = {topic(key) for key in keys[:10] if key in expected}
    result['topic_recall10'] = len(found)/len(topics) if topics else None
    return result


def variants(reader, query, response, memo, modes):
    import numpy as np
    conditions = response['conditions']
    if conditions['start'] or conditions['end'] or conditions['exclude']:
        raise ValueError('GENERAL_FIXTURE_CONDITION_UNSUPPORTED')
    current = [item['key'] for item in response['results']]
    focused = query.strip() if conditions['notices'] else focus_query(query)
    if focused == query.strip():
        return {mode: current for mode in modes}
    vectors = memo.encode([query, focused], query=True)
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    scores = reader._matrix @ vectors.T
    valid = [i for i, key in enumerate(reader._parent_keys)
             if not conditions['kind'] or reader._parents[key][1]['kind'] == conditions['kind']]
    admitted = [i for i in valid if float(max(scores[i])) >= reader.profile.cutoff]
    original = sorted((i for i in valid if scores[i, 0] >= reader.profile.cutoff),
                      key=lambda i: (-float(scores[i, 0]), reader._parent_keys[i], reader._ids[i]))
    result = {'original': list(dict.fromkeys(reader._parent_keys[i] for i in original))}
    for mode in modes:
        if mode == 'original':
            continue
        rank = (np.max(scores, axis=1) if mode == 'maximum' else
                scores[:, 0]*.5 + scores[:, 1]*.5 if mode == 'equal' else
                scores[:, 0]*.75 + scores[:, 1]*.25)
        ranked = sorted(admitted, key=lambda i: (-float(rank[i]), reader._parent_keys[i], reader._ids[i]))
        result[mode] = list(dict.fromkeys(reader._parent_keys[i] for i in ranked))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stage', choices=('development', 'holdout'), required=True)
    parser.add_argument('--selected', choices=('maximum', 'equal', 'original-heavy'))
    parser.add_argument('--device', choices=('mps', 'cpu'), default='mps')
    args = parser.parse_args()
    if args.output.exists() or (args.stage == 'holdout' and not args.selected):
        raise SystemExit('Use a fresh private output directory and a frozen selection for holdout.')
    output = private_directory(args.output)
    import numpy as np
    profile = Profile()
    encoder = SearchEncoder(settings, profile, device=args.device)
    encoder._load()

    class Memo:
        def __init__(self):
            self.contract, self.tokenizer = encoder.contract, encoder.tokenizer
            self.batch_size, self.cache = encoder.batch_size, {}

        def encode(self, texts, query=False):
            if not query:
                return encoder.encode(texts, query=False)
            missing = list(dict.fromkeys(text for text in texts if text not in self.cache))
            if missing:
                self.cache.update(zip(missing, encoder.encode(missing, query=True)))
            return np.stack([self.cache[text] for text in texts])

    memo = Memo()
    report = {'stage': args.stage, 'selected': args.selected, 'device': args.device,
              'runtime': encoder.contract, 'cutoff': profile.cutoff, 'quality_query_cache': True,
              'fixture_hashes': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (ROOT/'tests').glob('natural_search_*.py')},
              'query_rule_hash': hashlib.sha256((ROOT/'src/localbrain/natural_search/query.py').read_bytes()).hexdigest(),
              'sets': {}}
    sets = [('general_development', general_seed), ('previous_selection', selection_seed),
            ('previous_holdout', prior_seed), ('precision_development', precision_seed),
            ('precision_holdout', lambda root: precision_seed(root, held_out=True))]
    if args.stage == 'holdout':
        sets = [('new_holdout', lambda root: general_seed(root, held_out=True))]
    modes = ('original', args.selected) if args.selected else ('original', 'maximum', 'equal', 'original-heavy')
    with tempfile.TemporaryDirectory(prefix='localbrain-general-benchmark-') as scratch:
        for name, seed in sets:
            config, queries, relevance = seed(Path(scratch)/name)
            built = prepare(config, memo, profile)
            reader = Retriever(config, profile, memo)
            details = {mode: [] for mode in modes}
            try:
                for query in queries:
                    response = reader.search(query['query'], page_size=100)
                    keys_by_mode = variants(reader, query['query'], response, memo, modes)
                    if 'equal' in modes and [item['key'] for item in response['results']] != keys_by_mode['equal']:
                        raise ValueError('CURRENT_AND_COMPARATOR_ORDER_DIFFER')
                    for mode in modes:
                        keys = keys_by_mode[mode]
                        details[mode].append({**query, 'focus': focus_query(query['query']), 'keys': keys,
                                              'metrics': quality(keys, query['expected'], relevance)})
            finally:
                reader.close()
            report['sets'][name] = {'parents': len(relevance), 'queries': len(queries),
                                   'fragments': built['fragments'],
                                   'modes': {mode: {'metrics': aggregate([row['metrics'] for row in rows]),
                                                   'categories': {category: aggregate([row['metrics'] for row in rows if row.get('category') == category])
                                                                  for category in sorted({row['category'] for row in rows if 'category' in row})},
                                                   'queries': rows} for mode, rows in details.items()}}
            (output/'quality.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
            print(json.dumps({'set': name, 'metrics': {mode: row['metrics'] for mode, row in report['sets'][name]['modes'].items()}}), flush=True)


if __name__ == '__main__':
    main()
