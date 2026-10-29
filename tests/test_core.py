"""Offline correctness and persistence checks; no FFmpeg or network required."""
import copy
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from georush.catalog import Catalog, CatalogError
from georush.history import History
from georush.quiz import build_quiz, validate_quiz


COUNTRIES = [
    ("us", "United States", "Easy"), ("gb", "United Kingdom", "Easy"),
    ("fr", "France", "Easy"), ("jp", "Japan", "Easy"),
    ("br", "Brazil", "Easy"), ("ca", "Canada", "Easy"),
    ("de", "Germany", "Normal"), ("it", "Italy", "Normal"),
    ("kr", "South Korea", "Normal"), ("se", "Sweden", "Normal"),
    ("no", "Norway", "Normal"), ("pt", "Portugal", "Normal"),
    ("uz", "Uzbekistan", "Hard"), ("lk", "Sri Lanka", "Hard"),
    ("lt", "Lithuania", "Hard"), ("lv", "Latvia", "Hard"),
    ("ee", "Estonia", "Hard"), ("bt", "Bhutan", "Hard"),
]


def fixture_assets(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "flags").mkdir(exist_ok=True)
    rows = []
    for index, (code, name, difficulty) in enumerate(COUNTRIES):
        flag = root / "flags" / (code + ".png")
        # Synthetic flags are test fixtures only, never production quiz assets.
        image = Image.new("RGB", (96, 64), (index * 13 % 256, 100, 190))
        image.putpixel((index + 1, index + 1), (255, 210, 0))
        image.save(flag)
        rows.append({"code": code, "name": name, "difficulty": difficulty,
                     "flag": "flags/" + code + ".png",
                     "sha256": hashlib.sha256(flag.read_bytes()).hexdigest(),
                     "source": "synthetic unittest fixture, not a real country flag"})
    (root / "countries.json").write_text(json.dumps(rows), encoding="utf-8")
    return rows


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="GeoRush 한글 ")
        self.root = Path(self.temporary.name)
        self.assets = self.root / "에셋"
        self.rows = fixture_assets(self.assets)
        self.catalog = Catalog(self.assets)
        self.history = History(self.root / "제작 이력.sqlite3")

    def tearDown(self):
        self.temporary.cleanup()

    def quiz(self, **kwargs):
        return build_quiz(self.catalog, self.history, **kwargs)

    def test_correct_answer_and_distinct_countries_offline(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("Network forbidden")):
            quiz = self.quiz(seed=42)
            validate_quiz(quiz, self.catalog)
        questions = quiz["questions"]
        self.assertEqual(len(questions), 3)
        self.assertEqual(len({q["country_code"] for q in questions}), 3)
        for question in questions:
            self.assertEqual(len(question["options"]), 4)
            self.assertEqual(len(set(question["options"])), 4)
            self.assertEqual(question["options"].count(question["country_name"]), 1)
            self.assertEqual(question["options"][question["correct_index"]], question["country_name"])
            row = self.catalog.get(question["country_code"])
            self.assertEqual(row["name"], question["country_name"])
            self.assertTrue(Path(question["flag_path"]).is_file())

    def test_every_difficulty_selects_correct_pool(self):
        for difficulty in ("Easy", "Normal", "Hard", "Mixed"):
            with self.subTest(difficulty=difficulty):
                quiz = self.quiz(difficulty=difficulty, seed=17)
                validate_quiz(quiz, self.catalog)
                if difficulty != "Mixed":
                    self.assertTrue(all(q["difficulty"] == difficulty for q in quiz["questions"]))

    def test_seed_reproducible_before_reservation(self):
        first = self.quiz(seed=4)
        second = self.quiz(seed=4)
        self.assertEqual(first["signature"], second["signature"])
        self.assertEqual(first["questions"], second["questions"])

    def test_reserved_composition_cannot_be_repeated(self):
        first = self.quiz(seed=4)
        self.history.reserve_quiz(first["signature"], "Mixed", str(self.root / "영상 1"), first)
        second = self.quiz(seed=4)
        self.assertNotEqual(first["signature"], second["signature"])

    def test_correct_answer_position_is_not_fixed(self):
        positions = {question["correct_index"] for seed in range(24)
                     for question in self.quiz(seed=seed)["questions"]}
        self.assertEqual(positions, {0, 1, 2, 3})

    def test_wrong_answer_and_duplicate_option_are_rejected(self):
        quiz = self.quiz(seed=99)
        invalid = copy.deepcopy(quiz)
        invalid["questions"][0]["correct_index"] = (invalid["questions"][0]["correct_index"] + 1) % 4
        with self.assertRaises(ValueError):
            validate_quiz(invalid, self.catalog)
        invalid = copy.deepcopy(quiz)
        invalid["questions"][0]["options"][1] = invalid["questions"][0]["options"][0]
        with self.assertRaises(ValueError):
            validate_quiz(invalid, self.catalog)

    def test_country_name_and_flag_mapping_mismatch_is_rejected(self):
        quiz = self.quiz(seed=5)
        invalid = copy.deepcopy(quiz)
        question = invalid["questions"][0]
        other = next(row for row in self.rows if row["code"] != question["country_code"])
        question["flag_path"] = str(self.assets / other["flag"])
        with self.assertRaises(ValueError):
            validate_quiz(invalid, self.catalog)

    def test_missing_flag_rejected_and_not_selected(self):
        missing = self.rows[0]
        (self.assets / missing["flag"]).unlink()
        with self.assertRaises(CatalogError):
            self.catalog.validate_country(missing["code"])
        for seed in range(12):
            quiz = self.quiz(seed=seed)
            self.assertNotIn(missing["code"], {q["country_code"] for q in quiz["questions"]})

    def test_modified_flag_hash_rejected(self):
        row = self.rows[0]
        Image.new("RGB", (96, 64), (255, 0, 0)).save(self.assets / row["flag"])
        with self.assertRaises(CatalogError):
            self.catalog.validate_country(row["code"])

    def test_unknown_country_is_actionable_error(self):
        with self.assertRaises(CatalogError):
            self.catalog.get("zz")

    def test_failure_is_never_recorded_as_success(self):
        quiz = self.quiz(seed=14)
        run = self.history.reserve_quiz(quiz["signature"], "Mixed", str(self.root / "영상 실패"), quiz)
        self.history.finish(run, success=False, error="FFmpeg deliberately failed")
        rows = self.history.list_runs()
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]["status"], "success")
        self.assertIn("FFmpeg", rows[0]["error"])
        self.assertIn(quiz["signature"], self.history.used_signatures())

    def test_success_history_persists_after_reopening_unicode_path(self):
        quiz = self.quiz(seed=77)
        output = self.root / "OneDrive 바탕 화면" / "GeoRush_Output" / "영상 1"
        run = self.history.reserve_quiz(quiz["signature"], "Mixed", str(output), quiz)
        self.history.finish(run, success=True)
        reopened = History(self.root / "제작 이력.sqlite3")
        self.assertIn(quiz["signature"], reopened.used_signatures())
        row = reopened.list_runs()[0]
        self.assertEqual(row["status"], "success")
        self.assertEqual(Path(row["output_path"]), output)

    def test_signature_reservation_is_unique(self):
        quiz = self.quiz(seed=2)
        self.history.reserve_quiz(quiz["signature"], "Mixed", str(self.root / "one"), quiz)
        with self.assertRaises((ValueError, sqlite3.IntegrityError)):
            self.history.reserve_quiz(quiz["signature"], "Mixed", str(self.root / "two"), quiz)
        self.assertEqual(len(self.history.list_runs()), 1)


if __name__ == "__main__":
    unittest.main()
