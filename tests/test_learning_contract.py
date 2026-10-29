"""Synthetic-only persistence/replay witnesses for reviewed Learning data."""
import copy
import sqlite3
import unittest
from pathlib import Path

from localbrain.learning import (LearningError, assess_attempt, import_packet,
                                 set_visibility, submit_attempt)


def packet():
    return dict(version=1, lessons=[dict(
        key='demo-http', title='Demo HTTP lesson', topic='HTTP', why='Invented read-only report',
        explanation='A safe method requests read-only semantics.', reviewed_by='owner',
        version_status='unverified', applicability='Synthetic local example',
        sources=[dict(id='work', kind='work', title='Demo report', locator='synthetic report',
                      checked_on='2020-01-01', version='demo', snapshot='GET /report'),
                 dict(id='official', kind='official', title='HTTP semantics', locator='RFC9110',
                      checked_on='2020-01-01', version='unknown', snapshot='Safe semantics are read-only.',
                      url='https://example.test/official/http')],
        questions=[dict(id='q1', kind='recall', prompt='What does safe mean?', hint='Requested semantics',
                        answer='Read-only request semantics.', source_ids=['official'])])])


class LearningContractTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript((Path(__file__).parents[1]/'src/localbrain/schema.sql').read_text())
    def tearDown(self): self.db.close()
    def import_lesson(self):
        import_packet(self.db,packet(),'UTC')
        return self.db.execute('SELECT id FROM learning_lessons').fetchone()[0]
    def fields(self, token='demo-submission', **extra):
        return dict(action='answer',submission_key=token,question_id='q1',answer='Read-only semantics',confidence='high',hint_used='0',**extra)

    def test_revisions_append_and_reimport_does_not_revert_current_or_old_content(self):
        original=packet();self.assertEqual(import_packet(self.db,original,'UTC')['inserted'],1)
        first=self.db.execute('SELECT packet_json FROM learning_lessons').fetchone()[0]
        revised=copy.deepcopy(original);revised['lessons'][0]['explanation']='Revised, reviewed explanation.'
        self.assertEqual(import_packet(self.db,revised,'UTC')['inserted'],1)
        self.assertEqual(import_packet(self.db,original,'UTC')['unchanged'],1)
        rows=self.db.execute('SELECT * FROM learning_lessons ORDER BY id').fetchall()
        self.assertEqual(len(rows),2);self.assertEqual(rows[0]['packet_json'],first)
        self.assertGreater(rows[1]['id'],rows[0]['id'])

    def test_invalid_batch_does_not_partially_import(self):
        raw=packet();second=copy.deepcopy(raw['lessons'][0]);second['key']='demo-invalid'
        second['questions'][0]['source_ids']=['missing'];raw['lessons'].append(second)
        with self.assertRaises(LearningError):import_packet(self.db,raw,'UTC')
        self.assertEqual(self.db.execute('SELECT count(*) FROM learning_lessons').fetchone()[0],0)

    def test_submission_replay_and_one_way_self_assessment(self):
        lesson=self.import_lesson();fields=self.fields()
        attempt=submit_attempt(self.db,lesson,fields)
        self.assertEqual(submit_attempt(self.db,lesson,fields),attempt)
        with self.assertRaises(LearningError):submit_attempt(self.db,lesson,{**fields,'answer':'different'})
        assess_attempt(self.db,lesson,attempt,'recalled');assess_attempt(self.db,lesson,attempt,'recalled')
        with self.assertRaises(LearningError):assess_attempt(self.db,lesson,attempt,'again')
        self.assertEqual(self.db.execute('SELECT count(*) FROM learning_attempts').fetchone()[0],1)
        with self.assertRaises(sqlite3.IntegrityError):self.db.execute('DELETE FROM learning_lessons WHERE id=?',(lesson,))

    def test_reading_is_completed_without_answer_confidence_or_hint(self):
        lesson=self.import_lesson()
        attempt=submit_attempt(self.db,lesson,dict(action='read',submission_key='demo-read',question_id='q1'))
        row=self.db.execute('SELECT * FROM learning_attempts WHERE id=?',(attempt,)).fetchone()
        self.assertEqual((row['answer'],row['confidence'],row['hint_used'],row['outcome']),('',None,0,'read'))
        self.assertIsNotNone(row['assessed_at'])
        with self.assertRaises(LearningError):assess_attempt(self.db,lesson,attempt,'recalled')

    def test_visibility_is_reversible_and_shared_across_revisions(self):
        lesson=self.import_lesson();set_visibility(self.db,lesson,'hide','UTC')
        revised=packet();revised['lessons'][0]['title']='Revised demo'
        import_packet(self.db,revised,'UTC');newest=self.db.execute('SELECT max(id) FROM learning_lessons').fetchone()[0]
        self.assertEqual(self.db.execute('SELECT hidden FROM learning_visibility').fetchone()[0],1)
        set_visibility(self.db,newest,'restore','UTC')
        row=self.db.execute('SELECT * FROM learning_visibility').fetchone()
        self.assertEqual((row['hidden'],row['snoozed_until']),(0,None))
        self.assertEqual(self.db.execute('SELECT count(*) FROM learning_attempts').fetchone()[0],0)


if __name__=='__main__':unittest.main()
