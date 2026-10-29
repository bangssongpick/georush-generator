"""Exactly-three-file landscape publishing and timeline-derived upload text."""
from pathlib import Path
import shutil
import tempfile
from PIL import Image,ImageDraw
from .render import background,text,YELLOW,WHITE
from .timeline import chapters,timestamp

FINAL_FILES={'longform.mp4','longform_metadata.txt','longform_thumbnail.jpg'}


def metadata(quiz,timeline):
    count=len(quiz['questions'])
    chapter_text='\n'.join(f'{timestamp(at)} {label}' for at,label in chapters(timeline))
    return (f'[제목]\nGuess {count} Flags! 🌍 Easy to Expert Geography Quiz\n\n'
            f'[설명]\nCan you identify all {count} country flags?\n\n'
            'Test your geography knowledge in this Easy to Expert challenge!\n'
            'Choose A, B, C or D. Each question has an 8-second countdown and a 2-second answer reveal.\n'
            'Difficulty tiers are editorial groupings, not measured player ratings. Familiarity varies by viewer.\n\n'
            'Watch until the end and share your final score.\n'
            'Subscribe to GeoRush (@GeoRushGames) for more geography challenges.\n\n'
            'CHAPTERS\n'+chapter_text+'\n\n'
            '#GeoRush #FlagQuiz #GeographyQuiz #GuessTheFlag\n\n'
            f'[고정 댓글]\nHow many flags did you recognize? Share your score out of {count}!\n\n'
            '[태그]\nGeoRush, guess the flag, flag quiz, geography quiz, world flags, guess the country, geography challenge\n\n'
            '[카테고리]\n교육 / 아동용 아님\n')


def thumbnail(quiz,destination):
    count=len(quiz['questions']);image=background().copy();d=ImageDraw.Draw(image)
    text(d,f'GUESS {count} FLAGS!',(100,160,1720,150),110,YELLOW)
    text(d,'EASY TO EXPERT',(100,330,1720,100),58,WHITE)
    # Five actual challenge flags, distributed across the four editorial rounds.
    indices=[0,count//4,count//2,3*count//4,count-1]
    for n,index in enumerate(indices):
        x=130+n*340
        d.rounded_rectangle((x,505,x+300,740),radius=18,fill='#F4F8FF')
        with Image.open(quiz['questions'][index]['flag_path']) as source:
            flag=source.convert('RGB');flag.thumbnail((270,190),Image.Resampling.LANCZOS)
            image.paste(flag,(x+(300-flag.width)//2,622-flag.height//2))
    text(ImageDraw.Draw(image),f'CAN YOU SCORE {count}/{count}?',(100,815,1720,100),62,YELLOW)
    image.save(destination,quality=95,subsampling=0)
    return {'size':[1920,1080],'country_codes':[quiz['questions'][i]['country_code'] for i in indices],
            'source':'Verified flags from this actual challenge; no country names or answer positions'}


def publish(work,final):
    work,final=Path(work),Path(final)
    stage=Path(tempfile.mkdtemp(prefix='.GeoRush_Longform_pending_',dir=final.parent))
    try:
        for name in FINAL_FILES:shutil.copy2(work/name,stage/name)
        if {p.name for p in stage.iterdir()}!=FINAL_FILES:raise ValueError('롱폼 최종 파일 구조 오류')
        stage.rename(final)
    finally:
        if stage.exists():shutil.rmtree(stage)
