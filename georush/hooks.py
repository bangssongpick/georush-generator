"""v1.6.4 first-screen hooks for Mixed 3-flag Shorts (easy -> normal -> hard).

Studio (Nov 2026): 'stayed to watch' ~40%; the channel's best Short had a challenge title. The first headline now
rotates between a few challenge lines, chosen from the quiz's flags so one quiz always gets the same line.
Every line is true of a Mixed Short: its last flag is the only Hard one. Each has a matching Kokoro voice clip.
"""
import hashlib

DEFAULT = ('CAN YOU GET ALL 3?', 'first')
HOOKS = (
    DEFAULT,
    ('99% MISS THE LAST ONE!', 'hook_99'),
    ('THE LAST FLAG IS HARD!', 'hook_last'),
    ('ONLY EXPERTS GET 3/3!', 'hook_experts'),
    ('MOST PEOPLE FAIL #3!', 'hook_fail'),
)
VOICE_LINES = {
    'hook_99': 'Ninety-nine percent miss the last one!',
    'hook_last': 'The last flag is really hard!',
    'hook_experts': 'Only experts get all three!',
    'hook_fail': 'Most people fail number three!',
}


def applies(questions):
    """Only plain 3-flag Mixed Shorts: easy first, the single Hard flag last."""
    if len(questions) != 3 or any(q.get('kind') for q in questions):
        return False
    tiers = [q.get('difficulty') for q in questions]
    return tiers[-1] == 'Hard' and 'Hard' not in tiers[:-1]


def choose(questions):
    """(headline, voice clip key) for the first question."""
    if not applies(questions):
        return DEFAULT
    digest = hashlib.sha256(','.join(sorted(q['country_code'] for q in questions)).encode()).digest()
    return HOOKS[digest[0] % len(HOOKS)]
