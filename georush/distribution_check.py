"""Automated real GUI-button render check, runnable inside the frozen EXE."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import tempfile


def run_check(report_path, output_root=None):
    from .catalog import Catalog
    from .gui import GeoRushApp
    from .history import History
    from .output import get_history, FINAL_FILES
    from .paths import data_root
    from .paths import default_output_root, find_ffmpeg, resource_root
    from .quiz import validate_quiz
    from tkinter import font
    report_path = Path(report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output = Path(output_root or report_path.parent/'OneDrive 테스트'/'바탕 화면'/'GeoRush_Output').resolve()
    report = {'platform': sys.platform, 'frozen': bool(getattr(sys, 'frozen', False)),
              'resource_root': str(resource_root()), 'output_root': str(output),
              'onedrive_test_scope': 'Unicode OneDrive-like local path; real cloud sync not tested',
              'manual_appearance_review_required': True}
    app = None
    try:
        catalog = Catalog()
        valid, errors = catalog.valid_countries()
        assert len(valid) == 60 and not errors
        ffmpeg = Path(find_ffmpeg()).resolve()
        report['ffmpeg'] = str(ffmpeg)
        if report['frozen']:
            assert ffmpeg.is_relative_to(resource_root().resolve()), 'EXE used external FFmpeg'
        report['shell_desktop_output'] = str(default_output_root())
        if sys.platform == 'win32':
            desktop = default_output_root().parent
            desktop.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='GeoRush 경로 ', dir=desktop) as test_dir:
                probe = Path(test_dir)/'한글 확인.txt'
                probe.write_text('GeoRush 경로 확인', encoding='utf-8')
                assert probe.read_text(encoding='utf-8') == 'GeoRush 경로 확인'
            report['real_shell_desktop_write_read_pass'] = True
        app = GeoRushApp()
        report['default_font'] = font.nametofont('TkDefaultFont').actual('family')
        if sys.platform == 'win32':
            assert report['default_font'].lower() in ('malgun gothic', '맑은 고딕')
        app.output.set(str(output))
        video_count=int(os.environ.get('GEORUSH_CHECK_COUNT','1'))
        assert video_count in (1,3)
        app.video_count.set(str(video_count)); app.questions.set(3); app.bgm.set('10%')
        app.update()
        history = get_history(output)
        before = history.list_runs(limit=1)
        before_id = before[0]['id'] if before else 0
        beats = []
        def heartbeat():
            beats.append(time.monotonic())
            app.after(100, heartbeat)
        app.after(100, heartbeat)
        app.start_button.invoke()
        assert str(app.start_button['state']) == 'disabled'
        start = time.monotonic(); progress = []
        while time.monotonic()-start < 240:
            app.update(); progress.append(app.progress.get())
            if str(app.start_button['state']) == 'normal':
                break
            time.sleep(.02)
        assert app.results.get() == f'성공 {video_count}편 · 실패 0편', app.log.get('1.0', 'end')
        rows = [row for row in history.list_runs() if row['id']>before_id]
        assert len(rows)==video_count and all(row['status']=='success' for row in rows)
        batch=[]
        from .presentation_review import review_video
        for row in reversed(rows):
            folder = Path(row['output_path'])
            assert {p.name for p in folder.iterdir()} == FINAL_FILES
            assert all(p.is_file() for p in folder.iterdir())
            debug = data_root()/'debug'/folder.name
            quiz = json.loads((debug/'quiz_data.json').read_text(encoding='utf-8'))
            text = (folder/'shorts_metadata.txt').read_text(encoding='utf-8-sig')
            for header in ('[제목]', '[설명]', '[고정 댓글]', '[태그]', '[카테고리]'):
                assert header in text
            assert all(q['country_name'] not in text for q in quiz['questions'])
            from PIL import Image
            with Image.open(folder/'shorts_thumbnail.jpg') as thumbnail:
                assert thumbnail.size == (1080,1920) and thumbnail.format == 'JPEG'
            assert not (debug/'original_audio.wav').exists()
            validate_quiz(quiz, catalog)
            media = json.loads((debug/'MEDIA_REPORT.json').read_text(encoding='utf-8'))
            assert all(media['checks'].values())
            render = json.loads((debug/'RENDER_REPORT.json').read_text(encoding='utf-8'))
            assert render['audio']['clipped_samples'] == 0
            visual=review_video(folder/'shorts.mp4',quiz,debug/'v12_review',ffmpeg)
            batch.append({'video_folder':str(folder),'media':media,'render_audio':render['audio'],
                          'exact_three_user_files':sorted(p.name for p in folder.iterdir()),
                          'presentation_review':visual,
                          'video_sha256':hashlib.sha256((folder/'shorts.mp4').read_bytes()).hexdigest()})
        assert len(beats) > 2 and any(0 < p < 100 for p in progress)
        report.update(status='PASS', video_folder=batch[-1]['video_folder'],media=batch[-1]['media'],
                      exact_three_user_files=batch[-1]['exact_three_user_files'],
                      internal_history=str(history.path),internal_debug=str(debug),
                      thumbnail_from_final_video=True,batch_videos=batch,
                      heartbeat_count=len(beats),elapsed_seconds=round(time.monotonic()-start,3),
                      video_sha256=batch[-1]['video_sha256'])
    except Exception:
        report.update(status='FAIL', error=traceback.format_exc())
    finally:
        if app is not None:
            app.destroy()
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['status'] == 'PASS' else 1
