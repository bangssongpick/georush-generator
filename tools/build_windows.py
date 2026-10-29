"""Run on Windows only; assemble a Python-free directory distribution."""
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import json
import os
import tempfile
import hashlib

ROOT = Path(__file__).resolve().parents[1]


def build():
    if sys.platform != 'win32':
        raise SystemExit('Windows EXE must be built on Windows.')
    import imageio_ffmpeg
    ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    staging = ROOT/'build_support'
    staging.mkdir(exist_ok=True)
    bundled_source = staging/'ffmpeg.exe'
    shutil.copy2(ffmpeg, bundled_source)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
                    '--windowed', '--name', 'GeoRushGenerator', '--add-data', f'{ROOT / "assets"};assets',
                    '--add-binary', f'{bundled_source};bin', '--exclude-module', 'imageio_ffmpeg',
                    '--collect-all', 'PIL', '--hidden-import', 'tkinter', str(ROOT/'main.py')], cwd=ROOT, check=True)
    folder = ROOT/'dist'/'GeoRushGenerator'
    (folder/'START_HERE.cmd').write_bytes(b'@echo off\r\nstart "GeoRush" "%~dp0GeoRushGenerator.exe"\r\n')
    for name in ('THIRD_PARTY_NOTICES.md', 'LICENSE', 'V11_OUTPUT_KO.md'):
        shutil.copy2(ROOT/name, folder/name)
    (folder/'README.txt').write_text('GeoRush Windows x64\n\n압축을 완전히 풀고 START_HERE.cmd 또는 GeoRushGenerator.exe를 실행하세요.\nPython 설치는 필요 없습니다. _internal 폴더를 함께 보관하세요.\n기본 출력: Windows 실제 바탕화면의 GeoRush_Output\n영상 폴더에는 shorts.mp4, shorts_metadata.txt, shorts_thumbnail.jpg 3개만 생성됩니다.\n이력·로그: %LOCALAPPDATA%\\GeoRush (자세한 내용은 V11_OUTPUT_KO.md)\n검증 범위와 실제 실행 결과: WINDOWS_VALIDATION.json\nOneDrive 실시간 동기화 및 화면 외관은 사용자 PC에서 확인하세요.\n', encoding='utf-8')
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
    environment['GEORUSH_DATA_DIR'] = str(ROOT/'build_validation'/'AppData'/'GeoRush')
    environment['PATH'] = os.pathsep.join([str(Path(os.environ['SystemRoot'])/'System32'), os.environ['SystemRoot']])
    subprocess.run([str(folder/'GeoRushGenerator.exe'), '--distribution-check', str(report),
                    '--output', str(report.parent/'OneDrive 테스트'/'바탕 화면'/'GeoRush_Output')],
                   env=environment, check=True, timeout=300)
    result = json.loads(report.read_text(encoding='utf-8'))
    if result.get('status') != 'PASS' or not result.get('frozen'):
        raise SystemExit('EXE integration failed. See '+str(report))
    shutil.copy2(report, folder/report.name)
    moved_root = Path(tempfile.mkdtemp(prefix='GeoRush 이동 검증 '))
    moved = moved_root/'GeoRush 앱'
    shutil.copytree(folder, moved)
    moved_report = report.with_name('WINDOWS_RELOCATION_VALIDATION.json')
    moved_report.unlink(missing_ok=True)
    subprocess.run([str(moved/'GeoRushGenerator.exe'), '--distribution-check', str(moved_report),
                    '--output', str(report.parent/'OneDrive 테스트'/'바탕 화면'/'GeoRush_Output')],
                   env=environment, check=True, timeout=300)
    moved_result = json.loads(moved_report.read_text(encoding='utf-8'))
    if moved_result.get('status') != 'PASS' or not moved_result.get('frozen'):
        raise SystemExit('Relocated EXE integration failed. See '+str(moved_report))
    shutil.copy2(moved_report, folder/moved_report.name)
    archive = ROOT/'dist'/'GeoRush-v1.1-Windows-EXE.zip'
    temporary = archive.with_suffix('.pending.zip')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in folder.rglob('*'):
            if path.is_file():
                output.write(path, 'GeoRushGenerator/'+path.relative_to(folder).as_posix())
    with zipfile.ZipFile(temporary) as output:
        if output.testzip() is not None:
            raise SystemExit('ZIP CRC check failed')
    temporary.replace(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n', encoding='ascii')
    summary = {'windows_exe_build':'PASS','exe_bytes':(folder/'GeoRushGenerator.exe').stat().st_size,
               'zip_bytes':archive.stat().st_size,'zip_sha256':digest,
               'gui_to_mp4':result,'relocated_gui_to_mp4':moved_result,
               'system_python_and_ffmpeg_removed_from_test_PATH':True,
               'limits':['Windows hosted runner is not a clean physical PC', 'Manual GUI appearance and listening review needed', 'Real OneDrive sync not tested']}
    (ROOT/'dist'/'WINDOWS_BUILD_REPORT.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Windows EXE GUI-to-MP4 PASS. ZIP:', archive)
