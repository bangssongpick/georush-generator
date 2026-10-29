"""Windows path-resolution contracts simulated on Linux, not Windows execution."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from georush import paths


class UnicodePathTests(unittest.TestCase):
    def test_windows_shell_desktop_honors_onedrive_redirection(self):
        with tempfile.TemporaryDirectory(prefix="GeoRush OneDrive 바탕 화면 ") as folder:
            redirected = str(Path(folder) / "OneDrive" / "바탕 화면")

            def shell_desktop(_window, folder_id, _token, _flags, buffer):
                self.assertEqual(folder_id, 0x10)
                buffer.value = redirected
                return 0

            shell = SimpleNamespace(shell32=SimpleNamespace(SHGetFolderPathW=shell_desktop))
            with patch.object(paths.sys, "platform", "win32"), \
                    patch.object(paths.ctypes, "windll", shell, create=True):
                self.assertEqual(paths.default_output_root(), Path(redirected) / "GeoRush_Output")

    def test_windows_desktop_fallback_retains_unicode(self):
        with tempfile.TemporaryDirectory(prefix="GeoRush 경로 ") as folder:
            desktop = Path(folder) / "Desktop"
            desktop.mkdir()
            shell = SimpleNamespace(shell32=SimpleNamespace(SHGetFolderPathW=lambda *args: 1))
            with patch.object(paths.sys, "platform", "win32"), \
                    patch.object(paths.ctypes, "windll", shell, create=True), \
                    patch.dict(paths.os.environ, {"OneDrive": folder}, clear=True):
                self.assertEqual(paths.default_output_root(), desktop / "GeoRush_Output")

    def test_configured_ffmpeg_unicode_path_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix="GeoRush 도구 ") as folder:
            executable = Path(folder) / "FFmpeg 실행.exe"
            executable.write_bytes(b"fake executable path fixture, never executed")
            with patch.dict(paths.os.environ, {"GEORUSH_FFMPEG": str(executable)}):
                self.assertEqual(Path(paths.find_ffmpeg()), executable.resolve())

    def test_missing_explicit_ffmpeg_does_not_silently_use_another(self):
        with patch.dict(paths.os.environ, {"GEORUSH_FFMPEG": "/nonexistent/GeoRush ffmpeg.exe"}):
            with self.assertRaises(FileNotFoundError):
                paths.find_ffmpeg()


if __name__ == "__main__":
    unittest.main()
