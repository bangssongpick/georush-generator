"""v1.3.4: 3-second call-to-action, varied Shorts text, display names, contested flags left out of the quiz."""
from pathlib import Path
import re
import tempfile
import unittest

from PIL import Image, ImageDraw

from georush import pipeline, render
from georush.audio import COUNTDOWN_SECONDS, CTA_SECONDS, QUESTION_SECONDS
from georush.catalog import Catalog, EXCLUDED_FROM_QUIZ
from georush.longform import render as longform_render
from georush.longform.quiz import build as build_longform
from georush.names import DISPLAY_NAMES, display_name
from georush.quiz import build_quiz

HASHTAGS = '#GeoRush #GuessTheFlag #FlagQuiz #GeographyQuiz #Shorts'


class PolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    # --- call-to-action length ---------------------------------------------------------------------------
    def test_cta_is_three_seconds_and_timing_of_questions_is_unchanged(self):
        self.assertEqual((QUESTION_SECONDS, COUNTDOWN_SECONDS, CTA_SECONDS), (5.5, 4.0, 3.0))
        self.assertEqual(3 * QUESTION_SECONDS + CTA_SECONDS, 19.5)
        quiz = build_quiz(self.catalog, None, seed=1)
        context = render.prepare_animation(quiz['questions'])
        for second in (0.0, 5.5, 11.0, 16.49):  # all three questions, up to the last instant before the CTA
            self.assertFalse(render.animation_state(second, 3)['cta'], second)
        for second in (16.5, 18.0, 19.49):
            self.assertTrue(render.animation_state(second, 3)['cta'], second)
        # The card is fully drawn (progress line complete) and identical for the rest of the 3 seconds.
        self.assertEqual(render.animated_frame(context, 17.5).tobytes(), render.animated_frame(context, 19.4).tobytes())

    # --- display names --------------------------------------------------------------------------------------
    def test_display_names_are_reviewed_unique_and_only_for_known_names(self):
        canonical = {row['name'] for row in self.catalog.countries}
        self.assertTrue(set(DISPLAY_NAMES) <= canonical)
        shown = [display_name(name) for name in sorted(canonical)]
        self.assertEqual(len(set(shown)), len(canonical))  # no two countries look the same on screen
        for old, new in DISPLAY_NAMES.items():
            self.assertNotIn(new, canonical - {old}, new)
        self.assertEqual(display_name('Czech Republic'), 'Czechia')
        self.assertEqual(display_name('Türkiye'), 'Turkey')
        self.assertEqual(display_name('Germany'), 'Germany')

    def test_screens_show_display_names_while_data_keeps_verified_names(self):
        row = self.catalog.validate_country('tr')
        other = [self.catalog.validate_country(code)['name'] for code in ('us', 'cz', 'ci')]
        options = [row['name']] + other
        question = {'country_code': 'tr', 'country_name': row['name'], 'flag_path': row['flag_path'], 'flag': row['flag'],
                    'flag_sha256': row['sha256'], 'options': options, 'correct_index': 0, 'difficulty': row['difficulty'],
                    'longform_tier': 'Normal'}
        names, correct, _ = render._question_data(question)
        self.assertEqual(names, ['Turkey', 'United States', 'Czechia', 'Ivory Coast'])
        self.assertEqual(correct, 0)
        self.assertEqual(question['options'][0], 'Türkiye')  # untouched, so history and answer checks stay exact
        render._question_static(question, 0, 3, render._background(), reveal=True)  # draws without error
        longform_render.question_context(question, 0, 20)
        wrong = dict(question, country_name='Turkey')  # the answer check still compares the verified name
        with self.assertRaises(ValueError):
            render._question_data(wrong)

    # --- contested flags ------------------------------------------------------------------------------------
    def test_contested_flags_never_appear_as_question_or_option(self):
        banned_names = {self.catalog.get(code)['name'] for code in EXCLUDED_FROM_QUIZ}
        self.assertEqual(banned_names, {'Afghanistan', 'Syria'})
        valid, errors = self.catalog.valid_countries()
        self.assertEqual(errors, [])
        self.assertEqual(len(valid), 188)
        for seed in range(300):
            quiz = build_quiz(self.catalog, None, seed=seed)
            for question in quiz['questions']:
                self.assertNotIn(question['country_code'], EXCLUDED_FROM_QUIZ)
                self.assertFalse(banned_names & set(question['options']))
        for group in ('Easy', 'Normal', 'Hard'):
            for seed in range(40):
                for question in build_quiz(self.catalog, None, difficulty=group, seed=seed)['questions']:
                    self.assertNotIn(question['country_code'], EXCLUDED_FROM_QUIZ)
        for count in (20, 30, 40):
            for seed in range(15):
                for question in build_longform(self.catalog, count=count, seed=seed)['questions']:
                    self.assertNotIn(question['country_code'], EXCLUDED_FROM_QUIZ)
                    self.assertFalse(banned_names & set(question['options']))

    def test_flag_files_and_data_for_contested_countries_are_kept(self):
        for code in EXCLUDED_FROM_QUIZ:
            row = self.catalog.validate_country(code)  # still verifiable: provenance and old history stay intact
            self.assertTrue(Path(row['flag_path']).is_file())

    # --- varied Shorts text ---------------------------------------------------------------------------------
    def metadata_for(self, seed, questions=3):
        quiz = build_quiz(self.catalog, None, questions_per_video=questions, seed=seed)
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            pipeline._metadata(folder, quiz)
            return quiz, {name: (folder / name).read_text(encoding='utf-8') for name in
                          ('title.txt', 'description.txt', 'tags.txt', 'pinned_comment.txt')}

    def test_text_varies_but_keeps_branding_score_ask_and_never_names_countries(self):
        descriptions, tags, comments = set(), set(), set()
        for seed in range(80):
            quiz, text = self.metadata_for(seed)
            descriptions.add(text['description.txt'])
            tags.add(text['tags.txt'])
            comments.add(text['pinned_comment.txt'])
            self.assertTrue(text['description.txt'].endswith(HASHTAGS + '\n'))
            self.assertIn('(@GeoRushGames)', text['description.txt'])
            self.assertTrue(text['tags.txt'].startswith('GeoRush, GeoRushGames, guess the flag, flag quiz, geography quiz, '))
            self.assertTrue(text['tags.txt'].endswith(', Shorts\n'))
            self.assertLessEqual(len(text['tags.txt']), 500)
            self.assertEqual(len(set(text['tags.txt'].strip().split(', '))), len(text['tags.txt'].strip().split(', ')))
            for score in ('0/3', '1/3', '2/3', '3/3'):
                self.assertIn(score, text['pinned_comment.txt'])
            self.assertRegex(text['pinned_comment.txt'], r'(?i)score')
            for question in quiz['questions']:
                for value in text.values():
                    self.assertNotIn(question['country_name'], value)
        self.assertGreaterEqual(len(descriptions), 40)
        self.assertGreaterEqual(len(tags), 40)
        self.assertEqual(len(comments), 8)

    def test_same_quiz_always_gets_the_same_text(self):
        self.assertEqual(self.metadata_for(7)[1], self.metadata_for(7)[1])

    def test_one_and_five_question_videos_still_work(self):
        for n in (1, 5):
            _, text = self.metadata_for(n, questions=n)
            self.assertIn(f'0/{n}', text['pinned_comment.txt'])
            self.assertIn(f'{n}/{n}', text['pinned_comment.txt'])
            self.assertIsNone(re.search(r'\{[a-z]+\}', ''.join(text.values())))  # no unfilled placeholder


if __name__ == '__main__':
    unittest.main()
