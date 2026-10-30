"""Editorial longform tiers over the hash-verified 190-flag catalog."""
from collections import Counter
import hashlib
import json
import random
from ..quiz import validate_quiz, composition_signature

TIERS = ('Easy', 'Normal', 'Hard', 'Expert')
# Catalog 'Hard' flags split into Longform Hard and Expert; the first ten of each are the v1.3 groups.
HARD = frozenset(('ec bo pe cl co cr pa cu jm uy '
                  'bf bh bj bn bw bz cd cf cg ci cm ga gh gm gn gy la lr md mk '
                  'ml mr mu mv mw ne rw sl so sr sy tg tt ye zm').split())
EXPERT = frozenset(('kz uz ge am az al hr rs ba sk '
                    'ki mh fm nr pw tv to ws sb vu ag dm gd kn lc vc ad li sm cv '
                    'km st sc dj er gq gw sz ls ss bi bt tm tj tl').split())
DIFFICULTY_NOTE = ('Editorial progression, not a measured player difficulty rating. Easy/Normal reuse the '
                   'catalog groups. Hard: less familiar flags from the Americas, Africa and Asia. Expert: '
                   'microstates, Pacific and Caribbean islands, Balkan and Central Asian flags with similar '
                   'designs. Familiarity varies by viewer.')


def tier_for(row):
    if row['difficulty'] != 'Hard':
        return row['difficulty']
    if row['code'] in HARD:
        return 'Hard'
    if row['code'] in EXPERT:
        return 'Expert'
    raise ValueError('롱폼 난이도 기준이 없는 국가: '+row['code'])


def allocations(count):
    if type(count) is not int or count not in (20, 30, 40):
        raise ValueError('롱폼 문제 수는 20 / 30 / 40입니다.')
    return [count//4 + int(i<count%4) for i in range(4)]


def signature(questions):
    # Mode prefix separates this ordered challenge from Shorts set signatures.
    return 'longform:'+hashlib.sha256(json.dumps([q['country_code'] for q in questions]).encode()).hexdigest()


def validate(quiz, catalog):
    questions=quiz.get('questions', [])
    expected=allocations(len(questions))
    if quiz.get('mode')!='Longform' or quiz.get('signature')!=signature(questions):
        raise ValueError('롱폼 모드 또는 문제 순서 서명 오류')
    if len({q['country_code'] for q in questions})!=len(questions):
        raise ValueError('롱폼 국가 중복')
    offset=0
    for tier,count in zip(TIERS,expected):
        for question in questions[offset:offset+count]:
            if question.get('longform_tier')!=tier or tier_for(catalog.get(question['country_code']))!=tier:
                raise ValueError('롱폼 난이도 분류 또는 순서 오류')
        offset+=count
    # Reuse every original answer/name/path/hash check without lifting Shorts' 5-question bound.
    for i in range(0,len(questions),5):
        chunk=questions[i:i+5]
        validate_quiz({'questions':chunk,'signature':composition_signature(chunk)},catalog)
    distribution=Counter(q['correct_index'] for q in questions)
    if max(distribution.get(i,0) for i in range(4))-min(distribution.get(i,0) for i in range(4))>1:
        raise ValueError('정답 위치 분포가 불균형합니다.')
    return True


def build(catalog, history=None, count=40, seed=None):
    counts=allocations(count)
    valid,errors=catalog.valid_countries()
    pools={tier:[r for r in valid if tier_for(r)==tier] for tier in TIERS}
    for tier,needed in zip(TIERS,counts):
        if len(pools[tier])<needed:
            raise ValueError(f'{tier} 검증 국기 부족: 필요 {needed}, 사용 가능 {len(pools[tier])}. '+'; '.join(errors))
    used=history.used_signatures() if history else set()
    # v1.3.5: keep the flags of the previous two Longforms out of each round whenever the round still has enough others.
    recent=set().union(*history.recent_longform_country_codes(2)) if history else set()
    fresh={tier:[r for r in pools[tier] if r['code'] not in recent] for tier in TIERS}
    draw={tier:(fresh[tier] if len(fresh[tier])>=needed else pools[tier]) for tier,needed in zip(TIERS,counts)}
    rng=random.Random(seed)
    for _ in range(128):
        positions=[i%4 for i in range(count)];rng.shuffle(positions)
        questions=[]
        for tier,needed in zip(TIERS,counts):
            for row in rng.sample(draw[tier],needed):
                candidates=[r for r in pools[tier] if r['code']!=row['code']]
                wrong=rng.sample(candidates if len(candidates)>=3 else [r for r in valid if r['code']!=row['code']],3)
                options=[r['name'] for r in wrong];answer=positions[len(questions)]
                options.insert(answer,row['name'])
                questions.append({**{key:row[key] for key in ('flag_path','flag','difficulty')},
                    'country_code':row['code'],'country_name':row['name'],'flag_sha256':row['sha256'],
                    'options':options,'correct_index':answer,'longform_tier':tier})
        quiz={'schema_version':1,'mode':'Longform','channel':'GeoRush','difficulty':'Mixed',
              'difficulty_note':DIFFICULTY_NOTE,'questions':questions,'signature':signature(questions),
              'asset_warnings':errors,'seed':seed}
        if quiz['signature'] not in used:
            validate(quiz,catalog)
            return quiz
    raise ValueError('새 롱폼 문제 순서를 찾지 못했습니다.')
