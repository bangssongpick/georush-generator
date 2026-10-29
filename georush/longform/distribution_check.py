"""Real Tk button -> frozen producer -> complete decode and visual evidence."""
import json
import os
from pathlib import Path
import sys
import time
import traceback
from PIL import Image
from ..paths import data_root,resource_root,find_ffmpeg
from ..output import get_history
from .quiz import validate
from .output import FINAL_FILES,metadata
from .review import review


def run_check(report_path,output_root=None):
    from ..gui import GeoRushApp
    from ..catalog import Catalog
    report_path=Path(report_path);report_path.parent.mkdir(parents=True,exist_ok=True)
    output=Path(output_root or report_path.parent/'OneDrive 테스트'/'바탕 화면'/'GeoRush_Output')
    report={'platform':sys.platform,'frozen':bool(getattr(sys,'frozen',False)),'mode':'Longform'};app=None
    try:
        count=int(os.environ.get('GEORUSH_LONGFORM_QUESTIONS','20'));assert count in (20,30,40)
        ffmpeg=Path(find_ffmpeg()).resolve()
        if report['frozen']:assert ffmpeg.is_relative_to(resource_root().resolve())
        app=GeoRushApp();app.output.set(str(output));app.mode.set('Longform');app._mode_changed()
        app.long_questions.set(str(count));app.long_video_count.set('1')
        assert app.questions.get()==3 and app.video_count.get()=='1', 'Shorts settings were mutated'
        history=get_history(output);previous=history.list_runs(10000);before=max((r['id'] for r in previous),default=0)
        beats=[]
        def heartbeat():beats.append(time.monotonic());app.after(100,heartbeat)
        app.after(100,heartbeat);app.update();app.start_button.invoke()
        assert str(app.start_button['state'])=='disabled'
        started=time.monotonic();progress=[]
        while time.monotonic()-started<1500:
            app.update();progress.append(app.progress.get())
            if str(app.start_button['state'])=='normal':break
            time.sleep(.02)
        assert app.results.get()=='성공 1편 · 실패 0편',app.log.get('1.0','end')
        rows=[r for r in history.list_runs(10000) if r['id']>before]
        assert len(rows)==1 and rows[0]['status']=='success'
        # Previous rows remain byte-for-byte semantically unchanged; no DB migration.
        now={r['id']:r for r in history.list_runs(10000)}
        assert all(now[r['id']]==r for r in previous)
        folder=Path(rows[0]['output_path']);debug=data_root()/'debug'/folder.name
        assert {p.name for p in folder.iterdir()}==FINAL_FILES
        quiz=json.loads((debug/'quiz_data.json').read_text(encoding='utf-8'))
        timeline=json.loads((debug/'timeline.json').read_text(encoding='utf-8'))
        validate(quiz,Catalog());assert len(quiz['questions'])==count
        assert (folder/'longform_metadata.txt').read_text(encoding='utf-8-sig')==metadata(quiz,timeline)
        with Image.open(folder/'longform_thumbnail.jpg') as im:assert im.size==(1920,1080) and im.format=='JPEG'
        media=json.loads((debug/'MEDIA_REPORT.json').read_text(encoding='utf-8'));assert all(media['checks'].values())
        render=json.loads((debug/'RENDER_REPORT.json').read_text(encoding='utf-8'));assert render['audio']['clipped_samples']==0
        assert not (debug/'original_audio.wav').exists()
        visual=review(folder/'longform.mp4',quiz,timeline,debug/'review',ffmpeg)
        assert len(beats)>2 and any(0<p<100 for p in progress)
        app.mode.set('Shorts');app._mode_changed();assert app.questions.get()==3
        report.update(status='PASS',questions=count,video_folder=str(folder),media=media,render=render,visual=visual,
                      exact_three_files=sorted(FINAL_FILES),history_rows_preserved=len(previous),heartbeat_count=len(beats),
                      elapsed_seconds=round(time.monotonic()-started,3),debug_folder=str(debug),ffmpeg=str(ffmpeg))
    except Exception:report.update(status='FAIL',error=traceback.format_exc())
    finally:
        if app is not None:app.destroy()
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if report['status']=='PASS' else 1
