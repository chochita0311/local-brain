"""Transient page and no-store JSON-line stream; same-origin boundary is global."""
import json
import queue
import sqlite3

import anyio
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from localbrain.rendering.markdown import render_markdown
from .engine import ChatError


def install_routes(app, templates):
    @app.get('/context-search')
    def context_search_page(request: Request):
        return templates.TemplateResponse(request, 'context-search.html', {'active_page': 'context-search'})

    @app.get('/api/context-search/status')
    def context_search_status(request: Request):
        try:
            return request.app.state.context_search.status()
        except (OSError, sqlite3.DatabaseError):
            raise HTTPException(503, '자료 목록을 읽지 못했습니다. 연결 상태를 확인해 주세요.') from None

    @app.post('/api/context-search/unload')
    def context_search_unload(request: Request):
        request.app.state.context_search.unload_idle()
        return {'ok': True}

    @app.post('/api/context-search/answer')
    async def context_search_answer(request: Request):
        if request.headers.get('content-type', '').split(';')[0] != 'application/json':
            raise HTTPException(415, '질문 요청 형식을 확인해 주세요.')
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 120000:
                raise HTTPException(413, '질문과 대화를 줄여 다시 시도해 주세요.')
        service = request.app.state.context_search
        try:
            value = json.loads(body)
            body.clear()
            job = await run_in_threadpool(service.begin, value)
            value.clear()
        except ChatError as error:
            raise HTTPException(error.status, str(error)) from None
        except (ValueError, TypeError):
            raise HTTPException(422, '모델과 질문을 확인해 주세요.') from None
        except (OSError, sqlite3.DatabaseError):
            raise HTTPException(503, '자료 목록을 읽지 못했습니다. 연결 상태를 확인해 주세요.') from None

        def next_event():
            try:
                return job.events.get(timeout=0.25)
            except queue.Empty:
                return None

        async def stream():
            try:
                while not job.canceled.is_set():
                    value = await run_in_threadpool(next_event)
                    if value:
                        if value.get('type') == 'answer':
                            value['html'] = str(render_markdown(value['text']).html)
                        yield json.dumps(value, ensure_ascii=False) + '\n'
                        if value.get('type') in {'answer', 'error'}:
                            break
            finally:
                # A closed tab cancels the response scope; cleanup must still run.
                with anyio.CancelScope(shield=True):
                    await run_in_threadpool(service.release, job)

        return StreamingResponse(stream(), media_type='application/x-ndjson',
                                 headers={'Cache-Control': 'no-store, private', 'X-Accel-Buffering': 'no'})
