"""Actual FFmpeg fallback check: Windows imageio builds need no ffprobe."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from georush.paths import find_ffmpeg, subprocess_options
from georush.validation import validate_video


class RealMediaValidationTests(unittest.TestCase):
    def test_actual_decode_without_ffprobe(self):
        try:
            ffmpeg = find_ffmpeg()
        except FileNotFoundError:
            self.skipTest('Local FFmpeg is not installed')
        with tempfile.TemporaryDirectory(prefix='GeoRush 검증 ') as folder:
            path = Path(folder)/'실제 영상.mp4'
            result = subprocess.run([ffmpeg, '-v', 'error', '-y', '-f', 'lavfi', '-i',
                                     'testsrc2=size=1080x1920:rate=30:duration=1',
                                     '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=1',
                                     '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '2',
                                     '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ac', '2', '-t', '1', str(path)],
                                    capture_output=True, timeout=60, **subprocess_options())
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            with patch('georush.validation.shutil.which', return_value=None):
                report = validate_video(path, expected_duration=1, expected_frames=30, ffmpeg_path=ffmpeg)
            self.assertTrue(all(report['checks'].values()))
            self.assertEqual(report['probe_method'], 'ffmpeg_stream_header_and_full_decode')


if __name__ == '__main__':
    unittest.main()
