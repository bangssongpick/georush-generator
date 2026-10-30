"""v1.3.5: window title shows the real version; Longform description, tags and comment vary per quiz."""
from pathlib import Path
import re
import unittest

from georush import __version__
from georush.catalog import Catalog
from georush.longform.output import metadata
from georush.longform.quiz import build
from georush.longform.timeline import build_timeline
from georush.textvariants import long_texts, LONG_INTROS, LONG_BODIES, LONG_RULES, LONG_CALLS, LONG_FOLLOWS, LONG_COMMENTS

SOURCE = Path(__file__).resolve().parents[1] / 'georush'


class SmallPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def test_window_title_uses_the_package_version_and_text_is_current(self):
        gui = (SOURCE / 'gui.py').read_text(encoding='utf-8')
        self.assertIn('from . import __version__', gui)
        self.assertIn('self.title(f"GeoRush Generator v{__version__}")', gui)
        self.assertNotIn('GeoRush Generator v1.3"', gui)
        self.assertNotIn('다운로드가 필요합니다', gui)  # the EXE bundles Python and FFmpeg
        self.assertRegex(__version__, r'^\d+\.\d+\.\d+$')

    def texts(self, count, seed):
        quiz = build(self.catalog, count=count, seed=seed)
        return quiz, metadata(quiz, build_timeline(quiz))

    def test_longform_text_varies_but_keeps_format_chapters_and_hashtags(self):
        descriptions, tags, comments = set(), set(), set()
        for seed in range(60):
            quiz, text = self.texts(40, seed)
            description = text.split('[설명]\n', 1)[1].split('\n\n[고정 댓글]', 1)[0]
            descriptions.add(description.split('\n\nCHAPTERS\n')[0])
            tags.add(re.search(r'\[태그\]\n(.*)\n', text).group(1))
            comments.add(re.search(r'\[고정 댓글\]\n(.*)\n', text).group(1))
            self.assertEqual(re.findall(r'^\[([^\]]+)\]$', text, re.MULTILINE), ['제목', '설명', '고정 댓글', '태그', '카테고리'])
            self.assertTrue(description.endswith('#GeoRush #FlagQuiz #GeographyQuiz #GuessTheFlag'))
            self.assertIn('00:00 Welcome\n00:05 Easy\n01:45 Normal\n03:28 Hard\n05:11 Expert\n06:54 What\'s your score?', description)
            self.assertIn('(@GeoRushGames)', description)
            self.assertRegex(description, r'8[- ]seconds?')  # the real timing is always stated
            self.assertRegex(description, r'2-second (answer )?reveal')
            self.assertRegex(text.split('[고정 댓글]\n')[1], r'(?i)score')
            for question in quiz['questions']:
                self.assertNotIn(question['country_name'], text)
        self.assertGreaterEqual(len(descriptions), 40)
        self.assertGreaterEqual(len(tags), 40)
        self.assertEqual(len(comments), len(LONG_COMMENTS))

    def test_same_quiz_gets_the_same_text_and_variants_have_no_unfilled_placeholders(self):
        quiz, text = self.texts(20, 5)
        self.assertEqual(text, metadata(quiz, build_timeline(quiz)))
        self.assertEqual(long_texts(quiz['signature'], 20), long_texts(quiz['signature'], 20))
        for pool in (LONG_INTROS, LONG_BODIES, LONG_RULES, LONG_CALLS, LONG_FOLLOWS, LONG_COMMENTS):
            self.assertEqual(len(set(pool)), len(pool))
            for line in pool:
                self.assertIsNone(re.search(r'\{(?!count\})[a-z]+\}', line), line)


if __name__ == '__main__':
    unittest.main()
