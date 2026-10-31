"""Loopback/origin, JSON admission and stream cleanup without model execution."""
import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from localbrain.context_search.engine import validate_request
from localbrain.context_search.service import Job
from localbrain.context_search.web import install_routes
from localbrain.app.edition import install_boundary


class WebTests(unittest.TestCase):
    def setUp(self):
        self.app=FastAPI();install_boundary(self.app,SimpleNamespace())
        self.service=Mock()
        def begin(value):
            validate_request(value);job=Job();job.completed=True
            job.events.put(dict(type='answer',text='Demo answer',evidence=[]));return job
        self.service.begin.side_effect=begin
        self.service.status.return_value={'models':[], 'sources':[], 'runtime_missing':[], 'busy':False}
        self.app.state.context_search=self.service
        install_routes(self.app,Mock())

    def request(self, body=b'', headers=None, host='127.0.0.1'):
        async def receive(): return {'type':'http.request','body':body,'more_body':False}
        return Request(dict(type='http',method='POST',scheme='http',path='/api/context-search/answer',query_string=b'',
                            server=(host,80),headers=[(k.lower().encode(),v.encode()) for k,v in (headers or {'Content-Type':'application/json'}).items()],app=self.app),receive)

    async def answer(self, body, headers=None):
        endpoint=next(r.endpoint for r in self.app.routes if r.path=='/api/context-search/answer')
        return await endpoint(self.request(body,headers))

    def test_stream_is_no_store_and_releases_request(self):
        async def run():
            response=await self.answer(json.dumps(dict(model='4b',messages=[dict(role='user',content='Demo')])).encode())
            self.assertIn('no-store',response.headers['cache-control'])
            chunks=[chunk async for chunk in response.body_iterator]
            result=json.loads(''.join(chunks))
            self.assertEqual(result['text'],'Demo answer')
            self.assertIn('<p>Demo answer</p>',result['html'])
        asyncio.run(run())
        self.service.release.assert_called_once()

    def test_answer_markup_uses_shared_renderer_without_active_html_or_image_fetches(self):
        job=Job();job.completed=True
        job.events.put(dict(type='answer',text='**Demo** <script>alert(1)</script> ![image](https://example.test/private.png)',evidence=[]))
        self.service.begin.side_effect=lambda value:job
        async def run():
            response=await self.answer(b'{"model":"4b","messages":[{"role":"user","content":"Demo"}]}')
            chunks=[chunk async for chunk in response.body_iterator]
            return json.loads(''.join(chunks))['html']
        html=asyncio.run(run())
        self.assertIn('<strong>Demo</strong>',html)
        self.assertNotIn('<script>',html)
        self.assertNotIn('<img',html)

    def test_system_root_and_unbounded_or_non_json_inputs_are_refused(self):
        for value in (dict(model='4b',messages=[dict(role='system',content='x')]), dict(model='4b',messages=[],root='/outside')):
            with self.subTest(value=value),self.assertRaises(HTTPException) as caught:
                asyncio.run(self.answer(json.dumps(value).encode()))
            self.assertEqual(caught.exception.status_code,422)
        with self.assertRaises(HTTPException) as caught:
            asyncio.run(self.answer(b'x',{'Content-Type':'text/plain'}))
        self.assertEqual(caught.exception.status_code,415)
        with self.assertRaises(HTTPException) as caught:
            asyncio.run(self.answer(b'x'*120001))
        self.assertEqual(caught.exception.status_code,413)

    def test_cross_origin_and_non_loopback_are_refused(self):
        dispatch=self.app.user_middleware[0].kwargs['dispatch']
        async def admitted(request):return JSONResponse({'ok':True})
        response=asyncio.run(dispatch(self.request(headers={'Origin':'https://example.test'}),admitted))
        self.assertEqual(response.status_code,403)
        response=asyncio.run(dispatch(self.request(host='example.test'),admitted))
        self.assertEqual(response.status_code,403)
        self.service.unload_idle.assert_not_called()


if __name__ == '__main__': unittest.main()
