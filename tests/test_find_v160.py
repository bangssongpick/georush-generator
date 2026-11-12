"""v1.6.0: Find theme (pick the named country's flag), audience-country flags, challenge titles, CTA."""
import unittest

from georush import render
from georush.audio import COUNTDOWN_SECONDS
from georush.catalog import Catalog
from georush.quiz import build_quiz, validate_quiz
from georush.textvariants import short_texts
from georush.themes import AUDIENCE_FIND, AUDIENCE_NORMAL, FIRST_FLAGS, THEMES


class FindTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def test_find_quiz_is_valid_and_opens_with_an_audience_country(self):
        self.assertIn('Find', THEMES)
        for seed in range(25):
            quiz = build_quiz(self.catalog, None, seed=seed, theme='Find')
            validate_quiz(quiz, self.catalog)
            questions = quiz['questions']
            self.assertIn(questions[0]['country_code'], AUDIENCE_FIND)
            answers = {q['country_name'] for q in questions}
            for q in questions:
                self.assertEqual(q['kind'], 'find')
                self.assertEqual(len(q['option_flag_paths']), 4)
                others = set(q['options'])-{q['country_name']}
                self.assertFalse(others & answers)  # no round gives another away

    def test_wrong_option_flag_is_rejected(self):
        quiz = build_quiz(self.catalog, None, seed=3, theme='Find')
        paths = quiz['questions'][0]['option_flag_paths']
        paths[0], paths[1] = paths[1], paths[0]
        with self.assertRaises(ValueError):
            validate_quiz(quiz, self.catalog)

    def test_lookalikes_come_first(self):
        quiz = build_quiz(self.catalog, None, seed=1, theme='Find')
        for seed in range(80):
            quiz = build_quiz(self.catalog, None, seed=seed, theme='Find')
            for q in quiz['questions']:
                if q['country_code'] == 'id':
                    self.assertIn('Poland', q['options'])
                    return

    def test_find_frames_render(self):
        quiz = build_quiz(self.catalog, None, seed=5, theme='Find')
        context = render.prepare_animation(quiz['questions'])
        render.animated_frame(context, 0.0)
        render.animated_frame(context, COUNTDOWN_SECONDS+.3)
        self.assertTrue(render._headline(0, 3, quiz['questions'][0]).startswith('FIND '))

    def test_find_texts(self):
        title, description, tags, comment = short_texts('sig', 3, 'Mixed', 'Find', 130)
        self.assertIn('#130', title)
        self.assertLessEqual(len(title), 100)
        self.assertIn('#FindTheFlag', description)


class AudienceAndTitleTests(unittest.TestCase):
    def test_indonesia_is_a_first_flag_and_audience_flags_appear_in_the_middle(self):
        self.assertIn('id', FIRST_FLAGS)
        catalog = Catalog()
        middles = [build_quiz(catalog, None, 'Mixed', 3, seed)['questions'][1]['country_code'] for seed in range(60)]
        self.assertGreater(sum(code in AUDIENCE_NORMAL for code in middles), 10)

    def test_mixed_titles_are_challenge_style(self):
        titles = {short_texts(f's{i}', 3, 'Mixed')[0] for i in range(40)}
        self.assertTrue(any('Only 1 of These 3 Flags Is Hard' in t for t in titles))
        self.assertTrue(all(len(t) <= 100 for t in titles))
        self.assertNotIn('Only 1 of', short_texts('s1', 3, 'Easy')[0])


if __name__ == '__main__':
    unittest.main()
