"""v1.3.6: avoid_codes.txt next to the history database keeps listed flags out of new Shorts."""
from pathlib import Path
import tempfile
import unittest

from georush.catalog import Catalog
from georush.history import History
from georush.quiz import build_quiz


class AvoidTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='GeoRush 제외 ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.history = History(self.root/'history.sqlite3')
        self.catalog = Catalog()

    def test_missing_file_means_nothing_is_avoided(self):
        self.assertEqual(self.history.avoided_codes(), set())

    def test_file_is_parsed_loosely(self):
        (self.root/'avoid_codes.txt').write_text('﻿FR, de\nit  jp  x  123  usa\n', encoding='utf-8')
        self.assertEqual(self.history.avoided_codes(), {'fr', 'de', 'it', 'jp', 'x'} - {'x'})

    def test_listed_flags_never_appear(self):
        codes = sorted(row['code'] for row in self.catalog.valid_countries()[0])
        avoid = set(codes[:140])
        (self.root/'avoid_codes.txt').write_text(' '.join(sorted(avoid)), encoding='utf-8')
        for seed in range(40):
            quiz = build_quiz(self.catalog, self.history, 'Mixed', 3, seed)
            self.assertFalse({q['country_code'] for q in quiz['questions']} & avoid, seed)

    def test_too_long_a_list_is_only_a_preference(self):
        codes = [row['code'] for row in self.catalog.valid_countries()[0]]
        (self.root/'avoid_codes.txt').write_text(' '.join(codes), encoding='utf-8')
        quiz = build_quiz(self.catalog, self.history, 'Mixed', 3, 1)
        self.assertEqual(len(quiz['questions']), 3)


if __name__ == '__main__':
    unittest.main()
