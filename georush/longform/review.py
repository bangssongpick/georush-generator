"""Inspect actual encoded landscape frames against intended country/answer layouts."""
from pathlib import Path
import json
import math
import subprocess
import numpy as np
from PIL import Image,ImageDraw
from ..paths import subprocess_options
from .render import question_context,question_frame,screen,OPTION_BOXES
from .timeline import FPS,COUNTDOWN,chapters


def review(video,quiz,timeline,folder,ffmpeg):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    checks={0:('intro',None,0)}
    for segment in timeline['segments']:
        if segment['kind']=='question':
            base=segment['start']*FPS;index=segment['question_index']
            for offset in (0,9,COUNTDOWN*FPS+3):
                checks[base+offset]=('question',index,offset)
            if index==0:checks[base+COUNTDOWN*FPS-1]=('question',index,COUNTDOWN*FPS-1)
        elif segment['kind']=='chapter':checks[segment['start']*FPS]=('chapter',segment,0)
    checks[timeline['frames']-1]=('outro',timeline['segments'][-1],0)
    indices=sorted(checks)
    select='+'.join(f'eq(n,{f})' for f in indices)
    command=[str(ffmpeg),'-hide_banner','-v','error','-y','-i',str(video),'-vf',"select='"+select+"'",
             '-vsync','0','-q:v','2',str(folder/'frame_%03d.jpg')]
    p=subprocess.run(command,capture_output=True,timeout=600,**subprocess_options())
    if p.returncode:raise RuntimeError('롱폼 프레임 추출 실패: '+p.stderr.decode('utf-8',errors='replace')[-1200:])
    files=sorted(folder.glob('frame_*.jpg'))
    if len(files)!=len(indices):raise ValueError('실제 프레임 검사 수 불일치')
    entries=[];contexts={};minimum=100
    for frame,path in zip(indices,files):
        kind,info,offset=checks[frame]
        if kind=='question':
            if info not in contexts:
                contexts={info:question_context(quiz['questions'][info],info,len(quiz['questions']))}
            canonical=offset
            if 14<=offset<COUNTDOWN*FPS and offset%30>=5:canonical=offset//30*30+5
            if offset>=COUNTDOWN*FPS+10:canonical=COUNTDOWN*FPS+10
            intended=question_frame(contexts[info],canonical)
        else:intended=screen(timeline['segments'][0] if kind=='intro' else info,len(quiz['questions']))
        with Image.open(path) as source:actual=source.convert('RGB')
        difference=np.asarray(actual,dtype=np.float32)-np.asarray(intended,dtype=np.float32)
        mse=float(np.mean(difference**2));psnr=99 if not mse else 10*math.log10(255**2/mse)
        if psnr<28:raise ValueError(f'인코딩 프레임이 의도한 장면과 다릅니다: {frame}, PSNR={psnr:.2f}')
        minimum=min(minimum,psnr)
        entry={'frame':frame,'time':frame/FPS,'kind':kind,'psnr_db':round(psnr,3)}
        if kind=='question':
            q=quiz['questions'][info];entry.update(question=info+1,country_code=q['country_code'],answer_index=q['correct_index'])
            # Compare each complete card ROI, including the green correct card and name.
            for i,(x1,y1,x2,y2) in enumerate(OPTION_BOXES):
                roi=difference[y1-4:y2+4,x1-12:x2+12]
                if float(np.mean(roi**2))>240:raise ValueError('실제 선택지/정답 프레임 불일치')
            if offset==0:
                flag_pixels=np.asarray(actual)[300:600,600:1320]
                if np.std(flag_pixels)<12:raise ValueError('실제 문제 첫 프레임에서 국기 인식 불가')
        entries.append(entry)
    chosen=[0,1,2,3,4,min(7,len(files)-2),len(files)-1]
    sheet=Image.new('RGB',(1280,4*390),'#071226');d=ImageDraw.Draw(sheet)
    for slot,index in enumerate(chosen):
        with Image.open(files[index]) as source:
            tile=source.convert('RGB');tile.thumbnail((620,349));sheet.paste(tile,((slot%2)*640,(slot//2)*390))
        e=entries[index];d.text(((slot%2)*640+8,(slot//2)*390+352),f'{e["time"]:.2f}s / {e["kind"]} / {e["psnr_db"]} dB',fill='white')
    sheet.save(folder/'CONTACT_SHEET.jpg',quality=92)
    result={'status':'PASS','video':str(video),'inspected_frames':len(entries),'minimum_psnr_db':round(minimum,3),
            'all_questions_flag_and_reveal_checked':True,'chapters':chapters(timeline),'frames':entries,
            'scope':'Encoded frame/layout correspondence; not subjective engagement or manual listening'}
    (folder/'REVIEW.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
