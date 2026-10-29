"""Independent optional producer; compatible SQLite rows without destructive migration."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import sqlite3
import traceback
import uuid
from ..catalog import Catalog
from ..output import get_history
from ..paths import data_root,default_output_root,find_ffmpeg
from ..validation import validate_video
from .quiz import build,validate,allocations
from .timeline import build_timeline
from .render import render
from .output import metadata,thumbnail,publish


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def generate_batch(count=1,difficulty='Mixed',questions_per_video=40,bgm_volume=.10,
                   output_root=None,progress_callback=None,seed=None):
    if type(count) is not int or count not in (1,2,3):raise ValueError('롱폼 제작 편수는 1 / 2 / 3입니다.')
    allocations(questions_per_video)
    if difficulty!='Mixed':raise ValueError('롱폼 v1.3 난이도는 Mixed입니다.')
    if bgm_volume not in (.08,.10,.12):raise ValueError('BGM 볼륨은 8 / 10 / 12%입니다.')
    root=Path(output_root or default_output_root()).expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
    internal=data_root();catalog=Catalog();history=get_history(root);ffmpeg=find_ffmpeg();results=[]
    def emit(index,stage,progress,message):
        if progress_callback:
            try:progress_callback({'index':index,'total':count,'stage':stage,'progress':progress,'message':message})
            except Exception:pass
    for index in range(1,count+1):
        work=None;run_id=None;final=None
        try:
            emit(index,'prepare',0,'롱폼 국가·난이도 검증 중')
            for location in {root,internal}:
                location.mkdir(parents=True,exist_ok=True)
                if shutil.disk_usage(location).free<1024**3:raise OSError('롱폼 제작에는 출력·내부 데이터 드라이브에 각각 최소 1GB 여유 공간이 필요합니다.')
            label=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')+'_'+uuid.uuid4().hex[:6]
            final=root/('GeoRush_Longform_'+label);work=internal/'debug'/final.name;work.mkdir(parents=True)
            for retry in range(8):
                quiz=build(catalog,history,questions_per_video,None if seed is None else seed+index+retry*1009)
                try:
                    run_id=history.reserve_quiz(quiz['signature'],'Mixed',final,quiz);break
                except sqlite3.IntegrityError:
                    if retry==7:raise ValueError('다른 작업의 롱폼 문제 순서와 충돌합니다.')
            timeline=build_timeline(quiz)
            write(work/'quiz_data.json',quiz);write(work/'timeline.json',timeline)
            report=render(quiz,timeline,work,ffmpeg,bgm_volume,
                          lambda p,m:emit(index,'render',p*.9,m))
            emit(index,'validate',.92,'롱폼 영상·오디오 전체 디코딩 및 규격 검사')
            media=validate_video(work/'longform.mp4',timeline['duration'],timeline['frames'],ffmpeg,
                                 expected_resolution=(1920,1080),decode_timeout=600)
            validate(quiz,catalog)
            (work/'longform_metadata.txt').write_text(metadata(quiz,timeline),encoding='utf-8-sig')
            report['thumbnail']=thumbnail(quiz,work/'longform_thumbnail.jpg')
            write(work/'MEDIA_REPORT.json',media);write(work/'RENDER_REPORT.json',report)
            publish(work,final);history.finish(run_id,True)
            # Only private reproducible temporary media is removed, after successful publication.
            try:
                for name in ('longform.mp4','original_audio.wav','segments.ffconcat'):(work/name).unlink(missing_ok=True)
            except OSError as cleanup_error:
                (work/'CLEANUP_WARNING.txt').write_text(str(cleanup_error),encoding='utf-8')
            results.append({'status':'success','path':str(final),'debug_path':str(work),'signature':quiz['signature'],
                            'mode':'Longform','duration':timeline['duration'],'error':''})
            emit(index,'success',1,'롱폼 제작 성공: '+final.name)
        except Exception as exc:
            if run_id is not None:
                try:history.finish(run_id,False,str(exc))
                except Exception:
                    if work:(work/'HISTORY_ERROR.txt').write_text(traceback.format_exc(),encoding='utf-8')
            if work:
                (work/'ERROR.txt').write_text(traceback.format_exc(),encoding='utf-8')
            results.append({'status':'failed','path':str(work or internal),'mode':'Longform','error':str(exc)})
            emit(index,'failed',1,'롱폼 실패: '+str(exc))
    return results
