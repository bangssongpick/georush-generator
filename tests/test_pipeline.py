"""Failure isolation and output contracts with deliberately fake renderers.

These tests do not establish MP4 playback. Actual encoded sample validation is
performed separately by the production validation module.
"""
import json
import os
from PIL import Image
from georush.paths import history_path
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from georush.history import History
from georush import pipeline


class PipelineFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="GeoRush 배치 ")
        self.root = Path(self.temporary.name) / "OneDrive 바탕 화면" / "GeoRush_Output"
        self.data = Path(self.temporary.name)/"프로그램 데이터"
        env = patch.dict(os.environ, {"GEORUSH_DATA_DIR": str(self.data)})
        env.start(); self.addCleanup(env.stop)
        thumbnail = patch.object(pipeline, "extract_thumbnail", side_effect=lambda video, target, ffmpeg: Image.new("RGB", (1080,1920), "blue").save(target))
        thumbnail.start(); self.addCleanup(thumbnail.stop)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def fake_render(quiz, destination, *args, **kwargs):
        Path(destination).write_bytes(b"unit test fake video, not playable")
        return {"test_fixture": True}

    def patched_batch(self, **kwargs):
        with patch.object(pipeline, "find_ffmpeg", return_value="unused fake ffmpeg"), \
                patch.object(pipeline, "render_video", side_effect=self.fake_render), \
                patch.object(pipeline, "validate_video", return_value={"test_fixture": True}), \
                patch.object(pipeline, "extract_encoded_frames", return_value=[]):
            return pipeline.generate_batch(output_root=self.root, seed=41, **kwargs)

    def test_single_render_failure_does_not_abort_following_videos(self):
        calls = []

        def failing_first(quiz, destination, *args, **kwargs):
            calls.append(destination)
            if len(calls) == 1:
                raise RuntimeError("Deliberate FFmpeg process failure")
            return self.fake_render(quiz, destination)

        events = []
        with patch.object(pipeline, "find_ffmpeg", return_value="unused"), \
                patch.object(pipeline, "render_video", side_effect=failing_first), \
                patch.object(pipeline, "validate_video", return_value={"test_fixture": True}), \
                patch.object(pipeline, "extract_encoded_frames", return_value=[]):
            results = pipeline.generate_batch(count=3, output_root=self.root, seed=42,
                                              progress_callback=events.append)
        self.assertEqual([r["status"] for r in results], ["failed", "success", "success"])
        self.assertEqual(len(calls), 3)
        history = History(history_path()).list_runs()
        self.assertEqual(sum(r["status"] == "success" for r in history), 2)
        self.assertEqual(sum(r["status"] == "failed" for r in history), 1)
        self.assertTrue((Path(results[0]["path"]) / "ERROR.txt").is_file())
        self.assertTrue(any(e["stage"] == "failed" for e in events))
        self.assertTrue(any(e["stage"] == "success" for e in events))

    def test_validation_failure_never_commits_success(self):
        with patch.object(pipeline, "find_ffmpeg", return_value="unused"), \
                patch.object(pipeline, "render_video", side_effect=self.fake_render), \
                patch.object(pipeline, "validate_video", side_effect=ValueError("Invalid codec")):
            results = pipeline.generate_batch(output_root=self.root, seed=42)
        self.assertEqual(results[0]["status"], "failed")
        history = History(history_path()).list_runs()
        self.assertEqual(history[0]["status"], "failed")
        self.assertIn("Invalid codec", history[0]["error"])

    def test_metadata_unicode_folders_and_reexecution_do_not_collide(self):
        first = self.patched_batch(count=1)[0]
        second = self.patched_batch(count=1)[0]
        self.assertEqual(first["status"], "success")
        self.assertEqual(second["status"], "success")
        self.assertNotEqual(first["path"], second["path"])
        self.assertNotEqual(first["signature"], second["signature"])
        for result in (first, second):
            folder = Path(result["path"])
            self.assertEqual({p.name for p in folder.iterdir()}, {"shorts.mp4", "shorts_metadata.txt", "shorts_thumbnail.jpg"})
            quiz = json.loads((Path(result["debug_path"]) / "quiz_data.json").read_text(encoding="utf-8"))
            title = (folder / "shorts_metadata.txt").read_text(encoding="utf-8-sig")
            for question in quiz["questions"]:
                self.assertNotIn(question["country_name"], title)

    def test_disk_space_failure_creates_no_success_history(self):
        with patch.object(pipeline, "find_ffmpeg", return_value="unused"), \
                patch.object(pipeline.shutil, "disk_usage", return_value=SimpleNamespace(free=1)):
            results = pipeline.generate_batch(count=3, output_root=self.root)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r["status"] == "failed" for r in results))
        self.assertEqual(History(history_path()).list_runs(), [])

    def test_output_root_as_file_is_rejected(self):
        self.root.parent.mkdir(parents=True)
        self.root.write_text("Existing user file; must never be overwritten", encoding="utf-8")
        with self.assertRaises(OSError):
            pipeline.generate_batch(output_root=self.root)
        self.assertEqual(self.root.read_text(encoding="utf-8"), "Existing user file; must never be overwritten")


if __name__ == "__main__":
    unittest.main()
