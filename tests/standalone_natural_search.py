"""Explicit installed-wheel smoke with real offline embeddings and synthetic data."""

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists():
        raise SystemExit('Fresh isolated output required')
    for key, leaf in [('LOCALBRAIN_DATA_DIR', 'data'), ('LOCALBRAIN_CACHE_DIR', 'cache'),
                      ('LOCALBRAIN_DEVELOPMENT_DIR', 'evidence'), ('LOCALBRAIN_CONTEXT_ROOT', 'context'),
                      ('LOCALBRAIN_CLAUDE_ROOT', 'claude'), ('LOCALBRAIN_CODEX_ROOT', 'codex')]:
        os.environ[key] = str(root / leaf)
    import localbrain
    from localbrain.config import settings
    from localbrain.db import init_db
    from localbrain.cli import main as command
    from localbrain.natural_search.service import SearchService
    from localbrain.runtime_storage import private_directory
    assert 'site-packages' in Path(localbrain.__file__).parts, 'Must use an installed distribution'
    private_directory(root)
    init_db()
    assert command(['models', 'install', 'embedding', '--offline']) == 0
    context = private_directory(root / 'context' / 'public-fixture')
    body = '휴대전화에서 지출 내역을 입력하고 월별 합계를 보여주는 가계부 앱을 만들었다.'
    document = context / 'mobile.md'
    document.write_text(body)
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute("INSERT INTO sources(id,kind,provider_kind,name,root_path) VALUES (101,'codex','codex','synthetic-fixture','/synthetic/sessions')")
        connection.execute("INSERT INTO sources(id,kind,provider_kind,name,root_path) VALUES (102,'context','context','synthetic-fixture',?)", (str(context),))
        connection.execute("INSERT INTO context_roots(id,path,label) VALUES (101,?,'synthetic-fixture')", (str(context),))
        for ident, text in [(101, body), (102, '토마토 화분에 물을 주고 햇빛이 드는 곳으로 옮겼다.')]:
            connection.execute("""INSERT INTO sessions
                (id,source_id,external_id,source_path,title,session_class,session_role,index_policy,last_event_at)
                VALUES (?,101,?,?,'Synthetic work','work','primary','full','2026-10-06T05:00:00Z')""",
                (ident, str(ident), '/synthetic/'+str(ident)))
            connection.execute("""INSERT INTO activity_events
                (id,session_id,sequence,event_type,role,text,source_line)
                VALUES (?,?,0,'message','user',?,1)""", ('wheel-'+str(ident), ident, text))
        connection.execute("""INSERT INTO context_documents
            (id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash)
            VALUES (101,102,101,?,'mobile.md','Synthetic app document',?,?,1791252000000000000,'synthetic')""",
            (str(document), body, len(body.encode())))
    service = SearchService(settings)
    try:
        service.request_prepare()
        deadline = time.monotonic()+180
        while time.monotonic() < deadline and service.status()['state'] not in {'ready', 'failed', 'model-missing'}:
            time.sleep(0.1)
        assert service.status()['state'] == 'ready', service.status()
        result = service.search('돈 쓴 내역을 휴대전화에 기록하는 앱 관련 자료')
        assert result['coverage']['eligible_parents'] == 3
        keys = {item['key'] for item in result['results']}
        assert {'session:101', 'document:101'} <= keys, keys
        assert 'session:102' not in keys, keys
        report = {'installed_wheel_real_model': 'PASS', 'device': service.engine()[0].device,
                  'eligible_parents': result['coverage']['eligible_parents'],
                  'matching_parents': len(keys), 'partial': result['partial'],
                  'contract': service.engine()[0].contract}
        (root / 'result.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({key: report[key] for key in ('installed_wheel_real_model', 'device', 'eligible_parents', 'matching_parents', 'partial')}))
    finally:
        service.stop()


if __name__ == '__main__':
    main()
