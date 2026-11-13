"""Native 1080x1920 Pillow animation streamed into local FFmpeg."""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
import json
import math
import random
import shutil
import subprocess
import time

from PIL import Image, ImageDraw, ImageFont

from .audio import synthesize_audio, QUESTION_SECONDS, COUNTDOWN_SECONDS, COUNTDOWN_TICKS, CTA_SECONDS
from .names import display_name
from .themes import ZOOM_START
from .paths import resource_root, subprocess_options

WIDTH, HEIGHT, FPS = 1080, 1920, 30
YELLOW = '#FFE451'
WHITE = '#F5FAFF'
MUTED = '#B8D2FF'
GREEN = '#5DFFC2'
TITLE_SIZE = 74      # v1.3.7: larger first-screen question (was 66 / 40) so it reads at phone size
FLAG_POP_SECONDS = .35
HEADLINE_WIDTH = 900  # stays inside the 80-1000 px band that the title animation repaints
HEADLINE_Y = 216
FLAG_CARD = (40,298,1040,1024)  # v1.4.2: the flag fills the width of the screen (was a 553 px wide flag)
FLAG_MAX = (900,675)
FLAG_CENTER_Y = 661
OPTION_SIZE = 44      # v1.4.1: answer choices read at phone size (was 37); long names still wrap and shrink
OPTION_TEXT_HEIGHT = 138  # lines of a choice stay inside its 146 px card
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
    capital=question.get('kind')=='capital'
    if names[correct] != (question.get('answer_name') if capital else question['country_name']):
        raise ValueError('Correct answer does not match the question country')
    flag_path=Path(question['flag_path'])
    if not flag_path.is_file():
        raise FileNotFoundError(f'Flag image missing: {flag_path}')
    if capital:  # v1.4.0: capital-city options are shown as they are
        return names,correct,flag_path
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
    # Names wrap into at most three measured lines that also fit the card height. No ellipsis/truncation.
    words=name.split();size=OPTION_SIZE
    while size>=23:
        lines=[];line=''
        for word in words:
            candidate=f'{line} {word}'.strip()
            if draw.textbbox((0,0),candidate,font=_font(size))[2] > 324 and line:
                lines.append(line);line=word
            else:line=candidate
        if line:lines.append(line)
        if (len(lines)<=3 and len(lines)*(size+6)<=OPTION_TEXT_HEIGHT
                and all(draw.textbbox((0,0),line,font=_font(size))[2]<=324 for line in lines)):break
        size-=1
    if size<23 or len(lines)>3 or any(draw.textbbox((0,0),line,font=_font(size))[2]>324 for line in lines):
        raise ValueError(f'Option cannot fit safely on mobile layout: {name}')
    line_height=size+6
    top=y+(146-len(lines)*line_height)/2
    for line in lines:
        box=draw.textbbox((0,0),line,font=_font(size))
        draw.text((x+101,top-box[1]),line,font=_font(size),fill=WHITE)
        top+=line_height


# v1.6.0 Find: four flags in a 2x2 grid inside the flag card; the bottom cards only carry the letters.
FIND_CELLS = [(60+(i%2)*490, 318+(i//2)*353, 60+(i%2)*490+470, 318+(i//2)*353+333) for i in range(4)]
FIND_FLAG_MAX = (420,250)


def _find_grid(image, question, correct=None):
    """Find and Population grids. Population cards also show each country's people at the reveal."""
    draw=ImageDraw.Draw(image)
    for i,(x0,y0,x1,y1) in enumerate(FIND_CELLS):
        draw.rounded_rectangle((x0,y0,x1,y1),radius=22,fill='#FFFFFF',outline='#86AEFF',width=3)
        with Image.open(question['option_flag_paths'][i]) as source:
            flag=source.convert('RGBA')
        flag.thumbnail(FIND_FLAG_MAX,Image.Resampling.LANCZOS)
        cx=(x0+x1)//2;cy=(y0+y1)//2+14
        image.paste(flag,(cx-flag.width//2,cy-flag.height//2),flag)
        draw=ImageDraw.Draw(image)
        if correct is not None and i!=correct:  # the wrong flags fade out at the reveal
            shade=Image.new('RGBA',(x1-x0-6,y1-y0-6),(10,30,70,170))
            image.paste(shade,(x0+3,y0+3),shade);draw=ImageDraw.Draw(image)
        if correct is not None and i==correct:
            draw.rounded_rectangle((x0-4,y0-4,x1+4,y1+4),radius=26,outline=GREEN,width=10)
        draw.ellipse((x0+12,y0+12,x0+72,y0+72),fill=GREEN if correct==i else '#12356B')
        _center(draw,chr(65+i),y0+24,36,'#082E3F' if correct==i else YELLOW,x=x0+42)
        if correct is not None and question.get('kind')=='population':
            from .population import short_number
            label=short_number(question['populations'][i])
            draw.rounded_rectangle((x1-190,y1-70,x1-12,y1-12),radius=16,fill=GREEN if i==correct else '#0B2A60')
            _center(draw,label,y1-60,38,'#082E3F' if i==correct else WHITE,max_width=160,x=x1-101)


def _headline(index,count,question=None,hook=None):
    """v1.4.2: one short challenge line, so the flag is what a viewer sees first in the feed.
    A capital-city question names the country (its flag is on screen) and asks for its capital."""
    if question is not None and question.get('kind')=='capital':
        return f'CAPITAL OF {display_name(question["country_name"]).upper()}?'
    if question is not None and question.get('kind')=='population':
        return 'WHICH HAS THE MOST PEOPLE?' if index==0 else 'MOST PEOPLE?'
    if question is not None and question.get('kind')=='find':
        return f'FIND {display_name(question["country_name"]).upper()}!'
    if question is not None and question.get('kind')=='zoom' and not (count>1 and index==count-1):
        return 'ZOOMED IN! WHICH FLAG?'
    if count>1 and index==0:
        return hook or f'CAN YOU GET ALL {count}?'  # v1.6.4: rotating challenge hook (hooks.py)
    if count>1 and index==count-1:
        return 'FINAL FLAG!'
    return 'GUESS THE FLAG!'


def _question_static(question,index,count,background,reveal=False,hook=None):
    options,correct,flag_path=_question_data(question)
    image=background.copy();draw=ImageDraw.Draw(image)
    _center(draw,_headline(index,count,question,hook),HEADLINE_Y,TITLE_SIZE,YELLOW,max_width=HEADLINE_WIDTH)
    find=question.get('kind') in ('find','population')
    names_shown=question.get('kind')=='population'
    draw.rounded_rectangle(FLAG_CARD,radius=30,fill='#16457F' if find else '#F4F8FF',outline='#86AEFF',width=4)
    if find:
        _find_grid(image,question,correct if reveal else None)
    else:
        with Image.open(flag_path) as source:
            flag=source.convert('RGBA')
            flag.thumbnail(FLAG_MAX,Image.Resampling.LANCZOS)
            image.paste(flag,((WIDTH-flag.width)//2,FLAG_CENTER_Y-flag.height//2),flag)
    draw=ImageDraw.Draw(image)
    _center(draw,f'QUESTION {index+1} / {count}',122,27,MUTED,x=578)  # in the header, between the logo and FLAG QUIZ
    for option_index,name in enumerate(options):
        if find and not names_shown:  # the letters only: a name on a card would give the flag away
            name=options[correct] if reveal and option_index==correct else f'FLAG {chr(65+option_index)}'
        _option(draw,option_index,name,reveal and option_index==correct)
    if reveal and index==count-1:
        # v1.6.1: the score ask sits on the last answer, so the Short can loop without a closing screen.
        draw.rounded_rectangle((117,1620,963,1820),radius=34,fill=YELLOW)
        _center(draw,'COMMENT YOUR SCORE + COUNTRY!',1652,42,'#0B2A60',max_width=790)
        _center(draw,'LIKE & SUBSCRIBE FOR MORE!',1732,40,'#0B2A60',max_width=790)
    elif names_shown:
        from .population import SOURCE_LINE
        _center(draw,'@GeoRushGames',1735,31,MUTED)
        _center(draw,SOURCE_LINE,1790,26,MUTED)
    else:
        _center(draw,'@GeoRushGames',1735,31,MUTED)
        noun='capital' if question.get('kind')=='capital' else 'round' if find else 'flag'
        _center(draw,f'{count} {noun}{"s" if count != 1 else ""}. One challenge.',1790,26,MUTED)
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
    draw.rounded_rectangle((117,1090,963,1290),radius=34,fill='#FFE451')
    _center(draw,'COMMENT YOUR SCORE',1122,46,'#0B2A60',max_width=790)
    _center(draw,'+ WHERE YOU’RE FROM!',1202,40,'#0B2A60',max_width=790)  # v1.6.0: home-country replies
    _center(draw,'Follow @GeoRushGames',1405,48)
    _center(draw,'More flags. More fun.',1495,38,MUTED)
    _center(draw,'GeoRush',1740,53,WHITE)
    return image


def animation_state(second, question_count):
    """Shared timing in seconds; effects are local to the current question."""
    index = int((second+1e-8)//QUESTION_SECONDS)
    if index >= question_count and second < question_count*QUESTION_SECONDS+CTA_SECONDS:
        index = question_count-1  # v1.6.2: the last answer is held for CTA_SECONDS (spoken comment/subscribe ask)
    local = max(0.0, second-index*QUESTION_SECONDS)
    state = {'question_index': index, 'local': local, 'cta': index >= question_count,
             'reveal': local >= COUNTDOWN_SECONDS, 'flag_scale': 1.0,
             'title_offset': 0, 'digit_scale': 1.0, 'answer_scale': 1.0,
             'urgent': COUNTDOWN_SECONDS-1.0 <= local < COUNTDOWN_SECONDS,
             'progress': max(0.0, 1-local/COUNTDOWN_SECONDS)}
    if local < FLAG_POP_SECONDS:
        # v1.3.7: the flag is full size on the very first frame (it used to start at 84%) and gives a short pop.
        state['flag_scale'] = 1+.06*math.sin(math.pi*local/FLAG_POP_SECONDS)
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
    from .hooks import choose
    hook = choose(questions)[0]
    boards = [(_question_static(q,i,len(questions),background,hook=hook),
               _question_static(q,i,len(questions),background,True,hook=hook)) for i,q in enumerate(questions)]
    flags=[];sources=[]
    for question in questions:
        with Image.open(question['flag_path']) as source:
            full=source.convert('RGBA')
            flag=full.copy();flag.thumbnail(FLAG_MAX,Image.Resampling.LANCZOS)
            flags.append(flag)
            sources.append(full if question.get('kind')=='zoom' else None)
    return {'background':background,'boards':boards,'flags':flags,'sources':sources,
            'cta':_cta(background,len(questions)),'questions':questions,'hook':hook}


CONFETTI_SECONDS = 1.0
CONFETTI_COLORS = ('#FFE451', '#FF7AA8', '#7FC8FF', '#FFB265', '#FFFFFF')  # never green: green marks the answer


def _confetti(draw, index, x, y, elapsed):
    """v1.5.0: a short, deterministic burst from the correct card when the answer is revealed."""
    if not 0 <= elapsed < CONFETTI_SECONDS:
        return
    rng = random.Random(1000+index)
    for piece in range(36):
        angle = rng.uniform(math.pi*1.1, math.pi*1.9)
        speed = rng.uniform(420, 820)
        px = x+math.cos(angle)*speed*elapsed
        py = y+math.sin(angle)*speed*elapsed+900*elapsed*elapsed
        size = rng.choice((8, 10, 12))
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            draw.rectangle((px, py, px+size, py+size*.6), fill=CONFETTI_COLORS[piece % len(CONFETTI_COLORS)])


def _zoomed(source, size, center, local):
    """v1.5.0 Zoom: a crop around center that widens from ZOOM_START to the whole flag by the end of the countdown."""
    progress = min(max(local/COUNTDOWN_SECONDS, 0), 1)
    fraction = ZOOM_START+(1-ZOOM_START)*progress**1.6
    w, h = source.size[0]*fraction, source.size[1]*fraction
    cx = min(max(center[0]*source.size[0], w/2), source.size[0]-w/2)
    cy = min(max(center[1]*source.size[1], h/2), source.size[1]-h/2)
    crop = source.crop((round(cx-w/2), round(cy-h/2), round(cx+w/2), round(cy+h/2)))
    return crop.resize(size, Image.Resampling.LANCZOS)


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
        if questions[index].get('kind')=='zoom':
            draw.rectangle((FLAG_CARD[0]+4,FLAG_CARD[1]+4,FLAG_CARD[2]-4,FLAG_CARD[3]-4),fill='#F4F8FF')
            flag=_zoomed(context['sources'][index],context['flags'][index].size,questions[index]['zoom_center'],local)
            image.paste(flag,((WIDTH-flag.width)//2,FLAG_CENTER_Y-flag.height//2),flag)
        elif local < FLAG_POP_SECONDS and questions[index].get('kind') not in ('find','population'):
            # Keep the whole flag visible, including frame zero. No blackout/fade.
            draw.rectangle((FLAG_CARD[0]+4,FLAG_CARD[1]+4,FLAG_CARD[2]-4,FLAG_CARD[3]-4),fill='#F4F8FF')
            flag=context['flags'][index]
            scaled=flag.resize((round(flag.width*state['flag_scale']),round(flag.height*state['flag_scale'])),Image.Resampling.LANCZOS)
            image.paste(scaled,((WIDTH-scaled.width)//2,FLAG_CENTER_Y-scaled.height//2),scaled)
        if state['title_offset']:
            image.paste(context['background'].crop((80,HEADLINE_Y-8,1000,FLAG_CARD[1]-2)),(80,HEADLINE_Y-8))
            draw=ImageDraw.Draw(image)
            _center(draw,_headline(index,len(questions),questions[index],context.get('hook')),HEADLINE_Y+state['title_offset'],TITLE_SIZE,YELLOW,max_width=HEADLINE_WIDTH)
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
        _confetti(draw,index,x+224,y+73,local-COUNTDOWN_SECONDS)
    if index>0 and local<.16:
        draw.rectangle((0,214,int(WIDTH*(local/.16)),222),fill=YELLOW)
    return image


def render_video(quiz, destination, bgm_volume=.10, progress_callback=None, ffmpeg_path=None):
    """Create a local video atomically. Failed temporary output is never promoted."""
    started=time.monotonic();destination=Path(destination)
    questions=quiz['questions'];count=len(questions)
    if not 1<=count<=10:raise ValueError('Question count must be between 1 and 10')
    destination.parent.mkdir(parents=True,exist_ok=True)
    if ffmpeg_path is None:
        try:
            from .paths import find_ffmpeg
            ffmpeg_path=find_ffmpeg()
        except ImportError:
            ffmpeg_path=shutil.which('ffmpeg')
    if not ffmpeg_path:raise FileNotFoundError('FFmpeg is not installed or bundled')
    audio_path=destination.parent/'original_audio.wav'
    audio_report=synthesize_audio(audio_path,count,bgm_volume,questions)
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
    report['presentation']={'version':'1.2','intro_seconds':FLAG_POP_SECONDS,'first_flag_scale':1.0,
                            'countdown_seconds':COUNTDOWN_SECONDS,'answer_hold_seconds':QUESTION_SECONDS-COUNTDOWN_SECONDS,
                            'digit_pulse_seconds':.18,'answer_pulse_seconds':.28,'global_flashes':False,'camera_shake':False}
    (destination.parent/'render_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
