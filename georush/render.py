"""Native 1080x1920 Pillow animation streamed into local FFmpeg."""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
import json
import math
import shutil
import subprocess
import time

from PIL import Image, ImageDraw, ImageFont

from .audio import synthesize_audio, QUESTION_SECONDS, COUNTDOWN_SECONDS, COUNTDOWN_TICKS, CTA_SECONDS
from .names import display_name
from .paths import resource_root, subprocess_options

WIDTH, HEIGHT, FPS = 1080, 1920, 30
YELLOW = '#FFE451'
WHITE = '#F5FAFF'
MUTED = '#B8D2FF'
GREEN = '#5DFFC2'
ASSETS = resource_root()/'assets'


@lru_cache(maxsize=64)
def _font(size):
    path = ASSETS/'fonts'/'DejaVuSans-Bold.ttf'
    if not path.is_file():
        raise FileNotFoundError(f'Bundled font missing: {path}')
    return ImageFont.truetype(str(path),size)


def _center(draw, text, y, size, fill=WHITE, max_width=940, x=WIDTH//2):
    size = int(size)
    while size > 20 and draw.textbbox((0,0),text,font=_font(size))[2] > max_width:
        size -= 1
    box = draw.textbbox((0,0),text,font=_font(size))
    draw.text((x-(box[2]-box[0])/2,y-box[1]),text,font=_font(size),fill=fill)
    return size


def _background():
    import numpy as np
    top=np.array([10,45,110]);bottom=np.array([4,19,54])
    value=np.linspace(0,1,HEIGHT)[:,None,None]
    pixels=np.tile(((1-value)*top+value*bottom).astype('uint8'),(1,WIDTH,1))
    image=Image.fromarray(pixels,'RGB')
    draw=ImageDraw.Draw(image)
    draw.arc((-390,370,1200,1960),218,314,fill='#163E7A',width=4)
    draw.arc((780,-460,1560,320),80,230,fill='#215391',width=4)
    draw.rounded_rectangle((74,74,1006,196),radius=30,fill='#103B80',outline='#2861A7',width=2)
    draw.text((110,97),'GeoRush',font=_font(58),fill=WHITE)
    draw.text((755,118),'FLAG QUIZ',font=_font(25),fill=YELLOW)
    return image


def _question_data(question):
    options=question['options']
    names=[str(value.get('name',value.get('country_name',''))) if isinstance(value,dict) else str(value) for value in options]
    correct=int(question['correct_index'])
    if len(names)!=4 or len(set(names))!=4 or correct not in range(4):
        raise ValueError('A question requires exactly four unique options and one correct index')
    if names[correct] != question['country_name']:
        raise ValueError('Correct answer does not match the question country')
    flag_path=Path(question['flag_path'])
    if not flag_path.is_file():
        raise FileNotFoundError(f'Flag image missing: {flag_path}')
    # The checks above use the verified names; viewers see the familiar display names.
    return [display_name(name) for name in names],correct,flag_path


def _option(draw, index, name, correct=False):
    x=76+(index%2)*480;y=1255+(index//2)*178
    draw.rounded_rectangle((x,y,x+448,y+146),radius=25,
                           fill='#0F584F' if correct else '#12356B',
                           outline=GREEN if correct else '#5078B4',width=5 if correct else 2)
    draw.rounded_rectangle((x+17,y+36,x+80,y+106),radius=14,
                           fill=GREEN if correct else '#2C5189')
    draw.text((x+34,y+48),chr(65+index),font=_font(34),fill='#082E3F' if correct else YELLOW)
    # Names wrap into at most three measured lines. No ellipsis/truncation.
    words=name.split();size=37
    while size>=23:
        lines=[];line=''
        for word in words:
            candidate=f'{line} {word}'.strip()
            if draw.textbbox((0,0),candidate,font=_font(size))[2] > 324 and line:
                lines.append(line);line=word
            else:line=candidate
        if line:lines.append(line)
        if len(lines)<=3 and all(draw.textbbox((0,0),line,font=_font(size))[2]<=324 for line in lines):break
        size-=1
    if size<23 or len(lines)>3 or any(draw.textbbox((0,0),line,font=_font(size))[2]>324 for line in lines):
        raise ValueError(f'Option cannot fit safely on mobile layout: {name}')
    line_height=size+6
    top=y+(146-len(lines)*line_height)/2
    for line in lines:
        box=draw.textbbox((0,0),line,font=_font(size))
        draw.text((x+101,top-box[1]),line,font=_font(size),fill=WHITE)
        top+=line_height


def _headline(index,count):
    """v1.3.6: a hook on the first flag and a 'final flag' tease on the last, to keep viewers from swiping away."""
    if count>1 and index==0:
        return 'GUESS THE FLAG!',f'Can you get all {count}?'
    if count>1 and index==count-1:
        return 'FINAL FLAG!','Get it right for a perfect score!'
    return 'GUESS THE FLAG!','Which country is this?'


def _question_static(question,index,count,background,reveal=False):
    options,correct,flag_path=_question_data(question)
    image=background.copy();draw=ImageDraw.Draw(image)
    title,subtitle=_headline(index,count)
    _center(draw,title,250,66,YELLOW)
    _center(draw,subtitle,346,40,WHITE)
    draw.rounded_rectangle((130,445,950,945),radius=30,fill='#F4F8FF',outline='#86AEFF',width=4)
    with Image.open(flag_path) as source:
        flag=source.convert('RGBA')
        flag.thumbnail((742,415),Image.Resampling.LANCZOS)
        image.paste(flag,((WIDTH-flag.width)//2,695-flag.height//2),flag)
    draw=ImageDraw.Draw(image)
    _center(draw,f'QUESTION {index+1} / {count}',985,27,MUTED)
    for option_index,name in enumerate(options):
        _option(draw,option_index,name,reveal and option_index==correct)
    _center(draw,'@GeoRushGames',1735,31,MUTED)
    _center(draw,f'{count} flag{"s" if count != 1 else ""}. One challenge.',1790,26,MUTED)
    if reveal:
        _center(draw,'CORRECT ANSWER',1050,30,GREEN)
        _center(draw,f'{chr(65+correct)} · {options[correct]}',1105,48,WHITE,max_width=900)
    return image


def _cta(background,count):
    image=background.copy();draw=ImageDraw.Draw(image)
    _center(draw,'TIME\u2019S UP!',390,86,YELLOW)
    _center(draw,'HOW MANY DID',565,70)
    _center(draw,'YOU GET RIGHT?',657,70)
    _center(draw,f'0/{count}   1/{count}   2/{count}   {count}/{count}' if count==3 else f'SHARE YOUR SCORE: 0\u2013{count}',855,58,YELLOW)
    draw.rounded_rectangle((117,1110,963,1260),radius=34,fill='#FFE451')
    _center(draw,'COMMENT YOUR SCORE',1160,46,'#0B2A60',max_width=790)
    _center(draw,'Follow @GeoRushGames',1405,48)
    _center(draw,'More flags. More fun.',1495,38,MUTED)
    _center(draw,'GeoRush',1740,53,WHITE)
    return image


def animation_state(second, question_count):
    """Shared timing in seconds; effects are local to the current question."""
    index = int((second+1e-8)//QUESTION_SECONDS)
    local = max(0.0, second-index*QUESTION_SECONDS)
    state = {'question_index': index, 'local': local, 'cta': index >= question_count,
             'reveal': local >= COUNTDOWN_SECONDS, 'flag_scale': 1.0,
             'title_offset': 0, 'digit_scale': 1.0, 'answer_scale': 1.0,
             'urgent': COUNTDOWN_SECONDS-2.0 <= local < COUNTDOWN_SECONDS,
             'progress': max(0.0, 1-local/COUNTDOWN_SECONDS)}
    if local < .28:
        state['flag_scale'] = .84+.185*(1-(1-local/.28)**3)
    elif local < .65:
        t=(local-.28)/.37
        state['flag_scale'] = 1.025-.025*(t*t*(3-2*t))
    state['title_offset'] = round(8*(1-min(local/.35,1))**2)
    if local < COUNTDOWN_SECONDS:
        tick = min(COUNTDOWN_TICKS-1, int(local+1e-8))
        phase = max(0, local-tick)
        state['remaining'] = COUNTDOWN_TICKS-tick
        state['digit_scale'] = 1+.13*math.sin(math.pi*min(phase/.18,1))
    else:
        elapsed=local-COUNTDOWN_SECONDS
        state['answer_scale'] = 1+.04*math.sin(math.pi*min(elapsed/.28,1))
    return state


def prepare_animation(questions):
    background = _background()
    boards = [(_question_static(q,i,len(questions),background),
               _question_static(q,i,len(questions),background,True)) for i,q in enumerate(questions)]
    flags=[]
    for question in questions:
        with Image.open(question['flag_path']) as source:
            flag=source.convert('RGBA');flag.thumbnail((742,415),Image.Resampling.LANCZOS)
            flags.append(flag.copy())
    return {'background':background,'boards':boards,'flags':flags,
            'cta':_cta(background,len(questions)),'questions':questions}


def animated_frame(context, second):
    questions=context['questions'];state=animation_state(second,len(questions))
    index=state['question_index'];local=state['local']
    if state['cta']:
        image=context['cta'].copy();draw=ImageDraw.Draw(image)
        elapsed=second-len(questions)*QUESTION_SECONDS
        length=int(700*min(1,elapsed/.45))
        draw.rounded_rectangle((190,1320,190+max(1,length),1327),radius=3,fill=YELLOW)
        return image
    image=context['boards'][index][int(state['reveal'])].copy()
    draw=ImageDraw.Draw(image)
    if not state['reveal']:
        if local < .65:
            # Keep the whole flag visible, including frame zero. No blackout/fade.
            draw.rectangle((151,469,929,921),fill='#F4F8FF')
            flag=context['flags'][index]
            scaled=flag.resize((round(flag.width*state['flag_scale']),round(flag.height*state['flag_scale'])),Image.Resampling.LANCZOS)
            image.paste(scaled,((WIDTH-scaled.width)//2,695-scaled.height//2),scaled)
        if state['title_offset']:
            image.paste(context['background'].crop((80,232,1000,420)),(80,232))
            draw=ImageDraw.Draw(image)
            title,subtitle=_headline(index,len(questions))
            _center(draw,title,250+state['title_offset'],66,YELLOW)
            _center(draw,subtitle,346+state['title_offset'],40,WHITE)
        color='#FFC663' if state['urgent'] else YELLOW
        draw=ImageDraw.Draw(image)
        draw.arc((450,1033,630,1213),-90,270,fill='#34558B',width=9)
        draw.arc((450,1033,630,1213),-90,-90+360*state['progress'],fill=color,width=10)
        size=round(104*state['digit_scale'])
        _center(draw,str(state['remaining']),1061-round((size-104)/2),size,color,max_width=170)
        draw.rounded_rectangle((160,1219,920,1231),radius=6,fill='#34558B')
        end=160+round(760*state['progress'])
        if end>161:draw.rounded_rectangle((160,1219,end,1231),radius=6,fill=color)
    else:
        correct=int(questions[index]['correct_index'])
        x=76+(correct%2)*480;y=1255+(correct//2)*178
        card=context['boards'][index][1].crop((x,y,x+449,y+147))
        width=round(449*state['answer_scale']);height=round(147*state['answer_scale'])
        left=x-(width-449)//2;top=y-(height-147)//2
        image.paste(card.resize((width,height),Image.Resampling.LANCZOS),(left,top))
        draw=ImageDraw.Draw(image)
        draw.rounded_rectangle((left,top,left+width-1,top+height-1),radius=26,
                               outline='#A8FFE0' if local-COUNTDOWN_SECONDS<.35 else GREEN,width=6)
    if index>0 and local<.16:
        draw.rectangle((0,214,int(WIDTH*(local/.16)),222),fill=YELLOW)
    return image


def render_video(quiz, destination, bgm_volume=.10, progress_callback=None, ffmpeg_path=None):
    """Create a local video atomically. Failed temporary output is never promoted."""
    started=time.monotonic();destination=Path(destination)
    questions=quiz['questions'];count=len(questions)
    if not 1<=count<=5:raise ValueError('Question count must be between 1 and 5')
    destination.parent.mkdir(parents=True,exist_ok=True)
    if ffmpeg_path is None:
        try:
            from .paths import find_ffmpeg
            ffmpeg_path=find_ffmpeg()
        except ImportError:
            ffmpeg_path=shutil.which('ffmpeg')
    if not ffmpeg_path:raise FileNotFoundError('FFmpeg is not installed or bundled')
    audio_path=destination.parent/'original_audio.wav'
    audio_report=synthesize_audio(audio_path,count,bgm_volume)
    animation=prepare_animation(questions)
    inspection=destination.parent/'inspection';inspection.mkdir(exist_ok=True)
    duration=count*QUESTION_SECONDS+CTA_SECONDS
    frames=round(duration*FPS)
    temporary=destination.with_name(destination.stem+'.partial.mp4')
    log_path=destination.parent/'ffmpeg.log'
    args=[str(ffmpeg_path),'-hide_banner','-y','-f','rawvideo','-pix_fmt','rgb24',
          '-s',f'{WIDTH}x{HEIGHT}','-r',str(FPS),'-i','pipe:0','-i',str(audio_path),
          '-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','20',
          '-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000',
          '-t',str(duration),'-movflags','+faststart',str(temporary)]
    process=None
    inspections=[]
    try:
        with log_path.open('wb') as error_log:
            process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=error_log,
                                     **subprocess_options())
            for number in range(frames):
                second=number/FPS
                question_index=int(second//QUESTION_SECONDS)
                local=second-question_index*QUESTION_SECONDS
                image=animated_frame(animation,second)
                if (number%round(QUESTION_SECONDS*FPS)==0 or
                    number%round(QUESTION_SECONDS*FPS)==round(2.0*FPS) or
                    number%round(QUESTION_SECONDS*FPS)==round(COUNTDOWN_SECONDS*FPS)) and question_index<count:
                    label='start' if local<.01 else 'countdown' if local<COUNTDOWN_SECONDS else 'answer'
                    name=f'question_{question_index+1:02d}_{label}.jpg'
                    image.save(inspection/name,quality=92)
                    inspections.append({'file':name,'time_seconds':second,'frame':number})
                if number==count*round(QUESTION_SECONDS*FPS):
                    image.save(inspection/'cta.jpg',quality=92)
                    inspections.append({'file':'cta.jpg','time_seconds':second,'frame':number})
                try:process.stdin.write(image.tobytes())
                except BrokenPipeError as exc:
                    raise RuntimeError(f'FFmpeg stopped while encoding. See {log_path}') from exc
                if progress_callback and (number%15==0 or number==frames-1):
                    progress_callback({'stage':'render','progress':(number+1)/frames,
                                       'message':f'프레임 {number+1}/{frames}'})
            process.stdin.close()
            code=process.wait(timeout=120)
        if code!=0:
            details=log_path.read_text(encoding='utf-8',errors='replace')[-2500:]
            raise RuntimeError(f'FFmpeg failed ({code}): {details}')
        if not temporary.is_file() or temporary.stat().st_size<1000:
            raise RuntimeError('FFmpeg produced no usable video')
        temporary.replace(destination)
    except BaseException:
        if process is not None:
            if process.poll() is None:
                process.kill();process.wait(timeout=15)
            if process.stdin and not process.stdin.closed:process.stdin.close()
        temporary.unlink(missing_ok=True)
        raise
    report={'width':WIDTH,'height':HEIGHT,'fps':FPS,'duration':duration,'frames':frames,
            'native_resolution':[WIDTH,HEIGHT],'upscaled':False,'encoder':'libx264',
            'audio_codec':'aac','audio':audio_report,'elapsed_seconds':round(time.monotonic()-started,3),
            'inspection':inspections,
            'layout_safety':{'horizontal_margin':51,'minimum_option_font':23,'option_count':4,
                             'flag_aspect_preserved':True,'no_text_truncation':True},
            'ffmpeg_log':log_path.name}
    report['presentation']={'version':'1.2','intro_seconds':.65,'first_flag_scale':.84,
                            'countdown_seconds':COUNTDOWN_SECONDS,'answer_hold_seconds':QUESTION_SECONDS-COUNTDOWN_SECONDS,
                            'digit_pulse_seconds':.18,'answer_pulse_seconds':.28,'global_flashes':False,'camera_shake':False}
    (destination.parent/'render_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
