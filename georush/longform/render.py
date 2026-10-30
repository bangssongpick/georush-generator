"""Native landscape layout. Encode bounded image holds, never a full movie in RAM."""
from functools import lru_cache
from pathlib import Path
import json
import math
import shutil
import subprocess
import time
from PIL import Image,ImageDraw
from ..render import _font, WHITE, YELLOW, GREEN
from ..names import display_name
from ..paths import subprocess_options
from .timeline import FPS,COUNTDOWN
from .audio import synthesize

WIDTH,HEIGHT=1920,1080
ACCENTS={'Easy':'#FFE451','Normal':'#59D5FF','Hard':'#FFB265','Expert':'#D3B0FF'}
OPTION_BOXES=[(90,700,940,802),(980,700,1830,802),(90,824,940,926),(980,824,1830,926)]


def text(draw,value,box,size=42,fill=WHITE,minimum=24):
    """Measured wrapping: fail rather than crop or replace country names with ellipsis."""
    x,y,w,h=box
    for current in range(size,minimum-1,-1):
        lines=[];line=''
        for word in value.split():
            candidate=(line+' '+word).strip()
            if draw.textbbox((0,0),candidate,font=_font(current))[2]>w and line:
                lines.append(line);line=word
            else:line=candidate
        if line:lines.append(line)
        if len(lines)*(current+8)<=h and all(draw.textbbox((0,0),s,font=_font(current))[2]<=w for s in lines):
            top=y+(h-len(lines)*(current+8))/2
            for line in lines:
                bounds=draw.textbbox((0,0),line,font=_font(current))
                draw.text((x+(w-(bounds[2]-bounds[0]))/2,top-bounds[1]),line,font=_font(current),fill=fill)
                top+=current+8
            return current
    raise ValueError('롱폼 글자가 안전영역에 들어가지 않습니다: '+value)


@lru_cache(maxsize=1)
def background():
    import numpy as np
    alpha=np.linspace(0,1,HEIGHT)[:,None,None]
    pixels=np.tile(((1-alpha)*np.array([10,45,110])+alpha*np.array([4,19,54])).astype('uint8'),(1,WIDTH,1))
    image=Image.fromarray(pixels,'RGB');d=ImageDraw.Draw(image)
    d.arc((-300,-420,2200,1800),190,350,fill='#174B86',width=3)
    d.rounded_rectangle((60,35,1860,125),radius=25,fill='#103B80',outline='#2861A7',width=2)
    text(d,'GeoRush',(90,44,300,68),50)
    text(d,'@GeoRushGames',(690,995,540,45),26,'#B8D2FF')
    return image


def option(image,index,name,correct=False,scale=1.):
    x1,y1,x2,y2=OPTION_BOXES[index]
    card=Image.new('RGB',(x2-x1,y2-y1),'#0A2050');d=ImageDraw.Draw(card)
    d.rounded_rectangle((0,0,card.width-1,card.height-1),radius=20,
                       fill='#0F584F' if correct else '#12356B',outline=GREEN if correct else '#5078B4',width=5 if correct else 2)
    text(d,chr(65+index),(15,12,65,76),40,YELLOW if not correct else GREEN)
    text(d,name,(100,8,card.width-125,86),38)
    if scale!=1:
        card=card.resize((round(card.width*scale),round(card.height*scale)),Image.Resampling.LANCZOS)
    image.paste(card,(round((x1+x2-card.width)/2),round((y1+y2-card.height)/2)))


def question_context(q,index,count):
    image=background().copy();d=ImageDraw.Draw(image)
    accent=ACCENTS[q['longform_tier']]
    text(d,q['longform_tier'].upper(),(650,48,620,58),34,accent)
    text(d,f'QUESTION {index+1:02d} / {count}',(1420,50,400,55),32)
    text(d,'Which country is this?',(360,145,1200,80),54,YELLOW)
    d.rounded_rectangle((470,245,1450,655),radius=25,fill='#F4F8FF',outline='#86AEFF',width=3)
    with Image.open(q['flag_path']) as source:
        flag=source.convert('RGB');flag.thumbnail((870,350),Image.Resampling.LANCZOS)
    for i,name in enumerate(q['options']):option(image,i,display_name(name))
    return {'base':image,'flag':flag,'question':q,'index':index,'count':count}


def question_frame(context,frame):
    t=frame/FPS;q=context['question'];image=context['base'].copy();d=ImageDraw.Draw(image)
    flag=context['flag'];scale=.86+.14*(1-(1-min(t/.45,1))**3)
    flag=flag.resize((round(flag.width*scale),round(flag.height*scale)),Image.Resampling.LANCZOS)
    image.paste(flag,((WIDTH-flag.width)//2,450-flag.height//2))
    if t<COUNTDOWN:
        remain=COUNTDOWN-int(t)
        phase=t%1;pulse=1+.12*max(0,1-phase/.16)
        color=YELLOW if remain>2 else '#FFB265'
        d.ellipse((1645,325,1815,495),fill='#0A2050',outline=color,width=5)
        text(d,str(remain),(1650,335,160,145),round(92*pulse),color)
        text(d,'SECONDS',(1620,510,220,50),26,color)
        d.rounded_rectangle((90,960,1830,978),radius=8,fill='#234574')
        remaining=round(1740*max(0,1-t/COUNTDOWN))
        if remaining>0:d.rounded_rectangle((90,960,90+remaining,978),radius=8,fill=color)
    else:
        pulse=1+.025*math.sin(math.pi*min((t-COUNTDOWN)/.3,1))
        shown=display_name(q['country_name'])
        option(image,q['correct_index'],shown,True,pulse)
        d=ImageDraw.Draw(image)
        text(d,'CORRECT!',(1510,370,350,95),50,GREEN)
        text(d,f'{chr(65+q["correct_index"])}: {shown}',(1455,478,405,160),35,WHITE)
    return image


def screen(item,count):
    image=background().copy();d=ImageDraw.Draw(image)
    kind=item['kind']
    if kind=='intro':
        lines=[('GUESS '+str(count)+' FLAGS!',330,90,YELLOW),('EASY TO EXPERT',480,52,WHITE),
               (f'CAN YOU GET {count}/{count}?',595,52,WHITE),('8 seconds to choose. Then reveal!',735,32,'#B8D2FF')]
    elif kind=='chapter':
        lines=[(item['tier'].upper(),360,100,ACCENTS[item['tier']]),('NEXT ROUND',540,48,WHITE),
               ('New flags. Same 8-second timer.',680,34,'#B8D2FF')]
    else:
        lines=[("WHAT'S YOUR SCORE?",300,78,YELLOW),(f'COMMENT YOUR RESULT: __ / {count}',445,54,WHITE),
               ('SUBSCRIBE FOR MORE',620,48,WHITE),('GEOGRAPHY CHALLENGES!',700,48,YELLOW)]
    for value,y,size,color in lines:text(d,value,(120,y,1680,120),size,color)
    return image


def encode_segment(images,destination,duration,ffmpeg,log):
    """PNG concat timebase is explicitly 30fps: frame-accurate holds on Windows too."""
    lines=['ffconcat version 1.0']
    for path,frames in images:
        lines+=['file '+path.relative_to(destination.parent).as_posix(),'option framerate 30',f'duration {frames/FPS:.12f}']
    lines+=['file '+images[-1][0].relative_to(destination.parent).as_posix(),'option framerate 30']
    listing=destination.parent/'frames.ffconcat';listing.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    command=[str(ffmpeg),'-hide_banner','-v','error','-y','-threads','2','-f','concat','-safe','0','-i',str(listing),
             '-vf','fps=30,format=yuv420p','-frames:v',str(duration*FPS),'-an','-c:v','libx264','-preset','veryfast',
             '-crf','20','-threads','2','-filter_threads','1',str(destination)]
    with log.open('ab') as stream:
        try:
            subprocess.run(command,stdout=stream,stderr=stream,check=True,timeout=180,**subprocess_options())
        except subprocess.CalledProcessError as exc:
            stream.flush()
            raise RuntimeError('롱폼 FFmpeg 오류: '+log.read_text(encoding='utf-8',errors='replace')[-1200:]) from exc


def render(quiz,timeline,work,ffmpeg,bgm,progress=None):
    started=time.monotonic();work=Path(work);log=work/'ffmpeg.log'
    audio=synthesize(work/'original_audio.wav',timeline,bgm)
    segments=[]
    for si,item in enumerate(timeline['segments']):
        scratch=work/'frames';scratch.mkdir(exist_ok=True)
        encoded=work/f'segment_{si:03d}.mp4'
        images=[]
        if item['kind']=='question':
            context=question_context(quiz['questions'][item['question_index']],item['question_index'],len(quiz['questions']))
            # Short animations at native 30fps; stable states use exact-duration image holds.
            def key(f):
                if f<14 or f<COUNTDOWN*FPS and f%30<5 or COUNTDOWN*FPS<=f<COUNTDOWN*FPS+10:
                    return ('animated',f)
                if f<COUNTDOWN*FPS:
                    return ('hold',f//30)
                return ('answer',)
            start=0;previous=key(0)
            for f in range(1,item['duration']*FPS+1):
                current=key(f) if f<item['duration']*FPS else None
                if current!=previous:
                    path=scratch/f'f{start:04d}.png'
                    question_frame(context,start).save(path,compress_level=1)
                    images.append((path,f-start));start=f;previous=current
        else:
            path=scratch/'screen.png';screen(item,len(quiz['questions'])).save(path,compress_level=1)
            images=[(path,item['duration']*FPS)]
        encode_segment(images,encoded,item['duration'],ffmpeg,log)
        segments.append(encoded)
        shutil.rmtree(scratch)
        if progress:progress((si+1)/len(timeline['segments'])*.95,f'롱폼 장면 {si+1}/{len(timeline["segments"])} 렌더 완료')
    listing=work/'segments.ffconcat'
    listing.write_text('ffconcat version 1.0\n'+''.join('file '+p.name+'\n' for p in segments),encoding='utf-8')
    with log.open('ab') as stream:
        subprocess.run([str(ffmpeg),'-hide_banner','-v','error','-y','-f','concat','-safe','0','-i',str(listing),
                        '-i',str(work/'original_audio.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac',
                        '-b:a','192k','-t',str(timeline['duration']),'-movflags','+faststart',str(work/'longform.mp4')],
                       stdout=stream,stderr=stream,check=True,timeout=180,**subprocess_options())
    for path in segments:path.unlink()
    return {'width':WIDTH,'height':HEIGHT,'fps':FPS,'duration':timeline['duration'],'frames':timeline['frames'],
            'upscaled':False,'audio':audio,'elapsed_seconds':round(time.monotonic()-started,3),
            'bounded_memory':'one question, keyframe PNGs and 1-second PCM chunks','countdown':COUNTDOWN,
            'answer_seconds':2,'maximum_flag_size':[870,350],'layout':'native landscape, two by two options'}
