"""Actual tool results, native protocol and request boundaries, using synthetic files."""
import json
import tempfile
import unittest
from pathlib import Path

from localbrain.context_search.engine import ChatError, answer, parse_calls, validate_request, compact_result


class Generator:
    def __init__(self, outputs):
        self.outputs, self.seen, self.last_output = iter(outputs), [], ''
    def generate_messages(self, messages, *, tools):
        self.seen.append(json.loads(json.dumps(messages)))
        self.last_output = next(self.outputs)
        return self.last_output


def call(name, **arguments):
    return '<tool_call>' + json.dumps(dict(name=name, arguments=arguments)) + '</tool_call>'


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        (self.root / 'guide.md').write_text('Airflow owner is Demo operator.\nSchedule: daily06.\n')
        self.sources = [dict(id='demo', name='Demo vault', kind='local', mode='files', root=str(self.root))]
        self.history = [{'role': 'user', 'content': 'Who runs Airflow?'}]
    def tearDown(self): self.tmp.cleanup()

    def test_model_selected_search_and_read_supply_actual_evidence(self):
        gen = Generator([call('search_text', query='Airflow'), call('read_file', source='demo', path='guide.md'), 'Demo operator runs Airflow daily06. [S1]'])
        events = []
        result = answer(gen, self.sources, self.history, events.append)
        self.assertIn('daily06', result['evidence'][0]['text'])
        self.assertEqual(result['evidence'][0]['path'], 'guide.md')
        self.assertTrue(any(e.get('tool') == 'read_file' for e in events))
        tool = next(m for m in gen.seen[-1] if m['role'] == 'tool')
        self.assertIn('Demo operator', tool['content'])
        self.assertEqual(gen.last_output, '')
        self.assertNotIn(str(self.root), gen.seen[0][0]['content'])

    def test_ungrounded_answer_is_replaced_with_insufficient_evidence(self):
        result = answer(Generator(['An invented contact. [S1]'] * 2), self.sources, self.history, lambda e: None)
        self.assertEqual(result['evidence'], [])
        self.assertNotIn('invented', result['text'])

    def test_unknown_citation_requires_a_corrected_answer(self):
        gen = Generator([call('search_text', query='Airflow'), 'Claim [S99]', 'Demo operator [S1]'])
        result = answer(gen, self.sources, self.history, lambda e: None)
        self.assertEqual(result['text'], 'Demo operator [S1]')
        self.assertEqual(len(gen.seen), 3)

    def test_write_request_returns_error_without_changing_file(self):
        gen = Generator([call('delete_file', path='guide.md'), 'No evidence', 'No evidence'])
        result = answer(gen, self.sources, self.history, lambda e: None)
        self.assertTrue((self.root / 'guide.md').exists())
        self.assertTrue(result['limited'])
        self.assertTrue(any('error' in m['content'] for m in gen.seen[-1] if m['role'] == 'tool'))

    def test_malformed_protocol_is_refused_and_loop_is_bounded(self):
        for text in ('<tool_call>{bad}</tool_call>', '<tool_call>{', '<tool_call>[]</tool_call>'):
            with self.subTest(text=text), self.assertRaises(ChatError): parse_calls(text)
        gen = Generator([call('list_sources')] * 8)
        with self.assertRaisesRegex(ChatError, '탐색 한도'):
            answer(gen, self.sources, self.history, lambda e: None)

    def test_client_never_admits_system_tool_paths_or_unbounded_history(self):
        valid = dict(model='4b', messages=self.history)
        self.assertEqual(validate_request(valid)[0], '4b')
        for patch in ({'root': '/outside'}, {'model': 'remote'}, {'messages': [{'role': 'system', 'content': 'x'}]},
                      {'messages': [{'role': 'user', 'content': 'x', 'tool_calls': []}]},
                      {'messages': [{'role': 'user', 'content': 'x' * 4001}]}):
            with self.subTest(patch=patch), self.assertRaises(ChatError): validate_request({**valid, **patch})

    def test_tool_serialized_results_are_bounded_and_marked(self):
        result = compact_result(dict(matches=[{'text': 'x' * 1600}] * 40))
        self.assertLessEqual(len(json.dumps(result)), 6000)
        self.assertTrue(result['limited'])


if __name__ == '__main__': unittest.main()
