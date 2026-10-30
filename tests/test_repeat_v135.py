"""v1.3.5: a week of Shorts never repeats a flag; a Longform leaves out the previous two Longforms' flags."""
from pathlib import Path
import tempfile
import unittest

from georush.catalog import Catalog
from georush.history import History
from georush.longform.quiz import build as build_longform, tier_for, TIERS
from georush.quiz import RECENT_SHORTS, build_quiz


class RepetitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="GeoRush 반복 ")
        self.history = History(Path(self.temporary.name) / "이력.sqlite3")
        self.count = 0

    def tearDown(self):
        self.temporary.cleanup()

    def register(self, quiz):
        self.count += 1
        run = self.history.reserve_quiz(quiz['signature'], quiz['difficulty'], f'run{self.count}', quiz)
        self.history.finish(run, True)
        return [question['country_code'] for question in quiz['questions']]

    def test_window_is_one_week_of_shorts(self):
        self.assertEqual(RECENT_SHORTS, 21)  # 3 Shorts a day x 7 days

    def test_any_21_consecutive_shorts_share_no_flag(self):
        videos = [self.register(build_quiz(self.catalog, self.history, seed=i)) for i in range(63)]  # three weeks
        for start in range(len(videos) - 20):
            flags = [code for video in videos[start:start + 21] for code in video]
            self.assertEqual(len(flags), len(set(flags)), f'repeat inside videos {start + 1}-{start + 21}')

    def test_two_consecutive_longforms_leave_out_the_previous_two(self):
        longs = []
        for i in range(6):
            quiz = build_longform(self.catalog, self.history, count=40, seed=100 + i)
            longs.append({q['country_code'] for q in quiz['questions']})
            self.register(quiz)
        for i in range(2, 6):
            self.assertFalse(longs[i] & longs[i - 1], f'longform {i + 1} repeats flags of the one before')
            self.assertFalse(longs[i] & longs[i - 2], f'longform {i + 1} repeats flags of the one two before')

    def test_longform_stays_valid_and_balanced(self):
        for i in range(3):
            quiz = build_longform(self.catalog, self.history, count=40, seed=7 + i)
            self.register(quiz)
            counts = {tier: sum(q['longform_tier'] == tier for q in quiz['questions']) for tier in TIERS}
            self.assertEqual(counts, {'Easy': 10, 'Normal': 10, 'Hard': 10, 'Expert': 10})

    def test_shorts_history_does_not_hide_longform_flags_and_the_reverse(self):
        for i in range(5):
            self.register(build_quiz(self.catalog, self.history, seed=i))
        self.assertEqual(self.history.recent_longform_country_codes(), [])
        longform = build_longform(self.catalog, self.history, count=40, seed=3)
        self.register(longform)
        self.assertEqual(len(self.history.recent_longform_country_codes()), 1)
        self.assertEqual(len(self.history.recent_shorts_country_codes(21)), 5)


if __name__ == '__main__':
    unittest.main()
