"""v1.4.2: a flag as wide as the screen, famous flag first, hard flag last, 3 second timer."""
import unittest

from georush import render
from georush.audio import COUNTDOWN_SECONDS, COUNTDOWN_TICKS, CTA_SECONDS, QUESTION_SECONDS
from georush.catalog import Catalog
from georush.quiz import build_quiz
from georush.themes import FIRST_FLAGS


class FirstScreenV142Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def test_first_flags_are_easy_quiz_flags(self):
        rows = {row['code']: row for row in self.catalog.valid_countries()[0]}
        self.assertGreater(len(FIRST_FLAGS), 21)  # more than the no-repeat window of Shorts
        for code in FIRST_FLAGS:
            self.assertEqual(rows[code]['difficulty'], 'Easy', code)

    def test_mixed_order_is_famous_normal_hard(self):
        for seed in range(60):
            first, middle, last = build_quiz(self.catalog, None, 'Mixed', 3, seed)['questions']
            self.assertIn(first['country_code'], FIRST_FLAGS)
            self.assertEqual(middle['difficulty'], 'Normal')
            self.assertEqual(last['difficulty'], 'Hard')

    def test_other_lengths_keep_the_first_and_last_rule(self):
        for count in (1, 2, 4, 5):
            questions = build_quiz(self.catalog, None, 'Mixed', count, 3)['questions']
            self.assertEqual(len(questions), count)
            self.assertIn(questions[0]['country_code'], FIRST_FLAGS)
            if count > 1:
                self.assertEqual(questions[-1]['difficulty'], 'Hard')

    def test_single_difficulty_is_not_changed(self):
        for level in ('Easy', 'Normal', 'Hard'):
            questions = build_quiz(self.catalog, None, level, 3, 5)['questions']
            self.assertEqual({q['difficulty'] for q in questions}, {level})

    def test_every_theme_can_build_a_mixed_short(self):
        for theme in ('Africa', 'Asia', 'Europe', 'Americas', 'Oceania', 'Lookalike', 'Capital'):
            for seed in range(5):
                self.assertEqual(len(build_quiz(self.catalog, None, 'Mixed', 3, seed, theme)['questions']), 3)

    def test_timer_is_three_seconds_and_the_short_is_about_fifteen(self):
        self.assertEqual((COUNTDOWN_SECONDS, COUNTDOWN_TICKS), (3.0, 3))
        self.assertEqual(3*QUESTION_SECONDS+CTA_SECONDS, 16.5)
        self.assertEqual(render.animation_state(0.0, 3)['remaining'], 3)
        self.assertTrue(render.animation_state(2.0, 3)['urgent'])
        self.assertFalse(render.animation_state(1.99, 3)['urgent'])

    def test_flag_is_close_to_the_full_width(self):
        quiz = build_quiz(self.catalog, None, seed=1)
        context = render.prepare_animation(quiz['questions'])
        for flag in context['flags']:
            self.assertGreaterEqual(flag.width, 880)  # was 553 of the 1080 px screen


if __name__ == '__main__':
    unittest.main()
