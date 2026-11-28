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

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .audio import synthesize_audio, timing, QUESTION_SECONDS, COUNTDOWN_SECONDS, COUNTDOWN_TICKS, CTA_SECONDS
from .names import display_name
from .themes import ZOOM_START
from .paths import resource_root, subprocess_options

WIDTH, HEIGHT, FPS = 1080, 1920, 30
YELLOW = '#FFE451'
WHITE = '#F5FAFF'
MUTED = '#B8D2FF'
GREEN = '#5DFFC2'
TITLE_SIZE = 84      # v1.6.5: the headline sits in the big yellow banner of the approved design (was 74 on the plain background)
FLAG_POP_SECONDS = .35
HEADLINE_WIDTH = 900  # the banner is 960 px wide; the italic lean needs the rest
SHEAR = .2            # italic lean of the banner and badge text
BANNER = (60,326,1020,456)   # v1.6.5 design: glowing yellow banner under the globe logo
BADGE = (270,444,810,512)    # red badge on the banner's lower edge: "ONLY 1 IS RIGHT!", "ROUND 2 / 3", "FINAL ROUND!"
# Shorts draws its own buttons over the right edge (x > 930, y 1000-1650) and its caption over the bottom (y > 1600):
# everything the viewer has to read stays left of x=930 in the lower half and above y=1580.
FLAG_CARD = (40,534,1040,1180)  # single-flag card (the flag is 787 px wide, 73% of the screen; it was 83% before the logo took the top)
FLAG_MAX = (860,590)
FLAG_CENTER_Y = 857
FIND_CARD = (40,534,1040,1244)  # Find: the 2x2 grid takes the room the answer cards used to use
OPTION_SIZE = 44      # v1.4.1: answer choices read at phone size (was 37); long names still wrap and shrink
OPTION_TEXT_HEIGHT = 96  # lines of a choice stay inside its 104 px card
OPTION_W, OPTION_H = 430, 104
OPTION_X = (40,500)   # v1.6.5: right edge 930, clear of the Shorts buttons (was 1004)
OPTION_Y = (1350,1468)
OPTION_TEXT_WIDTH = 316
REVEAL_FX_SECONDS = .3  # v1.6.5: a short flash and pop on the right answer (local, never full screen)
# Where the countdown, the answer label and the last-answer banner sit for each kind of question.
LAYOUTS = {
    'find': {'ring':(465,1262,615,1412),'bar_y':1428,'label_y':1254,'name_y':1290,'name_size':44,'info_y':1342,
             'last_box':(117,1380,963,1560),'last_lines':(1412,1494),'last_label':True},
    'std': {'ring':(480,1190,600,1310),'bar_y':1322,'label_y':1196,'name_y':1240,'name_size':48,'info_y':1296,
            'last_box':(117,1190,963,1335),'last_lines':(1208,1268),'last_label':False},
}
ASSETS = resource_root()/'assets'


@lru_cache(maxsize=64)
def _font(size):
    path = ASSETS/'fonts'/'DejaVuSans-Bold.ttf'
    if not path.is_file():
        raise FileNotFoundError(f'Bundled font missing: {path}')
    return ImageFont.truetype(str(path),size)


def _center(draw, text, y, size, fill=WHITE, max_width=940, x=WIDTH//2, stroke=0):
    size = int(size)
    while size > 20 and draw.textbbox((0,0),text,font=_font(size))[2] > max_width:
        size -= 1
    box = draw.textbbox((0,0),text,font=_font(size))
    extra = {'stroke_width':stroke,'stroke_fill':fill} if stroke else {}
    draw.text((x-(box[2]-box[0])/2,y-box[1]),text,font=_font(size),fill=fill,**extra)
    return size


def _italic_center(image, text, cy, size, fill, max_width, stroke=0):
    """Heavy italic text centred on cy: drawn upright on a full-frame layer, then leaned by SHEAR around its own middle."""
    layer = Image.new('RGBA',image.size,(0,0,0,0));draw = ImageDraw.Draw(layer)
    size = int(size)
    while size > 20 and draw.textbbox((0,0),text,font=_font(size))[2]+SHEAR*size > max_width:
        size -= 1
    box = draw.textbbox((0,0),text,font=_font(size))
    _center(draw,text,cy-(box[3]-box[1])/2,size,fill,max_width=10**6,stroke=stroke)
    layer = layer.transform(layer.size,Image.Transform.AFFINE,(1,SHEAR,-SHEAR*cy,0,1,0),resample=Image.Resampling.BICUBIC)
    image.paste(layer,(0,0),layer)
    return size


@lru_cache(maxsize=1)
def _plate():
    path = ASSETS/'bg_v165.jpg'
    if not path.is_file():
        raise FileNotFoundError(f'Background plate missing: {path}')
    return Image.open(path).convert('RGB')


def _background():
    """v1.6.5: the approved design's globe logo, world maps and plane on top, a navy gradient, the grid floor at the bottom."""
    return _plate().copy()


def _glow(image, box, radius, color, blur=14, grow=6, alpha=180):
    """A soft neon halo behind a rounded box."""
    x0,y0,x1,y1 = box;pad = blur*3+grow
    layer = Image.new('RGBA',(x1-x0+2*pad,y1-y0+2*pad),(0,0,0,0))
    ImageDraw.Draw(layer).rounded_rectangle((pad-grow,pad-grow,pad+x1-x0+grow,pad+y1-y0+grow),radius=radius+grow,fill=color+(alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    image.paste(layer,(x0-pad,y0-pad),layer)


def _gradient_box(image, box, top, bottom, radius, outline=None, width=0):
    x0,y0,x1,y1 = box;w,h = x1-x0,y1-y0
    colour = Image.composite(Image.new('RGB',(w,h),bottom),Image.new('RGB',(w,h),top),Image.linear_gradient('L').resize((w,h)))
    mask = Image.new('L',(w,h),0);ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=radius,fill=255)
    image.paste(colour,(x0,y0),mask)
    if outline:
        ImageDraw.Draw(image).rounded_rectangle(box,radius=radius,outline=outline,width=width)


def _banner(image, headline, sub):
    """v1.6.5: the approved banner design with swappable text: yellow headline banner and red badge under the logo."""
    _glow(image,BANNER,34,(255,64,64),blur=16,grow=4,alpha=200)
    _gradient_box(image,BANNER,(255,238,96),(255,196,26),34,outline='#FF4A3D',width=6)
    draw = ImageDraw.Draw(image)
    for sign in (-1,1):  # the two small flares beside the banner
        x = BANNER[0]-26 if sign<0 else BANNER[2]+26
        for dy,tilt in ((378,26),(420,4)):
            draw.line((x-sign*22,dy-tilt,x+sign*22,dy+tilt),fill='#FFE14A',width=9)
    _italic_center(image,headline,(BANNER[1]+BANNER[3])//2-4,TITLE_SIZE,'#0E0E12',HEADLINE_WIDTH,stroke=2)
    _glow(image,BADGE,30,(255,40,60),blur=12,grow=3,alpha=210)
    _gradient_box(image,BADGE,(255,96,96),(204,16,30),30,outline='#FF9A90',width=3)
    _italic_center(image,sub,(BADGE[1]+BADGE[3])//2,48,'#FFFFFF',BADGE[2]-BADGE[0]-70,stroke=1)


def _card(image, box):
    """The white card with the blue neon rim that holds the flag or the four flags."""
    _glow(image,box,40,(46,134,255),blur=18,grow=8,alpha=210)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box,radius=38,fill='#F7FAFF',outline='#2E86FF',width=7)
    draw.rounded_rectangle((box[0]+10,box[1]+10,box[2]-10,box[3]-10),radius=30,outline='#D3E3FF',width=3)


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


def _option_box(index):
    return OPTION_X[index%2],OPTION_Y[index//2]


def _option(draw, index, name, correct=False):
    x,y=_option_box(index)
    draw.rounded_rectangle((x,y,x+OPTION_W,y+OPTION_H),radius=25,
                           fill='#0F584F' if correct else '#12356B',
                           outline=GREEN if correct else '#5078B4',width=5 if correct else 2)
    top_pad=(OPTION_H-70)//2
    draw.rounded_rectangle((x+14,y+top_pad,x+74,y+top_pad+70),radius=14,
                           fill=GREEN if correct else '#2C5189')
    draw.text((x+29,y+top_pad+11),chr(65+index),font=_font(34),fill='#082E3F' if correct else YELLOW)
    # Names wrap into at most three measured lines that also fit the card height. No ellipsis/truncation.
    words=name.split();size=OPTION_SIZE
    while size>=23:
        lines=[];line=''
        for word in words:
            candidate=f'{line} {word}'.strip()
            if draw.textbbox((0,0),candidate,font=_font(size))[2] > OPTION_TEXT_WIDTH and line:
                lines.append(line);line=word
            else:line=candidate
        if line:lines.append(line)
        if (len(lines)<=3 and len(lines)*(size+6)<=OPTION_TEXT_HEIGHT
                and all(draw.textbbox((0,0),line,font=_font(size))[2]<=OPTION_TEXT_WIDTH for line in lines)):break
        size-=1
    if size<23 or len(lines)>3 or any(draw.textbbox((0,0),line,font=_font(size))[2]>OPTION_TEXT_WIDTH for line in lines):
        raise ValueError(f'Option cannot fit safely on mobile layout: {name}')
    line_height=size+6
    top=y+(OPTION_H-len(lines)*line_height)/2
    for line in lines:
        box=draw.textbbox((0,0),line,font=_font(size))
        draw.text((x+92,top-box[1]),line,font=_font(size),fill=WHITE)
        top+=line_height


# v1.6.0 Find: four flags in a 2x2 grid inside the flag card. v1.6.5: light cells on the white neon card; Population uses
# the shorter card because its answer cards (the country names) still need room under the countdown.
FIND_CELLS = [(60+(i%2)*490, 552+(i//2)*350, 60+(i%2)*490+470, 552+(i//2)*350+336) for i in range(4)]
POP_CELLS = [(60+(i%2)*490, 552+(i//2)*306, 60+(i%2)*490+470, 552+(i//2)*306+296) for i in range(4)]
FIND_FLAG_MAX = (420,250)
POP_FLAG_MAX = (420,240)


def _mode(question):
    """'find' = four flags and no answer cards, 'std' = one flag and four answer cards (Population: four flags, short card)."""
    return 'find' if question.get('kind')=='find' else 'std'


def _find_grid(image, question, correct=None):
    """Find and Population grids. Population cells also show each country's people at the reveal."""
    population=question.get('kind')=='population'
    cells,flag_max=(POP_CELLS,POP_FLAG_MAX) if population else (FIND_CELLS,FIND_FLAG_MAX)
    draw=ImageDraw.Draw(image)
    for i,(x0,y0,x1,y1) in enumerate(cells):
        draw.rounded_rectangle((x0,y0+5,x1,y1+5),radius=26,fill='#B7C8E4')
        draw.rounded_rectangle((x0,y0,x1,y1),radius=26,fill='#DCE6F5')
        with Image.open(question['option_flag_paths'][i]) as source:
            flag=source.convert('RGBA')
        flag.thumbnail(flag_max,Image.Resampling.LANCZOS)
        cx=(x0+x1)//2;cy=(y0+y1)//2+(14 if not population else 8)
        image.paste(flag,(cx-flag.width//2,cy-flag.height//2),flag)
        draw=ImageDraw.Draw(image)
        if correct is not None and i!=correct:  # the wrong flags fade out at the reveal
            shade=Image.new('RGBA',(x1-x0-6,y1-y0-6),(10,30,70,170))
            image.paste(shade,(x0+3,y0+3),shade);draw=ImageDraw.Draw(image)
        if correct is not None and i==correct:
            draw.rounded_rectangle((x0-4,y0-4,x1+4,y1+4),radius=30,outline=GREEN,width=10)
        draw.ellipse((x0+10,y0+10,x0+70,y0+70),fill=GREEN if correct==i else '#0F2F6B',outline='#FFFFFF',width=3)
        _center(draw,chr(65+i),y0+22,38,'#082E3F' if correct==i else YELLOW,x=x0+40)
        if correct is not None and population:
            from .population import short_number
            label=short_number(question['populations'][i])
            draw.rounded_rectangle((x1-190,y1-62,x1-12,y1-12),radius=16,fill=GREEN if i==correct else '#0B2A60')
            _center(draw,label,y1-54,36,'#082E3F' if i==correct else WHITE,max_width=160,x=x1-101)


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


def _subline(index,count,question):
    """The red badge under the headline. The first Find round carries the challenge claim; the rest count the rounds."""
    if count>1 and index==count-1:
        return 'FINAL ROUND!'
    if question is not None and question.get('kind')=='find' and index==0:
        return 'ONLY 1 IS RIGHT!'  # true of every Find round: four flags, one is the country
    return f'ROUND {index+1} / {count}' if count>1 else 'ONE ROUND'


def _facts(question):
    """v1.6.7: one verifiable line about the answer's country (capital and people) for the reveal: flag questions only.
    Capital questions would give the answer away and Population questions already show the numbers."""
    if question.get('kind') in ('capital','population'):
        return None
    from .themes import capital_of
    from .population import population, short_number
    code=question.get('country_code')
    if not code:
        return None
    capital=capital_of(code);people=population(code)
    parts=([f'Capital: {capital}'] if capital else [])+([f'{short_number(people)} people'] if people else [])
    return ' \u00b7 '.join(parts) or None


def _story_panel(image, story, top):
    """v1.7 sample: the one-sentence story of the answer's flag, large, over the lower area at the reveal."""
    box=(36,top,932,1580);draw=ImageDraw.Draw(image)
    draw.rounded_rectangle(box,radius=34,fill='#0B2A60',outline=YELLOW,width=5)
    _center(draw,'FLAG STORY',top+22,32,GREEN,x=484)
    for size in range(52,31,-2):
        lines=[];line=''
        for word in story.split():
            candidate=f'{line} {word}'.strip()
            if line and draw.textbbox((0,0),candidate,font=_font(size))[2]>810:
                lines.append(line);line=word
            else:line=candidate
        lines.append(line)
        height=len(lines)*(size+14)
        if height<=box[3]-top-90:break
    else:
        raise ValueError(f'Story cannot fit on the screen: {story}')
    y=top+66+(box[3]-top-90-height)/2
    for line in lines:
        _center(draw,line,y,size,WHITE,max_width=810,x=484);y+=size+14


def _ask_box(draw, box, line_y, cta):
    draw.rounded_rectangle(box,radius=34,fill=YELLOW)
    line1,line2=cta or ('COMMENT YOUR SCORE + COUNTRY!','LIKE & SUBSCRIBE FOR MORE!')  # v1.6.6: cta.py picks the ask
    x=(box[0]+box[2])//2
    _center(draw,line1,line_y[0],40,'#0B2A60',max_width=790,x=x)
    _center(draw,line2,line_y[1],38,'#0B2A60',max_width=790,x=x)


def _question_static(question,index,count,background,reveal=False,hook=None,cta=None):
    options,correct,flag_path=_question_data(question)
    image=background.copy()
    mode=_mode(question);layout=LAYOUTS[mode];last=index==count-1
    kind=question.get('kind');grid=kind in ('find','population')
    _banner(image,_headline(index,count,question,hook),_subline(index,count,question))
    _card(image,FIND_CARD if mode=='find' else FLAG_CARD)
    if grid:
        _find_grid(image,question,correct if reveal else None)
    else:
        with Image.open(flag_path) as source:
            flag=source.convert('RGBA')
            flag.thumbnail(FLAG_MAX,Image.Resampling.LANCZOS)
            image.paste(flag,((WIDTH-flag.width)//2,FLAG_CENTER_Y-flag.height//2),flag)
    draw=ImageDraw.Draw(image)
    if mode=='std':  # Find has no answer cards: the letters sit on the flags and the answer is spelled out below
        for option_index,name in enumerate(options):
            _option(draw,option_index,name,reveal and option_index==correct)
    if kind=='population':  # CC BY 4.0 credit, kept above the Shorts caption
        from .population import SOURCE_LINE
        _center(draw,SOURCE_LINE,1590,24,MUTED)
    story=question.get('story')
    if reveal and story:  # the ask follows after the story (animated_frame)
        _center(draw,'CORRECT ANSWER',layout['label_y'],30,GREEN)
        _center(draw,f'{chr(65+correct)} · {options[correct]}',layout['name_y'],layout['name_size'],WHITE,max_width=900)
        _story_panel(image,story,1345 if mode=='find' else 1306)
        return image
    if reveal and last:
        # v1.6.1: the score ask sits on the last answer, so the Short can loop without a closing screen.
        # v1.6.5: it moved up out of the zone the Shorts caption covers.
        _ask_box(draw,layout['last_box'],layout['last_lines'],cta)
    if reveal and (not last or layout['last_label']):
        _center(draw,'CORRECT ANSWER',layout['label_y'],30,GREEN)
        _center(draw,f'{chr(65+correct)} · {options[correct]}',layout['name_y'],layout['name_size'] if not last else min(44,layout['name_size']),WHITE,max_width=900)
        facts=_facts(question)
        if facts:  # v1.6.7: a fact on the answer screen, with the data credited (CC BY 4.0) above the Shorts caption
            from .population import SOURCE_LINE
            _center(draw,facts,layout['info_y'],30,MUTED,max_width=900)
            _center(draw,SOURCE_LINE,1590,24,MUTED)
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


def animation_state(second, question_count, lengths=None):
    """Shared timing in seconds; effects are local to the current question. lengths = audio.timing(questions)."""
    seconds, hold = lengths or (QUESTION_SECONDS, CTA_SECONDS)
    index = int((second+1e-8)//seconds)
    if index >= question_count and second < question_count*seconds+hold:
        index = question_count-1  # v1.6.2: the last answer is held for CTA_SECONDS (spoken comment/subscribe ask)
    local = max(0.0, second-index*seconds)
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
    from .cta import choose as choose_cta
    hook = choose(questions)[0]
    ask = choose_cta(questions)
    boards = [(_question_static(q,i,len(questions),background,hook=hook,cta=ask[:2]),
               _question_static(q,i,len(questions),background,True,hook=hook,cta=ask[:2])) for i,q in enumerate(questions)]
    flags=[];sources=[]
    for question in questions:
        with Image.open(question['flag_path']) as source:
            full=source.convert('RGBA')
            flag=full.copy();flag.thumbnail(FLAG_MAX,Image.Resampling.LANCZOS)
            flags.append(flag)
            sources.append(full if question.get('kind')=='zoom' else None)
    return {'background':background,'boards':boards,'flags':flags,'sources':sources,'ask':ask[:2],
            'cta':_cta(background,len(questions)),'questions':questions,'hook':hook,'cta_variant':ask[3]}


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


def _reveal_pop(image, board, box, elapsed, strength):
    """v1.6.5: for REVEAL_FX_SECONDS the right answer swells by `strength` and glows white, then settles. Local to box."""
    if not 0 <= elapsed < REVEAL_FX_SECONDS:
        return
    t = elapsed/REVEAL_FX_SECONDS
    scale = 1+strength*math.sin(math.pi*t)
    x0,y0,x1,y1 = box;w,h = x1-x0,y1-y0
    pop = board.crop(box).resize((round(w*scale),round(h*scale)),Image.Resampling.LANCZOS).convert('RGBA')
    glow = Image.new('RGBA',pop.size,(0,0,0,0))
    inset = round(14*scale)
    ImageDraw.Draw(glow).rounded_rectangle((inset,inset,pop.width-inset,pop.height-inset),radius=26,fill=(255,255,255,round(120*(1-t))))
    pop = Image.alpha_composite(pop,glow).convert('RGB')
    image.paste(pop,(x0-(pop.width-w)//2,y0-(pop.height-h)//2))


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
    questions=context['questions'];lengths=timing(questions);state=animation_state(second,len(questions),lengths)
    index=state['question_index'];local=state['local']
    if state['cta']:
        image=context['cta'].copy();draw=ImageDraw.Draw(image)
        elapsed=second-len(questions)*lengths[0]
        length=int(700*min(1,elapsed/.45))
        draw.rounded_rectangle((190,1320,190+max(1,length),1327),radius=3,fill=YELLOW)
        return image
    image=context['boards'][index][int(state['reveal'])].copy()
    draw=ImageDraw.Draw(image)
    question=questions[index];mode=_mode(question);layout=LAYOUTS[mode]
    inner=(FLAG_CARD[0]+14,FLAG_CARD[1]+14,FLAG_CARD[2]-14,FLAG_CARD[3]-14)
    if not state['reveal']:
        if question.get('kind')=='zoom':
            draw.rectangle(inner,fill='#F7FAFF')
            flag=_zoomed(context['sources'][index],context['flags'][index].size,question['zoom_center'],local)
            image.paste(flag,((WIDTH-flag.width)//2,FLAG_CENTER_Y-flag.height//2),flag)
        elif local < FLAG_POP_SECONDS and question.get('kind') not in ('find','population'):
            # Keep the whole flag visible, including frame zero. No blackout/fade.
            draw.rectangle(inner,fill='#F7FAFF')
            flag=context['flags'][index]
            scaled=flag.resize((round(flag.width*state['flag_scale']),round(flag.height*state['flag_scale'])),Image.Resampling.LANCZOS)
            image.paste(scaled,((WIDTH-scaled.width)//2,FLAG_CENTER_Y-scaled.height//2),scaled)
        color='#FFC663' if state['urgent'] else YELLOW
        draw=ImageDraw.Draw(image)
        x0,y0,x1,y1=layout['ring'];ring=x1-x0
        draw.arc(layout['ring'],-90,270,fill='#34558B',width=9)
        draw.arc(layout['ring'],-90,-90+360*state['progress'],fill=color,width=10)
        base=round(104*ring/180);size=round(base*state['digit_scale'])
        _center(draw,str(state['remaining']),y0+round(28*ring/180)-round((size-base)/2),size,color,max_width=round(170*ring/180))
        bar=layout['bar_y']
        draw.rounded_rectangle((160,bar,920,bar+12),radius=6,fill='#34558B')
        end=160+round(760*state['progress'])
        if end>161:draw.rounded_rectangle((160,bar,end,bar+12),radius=6,fill=color)
    else:
        correct=int(question['correct_index']);elapsed=local-COUNTDOWN_SECONDS
        if mode=='std' and question.get('story'):
            origin=(WIDTH//2,FLAG_CENTER_Y)
        elif mode=='std':
            x,y=_option_box(correct)
            card=context['boards'][index][1].crop((x,y,x+OPTION_W+1,y+OPTION_H+1))
            width=round((OPTION_W+1)*state['answer_scale']);height=round((OPTION_H+1)*state['answer_scale'])
            left=x-(width-OPTION_W-1)//2;top=y-(height-OPTION_H-1)//2
            image.paste(card.resize((width,height),Image.Resampling.LANCZOS),(left,top))
            draw=ImageDraw.Draw(image)
            draw.rounded_rectangle((left,top,left+width-1,top+height-1),radius=26,
                                   outline='#A8FFE0' if elapsed<.35 else GREEN,width=6)
            origin=(x+OPTION_W//2,y+OPTION_H//2)
        else:
            cx0,cy0,cx1,cy1=FIND_CELLS[correct];origin=((cx0+cx1)//2,(cy0+cy1)//2)
        # v1.6.5: the right answer pops and flashes for a moment (a local glow that fades out, never a full-screen flash)
        box=(cx0-14,cy0-14,cx1+14,cy1+14) if mode=='find' else FLAG_CARD if question.get('kind')!='population' else POP_CELLS[correct]
        if question.get('kind')=='population':box=(box[0]-14,box[1]-14,box[2]+14,box[3]+14)
        _reveal_pop(image,context['boards'][index][1],box,elapsed,.05 if mode=='find' or question.get('kind')=='population' else .025)
        draw=ImageDraw.Draw(image)
        _confetti(draw,index,origin[0],origin[1],elapsed)
        if question.get('story') and index==len(questions)-1 and local>=lengths[0]:
            top=1345 if mode=='find' else 1306  # same top as the story panel, so the answer name stays readable
            _ask_box(draw,(36,top,932,1580),(top+80,top+168),context['ask'])  # held closing seconds, over the story panel
    if index>0 and local<.16:
        draw.rectangle((0,516,int(WIDTH*(local/.16)),522),fill=YELLOW)
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
    seconds,hold=timing(questions)
    duration=count*seconds+hold
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
                question_index=int(second//seconds)
                local=second-question_index*seconds
                image=animated_frame(animation,second)
                if (number%round(seconds*FPS)==0 or
                    number%round(seconds*FPS)==round(2.0*FPS) or
                    number%round(seconds*FPS)==round(COUNTDOWN_SECONDS*FPS)) and question_index<count:
                    label='start' if local<.01 else 'countdown' if local<COUNTDOWN_SECONDS else 'answer'
                    name=f'question_{question_index+1:02d}_{label}.jpg'
                    image.save(inspection/name,quality=92)
                    inspections.append({'file':name,'time_seconds':second,'frame':number})
                if number==count*round(seconds*FPS):
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
            'layout_safety':{'horizontal_margin':40,'right_edge_clear_of_shorts_buttons':930,'bottom_clear_of_caption':1580,'minimum_option_font':23,'option_count':4,
                             'flag_aspect_preserved':True,'no_text_truncation':True},
            'ffmpeg_log':log_path.name}
    report['presentation']={'version':'1.2','intro_seconds':FLAG_POP_SECONDS,'first_flag_scale':1.0,
                            'countdown_seconds':COUNTDOWN_SECONDS,'answer_hold_seconds':seconds-COUNTDOWN_SECONDS,
                            'digit_pulse_seconds':.18,'answer_pulse_seconds':.28,'global_flashes':False,'camera_shake':False}
    (destination.parent/'render_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
