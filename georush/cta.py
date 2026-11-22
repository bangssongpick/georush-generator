"""v1.6.6 test: two closing asks on the last answer of a 3-flag Short, chosen from the quiz so one quiz always gets the same one.

Why: across 41 Shorts almost every video stalls at 1,000-1,500 views while watch time is already good (stayed to watch
53-61%, average viewed 75-140%). What is weak is sharing (0-4 per video) and likes (about 1% of views). So half of the
Shorts ask viewers to tag a friend and like, instead of the original comment/subscribe ask:

  A (original): COMMENT YOUR SCORE + COUNTRY! / LIKE & SUBSCRIBE FOR MORE!      voice: "Comment your score, and subscribe for more!"
  B (test)    : TAG A FRIEND WHO CAN'T GET 3/3! / LIKE & SUBSCRIBE IF YOU GOT 3/3!   voice: "Tag a friend who can't get three!"

B says "three" aloud, so it is used on 3-question Shorts only. The variant is a pure function of the quiz's country codes,
so a finished video's variant can be recomputed later from `_youtube_uploaded.json` (see variant()).
"""
import hashlib

TEXT_A = ('COMMENT YOUR SCORE + COUNTRY!', 'LIKE & SUBSCRIBE FOR MORE!', 'outro')
TEXT_B = ("TAG A FRIEND WHO CAN'T GET {n}/{n}!", 'LIKE & SUBSCRIBE IF YOU GOT {n}/{n}!', 'outro_tag')


def variant(codes):
    """'A' or 'B' from the country codes of a quiz (any order). Only 3-question quizzes can be B."""
    codes = list(codes)
    if len(codes) != 3:
        return 'A'
    digest = hashlib.sha256(','.join(sorted(codes)).encode()).digest()
    return 'B' if digest[1] % 2 else 'A'


def choose(questions):
    """(line 1, line 2, voice clip key, variant) for the last answer."""
    name = variant(q['country_code'] for q in questions)
    line1, line2, key = TEXT_B if name == 'B' else TEXT_A
    n = len(questions)
    return line1.format(n=n), line2.format(n=n), key, name
