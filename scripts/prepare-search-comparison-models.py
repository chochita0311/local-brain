#!/usr/bin/env python3
"""Explicit public checkpoint download for optional development comparisons."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from localbrain.foundation.files import private_directory

MODELS = {
    'laya': ('convaiinnovations/laya-multilingual', 'e4e9ddf21a7b1903b7acffd8814ad4307bf63a67'),
    'reranker': ('Qwen/Qwen3-Reranker-0.6B', 'e61197ed45024b0ed8a2d74b80b4d909f1255473'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    root = private_directory(args.output)
    if (root / 'assets.json').exists():
        raise SystemExit('Use a fresh manifest directory')
    for name in ('HF_HUB_DISABLE_TELEMETRY', 'HF_HUB_DISABLE_IMPLICIT_TOKEN', 'HF_HUB_DISABLE_XET'):
        os.environ[name] = '1'
    try:
        import truststore
    except ImportError:
        pass
    else:
        truststore.inject_into_ssl()
    from huggingface_hub import snapshot_download
    models = {}
    for role, (repo, revision) in MODELS.items():
        snapshot = Path(snapshot_download(repo, revision=revision, token=False,
            local_files_only=args.offline,
            allow_patterns=['*.json', '*.safetensors', '*.txt', '*.model'], max_workers=2))
        hashes, size = {}, 0
        for path in sorted(snapshot.rglob('*')):
            if path.is_file():
                hasher = hashlib.sha256()
                with path.open('rb') as stream:
                    for block in iter(lambda: stream.read(1048576), b''):
                        hasher.update(block)
                hashes[path.relative_to(snapshot).as_posix()] = hasher.hexdigest()
                size += path.stat().st_size
        models[role] = {'repo': repo, 'revision': revision, 'path': str(snapshot),
                        'hashes': hashes, 'bytes': size}
        (root / 'assets.json').write_text(json.dumps(models, indent=2)+'\n')
        print(json.dumps({'role': role, 'revision': revision, 'bytes': size}), flush=True)


if __name__ == '__main__':
    main()
