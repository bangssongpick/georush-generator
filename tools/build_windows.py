"""Run on Windows only; assemble a Python-free directory distribution."""
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import json
import os

ROOT = Path(__file__).resolve().parents[1]


def build():
    if sys.platform != 'win32':
        raise SystemExit('Windows EXE must be built on Windows.')
    import imageio_ffmpeg
    ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
                    '--windowed', '--name', 'GeoRushGenerator', '--add-data', f'{ROOT / "assets"};assets',
                    '--add-binary', f'{ffmpeg};bin', '--collect-all', 'imageio_ffmpeg',
                    '--collect-all', 'PIL', '--hidden-import', 'tkinter', str(ROOT/'main.py')], cwd=ROOT, check=True)
    folder = ROOT/'dist'/'GeoRushGenerator'
    bundled = folder/'_internal'/'bin'/ffmpeg.name
    # Canonical local name ensures PATH/system FFmpeg cannot mask a missing resource.
    shutil.copy2(bundled, bundled.with_name('ffmpeg.exe')) if bundled.name != 'ffmpeg.exe' else None
    (folder/'START_HERE.cmd').write_bytes(b'@echo off\r\nstart "GeoRush" "%~dp0GeoRushGenerator.exe"\r\n')
    for name in ('THIRD_PARTY_NOTICES.md', 'LICENSE'):
        shutil.copy2(ROOT/name, folder/name)
    (folder/'README.txt').write_text('GeoRush Windows x64\n\n압축을 완전히 풀고 START_HERE.cmd 또는 GeoRushGenerator.exe를 실행하세요.\nPython 설치는 필요 없습니다. _internal 폴더를 함께 보관하세요.\n기본 출력: Windows 실제 바탕화면의 GeoRush_Output\n검증 범위와 실제 실행 결과: WINDOWS_VALIDATION.json\nOneDrive 실시간 동기화 및 화면 외관은 사용자 PC에서 확인하세요.\n', encoding='utf-8')
    with (folder/'FFMPEG_LICENSE_AND_BUILD.txt').open('w', encoding='utf-8') as out:
        subprocess.run([str(ffmpeg), '-L'], stdout=out, stderr=subprocess.STDOUT, check=True)
        subprocess.run([str(ffmpeg), '-buildconf'], stdout=out, stderr=subprocess.STDOUT, check=True)
    return folder


if __name__ == '__main__':
    folder = build()
    report = ROOT/'build_validation'/'WINDOWS_VALIDATION.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)
    environment = dict(os.environ)
    environment.pop('GEORUSH_FFMPEG', None)
    environment['PATH'] = os.pathsep.join([str(Path(os.environ['SystemRoot'])/'System32'), os.environ['SystemRoot']])
    subprocess.run([str(folder/'GeoRushGenerator.exe'), '--distribution-check', str(report),
                    '--output', str(report.parent/'OneDrive 테스트'/'바탕 화면'/'GeoRush_Output')],
                   env=environment, check=True, timeout=300)
    result = json.loads(report.read_text(encoding='utf-8'))
    if result.get('status') != 'PASS' or not result.get('frozen'):
        raise SystemExit('EXE integration failed. See '+str(report))
    shutil.copy2(report, folder/report.name)
    archive = ROOT/'dist'/'GeoRush-v1.0-Windows-x64.zip'
    temporary = archive.with_suffix('.pending.zip')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in folder.rglob('*'):
            if path.is_file():
                output.write(path, 'GeoRushGenerator/'+path.relative_to(folder).as_posix())
    with zipfile.ZipFile(temporary) as output:
        if output.testzip() is not None:
            raise SystemExit('ZIP CRC check failed')
    temporary.replace(archive)
    print('Windows EXE GUI-to-MP4 PASS. ZIP:', archive)
