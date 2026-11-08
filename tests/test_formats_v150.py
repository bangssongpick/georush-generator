"""v1.5.0: episode numbers, answer confetti, Zoom theme, 10-question Shorts and the fast 100-flag Longform."""
from pathlib import Path
import tempfile
import unittest

import numpy as np

from georush import render
from georush.audio import COUNTDOWN_SECONDS, QUESTION_SECONDS
from georush.catalog import Catalog
from georush.history import History
from georush.longform.quiz import allocations, build
from georush.longform.timeline import build_timeline
from georush.longform.output import metadata
from georush.quiz import build_quiz, composition_signature, validate_quiz
from georush.textvariants import short_texts, with_episode


class EpisodeTests(unittest.TestCase):
    def test_episode_goes_before_the_brand(self):
        self.assertEqual(with_episode('Guess These 3 Flags! | GeoRush Geography Quiz #Shorts', 37),
                         'Guess These 3 Flags! #37 | GeoRush Geography Quiz #Shorts')
        self.assertEqual(with_episode('Zoom Quiz #Shorts', 5), 'Zoom Quiz #5 #Shorts')
        self.assertEqual(with_episode('No brand', 2), 'No brand #2')
        self.assertEqual(with_episode('Same', None), 'Same')

    def test_texts_carry_the_episode_and_stay_short(self):
        for theme in ('Classic', 'Africa', 'Lookalike', 'Capital', 'Zoom'):
            title = short_texts('sig', 3, 'Mixed', theme, 123)[0]
            self.assertIn('#123', title)
            self.assertLessEqual(len(title), 100)

    def test_history_counts_finished_shorts_only(self):
        with tempfile.TemporaryDirectory() as folder:
            history = History(Path(folder)/'h.sqlite3')
            self.assertEqual(history.next_shorts_episode(), 1)
            run = history.reserve_quiz('a', 'Mixed', Path(folder)/'x', {'questions': []})
            self.assertEqual(history.next_shorts_episode(), 1)
            history.finish(run, True)
            failed = history.reserve_quiz('b', 'Mixed', Path(folder)/'y', {'questions': []})
            history.finish(failed, False, 'boom')
            long_run = history.reserve_quiz('c', 'Mixed', Path(folder)/'z', {'mode': 'Longform', 'questions': []})
            history.finish(long_run, True)
            self.assertEqual(history.next_shorts_episode(), 2)


class ConfettiTests(unittest.TestCase):
    def test_burst_only_right_after_the_reveal_and_never_green(self):
        quiz = build_quiz(Catalog(), None, seed=4)
        context = render.prepare_animation(quiz['questions'])
        plain = np.asarray(render.animated_frame(context, COUNTDOWN_SECONDS+1.2), dtype=int)
        burst = np.asarray(render.animated_frame(context, COUNTDOWN_SECONDS+.3), dtype=int)
        self.assertGreater(int((np.abs(burst-plain).sum(axis=2) > 60).sum()), 200)
        self.assertFalse(any(c.upper() in ('#5DFFC2', '#0F584F') for c in render.CONFETTI_COLORS))
        self.assertLess(render.CONFETTI_SECONDS, QUESTION_SECONDS-COUNTDOWN_SECONDS)  # gone before the next flag


class ZoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def test_zoom_quiz(self):
        quiz = build_quiz(self.catalog, None, seed=9, theme='Zoom')
        self.assertEqual(quiz['theme'], 'Zoom')
        for question in quiz['questions']:
            self.assertEqual(question['kind'], 'zoom')
        validate_quiz(quiz, self.catalog)
        plain = [{k: v for k, v in q.items() if k not in ('kind', 'zoom_center')} for q in quiz['questions']]
        self.assertNotEqual(quiz['signature'], composition_signature(plain))

    def test_bad_zoom_center_is_rejected(self):
        quiz = build_quiz(self.catalog, None, seed=9, theme='Zoom')
        quiz['questions'][0]['zoom_center'] = [0.0, 0.5]
        with self.assertRaises(ValueError):
            validate_quiz(quiz, self.catalog)

    def test_zoom_widens_to_the_full_flag(self):
        quiz = build_quiz(self.catalog, None, seed=9, theme='Zoom')
        context = render.prepare_animation(quiz['questions'])
        first = np.asarray(render.animated_frame(context, 0.0), dtype=int)[302:1020, 44:1036]
        late = np.asarray(render.animated_frame(context, COUNTDOWN_SECONDS-.05), dtype=int)[302:1020, 44:1036]
        board = np.asarray(context['boards'][0][0], dtype=int)[302:1020, 44:1036]
        self.assertGreater(float(np.abs(first-board).mean()), 5)    # starts zoomed in
        self.assertLess(float(np.abs(late-board).mean()), float(np.abs(first-board).mean()))
        self.assertEqual(render._headline(0, 3, quiz['questions'][0]), 'ZOOMED IN! WHICH FLAG?')


class SpeedRoundTests(unittest.TestCase):
    def test_ten_question_short(self):
        quiz = build_quiz(Catalog(), None, 'Mixed', 10, 3)
        self.assertEqual(len(quiz['questions']), 10)
        self.assertEqual(quiz['questions'][-1]['difficulty'], 'Hard')
        context = render.prepare_animation(quiz['questions'])
        render.animated_frame(context, 9*QUESTION_SECONDS+1)
        with self.assertRaises(ValueError):
            build_quiz(Catalog(), None, 'Mixed', 11, 3)


class FastLongformTests(unittest.TestCase):
    def test_hundred_flags_on_a_five_second_clock(self):
        self.assertEqual(allocations(100), [25, 25, 25, 25])
        quiz = build(Catalog(), count=100, seed=2)
        timeline = build_timeline(quiz)
        self.assertEqual(timeline['duration'], 624)
        self.assertEqual(timeline['countdown'], 5)
        text = metadata(quiz, timeline)
        self.assertIn('5-second', text.replace('5 seconds', '5-second'))
        self.assertNotIn('8-second', text)

    def test_old_lengths_keep_the_eight_second_clock(self):
        quiz = build(Catalog(), count=20, seed=2)
        timeline = build_timeline(quiz)
        self.assertEqual(timeline['countdown'], 8)
        self.assertNotIn('5-second', metadata(quiz, timeline))


if __name__ == '__main__':
    unittest.main()
