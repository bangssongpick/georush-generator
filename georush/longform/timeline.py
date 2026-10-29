"""One source of truth for chapters, rendering, audio and validation."""
INTRO=5
QUESTION=10
COUNTDOWN=8
REVEAL=2
CHAPTER=3
OUTRO=10
FPS=30


def build_timeline(quiz):
    items=[{'kind':'intro','start':0,'duration':INTRO,'label':'Welcome'}]
    cursor=INTRO
    previous=None
    for i,q in enumerate(quiz['questions']):
        tier=q['longform_tier']
        if tier!=previous:
            if previous is not None:
                items.append({'kind':'chapter','start':cursor,'duration':CHAPTER,'tier':tier,'label':tier})
                cursor+=CHAPTER
            chapter_start=cursor if previous is None else cursor-CHAPTER
            items.append({'kind':'question','start':cursor,'duration':QUESTION,'tier':tier,
                          'question_index':i,'chapter_start':chapter_start,'new_tier':True})
            previous=tier
        else:
            items.append({'kind':'question','start':cursor,'duration':QUESTION,'tier':tier,'question_index':i,'new_tier':False})
        cursor+=QUESTION
    items.append({'kind':'outro','start':cursor,'duration':OUTRO,'label':"What's your score?"})
    return {'segments':items,'duration':cursor+OUTRO,'frames':(cursor+OUTRO)*FPS,'fps':FPS}


def chapters(timeline):
    result=[(0,'Welcome')]
    for item in timeline['segments']:
        if item['kind']=='question' and item['new_tier']:
            result.append((item['chapter_start'],item['tier']))
    result.append((timeline['segments'][-1]['start'],"What's your score?"))
    return result


def timestamp(seconds):
    return f'{int(seconds)//60:02d}:{int(seconds)%60:02d}'
