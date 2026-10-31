"""Bounded worker lifecycle/protocol tests, without model weights or private inputs."""
import io
import json
import os
import queue
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from localbrain.context_search.engine import ChatError
from localbrain.context_search.service import ContextSearchService


class Process:
    def __init__(self, responses, hang=False):
        self.responses, self.hang, self.returncode = responses, hang, None
        self.stdin = self
        self.sent = []
    def poll(self): return self.returncode
    def write(self, value):
        self.sent.append(json.loads(value))
        if not self.hang: self.responses.put(dict(type='answer', text='Demo answer [S1]', evidence=[]))
    def flush(self): pass
    def close(self): pass
    def terminate(self): self.returncode = -15
    def wait(self, timeout=None): return self.returncode


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.config = SimpleNamespace(data_dir=self.root/'data', cache_dir=self.root/'cache')
        self.models = patch('localbrain.context_search.service.generation_models', return_value=[dict(key=k, available=True) for k in ('4b','8b')]); self.models.start()
        self.runtime = patch('localbrain.context_search.service.runtime_missing', return_value=[]); self.runtime.start()
        self.sources = patch('localbrain.context_search.service.source_catalog', return_value=[dict(id='demo', name='Demo',kind='local',mode='files',root=str(self.root/'vault'))]);self.sources.start()
        self.service = ContextSearchService(self.config)
        self.processes = []
    def tearDown(self):
        self.service.stop(); self.models.stop(); self.runtime.stop(); self.sources.stop(); self.tmp.cleanup()
    def fake_spawn(self, key, hang=False):
        self.service._terminate_worker()
        responses=queue.Queue(); process=Process(responses, hang)
        self.processes.append(process)
        self.service._process, self.service._responses, self.service._model = process,responses,key
        return process,responses
    def begin(self, key='4b'): return self.service.begin(dict(model=key,messages=[dict(role='user',content='Demo question')]))
    def finish(self, job):
        self.assertEqual(job.events.get(timeout=2)['type'],'answer')
        self.service.release(job)

    def test_same_model_reuses_weights_switch_and_shutdown_release_previous_worker(self):
        with patch.object(self.service, '_spawn', side_effect=self.fake_spawn):
            self.finish(self.begin()); self.finish(self.begin())
            self.assertEqual(len(self.processes),1)
            self.finish(self.begin('8b'))
            self.assertEqual(len(self.processes),2)
            self.assertEqual(self.processes[0].returncode,-15)
        self.service.stop()
        self.assertEqual(self.processes[-1].returncode,-15)
        self.assertIsNone(self.service._job)

    def test_busy_and_disconnect_cancel_without_replay_or_saved_dialogue(self):
        with patch.object(self.service,'_spawn',side_effect=lambda k:self.fake_spawn(k,True)):
            job=self.begin()
            with self.assertRaises(ChatError): self.begin()
            started=time.monotonic();self.service.release(job)
        self.assertLess(time.monotonic()-started,3)
        self.assertEqual(self.processes[0].returncode,-15)
        self.assertFalse(job.thread.is_alive())
        self.assertIsNone(self.service._job)
        self.assertEqual(list(self.root.iterdir()),[])

    def test_idle_unload_does_not_interrupt_another_active_question(self):
        with patch.object(self.service,'_spawn',side_effect=lambda k:self.fake_spawn(k,True)):
            job=self.begin()
            for _ in range(50):
                if self.processes: break
                time.sleep(.01)
            self.service.unload_idle()
            self.assertIsNone(self.processes[0].returncode)
            self.service.release(job)

    def test_missing_model_or_source_does_not_start_worker_or_download(self):
        with patch.object(self.service,'_spawn') as spawn:
            self.models.stop()
            with patch('localbrain.context_search.service.generation_models',return_value=[dict(key='4b',available=False)]), self.assertRaises(ChatError): self.begin()
            self.models.start(); self.sources.stop()
            with patch('localbrain.context_search.service.source_catalog',return_value=[]), self.assertRaises(ChatError): self.begin()
            self.sources.start()
        spawn.assert_not_called()

    def test_app_kernel_cache_is_separate_and_no_private_data_in_command(self):
        process=Mock(stdout=io.StringIO(''),stdin=io.StringIO());process.poll.return_value=0
        with patch('localbrain.context_search.service.subprocess.Popen',return_value=process) as spawn:
            self.service._spawn('8b')
        env=spawn.call_args.kwargs['env']
        self.assertEqual(env['TORCHINDUCTOR_CACHE_DIR'],str(self.config.cache_dir/'context-search/torch'))
        self.assertEqual(env['PYTORCH_KERNEL_CACHE_PATH'],str(self.config.cache_dir/'context-search/kernels'))
        self.assertEqual(env.get('HF_HUB_CACHE'),os.environ.get('HF_HUB_CACHE'))
        self.assertNotIn('Demo question',' '.join(spawn.call_args.args[0]))
        self.assertNotIn('messages',env)

    def test_child_terminates_on_owner_eof_while_loading(self):
        code = ("import os, time\nfrom localbrain.models import installation as model_installation\nmodel_installation.model_root = lambda k: __import__('pathlib').Path('/missing-demo-model')\nmodel_installation.install_model = lambda *a, **k: time.sleep(60)\nfrom localbrain.context_search.worker import main\nmain()\n")
        process=subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env={**os.environ,'LOCALBRAIN_CHAT_MODEL':'4b'})
        try:
            payload=dict(model='4b',messages=[dict(role='user',content='Demo')],sources=[])
            process.stdin.write((json.dumps(payload)+'\n').encode());process.stdin.flush()
            self.assertIn(b'loading',process.stdout.readline())
            process.stdin.close();process.wait(timeout=5)
            self.assertEqual(process.returncode,-15)
        finally:
            if process.poll() is None: process.kill();process.wait()
            process.stdout.close()


if __name__ == '__main__': unittest.main()
