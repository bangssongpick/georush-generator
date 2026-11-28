"""v1.7 flag stories: one sentence per flag, used only after a cross-check.

assets/flag_stories.json: {code: {"text", "source", "second", "checked"}}. "second" is an independent page that supports
the sentence and "checked" is the sha256 of the exact sentence that was compared with both sources. A sentence without
a matching record (never checked, or edited afterwards) is not used in any video.
"""
from functools import lru_cache
import hashlib
import json

from .paths import resource_root


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def is_verified(item):
    return bool(item.get('source') and str(item.get('second', '')).startswith('http')
                and item.get('checked') == text_hash(item.get('text', '')))


@lru_cache(maxsize=1)
def verified_stories():
    """{code: sentence} of the cross-checked stories only."""
    data = json.loads((resource_root()/'assets'/'flag_stories.json').read_text(encoding='utf-8'))
    return {code: item['text'] for code, item in data.items() if is_verified(item)}
