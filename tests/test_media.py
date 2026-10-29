"""Measure synthesized PCM and actual Pillow layouts, not Windows playback."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

import numpy as np
from PIL import ImageDraw

from georush.audio import synthesize_audio
from georush.render import WIDTH, HEIGHT, FPS, _background, _question_static


ASSETS = Path(__file__).resolve().parents[1] / "assets"


class LocalAudioTests(unittest.TestCase):
    def test_three_gains_duration_event_alignment_and_no_clipping(self):
        rms = {}
        with tempfile.TemporaryDirectory(prefix="GeoRush 오디오 ") as folder:
            for gain in (.08, .10, .12):
                path = Path(folder) / f"original_{gain}.wav"
                report = synthesize_audio(path, 3, gain)
                with wave.open(str(path), "rb") as wav:
                    self.assertEqual(wav.getnchannels(), 2)
                    self.assertEqual(wav.getframerate(), 48000)
                    self.assertEqual(wav.getsampwidth(), 2)
                    self.assertEqual(wav.getnframes(), 21 * 48000)
                    samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").reshape(-1, 2)
                self.assertEqual(report["clipped_samples"], 0)
                self.assertLess(np.abs(samples.astype(np.int32)).max(), 32767)
                self.assertLessEqual(report["peak_pcm"], .921)
                self.assertEqual(report["bgm_gain"], gain)
                events = report["events"]
                self.assertEqual(sum(e["kind"] == "countdown_tick" for e in events), 15)
                self.assertEqual(sum(e["kind"] == "transition" for e in events), 2)
                for start in (5.0, 11.5, 18.0):
                    self.assertTrue(any(e["kind"] == "correct_answer" and e["time_seconds"] == start
                                        for e in events))
                # No effects occur from .40 to .60s: measure the actual music gain.
                excerpt = samples[19200:28800].astype(np.float64)
                rms[gain] = float(np.sqrt(np.mean(excerpt ** 2)))
            self.assertAlmostEqual(rms[.12] / rms[.08], 1.5, delta=.002)

    def test_unsupported_audio_settings_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            for count, gain in ((0, .10), (6, .10), (3, .50)):
                with self.subTest(count=count, gain=gain):
                    with self.assertRaises(ValueError):
                        synthesize_audio(Path(folder) / "invalid.wav", count, gain)


class PillowLayoutTests(unittest.TestCase):
    def test_longest_country_names_are_measured_without_truncation(self):
        countries = json.loads((ASSETS / "countries.json").read_text(encoding="utf-8"))
        longest = sorted(countries, key=lambda row: len(row["name"]), reverse=True)[:4]
        names = [row["name"] for row in longest]
        question = {"country_name": names[0], "options": names, "correct_index": 0,
                    "flag_path": str(ASSETS / longest[0]["flag"])}
        seen = []
        original = ImageDraw.ImageDraw.text

        def measured(draw, xy, text, *args, **kwargs):
            bbox = draw.textbbox(xy, text, font=kwargs.get("font"))
            seen.append((str(text), bbox))
            return original(draw, xy, text, *args, **kwargs)

        with patch.object(ImageDraw.ImageDraw, "text", measured):
            background = _background()
            first = _question_static(question, 0, 3, background)
            answer = _question_static(question, 0, 3, background, reveal=True)
        self.assertEqual((WIDTH, HEIGHT, FPS), (1080, 1920, 30))
        self.assertEqual(first.size, (1080, 1920))
        self.assertNotEqual(first.tobytes(), answer.tobytes())
        for text, (left, top, right, bottom) in seen:
            with self.subTest(text=text):
                self.assertGreaterEqual(left, 45)
                self.assertLessEqual(right, WIDTH - 45)
                self.assertGreaterEqual(top, 45)
                self.assertLessEqual(bottom, HEIGHT - 45)
        self.assertTrue(any(text == "Which country is this?" for text, _ in seen))
        self.assertTrue(any(text == "CORRECT ANSWER" for text, _ in seen))
        self.assertFalse(any("..." in text or "…" in text for text, _ in seen))

    def test_missing_flag_stops_board_creation(self):
        question = {"country_name": "Canada", "options": ["Canada", "France", "Japan", "Brazil"],
                    "correct_index": 0, "flag_path": "/nonexistent/georush_missing_flag.png"}
        with self.assertRaises(FileNotFoundError):
            _question_static(question, 0, 3, _background())


if __name__ == "__main__":
    unittest.main()
