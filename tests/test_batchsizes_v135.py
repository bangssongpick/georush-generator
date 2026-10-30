"""v1.3.5: one run may make 1/2/3/5/10/20 Shorts (Longform 1/2/3); every entry point reads the same list."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from georush import pipeline
from georush.batchsizes import LONGFORM_BATCH_SIZES, SHORTS_BATCH_SIZES

ROOT = Path(__file__).resolve().parents[1]


class BatchSizeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="GeoRush 개수 ")
        self.root = Path(self.temporary.name) / "출력"
        env = patch.dict(os.environ, {"GEORUSH_DATA_DIR": str(Path(self.temporary.name) / "데이터")})
        env.start(); self.addCleanup(env.stop)
        thumbnail = patch.object(pipeline, "extract_thumbnail",
                                 side_effect=lambda video, target, ffmpeg: Image.new("RGB", (1080, 1920), "blue").save(target))
        thumbnail.start(); self.addCleanup(thumbnail.stop)
        self.addCleanup(self.temporary.cleanup)

    def run_batch(self, count):
        def fake_render(quiz, destination, *args, **kwargs):
            Path(destination).write_bytes(b"unit test fake video")
            return {"test_fixture": True}
        with patch.object(pipeline, "find_ffmpeg", return_value="unused"), \
                patch.object(pipeline, "render_video", side_effect=fake_render), \
                patch.object(pipeline, "validate_video", return_value={"test_fixture": True}), \
                patch.object(pipeline, "extract_encoded_frames", return_value=[]):
            return pipeline.generate_batch(count=count, output_root=self.root, seed=5)

    def test_the_lists(self):
        self.assertEqual(SHORTS_BATCH_SIZES, (1, 2, 3, 5, 10, 20))
        self.assertEqual(LONGFORM_BATCH_SIZES, (1, 2, 3))

    def test_other_counts_are_refused_with_a_clear_message(self):
        for count in (0, 4, 7, 15, 21, 100, True * 4):
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, '1 / 2 / 3 / 5 / 10 / 20'):
                pipeline.generate_batch(count=count, output_root=self.root)

    def test_twenty_shorts_in_one_run_never_repeat_a_flag(self):
        results = self.run_batch(20)
        self.assertEqual([r['status'] for r in results], ['success'] * 20)
        self.assertEqual(len({r['path'] for r in results}), 20)
        import json
        flags = []
        for result in results:
            quiz = json.loads((Path(result['debug_path']) / 'quiz_data.json').read_text(encoding='utf-8'))
            flags += [q['country_code'] for q in quiz['questions']]
        self.assertEqual(len(flags), 60)
        self.assertEqual(len(set(flags)), 60)  # inside one week of Shorts no flag repeats (v1.3.5)

    def test_two_shorts_work_now(self):
        self.assertEqual([r['status'] for r in self.run_batch(2)], ['success', 'success'])  # used to pass argparse but fail here

    def test_every_entry_point_reads_the_shared_list(self):
        for name in ('main.py', 'georush/gui.py', 'georush/pipeline.py'):
            self.assertIn('SHORTS_BATCH_SIZES', (ROOT / name).read_text(encoding='utf-8'), name)
        self.assertNotIn('(1, 3, 5, 10)', (ROOT / 'georush/gui.py').read_text(encoding='utf-8'))
        self.assertNotIn('(1,3,5,10)', (ROOT / 'georush/gui.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
