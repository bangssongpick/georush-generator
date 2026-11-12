"""Deterministic when seeded, locally verified four-choice flag quizzes."""
import hashlib
import json
from pathlib import Path
import random

from .catalog import CatalogError
from .themes import (ZOOM_MARGIN, ZOOM_START, FIRST_FLAGS, THEMES, AUDIENCE_FIND, AUDIENCE_NORMAL, AUDIENCE_NORMAL_SHARE,
                     capital_of, continent_of, lookalike_mates, theme_pool)

LEVELS = ('Easy', 'Normal', 'Hard', 'Mixed')
TIER_ORDER = {'Easy': 0, 'Normal': 1, 'Hard': 2}
MAX_QUESTIONS = 10  # v1.5.0: speed rounds of up to 10 flags (was 5)
RECENT_SHORTS = 21  # Shorts whose countries are avoided, newest first: one week at 3 Shorts a day (v1.3.2-v1.3.4: 7)


def composition_signature(questions):
    # Reordering answers or questions must not bypass duplicate-composition checks.
    # v1.4.0: a capital-city question about a country is a different video than its flag question.
    # v1.5.0: so is a zoomed-in question.
    codes = sorted((question['kind']+':' if question.get('kind') in ('capital', 'zoom', 'find', 'population') else '')+question['country_code']
                   for question in questions)
    return hashlib.sha256(json.dumps(codes, separators=(',', ':')).encode()).hexdigest()


def validate_quiz(quiz, catalog):
    questions = quiz.get('questions', [])
    if not questions or len(questions) > MAX_QUESTIONS:
        raise ValueError(f'문제 수는 1~{MAX_QUESTIONS}개여야 합니다.')
    seen = set()
    for question in questions:
        code = question.get('country_code')
        if code in seen:
            raise ValueError('동일 영상 안에 국가가 중복됩니다.')
        seen.add(code)
        try:
            country = catalog.validate_country(code)
        except CatalogError as exc:
            raise ValueError(str(exc)) from exc
        if question.get('country_name') != country['name']:
            raise ValueError('국가 이름과 국기 코드가 일치하지 않습니다.')
        capital = question.get('kind') == 'capital'
        if capital and (not capital_of(code) or question.get('answer_name') != capital_of(code)):
            raise ValueError('수도 문제의 정답이 해당 국가의 수도와 일치하지 않습니다.')
        if question.get('kind') == 'zoom':
            center = question.get('zoom_center')
            if not (isinstance(center, list) and len(center) == 2 and all(ZOOM_MARGIN <= v <= 1-ZOOM_MARGIN for v in center)):
                raise ValueError('확대 문제의 확대 위치가 올바르지 않습니다.')
        if question.get('kind') == 'population':
            from .population import margin_ok, population
            names = {row['name']: row['code'] for row in catalog.countries}
            codes = [names.get(o) for o in question.get('options', [])]
            if None in codes or max(codes, key=population) != code or not margin_ok(codes, 'Hard'):
                raise ValueError('인구 문제의 정답이 인구가 가장 많은 나라가 아니거나 차이가 너무 작습니다.')
        if question.get('kind') in ('find', 'population'):
            paths = question.get('option_flag_paths')
            names = {row['name']: row['code'] for row in catalog.countries}
            if (not isinstance(paths, list) or len(paths) != 4 or any(o not in names for o in question.get('options', []))
                    or any(Path(p).resolve() != Path(catalog.validate_country(names[o])['flag_path']).resolve()
                           for o, p in zip(question['options'], paths))):
                raise ValueError('국기 찾기 문제의 보기 국기가 국가와 일치하지 않습니다.')
        expected = Path(country['flag_path']).resolve()
        if Path(question.get('flag_path', '')).resolve() != expected:
            raise ValueError('문제의 국기 파일이 해당 국가와 일치하지 않습니다.')
        options = question.get('options', [])
        answer = question.get('correct_index')
        if not isinstance(options, list) or len(options) != 4 or len(set(options)) != 4:
            raise ValueError('선택지는 서로 다른 4개여야 합니다.')
        if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < 4:
            raise ValueError('정답 위치가 올바르지 않습니다.')
        if capital:
            valid_names = {capital_of(row['code']) for row in catalog.countries} - {''}
            expected_answer = question['answer_name']
        else:
            valid_names = {row['name'] for row in catalog.countries}
            expected_answer = country['name']
        if any(option not in valid_names for option in options):
            raise ValueError('선택지에 확인되지 않은 국가가 있습니다.')
        if options[answer] != expected_answer or options.count(expected_answer) != 1:
            raise ValueError('정답은 정확히 하나여야 합니다.')
    if quiz.get('signature') != composition_signature(questions):
        raise ValueError('문제 구성 서명이 일치하지 않습니다.')
    return True


def _zoom_center(rng, flag_path):
    """The most detailed of a few random spots, so a zoomed-in corner is never a plain stripe of colour."""
    from PIL import Image, ImageStat
    with Image.open(flag_path) as source:
        image = source.convert('RGB')
    best, score = None, -1.0
    for _ in range(12):
        center = [round(rng.uniform(ZOOM_MARGIN, 1-ZOOM_MARGIN), 3) for _ in range(2)]
        w, h = image.size[0]*ZOOM_START, image.size[1]*ZOOM_START
        box = (round(center[0]*image.size[0]-w/2), round(center[1]*image.size[1]-h/2))
        crop = image.crop((box[0], box[1], box[0]+round(w), box[1]+round(h)))
        value = sum(ImageStat.Stat(crop).stddev)
        if value > score:
            best, score = center, value
    return best


def _first_flag(rng, pool, recent_runs, first_codes=FIRST_FLAGS):
    """A famous flag, the one least recently used. The avoid list does not apply: a quick win matters more here."""
    famous = [row for row in pool if row['code'] in first_codes]
    candidates = famous or [row for row in pool if row['difficulty'] == 'Easy'] or pool
    for window in range(len(recent_runs), -1, -1):
        unused = [row for row in candidates if row['code'] not in set().union(*recent_runs[:window])]
        if unused:
            return rng.choice(unused)
    return rng.choice(candidates)


def _progression_sample(rng, fresh, pool, k, recent_runs, first_codes=FIRST_FLAGS):
    """v1.4.2 Mixed order: famous first flag, Normal flags in the middle, a Hard flag last.
    v1.6.0: half of the time one middle flag is from the channel's big audience countries (if not used lately)."""
    selected = [_first_flag(rng, pool, recent_runs, first_codes)]
    if k > 2 and rng.random() < AUDIENCE_NORMAL_SHARE:
        recent = set().union(*recent_runs) if recent_runs else set()
        home = [row for row in fresh if row['code'] in AUDIENCE_NORMAL and row['code'] not in recent
                and row['difficulty'] == 'Normal' and row not in selected]
        if home:
            selected.append(rng.choice(home))

    def take(tier, count):
        for rows in ([row for row in fresh if row['difficulty'] == tier], fresh,
                     [row for row in pool if row['difficulty'] == tier], pool):
            rows = [row for row in rows if row not in selected]
            if len(rows) >= count:
                selected.extend(rng.sample(rows, count))
                return
        raise CatalogError('문제를 만들 국가가 부족합니다.')
    if k > 1:
        take('Hard', 1)
        take('Normal', k-len(selected))
    return selected


def _distractors(rng, country, valid, theme):
    """Three wrong answers. Classic keeps the exact v1.3 draw so old seeds give the same quizzes."""
    candidates = [row for row in valid if row['code'] != country['code']]
    if theme == 'Classic':
        # Same-tier distractors keep Easy/Normal/Hard meaningful, with a safe fallback.
        same_tier = [row for row in candidates if row['difficulty'] == country['difficulty']]
        return rng.sample(same_tier if len(same_tier) >= 3 else candidates, 3)
    if theme == 'Capital':
        candidates = [row for row in candidates if capital_of(row['code'])]
    wrong = []
    if theme in ('Lookalike', 'Find'):  # v1.6.0: a Find round is only hard when the other flags look alike
        mates = [row for row in candidates if row['code'] in lookalike_mates(country['code'])]
        wrong = rng.sample(mates, min(3, len(mates)))
    # Regional and capital questions take wrong answers from the same continent, so they cannot be guessed by region.
    continent = continent_of(country['code'])
    for group in ([row for row in candidates if continent_of(row['code']) == continent], candidates):
        rest = [row for row in group if row not in wrong]
        if len(rest) >= 3-len(wrong):
            return wrong+rng.sample(rest, 3-len(wrong))
    raise CatalogError('선택지를 만들 국가가 부족합니다.')


def _population_questions(rng, valid, k, recent_runs, avoid):
    """v1.6.2: k rounds of 'which has the most people?', easy -> hard margins, every country used once per video.
    Most rounds include one of the channel's big audience countries."""
    from .population import margin_ok, population
    tiers = (['Easy'] + ['Normal']*(k-2) + ['Hard']) if k > 1 else ['Easy']
    recent = set().union(*recent_runs) if recent_runs else set()
    used, questions = set(), []
    for tier in tiers[:k]:
        for attempt in range(4000):
            pool = [row for row in valid if row['code'] not in used]
            home = [row for row in pool if row['code'] in AUDIENCE_FIND]
            first = rng.choice(home) if home and rng.random() < .7 else rng.choice(pool)
            rows = [first] + rng.sample([row for row in pool if row is not first], 3)
            codes = [row['code'] for row in rows]
            harder = {'Easy': None, 'Normal': 'Easy', 'Hard': 'Normal'}[tier]  # a Hard round is not also a Normal one
            if not margin_ok(codes, tier) or (harder and margin_ok(codes, harder)):
                continue
            answer = max(rows, key=lambda row: population(row['code']))
            if answer['code'] in (recent | avoid) and attempt < 3000:
                continue
            break
        else:
            raise CatalogError('인구 문제를 만들 국가 조합을 찾지 못했습니다.')
        used.update(codes)
        rng.shuffle(rows)
        options = [row['name'] for row in rows]
        questions.append({'country_code': answer['code'], 'country_name': answer['name'],
                          'flag_path': answer['flag_path'], 'flag': answer['flag'], 'flag_sha256': answer['sha256'],
                          'options': options, 'correct_index': options.index(answer['name']), 'difficulty': tier,
                          'kind': 'population', 'option_flag_paths': [row['flag_path'] for row in rows],
                          'populations': [population(row['code']) for row in rows]})
    return questions


def build_quiz(catalog, history=None, difficulty='Mixed', questions_per_video=3, seed=None, theme='Classic'):
    if difficulty not in LEVELS:
        raise ValueError('지원하지 않는 난이도입니다.')
    if theme not in THEMES:
        raise ValueError('지원하지 않는 주제입니다.')
    if not isinstance(questions_per_video, int) or not 1 <= questions_per_video <= MAX_QUESTIONS:
        raise ValueError(f'한 영상의 문제 수는 1~{MAX_QUESTIONS}개입니다.')
    rng = random.Random(seed)
    valid, errors = catalog.valid_countries()
    pool = valid if difficulty == 'Mixed' else [row for row in valid if row['difficulty'] == difficulty]
    pool = theme_pool(theme, pool)
    if len(valid) < 4 or len(pool) < questions_per_video:
        raise CatalogError('검증된 국가·국기가 부족해 문제를 만들 수 없습니다. '+ '; '.join(errors[:3]))
    used = history.used_signatures() if history is not None else set()
    recent_runs = history.recent_shorts_country_codes(RECENT_SHORTS) if history is not None else []
    # Drop the oldest Shorts from the avoided set until enough countries remain; 0 means the whole pool.
    avoid = history.avoided_codes() if history is not None else set()  # v1.3.6: flags already on the channel
    for window in range(len(recent_runs), -1, -1):
        recent = set().union(*recent_runs[:window]) | avoid
        fresh = [row for row in pool if row['code'] not in recent]
        if len(fresh) >= questions_per_video:
            break
    if len(fresh) < questions_per_video:  # the avoid list left too little: it is a preference, not a rule
        fresh = pool
    selection_pool = fresh
    if theme == 'Population':
        for attempt in range(64):
            questions = _population_questions(rng, valid, questions_per_video, recent_runs, avoid)
            signature = composition_signature(questions)
            if signature not in used:
                quiz = {'schema_version': 1, 'channel': 'GeoRush', 'difficulty': difficulty, 'questions': questions,
                        'signature': signature, 'asset_warnings': errors, 'seed': seed, 'theme': theme}
                validate_quiz(quiz, catalog)
                return quiz
        raise ValueError('새 인구 문제 구성을 찾지 못했습니다.')
    for attempt in range(512):
        rows = selection_pool if attempt < 256 else pool
        if difficulty == 'Mixed':
            first_codes = AUDIENCE_FIND if theme == 'Find' else FIRST_FLAGS
            selected = _progression_sample(rng, rows, pool, questions_per_video, recent_runs, first_codes)
        else:
            selected = rng.sample(rows, questions_per_video)
        if theme == 'Lookalike' and any(row['code'] in lookalike_mates(other['code'])
                                        for row in selected for other in selected):
            continue  # two flags of one look-alike group in a video would give each other away
        questions = []
        for country in selected:
            # v1.6.0 Find: another round's answer is never a wrong flag here (it would give that round away).
            choices = [row for row in valid if row is country or row not in selected] if theme == 'Find' else valid
            wrong = _distractors(rng, country, choices, theme)
            label = (lambda row: capital_of(row['code'])) if theme == 'Capital' else (lambda row: row['name'])
            answer = label(country)
            options = [answer] + [label(row) for row in wrong]
            rng.shuffle(options)
            question = {'country_code': country['code'], 'country_name': country['name'],
                        'flag_path': country['flag_path'], 'flag': country['flag'],
                        'flag_sha256': country['sha256'], 'options': options,
                        'correct_index': options.index(answer),
                        'difficulty': country['difficulty']}
            if theme == 'Capital':
                question.update(kind='capital', answer_name=answer)
            elif theme == 'Zoom':
                question.update(kind='zoom', zoom_center=_zoom_center(rng, country['flag_path']))
            elif theme == 'Find':
                by_name = {row['name']: row['flag_path'] for row in [country]+wrong}
                question.update(kind='find', option_flag_paths=[by_name[name] for name in options])
            questions.append(question)
        # v1.3.6: easiest flag first (a quick win keeps viewers), hardest last (a reason to stay for the finale).
        # Python's sort is stable, so the famous first flag stays first. The signature ignores order.
        questions.sort(key=lambda q: TIER_ORDER.get(q['difficulty'], 1))
        signature = composition_signature(questions)
        if signature not in used:
            quiz = {'schema_version': 1, 'channel': 'GeoRush', 'difficulty': difficulty,
                    'questions': questions, 'signature': signature,
                    'asset_warnings': errors, 'seed': seed}
            if theme != 'Classic':  # Classic quiz files stay exactly as before
                quiz['theme'] = theme
            validate_quiz(quiz, catalog)
            return quiz
    raise ValueError('새 문제 구성을 찾지 못했습니다. 다른 난이도나 문제 수를 선택하세요.')
