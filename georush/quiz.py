"""Deterministic when seeded, locally verified four-choice flag quizzes."""
import hashlib
import json
from pathlib import Path
import random

from .catalog import CatalogError
from .themes import FIRST_FLAGS, THEMES, capital_of, continent_of, lookalike_mates, theme_pool

LEVELS = ('Easy', 'Normal', 'Hard', 'Mixed')
TIER_ORDER = {'Easy': 0, 'Normal': 1, 'Hard': 2}
RECENT_SHORTS = 21  # Shorts whose countries are avoided, newest first: one week at 3 Shorts a day (v1.3.2-v1.3.4: 7)


def composition_signature(questions):
    # Reordering answers or questions must not bypass duplicate-composition checks.
    # v1.4.0: a capital-city question about a country is a different video than its flag question.
    codes = sorted(('capital:' if question.get('kind') == 'capital' else '')+question['country_code']
                   for question in questions)
    return hashlib.sha256(json.dumps(codes, separators=(',', ':')).encode()).hexdigest()


def validate_quiz(quiz, catalog):
    questions = quiz.get('questions', [])
    if not questions or len(questions) > 5:
        raise ValueError('문제 수는 1~5개여야 합니다.')
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


def _first_flag(rng, pool, recent_runs):
    """A famous flag, the one least recently used. The avoid list does not apply: a quick win matters more here."""
    famous = [row for row in pool if row['code'] in FIRST_FLAGS]
    candidates = famous or [row for row in pool if row['difficulty'] == 'Easy'] or pool
    for window in range(len(recent_runs), -1, -1):
        unused = [row for row in candidates if row['code'] not in set().union(*recent_runs[:window])]
        if unused:
            return rng.choice(unused)
    return rng.choice(candidates)


def _progression_sample(rng, fresh, pool, k, recent_runs):
    """v1.4.2 Mixed order: famous first flag, Normal flags in the middle, a Hard flag last."""
    selected = [_first_flag(rng, pool, recent_runs)]

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
        take('Normal', k-2)
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
    if theme == 'Lookalike':
        mates = [row for row in candidates if row['code'] in lookalike_mates(country['code'])]
        wrong = rng.sample(mates, min(3, len(mates)))
    # Regional and capital questions take wrong answers from the same continent, so they cannot be guessed by region.
    continent = continent_of(country['code'])
    for group in ([row for row in candidates if continent_of(row['code']) == continent], candidates):
        rest = [row for row in group if row not in wrong]
        if len(rest) >= 3-len(wrong):
            return wrong+rng.sample(rest, 3-len(wrong))
    raise CatalogError('선택지를 만들 국가가 부족합니다.')


def build_quiz(catalog, history=None, difficulty='Mixed', questions_per_video=3, seed=None, theme='Classic'):
    if difficulty not in LEVELS:
        raise ValueError('지원하지 않는 난이도입니다.')
    if theme not in THEMES:
        raise ValueError('지원하지 않는 주제입니다.')
    if not isinstance(questions_per_video, int) or not 1 <= questions_per_video <= 5:
        raise ValueError('한 영상의 문제 수는 1~5개입니다.')
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
    for attempt in range(512):
        rows = selection_pool if attempt < 256 else pool
        if difficulty == 'Mixed':
            selected = _progression_sample(rng, rows, pool, questions_per_video, recent_runs)
        else:
            selected = rng.sample(rows, questions_per_video)
        if theme == 'Lookalike' and any(row['code'] in lookalike_mates(other['code'])
                                        for row in selected for other in selected):
            continue  # two flags of one look-alike group in a video would give each other away
        questions = []
        for country in selected:
            wrong = _distractors(rng, country, valid, theme)
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
