"""Review actual encoded frame numbers, not stand-in images. Developer check only."""
from pathlib import Path
import json
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw
from .audio import COUNTDOWN_SECONDS, CTA_SECONDS, QUESTION_SECONDS
from .render import prepare_animation, animated_frame, _font
from .paths import subprocess_options


def review_video(video, quiz, destination, ffmpeg):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    # Frame numbers follow the real timing constants (v1.3.6: 5.5 s questions, 4 s countdown, 3 s call-to-action).
    reveal=round(COUNTDOWN_SECONDS*30);second_question=round(QUESTION_SECONDS*30)
    last=round((len(quiz['questions'])*QUESTION_SECONDS+CTA_SECONDS)*30)-1
    indices=[0,3,9,21,30,33,75,93,reveal-1,reveal+1,reveal+4,second_question,last]
    select='select='+ '+'.join(f'eq(n\\,{n})' for n in indices)
    result=subprocess.run([str(ffmpeg),'-hide_banner','-v','error','-y','-i',str(video),
                           '-vf',select,'-fps_mode','passthrough','-frames:v',str(len(indices)),
                           str(destination/'frame_%02d.png')],capture_output=True,timeout=120,**subprocess_options())
    if result.returncode:raise RuntimeError(result.stderr.decode('utf8',errors='replace')[-2000:])
    context=prepare_animation(quiz['questions']);frames={};checks=[]
    for order,n in enumerate(indices,1):
        path=destination/f'frame_{order:02d}.png'
        with Image.open(path) as im:
            assert im.size==(1080,1920)
            pixels=np.asarray(im.convert('RGB'),dtype=float)
        expected=np.asarray(animated_frame(context,n/30),dtype=float)
        error=float(np.mean((pixels-expected)**2));psnr=10*math.log10(255**2/max(error,1e-12))
        assert psnr>28,('Encoded frame differs from intended presentation',n,psnr)
        frames[n]=pixels
        checks.append({'frame':n,'seconds':n/30,'file':path.name,'intended_frame_psnr_db':round(psnr,3)})
    intro_delta=float(np.abs(frames[0][469:921,151:929]-frames[9][469:921,151:929]).mean())
    assert intro_delta>1,('Encoded flag entrance does not move',intro_delta)
    assert frames[0][480:915,170:910].std()>20
    for n in (reveal+1,reveal+4):
        winners=[]
        for option in range(4):
            x=76+option%2*480;y=1255+option//2*178
            p=frames[n][y:y+147,x:x+449]
            green=(p[:,:,1]>p[:,:,0]+60)&(p[:,:,1]>p[:,:,2]+25)&(p[:,:,1]>140)
            if green.sum()>1000:winners.append(option)
        assert winners==[quiz['questions'][0]['correct_index']],('Incorrect revealed answer',n,winners)
    for n in (0,second_question):
        p=frames[n][1245:1605,60:1030]
        green=(p[:,:,1]>p[:,:,0]+60)&(p[:,:,1]>p[:,:,2]+25)&(p[:,:,1]>140)
        assert green.sum()<200,('Answer effect leaked into new question',n)
    selected=[0,9,21,30,75,reveal-1,reveal+1,second_question,last]
    sheet=Image.new('RGB',(810,1530),'#031025');draw=ImageDraw.Draw(sheet)
    for i,n in enumerate(selected):
        x=i%3*270;y=i//3*510
        image=Image.fromarray(frames[n].astype('uint8')).resize((270,480),Image.Resampling.LANCZOS)
        sheet.paste(image,(x,y+30));draw.text((x+8,y+5),f'{n/30:.3f}s / f{n}',font=_font(18),fill='white')
    sheet.save(destination/'CONTACT_SHEET.jpg',quality=93)
    report={'status':'PASS','video':str(video),'frames':checks,'encoded_flag_intro_mean_delta':round(intro_delta,3),
            'first_frame_visible_flag_and_question':True,'answer_green_matches_correct_index':True,
            'no_answer_effect_at_question_start':True,'comparison':'Encoded pixels vs intended Pillow frames, PSNR>28dB',
            'question_codes':[q['country_code'] for q in quiz['questions']],
            'human_review_required':['interest of first second','subjective audio quality','mobile viewing comfort']}
    (destination/'PRESENTATION_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report
