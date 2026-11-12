"""v1.6.2 'Population' Shorts: which of four countries has the most people?

Numbers come from the pinned World Bank file assets/country_population.json (SP.POP.TOTL, CC BY 4.0), never from
the network at run time. Only clear-cut rounds are asked: the biggest country must beat the runner-up by a margin.
"""
from functools import lru_cache
import json

from .paths import resource_root

# The answer must have at least this many times the people of the runner-up, per round (easy -> hard).
MARGINS = {'Easy': 3.0, 'Normal': 1.6, 'Hard': 1.25}
SOURCE_LINE = 'Population: World Bank (2025)'


@lru_cache(maxsize=1)
def _data():
    path = resource_root()/'assets'/'country_population.json'
    return json.loads(path.read_text(encoding='utf-8'))


def population(code):
    row = _data()['countries'].get(code)
    return int(row['population']) if row else 0


def source_note():
    return _data()['source']


def short_number(value):
    """286M / 1.46B / 850K for the reveal labels."""
    if value >= 1e9:
        return f'{value/1e9:.2f}B'
    if value >= 1e7:
        return f'{value/1e6:.0f}M'
    if value >= 1e6:
        return f'{value/1e6:.1f}M'
    return f'{value/1e3:.0f}K'


def margin_ok(codes, tier):
    values = sorted((population(c) for c in codes), reverse=True)
    return values[1] > 0 and values[0] >= MARGINS[tier]*values[1]
