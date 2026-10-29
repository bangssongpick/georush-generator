"""Publish exactly three user files; keep production evidence privately."""
from pathlib import Path
import os
import shutil
import sqlite3
import subprocess
import tempfile

from PIL import Image
from .paths import data_root, history_path, subprocess_options
from .history import History

FINAL_FILES = {'shorts.mp4', 'shorts_metadata.txt', 'shorts_thumbnail.jpg'}


def get_history(output_root):
    history = History(history_path())
    legacy = Path(output_root)/'georush_history.sqlite3'
    if legacy.is_file() and legacy.resolve() != history.path.resolve():
        # Copy records, not files: preserve earlier roots and leave their DB intact.
        source = sqlite3.connect(legacy.resolve().as_uri()+'?mode=ro', uri=True)
        try:
            rows = source.execute('SELECT created_at,signature,difficulty,output_path,status,error,quiz_json FROM runs').fetchall()
            with history._connect() as target:
                target.executemany('INSERT OR IGNORE INTO runs(created_at,signature,difficulty,output_path,status,error,quiz_json) VALUES(?,?,?,?,?,?,?)', rows)
        finally:
            source.close()
    return history


def combine_metadata(work):
    work = Path(work)
    text = ('[제목]\n'+(work/'title.txt').read_text(encoding='utf-8').strip()+
            '\n\n[설명] (해시태그까지 통째로 복사)\n'+(work/'description.txt').read_text(encoding='utf-8').strip()+
            '\n\n[고정 댓글]\n'+(work/'pinned_comment.txt').read_text(encoding='utf-8').strip()+
            '\n\n[태그] (쉼표 포함 통째로 복사)\n'+(work/'tags.txt').read_text(encoding='utf-8').strip()+
            '\n\n[카테고리]\n교육 / 아동용 아님\n\n'+'='*50+'\n')
    (work/'shorts_metadata.txt').write_text(text, encoding='utf-8-sig')


def extract_thumbnail(video, destination, ffmpeg):
    result = subprocess.run([str(ffmpeg), '-hide_banner', '-v', 'error', '-y', '-ss', '0',
                             '-i', str(video), '-frames:v', '1', '-q:v', '2', str(destination)],
                            capture_output=True, timeout=60, **subprocess_options())
    if result.returncode:
        raise RuntimeError('대표 이미지 생성 실패: '+result.stderr.decode('utf-8', errors='replace')[-1500:])
    with Image.open(destination) as image:
        if image.format != 'JPEG' or image.size != (1080, 1920):
            raise ValueError('대표 이미지는 실제 영상의 1080×1920 JPG여야 합니다.')
        image.verify()


def publish(work, final):
    work, final = Path(work), Path(final)
    stage = Path(tempfile.mkdtemp(prefix='.GeoRush_pending_', dir=final.parent))
    try:
        for source, name in [('video.mp4', 'shorts.mp4'), ('shorts_metadata.txt', 'shorts_metadata.txt'),
                             ('shorts_thumbnail.jpg', 'shorts_thumbnail.jpg')]:
            shutil.copy2(work/source, stage/name)
        if {p.name for p in stage.iterdir()} != FINAL_FILES:
            raise ValueError('최종 출력 파일 수가 올바르지 않습니다.')
        stage.rename(final)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def keep_success_evidence(work):
    work = Path(work)
    # Video exists in the validated final directory; synthesized PCM is reproducible.
    for name in ('video.mp4', 'original_audio.wav'):
        (work/name).unlink(missing_ok=True)
    for path in work.glob('*.partial.mp4'):
        path.unlink(missing_ok=True)
    if os.environ.get('GEORUSH_DEBUG') != '1':
        for name in ('inspection', 'encoded_inspection'):
            path = work/name
            if path.is_dir():
                shutil.rmtree(path)
