"""Longform contracts; actual Windows GUI/MP4 tests run separately in release CI."""
from collections import Counter
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from georush.catalog import Catalog
from georush.history import History
from georush.quiz import build_quiz
from georush.longform.quiz import build,validate,allocations,tier_for,TIERS,HARD,EXPERT
from georush.longform.timeline import build_timeline,chapters,timestamp
from georush.longform.output import metadata,thumbnail,publish,FINAL_FILES
from georush.longform.render import question_context,question_frame,text
from georush.longform import pipeline

class LongformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=Catalog()

    def check_count(self,count):
        quiz=build(self.catalog,count=count,seed=count);self.assertTrue(validate(quiz,self.catalog))
        self.assertEqual(len(quiz['questions']),count)
        self.assertEqual(len({q['country_code'] for q in quiz['questions']}),count)
        self.assertEqual([Counter(q['longform_tier'] for q in quiz['questions'])[t] for t in TIERS],allocations(count))
        self.assertLessEqual(max(Counter(q['correct_index'] for q in quiz['questions']).values())-min(Counter(q['correct_index'] for q in quiz['questions']).values()),1)
        for q in quiz['questions']:
            self.assertEqual(len(set(q['options'])),4);self.assertEqual(q['options'][q['correct_index']],q['country_name'])
        return quiz
    def test_20_questions(self):self.check_count(20)
    def test_30_questions(self):self.check_count(30)
    def test_40_questions(self):self.check_count(40)
    def test_editorial_groups_explicit_without_changing_catalog(self):
        rows=self.catalog.countries
        self.assertEqual(Counter(r['difficulty'] for r in rows),{'Easy':20,'Normal':20,'Hard':20})
        self.assertEqual(Counter(tier_for(r) for r in rows),{'Easy':20,'Normal':20,'Hard':10,'Expert':10})
        self.assertFalse(HARD&EXPERT);self.assertIn('not a measured',build(self.catalog,count=20)['difficulty_note'])
    def test_invalid_sizes_rejected(self):
        for count in (0,5,21,60,True):
            with self.assertRaises(ValueError):allocations(count)
    def test_missing_expert_asset_blocks_generation(self):
        valid,errors=self.catalog.valid_countries()
        with patch.object(self.catalog,'valid_countries',return_value=([r for r in valid if r['code']!='kz'],['missing kz'])):
            with self.assertRaisesRegex(ValueError,'Expert'):build(self.catalog,count=40)
    def test_duplicate_or_wrong_country_blocked(self):
        q=build(self.catalog,count=20,seed=1)
        bad=copy.deepcopy(q);bad['questions'][0]['country_name']='Fake Country'
        with self.assertRaises(ValueError):validate(bad,self.catalog)
        bad=copy.deepcopy(q);bad['questions'][1]=bad['questions'][0]
        with self.assertRaises(ValueError):validate(bad,self.catalog)
    def test_unbalanced_answers_blocked(self):
        q=build(self.catalog,count=20)
        for item in q['questions']:
            answer=item['options'].pop(item['correct_index']);item['options'].insert(0,answer);item['correct_index']=0
        with self.assertRaisesRegex(ValueError,'분포'):validate(q,self.catalog)
    def test_signature_duplicate_and_short_history_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            h=History(Path(td)/'history.db');short=build_quiz(self.catalog,seed=1)
            rid=h.reserve_quiz(short['signature'],'Mixed','shorts',short);h.finish(rid,True)
            before=h.list_runs()[0]
            q=build(self.catalog,h,20,13);rid=h.reserve_quiz(q['signature'],'Mixed','longform',q);h.finish(rid,True)
            another=build(self.catalog,h,20,13)
            self.assertNotEqual(q['signature'],another['signature']);self.assertIn(before,h.list_runs())
    def test_timeline_and_all_real_chapters(self):
        for count,duration in ((20,224),(30,324),(40,424)):
            q=build(self.catalog,count=count);t=build_timeline(q)
            self.assertEqual(t['duration'],duration);self.assertEqual(t['frames'],duration*30)
            for a,b in zip(t['segments'],t['segments'][1:]):self.assertEqual(a['start']+a['duration'],b['start'])
            self.assertEqual(len(chapters(t)),6)
            for start,label in chapters(t):self.assertTrue(any(s['start']==start for s in t['segments']))
    def test_metadata_count_no_answer_leak_and_real_chapters(self):
        q=build(self.catalog,count=30);t=build_timeline(q);m=metadata(q,t)
        for header in ('[제목]','[설명]','[고정 댓글]','[태그]','[카테고리]'):self.assertIn(header,m)
        self.assertNotIn('[챕터]',m)
        self.assertIn('30 Flags',m);self.assertNotIn('#Shorts',m)
        for question in q['questions']:self.assertNotIn(question['country_name'],m)
        for at,label in chapters(t):self.assertIn(timestamp(at)+' '+label,m)
    def test_thumbnail_actual_flags_and_size(self):
        q=build(self.catalog,count=40)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'t.jpg';r=thumbnail(q,p)
            with Image.open(p) as im:self.assertEqual(im.size,(1920,1080));self.assertEqual(im.format,'JPEG')
            self.assertTrue(set(r['country_codes'])<={q['country_code'] for q in q['questions']})
    def test_long_names_all_fit_and_first_frame_visible(self):
        q=build(self.catalog,count=40,seed=7)
        for row in self.catalog.valid_countries()[0]:
            question=copy.deepcopy(q['questions'][0]);question['options'][1]=row['name']
            context=question_context(question,0,40)
        context=question_context(q['questions'][0],0,40)
        import numpy as np
        first=np.array(question_frame(context,0));next_frame=np.array(question_frame(context,9))
        self.assertGreater(first[300:600,600:1320].std(),12)
        self.assertGreater(np.mean(np.abs(first.astype(float)-next_frame)),.1)
    def test_reveal_is_reset_next_question(self):
        q=build(self.catalog,count=20);a=question_context(q['questions'][0],0,20);b=question_context(q['questions'][1],1,20)
        self.assertNotEqual(question_frame(a,243).tobytes(),question_frame(a,0).tobytes())
        for box in __import__('georush.longform.render',fromlist=['OPTION_BOXES']).OPTION_BOXES:
            self.assertEqual(question_frame(b,0).crop(box).tobytes(),b['base'].crop(box).tobytes())
    def test_atomic_three_file_publish_and_no_diagnostics(self):
        with tempfile.TemporaryDirectory(prefix='GeoRush 한글 ') as td:
            work=Path(td)/'private';work.mkdir();final=Path(td)/'out'
            for name in FINAL_FILES:(work/name).write_bytes(b'fixture')
            (work/'error.log').write_text('private')
            publish(work,final);self.assertEqual({p.name for p in final.iterdir()},FINAL_FILES)
    def test_partial_publish_no_final(self):
        with tempfile.TemporaryDirectory() as td:
            work=Path(td)/'private';work.mkdir();final=Path(td)/'out'
            with self.assertRaises(OSError):publish(work,final)
            self.assertFalse(final.exists());self.assertEqual(list(Path(td).glob('.GeoRush*')),[])
    def test_pipeline_failure_private_not_success(self):
        with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{'GEORUSH_DATA_DIR':str(Path(td)/'internal')}):
            root=Path(td)/'user'
            with patch.object(pipeline,'render',side_effect=RuntimeError('deliberate FFmpeg failure')):
                r=pipeline.generate_batch(count=2,questions_per_video=20,output_root=root)
            self.assertEqual([x['status'] for x in r],['failed','failed']);self.assertEqual(list(root.iterdir()),[])
            self.assertTrue(all((Path(x['path'])/'ERROR.txt').exists() for x in r))
            self.assertTrue(all(x['status']=='failed' for x in History(Path(td)/'internal/georush_history.sqlite3').list_runs()))
    def test_streamed_audio_length_sync_peak_and_fade(self):
        import wave,numpy as np
        from georush.longform.audio import synthesize
        timeline={'duration':11,'segments':[{'kind':'question','start':0,'duration':10},{'kind':'outro','start':10,'duration':1}]}
        with tempfile.TemporaryDirectory() as td:
            for gain in (.08,.10,.12):
                path=Path(td)/'track.wav';report=synthesize(path,timeline,gain)
                with wave.open(str(path)) as wav:
                    self.assertEqual(wav.getnframes(),11*48000);samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2')
                self.assertEqual(report['clipped_samples'],0);self.assertEqual(report['max_chunk_seconds'],1)
                self.assertEqual([e['time'] for e in report['events'] if e['kind']=='tick'],list(range(8)))
                self.assertEqual([e['time'] for e in report['events'] if e['kind']=='answer'][0],8)
                self.assertLess(abs(int(samples[-1])),5)
