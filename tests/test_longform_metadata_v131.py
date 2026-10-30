"""Copy the complete YouTube description once; keep all other fields intact."""
import copy
import re
import unittest

from georush.catalog import Catalog
from georush.longform.output import metadata
from georush.longform.quiz import build
from georush.longform.timeline import build_timeline
from georush.textvariants import LONG_COMMENTS, LONG_DISCLAIMER, LONG_FOLLOWS, LONG_INTROS


class LongformMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def check_metadata(self, count, expected_chapters):
        quiz = build(self.catalog, count=count, seed=131)
        text = metadata(quiz, build_timeline(quiz))
        headers = re.findall(r'^\[([^\]]+)\]$', text, re.MULTILINE)
        self.assertEqual(headers, ['제목', '설명', '고정 댓글', '태그', '카테고리'])
        self.assertNotIn('[챕터]', text)
        description = text.split('[설명]\n', 1)[1].split('\n\n[고정 댓글]', 1)[0]
        # v1.3.5: the wording varies per quiz; the structure (intro first, subscribe text before CHAPTERS, hashtags last) does not.
        self.assertTrue(any(description.startswith(intro.format(count=count)) for intro in LONG_INTROS))
        subscribes = [line for line in LONG_FOLLOWS if line in description]
        self.assertEqual(len(subscribes), 1)
        subscribe = subscribes[0]
        self.assertIn(LONG_DISCLAIMER, description)
        self.assertEqual(description.count('CHAPTERS\n'), 1)
        actual_chapters = description.split('CHAPTERS\n', 1)[1].split('\n\n', 1)[0]
        self.assertEqual(actual_chapters, expected_chapters)
        hashtags = '#GeoRush #FlagQuiz #GeographyQuiz #GuessTheFlag'
        self.assertTrue(description.endswith(hashtags))
        self.assertLess(description.index(subscribe), description.index('CHAPTERS\n'))
        self.assertLess(description.index('CHAPTERS\n'), description.index(hashtags))
        self.assertIn(f'[제목]\nGuess {count} Flags! 🌍 Easy to Expert Geography Quiz\n', text)
        self.assertTrue(any(f'[고정 댓글]\n{comment.format(count=count)}\n' in text for comment in LONG_COMMENTS))
        tags = re.search(r'\[태그\]\n(.*)\n', text).group(1)
        self.assertTrue(tags.startswith('GeoRush, guess the flag, flag quiz, geography quiz, '))
        self.assertEqual(len(tags.split(', ')), 8)
        self.assertEqual(len(set(tags.split(', '))), 8)
        self.assertTrue(text.endswith('[카테고리]\n교육 / 아동용 아님\n'))
        for question in quiz['questions']:
            self.assertNotIn(question['country_name'], text)

    def test_20_question_description_contains_complete_chapters(self):
        self.check_metadata(20, "00:00 Welcome\n00:05 Easy\n00:55 Normal\n01:48 Hard\n02:41 Expert\n03:34 What's your score?")

    def test_30_question_description_contains_complete_chapters(self):
        self.check_metadata(30, "00:00 Welcome\n00:05 Easy\n01:25 Normal\n02:48 Hard\n04:01 Expert\n05:14 What's your score?")

    def test_40_question_description_contains_complete_chapters(self):
        self.check_metadata(40, "00:00 Welcome\n00:05 Easy\n01:45 Normal\n03:28 Hard\n05:11 Expert\n06:54 What's your score?")

    def test_chapters_follow_supplied_timeline_instead_of_fixed_count_table(self):
        quiz = build(self.catalog, count=20, seed=131)
        timeline = copy.deepcopy(build_timeline(quiz))
        # A valid alternate intro duration shifts every subsequent actual segment.
        timeline['segments'][0]['duration'] += 7
        for segment in timeline['segments'][1:]:
            segment['start'] += 7
            if 'chapter_start' in segment:
                segment['chapter_start'] += 7
        timeline['duration'] += 7
        timeline['frames'] += 7 * timeline['fps']
        text = metadata(quiz, timeline)
        description = text.split('[설명]\n', 1)[1].split('\n\n[고정 댓글]', 1)[0]
        self.assertIn("CHAPTERS\n00:00 Welcome\n00:12 Easy\n01:02 Normal\n01:55 Hard\n02:48 Expert\n03:41 What's your score?\n\n", description)
        self.assertNotIn('00:05 Easy', description)
