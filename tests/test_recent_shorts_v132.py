"""v1.3.2: Shorts avoid countries of the latest 7 Shorts only; Longform runs never count."""
from pathlib import Path
import tempfile
import unittest

from georush.catalog import Catalog
from georush.history import History
from georush.quiz import RECENT_SHORTS, build_quiz, composition_signature
from tests.test_core import COUNTRIES, fixture_assets


def codes_of(quiz):
    return {question['country_code'] for question in quiz['questions']}


class RecentShortsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="GeoRush 최근 ")
        root = Path(self.temporary.name)
        fixture_assets(root / "에셋")
        self.catalog = Catalog(root / "에셋")
        self.history = History(root / "제작 이력.sqlite3")
        self.count = 0

    def tearDown(self):
        self.temporary.cleanup()

    def add_run(self, codes, longform=False, status=True):
        self.count += 1
        questions = [{'country_code': code} for code in codes]
        signature = composition_signature(questions)
        if longform:
            signature = 'longform:' + signature
        run_id = self.history.reserve_quiz(signature, 'Mixed', f'run{self.count}', {'questions': questions})
        self.history.finish(run_id, success=status)

    def test_default_window_is_one_week(self):
        self.assertEqual(RECENT_SHORTS, 21)  # v1.3.5: was 7; the small 18-flag fixture below still works through the shrinking window

    def test_longform_runs_do_not_mark_countries_recent(self):
        # A Longform listing every country used to disable the avoidance entirely.
        self.add_run(['us', 'gb', 'fr'])
        self.add_run([code for code, _, _ in COUNTRIES], longform=True)
        self.assertEqual(self.history.recent_shorts_country_codes(), [{'us', 'gb', 'fr'}])
        for seed in range(40):
            self.assertFalse(codes_of(build_quiz(self.catalog, self.history, seed=seed)) & {'us', 'gb', 'fr'})

    def test_only_latest_seven_shorts_are_avoided(self):
        self.add_run(['us', 'gb', 'ca'])  # 8th newest: no longer avoided
        newer = [['ca', 'br', 'de'], ['it', 'kr', 'se'], ['no', 'pt', 'uz'], ['lk', 'lt', 'lv'],
                 ['ee', 'bt', 'ca'], ['de', 'it', 'br'], ['kr', 'se', 'no']]
        for codes in newer:
            self.add_run(codes)
        self.assertEqual(len(self.history.recent_shorts_country_codes()), 7)
        seen = set()
        for seed in range(40):
            codes = codes_of(build_quiz(self.catalog, self.history, seed=seed))
            self.assertLessEqual(codes, {'us', 'gb', 'fr', 'jp'})
            seen |= codes
        self.assertTrue(seen & {'us', 'gb'})

    def test_window_shrinks_from_oldest_when_too_few_countries(self):
        # Easy has six fixture countries; the newest Short must still be avoided.
        self.add_run(['jp', 'br', 'de'])
        self.add_run(['us', 'gb', 'fr'])
        for seed in range(20):
            self.assertEqual(codes_of(build_quiz(self.catalog, self.history, 'Easy', seed=seed)), {'jp', 'br', 'ca'})

    def test_failed_shorts_are_not_avoided_and_empty_history_works(self):
        self.assertEqual(self.history.recent_shorts_country_codes(), [])
        build_quiz(self.catalog, self.history, seed=1)
        self.add_run(['us', 'gb', 'fr'], status=False)
        self.assertEqual(self.history.recent_shorts_country_codes(), [])

    def test_composition_duplicates_still_blocked(self):
        # Every Easy combination except one is used; the remaining one must be chosen.
        from itertools import combinations
        easy = [code for code, _, level in COUNTRIES if level == 'Easy']
        combos = list(combinations(easy, 3))
        for combo in combos[:-1]:
            self.add_run(list(combo), longform=False)
        quiz = build_quiz(self.catalog, self.history, 'Easy', seed=3)
        self.assertEqual(codes_of(quiz), set(combos[-1]))


if __name__ == '__main__':
    unittest.main()
