"""Actual Pillow frames and PCM timing, additional to the unchanged v1.1 suite."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave
import numpy as np
from PIL import ImageDraw
from georush.catalog import Catalog
from georush.quiz import build_quiz
from georush.render import prepare_animation, animated_frame, animation_state
from georush.audio import synthesize_audio, QUESTION_SECONDS, COUNTDOWN_SECONDS


class PresentationV12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.quiz=build_quiz(Catalog(),None,seed=4242)
        cls.context=prepare_animation(cls.quiz['questions'])

    def test_first_frame_has_recognizable_flag_and_question(self):
        pixels=np.asarray(animated_frame(self.context,0),dtype=np.int16)
        flag=pixels[480:915,170:910]
        self.assertGreater(int(((flag.max(axis=2)-flag.min(axis=2))>35).sum()),10000)
        title=pixels[250:410,140:940]
        self.assertGreater(int(((title[:,:,0]>200)&(title[:,:,1]>170)).sum()),1000)
        self.assertEqual(animation_state(0,3)['flag_scale'],.84)

    def test_flag_intro_moves_then_settles_before_one_second(self):
        crops=[animated_frame(self.context,t).crop((150,465,930,925)).tobytes() for t in (0,.3,.7,1)]
        self.assertNotEqual(crops[0],crops[1]);self.assertNotEqual(crops[1],crops[2])
        self.assertEqual(crops[2],crops[3])

    def test_flag_bounds_remain_inside_white_card(self):
        for q in range(3):
            w,h=self.context['flags'][q].size
            for step in range(31):
                s=animation_state(q*6.5+step/30,3)['flag_scale']
                self.assertGreaterEqual((1080-w*s)/2,130)
                self.assertLessEqual((1080+w*s)/2,950)
                self.assertGreaterEqual(695-h*s/2,445)
                self.assertLessEqual(695+h*s/2,945)

    def test_question_and_choices_remain_legible_without_global_flash(self):
        seen=[];original=ImageDraw.ImageDraw.text
        def measured(draw,xy,text,*args,**kwargs):
            seen.append((str(text),draw.textbbox(xy,text,font=kwargs.get('font'))))
            return original(draw,xy,text,*args,**kwargs)
        with patch.object(ImageDraw.ImageDraw,'text',measured):
            for t in (0,.1,.3,.7,1,3.09,4.99,5,5.13,6.49):
                animated_frame(self.context,t)
        for text,(x0,y0,x1,y1) in seen:
            self.assertGreaterEqual(x0,45,text);self.assertLessEqual(x1,1035,text)
            self.assertGreaterEqual(y0,45,text);self.assertLessEqual(y1,1875,text)
        options=[animated_frame(self.context,t).crop((60,1245,1030,1605)).tobytes() for t in (0,.3,.7,1,3.09,4.99)]
        self.assertTrue(all(p==options[0] for p in options))
        before=np.asarray(animated_frame(self.context,0),dtype=float)
        after=np.asarray(animated_frame(self.context,.3),dtype=float)
        stable=np.ones((1920,1080),dtype=bool)
        stable[232:420,80:1000]=False
        stable[469:922,151:930]=False
        stable[1030:1233,155:925]=False
        self.assertEqual(float(np.abs(after-before)[stable].max()),0)

    def test_countdown_tick_pulse_progress_and_urgent_color_timing(self):
        for q in range(3):
            progress=[]
            for tick in range(5):
                base=q*6.5+tick
                self.assertEqual(animation_state(base,3)['remaining'],5-tick)
                self.assertGreater(animation_state(base+.09,3)['digit_scale'],1.12)
                self.assertAlmostEqual(animation_state(base+.30,3)['digit_scale'],1)
                progress.append(animation_state(base,3)['progress'])
            self.assertEqual(progress,sorted(progress,reverse=True))
            self.assertFalse(animation_state(q*6.5+2.99,3)['urgent'])
            self.assertTrue(animation_state(q*6.5+3,3)['urgent'])

    def test_answer_has_unchanged_hold_and_short_scale_reward(self):
        self.assertEqual((QUESTION_SECONDS,COUNTDOWN_SECONDS),(6.5,5.0))
        for q in range(3):
            base=q*6.5
            self.assertFalse(animation_state(base+4.99,3)['reveal'])
            self.assertTrue(animation_state(base+5,3)['reveal'])
            self.assertGreater(animation_state(base+5.14,3)['answer_scale'],1.039)
            self.assertAlmostEqual(animation_state(base+5.4,3)['answer_scale'],1)
            self.assertTrue(animation_state(base+6.49,3)['reveal'])

    def test_answer_card_stays_safe_in_every_position(self):
        scale=animation_state(5.14,3)['answer_scale']
        for i in range(4):
            x=76+(i%2)*480;y=1255+(i//2)*178
            self.assertGreaterEqual(x-(449*scale-449)/2,45)
            self.assertLessEqual(x+449+(449*scale-449)/2,1035)
            self.assertGreaterEqual(y-(147*scale-147)/2,1230)
            self.assertLessEqual(y+147+(147*scale-147)/2,1610)

    def test_next_question_resets_answer_effect(self):
        for q in (1,2):
            state=animation_state(q*6.5,3)
            self.assertFalse(state['reveal']);self.assertEqual(state['answer_scale'],1)
            self.assertEqual(state['remaining'],5)
            actual=animated_frame(self.context,q*6.5).crop((60,1245,1030,1605)).tobytes()
            expected=self.context['boards'][q][0].crop((60,1245,1030,1605)).tobytes()
            self.assertEqual(actual,expected)

    def test_pcm_cues_are_unique_synced_and_fade_without_clipping(self):
        with tempfile.TemporaryDirectory() as folder:
            for gain in (.08,.10,.12):
                path=Path(folder)/f'{gain}.wav';report=synthesize_audio(path,3,gain)
                with wave.open(str(path)) as w:
                    pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float64)/32767
                events=report['events'];keys=[(e['kind'],round(e['time_seconds'],6)) for e in events]
                self.assertEqual(len(keys),len(set(keys)))
                for q in range(3):
                    self.assertIn(('entrance',round(q*6.5+.12,6)),keys)
                    for tick in range(5):self.assertIn(('countdown_tick',q*6.5+tick),keys)
                    self.assertIn(('correct_answer',q*6.5+5),keys)
                self.assertEqual(report['clipped_samples'],0)
                self.assertLess(float(np.abs(np.diff(pcm,axis=0)).max()),.15)
                self.assertTrue(np.all(pcm[-1]==0));self.assertEqual(report['end_fade_seconds'],.45)

    def test_visual_frames_change_and_cta_fills_the_canvas(self):
        frames=[animated_frame(self.context,t) for t in (0,.3,.7,1,2.5,4.9666667,5.0333333,6.5,20.9666667)]
        self.assertEqual(len({im.tobytes() for im in frames}),len(frames))
        self.assertTrue(all(im.size==(1080,1920) for im in frames))
        self.assertGreater(float(np.asarray(frames[-1]).std()),20)
