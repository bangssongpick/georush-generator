"""Unicode-safe local paths and local executable discovery; no downloads."""
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import sys


def resource_root():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))


def data_root():
    override = os.environ.get('GEORUSH_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData'/'Local')))/'GeoRush'
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local'/'share')))/'GeoRush'


def history_path():
    return data_root()/'georush_history.sqlite3'


def default_output_root():
    if sys.platform == 'win32':
        # Windows shell Desktop honors redirected/OneDrive Desktop locations.
        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buffer) == 0:
            return Path(buffer.value) / 'GeoRush_Output'
        for key in ('OneDrive', 'OneDriveConsumer', 'USERPROFILE'):
            base = os.environ.get(key)
            if base and (Path(base)/'Desktop').is_dir():
                return Path(base)/'Desktop'/'GeoRush_Output'
    return Path.home()/'Desktop'/'GeoRush_Output'


def find_ffmpeg():
    configured = os.environ.get('GEORUSH_FFMPEG')
    if configured:
        path = Path(configured).expanduser()
        if not path.is_file():
            raise FileNotFoundError('GEORUSH_FFMPEG 경로에 실행 파일이 없습니다.')
        return str(path.resolve())
    for path in (resource_root()/'bin'/'ffmpeg.exe', resource_root()/'bin'/'ffmpeg'):
        if path.is_file():
            return str(path)
    found = shutil.which('ffmpeg')
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise FileNotFoundError('로컬 FFmpeg가 없습니다. INSTALL.cmd를 실행하거나 bin/ffmpeg.exe를 넣어 주세요.') from exc


def subprocess_options():
    return {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}


def open_folder(path):
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'win32':
        os.startfile(str(path))
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', str(path)])
    else:
        subprocess.Popen(['xdg-open', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
