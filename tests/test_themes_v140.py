"""v1.4.0 Shorts series themes: regions, look-alike flags and capital cities. Classic stays unchanged."""
import unittest
from unittest.mock import patch

from PIL import ImageDraw

from georush import render
from georush.catalog import Catalog
from georush.names import display_name
from georush.quiz import build_quiz, composition_signature, validate_quiz
from georush.textvariants import short_texts
from georush.themes import (CAPITAL_EXCLUDED, LOOKALIKE_GROUPS, REGIONS, THEMES, capital_of, continent_of,
                            lookalike_mates, theme_pool)


class ThemeDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()
        cls.valid, _ = cls.catalog.valid_countries()

    def test_lookalike_groups_use_quiz_countries_once(self):
        codes = [code for group in LOOKALIKE_GROUPS for code in group]
        self.assertEqual(len(codes), len(set(codes)))
        valid = {row['code'] for row in self.valid}
        self.assertFalse(set(codes) - valid)
        self.assertTrue(all(len(group) >= 2 for group in LOOKALIKE_GROUPS))

    def test_every_theme_has_enough_countries_for_a_five_question_short(self):
        for theme in THEMES:
            self.assertGreaterEqual(len(theme_pool(theme, self.valid)), 8, theme)

    def test_capitals_are_unique_and_disputed_ones_are_never_asked(self):
        capitals = [capital_of(row['code']) for row in theme_pool('Capital', self.valid)]
        self.assertEqual(len(capitals), len(set(capitals)))
        self.assertTrue(all(capitals))
        self.assertFalse({row['code'] for row in theme_pool('Capital', self.valid)} & set(CAPITAL_EXCLUDED))
        self.assertEqual(capital_of('ua'), 'Kyiv')
        self.assertEqual(capital_of('fr'), 'Paris')


class ThemeQuizTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def test_classic_is_unchanged(self):
        quiz = build_quiz(self.catalog, None, seed=11)
        self.assertNotIn('theme', quiz)
        self.assertEqual(quiz, build_quiz(self.catalog, None, seed=11, theme='Classic'))
        self.assertTrue(all('kind' not in question for question in quiz['questions']))

    def test_region_quizzes_stay_inside_the_region(self):
        names = {row['name']: row['code'] for row in self.catalog.countries}
        for theme, continents in REGIONS.items():
            for seed in range(6):
                quiz = build_quiz(self.catalog, None, seed=seed, theme=theme)
                self.assertEqual(quiz['theme'], theme)
                for question in quiz['questions']:
                    self.assertIn(continent_of(question['country_code']), continents)
                    for option in question['options']:  # wrong answers come from the same region too
                        self.assertIn(continent_of(names[option]), continents, (theme, option))

    def test_lookalike_questions_offer_the_look_alike(self):
        names = {row['name']: row['code'] for row in self.catalog.countries}
        for seed in range(12):
            quiz = build_quiz(self.catalog, None, seed=seed, theme='Lookalike')
            codes = [question['country_code'] for question in quiz['questions']]
            for question in quiz['questions']:
                offered = {names[option] for option in question['options']}
                self.assertTrue(offered & set(lookalike_mates(question['country_code'])))
                self.assertFalse(set(lookalike_mates(question['country_code'])) & set(codes))
            validate_quiz(quiz, self.catalog)

    def test_capital_questions(self):
        capitals = {capital_of(row['code']) for row in self.catalog.countries} - {''}
        for seed in range(12):
            quiz = build_quiz(self.catalog, None, seed=seed, theme='Capital')
            for question in quiz['questions']:
                self.assertEqual(question['kind'], 'capital')
                self.assertEqual(question['options'][question['correct_index']], capital_of(question['country_code']))
                self.assertEqual(question['answer_name'], capital_of(question['country_code']))
                self.assertTrue(set(question['options']) <= capitals)
                self.assertEqual(len(set(question['options'])), 4)
            validate_quiz(quiz, self.catalog)

    def test_capital_signature_differs_from_the_flag_quiz(self):
        quiz = build_quiz(self.catalog, None, seed=3, theme='Capital')
        as_flags = [{k: v for k, v in question.items() if k != 'kind'} for question in quiz['questions']]
        self.assertNotEqual(composition_signature(quiz['questions']), composition_signature(as_flags))

    def test_wrong_capital_is_rejected(self):
        quiz = build_quiz(self.catalog, None, seed=5, theme='Capital')
        question = quiz['questions'][0]
        question['answer_name'] = question['options'][(question['correct_index']+1) % 4]
        with self.assertRaises(ValueError):
            validate_quiz(quiz, self.catalog)

    def test_easy_first_order_is_kept_in_themes(self):
        order = {'Easy': 0, 'Normal': 1, 'Hard': 2}
        for theme in THEMES:
            quiz = build_quiz(self.catalog, None, seed=21, theme=theme)
            tiers = [order[question['difficulty']] for question in quiz['questions']]
            self.assertEqual(tiers, sorted(tiers), theme)

    def test_unknown_theme_is_refused(self):
        with self.assertRaises(ValueError):
            build_quiz(self.catalog, None, seed=1, theme='Moon')


class ThemeScreenAndTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def test_capital_screen_asks_for_the_capital_and_shows_capitals(self):
        quiz = build_quiz(self.catalog, None, seed=8, theme='Capital')
        question = quiz['questions'][0]
        options, correct, _ = render._question_data(question)
        self.assertEqual(options, question['options'])
        title, subtitle = render._headline(0, 3, question)
        self.assertEqual(title, 'NAME THE CAPITAL!')
        self.assertEqual(subtitle, f'Capital of {display_name(question["country_name"])}?')
        self.assertEqual(render._headline(2, 3, quiz['questions'][2])[0], 'FINAL CAPITAL!')
        context = render.prepare_animation(quiz['questions'])
        for second in (0.0, 2.0, 4.6, 11.0):
            render.animated_frame(context, second)

    def test_longest_capital_subtitle_stays_inside_the_repainted_band(self):
        longest = max((row for row in self.catalog.countries if capital_of(row['code'])),
                      key=lambda row: len(display_name(row['name'])))
        question = {'kind': 'capital', 'country_name': longest['name']}
        _, subtitle = render._headline(1, 3, question)
        seen = []
        original = ImageDraw.ImageDraw.text

        def measured(draw, xy, text, *args, **kwargs):
            seen.append((str(text), draw.textbbox(xy, text, font=kwargs.get('font'))))
            return original(draw, xy, text, *args, **kwargs)
        image = render._background()
        with patch.object(ImageDraw.ImageDraw, 'text', measured):
            render._center(ImageDraw.Draw(image), subtitle, 346, 40, render.WHITE, max_width=900)
        x0, _, x1, _ = seen[-1][1]
        self.assertGreaterEqual(x0, 80)
        self.assertLessEqual(x1, 1000)

    def test_classic_texts_are_unchanged_by_the_theme_parameter(self):
        self.assertEqual(short_texts('abc', 3, 'Mixed'), short_texts('abc', 3, 'Mixed', 'Classic'))

    def test_theme_texts(self):
        for theme in THEMES[1:]:
            title, description, tags, comment = short_texts('sig', 3, 'Mixed', theme)
            self.assertLessEqual(len(title), 100, title)
            self.assertIn('#Shorts', title)
            self.assertIn('@GeoRushGames', description)
            self.assertIn('GeoRush', tags)
            if theme in REGIONS:
                self.assertIn(theme, title+description)
        title, description, _, comment = short_texts('sig', 3, 'Mixed', 'Capital')
        self.assertIn('Capital', title)
        self.assertIn('#CapitalCities', description)
        self.assertNotIn('flag', comment.lower())


if __name__ == '__main__':
    unittest.main()
