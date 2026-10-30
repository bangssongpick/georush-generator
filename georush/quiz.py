"""Deterministic when seeded, locally verified four-choice flag quizzes."""
import hashlib
import json
from pathlib import Path
import random

from .catalog import CatalogError

LEVELS = ('Easy', 'Normal', 'Hard', 'Mixed')
RECENT_SHORTS = 21  # Shorts whose countries are avoided, newest first: one week at 3 Shorts a day (v1.3.2-v1.3.4: 7)


def composition_signature(questions):
    # Reordering answers or questions must not bypass duplicate-composition checks.
    codes = sorted(question['country_code'] for question in questions)
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
        expected = Path(country['flag_path']).resolve()
        if Path(question.get('flag_path', '')).resolve() != expected:
            raise ValueError('문제의 국기 파일이 해당 국가와 일치하지 않습니다.')
        options = question.get('options', [])
        answer = question.get('correct_index')
        if not isinstance(options, list) or len(options) != 4 or len(set(options)) != 4:
            raise ValueError('선택지는 서로 다른 4개여야 합니다.')
        if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < 4:
            raise ValueError('정답 위치가 올바르지 않습니다.')
        valid_names = {row['name'] for row in catalog.countries}
        if any(option not in valid_names for option in options):
            raise ValueError('선택지에 확인되지 않은 국가가 있습니다.')
        if options[answer] != country['name'] or options.count(country['name']) != 1:
            raise ValueError('정답은 정확히 하나여야 합니다.')
    if quiz.get('signature') != composition_signature(questions):
        raise ValueError('문제 구성 서명이 일치하지 않습니다.')
    return True


def _tier_balanced_sample(rng, rows, k):
    # Mixed gives each difficulty an equal chance however many countries it has (Easy 40 / Normal 60 / Hard 90),
    # matching the v1.3 one-third split of the original 20/20/20 catalog.
    rows, selected = list(rows), []
    for _ in range(k):
        sizes = {}
        for row in rows:
            sizes[row['difficulty']] = sizes.get(row['difficulty'], 0) + 1
        chosen = rng.choices(rows, weights=[1 / sizes[row['difficulty']] for row in rows])[0]
        selected.append(chosen)
        rows.remove(chosen)
    return selected


def build_quiz(catalog, history=None, difficulty='Mixed', questions_per_video=3, seed=None):
    if difficulty not in LEVELS:
        raise ValueError('지원하지 않는 난이도입니다.')
    if not isinstance(questions_per_video, int) or not 1 <= questions_per_video <= 5:
        raise ValueError('한 영상의 문제 수는 1~5개입니다.')
    rng = random.Random(seed)
    valid, errors = catalog.valid_countries()
    pool = valid if difficulty == 'Mixed' else [row for row in valid if row['difficulty'] == difficulty]
    if len(valid) < 4 or len(pool) < questions_per_video:
        raise CatalogError('검증된 국가·국기가 부족해 문제를 만들 수 없습니다. '+ '; '.join(errors[:3]))
    used = history.used_signatures() if history is not None else set()
    recent_runs = history.recent_shorts_country_codes(RECENT_SHORTS) if history is not None else []
    # Drop the oldest Shorts from the avoided set until enough countries remain; 0 means the whole pool.
    for window in range(len(recent_runs), -1, -1):
        recent = set().union(*recent_runs[:window])
        fresh = [row for row in pool if row['code'] not in recent]
        if len(fresh) >= questions_per_video:
            break
    selection_pool = fresh
    pick = _tier_balanced_sample if difficulty == 'Mixed' else lambda r, rows, k: r.sample(rows, k)
    for attempt in range(512):
        selected = pick(rng, selection_pool if attempt < 256 else pool, questions_per_video)
        questions = []
        for country in selected:
            candidates = [row for row in valid if row['code'] != country['code']]
            # Same-tier distractors keep Easy/Normal/Hard meaningful, with a safe fallback.
            same_tier = [row for row in candidates if row['difficulty'] == country['difficulty']]
            wrong = rng.sample(same_tier if len(same_tier) >= 3 else candidates, 3)
            options = [country['name']] + [row['name'] for row in wrong]
            rng.shuffle(options)
            questions.append({'country_code': country['code'], 'country_name': country['name'],
                              'flag_path': country['flag_path'], 'flag': country['flag'],
                              'flag_sha256': country['sha256'], 'options': options,
                              'correct_index': options.index(country['name']),
                              'difficulty': country['difficulty']})
        signature = composition_signature(questions)
        if signature not in used:
            quiz = {'schema_version': 1, 'channel': 'GeoRush', 'difficulty': difficulty,
                    'questions': questions, 'signature': signature,
                    'asset_warnings': errors, 'seed': seed}
            validate_quiz(quiz, catalog)
            return quiz
    raise ValueError('새 문제 구성을 찾지 못했습니다. 다른 난이도나 문제 수를 선택하세요.')
