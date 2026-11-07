"""v1.4.0 Shorts series themes: region-only flags, look-alike flags and capital cities.

Classic is the original flag quiz and stays byte-for-byte the same. Every theme uses the pinned upstream country
data (continent, capital) that already ships with the assets, so no new images or downloads are needed.
"""
from functools import lru_cache
import json

from .paths import resource_root

THEMES = ('Classic', 'Africa', 'Asia', 'Europe', 'Americas', 'Oceania', 'Lookalike', 'Capital')
REGIONS = {'Africa': {'Africa'}, 'Asia': {'Asia'}, 'Europe': {'Europe'},
           'Americas': {'North America', 'South America'}, 'Oceania': {'Oceania'}}

# v1.4.2: the first flag of a Mixed Short comes from these world-famous flags, so a viewer starts with a quick win.
FIRST_FLAGS = ('jp', 'br', 'us', 'ca', 'gb', 'fr', 'de', 'it', 'es', 'kr', 'cn', 'in', 'mx', 'ar', 'au', 'ru', 'gr', 'se',
               'ch', 'za', 'no', 'sa')  # more than the 21 Shorts of the no-repeat window

# Hand-checked groups of flags that viewers commonly confuse. Every code must be in the catalog (checked by tests).
LOOKALIKE_GROUPS = (
    ('id', 'pl'),              # red over white / white over red (Monaco is not in the catalog)
    ('ro', 'ad', 'md'),        # blue-yellow-red vertical tricolours (Chad is not in the catalog)
    ('ie', 'ci', 'it'),        # green-white-orange / green-white-red
    ('nl', 'ru'),              # red-white-blue horizontal tricolours (Luxembourg is not in the catalog)
    ('au', 'nz'),              # Union Jack and Southern Cross
    ('no', 'is', 'dk'),        # Nordic crosses in red/blue
    ('sn', 'ml', 'gn', 'cm'),  # green-yellow-red vertical tricolours
    ('co', 'ec', 've'),        # yellow-blue-red
    ('sk', 'si', 'rs'),        # white-blue-red with a coat of arms
    ('qa', 'bh'),              # serrated white band
    ('hn', 'ni', 'sv'),        # blue-white-blue
    ('tr', 'tn'),              # red with crescent and star
    ('at', 'lv', 'pe'),        # red-white-red
    ('ne', 'in'),              # orange-white-green with a central disc
    ('eg', 'ye', 'iq'),        # red-white-black horizontal tricolours
    ('jo', 'sd', 'ae', 'kw'),  # pan-Arab colours with a hoist triangle or band
    ('lr', 'us', 'my'),        # red and white stripes with a blue canton
)

# Capital mode: countries whose capital is split, disputed or not an official city are never asked.
CAPITAL_EXCLUDED = {
    'bo': 'Sucre (constitutional) and La Paz (seat of government)',
    'za': 'three capitals: Pretoria, Cape Town and Bloemfontein',
    'sz': 'Lobamba and Mbabane',
    'lk': 'Sri Jayawardenepura Kotte and Colombo',
    'il': 'status of Jerusalem is internationally disputed',
    'ci': 'Yamoussoukro is official but Abidjan is the economic capital',
    'bj': 'Porto-Novo is official but Cotonou is the seat of government',
    'nr': 'no official capital (Yaren District)',
    'ye': 'Sana\'a and Aden are contested during the civil war',
    'nl': 'Amsterdam is the capital but the government sits in The Hague',
}
# Upstream spellings replaced by the current English usage.
CAPITAL_NAMES = {'ua': 'Kyiv'}


@lru_cache(maxsize=1)
def _upstream():
    path = resource_root()/'assets'/'country_source_upstream.json'
    return {row['code']: row for row in json.loads(path.read_text(encoding='utf-8'))}


def continent_of(code, upstream=None):
    return (upstream or _upstream()).get(code, {}).get('continent', '')


def capital_of(code, upstream=None):
    if code in CAPITAL_EXCLUDED:
        return ''
    return CAPITAL_NAMES.get(code) or str((upstream or _upstream()).get(code, {}).get('capital', '')).strip()


def lookalike_mates(code):
    for group in LOOKALIKE_GROUPS:
        if code in group:
            return [other for other in group if other != code]
    return []


def theme_pool(theme, rows, upstream=None):
    """Countries that can be asked in this theme (already validated rows)."""
    if theme not in THEMES:
        raise ValueError(f'지원하지 않는 주제입니다: {theme}')
    if theme == 'Classic':
        return list(rows)
    upstream = upstream or _upstream()
    if theme in REGIONS:
        return [row for row in rows if continent_of(row['code'], upstream) in REGIONS[theme]]
    if theme == 'Lookalike':
        valid = {row['code'] for row in rows}
        return [row for row in rows if len([c for c in lookalike_mates(row['code']) if c in valid]) >= 1]
    return [row for row in rows if capital_of(row['code'], upstream)]
